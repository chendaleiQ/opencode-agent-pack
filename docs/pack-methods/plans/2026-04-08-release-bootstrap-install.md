# Release Bootstrap Install Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a release-backed one-command install flow that lets users install `opencode-agent-pack` without cloning the repository.

**Architecture:** Keep `install.sh` and `install.ps1` as the canonical installers that mutate the target directory. Add a small bootstrap layer for shell and PowerShell that only resolves a GitHub Release asset, downloads and extracts it, then hands off to the packaged local installer. Add a small Python helper for URL/layout validation so the bootstrap logic stays thin and testable, then document the new install flow first in both READMEs.

**Tech Stack:** Bash, PowerShell, Python 3, `unittest`, GitHub Release artifacts, existing installer scripts

---

## File Structure

- Create: `bootstrap/install.sh`
  Public Unix bootstrap entrypoint for remote `curl ... | bash` usage. Downloads a release artifact, extracts it, invokes packaged `install.sh`.
- Create: `bootstrap/install.ps1`
  Public Windows bootstrap entrypoint for remote `irm ... | iex` usage. Downloads a release artifact, extracts it, invokes packaged `install.ps1`.
- Create: `pack/tools/release_bootstrap.py`
  Shared Python helper for release URL construction, archive-layout validation, and basic argument parsing helpers that are easier to test in Python than in shell.
- Create: `pack/tools/release_package.py`
  Local packaging helper that builds `.tar.gz` and `.zip` release artifacts from the repository root and validates required contents.
- Create: `tests/test_release_bootstrap.py`
  Unit tests for release asset URL resolution and extracted archive validation.
- Create: `tests/test_release_package.py`
  Tests for generated archive contents and required file validation.
- Modify: `README.md`
  Promote one-command install and demote local clone-based installation to a manual/developer path.
- Modify: `README.zh-CN.md`
  Chinese documentation update matching the new default install path.
- Modify: `RELEASE.md`
  Document the release artifact requirement and minimum release check for bootstrap assets.

### Task 1: Add Testable Release Bootstrap Helpers

**Files:**
- Create: `pack/tools/release_bootstrap.py`
- Test: `tests/test_release_bootstrap.py`

- [ ] **Step 1: Write the failing tests for release URL resolution and extracted layout validation**

```python
import tempfile
import unittest
from pathlib import Path

from pack.tools.release_bootstrap import (
    build_release_asset_url,
    validate_extracted_release,
)


class ReleaseBootstrapTests(unittest.TestCase):
    def test_build_release_asset_url_for_tarball(self):
        self.assertEqual(
            build_release_asset_url(
                repo="chendaleiQ/opencode-agent-pack",
                version="v1.2.3",
                archive_format="tar.gz",
            ),
            "https://github.com/chendaleiQ/opencode-agent-pack/releases/download/v1.2.3/opencode-agent-pack-v1.2.3.tar.gz",
        )

    def test_validate_extracted_release_requires_packaged_installers(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "pack").mkdir()
            (root / "pack" / "AGENTS.md").write_text("agents", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "missing required release files"):
                validate_extracted_release(root)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python3 -m unittest tests.test_release_bootstrap -v`
Expected: FAIL with `ModuleNotFoundError` or missing symbol errors for `pack.tools.release_bootstrap`.

- [ ] **Step 3: Write the minimal helper implementation**

```python
from pathlib import Path


RELEASE_BASENAME = "opencode-agent-pack"
REQUIRED_RELEASE_FILES = ("install.sh", "install.ps1", "pack")


def build_release_asset_url(repo: str, version: str, archive_format: str) -> str:
    filename = f"{RELEASE_BASENAME}-{version}.{archive_format}"
    return f"https://github.com/{repo}/releases/download/{version}/{filename}"


def validate_extracted_release(root: Path) -> Path:
    missing = [name for name in REQUIRED_RELEASE_FILES if not (root / name).exists()]
    if missing:
        raise ValueError(f"missing required release files: {', '.join(missing)}")
    return root
```

- [ ] **Step 4: Expand the helper to support both archive naming and nested archive roots**

```python
from pathlib import Path


RELEASE_BASENAME = "opencode-agent-pack"
REQUIRED_RELEASE_FILES = ("install.sh", "install.ps1", "pack")


def build_release_asset_filename(version: str, archive_format: str) -> str:
    if archive_format not in {"tar.gz", "zip"}:
        raise ValueError("unsupported archive format")
    return f"{RELEASE_BASENAME}-{version}.{archive_format}"


def build_release_asset_url(repo: str, version: str, archive_format: str) -> str:
    filename = build_release_asset_filename(version, archive_format)
    return f"https://github.com/{repo}/releases/download/{version}/{filename}"


def validate_extracted_release(root: Path) -> Path:
    candidates = [root]
    candidates.extend(path for path in root.iterdir() if path.is_dir())

    for candidate in candidates:
        missing = [name for name in REQUIRED_RELEASE_FILES if not (candidate / name).exists()]
        if not missing:
            return candidate

    raise ValueError(
        "missing required release files: install.sh, install.ps1, pack"
    )
```

