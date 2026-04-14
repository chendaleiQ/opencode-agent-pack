function Install-DoTheThing {
  param([Parameter(Mandatory = $true)][string]$Platform)

  $repoUrl = if ($env:DTT_REPO_URL) { $env:DTT_REPO_URL } else { 'https://github.com/chendaleiQ/do-the-thing.git' }
  $installRoot = if ($env:DTT_INSTALL_ROOT) { $env:DTT_INSTALL_ROOT } else { Join-Path $HOME '.local/share/do-the-thing' }
  $opencodeConfigDir = if ($env:OPENCODE_CONFIG_DIR) { $env:OPENCODE_CONFIG_DIR } else { Join-Path $HOME '.config/opencode' }
  $defaultOpenCodeRef = 'main'
  $pluginValue = 'do-the-thing@git+https://github.com/chendaleiQ/do-the-thing.git'
  $pluginRef = if ($env:DTT_PLUGIN_REF) { $env:DTT_PLUGIN_REF } else { $defaultOpenCodeRef }
  if ($pluginRef) {
    $pluginValue = "$pluginValue#$pluginRef"
  }

  if ($Platform -notin @('opencode', 'codex')) {
    throw 'usage: Install-DoTheThing <opencode|codex>'
  }

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
      $env:Path = [System.Environment]::GetEnvironmentVariable('Path', 'Machine') + ';' +
                  [System.Environment]::GetEnvironmentVariable('Path', 'User')
    }

    if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
      throw 'Error: git is still not available after install attempt. Please install git manually, then rerun this installer.'
    }
  }

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

  function Backup-File([string]$Path) {
    $timestamp = Get-Date -Format 'yyyyMMdd-HHmmss'
    $backupPath = "$Path.bak.$timestamp"
    Copy-Item -LiteralPath $Path -Destination $backupPath -Force
    return $backupPath
  }

  function Read-JsonObject([string]$Path) {
    if (-not (Test-Path $Path)) {
      return @{}
    }

    $backupPath = Backup-File $Path
    try {
      $raw = Get-Content -LiteralPath $Path -Raw -Encoding UTF8
      if ([string]::IsNullOrWhiteSpace($raw)) {
        Write-Host "Backup written to $backupPath"
        return @{}
      }
      $parsed = $raw | ConvertFrom-Json -AsHashtable -Depth 100 -ErrorAction Stop
      if ($null -eq $parsed) {
        $parsed = @{}
      }
      Write-Host "Backup written to $backupPath"
      return $parsed
    } catch {
      throw "Invalid JSON in $Path; backup saved to $backupPath. $($_.Exception.Message)"
    }
  }

  if ($Platform -eq 'codex') {
    Ensure-GitAvailable
  }

  switch ($Platform) {
    'opencode' {
      $configDirExists = Test-Path $opencodeConfigDir
      New-Item -ItemType Directory -Force -Path $opencodeConfigDir | Out-Null
      $configPath = Join-Path $opencodeConfigDir 'opencode.json'

      if (-not $configDirExists) {
        Write-Warning "OpenCode config directory was not found at $opencodeConfigDir. The installer will create it now, but please confirm OpenCode is installed and uses this location."
      }

      Write-Host "Step 1/3: Updating $configPath"
      Write-Host 'Step 2/3: Ensuring do-the-thing plugin entry is present'

      $data = Read-JsonObject $configPath
      $plugins = @()
      if ($data.ContainsKey('plugin') -and $data['plugin'] -is [System.Collections.IEnumerable] -and $data['plugin'] -isnot [string]) {
        foreach ($item in $data['plugin']) {
          $plugins += [string]$item
        }
      }

      $nextPlugins = New-Object System.Collections.Generic.List[string]
      $insertAt = $null
      foreach ($plugin in $plugins) {
        if ($plugin -eq $pluginValue) {
          if ($null -eq $insertAt) { $insertAt = $nextPlugins.Count }
          continue
        }
        if ($plugin.StartsWith('do-the-thing@')) {
          if ($null -eq $insertAt) { $insertAt = $nextPlugins.Count }
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

      $data['plugin'] = @($nextPlugins.ToArray())
      $data['default_agent'] = 'leader'
      $json = $data | ConvertTo-Json -Depth 100
      Set-Content -LiteralPath $configPath -Value ($json + "`n") -Encoding UTF8

      Write-Host 'Step 3/3: Done.'
      Write-Host 'OpenCode install complete.'
      Write-Host "Configured file: $configPath"
      Write-Host "Default OpenCode install tracks the repository main branch: $defaultOpenCodeRef"
      Write-Host 'Configured plugin entry:'
      Write-Host "  `"plugin`": [`"$pluginValue`"]"
      Write-Host 'Next step: restart OpenCode.'
      Write-Host 'Then test with: switch to leader and say ready'
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
