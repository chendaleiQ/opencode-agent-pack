# do-the-thing for OpenCode

OpenCode uses one-command native install and supports `agent router`.

## Quick Start

Prerequisite: install [OpenCode.ai](https://opencode.ai) first.

The installer defaults to the repository `main` branch.
PR merges to `main` become the default update path.

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
  "plugin": ["do-the-thing@git+https://github.com/chendaleiQ/do-the-thing.git#main"]
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

By default, reinstalling keeps you on `main`, so merged PRs become available on the normal update path.
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

## Track a Development Branch Reliably

If you want to test a remote development branch such as `dev`, using `#dev` directly may still hit a cached git dependency. To force OpenCode onto the latest remote `dev` commit, resolve the branch to its current commit SHA first and write that SHA into `opencode.json`.

### macOS / Linux

```bash
curl -fsSL https://raw.githubusercontent.com/chendaleiQ/do-the-thing/refs/heads/dev/install/opencode-dev-update.sh | bash
```

This script:

1. resolves remote `dev` to the latest commit SHA
2. reruns the normal OpenCode installer with `DTT_PLUGIN_REF=<resolved-sha>`
3. updates `~/.config/opencode/opencode.json`

Run it before starting OpenCode when you want the newest `dev` build.

If you use a different branch, set `DTT_DEV_REF`:

```bash
curl -fsSL https://raw.githubusercontent.com/chendaleiQ/do-the-thing/refs/heads/dev/install/opencode-dev-update.sh | DTT_DEV_REF=my-branch bash
```

If you want one command for update + launch, add an alias like:

```bash
alias opencode-dev='curl -fsSL https://raw.githubusercontent.com/chendaleiQ/do-the-thing/refs/heads/dev/install/opencode-dev-update.sh | bash && opencode'
```

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

This repo now treats `main` as the releasable default track. Keep development in PR branches, merge only releasable work to `main`, and use `DTT_PLUGIN_REF` only when you explicitly want to override that default.
