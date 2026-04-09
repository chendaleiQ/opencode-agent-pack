# do-the-thing for Cursor

Cursor is supported in compatibility mode. The workflow plugin is available, but `agent router` is not.

In Cursor Agent chat, tell it:

```text
Fetch and follow instructions from https://raw.githubusercontent.com/chendaleiQ/do-the-thing/refs/heads/main/.cursor-plugin/README.md
```

## Install

Use the GitHub-hosted plugin instructions as the source of truth for the workflow prompts and plugin files. Cursor should use the same single-entry workflow and built-in method skills, but not `agent router`.

## Verify Installation

Start a new Cursor agent session and ask for a task that should trigger workflow routing. The session should route through `leader` and use the built-in method skills.
