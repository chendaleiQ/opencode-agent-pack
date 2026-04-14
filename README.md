# do-the-thing

[English](./README.md) | [简体中文](./docs/project/README.zh-CN.md)

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

Use `/providers` if you need to adjust the plugin-scoped provider allowlist.

## Project Docs
- Workflow: [`docs/project/WORKFLOW.md`](./docs/project/WORKFLOW.md)
- Router: [`docs/project/ROUTER.md`](./docs/project/ROUTER.md)
- Architecture: [`docs/project/V2-ARCHITECTURE.md`](./docs/project/V2-ARCHITECTURE.md)
- Release: [`docs/project/RELEASE.md`](./docs/project/RELEASE.md)
- Maintenance: [`docs/project/MAINTAINING.md`](./docs/project/MAINTAINING.md)

## Who This Is For
- solo developers wanting low-friction automation
- teams needing consistent execution rules
- projects wanting a reusable workflow plugin
