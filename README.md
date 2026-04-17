# do-the-thing

[English](./README.md) | [简体中文](./docs/README.zh-CN.md)

do-the-thing is a single-entry agent workflow plugin.
Install it once, start with `leader`, and let the system handle triage, delegation, review, verification, and closure.

## What This Is
- Single-entry workflow: start from `leader`
- Automatic routing: choose lane / tier by task complexity and risk
- Less manual overhead: you do not need to pick the agent or model first

## Platform Support
- OpenCode: supported, including `agent router`
- Claude Code: coming soon
- Cursor: coming soon
- Codex: coming soon

## How It Works
- Default entry: `leader`
- Low-risk local work can be delegated to faster tiers
- High-risk judgment, escalation, and final closure stay with higher tiers
- When `needsPlan=true`, work must stop for spec approval, then plan approval, before execution starts
- Planned artifacts live under `docs/dtt/specs/` and `docs/dtt/plans/`

## User Entry Flow
- default workflow entry: start with `leader`
- in hosts that expose agent switching, switch to `leader` once at the start of the session, then give the task directly
- after that, do not manually pick analyzer/implementer/reviewer unless `leader` explicitly tells you to
- for a fresh OpenCode install, the quick check is: `switch to leader and say ready`

## Installation

### OpenCode

One-command native install. By default, the installer follows the repository `main` branch.

macOS / Linux:

```bash
curl -fsSL https://raw.githubusercontent.com/chendaleiQ/do-the-thing/refs/heads/main/install/install.sh | bash -s -- opencode
```

Windows PowerShell:

```powershell
irm https://raw.githubusercontent.com/chendaleiQ/do-the-thing/refs/heads/main/install/install.ps1 | iex; Install-DoTheThing opencode
```

To pin a specific ref during reinstall, set `DTT_PLUGIN_REF` first.

For testing a remote development branch while avoiding stale git-plugin caches, use `install/opencode-dev-update.sh` from that branch to resolve the branch to its latest commit SHA before launching OpenCode.

Detailed docs: [`.opencode/INSTALL.md`](./.opencode/INSTALL.md)

### Claude Code

coming soon

### Cursor

coming soon

### Codex

coming soon

### Verify Installation

Restart OpenCode, start a new session, then run: `switch to leader and say ready`.

## Use
1. Switch to `leader`
2. Describe the task directly
3. Let the workflow handle routing, escalation, and closure

For planned work, `leader` keeps the spec/plan steps human-readable in the current conversation language while storing the artifacts under `docs/dtt/`.

Use `/providers` if you need to adjust the plugin-scoped provider allowlist.

## Project Docs
- Workflow: [`docs/WORKFLOW.md`](./docs/WORKFLOW.md)
- Architecture: [`docs/ARCHITECTURE.md`](./docs/ARCHITECTURE.md)
- Release: [`docs/RELEASE.md`](./docs/RELEASE.md)
- Maintenance: [`docs/MAINTAINING.md`](./docs/MAINTAINING.md)

## Who This Is For
- solo developers wanting low-friction automation
- teams needing consistent execution rules
- projects wanting a reusable workflow plugin
