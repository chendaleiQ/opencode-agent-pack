# Provider Allowlist Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a pack-scoped provider allowlist that users configure during install and can later reconfigure with `/providers`, with router enforcement that never routes outside the configured provider set.

**Architecture:** Introduce a small Python helper module to centralize provider detection and `settings.json` read/write logic. Reuse that helper from the router and both installers so the allowlist behavior stays consistent across bash, PowerShell, and command-driven reconfiguration.

**Tech Stack:** Python 3 stdlib (`argparse`, `json`, `pathlib`, `unittest`), bash, PowerShell, markdown command files

---

### Task 1: Add a Shared Provider Policy Helper

**Files:**
- Create: `pack/tools/provider_policy.py`
- Create: `tests/test_provider_policy.py`

- [ ] **Step 1: Write the failing tests for provider candidate discovery and settings merge**

```python
import json
import tempfile
import unittest
from pathlib import Path

from pack.tools.provider_policy import (
    detect_provider_candidates,
    merge_allowed_providers,
    read_allowed_providers,
)


class ProviderPolicyTests(unittest.TestCase):
    def test_detect_provider_candidates_prefers_local_sources_and_moves_active_provider_first(self):
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
                "opencodeAgentPack": {"otherSetting": True},
            },
            ["openai", "openrouter"],
        )

        self.assertEqual(merged["theme"], "solarized")
        self.assertEqual(merged["opencodeAgentPack"]["otherSetting"], True)
        self.assertEqual(
            merged["opencodeAgentPack"]["allowedProviders"],
            ["openai", "openrouter"],
        )

    def test_read_allowed_providers_returns_empty_when_missing(self):
        self.assertEqual(read_allowed_providers({}), [])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python3 -m unittest tests/test_provider_policy.py -v`

Expected: `ImportError` or `ModuleNotFoundError` for `pack.tools.provider_policy`

- [ ] **Step 3: Write the minimal helper implementation and CLI**

```python
import argparse
import json
from pathlib import Path
from typing import Any, Dict, List


def _load_json_file(path: Path) -> Dict[str, Any]:
    if not path.exists() or not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def detect_provider_candidates(config_dir: Path, data_dir: Path, cache_dir: Path) -> List[str]:
    config_obj = _load_json_file(config_dir / "opencode.json")
    auth_obj = _load_json_file(data_dir / "auth.json")
    models_obj = _load_json_file(cache_dir / "models.json")

    active_provider = config_obj.get("provider", "")
    found = set()
    found.update(k for k in auth_obj.keys() if isinstance(k, str) and k)
    found.update(k for k in models_obj.keys() if isinstance(k, str) and k)
    if isinstance(active_provider, str) and active_provider:
        found.add(active_provider)

    ordered = sorted(found)
    if active_provider in ordered:
        ordered.remove(active_provider)
        ordered.insert(0, active_provider)
    return ordered


def read_allowed_providers(settings_obj: Dict[str, Any]) -> List[str]:
    pack_obj = settings_obj.get("opencodeAgentPack", {})
    if not isinstance(pack_obj, dict):
        return []
    raw = pack_obj.get("allowedProviders", [])
    if not isinstance(raw, list):
        return []
    return [item for item in raw if isinstance(item, str) and item]


def merge_allowed_providers(settings_obj: Dict[str, Any], allowed: List[str]) -> Dict[str, Any]:
    merged = dict(settings_obj)
    pack_obj = merged.get("opencodeAgentPack", {})
    if not isinstance(pack_obj, dict):
        pack_obj = {}
    pack_obj = dict(pack_obj)
    pack_obj["allowedProviders"] = allowed
    merged["opencodeAgentPack"] = pack_obj
    return merged


def main() -> int:
    parser = argparse.ArgumentParser(description="Detect and persist pack-scoped provider policy")
    parser.add_argument("--config-dir", default=str(Path.home() / ".config" / "opencode"))
    parser.add_argument("--data-dir", default=str(Path.home() / ".local" / "share" / "opencode"))
    parser.add_argument("--cache-dir", default=str(Path.home() / ".cache" / "opencode"))
    parser.add_argument("--settings-path", default="")
    parser.add_argument("--detect-providers", action="store_true")
    parser.add_argument("--print-allowed-providers", action="store_true")
    parser.add_argument("--set-allowed-providers-json", default="")
    args = parser.parse_args()

    settings_path = Path(args.settings_path) if args.settings_path else Path(args.config_dir) / "settings.json"
    settings_obj = _load_json_file(settings_path)

    if args.detect_providers:
        print(json.dumps(detect_provider_candidates(Path(args.config_dir), Path(args.data_dir), Path(args.cache_dir))))
        return 0

    if args.print_allowed_providers:
        print(json.dumps(read_allowed_providers(settings_obj)))
        return 0

    if args.set_allowed_providers_json:
        allowed = json.loads(args.set_allowed_providers_json)
        if not isinstance(allowed, list) or not all(isinstance(item, str) and item for item in allowed):
            raise SystemExit("allowed providers must be a JSON array of non-empty strings")
        settings_path.parent.mkdir(parents=True, exist_ok=True)
        settings_path.write_text(
            json.dumps(merge_allowed_providers(settings_obj, allowed), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        return 0

    raise SystemExit("choose one action: --detect-providers, --print-allowed-providers, or --set-allowed-providers-json")


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python3 -m unittest tests/test_provider_policy.py -v`

