function Install-DoTheThing {
  param([Parameter(Mandatory = $true)][string]$Platform)

  $repoUrl = if ($env:DTT_REPO_URL) { $env:DTT_REPO_URL } else { 'https://github.com/chendaleiQ/do-the-thing.git' }
  $installRoot = if ($env:DTT_INSTALL_ROOT) { $env:DTT_INSTALL_ROOT } else { Join-Path $HOME '.local/share/do-the-thing' }
  $opencodeConfigDir = if ($env:OPENCODE_CONFIG_DIR) { $env:OPENCODE_CONFIG_DIR } else { Join-Path $HOME '.config/opencode' }
  $pluginValue = 'do-the-thing@git+https://github.com/chendaleiQ/do-the-thing.git'
  if ($env:DTT_PLUGIN_REF) {
    $pluginValue = "$pluginValue#$($env:DTT_PLUGIN_REF)"
  }

  if ($Platform -notin @('opencode', 'codex')) {
    throw 'usage: Install-DoTheThing <opencode|codex>'
  }

  # -----------------------------------------------------------------------
  # Dependency helpers
  # -----------------------------------------------------------------------

  function Ensure-GitAvailable {
    if (Get-Command git -ErrorAction SilentlyContinue) { return }

    Write-Host 'git is not installed. Attempting automatic install ...' -ForegroundColor Yellow

    $installed = $false
    if (Get-Command winget -ErrorAction SilentlyContinue) {
      Write-Host 'Using winget to install Git ...'
      winget install --id Git.Git -e --accept-source-agreements --accept-package-agreements
      $installed = $true
    } elseif (Get-Command choco -ErrorAction SilentlyContinue) {
      Write-Host 'Using Chocolatey to install Git ...'
      choco install git -y
      $installed = $true
    } elseif (Get-Command scoop -ErrorAction SilentlyContinue) {
      Write-Host 'Using Scoop to install Git ...'
      scoop install git
      $installed = $true
    }

    if ($installed) {
      # Refresh PATH so the current session can find git
      $env:Path = [System.Environment]::GetEnvironmentVariable('Path', 'Machine') + ';' +
                  [System.Environment]::GetEnvironmentVariable('Path', 'User')
    }

    if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
      throw 'Error: git is still not available after install attempt. Please install git manually, then rerun this installer.'
    }
  }

  # -----------------------------------------------------------------------
  # Repository helpers
  # -----------------------------------------------------------------------

  function Sync-RepoClone {
    New-Item -ItemType Directory -Force -Path (Split-Path $installRoot -Parent) | Out-Null

    if (Test-Path (Join-Path $installRoot '.git')) {
      try {
        $output = git -C $installRoot pull --ff-only 2>&1
        if ($LASTEXITCODE -ne 0) { throw $output }
      } catch {
        Write-Error "git pull --ff-only failed. Your local clone may have diverged."
        Write-Error "To recover, try:"
        Write-Error "  git -C `"$installRoot`" fetch origin; git -C `"$installRoot`" reset --hard origin/main"
        throw
      }
    } else {
      if (Test-Path $installRoot) {
        Remove-Item -Recurse -Force $installRoot
      }
      git clone $repoUrl $installRoot | Out-Null
    }
  }

  # -----------------------------------------------------------------------
  # Ensure dependencies for the chosen target
  # -----------------------------------------------------------------------

  if ($Platform -eq 'codex') {
    Ensure-GitAvailable
  }
  # Both opencode and codex targets need python3 available (opencode uses it for JSON config).

  # -----------------------------------------------------------------------
  # Platform install logic
  # -----------------------------------------------------------------------

  switch ($Platform) {
    'opencode' {
      # OpenCode's native plugin system fetches the pack directly from the git
      # URL registered in opencode.json.  No local clone is needed — the plugin
      # runtime resolves the git+https reference at startup and keeps its own cache.
      #
      # Delegate JSON manipulation to a Python snippet so the behaviour is
      # identical to the shell (bash) installer regardless of PowerShell version.
      New-Item -ItemType Directory -Force -Path $opencodeConfigDir | Out-Null
      $configPath = Join-Path $opencodeConfigDir 'opencode.json'

      $env:OPENCODE_JSON = $configPath
      $env:DTT_PLUGIN_REF = if ($env:DTT_PLUGIN_REF) { $env:DTT_PLUGIN_REF } else { '' }
      $pythonCode = @'
import json
import os
from pathlib import Path

config_path = Path(os.environ["OPENCODE_JSON"])
plugin_value = "do-the-thing@git+https://github.com/chendaleiQ/do-the-thing.git"
plugin_ref = os.environ.get("DTT_PLUGIN_REF", "").strip()
if plugin_ref:
    plugin_value = f"{plugin_value}#{plugin_ref}"

if config_path.exists():
    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        data = {}
else:
    data = {}

plugins = data.get("plugin")
if not isinstance(plugins, list):
    plugins = []

next_plugins = []
insert_at = None
for plugin in plugins:
    if plugin == plugin_value:
        if insert_at is None:
            insert_at = len(next_plugins)
        continue
    if isinstance(plugin, str) and plugin.startswith("do-the-thing@"):
        if insert_at is None:
            insert_at = len(next_plugins)
        continue
    if plugin not in next_plugins:
        next_plugins.append(plugin)

if insert_at is None:
    next_plugins.append(plugin_value)
else:
    next_plugins.insert(insert_at, plugin_value)

data["plugin"] = next_plugins

config_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
'@
      python3 -c $pythonCode
      Write-Host 'OpenCode install complete.'
      Write-Host "Verify: confirm $configPath contains the do-the-thing plugin entry then restart OpenCode."
      Write-Host 'Update: rerun with $env:DTT_PLUGIN_REF=<ref> to replace existing do-the-thing entries, then restart OpenCode.'
      Write-Host "Uninstall: remove do-the-thing from $configPath"
    }
    'codex' {
      Sync-RepoClone
      $skillsRoot = Join-Path $HOME '.agents/skills'
      New-Item -ItemType Directory -Force -Path $skillsRoot | Out-Null
      $junctionPath = Join-Path $skillsRoot 'do-the-thing'
      if (Test-Path $junctionPath) {
        Remove-Item -Recurse -Force $junctionPath
      }
      try {
        $mkOutput = cmd /c mklink /J "$junctionPath" "$installRoot\skills" 2>&1
        if ($LASTEXITCODE -ne 0) { throw $mkOutput }
      } catch {
        Write-Error "Failed to create directory junction at $junctionPath."
        Write-Error "You may need to run PowerShell as Administrator, or enable Developer Mode in Windows Settings."
        throw
      }
      Write-Host 'Codex install complete.'
      Write-Host "Verify: dir $junctionPath"
      Write-Host "Uninstall link: Remove-Item -Recurse -Force $junctionPath"
      Write-Host "Installed repository: $installRoot"
      Write-Host "Update: git -C $installRoot pull --ff-only"
      Write-Host "Uninstall: Remove-Item -Recurse -Force $installRoot"
    }
  }
}
