# do-the-thing for OpenCode

OpenCode uses native plugin install and supports `agent router`.

## Prerequisites

- [OpenCode.ai](https://opencode.ai) installed

## Install

Add do-the-thing to the `plugin` array in your `opencode.json` (global or project-level):

```json
{
  "plugin": ["do-the-thing@git+https://github.com/chendaleiQ/do-the-thing.git"]
}
```

Restart OpenCode. That's it - the plugin auto-installs from GitHub, syncs the workflow files into your OpenCode config directory, and registers the built-in skills.

To pin a specific version:

```json
{
  "plugin": ["do-the-thing@git+https://github.com/chendaleiQ/do-the-thing.git#v1.1.1"]
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

do-the-thing updates automatically when you restart OpenCode.

## Troubleshooting

1. Check that the `plugin` line exists in your `opencode.json`
2. Restart OpenCode after adding or changing the plugin line
3. Confirm that `AGENTS.md`, `agents/`, `commands/`, `skills/`, and `tools/` were synced into your OpenCode config directory