Expected: `OK`

- [ ] **Step 5: Commit**

```bash
git add pack/tools/provider_policy.py tests/test_provider_policy.py
git commit -m "feat: add provider allowlist helper"
```

### Task 2: Enforce the Allowlist in the Router

**Files:**
- Modify: `pack/tools/subagent_model_router.py`
- Create: `tests/test_subagent_model_router.py`
- Modify: `pack/tools/provider_policy.py`

- [ ] **Step 1: Write the failing router tests**

```python
import tempfile
import unittest
from pathlib import Path

from pack.tools.provider_policy import merge_allowed_providers
from pack.tools.subagent_model_router import (
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
                detected_candidates=["openai", "openrouter"],
                provider_catalog={"openai": ["gpt-5.4"], "openrouter": ["anthropic/claude-sonnet-4.5"]},
            )

    def test_disallowed_current_provider_falls_back_inside_allowlist(self):
        provider, warnings = resolve_effective_provider(
            current_provider="openai",
            provider_arg="",
            allowed_providers=["openrouter"],
            detected_candidates=["openai", "openrouter"],
            provider_catalog={"openai": ["gpt-5.4"], "openrouter": ["openai/gpt-5-mini"]},
        )
        self.assertEqual(provider, "openrouter")
        self.assertEqual(
            warnings,
            ["current provider 'openai' is not allowed; fell back to 'openrouter'"],
        )

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
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python3 -m unittest tests/test_subagent_model_router.py -v`

Expected: `ImportError` for the new router functions

- [ ] **Step 3: Update the router to use settings allowlists and cached model catalogs**

```python
from pack.tools.provider_policy import (
    detect_provider_candidates,
    read_allowed_providers,
)


def load_provider_catalog(cache_dir: Path) -> Dict[str, List[str]]:
    payload = {}
    models_path = cache_dir / "models.json"
    if models_path.exists() and models_path.is_file():
        try:
            payload = json.loads(models_path.read_text(encoding="utf-8"))
        except Exception:
            payload = {}

    catalog: Dict[str, List[str]] = {}
    for provider, info in payload.items():
        if not isinstance(provider, str) or not isinstance(info, dict):
            continue
        models = info.get("models", {})
        if isinstance(models, dict):
            catalog[provider] = sorted([key for key in models.keys() if isinstance(key, str) and key])
    return catalog


def resolve_effective_provider(
    current_provider: str,
    provider_arg: str,
    allowed_providers: List[str],
    detected_candidates: List[str],
    provider_catalog: Dict[str, List[str]],
) -> Tuple[str, List[str]]:
    warnings: List[str] = []
    effective_allowed = allowed_providers or detected_candidates
    if provider_arg:
        if effective_allowed and provider_arg not in effective_allowed:
            raise ValueError(f"provider '{provider_arg}' is not allowed")
        return provider_arg, warnings

    if current_provider and current_provider in effective_allowed:
        return current_provider, warnings

    if current_provider and effective_allowed and current_provider not in effective_allowed:
        for candidate in effective_allowed:
            if provider_catalog.get(candidate):
                warnings.append(
                    f"current provider '{current_provider}' is not allowed; fell back to '{candidate}'"
                )
                return candidate, warnings

    if effective_allowed:
        return effective_allowed[0], warnings

    return current_provider or "openai", warnings
```