- [ ] **Step 5: Re-run the tests and make them pass**

Run: `python3 -m unittest tests.test_release_bootstrap -v`
Expected: PASS for the new helper tests.

- [ ] **Step 6: Commit the helper layer**

```bash
git add pack/tools/release_bootstrap.py tests/test_release_bootstrap.py
git commit -m "feat: add release bootstrap helpers"
```

### Task 2: Add the Shell and PowerShell Bootstrap Entry Scripts

**Files:**
- Create: `bootstrap/install.sh`
- Create: `bootstrap/install.ps1`
- Modify: `tests/test_release_bootstrap.py`

- [ ] **Step 1: Add failing tests for bootstrap argument handling and packaged installer lookup**

```python
import unittest

from pack.tools.release_bootstrap import build_release_asset_filename


class ReleaseBootstrapScriptShapeTests(unittest.TestCase):
    def test_build_release_asset_filename_for_zip(self):
        self.assertEqual(
            build_release_asset_filename("v1.2.3", "zip"),
            "opencode-agent-pack-v1.2.3.zip",
        )
```

- [ ] **Step 2: Run the tests to verify the helper surface is still incomplete**

Run: `python3 -m unittest tests.test_release_bootstrap -v`
Expected: FAIL if `build_release_asset_filename` is not yet exposed or validated.

- [ ] **Step 3: Create the Unix bootstrap script with download, extract, and hand-off flow**

```bash
#!/usr/bin/env bash
set -euo pipefail

REPO="chendaleiQ/opencode-agent-pack"
PYTHON_BIN="${PYTHON_BIN:-python3}"
VERSION="${OPENCODE_AGENT_PACK_VERSION:-latest}"

tmpdir="$(mktemp -d "${TMPDIR:-/tmp}/opencode-agent-pack.XXXXXX")"
cleanup() {
  rm -rf "$tmpdir"
}
trap cleanup EXIT

if [ "$VERSION" = "latest" ]; then
  echo "Error: bootstrap latest resolution is not implemented yet. Set OPENCODE_AGENT_PACK_VERSION=vX.Y.Z." >&2
  exit 1
fi

asset_url="$($PYTHON_BIN -c 'from pack.tools.release_bootstrap import build_release_asset_url; import sys; print(build_release_asset_url(sys.argv[1], sys.argv[2], "tar.gz"))' "$REPO" "$VERSION")"
archive_path="$tmpdir/release.tar.gz"

curl -fsSL "$asset_url" -o "$archive_path"
tar -xzf "$archive_path" -C "$tmpdir"
release_root="$($PYTHON_BIN -c 'from pathlib import Path; from pack.tools.release_bootstrap import validate_extracted_release; import sys; print(validate_extracted_release(Path(sys.argv[1])))' "$tmpdir")"

bash "$release_root/install.sh" "$@"
```

- [ ] **Step 4: Create the PowerShell bootstrap script with the same hand-off boundary**

```powershell
$ErrorActionPreference = "Stop"

$Repo = "chendaleiQ/opencode-agent-pack"
$Version = if ($env:OPENCODE_AGENT_PACK_VERSION) { $env:OPENCODE_AGENT_PACK_VERSION } else { "latest" }
$Python = if ($env:PYTHON_BIN) { $env:PYTHON_BIN } else { "python3" }
$TempRoot = Join-Path ([System.IO.Path]::GetTempPath()) ([System.Guid]::NewGuid().ToString())
New-Item -ItemType Directory -Path $TempRoot | Out-Null

try {
    if ($Version -eq "latest") {
        throw "bootstrap latest resolution is not implemented yet. Set OPENCODE_AGENT_PACK_VERSION=vX.Y.Z."
    }

    $AssetUrl = & $Python -c "from pack.tools.release_bootstrap import build_release_asset_url; import sys; print(build_release_asset_url(sys.argv[1], sys.argv[2], 'zip'))" $Repo $Version
    $ArchivePath = Join-Path $TempRoot "release.zip"

    Invoke-WebRequest -Uri $AssetUrl -OutFile $ArchivePath
    Expand-Archive -Path $ArchivePath -DestinationPath $TempRoot -Force

    $ReleaseRoot = & $Python -c "from pathlib import Path; from pack.tools.release_bootstrap import validate_extracted_release; import sys; print(validate_extracted_release(Path(sys.argv[1])))" $TempRoot
    & (Join-Path $ReleaseRoot "install.ps1") @args
}
finally {
    Remove-Item -Path $TempRoot -Recurse -Force -ErrorAction SilentlyContinue
}
```

