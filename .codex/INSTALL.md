# do-the-thing for Codex

Codex uses one-command install. `agent router` is not available.

## One-Command Install

### macOS / Linux

```bash
curl -fsSL https://raw.githubusercontent.com/chendaleiQ/do-the-thing/refs/heads/main/install/install.sh | bash -s -- codex
```

### Windows PowerShell

```powershell
irm https://raw.githubusercontent.com/chendaleiQ/do-the-thing/refs/heads/main/install/install.ps1 | iex; Install-DoTheThing codex
```

## Under the Hood

The installer clones the repository locally, then wires Codex discovery to the `skills/` directory.

Unix reference:

```bash
ln -s ~/.local/share/do-the-thing/skills ~/.agents/skills/do-the-thing
```

Windows reference:

```powershell
cmd /c mklink /J "$env:USERPROFILE\.agents\skills\do-the-thing" "$env:USERPROFILE\.local\share\do-the-thing\skills"
```

## Verify Installation

```bash
ls -la ~/.agents/skills/do-the-thing
```

Start a new Codex session and ask for a task that should trigger the single-entry workflow. The session should route through `leader`, use built-in method skills, and operate without `agent router`.

## Updating

Run the installer again to refresh the local clone and link.

## Uninstalling

Remove the `~/.agents/skills/do-the-thing` link/junction and then remove the local clone directory.