Also update `main()` so that it:
- loads `settings.json`
- reads `allowedProviders`
- loads `~/.cache/opencode/models.json`
- constrains provider selection and `available_models`
- prefers cached provider catalog models before network discovery

Use this shape in `main()`:

```python
config_dir = Path.home() / ".config" / "opencode"
data_dir = Path.home() / ".local" / "share" / "opencode"
cache_dir = Path.home() / ".cache" / "opencode"
settings_obj = load_local_opencode_config(str(config_dir / "settings.json"))
allowed_providers = read_allowed_providers(settings_obj)
detected_candidates = detect_provider_candidates(config_dir, data_dir, cache_dir)
provider_catalog = load_provider_catalog(cache_dir)
provider, allowlist_warnings = resolve_effective_provider(
    current_provider=detect_provider(config_obj, ""),
    provider_arg=args.provider,
    allowed_providers=allowed_providers,
    detected_candidates=detected_candidates,
    provider_catalog=provider_catalog,
)
warnings.extend(allowlist_warnings)
available_models = list(dict.fromkeys(provider_catalog.get(provider, []) + available_models))
```

- [ ] **Step 4: Run the router tests and the existing helper tests**

Run: `python3 -m unittest tests/test_provider_policy.py tests/test_subagent_model_router.py -v`

Expected: `OK`

- [ ] **Step 5: Commit**

```bash
git add pack/tools/provider_policy.py pack/tools/subagent_model_router.py tests/test_subagent_model_router.py
git commit -m "feat: enforce provider allowlists in router"
```

### Task 3: Add Non-Interactive Default-All Configuration to the Bash Installer

**Files:**
- Modify: `install.sh`
- Create: `tests/test_install_sh_provider_allowlist.py`

- [ ] **Step 1: Write the failing bash installer smoke test**

```python
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path


class InstallShProviderAllowlistTests(unittest.TestCase):
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
                '{"openai":{"type":"oauth","access":"token"},"openrouter":{"type":"api","key":"secret"}}',
                encoding="utf-8",
            )
            (cache_dir / "models.json").write_text(
                '{"anthropic":{"models":{"claude-sonnet-4-5-20250929":{}}}}',
                encoding="utf-8",
            )
            (config_dir / "opencode.json").write_text(
                '{"provider":"openai","model":"gpt-5.4"}',
                encoding="utf-8",
            )

            completed = subprocess.run(
                ["bash", "install.sh"],
                cwd=repo_root,
                env={**os.environ, "HOME": str(home)},
                text=True,
                capture_output=True,
                check=True,
            )

            self.assertIn("Installed opencode-agent-pack", completed.stdout)
            settings = json.loads((config_dir / "settings.json").read_text(encoding="utf-8"))
            self.assertEqual(
                settings["opencodeAgentPack"]["allowedProviders"],
                ["openai", "anthropic", "openrouter"],
            )


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python3 -m unittest tests/test_install_sh_provider_allowlist.py -v`

Expected: failure because `settings.json` does not contain `opencodeAgentPack.allowedProviders`

- [ ] **Step 3: Update `install.sh` to detect providers and write default-all settings**

```bash
PYTHON_BIN="${PYTHON_BIN:-python3}"

detect_provider_candidates() {
  "$PYTHON_BIN" "${SCRIPT_DIR}/pack/tools/provider_policy.py" \
    --config-dir "${HOME}/.config/opencode" \
    --data-dir "${HOME}/.local/share/opencode" \
    --cache-dir "${HOME}/.cache/opencode" \
    --detect-providers
}

write_allowed_providers() {
  local settings_path="$1"
  local allowed_json="$2"
  "$PYTHON_BIN" "${SCRIPT_DIR}/pack/tools/provider_policy.py" \
    --settings-path "$settings_path" \
    --set-allowed-providers-json "$allowed_json"
}
```

After `cp -R "${PACK_DIR}/." "$TARGET/"`, add:

```bash
candidate_json="$(detect_provider_candidates)"
selection_json="$candidate_json"

if [ -t 0 ]; then
  echo "Select allowed providers for opencode-agent-pack"
  "$PYTHON_BIN" "${SCRIPT_DIR}/pack/tools/provider_policy.py" \
    --config-dir "${HOME}/.config/opencode" \
    --data-dir "${HOME}/.local/share/opencode" \
    --cache-dir "${HOME}/.cache/opencode" \
    --detect-providers
  echo "Press Enter to accept all detected providers."
else
  echo "Non-interactive install detected; defaulting to all detected providers."
fi

write_allowed_providers "${TARGET}/settings.json" "$selection_json"
```

