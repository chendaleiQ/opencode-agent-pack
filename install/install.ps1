function Install-DoTheThing {
  param([Parameter(Mandatory = $true)][string]$Platform)

  $repoUrl = if ($env:DTT_REPO_URL) { $env:DTT_REPO_URL } else { 'https://github.com/chendaleiQ/do-the-thing.git' }
  $installRoot = if ($env:DTT_INSTALL_ROOT) { $env:DTT_INSTALL_ROOT } else { Join-Path $HOME '.local/share/do-the-thing' }
  $opencodeConfigDir = if ($env:OPENCODE_CONFIG_DIR) { $env:OPENCODE_CONFIG_DIR } else { Join-Path $HOME '.config/opencode' }

  if ($Platform -notin @('opencode', 'claude', 'codex')) {
    throw 'usage: Install-DoTheThing <opencode|claude|codex>'
  }

  function Sync-RepoClone {
    New-Item -ItemType Directory -Force -Path (Split-Path $installRoot -Parent) | Out-Null

    if (Test-Path (Join-Path $installRoot '.git')) {
      git -C $installRoot pull --ff-only | Out-Null
    } else {
      if (Test-Path $installRoot) {
        Remove-Item -Recurse -Force $installRoot
      }
      git clone $repoUrl $installRoot | Out-Null
    }
  }

  switch ($Platform) {
    'opencode' {
      New-Item -ItemType Directory -Force -Path $opencodeConfigDir | Out-Null
      $configPath = Join-Path $opencodeConfigDir 'opencode.json'
      if (Test-Path $configPath) {
        try {
          $config = Get-Content $configPath -Raw | ConvertFrom-Json -AsHashtable
        } catch {
          $config = @{}
        }
      } else {
        $config = @{}
      }
      if ($null -eq $config['plugin'] -or $config['plugin'] -isnot [System.Collections.IList]) {
        $config['plugin'] = @()
      }
      if ($config['plugin'] -notcontains 'do-the-thing@git+https://github.com/chendaleiQ/do-the-thing.git') {
        $config['plugin'] += 'do-the-thing@git+https://github.com/chendaleiQ/do-the-thing.git'
      }
      $config | ConvertTo-Json -Depth 10 | Set-Content -Encoding UTF8 $configPath
      Write-Host 'OpenCode install complete.'
      Write-Host "Verify: confirm $configPath contains ""plugin"": [""do-the-thing@git+https://github.com/chendaleiQ/do-the-thing.git""] then restart OpenCode."
      Write-Host "Update: restart OpenCode after changing or re-pinning the plugin reference."
      Write-Host "Uninstall: remove do-the-thing from $configPath"
    }
    'claude' {
      Sync-RepoClone
      Write-Host 'Claude Code install complete.'
      Write-Host "Verify: confirm $installRoot/.claude-plugin/plugin.json exists."
      Write-Host "Usage: claude --plugin-dir $installRoot"
      Write-Host "Installed repository: $installRoot"
      Write-Host "Update: git -C $installRoot pull --ff-only"
      Write-Host "Uninstall: Remove-Item -Recurse -Force $installRoot"
    }
    'codex' {
      Sync-RepoClone
      $skillsRoot = Join-Path $HOME '.agents/skills'
      New-Item -ItemType Directory -Force -Path $skillsRoot | Out-Null
      $junctionPath = Join-Path $skillsRoot 'do-the-thing'
      if (Test-Path $junctionPath) {
        Remove-Item -Recurse -Force $junctionPath
      }
      cmd /c mklink /J "$junctionPath" "$installRoot\skills" | Out-Null
      Write-Host 'Codex install complete.'
      Write-Host "Verify: dir $junctionPath"
      Write-Host "Uninstall link: Remove-Item -Recurse -Force $junctionPath"
      Write-Host "Installed repository: $installRoot"
      Write-Host "Update: git -C $installRoot pull --ff-only"
      Write-Host "Uninstall: Remove-Item -Recurse -Force $installRoot"
    }
  }
}
