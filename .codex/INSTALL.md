# do-the-thing for Codex

Codex is supported in compatibility mode. The workflow plugin is available, but `agent router` is not.

Tell Codex:

```text
Fetch and follow instructions from https://raw.githubusercontent.com/chendaleiQ/do-the-thing/refs/heads/main/.codex/INSTALL.md
```

## Install

Codex should use the GitHub-hosted plugin files and workflow prompts, but must not rely on `agent router`.

## Verify Installation

Start a new Codex session and ask for a task that should trigger the single-entry workflow. The session should route through `leader`, use built-in method skills, and operate without `agent router`.
