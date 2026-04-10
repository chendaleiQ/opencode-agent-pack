# do-the-thing for OpenCode

OpenCode uses one-command native install and supports `agent router`.

## Prerequisites

- [OpenCode.ai](https://opencode.ai) installed

## One-Command Install

### macOS / Linux

```bash
curl -fsSL https://raw.githubusercontent.com/chendaleiQ/do-the-thing/refs/heads/main/install/install.sh | bash -s -- opencode
```

To pin or update the plugin reference while reinstalling:

```bash
curl -fsSL https://raw.githubusercontent.com/chendaleiQ/do-the-thing/refs/heads/main/install/install.sh | DTT_PLUGIN_REF=v1.2.0 bash -s -- opencode
```

### Windows PowerShell

```powershell
irm https://raw.githubusercontent.com/chendaleiQ/do-the-thing/refs/heads/main/install/install.ps1 | iex; Install-DoTheThing opencode
```

To pin or update the plugin reference while reinstalling:

```powershell
$env:DTT_PLUGIN_REF = 'v1.2.0'; irm https://raw.githubusercontent.com/chendaleiQ/do-the-thing/refs/heads/main/install/install.ps1 | iex; Install-DoTheThing opencode
```

## Native Plugin Details

Add do-the-thing to the `plugin` array in your `opencode.json` (global or project-level):

```json
{
  "plugin": ["do-the-thing@git+https://github.com/chendaleiQ/do-the-thing.git"]
}
```

Restart OpenCode. That's it - the plugin auto-installs from GitHub, syncs the workflow files into your OpenCode config directory, and registers the built-in skills. Pack-owned built-in skills use a `dtt-` prefix to avoid collisions with similarly named external Superpowers skills.

To pin a specific version:

```json
{
  "plugin": ["do-the-thing@git+https://github.com/chendaleiQ/do-the-thing.git#v1.2.0"]
}
```

## Migrating from old manual installs

If you previously copied files into `~/.config/opencode/`, remove the old setup first:

```bash
rm -f ~/.config/opencode/AGENTS.md
rm -rf ~/.config/opencode/agents ~/.config/opencode/commands ~/.config/opencode/skills ~/.config/opencode/tools
```

If you also have older skill sources in `~/.agents/skills`, remove or disable them before enabling do-the-thing. The plugin will stop loading when it detects duplicate skill names from multiple sources.

## Verify Installation

Start a new OpenCode session and ask for a task that should trigger workflow routing. The session should route through `leader`, use the built-in method skills, and keep `agent router` available.

## Updating

Run the one-command installer again to update the configured `do-the-thing` plugin entry in place. The installer replaces any existing `do-the-thing@...` entries, dedupes repeated entries, and leaves unrelated plugins unchanged. Set `DTT_PLUGIN_REF` before rerunning if you want to move to a specific tag, branch, or commit, then restart OpenCode.

## Troubleshooting

1. Check that the `plugin` line exists in your `opencode.json`
2. If needed, rerun the installer with `DTT_PLUGIN_REF=<ref>` to replace stale `do-the-thing` entries
3. Restart OpenCode after adding or changing the plugin line
4. Confirm that `AGENTS.md`, `agents/`, `commands/`, `skills/`, and `tools/` were synced into your OpenCode config directory
