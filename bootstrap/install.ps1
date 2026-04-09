param(
    [string]$Version = "latest",
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$InstallArgs = @()
)

$ErrorActionPreference = "Stop"
$Repo = "chendaleiQ/do-the-thing"

if ($env:DO_THE_THING_VERSION) {
    $Version = $env:DO_THE_THING_VERSION
}

function Get-LatestReleaseVersion {
    $response = Invoke-RestMethod -Headers @{ Accept = "application/vnd.github+json" } -Uri "https://api.github.com/repos/$Repo/releases/latest"
    if (-not $response.tag_name) {
        throw "missing tag_name in latest release metadata"
    }
    return [string]$response.tag_name
}

if ($Version -eq "latest") {
    $Version = Get-LatestReleaseVersion
}

$TempRoot = Join-Path ([System.IO.Path]::GetTempPath()) ([System.Guid]::NewGuid().ToString())
New-Item -ItemType Directory -Path $TempRoot | Out-Null

try {
    $ArchivePath = Join-Path $TempRoot ("do-the-thing-{0}.zip" -f $Version)
    $AssetUrl = "https://github.com/$Repo/releases/download/$Version/do-the-thing-$Version.zip"

    Invoke-WebRequest -Uri $AssetUrl -OutFile $ArchivePath
    Expand-Archive -Path $ArchivePath -DestinationPath $TempRoot -Force

    $HelperPath = Join-Path $TempRoot "pack/tools/release_bootstrap.py"
    if (-not (Test-Path $HelperPath -PathType Leaf)) {
        $HelperPath = Join-Path $TempRoot "do-the-thing-$Version/pack/tools/release_bootstrap.py"
    }

    if (-not (Test-Path $HelperPath -PathType Leaf)) {
        throw "release package is missing pack/tools/release_bootstrap.py"
    }

    $PythonBin = if ($env:PYTHON_BIN) { $env:PYTHON_BIN } else { "python3" }
    $ReleaseRoot = & $PythonBin $HelperPath --validate-extracted-root $TempRoot
    if ($LASTEXITCODE -ne 0) {
        throw "release root validation failed"
    }

    $InstallerPath = Join-Path $ReleaseRoot "install.ps1"
    if (-not (Test-Path $InstallerPath -PathType Leaf)) {
        throw "release package is missing install.ps1"
    }

    & $InstallerPath @InstallArgs
    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }
}
finally {
    Remove-Item -Path $TempRoot -Recurse -Force -ErrorAction SilentlyContinue
}
