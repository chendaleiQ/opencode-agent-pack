param(
    [switch]$Global,
    [string]$Target,
    [switch]$Force
)

if ($Global) {
    Write-Error "-Global is not needed. Default install target is ~/.config/opencode/."
    exit 1
}

$ErrorActionPreference = "Stop"
$preserveFiles = @("opencode.json", "settings.json")
$pythonCandidates = @(
    @{ Command = $env:PYTHON_BIN; PrefixArgs = @() }
    @{ Command = "python3"; PrefixArgs = @() }
    @{ Command = "python"; PrefixArgs = @() }
    @{ Command = "py"; PrefixArgs = @("-3") }
)

function Show-Usage {
@"
opencode-agent-pack installer

Usage:
    .\install.ps1 [-Target <path>] [-Force]

Options:
    -Target       Install into a custom directory (default: ~/.config/opencode/)
    -Force        Rebuild target directory from scratch when non-empty
"@
}

function Get-PythonCommand {
    foreach ($candidate in $pythonCandidates) {
        if ([string]::IsNullOrWhiteSpace($candidate.Command)) {
            continue
        }
        if (-not (Get-Command $candidate.Command -ErrorAction SilentlyContinue)) {
            continue
        }
        if (Test-PythonCommand -Command $candidate.Command -PrefixArgs $candidate.PrefixArgs) {
            return $candidate
        }
    }

    throw "Python is required to detect and persist provider allowlists."
}

function Test-PythonCommand {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Command,

        [string[]]$PrefixArgs = @()
    )

    $probeArgs = @()
    if ($PrefixArgs) {
        $probeArgs += $PrefixArgs
    }
    $probeArgs += @(
        "-c",
        "import sys; raise SystemExit(0 if sys.version_info[0] == 3 else 1)"
    )

    & $Command @probeArgs *> $null
    return $LASTEXITCODE -eq 0
}

function Invoke-ProviderPolicy {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$Arguments
    )

    $invokeArgs = @()
    if ($script:PythonPrefixArgs) {
        $invokeArgs += $script:PythonPrefixArgs
    }
    $invokeArgs += (Join-Path $script:PackDir "tools/provider_policy.py")
    $invokeArgs += $Arguments

    $output = & $script:PythonBin @invokeArgs
    $exitCode = $LASTEXITCODE
    if ($exitCode -ne 0) {
        $prettyArgs = $invokeArgs -join " "
        throw "provider_policy.py failed with exit code $exitCode: $prettyArgs"
    }

    return $output
}

function Convert-AllowedProvidersToJsonArray {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$AllowedProviders
    )

    # Serialize each provider individually so a one-item selection never collapses to a JSON string.
    $jsonItems = @()
    foreach ($provider in @($AllowedProviders)) {
        $jsonItems += (ConvertTo-Json -InputObject $provider -Compress)
    }

    $jsonArray = '[' + ($jsonItems -join ',') + ']'
    if (-not $jsonArray.StartsWith('[') -or -not $jsonArray.EndsWith(']')) {
        throw "internal error: allowed providers must serialize as a JSON array"
    }

    return $jsonArray
}

function Detect-ProviderCandidates {
    $output = Invoke-ProviderPolicy @(
        "--config-dir", (Join-Path $home ".config/opencode"),
        "--data-dir", (Join-Path $home ".local/share/opencode"),
        "--cache-dir", (Join-Path $home ".cache/opencode"),
        "--detect-providers"
    )

    if ([string]::IsNullOrWhiteSpace($output)) {
        return @()
    }

    @($output | ConvertFrom-Json)
}

function Write-AllowedProviders {
    param(
        [Parameter(Mandatory = $true)]
        [string]$SettingsPath,

        [Parameter(Mandatory = $true)]
        [string[]]$AllowedProviders
    )

    $allowedJson = Convert-AllowedProvidersToJsonArray -AllowedProviders $AllowedProviders
    Invoke-ProviderPolicy @(
        "--settings-path", $SettingsPath,
        "--set-allowed-providers-json", $allowedJson
    ) | Out-Null
}

function Show-ProviderSelectionPrompt {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$Candidates
    )

    Write-Host "Select allowed providers for opencode-agent-pack"
    for ($idx = 0; $idx -lt $Candidates.Count; $idx++) {
        Write-Host ("[{0}] {1}" -f ($idx + 1), $Candidates[$idx])
    }
    Write-Host "Enter comma-separated numbers, or press Enter for all:"
}

function Parse-ProviderSelection {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$Candidates,

        [Parameter(Mandatory = $true)]
        [string]$Selection
    )

    $raw = $Selection.Trim()
    if ([string]::IsNullOrWhiteSpace($raw)) {
        return @($Candidates)
    }

    $indexes = New-Object System.Collections.Generic.List[int]
    $seen = New-Object System.Collections.Generic.HashSet[int]

    foreach ($item in $raw.Split(",")) {
        $trimmed = $item.Trim()
        if ([string]::IsNullOrWhiteSpace($trimmed) -or $trimmed -notmatch '^\d+$') {
            throw "Invalid provider selection."
        }

        $idx = [int]$trimmed
        if ($idx -lt 1 -or $idx -gt $Candidates.Count -or -not $seen.Add($idx)) {
            throw "Invalid provider selection."
        }

        $indexes.Add($idx)
    }

    $selected = @()
    foreach ($idx in $indexes) {
        $selected += $Candidates[$idx - 1]
    }

    return $selected
}

