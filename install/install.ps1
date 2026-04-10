function Install-DoTheThing {
  param([Parameter(Mandatory = $true)][string]$Platform)

  $repoUrl = if ($env:DTT_REPO_URL) { $env:DTT_REPO_URL } else { 'https://github.com/chendaleiQ/do-the-thing.git' }
  $installRoot = if ($env:DTT_INSTALL_ROOT) { $env:DTT_INSTALL_ROOT } else { Join-Path $HOME '.local/share/do-the-thing' }
  $opencodeConfigDir = if ($env:OPENCODE_CONFIG_DIR) { $env:OPENCODE_CONFIG_DIR } else { Join-Path $HOME '.config/opencode' }
  $pluginValue = 'do-the-thing@git+https://github.com/chendaleiQ/do-the-thing.git'
  if ($env:DTT_PLUGIN_REF) {
    $pluginValue = "$pluginValue#$($env:DTT_PLUGIN_REF)"
  }

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
      $plugins = if ($null -eq $config['plugin'] -or $config['plugin'] -isnot [System.Collections.IList]) {
        @()
      } else {
        @($config['plugin'])
      }

      $nextPlugins = New-Object System.Collections.Generic.List[object]
      $insertAt = $null
      foreach ($plugin in $plugins) {
        if ($plugin -eq $pluginValue) {
          if ($null -eq $insertAt) {
            $insertAt = $nextPlugins.Count
          }
          continue
        }
        if ($plugin -is [string] -and $plugin.StartsWith('do-the-thing@')) {
          if ($null -eq $insertAt) {
            $insertAt = $nextPlugins.Count
          }
          continue
        }
        if (-not $nextPlugins.Contains($plugin)) {
          [void]$nextPlugins.Add($plugin)
        }
      }

      if ($null -eq $insertAt) {
        [void]$nextPlugins.Add($pluginValue)
      } else {
        $nextPlugins.Insert($insertAt, $pluginValue)
      }

      $config['plugin'] = @($nextPlugins)
      $config | ConvertTo-Json -Depth 10 | Set-Content -Encoding UTF8 $configPath
      Write-Host 'OpenCode install complete.'
      Write-Host "Verify: confirm $configPath contains ""plugin"": [""$pluginValue""] then restart OpenCode."
      Write-Host 'Update: rerun with $env:DTT_PLUGIN_REF=<ref> to replace existing do-the-thing entries, then restart OpenCode.'
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
