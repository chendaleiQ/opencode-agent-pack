import json
import io
import sys
import tempfile
import unittest
from pathlib import Path
from contextlib import redirect_stdout
from unittest import mock

import tools.provider_policy as provider_policy
from tools.provider_policy import (
    detect_provider_candidates,
    has_explicit_allowed_providers,
    merge_allowed_providers,
    read_allowed_providers,
)


class ProviderPolicyTests(unittest.TestCase):
    def test_detect_provider_candidates_prefers_local_sources_and_moves_active_provider_first(
        self,
    ):
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
                        "openrouter": {"type": "api", "key": "secret"},
                        "openai": {"type": "oauth", "access": "token"},
                    }
                ),
                encoding="utf-8",
            )
            (cache_dir / "models.json").write_text(
                json.dumps(
                    {
                        "anthropic": {"models": {}},
                        "openai": {"models": {"gpt-5.4": {}}},
                    }
                ),
                encoding="utf-8",
            )
            (config_dir / "opencode.json").write_text(
                json.dumps(
                    {
                        "provider": "minimax-cn-coding-plan",
                        "model": "MiniMax-M2.7",
                    }
                ),
                encoding="utf-8",
            )

            self.assertEqual(
                detect_provider_candidates(
                    config_dir=config_dir,
                    data_dir=data_dir,
                    cache_dir=cache_dir,
                ),
                [
                    "minimax-cn-coding-plan",
                    "anthropic",
                    "openai",
                    "openrouter",
                ],
            )

    def test_merge_allowed_providers_preserves_unrelated_settings(self):
        merged = merge_allowed_providers(
            {
                "theme": "solarized",
                "doTheThing": {"otherSetting": True},
            },
            ["openai", "openrouter"],
        )

        self.assertEqual(merged["theme"], "solarized")
        self.assertEqual(merged["doTheThing"]["otherSetting"], True)
        self.assertEqual(
            merged["doTheThing"]["allowedProviders"],
            ["openai", "openrouter"],
        )

    def test_merge_allowed_providers_keeps_caller_list_as_is(self):
        merged = merge_allowed_providers({}, ["openai", "", 123, "openrouter"])

        self.assertEqual(
            merged["doTheThing"]["allowedProviders"], ["openai", "", 123, "openrouter"]
        )

    def test_has_explicit_allowed_providers_distinguishes_missing_from_empty(self):
        self.assertFalse(has_explicit_allowed_providers({}))
        self.assertFalse(has_explicit_allowed_providers({"doTheThing": {}}))
        self.assertTrue(
            has_explicit_allowed_providers({"doTheThing": {"allowedProviders": []}})
        )
        self.assertEqual(
            read_allowed_providers({"doTheThing": {"allowedProviders": []}}),
            [],
        )

    def test_cli_rejects_invalid_allowed_providers_json(self):
        with mock.patch.object(
            sys,
            "argv",
            [
                "provider_policy.py",
                "--settings-path",
                str(Path("/tmp/settings.json")),
                "--set-allowed-providers-json",
                '["openai", ""]',
            ],
        ):
            with self.assertRaises(SystemExit) as ctx:
                provider_policy.main()

        self.assertEqual(
            str(ctx.exception),
            "allowed providers must be a JSON array of non-empty strings",
        )

    def test_cli_round_trip_writes_and_reads_settings_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            settings_path = Path(tmp) / "settings.json"
            with mock.patch.object(
                sys,
                "argv",
                [
                    "provider_policy.py",
                    "--settings-path",
                    str(settings_path),
                    "--set-allowed-providers-json",
                    '["openai", "openrouter"]',
                ],
            ):
                self.assertEqual(provider_policy.main(), 0)

            with mock.patch.object(
                sys,
                "argv",
                [
                    "provider_policy.py",
                    "--settings-path",
                    str(settings_path),
                    "--print-allowed-providers",
                ],
            ):
                stdout = io.StringIO()
                with redirect_stdout(stdout):
                    self.assertEqual(provider_policy.main(), 0)

            self.assertEqual(json.loads(stdout.getvalue()), ["openai", "openrouter"])
            self.assertEqual(
                json.loads(settings_path.read_text(encoding="utf-8"))["doTheThing"][
                    "allowedProviders"
                ],
                ["openai", "openrouter"],
            )

    def test_cli_rejects_malformed_settings_json_on_read_and_write_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            settings_path = Path(tmp) / "settings.json"
            settings_path.write_text("{", encoding="utf-8")

            with mock.patch.object(
                sys,
                "argv",
                [
                    "provider_policy.py",
                    "--settings-path",
                    str(settings_path),
                    "--print-allowed-providers",
                ],
            ):
                with self.assertRaises(SystemExit) as ctx:
                    provider_policy.main()
                self.assertEqual(
                    str(ctx.exception),
                    "invalid settings.json: expected a JSON object",
                )

            with mock.patch.object(
                sys,
                "argv",
                [
                    "provider_policy.py",
                    "--settings-path",
                    str(settings_path),
                    "--set-allowed-providers-json",
                    '["openai"]',
                ],
            ):
                with self.assertRaises(SystemExit) as ctx:
                    provider_policy.main()
                self.assertEqual(
                    str(ctx.exception),
                    "invalid settings.json: expected a JSON object",
                )

    def test_cli_detect_providers_ignores_malformed_settings_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            config_dir = home / ".config" / "opencode"
            data_dir = home / ".local" / "share" / "opencode"
            cache_dir = home / ".cache" / "opencode"
            config_dir.mkdir(parents=True)
            data_dir.mkdir(parents=True)
            cache_dir.mkdir(parents=True)

            (data_dir / "auth.json").write_text(
                json.dumps({"openai": {"type": "oauth", "access": "token"}}),
                encoding="utf-8",
            )
            (config_dir / "opencode.json").write_text(
                json.dumps({"provider": "openai", "model": "gpt-5.4"}),
                encoding="utf-8",
            )
            (config_dir / "settings.json").write_text("{", encoding="utf-8")

            with mock.patch.object(
                sys,
                "argv",
                [
                    "provider_policy.py",
                    "--config-dir",
                    str(config_dir),
                    "--data-dir",
                    str(data_dir),
                    "--cache-dir",
                    str(cache_dir),
                    "--detect-providers",
                ],
            ):
                stdout = io.StringIO()
                with redirect_stdout(stdout):
                    self.assertEqual(provider_policy.main(), 0)

            self.assertEqual(json.loads(stdout.getvalue()), ["openai"])

    def test_cli_rejects_structurally_malformed_pack_settings(self):
        malformed_payloads = [
            '{"doTheThing": []}',
            '{"doTheThing": {"allowedProviders": "openai"}}',
            '{"doTheThing": {"allowedProviders": ["openai", 123, ""]}}',
        ]
        for payload in malformed_payloads:
            with self.subTest(payload=payload):
                with tempfile.TemporaryDirectory() as tmp:
                    settings_path = Path(tmp) / "settings.json"
                    settings_path.write_text(payload, encoding="utf-8")

                    with mock.patch.object(
                        sys,
                        "argv",
                        [
                            "provider_policy.py",
                            "--settings-path",
                            str(settings_path),
                            "--print-allowed-providers",
                        ],
                    ):
                        with self.assertRaises(SystemExit) as ctx:
                            provider_policy.main()
                    expected_message = (
                        "invalid settings.json: expected doTheThing to be a JSON object"
                        if payload == '{"doTheThing": []}'
                        else "invalid settings.json: expected allowedProviders to be a JSON array"
                    )
                    if (
                        payload
                        == '{"doTheThing": {"allowedProviders": ["openai", 123, ""]}}'
                    ):
                        expected_message = "invalid settings.json: expected allowedProviders entries to be non-empty strings"
                    self.assertEqual(str(ctx.exception), expected_message)

                    with mock.patch.object(
                        sys,
                        "argv",
                        [
                            "provider_policy.py",
                            "--settings-path",
                            str(settings_path),
                            "--set-allowed-providers-json",
                            '["openai"]',
                        ],
                    ):
                        with self.assertRaises(SystemExit) as ctx:
                            provider_policy.main()
                    expected_message = (
                        "invalid settings.json: expected doTheThing to be a JSON object"
                        if payload == '{"doTheThing": []}'
                        else "invalid settings.json: expected allowedProviders to be a JSON array"
                    )
                    if (
                        payload
                        == '{"doTheThing": {"allowedProviders": ["openai", 123, ""]}}'
                    ):
                        expected_message = "invalid settings.json: expected allowedProviders entries to be non-empty strings"
                    self.assertEqual(str(ctx.exception), expected_message)

    def test_cli_rejects_multiple_actions(self):
        with mock.patch.object(
            sys,
            "argv",
            [
                "provider_policy.py",
                "--detect-providers",
                "--print-allowed-providers",
            ],
        ):
            with self.assertRaises(SystemExit) as ctx:
                provider_policy.main()

        self.assertEqual(
            str(ctx.exception),
            "choose one action: specify exactly one of --detect-providers, --print-allowed-providers, or --set-allowed-providers-json",
        )

    def test_read_allowed_providers_returns_empty_when_missing(self):
        self.assertEqual(read_allowed_providers({}), [])


if __name__ == "__main__":
    unittest.main()
