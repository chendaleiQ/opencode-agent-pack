# do-the-thing for OpenCode

OpenCode uses one-command native install and supports `agent router`.

## Quick Start

Prerequisite: install [OpenCode.ai](https://opencode.ai) first.

The installer defaults to the latest stable release: `v1.4.0`.

### macOS / Linux

```bash
curl -fsSL https://raw.githubusercontent.com/chendaleiQ/do-the-thing/refs/heads/main/install/install.sh | bash -s -- opencode
```

### Windows PowerShell

```powershell
irm https://raw.githubusercontent.com/chendaleiQ/do-the-thing/refs/heads/main/install/install.ps1 | iex; Install-DoTheThing opencode
```

By default this writes:

```json
{
  "plugin": ["do-the-thing@git+https://github.com/chendaleiQ/do-the-thing.git#v1.4.0"]
}
```

The installer updates `~/.config/opencode/opencode.json` by default. That is the global config path. If you prefer a project-level `opencode.json`, edit that file manually and add the same plugin entry there.

Restart OpenCode. That's it - the plugin auto-installs from GitHub, syncs the workflow files into your OpenCode config directory, and registers the built-in skills. Pack-owned built-in skills use a `dtt-` prefix to avoid collisions with similarly named external Superpowers skills.

## Verify Installation

1. Restart OpenCode.
2. Start a new session.
3. Run this quick check:
   - switch to `leader` and say `ready`
4. Expected result:
   - `leader` is available
   - the workflow still routes through `leader`
   - `agent router` remains available in OpenCode

## Update or Pin a Version

Run the installer again any time.

If you want to pin a specific tag, branch, or commit, set `DTT_PLUGIN_REF` before reinstalling.

### macOS / Linux

```bash
curl -fsSL https://raw.githubusercontent.com/chendaleiQ/do-the-thing/refs/heads/main/install/install.sh | DTT_PLUGIN_REF=v1.2.0 bash -s -- opencode
```

### Windows PowerShell

```powershell
$env:DTT_PLUGIN_REF = 'v1.2.0'; irm https://raw.githubusercontent.com/chendaleiQ/do-the-thing/refs/heads/main/install/install.ps1 | iex; Install-DoTheThing opencode
```

The installer replaces any existing `do-the-thing@...` entries, dedupes repeated entries, and leaves unrelated plugins unchanged.

## Uninstall

Remove the `do-the-thing@...` entry from your `opencode.json`, then restart OpenCode.

## Troubleshooting

1. Confirm `opencode.json` contains the expected plugin entry.
2. Restart OpenCode after adding or changing the plugin line.
3. If the installer reports invalid JSON, fix `opencode.json` and use the generated `opencode.json.bak.<timestamp>` backup if needed.
4. If the installer warns that the OpenCode config directory was missing, confirm OpenCode is installed and uses `~/.config/opencode` (or your custom `OPENCODE_CONFIG_DIR`).
5. If you previously copied files into `~/.config/opencode/`, remove the old setup first:

```bash
rm -f ~/.config/opencode/AGENTS.md
rm -rf ~/.config/opencode/agents ~/.config/opencode/commands ~/.config/opencode/skills ~/.config/opencode/tools
```

If you also have older skill sources in `~/.agents/skills`, remove or disable them before enabling do-the-thing. The plugin will stop loading when it detects duplicate skill names from multiple sources.

## Advanced Notes

The default install targets the latest stable release so new users get the newest published baseline without needing extra flags. If you need an older or experimental ref, override it with `DTT_PLUGIN_REF` and reinstall.
