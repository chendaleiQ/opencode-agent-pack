# do-the-thing for Claude Code

Claude Code is supported in compatibility mode. The workflow plugin is available, but `agent router` is not.

Tell Claude Code:

```text
Fetch and follow instructions from https://raw.githubusercontent.com/chendaleiQ/do-the-thing/refs/heads/main/.claude-plugin/README.md
```

## Install

Use the GitHub-hosted plugin instructions as the source of truth for the workflow prompts and plugin files. Claude Code should use the same single-entry workflow and built-in method skills, but not `agent router`.

## Verify Installation

Start a new Claude Code session and ask for a task that should trigger workflow routing. The session should route through `leader` and use the built-in method skills.