function Select-AllowedProviders {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$Candidates
    )

    if ($Candidates.Count -eq 0) {
        if ([Console]::IsInputRedirected -or -not [Environment]::UserInteractive) {
            Write-Warning "No providers were detected; skipping provider allowlist write."
            return [pscustomobject]@{
                ShouldWrite      = $false
                AllowedProviders = @()
            }
        }

        Write-Host "No providers were detected from local OpenCode state."
        $confirm = Read-Host "Write an explicit empty allowlist anyway? [y/N]"
        if ($confirm -match '^[Yy](es)?$') {
            return [pscustomobject]@{
                ShouldWrite      = $true
                AllowedProviders = @()
            }
        }

        Write-Host "Skipping provider allowlist write."
        return [pscustomobject]@{
            ShouldWrite      = $false
            AllowedProviders = @()
        }
    }

    if ([Console]::IsInputRedirected -or -not [Environment]::UserInteractive) {
        Write-Host "Non-interactive install detected; defaulting to all detected providers." -ForegroundColor Yellow
        return [pscustomobject]@{
            ShouldWrite      = $true
            AllowedProviders = @($Candidates)
        }
    }

    while ($true) {
        Show-ProviderSelectionPrompt -Candidates $Candidates
        $selection = Read-Host
        try {
            return [pscustomobject]@{
                ShouldWrite      = $true
                AllowedProviders = @(Parse-ProviderSelection -Candidates $Candidates -Selection $selection)
            }
        } catch {
            Write-Host "Invalid selection. Enter comma-separated numbers, or press Enter for all." -ForegroundColor Red
        }
    }
}

function Get-ResolvedTarget {
    param(
        [string]$CustomTarget
    )

    if ($CustomTarget) {
        return $CustomTarget
    }

    return Join-Path $home ".config/opencode"
}

function Ensure-Directory {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    if (-not (Test-Path $Path)) {
        New-Item -ItemType Directory -Path $Path | Out-Null
    }
}

function Backup-PreservedFiles {
    param(
        [Parameter(Mandatory = $true)]
        [string]$SourceDir
    )

    $backup = Join-Path ([System.IO.Path]::GetTempPath()) ([System.Guid]::NewGuid().ToString())
    New-Item -ItemType Directory -Path $backup | Out-Null

    foreach ($name in $preserveFiles) {
        $src = Join-Path $SourceDir $name
        if (Test-Path $src -PathType Leaf) {
            Copy-Item -Path $src -Destination (Join-Path $backup $name) -Force
        }
    }

    return $backup
}

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$PackDir = Join-Path $ScriptDir "pack"
$PythonLauncher = Get-PythonCommand
$PythonBin = $PythonLauncher.Command
$PythonPrefixArgs = $PythonLauncher.PrefixArgs

if (-not (Test-Path $PackDir -PathType Container)) {
    throw "pack directory not found: $PackDir"
}

$mode = "global"
$home = [Environment]::GetFolderPath("UserProfile")
$resolvedTarget = Get-ResolvedTarget -CustomTarget $Target
$backupDir = $null

if ($Target) {
    $mode = "custom"
    $resolvedTarget = $Target
}

Ensure-Directory -Path $resolvedTarget

$hasExisting = (Get-ChildItem -Path $resolvedTarget -Force -ErrorAction SilentlyContinue | Measure-Object).Count -gt 0
if ($hasExisting -and -not $Force) {
    throw "Target directory is not empty: $resolvedTarget. Use -Force to rebuild."
}

if ($hasExisting -and $Force) {
    # Force mode is a clean rebuild: remove all existing target contents first.
    $backupDir = Backup-PreservedFiles -SourceDir $resolvedTarget
    Get-ChildItem -Path $resolvedTarget -Force | Remove-Item -Recurse -Force
}

$candidateProviders = Detect-ProviderCandidates
$selectionResult = Select-AllowedProviders -Candidates $candidateProviders

Copy-Item -Path (Join-Path $PackDir "*") -Destination $resolvedTarget -Recurse -Force

if ($backupDir) {
    foreach ($name in $preserveFiles) {
        $src = Join-Path $backupDir $name
        if (Test-Path $src -PathType Leaf) {
            Move-Item -Path $src -Destination (Join-Path $resolvedTarget $name) -Force
        }
    }
    Remove-Item -Path $backupDir -Recurse -Force
}

if ($selectionResult.ShouldWrite) {
    Write-AllowedProviders -SettingsPath (Join-Path $resolvedTarget "settings.json") -AllowedProviders $selectionResult.AllowedProviders
}

Write-Host "Installed opencode-agent-pack"
Write-Host "Mode: $mode"
Write-Host "Target: $resolvedTarget"
Write-Host "Done."
