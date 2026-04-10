# do-the-thing for Claude Code

Claude Code support is **deferred**.

## Why Deferred

Claude Code currently requires `--plugin-dir` to be passed on every invocation. There is no persistent plugin registration mechanism, so the plugin directory cannot be saved across sessions.

Until Claude Code adds a way to persistently register a plugin directory, the one-command installer does not include a `claude` target.

## Manual Usage (Advanced)

If you still want to use the plugin manually, clone the repository and pass the directory each time:

```bash
git clone https://github.com/chendaleiQ/do-the-thing.git ~/.local/share/do-the-thing
claude --plugin-dir ~/.local/share/do-the-thing
```

The plugin manifest lives at `.claude-plugin/plugin.json` inside the repository root.

## Status

This page will be updated when Claude Code provides persistent plugin registration.
