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
- OpenCode: full plugin support, including `agent router`
- Cursor: workflow plugin support without `agent router`
- Claude Code: workflow plugin support without `agent router`
- Codex: workflow plugin support without `agent router`

`agent router` is currently OpenCode-only. Other platforms still use the same single-entry workflow, built-in method skills, and prompt system, but without native router integration.

It is **not**:
- a prompt snippet collection
- a single isolated skill
- a multi-entry agent menu

## Workflow at a Glance
- one strongest entry: `leader`
- automatic lane routing: `quick`, `standard`, `guarded`, `strict`
- built-in method skills for planning, debugging, review, verification, and execution
- optional model router for OpenCode environments

Detailed workflow docs:
- [`docs/project/WORKFLOW.md`](./docs/project/WORKFLOW.md)
- [`docs/project/ROUTER.md`](./docs/project/ROUTER.md)

## Installation

Platform installation differs slightly by host. OpenCode has full support, while Cursor, Claude Code, and Codex run without `agent router`.

### Claude Code

Tell Claude Code:

```text
Fetch and follow instructions from https://raw.githubusercontent.com/chendaleiQ/do-the-thing/refs/heads/main/.claude-plugin/README.md
```

Detailed docs: [`.claude-plugin/README.md`](./.claude-plugin/README.md)

### Cursor

In Cursor Agent chat, tell it:

```text
Fetch and follow instructions from https://raw.githubusercontent.com/chendaleiQ/do-the-thing/refs/heads/main/.cursor-plugin/README.md
```

Detailed docs: [`.cursor-plugin/README.md`](./.cursor-plugin/README.md)

### Codex

Tell Codex:

```text
Fetch and follow instructions from https://raw.githubusercontent.com/chendaleiQ/do-the-thing/refs/heads/main/.codex/INSTALL.md
```

Detailed docs: [`.codex/INSTALL.md`](./.codex/INSTALL.md)

### OpenCode

Tell OpenCode:

```text
Fetch and follow instructions from https://raw.githubusercontent.com/chendaleiQ/do-the-thing/refs/heads/main/.opencode/INSTALL.md
```

Detailed docs: [`.opencode/INSTALL.md`](./.opencode/INSTALL.md)

### Verify Installation

Start a new session in your chosen platform and ask for a task that should trigger workflow routing. The session should route through `leader`, use the built-in method skills, and only use `agent router` when running in OpenCode.

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
