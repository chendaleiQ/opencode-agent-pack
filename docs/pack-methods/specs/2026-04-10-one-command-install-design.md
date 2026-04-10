# One-Command Install Design

**Goal:** Make `do-the-thing` installable through a one-command user experience on macOS, Linux, and Windows PowerShell for OpenCode, Claude Code, and Codex.

**Problem:** The repository currently mixes one real OpenCode install path with placeholder or high-friction install docs for other platforms. This makes platform support inconsistent and not aligned with the desired UX of “the simplest possible user install.”

**Approach:** Add cross-platform remote installers as the primary user-facing entrypoint. Users should install with a single command, while the installers hide the underlying clone, update, link, or platform-specific setup steps. OpenCode, Claude Code, and Codex will each map to a supported install mode behind the same installer interface. Cursor is not included in this implementation because current evidence only supports a bootstrap compatibility layer, not native-parity install support.

## Scope

In scope:
- add a Unix installer entrypoint for one-command installs
- add a PowerShell installer entrypoint for Windows installs
- support OpenCode, Claude Code, and Codex as installer targets
- add the missing Claude plugin manifest needed for Claude-native packaging
- update platform docs and README files to make the installer the primary user path
- add tests that verify one-command install docs and supported-platform wording

Out of scope:
- implementing Cursor installation
- replacing platform-native internals with a single shared runtime abstraction
- changing the repository’s core workflow payload (`AGENTS.md`, `agents/`, `skills/`, `commands/`, `tools/`)

## Design Principles

1. **User simplicity first**
   The main installation instructions must be one command per platform and OS family, even if the underlying implementation still uses clone, plugin, or symlink mechanics.

2. **Hide platform-specific complexity inside installers**
   The user should not need to understand repository layout, target directories, symlink rules, or update mechanics.

3. **Preserve native platform behavior where available**
   OpenCode should still use its plugin path, Claude should still use Claude plugin packaging, and Codex should still use its discoverable skills path.

4. **Do not overclaim Cursor support**
   Cursor may be installable later through a bootstrap compatibility layer, but that is not equivalent to the supported platforms in this phase.

## Proposed Files

### New

- `install/install.sh`
  Unix installer entrypoint for macOS and Linux.

- `install/install.ps1`
  Windows PowerShell installer entrypoint.

- `.claude-plugin/plugin.json`
  Claude plugin manifest.

### Modified

- `.opencode/INSTALL.md`
- `.claude-plugin/README.md`
- `.codex/INSTALL.md`
- `README.md`
- `docs/project/README.zh-CN.md`
- `tests/test_platform_install_docs.py`

## Installer Interface

### Unix

Users should install with:

```bash
curl -fsSL <raw-install-sh-url> | bash -s -- <platform>
```

Supported `<platform>` values in this phase:
- `opencode`
- `claude`
- `codex`

### Windows PowerShell

Users should install with:

```powershell
irm <raw-install-ps1-url> | iex; Install-DoTheThing <platform>
```

Supported `<platform>` values in this phase:
- `opencode`
- `claude`
- `codex`

The installer output should always include:
- where the repository was installed
- how to verify installation
- how to update
- how to uninstall

## Platform-Specific Internal Behavior

### OpenCode

The installer should:
- install or update the repository into a stable local path
- configure the OpenCode plugin path expected by the existing install model
- keep the underlying OpenCode plugin mechanism intact

OpenCode documentation should present the one-command installer as the primary path and keep the existing native details as secondary reference material if needed.

### Claude Code

The installer should:
- install or update the repository into a stable local path
- ensure `.claude-plugin/plugin.json` exists and is valid
- configure usage around Claude’s plugin loading model

Claude documentation should present the one-command installer as the primary path. The lower-level plugin details should remain documented as implementation detail or fallback guidance.

### Codex

The installer should:
- install or update the repository into a stable local path
- create the required discovery link into the Codex/agent skill discovery location
- use a symlink on Unix and junction-compatible behavior on Windows

Codex documentation should present the one-command installer as the main path, while still documenting the underlying clone-plus-link behavior for transparency and troubleshooting.

## Cursor Assessment

Cursor currently appears technically compatible only through bootstrap-style installation into repo-local Cursor config surfaces such as `.cursor/rules/*.mdc`, `.cursor/mcp.json`, or `.cursor/settings.json`.

That means Cursor may support a one-command installer in the future, but it would be a compatibility install rather than true native parity. This work should therefore document Cursor as deferred rather than supported.

## Verification Model

Repository-level verification should prove that:

1. the one-command installer files exist for Unix and PowerShell
2. `.claude-plugin/plugin.json` exists
3. OpenCode, Claude, and Codex docs all present one-command install entrypoints
4. README and Chinese README reflect OpenCode + Claude + Codex as supported installer targets
5. Cursor is explicitly marked deferred / under investigation

## Risks and Mitigations

### Risk: platform internals differ too much for one visible install UX
Mitigation: keep the user interface unified but let each target branch internally.

### Risk: PowerShell and shell installers drift apart
Mitigation: keep target names, messaging, and verification output parallel across both installers.

### Risk: Claude plugin loading may still need a manual launch detail
Mitigation: document the one-command install as the setup step, then provide the shortest possible post-install usage guidance.

### Risk: Cursor expectations remain high after docs changes
Mitigation: explicitly state Cursor is not yet implemented in both English and Chinese docs.

## Success Criteria

This work is successful when:

- OpenCode, Claude Code, and Codex each have a one-command documented install path on Unix and Windows
- the repository contains installer entrypoints for shell and PowerShell
- Claude has a valid plugin manifest
- README language matches actual supported platforms
- Cursor is documented as deferred rather than implied to be already installable
