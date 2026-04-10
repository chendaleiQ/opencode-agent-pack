# One-Command Install Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add one-command installers for OpenCode, Claude Code, and Codex across macOS, Linux, and Windows PowerShell, while updating docs and tests to make those installers the primary supported installation path.

**Architecture:** Add two installer entrypoints—one shell script and one PowerShell script—as the only primary user-facing installation surface. Each installer branches by platform target (`opencode`, `claude`, `codex`) and hides the platform-specific clone, update, plugin, or link mechanics behind a unified user command. Preserve the existing workflow payload and OpenCode internals, add the missing Claude plugin manifest, and document Cursor only as deferred.

**Tech Stack:** Shell, PowerShell, JSON, Markdown, Python `unittest`, existing repository plugin payload

---

### Task 1: Add installer and manifest test coverage first

**Files:**
- Modify: `tests/test_platform_install_docs.py`
- Create: `install/install.sh`
- Create: `install/install.ps1`
- Create: `.claude-plugin/plugin.json`
- Test: `tests/test_platform_install_docs.py`

- [ ] **Step 1: Add failing tests for installer entrypoints and Claude manifest**

```python
    def test_one_command_installer_files_exist(self):
        self.assertTrue((self.repo_root / "install" / "install.sh").exists())
        self.assertTrue((self.repo_root / "install" / "install.ps1").exists())

    def test_claude_plugin_manifest_exists(self):
        path = self.repo_root / ".claude-plugin" / "plugin.json"
        self.assertTrue(path.exists())

        data = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual("do-the-thing", data["name"])
        self.assertIn("description", data)
        self.assertIn("version", data)
```

- [ ] **Step 2: Run the targeted tests and verify they fail**

Run: `python3 -m unittest tests.test_platform_install_docs.PlatformInstallDocsTests.test_one_command_installer_files_exist tests.test_platform_install_docs.PlatformInstallDocsTests.test_claude_plugin_manifest_exists -v`
Expected: FAIL because the installer files and Claude manifest do not all exist yet

- [ ] **Step 3: Add minimal installer entrypoints and Claude manifest**

```bash
#!/usr/bin/env bash
set -euo pipefail

platform="${1:-}"
test -n "$platform" || { echo "usage: install.sh <opencode|claude|codex>"; exit 1; }
echo "Installing do-the-thing for: $platform"
```

```powershell
function Install-DoTheThing {
  param([Parameter(Mandatory = $true)][string]$Platform)
  Write-Host "Installing do-the-thing for: $Platform"
}
```

```json
{
  "name": "do-the-thing",
  "description": "Single-entry workflow plugin with one-command installation support.",
  "version": "1.1.1"
}
```

- [ ] **Step 4: Re-run the targeted tests and verify they pass**

Run: `python3 -m unittest tests.test_platform_install_docs.PlatformInstallDocsTests.test_one_command_installer_files_exist tests.test_platform_install_docs.PlatformInstallDocsTests.test_claude_plugin_manifest_exists -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add install/install.sh install/install.ps1 .claude-plugin/plugin.json tests/test_platform_install_docs.py
git commit -m "test: cover one-command installer entrypoints"
```

### Task 2: Implement installer target branching for OpenCode, Claude, and Codex

**Files:**
- Modify: `install/install.sh`
- Modify: `install/install.ps1`
- Test: manual readback in plan execution

- [ ] **Step 1: Expand `install/install.sh` to validate supported targets**

```bash
case "$platform" in
  opencode|claude|codex) ;;
  *)
    echo "unsupported platform: $platform" >&2
    exit 1
    ;;
esac
```

- [ ] **Step 2: Add stable install directory selection and shared clone/update logic in shell**

```bash
repo_url="https://github.com/chendaleiQ/do-the-thing.git"
install_root="${HOME}/.local/share/do-the-thing"
mkdir -p "$install_root"

if [ -d "$install_root/.git" ]; then
  git -C "$install_root" pull --ff-only
else
  rm -rf "$install_root"
  git clone "$repo_url" "$install_root"
fi
```

- [ ] **Step 3: Add per-platform shell handlers**

Implement handlers that:
- configure OpenCode with the existing plugin path model
- report Claude post-install usage with the shortest supported plugin usage guidance
- create Codex symlink discovery path on Unix

- [ ] **Step 4: Mirror the same target validation, clone/update logic, and handlers in PowerShell**

Implement PowerShell equivalents that:
- support `opencode`, `claude`, `codex`
- clone or update to a stable user directory
- create a junction or equivalent for Codex on Windows
- print verify/update/uninstall guidance

- [ ] **Step 5: Read both installers back and confirm the supported targets and outputs are aligned**

Review:
- `install/install.sh`
- `install/install.ps1`

Expected:
- both installers support the same target names
- both installers reject unsupported targets
- both installers provide verify/update/uninstall messaging

- [ ] **Step 6: Commit**

```bash
git add install/install.sh install/install.ps1
git commit -m "feat: add one-command platform installers"
```

### Task 3: Convert OpenCode, Claude, and Codex docs to one-command install docs

**Files:**
- Modify: `.opencode/INSTALL.md`
- Modify: `.claude-plugin/README.md`
- Modify: `.codex/INSTALL.md`
- Modify: `tests/test_platform_install_docs.py`
- Test: `tests/test_platform_install_docs.py`

- [ ] **Step 1: Add failing doc tests for one-command install instructions**