- [ ] **Step 5: Tighten the scripts to avoid importing repo-local Python modules from a remote pipe context**

```bash
helper_path="$tmpdir/release_bootstrap.py"
curl -fsSL "https://raw.githubusercontent.com/chendaleiQ/opencode-agent-pack/${VERSION}/pack/tools/release_bootstrap.py" -o "$helper_path"
asset_url="$($PYTHON_BIN "$helper_path" --repo "$REPO" --version "$VERSION" --archive-format tar.gz --print-asset-url)"
release_root="$($PYTHON_BIN "$helper_path" --validate-extracted-root "$tmpdir")"
```

```powershell
$HelperPath = Join-Path $TempRoot "release_bootstrap.py"
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/chendaleiQ/opencode-agent-pack/$Version/pack/tools/release_bootstrap.py" -OutFile $HelperPath
$AssetUrl = & $Python $HelperPath --repo $Repo --version $Version --archive-format zip --print-asset-url
$ReleaseRoot = & $Python $HelperPath --validate-extracted-root $TempRoot
```

- [ ] **Step 6: Re-run helper tests and do a basic script syntax check**

Run: `python3 -m unittest tests.test_release_bootstrap -v`
Expected: PASS

Run: `bash -n bootstrap/install.sh`
Expected: no output

Run: `pwsh -NoProfile -Command "[void][System.Management.Automation.Language.Parser]::ParseFile('bootstrap/install.ps1', [ref]$null, [ref]$null)"`
Expected: no output

- [ ] **Step 7: Commit the bootstrap entrypoints**

```bash
git add bootstrap/install.sh bootstrap/install.ps1 pack/tools/release_bootstrap.py tests/test_release_bootstrap.py
git commit -m "feat: add release bootstrap installers"
```

### Task 3: Add Release Packaging Support

**Files:**
- Create: `pack/tools/release_package.py`
- Create: `tests/test_release_package.py`
- Modify: `RELEASE.md`

- [ ] **Step 1: Write failing tests for release artifact contents**

```python
import tarfile
import tempfile
import unittest
import zipfile
from pathlib import Path

from pack.tools.release_package import build_release_archives


class ReleasePackageTests(unittest.TestCase):
    def test_build_release_archives_include_required_files(self):
        repo_root = Path(__file__).resolve().parents[1]

        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp)
            tar_path, zip_path = build_release_archives(repo_root, out_dir, "v1.2.3")

            with tarfile.open(tar_path, "r:gz") as tar:
                names = tar.getnames()
            with zipfile.ZipFile(zip_path) as archive:
                zip_names = archive.namelist()

            self.assertIn("install.sh", names)
            self.assertIn("install.ps1", names)
            self.assertTrue(any(name.startswith("pack/") for name in names))
            self.assertIn("install.sh", zip_names)
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python3 -m unittest tests.test_release_package -v`
Expected: FAIL because `pack.tools.release_package` does not exist.

- [ ] **Step 3: Write the minimal archive builder implementation**

```python
import tarfile
import zipfile
from pathlib import Path


RELEASE_ITEMS = ("install.sh", "install.ps1", "pack")


def build_release_archives(repo_root: Path, out_dir: Path, version: str):
    out_dir.mkdir(parents=True, exist_ok=True)
    tar_path = out_dir / f"opencode-agent-pack-{version}.tar.gz"
    zip_path = out_dir / f"opencode-agent-pack-{version}.zip"

    with tarfile.open(tar_path, "w:gz") as tar:
        for item in RELEASE_ITEMS:
            tar.add(repo_root / item, arcname=item)

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for item in RELEASE_ITEMS:
            path = repo_root / item
            if path.is_dir():
                for child in path.rglob("*"):
                    if child.is_file():
                        archive.write(child, child.relative_to(repo_root))
            else:
                archive.write(path, item)

    return tar_path, zip_path
```

- [ ] **Step 4: Add a small CLI and release policy note for manual packaging**

```python
import argparse
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=str(Path(__file__).resolve().parents[2]))
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--version", required=True)
    args = parser.parse_args()

    build_release_archives(Path(args.repo_root), Path(args.out_dir), args.version)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

Update `RELEASE.md` with a new minimum check line:

```md
7. GitHub Release artifacts are built and include `install.sh`, `install.ps1`, and `pack/`
```

- [ ] **Step 5: Re-run the release packaging tests**

Run: `python3 -m unittest tests.test_release_package -v`
Expected: PASS

- [ ] **Step 6: Commit the packaging support**

```bash
git add pack/tools/release_package.py tests/test_release_package.py RELEASE.md
git commit -m "feat: add release packaging artifacts"
```

### Task 4: Switch Documentation to the New Install Flow

**Files:**
- Modify: `README.md`
- Modify: `README.zh-CN.md`

- [ ] **Step 1: Update the English README install section to lead with bootstrap usage**

Replace the current install section shape with:

```md
## Install

