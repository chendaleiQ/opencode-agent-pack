import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


class PlatformInstallDocsTests(unittest.TestCase):
    def setUp(self):
        self.repo_root = Path(__file__).resolve().parents[1]

    def test_platform_install_entry_files_exist(self):
        expected = [
            self.repo_root / "install" / "install.sh",
            self.repo_root / "install" / "install.ps1",
            self.repo_root / ".opencode" / "INSTALL.md",
            self.repo_root / ".opencode" / "plugins" / "do-the-thing.js",
            self.repo_root / ".codex" / "INSTALL.md",
            self.repo_root / ".cursor-plugin" / "README.md",
            self.repo_root / ".claude-plugin" / "README.md",
            self.repo_root / ".claude-plugin" / "plugin.json",
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

    def test_readme_uses_one_command_install_for_supported_platforms(self):
        content = (self.repo_root / "README.md").read_text(encoding="utf-8")

        self.assertIn("curl -fsSL", content)
        self.assertIn("install.sh | bash -s -- opencode", content)
        self.assertIn("install.sh | bash -s -- claude", content)
        self.assertIn("install.sh | bash -s -- codex", content)
        self.assertIn("Install-DoTheThing opencode", content)
        self.assertIn("Install-DoTheThing claude", content)
        self.assertIn("Install-DoTheThing codex", content)

    def test_platform_install_docs_use_installer_not_fetch_and_follow(self):
        docs = [
            self.repo_root / ".opencode" / "INSTALL.md",
            self.repo_root / ".codex" / "INSTALL.md",
            self.repo_root / ".cursor-plugin" / "README.md",
            self.repo_root / ".claude-plugin" / "README.md",
            self.repo_root / "README.md",
        ]

        for path in docs:
            content = path.read_text(encoding="utf-8")
            self.assertNotIn("Fetch and follow instructions from", content)

    def test_claude_plugin_manifest_exists_and_has_required_fields(self):
        path = self.repo_root / ".claude-plugin" / "plugin.json"
        self.assertTrue(path.exists(), f"missing Claude plugin manifest: {path}")

        data = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual("do-the-thing", data["name"])
        self.assertIn("description", data)
        self.assertEqual("1.2.0", data["version"])

    def test_opencode_install_doc_uses_one_command_install(self):
        content = (self.repo_root / ".opencode" / "INSTALL.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("curl -fsSL", content)
        self.assertIn("install.sh | bash -s -- opencode", content)
        self.assertIn("Install-DoTheThing opencode", content)
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

    def test_claude_doc_uses_one_command_install(self):
        content = (self.repo_root / ".claude-plugin" / "README.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("curl -fsSL", content)
        self.assertIn("install.sh | bash -s -- claude", content)
        self.assertIn("Install-DoTheThing claude", content)
        self.assertIn(".claude-plugin/plugin.json", content)
        self.assertIn("Verify Installation", content)

    def test_codex_doc_uses_one_command_install(self):
        content = (self.repo_root / ".codex" / "INSTALL.md").read_text(encoding="utf-8")

        self.assertIn("curl -fsSL", content)
        self.assertIn("install.sh | bash -s -- codex", content)
        self.assertIn("Install-DoTheThing codex", content)
        self.assertIn("ln -s", content)
        self.assertIn("mklink /J", content)
        self.assertIn("Updating", content)
        self.assertIn("Uninstalling", content)

    def test_platform_docs_distinguish_supported_vs_deferred_install(self):
        readme = (self.repo_root / "README.md").read_text(encoding="utf-8")
        codex = (self.repo_root / ".codex" / "INSTALL.md").read_text(encoding="utf-8")
        cursor = (self.repo_root / ".cursor-plugin" / "README.md").read_text(
            encoding="utf-8"
        )
        claude = (self.repo_root / ".claude-plugin" / "README.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("OpenCode: one-command native install", readme)
        self.assertIn("Claude Code: one-command native install", readme)
        self.assertIn("Codex: one-command install", readme)
        self.assertIn("Cursor: deferred", readme)
        self.assertIn("one-command", codex.lower())
        self.assertIn("deferred", cursor.lower())
        self.assertIn("one-command", claude.lower())

    def test_installer_entrypoints_use_supported_target_names(self):
        shell = (self.repo_root / "install" / "install.sh").read_text(encoding="utf-8")
        ps1 = (self.repo_root / "install" / "install.ps1").read_text(encoding="utf-8")

        for target in ["opencode", "claude", "codex"]:
            self.assertIn(target, shell)
            self.assertIn(target, ps1)

        self.assertIn("Install-DoTheThing", ps1)

    def test_opencode_installers_document_plugin_ref_override(self):
        shell = (self.repo_root / "install" / "install.sh").read_text(encoding="utf-8")
        ps1 = (self.repo_root / "install" / "install.ps1").read_text(encoding="utf-8")
        doc = (self.repo_root / ".opencode" / "INSTALL.md").read_text(encoding="utf-8")

        self.assertIn("DTT_PLUGIN_REF", shell)
        self.assertIn("DTT_PLUGIN_REF", ps1)
        self.assertIn("DTT_PLUGIN_REF", doc)

    def test_shell_installer_configures_opencode_plugin_entry(self):
        script = self.repo_root / "install" / "install.sh"

        with tempfile.TemporaryDirectory() as tmpdir:
            temp = Path(tmpdir)
            env = os.environ.copy()
            env["HOME"] = tmpdir
            env["DTT_REPO_URL"] = str(self.repo_root)
            env["DTT_INSTALL_ROOT"] = str(temp / "installed" / "do-the-thing")
            env["OPENCODE_CONFIG_DIR"] = str(temp / "opencode-config")

            subprocess.run(
                ["bash", str(script), "opencode"],
                check=True,
                cwd=self.repo_root,
                env=env,
                capture_output=True,
                text=True,
            )

            config_path = temp / "opencode-config" / "opencode.json"
            self.assertTrue(config_path.exists())
            config = json.loads(config_path.read_text(encoding="utf-8"))
            self.assertIn("plugin", config)
            self.assertIn(
                "do-the-thing@git+https://github.com/chendaleiQ/do-the-thing.git",
                config["plugin"],
            )

    def test_shell_installer_updates_existing_opencode_plugin_entry_with_override(self):
        script = self.repo_root / "install" / "install.sh"

        with tempfile.TemporaryDirectory() as tmpdir:
            temp = Path(tmpdir)
            config_dir = temp / "opencode-config"
            config_dir.mkdir(parents=True)
            (config_dir / "opencode.json").write_text(
                json.dumps(
                    {
                        "plugin": [
                            "other-plugin@1.0.0",
                            "do-the-thing@git+https://github.com/chendaleiQ/do-the-thing.git#old",
                            "do-the-thing@file:///tmp/local",
                        ],
                        "provider": "openai",
                    }
                ),
                encoding="utf-8",
            )
            env = os.environ.copy()
            env["HOME"] = tmpdir
            env["DTT_REPO_URL"] = str(self.repo_root)
            env["DTT_INSTALL_ROOT"] = str(temp / "installed" / "do-the-thing")
            env["OPENCODE_CONFIG_DIR"] = str(config_dir)
            env["DTT_PLUGIN_REF"] = "v1.2.0"

            subprocess.run(
                ["bash", str(script), "opencode"],
                check=True,
                cwd=self.repo_root,
                env=env,
                capture_output=True,
                text=True,
            )

            config = json.loads(
                (config_dir / "opencode.json").read_text(encoding="utf-8")
            )
            self.assertEqual(
                config,
                {
                    "plugin": [
                        "other-plugin@1.0.0",
                        "do-the-thing@git+https://github.com/chendaleiQ/do-the-thing.git#v1.2.0",
                    ],
                    "provider": "openai",
                },
            )

    def test_powershell_installer_updates_existing_opencode_plugin_entry_with_override(
        self,
    ):
        powershell = shutil.which("pwsh") or shutil.which("powershell")
        if powershell is None:
            self.skipTest("PowerShell runtime not available")

        script = self.repo_root / "install" / "install.ps1"

        with tempfile.TemporaryDirectory() as tmpdir:
            temp = Path(tmpdir)
            config_dir = temp / "opencode-config"
            config_dir.mkdir(parents=True)
            (config_dir / "opencode.json").write_text(
                json.dumps(
                    {
                        "plugin": [
                            "other-plugin@1.0.0",
                            "do-the-thing@git+https://github.com/chendaleiQ/do-the-thing.git#old",
                            "do-the-thing@file:///tmp/local",
                        ],
                        "provider": "openai",
                    }
                ),
                encoding="utf-8",
            )

            env = os.environ.copy()
            env["HOME"] = tmpdir
            env["DTT_REPO_URL"] = str(self.repo_root)
            env["DTT_INSTALL_ROOT"] = str(temp / "installed" / "do-the-thing")
            env["OPENCODE_CONFIG_DIR"] = str(config_dir)
            env["DTT_PLUGIN_REF"] = "v1.2.0"

            subprocess.run(
                [
                    powershell,
                    "-NoLogo",
                    "-NoProfile",
                    "-Command",
                    f"& {{ . '{script}'; Install-DoTheThing opencode }}",
                ],
                check=True,
                cwd=self.repo_root,
                env=env,
                capture_output=True,
                text=True,
            )

            config = json.loads(
                (config_dir / "opencode.json").read_text(encoding="utf-8")
            )
            self.assertEqual(
                config,
                {
                    "plugin": [
                        "other-plugin@1.0.0",
                        "do-the-thing@git+https://github.com/chendaleiQ/do-the-thing.git#v1.2.0",
                    ],
                    "provider": "openai",
                },
            )

    def test_shell_installer_creates_codex_skill_symlink(self):
        script = self.repo_root / "install" / "install.sh"

        with tempfile.TemporaryDirectory() as tmpdir:
            temp = Path(tmpdir)
            env = os.environ.copy()
            env["HOME"] = tmpdir
            env["DTT_REPO_URL"] = str(self.repo_root)
            env["DTT_INSTALL_ROOT"] = str(temp / "installed" / "do-the-thing")

            subprocess.run(
                ["bash", str(script), "codex"],
                check=True,
                cwd=self.repo_root,
                env=env,
                capture_output=True,
                text=True,
            )

            link_path = temp / ".agents" / "skills" / "do-the-thing"
            self.assertTrue(link_path.exists())
            self.assertTrue(link_path.is_symlink())
            self.assertEqual(
                str(temp / "installed" / "do-the-thing" / "skills"),
                os.readlink(link_path),
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

    def test_readmes_reflect_one_command_support_matrix(self):
        readme = (self.repo_root / "README.md").read_text(encoding="utf-8")
        zh = (self.repo_root / "docs" / "project" / "README.zh-CN.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("OpenCode: one-command native install", readme)
        self.assertIn("Claude Code: one-command native install", readme)
        self.assertIn("Codex: one-command install", readme)
        self.assertIn("Cursor: deferred", readme)
        self.assertIn("OpenCode：一条命令原生安装", zh)
        self.assertIn("Claude Code：一条命令原生安装", zh)
        self.assertIn("Codex：一条命令安装", zh)
        self.assertIn("Cursor：暂缓", zh)

    def test_readme_directory_tree_has_no_examples_or_pack_dir(self):
        content = (self.repo_root / "README.md").read_text(encoding="utf-8")

        self.assertNotIn("examples/", content)
        self.assertNotIn("└─ pack/", content)
        self.assertIn("└─ tools/", content)


if __name__ == "__main__":
    unittest.main()
