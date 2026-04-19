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
        self.default_opencode_plugin = (
            "do-the-thing@git+https://github.com/chendaleiQ/do-the-thing.git#main"
        )

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
        self.assertIn("Install-DoTheThing opencode", content)
        self.assertIn("### Codex", content)
        self.assertIn("partial support", content)
        self.assertIn(".codex/INSTALL.md", content)

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

    def test_git_has_no_tracked_pyc_files(self):
        result = subprocess.run(
            ["git", "ls-files", "*.pyc"],
            check=True,
            cwd=self.repo_root,
            capture_output=True,
            text=True,
        )

        self.assertEqual("", result.stdout, "tracked .pyc files found")

    def test_claude_plugin_manifest_exists_and_has_required_fields(self):
        path = self.repo_root / ".claude-plugin" / "plugin.json"
        self.assertTrue(path.exists(), f"missing Claude plugin manifest: {path}")

        data = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual("do-the-thing", data["name"])
        self.assertIn("description", data)
        self.assertEqual("1.4.0", data["version"])

    def test_opencode_install_doc_uses_one_command_install(self):
        content = (self.repo_root / ".opencode" / "INSTALL.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("curl -fsSL", content)
        self.assertIn("install.sh | bash -s -- opencode", content)
        self.assertIn("Install-DoTheThing opencode", content)
        self.assertIn(f'"plugin": ["{self.default_opencode_plugin}"]', content)
        self.assertIn("Quick Start", content)
        self.assertIn("repository `main` branch", content)
        self.assertIn("PR merges to `main` become the default update path", content)
        self.assertIn("Restart OpenCode", content)
        self.assertIn("switch to `leader` and say `ready`", content)
        self.assertIn("Pack-owned built-in skills use a `dtt-` prefix", content)
        self.assertIn("detects duplicate skill names from multiple sources", content)

    def test_opencode_plugin_syncs_from_package_root_not_runtime_directory(self):
        content = (
            self.repo_root / ".opencode" / "plugins" / "do-the-thing.js"
        ).read_text(encoding="utf-8")

        self.assertIn("fileURLToPath(import.meta.url)", content)
        self.assertIn("syncManagedContent(PACKAGE_ROOT, configDir)", content)
        self.assertNotIn("syncManagedContent(directory, configDir)", content)

    def test_claude_doc_shows_deferred_status(self):
        content = (self.repo_root / ".claude-plugin" / "README.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("deferred", content.lower())
        self.assertIn(".claude-plugin/plugin.json", content)

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

        def readme_section(title):
            marker = f"### {title}\n\n"
            start = readme.index(marker) + len(marker)
            remainder = readme[start:]
            next_section = remainder.find("\n### ")
            if next_section != -1:
                return remainder[:next_section]
            return remainder

        self.assertIn("One-command native install.", readme_section("OpenCode"))
        self.assertIn("one-command installation", readme_section("Codex"))
        self.assertIn("skills", readme_section("Codex"))
        self.assertIn("does **not** install the full", readme_section("Codex"))
        self.assertIn("coming soon", readme_section("Cursor"))
        self.assertIn("coming soon", readme_section("Claude Code"))
        self.assertIn("Codex uses one-command install.", codex)
        self.assertIn(
            "That path is still under investigation and is not part of the supported one-command install targets in this release.",
            cursor,
        )
        self.assertIn("Claude Code support is **deferred**.", claude)
        self.assertIn(
            "Until Claude Code adds a way to persistently register a plugin directory, the one-command installer does not include a `claude` target.",
            claude,
        )

    def test_readme_describes_concise_install_and_usage_flow(self):
        content = (self.repo_root / "README.md").read_text(encoding="utf-8")

        self.assertIn("## How It Works", content)
        self.assertIn("## Use", content)
        self.assertIn(
            "Use `/providers` if you need to adjust the plugin-scoped provider allowlist.",
            content,
        )

    def test_installer_entrypoints_use_supported_target_names(self):
        shell = (self.repo_root / "install" / "install.sh").read_text(encoding="utf-8")
        ps1 = (self.repo_root / "install" / "install.ps1").read_text(encoding="utf-8")

        for target in ["opencode", "codex"]:
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

    def test_opencode_installers_use_main_by_default_and_no_python_dependency_in_powershell(
        self,
    ):
        shell = (self.repo_root / "install" / "install.sh").read_text(encoding="utf-8")
        ps1 = (self.repo_root / "install" / "install.ps1").read_text(encoding="utf-8")

        self.assertIn('DTT_DEFAULT_OPENCODE_REF="main"', shell)
        self.assertIn("if ($env:DTT_PLUGIN_REF)", ps1)
        self.assertIn("$defaultOpenCodeRef = 'main'", ps1)
        self.assertNotIn("Ensure-PythonAvailable", ps1)
        self.assertNotIn("python3 -c", ps1)

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
            self.assertIn(self.default_opencode_plugin, config["plugin"])

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
            env["DTT_PLUGIN_REF"] = "v1.3.0"

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
                    "default_agent": "leader",
                    "plugin": [
                        "other-plugin@1.0.0",
                        "do-the-thing@git+https://github.com/chendaleiQ/do-the-thing.git#v1.3.0",
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
            env["DTT_PLUGIN_REF"] = "v1.3.0"

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
                    "default_agent": "leader",
                    "plugin": [
                        "other-plugin@1.0.0",
                        "do-the-thing@git+https://github.com/chendaleiQ/do-the-thing.git#v1.3.0",
                    ],
                    "provider": "openai",
                },
            )

    def test_shell_installer_writes_usable_temp_opencode_config(self):
        script = self.repo_root / "install" / "install.sh"
        plugin_url = (
            self.repo_root / ".opencode" / "plugins" / "do-the-thing.js"
        ).as_uri()

        with tempfile.TemporaryDirectory() as tmpdir:
            temp = Path(tmpdir)
            config_dir = temp / "opencode-config"
            config_dir.mkdir(parents=True)
            (config_dir / "opencode.json").write_text(
                json.dumps(
                    {
                        "provider": "openai",
                        "plugin": [
                            "other-plugin@1.0.0",
                            "do-the-thing@git+https://github.com/chendaleiQ/do-the-thing.git#old",
                            "do-the-thing@file:///tmp/local",
                        ],
                    }
                ),
                encoding="utf-8",
            )
            env = os.environ.copy()
            env["HOME"] = tmpdir
            env["DTT_REPO_URL"] = str(self.repo_root)
            env["DTT_INSTALL_ROOT"] = str(temp / "installed" / "do-the-thing")
            env["OPENCODE_CONFIG_DIR"] = str(config_dir)

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
                    "provider": "openai",
                    "default_agent": "leader",
                    "plugin": [
                        "other-plugin@1.0.0",
                        self.default_opencode_plugin,
                    ],
                },
            )

            runtime_check = subprocess.run(
                [
                    "node",
                    "--input-type=module",
                    "-e",
                    "\n".join(
                        [
                            f"const mod = await import({json.dumps(plugin_url)});",
                            "const hooks = await mod.DoTheThingPlugin({",
                            "  project: { id: 'proj-1' },",
                            f"  directory: {json.dumps(str(self.repo_root))},",
                            f"  worktree: {json.dumps(str(self.repo_root))},",
                            "});",
                            "const config = {};",
                            "await hooks.config(config);",
                            "console.log(JSON.stringify({ skillsPaths: config.skills.paths, hasBeforeHook: typeof hooks['tool.execute.before'] === 'function' }));",
                        ]
                    ),
                ],
                check=True,
                cwd=self.repo_root,
                env={**env, "OPENCODE_CONFIG_DIR": str(config_dir)},
                capture_output=True,
                text=True,
            )

            self.assertEqual(
                json.loads(runtime_check.stdout.strip()),
                {
                    "skillsPaths": [str(config_dir / "skills")],
                    "hasBeforeHook": True,
                },
            )

    def test_powershell_installer_configures_opencode_plugin_entry_by_default(self):
        powershell = shutil.which("pwsh") or shutil.which("powershell")
        if powershell is None:
            self.skipTest("PowerShell runtime not available")

        script = self.repo_root / "install" / "install.ps1"

        with tempfile.TemporaryDirectory() as tmpdir:
            temp = Path(tmpdir)
            env = os.environ.copy()
            env["HOME"] = tmpdir
            env["DTT_REPO_URL"] = str(self.repo_root)
            env["DTT_INSTALL_ROOT"] = str(temp / "installed" / "do-the-thing")
            env["OPENCODE_CONFIG_DIR"] = str(temp / "opencode-config")

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

            config_path = temp / "opencode-config" / "opencode.json"
            self.assertTrue(config_path.exists())
            config = json.loads(config_path.read_text(encoding="utf-8"))
            self.assertIn("plugin", config)
            self.assertIn(self.default_opencode_plugin, config["plugin"])

    def test_shell_opencode_installer_rejects_invalid_json_and_keeps_backup(self):
        script = self.repo_root / "install" / "install.sh"

        with tempfile.TemporaryDirectory() as tmpdir:
            temp = Path(tmpdir)
            config_dir = temp / "opencode-config"
            config_dir.mkdir(parents=True)
            config_path = config_dir / "opencode.json"
            original = "{ invalid json\n"
            config_path.write_text(original, encoding="utf-8")

            env = os.environ.copy()
            env["HOME"] = tmpdir
            env["OPENCODE_CONFIG_DIR"] = str(config_dir)

            result = subprocess.run(
                ["bash", str(script), "opencode"],
                cwd=self.repo_root,
                env=env,
                capture_output=True,
                text=True,
            )

            self.assertNotEqual(0, result.returncode)
            self.assertIn("Invalid JSON", result.stderr)
            self.assertEqual(original, config_path.read_text(encoding="utf-8"))
            backups = list(config_dir.glob("opencode.json.bak.*"))
            self.assertEqual(1, len(backups))
            self.assertEqual(original, backups[0].read_text(encoding="utf-8"))

    def test_powershell_opencode_installer_rejects_invalid_json_and_keeps_backup(self):
        powershell = shutil.which("pwsh") or shutil.which("powershell")
        if powershell is None:
            self.skipTest("PowerShell runtime not available")

        script = self.repo_root / "install" / "install.ps1"

        with tempfile.TemporaryDirectory() as tmpdir:
            temp = Path(tmpdir)
            config_dir = temp / "opencode-config"
            config_dir.mkdir(parents=True)
            config_path = config_dir / "opencode.json"
            original = "{ invalid json\n"
            config_path.write_text(original, encoding="utf-8")

            env = os.environ.copy()
            env["HOME"] = tmpdir
            env["OPENCODE_CONFIG_DIR"] = str(config_dir)

            result = subprocess.run(
                [
                    powershell,
                    "-NoLogo",
                    "-NoProfile",
                    "-Command",
                    f"& {{ . '{script}'; Install-DoTheThing opencode }}",
                ],
                cwd=self.repo_root,
                env=env,
                capture_output=True,
                text=True,
            )

            self.assertNotEqual(0, result.returncode)
            self.assertIn("Invalid JSON", result.stderr)
            self.assertEqual(original, config_path.read_text(encoding="utf-8"))
            backups = list(config_dir.glob("opencode.json.bak.*"))
            self.assertEqual(1, len(backups))
            self.assertEqual(original, backups[0].read_text(encoding="utf-8"))

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
        zh = (self.repo_root / "docs" / "README.zh-CN.md").read_text(encoding="utf-8")

        for token in [
            "OpenCode",
            "One-command native install",
            "Claude Code",
            "Codex",
            "Cursor",
            "coming soon",
            "partial support",
            "repository `main` branch",
        ]:
            self.assertIn(token, readme)
        self.assertIn("一条命令原生安装", zh)
        self.assertIn("Claude Code：coming soon", zh)
        self.assertIn("Codex：部分支持", zh)
        self.assertIn("Cursor：coming soon", zh)
        self.assertIn("仓库 `main` 分支", zh)

    def test_readme_stays_concise_without_old_directory_tree_section(self):
        content = (self.repo_root / "README.md").read_text(encoding="utf-8")

        self.assertNotIn("examples/", content)
        self.assertNotIn("└─ pack/", content)
        self.assertNotIn("└─ tools/", content)
        self.assertIn("## Project Docs", content)


if __name__ == "__main__":
    unittest.main()