If you choose to support interactive numeric selection in bash now, do it in the same script after the `-t 0` check by:
- parsing the JSON array into indexed lines with `python3 - <<'PY'`
- reading a comma-separated selection
- mapping indexes back to provider names
- falling back to the full list on empty input

- [ ] **Step 4: Run the bash installer test**

Run: `python3 -m unittest tests/test_install_sh_provider_allowlist.py -v`

Expected: `OK`

- [ ] **Step 5: Commit**

```bash
git add install.sh tests/test_install_sh_provider_allowlist.py
git commit -m "feat: write provider allowlists during bash install"
```

### Task 4: Add PowerShell Installer Parity and the `/providers` Command

**Files:**
- Modify: `install.ps1`
- Create: `pack/commands/providers.md`

- [ ] **Step 1: Update `install.ps1` to mirror the bash installer flow**

```powershell
$pythonBin = if ($env:PYTHON_BIN) { $env:PYTHON_BIN } else { "python3" }

function Get-ProviderCandidatesJson {
    & $pythonBin (Join-Path $ScriptDir "pack/tools/provider_policy.py") `
        --config-dir (Join-Path $home ".config/opencode") `
        --data-dir (Join-Path $home ".local/share/opencode") `
        --cache-dir (Join-Path $home ".cache/opencode") `
        --detect-providers
}

function Set-AllowedProviders {
    param(
        [string]$SettingsPath,
        [string]$AllowedJson
    )

    & $pythonBin (Join-Path $ScriptDir "pack/tools/provider_policy.py") `
        --settings-path $SettingsPath `
        --set-allowed-providers-json $AllowedJson
}
```

After the pack copy and config restore, add:

```powershell
$candidateJson = Get-ProviderCandidatesJson
$selectionJson = $candidateJson

if ($Host.Name -match "ConsoleHost") {
    Write-Host "Select allowed providers for opencode-agent-pack"
    Write-Host "Press Enter to accept all detected providers."
} else {
    Write-Host "Non-interactive install detected; defaulting to all detected providers."
}

Set-AllowedProviders -SettingsPath (Join-Path $resolvedTarget "settings.json") -AllowedJson $selectionJson
```

- [ ] **Step 2: Run a manual PowerShell smoke check**

Run:

```bash
TMP_HOME="$(mktemp -d)"
mkdir -p "$TMP_HOME/.config/opencode" "$TMP_HOME/.local/share/opencode" "$TMP_HOME/.cache/opencode"
printf '{"openai":{"type":"oauth","access":"token"}}' > "$TMP_HOME/.local/share/opencode/auth.json"
pwsh -File install.ps1 -Target "$TMP_HOME/.config/opencode"
sed -n '1,40p' "$TMP_HOME/.config/opencode/settings.json"
```

Expected:
- installer prints `Installed opencode-agent-pack`
- `settings.json` includes `opencodeAgentPack.allowedProviders`

- [ ] **Step 3: Add the `/providers` command file**

```markdown
# Command: /providers

## Purpose
Inspect and update the provider allowlist used by opencode-agent-pack routing.

## Leader Instructions
- Read `~/.config/opencode/settings.json`
- Read provider candidates from `~/.local/share/opencode/auth.json`, `~/.cache/opencode/models.json`, and `~/.config/opencode/opencode.json`
- Show the current allowed provider list
- Ask the user for the replacement multi-select choice
- Update `settings.json` so `opencodeAgentPack.allowedProviders` matches the new selection
- Confirm the final saved provider list

## Scope Boundary
- Only update pack-owned settings
- Do not modify `opencode.json`
- Do not expose secrets from `auth.json`
```

- [ ] **Step 4: Verify the command file content and installer parity**

Run:

```bash
sed -n '1,220p' pack/commands/providers.md
rg -n "allowedProviders|provider_policy.py|Non-interactive install detected" install.sh install.ps1 pack/commands/providers.md
```

Expected:
- `/providers` instructions mention only pack-scoped settings
- both installers call `provider_policy.py`
- both installers write `allowedProviders`

