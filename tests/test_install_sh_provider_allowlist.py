import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path


class InstallShProviderAllowlistTests(unittest.TestCase):
    def test_non_interactive_install_sets_default_agent_and_preserves_existing_config(
        self,
    ):
        repo_root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            config_dir = home / ".config" / "opencode"
            data_dir = home / ".local" / "share" / "opencode"
            cache_dir = home / ".cache" / "opencode"
            config_dir.mkdir(parents=True)
            data_dir.mkdir(parents=True)
            cache_dir.mkdir(parents=True)

            (config_dir / "opencode.json").write_text(
                json.dumps({"provider": "openai", "model": "gpt-5.4"}),
                encoding="utf-8",
            )

            subprocess.run(
                ["bash", "install.sh", "--force"],
                cwd=repo_root,
                env={**os.environ, "HOME": str(home)},
                stdin=subprocess.DEVNULL,
                text=True,
                capture_output=True,
                check=True,
            )

            self.assertEqual(
                json.loads((config_dir / "opencode.json").read_text(encoding="utf-8")),
                {
                    "provider": "openai",
                    "model": "gpt-5.4",
                    "default_agent": "leader",
                },
            )

    def test_non_interactive_install_writes_default_all_allowed_providers(self):
        repo_root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            config_dir = home / ".config" / "opencode"
            data_dir = home / ".local" / "share" / "opencode"
            cache_dir = home / ".cache" / "opencode"
            config_dir.mkdir(parents=True)
            data_dir.mkdir(parents=True)
            cache_dir.mkdir(parents=True)

            (data_dir / "auth.json").write_text(
                json.dumps(
                    {
                        "openai": {"type": "oauth", "access": "token"},
                        "openrouter": {"type": "api", "key": "secret"},
                    }
                ),
                encoding="utf-8",
            )
            (cache_dir / "models.json").write_text(
                json.dumps(
                    {
                        "anthropic": {"models": {"claude-sonnet-4-5-20250929": {}}},
                    }
                ),
                encoding="utf-8",
            )
            (config_dir / "opencode.json").write_text(
                json.dumps({"provider": "openai", "model": "gpt-5.4"}),
                encoding="utf-8",
            )
            (config_dir / "settings.json").write_text(
                json.dumps(
                    {
                        "theme": "solarized",
                        "doTheThing": {"otherSetting": True},
                    }
                ),
                encoding="utf-8",
            )

            completed = subprocess.run(
                ["bash", "install.sh", "--force"],
                cwd=repo_root,
                env={**os.environ, "HOME": str(home)},
                stdin=subprocess.DEVNULL,
                text=True,
                capture_output=True,
                check=True,
            )

            self.assertIn("Installed do-the-thing", completed.stdout)

            settings = json.loads(
                (config_dir / "settings.json").read_text(encoding="utf-8")
            )
            self.assertEqual(settings["theme"], "solarized")
            self.assertEqual(settings["doTheThing"]["otherSetting"], True)
            self.assertEqual(
                settings["doTheThing"]["allowedProviders"],
                ["openai", "anthropic", "openrouter"],
            )
            self.assertEqual(
                json.loads((config_dir / "opencode.json").read_text(encoding="utf-8")),
                {
                    "provider": "openai",
                    "model": "gpt-5.4",
                    "default_agent": "leader",
                },
            )

    def test_non_interactive_install_with_no_detected_providers_preserves_existing_allowlist(
        self,
    ):
        repo_root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            config_dir = home / ".config" / "opencode"
            data_dir = home / ".local" / "share" / "opencode"
            cache_dir = home / ".cache" / "opencode"
            config_dir.mkdir(parents=True)
            data_dir.mkdir(parents=True)
            cache_dir.mkdir(parents=True)

            (config_dir / "settings.json").write_text(
                json.dumps(
                    {
                        "theme": "solarized",
                        "doTheThing": {"allowedProviders": ["openrouter"]},
                    }
                ),
                encoding="utf-8",
            )

            completed = subprocess.run(
                ["bash", "install.sh", "--force"],
                cwd=repo_root,
                env={**os.environ, "HOME": str(home)},
                stdin=subprocess.DEVNULL,
                text=True,
                capture_output=True,
                check=True,
            )

            self.assertIn("Installed do-the-thing", completed.stdout)
            settings = json.loads(
                (config_dir / "settings.json").read_text(encoding="utf-8")
            )
            self.assertEqual(settings["theme"], "solarized")
            self.assertEqual(
                settings["doTheThing"]["allowedProviders"],
                ["openrouter"],
            )

    def test_repeated_non_interactive_install_keeps_default_agent_stable(self):
        repo_root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            config_dir = home / ".config" / "opencode"
            data_dir = home / ".local" / "share" / "opencode"
            cache_dir = home / ".cache" / "opencode"
            config_dir.mkdir(parents=True)
            data_dir.mkdir(parents=True)
            cache_dir.mkdir(parents=True)

            (config_dir / "opencode.json").write_text(
                json.dumps({"provider": "openai"}),
                encoding="utf-8",
            )

            env = {**os.environ, "HOME": str(home)}
            subprocess.run(
                ["bash", "install.sh", "--force"],
                cwd=repo_root,
                env=env,
                stdin=subprocess.DEVNULL,
                text=True,
                capture_output=True,
                check=True,
            )
            subprocess.run(
                ["bash", "install.sh", "--force"],
                cwd=repo_root,
                env=env,
                stdin=subprocess.DEVNULL,
                text=True,
                capture_output=True,
                check=True,
            )

            self.assertEqual(
                json.loads((config_dir / "opencode.json").read_text(encoding="utf-8")),
                {"provider": "openai", "default_agent": "leader"},
            )


if __name__ == "__main__":
    unittest.main()