```python
    def test_opencode_doc_uses_one_command_install(self):
        content = (self.repo_root / ".opencode" / "INSTALL.md").read_text(encoding="utf-8")
        self.assertIn("curl -fsSL", content)
        self.assertIn("install.sh | bash -s -- opencode", content)
        self.assertIn("Install-DoTheThing opencode", content)

    def test_claude_doc_uses_one_command_install(self):
        content = (self.repo_root / ".claude-plugin" / "README.md").read_text(encoding="utf-8")
        self.assertIn("curl -fsSL", content)
        self.assertIn("install.sh | bash -s -- claude", content)
        self.assertIn("Install-DoTheThing claude", content)
        self.assertIn(".claude-plugin/plugin.json", content)

    def test_codex_doc_uses_one_command_install(self):
        content = (self.repo_root / ".codex" / "INSTALL.md").read_text(encoding="utf-8")
        self.assertIn("curl -fsSL", content)
        self.assertIn("install.sh | bash -s -- codex", content)
        self.assertIn("Install-DoTheThing codex", content)
        self.assertIn("ln -s", content)
        self.assertIn("mklink /J", content)
```

- [ ] **Step 2: Run the targeted tests and verify they fail**

Run: `python3 -m unittest tests.test_platform_install_docs.PlatformInstallDocsTests.test_opencode_doc_uses_one_command_install tests.test_platform_install_docs.PlatformInstallDocsTests.test_claude_doc_uses_one_command_install tests.test_platform_install_docs.PlatformInstallDocsTests.test_codex_doc_uses_one_command_install -v`
Expected: FAIL because the docs do not yet use the one-command install entrypoint

- [ ] **Step 3: Rewrite the three platform docs to make the installer the primary path**

For each platform doc, include:
- Unix one-command install
- PowerShell one-command install
- Verify
- Updating
- Uninstalling

And keep platform-specific internal details as troubleshooting/reference rather than the main install path.

- [ ] **Step 4: Re-run the targeted tests and verify they pass**

Run: `python3 -m unittest tests.test_platform_install_docs.PlatformInstallDocsTests.test_opencode_doc_uses_one_command_install tests.test_platform_install_docs.PlatformInstallDocsTests.test_claude_doc_uses_one_command_install tests.test_platform_install_docs.PlatformInstallDocsTests.test_codex_doc_uses_one_command_install -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add .opencode/INSTALL.md .claude-plugin/README.md .codex/INSTALL.md tests/test_platform_install_docs.py
git commit -m "docs: switch platform installs to one-command flow"
```

### Task 4: Align README and Chinese README with supported one-command targets

**Files:**
- Modify: `README.md`
- Modify: `docs/project/README.zh-CN.md`
- Modify: `tests/test_platform_install_docs.py`
- Test: `tests/test_platform_install_docs.py`

- [ ] **Step 1: Add a failing test for updated support matrix wording**

```python
    def test_readmes_reflect_one_command_support_matrix(self):
        readme = (self.repo_root / "README.md").read_text(encoding="utf-8")
        zh = (self.repo_root / "docs" / "project" / "README.zh-CN.md").read_text(encoding="utf-8")

        self.assertIn("OpenCode: one-command native install", readme)
        self.assertIn("Claude Code: one-command native install", readme)
        self.assertIn("Codex: one-command install", readme)
        self.assertIn("Cursor: deferred", readme)
        self.assertIn("OpenCode：一条命令原生安装", zh)
        self.assertIn("Claude Code：一条命令原生安装", zh)
        self.assertIn("Codex：一条命令安装", zh)
        self.assertIn("Cursor：暂缓", zh)
```

- [ ] **Step 2: Run the targeted test and verify it fails**

Run: `python3 -m unittest tests.test_platform_install_docs.PlatformInstallDocsTests.test_readmes_reflect_one_command_support_matrix -v`
Expected: FAIL because the READMEs do not yet reflect the new one-command support matrix

- [ ] **Step 3: Update README and Chinese README support sections and install examples**

Update both docs so they:
- present one-command install examples for OpenCode, Claude, and Codex
- mark Cursor as deferred / under investigation
- stop leading with high-friction manual install paths

- [ ] **Step 4: Re-run the targeted test and verify it passes**

Run: `python3 -m unittest tests.test_platform_install_docs.PlatformInstallDocsTests.test_readmes_reflect_one_command_support_matrix -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add README.md docs/project/README.zh-CN.md tests/test_platform_install_docs.py
git commit -m "docs: align support matrix with one-command install"
```

### Task 5: Run full install-doc verification and sanity-check generated UX

**Files:**
- Test: `tests/test_platform_install_docs.py`
- Review: installer and platform docs

- [ ] **Step 1: Run the full platform install doc test suite**

Run: `python3 -m unittest tests.test_platform_install_docs -v`
Expected: PASS

- [ ] **Step 2: Read the final user-facing files back for sanity**

Review:
- `install/install.sh`
- `install/install.ps1`
- `.opencode/INSTALL.md`
- `.claude-plugin/README.md`
- `.codex/INSTALL.md`
- `README.md`
- `docs/project/README.zh-CN.md`

Expected:
- user-visible install instructions are one-command first
- OpenCode, Claude, and Codex are supported
- Cursor is clearly deferred
- platform-specific internal details are still available for troubleshooting

- [ ] **Step 3: Commit any final adjustments if needed**

```bash
git add install .opencode .claude-plugin .codex README.md docs/project/README.zh-CN.md tests/test_platform_install_docs.py
git commit -m "test: verify one-command install docs"
```
