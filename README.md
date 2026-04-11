# do-the-thing

[English](./README.md) | [简体中文](./docs/project/README.zh-CN.md)

do-the-thing is a cross-platform agent workflow plugin.
Install once, then only talk to one default strongest entry agent: `leader`.
The documented workflow routes triage, delegation, escalation, review, verification, and final closure through that single entry.

Tell one agent the task, let the system handle the rest.

## What Problem This Solves
Most multi-agent setups force users to manually decide:
- which model to use
- which agent to call
- whether a task is risky
- whether to run fast path or strict path

This plugin removes that burden at the workflow level:
- you give one task to `leader`
- do-the-thing defines how triage, lane routing, tier routing, subagent dispatch, review/verify, escalation, and final closure should happen

## Core Positioning
This is **do-the-thing**: a single-entry agent workflow plugin with automatic lane+tier routing.

## Platform Support
- OpenCode: one-command native install, including `agent router`
- Cursor: deferred
- Claude Code: deferred
- Codex: one-command install

`agent router` is currently OpenCode-only. Codex uses the same built-in method skills but without native router integration. OpenCode also provides the runtime guard layer for workflow state, audit logging, profile-based enforcement modes, evidence staleness tracking, and close-time evidence gating. Claude Code and Cursor remain deferred.

It is **not**:
- a prompt snippet collection
- a single isolated skill
- a multi-entry agent menu

## Workflow at a Glance
- one strongest entry: `leader`
- automatic lane routing: `quick`, `standard`, `guarded`, `strict`
- entry-driven workflow state so different task entry shapes can follow different safe paths
- layered evidence model for triage, review, verification, and manual checks
- built-in method skills for planning, debugging, review, verification, and execution
- OpenCode runtime guard for workflow state, audit logs, profile modes (minimal/standard/strict), evidence staleness, and close-time evidence gating
- pack-owned built-in skills use a `dtt-` prefix to avoid collisions with similarly named external Superpowers skills
- optional model router for OpenCode environments

Detailed workflow docs:
- [`docs/project/WORKFLOW.md`](./docs/project/WORKFLOW.md)
- [`docs/project/ROUTER.md`](./docs/project/ROUTER.md)

## Installation

Platform installation is one-command first for supported targets.

### Claude Code

Deferred.

Claude Code currently requires `--plugin-dir` on every invocation, which cannot be persisted. Install support is deferred until a persistent plugin registration mechanism is available.

Detailed docs: [`.claude-plugin/README.md`](./.claude-plugin/README.md)

### Cursor

Deferred.

Cursor support is under investigation and is not included in the supported one-command installer targets yet.

Detailed docs: [`.cursor-plugin/README.md`](./.cursor-plugin/README.md)

### Codex

One-command install.

macOS / Linux:

```bash
curl -fsSL https://raw.githubusercontent.com/chendaleiQ/do-the-thing/refs/heads/main/install/install.sh | bash -s -- codex
```

Windows PowerShell:

```powershell
irm https://raw.githubusercontent.com/chendaleiQ/do-the-thing/refs/heads/main/install/install.ps1 | iex; Install-DoTheThing codex
```

Detailed docs: [`.codex/INSTALL.md`](./.codex/INSTALL.md)

### OpenCode

One-command native install.

The installer defaults OpenCode to the repository `main` branch.

macOS / Linux:

```bash
curl -fsSL https://raw.githubusercontent.com/chendaleiQ/do-the-thing/refs/heads/main/install/install.sh | bash -s -- opencode
```

Windows PowerShell:

```powershell
irm https://raw.githubusercontent.com/chendaleiQ/do-the-thing/refs/heads/main/install/install.ps1 | iex; Install-DoTheThing opencode
```

Merged PRs to `main` become the default update path. To replace that default with a specific pin while reinstalling, set `DTT_PLUGIN_REF` before running the installer again.

Detailed docs: [`.opencode/INSTALL.md`](./.opencode/INSTALL.md)

V2 architecture blueprint: [`docs/project/V2-ARCHITECTURE.md`](./docs/project/V2-ARCHITECTURE.md)

### Verify Installation

Restart OpenCode, start a new session, then run: `switch to leader and say ready`.
The session should route through `leader`, use the built-in method skills, and keep `agent router` available in OpenCode.

## Use

After install, user workflow is intentionally simple:
1. switch to `leader` agent, then ask task directly
2. `leader` handles triage/routing/escalation within the documented workflow
3. `leader` provides the final closure summary after review/end-gate checks
4. use `/providers` whenever you want to update the plugin-scoped provider allowlist

## Project Docs
- Workflow details: [`docs/project/WORKFLOW.md`](./docs/project/WORKFLOW.md)
- Router details: [`docs/project/ROUTER.md`](./docs/project/ROUTER.md)
- Release policy: [`docs/project/RELEASE.md`](./docs/project/RELEASE.md)
- Maintenance guide: [`docs/project/MAINTAINING.md`](./docs/project/MAINTAINING.md)

## Who This Is For
- solo developers wanting low-friction automation
- teams needing consistent safe routing rules
- OSS repos wanting a reusable default automation plugin
- internal engineering orgs standardizing task execution policy

## Directory Structure
```text
do-the-thing/
├─ README.md
├─ docs/
│  ├─ project/
│  │  ├─ README.zh-CN.md
│  │  ├─ RELEASE.md
│  │  └─ MAINTAINING.md
│  └─ pack-methods/
├─ LICENSE
├─ evals/
│  ├─ README.md
│  ├─ rubric.md
│  └─ cases/
├─ .opencode/
├─ .codex/
├─ .cursor-plugin/
├─ .claude-plugin/
├─ AGENTS.md
├─ agents/
├─ commands/
├─ skills/
└─ tools/
```
