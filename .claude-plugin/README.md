# do-the-thing for Claude Code

Claude Code uses one-command native install. `agent router` is not available.

## One-Command Install

### macOS / Linux

```bash
curl -fsSL https://raw.githubusercontent.com/chendaleiQ/do-the-thing/refs/heads/main/install/install.sh | bash -s -- claude
```

### Windows PowerShell

```powershell
irm https://raw.githubusercontent.com/chendaleiQ/do-the-thing/refs/heads/main/install/install.ps1 | iex; Install-DoTheThing claude
```

## Native Plugin Details

The repository root is the Claude plugin directory. Its plugin manifest lives at `.claude-plugin/plugin.json` inside that root.

The installer clones the repository into a stable local directory and prints the shortest supported usage guidance:

```bash
claude --plugin-dir ~/.local/share/do-the-thing
```

## Verify Installation

Start a new Claude Code session and ask for a task that should trigger workflow routing. The session should route through `leader` and use the built-in method skills.

## Updating

Run the installer again to refresh the local clone.

## Uninstalling

Remove the local clone directory created by the installer.
