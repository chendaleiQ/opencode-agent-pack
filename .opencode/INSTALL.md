# do-the-thing for OpenCode

OpenCode uses one-command native install and supports `agent router`.

> Current default: the installer pins OpenCode to the final pre-hooks V1 release, `v1.4.0-pre-hooks`.

## Prerequisites

- [OpenCode.ai](https://opencode.ai) installed

## One-Command Install

### macOS / Linux

```bash
curl -fsSL https://raw.githubusercontent.com/chendaleiQ/do-the-thing/refs/heads/main/install/install.sh | bash -s -- opencode
```

This writes the following plugin entry by default:

```json
{
  "plugin": ["do-the-thing@git+https://github.com/chendaleiQ/do-the-thing.git#v1.4.0-pre-hooks"]
}
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
  "plugin": ["do-the-thing@git+https://github.com/chendaleiQ/do-the-thing.git#v1.4.0-pre-hooks"]
}
```

Restart OpenCode. That's it - the plugin auto-installs from GitHub, syncs the workflow files into your OpenCode config directory, and registers the built-in skills. Pack-owned built-in skills use a `dtt-` prefix to avoid collisions with similarly named external Superpowers skills.

## Why OpenCode defaults to V1 today

The installer currently defaults to the final pre-hooks V1 release so OpenCode users get the stable single-entry workflow baseline while the hook-enforced V2 line is documented and developed separately.

The default V1 install **does not include the OpenCode V2 runtime guard**. It is the stable pre-hooks line.

If you want to track a different tag, branch, or commit, set `DTT_PLUGIN_REF` before reinstalling.

## V2 Architecture Track

V2 is being defined as a **leader-first, state-machine-centered, hook-enforced** architecture.

See [`../docs/project/V2-ARCHITECTURE.md`](../docs/project/V2-ARCHITECTURE.md) for the architecture blueprint.

## OpenCode Runtime Guard (future V2 direction)

The V2 direction for OpenCode keeps the single-entry model and adds a stronger runtime guard layer that is expected to cover:

- blocks obvious workflow bypasses like `git commit --no-verify`
- blocks edits to protected lint/formatter config files
- tracks entry-driven workflow state and phase transitions
- records layered evidence for triage, review, verification, and manual checks
- tracks evidence staleness (re-verification required after file edits)
- operates in profile modes: minimal (audit-only), standard (full guard), strict (all evidence required)
- records workflow state for each session
- injects workflow-state reminders into the system prompt
- writes audit records for important workflow events
- provides audit statistics aggregation
- blocks final close attempts when required evidence is missing

Formal command verification is preferred, but explicit manual verification notes remain valid when no formal verify command exists.

Runtime data is stored under your OpenCode config directory:

- workflow state: `~/.config/opencode/do-the-thing/sessions/`
- audit logs: `~/.config/opencode/do-the-thing/audit/`

This runtime guard direction is intentionally lightweight and dependency-free. Codex continues to receive the built-in method skills, but not the OpenCode runtime guard, workflow state, or audit layer.

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

### Default V1 install

1. Check that `opencode.json` contains the pinned plugin entry
2. Restart OpenCode
3. Start a new session and confirm the workflow still routes through `leader`

The default V1 install should not be validated by looking for V2 runtime guard state, audit logs, or evidence-gate artifacts.

### Optional V2 track

Start a new OpenCode session and ask for a task that should trigger workflow routing. The session should route through `leader`, use the built-in method skills, keep `agent router` available, and create runtime guard state under `~/.config/opencode/do-the-thing/`.

## Updating

Run the one-command installer again to update the configured `do-the-thing` plugin entry in place. The installer replaces any existing `do-the-thing@...` entries, dedupes repeated entries, and leaves unrelated plugins unchanged. Set `DTT_PLUGIN_REF` before rerunning if you want to move to a specific tag, branch, or commit, then restart OpenCode.

## Troubleshooting

1. Check that the `plugin` line exists in your `opencode.json`
2. If needed, rerun the installer with `DTT_PLUGIN_REF=<ref>` to replace stale `do-the-thing` entries
3. Restart OpenCode after adding or changing the plugin line
4. For the default V1 install, stop after confirming `leader` routing and the pinned plugin entry
5. Only V2-track installs should expect `~/.config/opencode/do-the-thing/` runtime state or audit files
