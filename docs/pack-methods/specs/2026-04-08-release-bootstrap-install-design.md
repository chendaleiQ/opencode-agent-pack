# Release Bootstrap Install Design

## Summary
Add a true one-command install path that does not require cloning the repository. The default install entry becomes a remote bootstrap script that downloads a versioned GitHub Release artifact, extracts it to a temporary directory, and then invokes the existing local installer.

## Background
The current installation flow assumes the user already has the repository checked out locally:

- `bash install.sh`
- `./install.ps1`

That works for contributors and local testing, but it is a poor default user experience because first-time users must manually clone the repository before they can install the pack.

The project already has working local installers with important behavior:

- install into `~/.config/opencode/` by default
- support `--target` / `-Target`
- support `--force` / `-Force`
- preserve `opencode.json` and `settings.json`
- configure the pack-scoped provider allowlist
- set `leader` as the default agent

Those behaviors should remain the source of truth for installation. The new work is about distribution and entrypoint simplification, not rewriting installation logic.

## Goals
- Let a user install without cloning the repository.
- Make the default documented install path a single `curl/bash` command.
- Download only fixed, release-backed versions by default.
- Keep the existing local installer as the canonical installer implementation.
- Support both Unix shell and PowerShell bootstrap entrypoints.

## Non-Goals
- Do not add package manager support in this change.
- Do not make the bootstrap script install directly from the moving default branch.
- Do not duplicate provider/config merge logic into the bootstrap layer.
- Do not remove the existing local install scripts from the repository.

## Chosen Approach

### Recommended Flow
Use a two-layer install design:

1. A small remote bootstrap script is the public one-command entrypoint.
2. The bootstrap script downloads a GitHub Release artifact for a fixed version.
3. The bootstrap script extracts the artifact into a temporary directory.
4. The bootstrap script calls the packaged local installer from that extracted directory.
5. The local installer performs the real install into the final target.

This keeps network/download concerns separate from installation concerns.

## Alternatives Considered

### 1. Download repository archive by tag
Pros:
- simpler than managing explicit release artifacts
- still versionable

Cons:
- less explicit than GitHub Releases as an official distribution channel
- weaker release story for users who expect installable assets
- more closely tied to source distribution than product distribution

### 2. Separate dedicated installer/bootstrap repository
Pros:
- flexible for future package manager expansion
- clear separation between product and installer assets

Cons:
- too much maintenance overhead for the current project size
- introduces an additional publishing surface immediately

### 3. Put all download logic directly into `install.sh` and `install.ps1`
Pros:
- fewer top-level scripts

Cons:
- mixes distribution logic into the installer
- makes local testing and packaging harder to reason about
- increases cross-platform duplication

## Distribution Design

### Release Artifacts
Each GitHub Release should publish installable archives:

- `do-the-thing-<version>.tar.gz`
- `do-the-thing-<version>.zip`

The archive contents should include the files required for local installation:

- `pack/`
- `install.sh`
- `install.ps1`

Optional metadata may be included if useful for bootstrap validation, but it should not be required for the initial version.

### Bootstrap Entry Scripts
Add lightweight bootstrap scripts intended for remote execution:

- `bootstrap/install.sh`
- `bootstrap/install.ps1`

Responsibilities:
- resolve the requested version
- construct the correct GitHub Release asset URL
- download the release archive
- extract it into a temporary directory
- invoke the packaged local installer with pass-through arguments
- clean up temporary files

Non-responsibilities:
- provider allowlist prompting
- config file merge logic
- direct writes into final install config

Those responsibilities stay in the packaged local installer.

## Version Policy

### Default Version Resolution
The bootstrap installer should default to a fixed release version, not repository HEAD.

Acceptable initial strategies:
- explicit version argument is required, or
- bootstrap script resolves "latest" by querying GitHub Releases and then downloads the corresponding tagged asset

The user requirement here is that installation must be backed by GitHub Release artifacts rather than cloning or pulling from an unfixed branch state.

For the initial implementation, the simplest acceptable product behavior is:
- no clone required
- release-backed artifact download only
- reproducible by version when a version is specified

## Installer Boundary

### Local Installer Remains Canonical
Keep `install.sh` and `install.ps1` as the canonical installers for actual target mutation.

That means:
- bootstrap downloads and unpacks
- local installer validates target state
- local installer preserves config files
- local installer writes `settings.json` and `opencode.json`

This avoids splitting install behavior across multiple layers.

### Expected Invocation Shape
After extraction, bootstrap should run the packaged installer from the extracted artifact root so existing relative paths continue to work.

For Unix-like systems, the bootstrap path should be conceptually equivalent to:

```bash
tmpdir=...
tar -xzf release.tar.gz -C "$tmpdir"
bash "$tmpdir/install.sh" "$@"
```

For PowerShell, the bootstrap path should be conceptually equivalent to:

```powershell
$tmp = ...
Expand-Archive ...
& "$tmp\install.ps1" @args
```

## README Changes

### Default Install Section
The README and Chinese README should promote one-command install first.

Target shape:

```bash
curl -fsSL <bootstrap-url> | bash
```

PowerShell:

```powershell
irm <bootstrap-url> | iex
```

### Secondary Install Paths
Keep local installer usage documented, but demote it to:
- manual install
- offline install
- contributor/developer workflow

### Messaging Shift
The docs should explicitly say users do not need to clone the repository to install.

## Failure Handling

### Bootstrap Failures
Bootstrap should fail clearly when:
- release asset cannot be found
- download fails
- archive extraction fails
- packaged installer is missing from the archive

Messages should point at the release/version problem, not imply the user should clone the repo.

### Local Installer Failures
Once bootstrap hands off to the packaged installer, current installer behavior remains authoritative, including:
- refusing non-empty targets without force
- provider selection behavior
- config preservation

## Testing Strategy

### Unit/Integration Coverage
Add tests that cover:
- bootstrap URL/version resolution logic where practical
- bootstrap invoking packaged installer from an extracted archive layout
- release artifact layout contains required files
- README examples align with the shipped bootstrap entrypoints

### Regression Focus
Keep existing installer tests to ensure the bootstrap change does not alter:
- `opencode.json` merge behavior
- `settings.json` preservation
- provider allowlist behavior
- default agent behavior

## Risks
- The project needs a reliable release packaging step; otherwise the documented install command will rot.
- Remote bootstrap adds network and archive-format failure modes that the current local-only flow does not have.
- A `curl | bash` entrypoint must stay small and auditable to avoid becoming a second full installer.

## Acceptance Criteria
- A first-time user can install without cloning the repository.
- The default documented install path downloads from GitHub Release artifacts.
- The bootstrap script only handles fetch/extract/hand-off concerns.
- The existing local installers remain the only place that mutates installed config.
- README and `README.zh-CN.md` document the new one-command install flow first.
- Manual local installation remains available as a secondary path.

## Deferred Work
- Homebrew support
- npm support
- pip support
- signed artifact verification
- explicit channel selection such as stable vs prerelease