- [ ] **Step 5: Commit**

```bash
git add install.ps1 pack/commands/providers.md
git commit -m "feat: add provider allowlist command and powershell install support"
```

### Task 5: Update Documentation and Run Full Verification

**Files:**
- Modify: `README.md`
- Modify: `docs/pack-methods/specs/2026-04-08-provider-allowlist-design.md`

- [ ] **Step 1: Update the README install and usage sections**

```markdown
## Install

- installer defaults to global install (`~/.config/opencode/`)
- installer now configures a pack-scoped provider allowlist during install
- provider selection defaults to all detected local providers
- provider policy is stored in `settings.json` under `opencodeAgentPack.allowedProviders`

## Use

After install, user workflow is intentionally simple:
1. switch to `leader` agent, then ask task directly
2. use `/providers` any time to reconfigure allowed routing providers
3. `leader` handles triage/routing/escalation within the documented workflow
```

Update the optional router tool section to mention:

```markdown
- routing is constrained by the pack-scoped provider allowlist in `settings.json`
- when the active provider is disallowed, the router falls back inside the allowlist
```

- [ ] **Step 2: Run the full Python verification suite**

Run: `python3 -m unittest tests/test_provider_policy.py tests/test_subagent_model_router.py tests/test_install_sh_provider_allowlist.py -v`

Expected: `OK`

- [ ] **Step 3: Run one router smoke check with a temporary HOME**

Run:

```bash
TMP_HOME="$(mktemp -d)"
mkdir -p "$TMP_HOME/.config/opencode" "$TMP_HOME/.local/share/opencode" "$TMP_HOME/.cache/opencode"
printf '{"provider":"openai","model":"gpt-5.4"}' > "$TMP_HOME/.config/opencode/opencode.json"
printf '{"openrouter":{"type":"api","key":"secret"}}' > "$TMP_HOME/.local/share/opencode/auth.json"
printf '{"opencodeAgentPack":{"allowedProviders":["openrouter"]}}' > "$TMP_HOME/.config/opencode/settings.json"
printf '{"openrouter":{"models":{"openai/gpt-5-mini":{}}},"openai":{"models":{"gpt-5.4":{}}}}' > "$TMP_HOME/.cache/opencode/models.json"
HOME="$TMP_HOME" python3 pack/tools/subagent_model_router.py \
  --auto-detect-config \
  --triage-json '{"taskType":"feature","lane":"quick","analysisTier":"tier_fast","executorTier":"tier_fast","reviewTier":"tier_mid","needsReviewer":false}'
```

Expected:
- output `provider` is `openrouter`
- `warnings` mentions the fallback from `openai`
- `availableModelsSource` includes cached/local sources rather than only config

- [ ] **Step 4: Review the final diff for scope discipline**

Run:

```bash
git diff -- install.sh install.ps1 README.md pack/commands/providers.md pack/tools/provider_policy.py pack/tools/subagent_model_router.py tests/test_provider_policy.py tests/test_subagent_model_router.py tests/test_install_sh_provider_allowlist.py
```

Expected:
- diff is limited to provider allowlist config, router enforcement, installer flow, `/providers`, and docs
- no secrets appear in repo changes
- no changes rewrite `opencode.json`

- [ ] **Step 5: Commit**

```bash
git add README.md docs/pack-methods/specs/2026-04-08-provider-allowlist-design.md
git commit -m "docs: document provider allowlist workflow"
```

## Self-Review

### Spec coverage
- Install-time mandatory provider selection with Enter-for-all: covered in Tasks 3 and 4
- Post-install `/providers` reconfiguration: covered in Task 4
- `settings.json` storage under `opencodeAgentPack.allowedProviders`: covered in Tasks 1, 3, and 4
- Router enforcement and fallback inside allowlist: covered in Task 2 and verified in Task 5
- Pack scope only, no global OpenCode provider changes: covered in Task 4 and Task 5 diff review
- No model-level allowlist in this change: kept out of every task

### Placeholder scan
- No `TBD`, `TODO`, or “implement later” placeholders remain.
- Each code-changing step includes actual code.
- Each verification step includes exact commands and expected outcomes.

### Type consistency
- `allowedProviders` is consistently named in helper, router, installers, command docs, and README.
- The helper CLI flags are used consistently as `--detect-providers`, `--print-allowed-providers`, and `--set-allowed-providers-json`.
