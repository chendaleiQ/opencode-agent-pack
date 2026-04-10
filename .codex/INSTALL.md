# do-the-thing for Codex

Codex uses one-command install. `agent router` is not available.

## What Codex Gets

The installer links the pack's `skills/` directory into Codex's skill discovery path. This gives Codex access to the 11 built-in `dtt-*` method skills (brainstorming, change-triage, writing-plans, debugging, etc.).

**Note:** The full agent workflow (`leader` → `analyzer`/`implementer`/`reviewer` routing) requires agent definitions in `AGENTS.md` and `agents/`, which are not linked by this installer. Codex users can invoke the `dtt-*` skills individually but do not get the orchestrated single-entry workflow that OpenCode provides.

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

Start a new Codex session and try invoking a `dtt-*` skill directly (e.g., ask it to use `dtt-change-triage` on a task).

## Updating

Run the installer again to refresh the local clone and link.

## Uninstalling

Remove the `~/.agents/skills/do-the-thing` link/junction and then remove the local clone directory.
