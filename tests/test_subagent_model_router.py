import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from contextlib import redirect_stderr, redirect_stdout
from unittest import mock

from pack.tools import subagent_model_router
from pack.tools.subagent_model_router import (
    default_settings_path_for_config,
    load_local_opencode_config,
    load_provider_catalog,
    resolve_effective_provider,
)


class SubagentModelRouterTests(unittest.TestCase):
    def test_explicit_provider_outside_allowlist_raises(self):
        with self.assertRaisesRegex(ValueError, "not allowed"):
            resolve_effective_provider(
                current_provider="openai",
                provider_arg="openrouter",
                allowed_providers=["openai"],
                has_allowlist=True,
                detected_candidates=["openai", "openrouter"],
                provider_catalog={
                    "openai": ["gpt-5.4"],
                    "openrouter": ["anthropic/claude-sonnet-4.5"],
                },
            )

    def test_disallowed_current_provider_falls_back_inside_allowlist(self):
        provider, warnings = resolve_effective_provider(
            current_provider="openai",
            provider_arg="",
            allowed_providers=["openrouter"],
            has_allowlist=True,
            detected_candidates=["openai", "openrouter"],
            provider_catalog={},
        )

        self.assertEqual(provider, "openrouter")
        self.assertEqual(
            warnings,
            ["current provider 'openai' is not allowed; fell back to 'openrouter'"],
        )

    def test_allowed_current_provider_steps_aside_for_usable_allowed_provider(self):
        provider, warnings = resolve_effective_provider(
            current_provider="openai",
            provider_arg="",
            allowed_providers=["openai", "openrouter"],
            has_allowlist=True,
            detected_candidates=["openai", "openrouter"],
            provider_catalog={"openrouter": ["openai/gpt-5-mini"]},
        )

        self.assertEqual(provider, "openrouter")
        self.assertEqual(
            warnings,
            [
                "current provider 'openai' has no usable models; fell back to 'openrouter'"
            ],
        )

    def test_allowed_current_provider_with_config_models_stays_primary(self):
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
                    {"doTheThing": {"allowedProviders": ["openai", "openrouter"]}}
                ),
                encoding="utf-8",
            )
            (config_dir / "opencode.json").write_text(
                json.dumps({"provider": "openai", "model": "gpt-5.4"}),
                encoding="utf-8",
            )
            (cache_dir / "models.json").write_text(
                json.dumps({"openrouter": {"models": {"openai/gpt-5-mini": {}}}}),
                encoding="utf-8",
            )

            with mock.patch("pathlib.Path.home", return_value=home):
                with mock.patch.object(
                    sys,
                    "argv",
                    [
                        "subagent_model_router.py",
                        "--auto-detect-config",
                        "--triage-json",
                        '{"lane":"quick","taskType":"investigation","analysisTier":"tier_mid","executorTier":"tier_mid","reviewTier":"tier_mid","needsReviewer":false}',
                    ],
                ):
                    stdout = io.StringIO()
                    with redirect_stdout(stdout):
                        self.assertEqual(subagent_model_router.main(), 0)

            payload = json.loads(stdout.getvalue())
            self.assertEqual(payload["provider"], "openai")
            self.assertNotIn("fell back to 'openrouter'", json.dumps(payload))

    def test_allowed_current_provider_with_catalog_models_stays_primary(self):
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
                    {"doTheThing": {"allowedProviders": ["openai", "openrouter"]}}
                ),
                encoding="utf-8",
            )
            (config_dir / "opencode.json").write_text(
                json.dumps({"provider": "openai"}),
                encoding="utf-8",
            )
            (cache_dir / "models.json").write_text(
                json.dumps(
                    {
                        "openai": {"models": {"gpt-5.4": {}}},
                        "openrouter": {"models": {"openai/gpt-5-mini": {}}},
                    }
                ),
                encoding="utf-8",
            )

            with mock.patch("pathlib.Path.home", return_value=home):
                with mock.patch.object(
                    sys,
                    "argv",
                    [
                        "subagent_model_router.py",
                        "--auto-detect-config",
                        "--triage-json",
                        '{"lane":"quick","taskType":"investigation","analysisTier":"tier_mid","executorTier":"tier_mid","reviewTier":"tier_mid","needsReviewer":false}',
                    ],
                ):
                    stdout = io.StringIO()
                    with redirect_stdout(stdout):
                        self.assertEqual(subagent_model_router.main(), 0)

            payload = json.loads(stdout.getvalue())
            self.assertEqual(payload["provider"], "openai")
            self.assertNotIn("fell back to 'openrouter'", json.dumps(payload))

    def test_no_allowlist_allows_detected_candidates(self):
        provider, warnings = resolve_effective_provider(
            current_provider="openai",
            provider_arg="",
            allowed_providers=[],
            has_allowlist=False,
            detected_candidates=["openai", "openrouter"],
            provider_catalog={"openai": ["gpt-5.4"], "openrouter": []},
        )

        self.assertEqual(provider, "openai")
        self.assertEqual(warnings, [])

    def test_explicit_empty_allowlist_denies_all_providers(self):
        with self.assertRaisesRegex(ValueError, "no providers are allowed"):
            resolve_effective_provider(
                current_provider="openai",
                provider_arg="",
                allowed_providers=[],
                has_allowlist=True,
                detected_candidates=["openai", "openrouter"],
                provider_catalog={"openai": ["gpt-5.4"]},
            )

    def test_custom_config_path_uses_sibling_settings_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            config_dir = home / ".config" / "opencode"
            data_dir = home / ".local" / "share" / "opencode"
            cache_dir = home / ".cache" / "opencode"
            custom_dir = home / "custom-opencode"
            config_dir.mkdir(parents=True)
            data_dir.mkdir(parents=True)
            cache_dir.mkdir(parents=True)
            custom_dir.mkdir(parents=True)

            (custom_dir / "settings.json").write_text(
                json.dumps({"doTheThing": {"allowedProviders": ["openrouter"]}}),
                encoding="utf-8",
            )
            (custom_dir / "opencode.json").write_text(
                json.dumps({"provider": "openai"}),
                encoding="utf-8",
            )
            (cache_dir / "models.json").write_text(
                json.dumps(
                    {
                        "openai": {"models": {"gpt-5.4": {}}},
                        "openrouter": {"models": {"openai/gpt-5-mini": {}}},
                    }
                ),
                encoding="utf-8",
            )

            with mock.patch("pathlib.Path.home", return_value=home):
                with mock.patch.object(
                    sys,
                    "argv",
                    [
                        "subagent_model_router.py",
                        "--auto-detect-config",
                        "--config-path",
                        str(custom_dir / "opencode.json"),
                        "--triage-json",
                        '{"lane":"quick","taskType":"investigation","analysisTier":"tier_mid","executorTier":"tier_mid","reviewTier":"tier_mid","needsReviewer":false}',
                    ],
                ):
                    stdout = io.StringIO()
                    with redirect_stdout(stdout):
                        self.assertEqual(subagent_model_router.main(), 0)

            payload = json.loads(stdout.getvalue())
            self.assertEqual(payload["provider"], "openrouter")
            self.assertIn("fell back to 'openrouter'", json.dumps(payload))

    def test_default_settings_path_uses_config_path_parent_when_present(self):
        self.assertEqual(
            default_settings_path_for_config("/tmp/custom/opencode.json"),
            Path("/tmp/custom/settings.json"),
        )
        self.assertEqual(
            default_settings_path_for_config(""),
            Path.home() / ".config" / "opencode" / "settings.json",
        )

    def test_active_config_loader_ignores_settings_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            config_dir = home / ".config" / "opencode"
            config_dir.mkdir(parents=True)
            (config_dir / "settings.json").write_text(
                json.dumps(
                    {
                        "provider": "openrouter",
                        "doTheThing": {"allowedProviders": ["openai"]},
                    }
                ),
                encoding="utf-8",
            )

            with mock.patch("pathlib.Path.home", return_value=home):
                self.assertEqual(load_local_opencode_config(""), {})

    def test_allowed_provider_without_models_fails_in_main(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            config_dir = home / ".config" / "opencode"
            data_dir = home / ".local" / "share" / "opencode"
            cache_dir = home / ".cache" / "opencode"
            config_dir.mkdir(parents=True)
            data_dir.mkdir(parents=True)
            cache_dir.mkdir(parents=True)

            (config_dir / "settings.json").write_text(
                json.dumps({"doTheThing": {"allowedProviders": ["openai"]}}),
                encoding="utf-8",
            )
            (config_dir / "opencode.json").write_text(
                json.dumps({"provider": "openai"}),
                encoding="utf-8",
            )

            with mock.patch("pathlib.Path.home", return_value=home):
                with mock.patch.object(
                    sys,
                    "argv",
                    [
                        "subagent_model_router.py",
                        "--auto-detect-config",
                        "--triage-json",
                        '{"lane":"quick","taskType":"investigation","analysisTier":"tier_mid","executorTier":"tier_mid","reviewTier":"tier_mid","needsReviewer":false}',
                    ],
                ):
                    stderr = io.StringIO()
                    with redirect_stderr(stderr):
                        self.assertEqual(subagent_model_router.main(), 2)

            self.assertIn("no allowed provider", stderr.getvalue())

    def test_fallback_provider_does_not_inherit_other_provider_config_models(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            config_dir = home / ".config" / "opencode"
            data_dir = home / ".local" / "share" / "opencode"
            cache_dir = home / ".cache" / "opencode"
            config_dir.mkdir(parents=True)
            data_dir.mkdir(parents=True)
            cache_dir.mkdir(parents=True)

            (config_dir / "settings.json").write_text(
                json.dumps({"doTheThing": {"allowedProviders": ["openrouter"]}}),
                encoding="utf-8",
            )
            (config_dir / "opencode.json").write_text(
                json.dumps({"provider": "openai", "model": "gpt-5.4"}),
                encoding="utf-8",
            )

            with mock.patch("pathlib.Path.home", return_value=home):
                with mock.patch.object(
                    sys,
                    "argv",
                    [
                        "subagent_model_router.py",
                        "--auto-detect-config",
                        "--triage-json",
                        '{"lane":"quick","taskType":"investigation","analysisTier":"tier_mid","executorTier":"tier_mid","reviewTier":"tier_mid","needsReviewer":false}',
                    ],
                ):
                    stderr = io.StringIO()
                    with redirect_stderr(stderr):
                        self.assertEqual(subagent_model_router.main(), 2)

            self.assertIn("no allowed provider", stderr.getvalue())

    def test_provider_catalog_loads_models_from_models_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache_dir = Path(tmp) / ".cache" / "opencode"
            cache_dir.mkdir(parents=True)
            (cache_dir / "models.json").write_text(
                '{"openai":{"models":{"gpt-5.4":{},"gpt-5.4-mini":{}}},"openrouter":{"models":{"openai/gpt-5-mini":{}}}}',
                encoding="utf-8",
            )

            self.assertEqual(
                load_provider_catalog(cache_dir),
                {
                    "openai": ["gpt-5.4", "gpt-5.4-mini"],
                    "openrouter": ["openai/gpt-5-mini"],
                },
            )


if __name__ == "__main__":
    unittest.main()
