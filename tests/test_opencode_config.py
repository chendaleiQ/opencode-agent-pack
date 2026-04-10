import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class OpenCodeConfigTests(unittest.TestCase):
    def test_set_default_agent_preserves_existing_fields(self):
        repo_root = Path(__file__).resolve().parents[1]
        script = repo_root / "tools" / "opencode_config.py"

        with tempfile.TemporaryDirectory() as tmp:
            config_path = Path(tmp) / "opencode.json"
            config_path.write_text(
                json.dumps({"provider": "openai", "model": "gpt-5.4"}),
                encoding="utf-8",
            )

            subprocess.run(
                [
                    sys.executable,
                    str(script),
                    "--config-path",
                    str(config_path),
                    "--set-default-agent",
                    "leader",
                ],
                check=True,
            )

            self.assertEqual(
                json.loads(config_path.read_text(encoding="utf-8")),
                {
                    "provider": "openai",
                    "model": "gpt-5.4",
                    "default_agent": "leader",
                },
            )

    def test_set_opencode_plugin_replaces_existing_dtt_entries_and_dedupes(self):
        repo_root = Path(__file__).resolve().parents[1]
        script = repo_root / "tools" / "opencode_config.py"

        with tempfile.TemporaryDirectory() as tmp:
            config_path = Path(tmp) / "opencode.json"
            config_path.write_text(
                json.dumps(
                    {
                        "plugin": [
                            "other-plugin@1.0.0",
                            "do-the-thing@git+https://github.com/chendaleiQ/do-the-thing.git#old",
                            "do-the-thing@git+https://github.com/chendaleiQ/do-the-thing.git",
                            "other-plugin@1.0.0",
                            "do-the-thing@file:///tmp/local",
                        ]
                    }
                ),
                encoding="utf-8",
            )

            subprocess.run(
                [
                    sys.executable,
                    str(script),
                    "--config-path",
                    str(config_path),
                    "--set-opencode-plugin",
                    "do-the-thing@git+https://github.com/chendaleiQ/do-the-thing.git#v1.2.0",
                ],
                check=True,
            )

            self.assertEqual(
                json.loads(config_path.read_text(encoding="utf-8")),
                {
                    "plugin": [
                        "other-plugin@1.0.0",
                        "do-the-thing@git+https://github.com/chendaleiQ/do-the-thing.git#v1.2.0",
                    ]
                },
            )

    def test_set_opencode_plugin_creates_plugin_array_when_missing(self):
        repo_root = Path(__file__).resolve().parents[1]
        script = repo_root / "tools" / "opencode_config.py"

        with tempfile.TemporaryDirectory() as tmp:
            config_path = Path(tmp) / "opencode.json"
            config_path.write_text(json.dumps({"provider": "openai"}), encoding="utf-8")

            subprocess.run(
                [
                    sys.executable,
                    str(script),
                    "--config-path",
                    str(config_path),
                    "--set-opencode-plugin",
                    "do-the-thing@git+https://github.com/chendaleiQ/do-the-thing.git#main",
                ],
                check=True,
            )

            self.assertEqual(
                json.loads(config_path.read_text(encoding="utf-8")),
                {
                    "provider": "openai",
                    "plugin": [
                        "do-the-thing@git+https://github.com/chendaleiQ/do-the-thing.git#main"
                    ],
                },
            )


if __name__ == "__main__":
    unittest.main()
