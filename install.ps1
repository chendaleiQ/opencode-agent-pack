param(
    [switch]$Project,
    [switch]$Global,
    [string]$Target,
    [switch]$Force
)

$ErrorActionPreference = "Stop"

function Show-Usage {
@"
opencode-agent-pack installer

Usage:
  .\install.ps1 [-Project | -Global | -Target <path>] [-Force]

Options:
  -Project      Install into current project: .opencode\ (default)
  -Global       Install into: ~/.config/opencode/
  -Target       Install into a custom directory
  -Force        Allow overwrite/merge when target is non-empty
"@
}

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$PackDir = Join-Path $ScriptDir "pack"

if (-not (Test-Path $PackDir -PathType Container)) {
    throw "pack directory not found: $PackDir"
}

$mode = "project"
$resolvedTarget = ".opencode"

if ($Global) {
    $mode = "global"
    $home = [Environment]::GetFolderPath("UserProfile")
    $resolvedTarget = Join-Path $home ".config/opencode"
}
elseif ($Target) {
    $mode = "custom"
    $resolvedTarget = $Target
}
elseif ($Project -or (-not $Global -and -not $Target)) {
    $mode = "project"
    $resolvedTarget = ".opencode"
}

if (-not (Test-Path $resolvedTarget)) {
    New-Item -ItemType Directory -Path $resolvedTarget | Out-Null
}

$hasExisting = (Get-ChildItem -Path $resolvedTarget -Force -ErrorAction SilentlyContinue | Measure-Object).Count -gt 0
if ($hasExisting -and -not $Force) {
    throw "Target directory is not empty: $resolvedTarget. Use -Force to overwrite/merge."
}

Copy-Item -Path (Join-Path $PackDir "*") -Destination $resolvedTarget -Recurse -Force

Write-Host "Installed opencode-agent-pack"
Write-Host "Mode: $mode"
Write-Host "Target: $resolvedTarget"
Write-Host "Done."
