import unittest
from pathlib import Path


class PlatformInstallDocsTests(unittest.TestCase):
    def setUp(self):
        self.repo_root = Path(__file__).resolve().parents[1]

    def test_platform_install_entry_files_exist(self):
        expected = [
            self.repo_root / ".opencode" / "INSTALL.md",
            self.repo_root / ".opencode" / "plugins" / "do-the-thing.js",
            self.repo_root / ".codex" / "INSTALL.md",
            self.repo_root / ".cursor-plugin" / "README.md",
            self.repo_root / ".claude-plugin" / "README.md",
            self.repo_root / "package.json",
        ]

        for path in expected:
            self.assertTrue(path.exists(), f"missing platform install file: {path}")

    def test_readme_uses_platform_first_install_sections(self):
        content = (self.repo_root / "README.md").read_text(encoding="utf-8")

        self.assertIn("## Installation", content)
        self.assertIn("### Claude Code", content)
        self.assertIn("### Cursor", content)
        self.assertIn("### Codex", content)
        self.assertIn("### OpenCode", content)
        self.assertIn("### Verify Installation", content)

    def test_readme_uses_fetch_and_follow_for_opencode_and_codex(self):
        content = (self.repo_root / "README.md").read_text(encoding="utf-8")

        self.assertIn(
            "Fetch and follow instructions from https://raw.githubusercontent.com/chendaleiQ/do-the-thing/refs/heads/main/.codex/INSTALL.md",
            content,
        )
        self.assertIn(
            "Fetch and follow instructions from https://raw.githubusercontent.com/chendaleiQ/do-the-thing/refs/heads/main/.opencode/INSTALL.md",
            content,
        )

    def test_platform_install_docs_avoid_local_script_install_flow(self):
        docs = [
            self.repo_root / ".opencode" / "INSTALL.md",
            self.repo_root / ".codex" / "INSTALL.md",
            self.repo_root / ".cursor-plugin" / "README.md",
            self.repo_root / ".claude-plugin" / "README.md",
            self.repo_root / "README.md",
        ]

        for path in docs:
            content = path.read_text(encoding="utf-8")
            self.assertNotIn("git clone", content)
            self.assertNotIn("bash install.sh", content)
            self.assertNotIn("install.ps1", content)
            self.assertNotIn("bootstrap/install.sh", content)

    def test_opencode_install_doc_uses_plugin_array_install(self):
        content = (self.repo_root / ".opencode" / "INSTALL.md").read_text(
            encoding="utf-8"
        )

        self.assertIn(
            '"plugin": ["do-the-thing@git+https://github.com/chendaleiQ/do-the-thing.git"]',
            content,
        )
        self.assertIn("Restart OpenCode", content)
        self.assertIn("Pack-owned built-in skills use a `dtt-` prefix", content)
        self.assertIn("detects duplicate skill names from multiple sources", content)

    def test_opencode_plugin_syncs_from_package_root_not_runtime_directory(self):
        content = (
            self.repo_root / ".opencode" / "plugins" / "do-the-thing.js"
        ).read_text(encoding="utf-8")

        self.assertIn("fileURLToPath(import.meta.url)", content)
        self.assertIn("syncManagedContent(PACKAGE_ROOT, configDir)", content)
        self.assertNotIn("syncManagedContent(directory, configDir)", content)

    def test_platform_docs_distinguish_native_vs_manual_install(self):
        readme = (self.repo_root / "README.md").read_text(encoding="utf-8")
        codex = (self.repo_root / ".codex" / "INSTALL.md").read_text(encoding="utf-8")
        cursor = (self.repo_root / ".cursor-plugin" / "README.md").read_text(
            encoding="utf-8"
        )
        claude = (self.repo_root / ".claude-plugin" / "README.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("Native plugin install.", readme)
        self.assertIn("Manual install.", readme)
        self.assertIn("Manual compatibility install.", readme)
        self.assertIn("manual install", codex.lower())
        self.assertIn("manual compatibility install", cursor.lower())
        self.assertIn("manual compatibility install", claude.lower())

    def test_legacy_install_script_chain_is_removed(self):
        removed = [
            self.repo_root / "install.sh",
            self.repo_root / "install.ps1",
            self.repo_root / "bootstrap" / "install.sh",
            self.repo_root / "bootstrap" / "install.ps1",
            self.repo_root / "pack" / "tools" / "release_bootstrap.py",
            self.repo_root / "pack" / "tools" / "release_package.py",
            self.repo_root / "tests" / "test_install_sh_provider_allowlist.py",
            self.repo_root / "tests" / "test_release_bootstrap.py",
            self.repo_root / "tests" / "test_release_package.py",
        ]

        for path in removed:
            self.assertFalse(
                path.exists(), f"legacy install artifact still exists: {path}"
            )

    def test_repository_uses_top_level_core_layout(self):
        expected = [
            self.repo_root / "AGENTS.md",
            self.repo_root / "agents",
            self.repo_root / "commands",
            self.repo_root / "skills",
        ]

        for path in expected:
            self.assertTrue(path.exists(), f"missing top-level core path: {path}")

        self.assertFalse((self.repo_root / "pack").exists())
        self.assertFalse((self.repo_root / "bootstrap").exists())

    def test_readme_directory_tree_has_no_examples_or_pack_dir(self):
        content = (self.repo_root / "README.md").read_text(encoding="utf-8")

        self.assertNotIn("examples/", content)
        self.assertNotIn("└─ pack/", content)
        self.assertIn("└─ tools/", content)


if __name__ == "__main__":
    unittest.main()