### One-Command Install (default)

Install from a GitHub Release without cloning the repository:

```bash
curl -fsSL https://raw.githubusercontent.com/chendaleiQ/opencode-agent-pack/main/bootstrap/install.sh | bash
```

PowerShell:

```powershell
irm https://raw.githubusercontent.com/chendaleiQ/opencode-agent-pack/main/bootstrap/install.ps1 | iex
```

Set `OPENCODE_AGENT_PACK_VERSION=vX.Y.Z` before running the command when you want a fixed release version.
```

- [ ] **Step 2: Keep the local installer path but demote it to manual/offline install**

Add a follow-up subsection like:

```md
### Manual Local Install

For offline use, local testing, or contributor workflows:

```bash
git clone git@github.com:chendaleiQ/opencode-agent-pack.git
cd opencode-agent-pack
bash install.sh
```
```

- [ ] **Step 3: Apply the same messaging update to the Chinese README**

Use this structure in `README.zh-CN.md`:

```md
### 一键安装（默认）

无需 clone 仓库，直接从 GitHub Release 安装：

```bash
curl -fsSL https://raw.githubusercontent.com/chendaleiQ/opencode-agent-pack/main/bootstrap/install.sh | bash
```

PowerShell：

```powershell
irm https://raw.githubusercontent.com/chendaleiQ/opencode-agent-pack/main/bootstrap/install.ps1 | iex
```

如需固定版本，先设置 `OPENCODE_AGENT_PACK_VERSION=vX.Y.Z`。
```

- [ ] **Step 4: Read the install sections back and verify wording matches shipped behavior**

Run: `python3 -m unittest tests.test_release_bootstrap tests.test_release_package tests.test_install_sh_provider_allowlist -v`
Expected: PASS

Then manually confirm both READMEs state all of the following exactly:
- clone is no longer required for the default path
- default path uses bootstrap scripts
- bootstrap downloads a GitHub Release artifact
- local install remains available as a secondary path

- [ ] **Step 5: Commit the documentation switch**

```bash
git add README.md README.zh-CN.md
git commit -m "docs: switch install docs to release bootstrap"
```

### Task 5: Final Verification and Cleanup

**Files:**
- Review: `bootstrap/install.sh`
- Review: `bootstrap/install.ps1`
- Review: `pack/tools/release_bootstrap.py`
- Review: `pack/tools/release_package.py`
- Review: `README.md`
- Review: `README.zh-CN.md`
- Review: `RELEASE.md`

- [ ] **Step 1: Run the focused Python test suite**

Run: `python3 -m unittest tests.test_release_bootstrap tests.test_release_package tests.test_install_sh_provider_allowlist tests.test_provider_policy tests.test_opencode_config -v`
Expected: PASS

- [ ] **Step 2: Run shell and PowerShell syntax validation one more time**

Run: `bash -n bootstrap/install.sh && bash -n install.sh`
Expected: no output

Run: `pwsh -NoProfile -Command "[void][System.Management.Automation.Language.Parser]::ParseFile('bootstrap/install.ps1', [ref]$null, [ref]$null); [void][System.Management.Automation.Language.Parser]::ParseFile('install.ps1', [ref]$null, [ref]$null)"`
Expected: no output

- [ ] **Step 3: Build release archives locally to verify packaging works end-to-end**

Run: `python3 -m pack.tools.release_package --out-dir /tmp/opencode-agent-pack-release --version v0.0.0-test`
Expected: creates `/tmp/opencode-agent-pack-release/opencode-agent-pack-v0.0.0-test.tar.gz` and `.zip`

- [ ] **Step 4: Inspect the built archives by running the archive tests again**

Run: `python3 -m unittest tests.test_release_package -v`
Expected: PASS

- [ ] **Step 5: Create the final implementation commit**

```bash
git add bootstrap/install.sh bootstrap/install.ps1 pack/tools/release_bootstrap.py pack/tools/release_package.py tests/test_release_bootstrap.py tests/test_release_package.py README.md README.zh-CN.md RELEASE.md
git commit -m "feat: add release bootstrap installation flow"
```

## Self-Review

- Spec coverage check:
  - one-command no-clone install: Task 2 and Task 4
  - release-backed artifacts only: Task 1, Task 2, Task 3
  - canonical local installers unchanged in responsibility: Task 2 and Task 5
  - README-first install flow: Task 4
  - release packaging requirement: Task 3
- Placeholder scan: no `TODO`, `TBD`, or "implement later" placeholders remain in tasks.
- Type consistency check:
  - helper names are consistent across tasks: `build_release_asset_filename`, `build_release_asset_url`, `validate_extracted_release`, `build_release_archives`
  - archive filenames consistently use `opencode-agent-pack-<version>.<ext>`
