#!/usr/bin/env python3
import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib import error, request

from pack.tools.provider_policy import (
    detect_provider_candidates,
    has_explicit_allowed_providers,
    load_settings,
    read_allowed_providers,
)


PREFERRED_MODELS = {
    "openai": {
        "tier_top": ["gpt-5.4", "gpt-5.3", "gpt-5"],
        "tier_mid": ["gpt-5.3", "gpt-5.4-mini", "gpt-5-mini"],
        "tier_fast": ["gpt-5.4-mini", "gpt-5-mini", "gpt-5.3"],
    }
}

FAST_HINTS = [
    "mini",
    "nano",
    "lite",
    "flash",
    "haiku",
    "small",
    "8b",
]

TOP_HINTS = [
    "opus",
    "pro",
    "sonnet",
    "70b",
    "90b",
    "405b",
    "ultra",
    "gpt-5",
    "claude-4",
    "claude-3.7",
]


def _env_tier_overrides() -> Dict[str, str]:
    return {
        "tier_fast": os.getenv("OPENCODE_MODEL_TIER_FAST", ""),
        "tier_mid": os.getenv("OPENCODE_MODEL_TIER_MID", ""),
        "tier_top": os.getenv("OPENCODE_MODEL_TIER_TOP", ""),
    }


def _parse_json(raw: str, name: str) -> Dict[str, Any]:
    stripped = raw.strip()
    if stripped == "...":
        raise ValueError(
            f"invalid {name}: '...' is a placeholder, provide a real JSON object"
        )
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid {name}: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"{name} must be a JSON object")
    return data


def _parse_json_list(raw: str, name: str) -> List[str]:
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid {name}: {exc}") from exc
    if not isinstance(data, list):
        raise ValueError(f"{name} must be a JSON array")
    out: List[str] = []
    for item in data:
        if isinstance(item, str) and item:
            out.append(item)
    return out


def _request_json(url: str, headers: Optional[Dict[str, str]] = None, timeout: int = 20) -> Dict[str, Any]:
    req = request.Request(url)
    if headers:
        for k, v in headers.items():
            req.add_header(k, v)
    with request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _extract_model_ids_from_payload(payload: Dict[str, Any]) -> List[str]:
    data = payload.get("data", [])
    models: List[str] = []
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                model_id = item.get("id") or item.get("name")
                if isinstance(model_id, str) and model_id:
                    models.append(model_id)
    return models


def discover_openai_models(api_key: str) -> List[str]:
    base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com").rstrip("/")
    url = f"{base_url}/v1/models"
    try:
        payload = _request_json(url, {"Authorization": f"Bearer {api_key}"})
    except error.HTTPError as exc:
        raise ValueError(f"openai model discovery failed: http {exc.code}") from exc
    except error.URLError as exc:
        raise ValueError(f"openai model discovery failed: {exc.reason}") from exc
    return sorted(set(_extract_model_ids_from_payload(payload)))


def discover_openrouter_models(api_key: str) -> List[str]:
    base_url = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai").rstrip("/")
    url = f"{base_url}/api/v1/models"
    try:
        payload = _request_json(url, {"Authorization": f"Bearer {api_key}"})
    except error.HTTPError as exc:
        raise ValueError(f"openrouter model discovery failed: http {exc.code}") from exc
    except error.URLError as exc:
        raise ValueError(f"openrouter model discovery failed: {exc.reason}") from exc
    return sorted(set(_extract_model_ids_from_payload(payload)))


def discover_anthropic_models(api_key: str) -> List[str]:
    url = "https://api.anthropic.com/v1/models"
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
    }
    try:
        payload = _request_json(url, headers)
    except error.HTTPError as exc:
        raise ValueError(f"anthropic model discovery failed: http {exc.code}") from exc
    except error.URLError as exc:
        raise ValueError(f"anthropic model discovery failed: {exc.reason}") from exc
    return sorted(set(_extract_model_ids_from_payload(payload)))


def discover_ollama_models() -> List[str]:
    base_url = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434").rstrip("/")
    url = f"{base_url}/api/tags"
    try:
        payload = _request_json(url)
    except error.HTTPError as exc:
        raise ValueError(f"ollama model discovery failed: http {exc.code}") from exc
    except error.URLError as exc:
        raise ValueError(f"ollama model discovery failed: {exc.reason}") from exc

    models: List[str] = []
    data = payload.get("models", [])
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                name = item.get("name")
                if isinstance(name, str) and name:
                    models.append(name)
    return sorted(set(models))


def discover_provider_models(provider: str) -> Tuple[List[str], List[str]]:
    warnings: List[str] = []
    models: List[str] = []

    try:
        if provider == "openai":
            api_key = os.getenv("OPENAI_API_KEY", "")
            if not api_key:
                warnings.append("OPENAI_API_KEY not set; skip openai discovery")
            else:
                models = discover_openai_models(api_key)
        elif provider == "openrouter":
            api_key = os.getenv("OPENROUTER_API_KEY", "")
            if not api_key:
                warnings.append("OPENROUTER_API_KEY not set; skip openrouter discovery")
            else:
                models = discover_openrouter_models(api_key)
        elif provider == "anthropic":
            api_key = os.getenv("ANTHROPIC_API_KEY", "")
            if not api_key:
                warnings.append("ANTHROPIC_API_KEY not set; skip anthropic discovery")
            else:
                models = discover_anthropic_models(api_key)
        elif provider == "ollama":
            models = discover_ollama_models()
        else:
            warnings.append(f"provider '{provider}' has no built-in discovery; use --available-models-json")
    except ValueError as exc:
        warnings.append(str(exc))

    return models, warnings


def _extract_strings_by_key(obj: Any, key_patterns: List[str], out: List[str]) -> None:
    if isinstance(obj, dict):
        for k, v in obj.items():
            k_norm = str(k).lower()
            if any(p in k_norm for p in key_patterns):
                if isinstance(v, str) and v:
                    out.append(v)
                elif isinstance(v, list):
                    for item in v:
                        if isinstance(item, str) and item:
                            out.append(item)
            _extract_strings_by_key(v, key_patterns, out)
    elif isinstance(obj, list):
        for item in obj:
            _extract_strings_by_key(item, key_patterns, out)


def load_local_opencode_config(config_path: str) -> Dict[str, Any]:
    candidate_paths: List[Path] = []
    if config_path:
        candidate_paths.append(Path(config_path))
    else:
        home = Path.home()
        candidate_paths.append(home / ".config" / "opencode" / "opencode.json")

    for path in candidate_paths:
        if path.exists() and path.is_file():
            try:
                return json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                continue
    return {}


def default_settings_path_for_config(config_path: str) -> Path:
    if config_path:
        return Path(config_path).expanduser().parent / "settings.json"
    return Path.home() / ".config" / "opencode" / "settings.json"


def detect_provider(config_obj: Dict[str, Any], provider_arg: str) -> str:
    if provider_arg:
        return provider_arg

    env_provider = os.getenv("OPENCODE_PROVIDER", "")
    if env_provider:
        return env_provider

    found: List[str] = []
    _extract_strings_by_key(config_obj, ["provider"], found)
    if found:
        return found[0].lower()

    return "openai"


def detect_config_provider(config_obj: Dict[str, Any]) -> str:
    found: List[str] = []
    _extract_strings_by_key(config_obj, ["provider"], found)
    return found[0].lower() if found else ""


def detect_models_from_config(config_obj: Dict[str, Any]) -> List[str]:
    found: List[str] = []
    _extract_strings_by_key(config_obj, ["model", "models", "defaultmodel"], found)

    cleaned: List[str] = []
    for m in found:
        # Filter obvious non-model values.
        if len(m) < 2:
            continue
        if re.match(r"^[A-Za-z]:\\", m):
            continue
        cleaned.append(m)

    return sorted(set(cleaned))


def load_provider_catalog(cache_dir: Path) -> Dict[str, List[str]]:
    models_path = cache_dir / "models.json"
    if not models_path.exists() or not models_path.is_file():
        return {}

    try:
        payload = json.loads(models_path.read_text(encoding="utf-8"))
    except Exception:
        return {}

    if not isinstance(payload, dict):
        return {}

    catalog: Dict[str, List[str]] = {}
    for provider, info in payload.items():
        if not isinstance(provider, str) or not provider or not isinstance(info, dict):
            continue

        models = info.get("models", {})
        if not isinstance(models, dict):
            continue

        model_ids = sorted(
            key for key in models.keys() if isinstance(key, str) and key
        )
        if model_ids:
            catalog[provider] = model_ids

    return catalog


def resolve_effective_provider(
    current_provider: str,
    provider_arg: str,
    allowed_providers: List[str],
    has_allowlist: bool,
    detected_candidates: List[str],
    provider_catalog: Dict[str, List[str]],
    current_provider_has_usable_models: bool = False,
) -> Tuple[str, List[str]]:
    warnings: List[str] = []
    effective_allowed = list(dict.fromkeys(allowed_providers if has_allowlist else detected_candidates))

    if provider_arg:
        if has_allowlist and provider_arg not in effective_allowed:
            raise ValueError(f"provider '{provider_arg}' is not allowed")
        return provider_arg, warnings

    if has_allowlist:
        if not effective_allowed:
            raise ValueError("provider allowlist is empty; no providers are allowed")

        ordered_candidates: List[str] = []
        seen = set()

        if current_provider and current_provider in effective_allowed:
            ordered_candidates.append(current_provider)
            seen.add(current_provider)

        for provider in detected_candidates:
            if provider in effective_allowed and provider not in seen:
                ordered_candidates.append(provider)
                seen.add(provider)

        for provider in effective_allowed:
            if provider not in seen:
                ordered_candidates.append(provider)
                seen.add(provider)

        if current_provider and current_provider in effective_allowed:
            if current_provider_has_usable_models:
                return current_provider, warnings

            for candidate in ordered_candidates:
                if candidate != current_provider and provider_catalog.get(candidate):
                    warnings.append(
                        f"current provider '{current_provider}' has no usable models; fell back to '{candidate}'"
                    )
                    return candidate, warnings

            return current_provider, warnings

        for candidate in ordered_candidates:
            if provider_catalog.get(candidate):
                if current_provider:
                    warnings.append(
                        f"current provider '{current_provider}' is not allowed; fell back to '{candidate}'"
                    )
                return candidate, warnings

        candidate = ordered_candidates[0] if ordered_candidates else ""
        if candidate:
            if current_provider:
                warnings.append(
                    f"current provider '{current_provider}' is not allowed; fell back to '{candidate}'"
                )
            return candidate, warnings
        raise ValueError("no allowed provider candidates detected")

    if effective_allowed:
        return effective_allowed[0], warnings

    return current_provider or "openai", warnings


def ensure_provider_has_usable_models(
    has_allowlist: bool,
    available_models: List[str],
) -> None:
    if has_allowlist and not available_models:
        raise ValueError("no allowed provider has usable model data")


def build_model_map(
    provider: str,
    available_models: List[str],
    leader_model: str,
) -> Dict[str, str]:
    overrides = _env_tier_overrides()
    preferred = PREFERRED_MODELS.get(provider, PREFERRED_MODELS["openai"])

    def pick(tier: str, fallback: str) -> str:
        if overrides.get(tier):
            return overrides[tier]
        for candidate in preferred.get(tier, []):
            if candidate in available_models:
                return candidate
        return fallback

    top_fallback = leader_model or preferred["tier_top"][0]
    model_map = {
        "tier_top": pick("tier_top", top_fallback),
        "tier_mid": pick("tier_mid", preferred["tier_mid"][0]),
        "tier_fast": pick("tier_fast", preferred["tier_fast"][0]),
    }

    # Always force top tier to leader model when specified.
    if leader_model:
        model_map["tier_top"] = leader_model

    return model_map


def build_tier_candidates(provider: str, available_models: List[str]) -> Dict[str, List[str]]:
    preferred = PREFERRED_MODELS.get(provider, PREFERRED_MODELS["openai"])

    def classify(model: str) -> str:
        m = model.lower()
        if any(h in m for h in FAST_HINTS):
            return "tier_fast"
        if any(h in m for h in TOP_HINTS):
            return "tier_top"
        return "tier_mid"

    tiers = {"tier_fast": [], "tier_mid": [], "tier_top": []}

    # First, place by classifier.
    for model in available_models:
        tiers[classify(model)].append(model)

    # Then, boost provider preferred models to the front.
    for tier in ["tier_fast", "tier_mid", "tier_top"]:
        preferred_hits = [m for m in preferred.get(tier, []) if m in available_models]
        rest = [m for m in tiers[tier] if m not in preferred_hits]
        tiers[tier] = preferred_hits + sorted(rest)

    return tiers


def _tier_model(tier: str, model_map: Dict[str, str]) -> str:
    return model_map.get(tier, model_map["tier_mid"])


def build_dispatch(
    triage: Dict[str, Any],
    context: Dict[str, Any],
    model_map: Dict[str, str],
    provider: str,
    available_models: List[str],
    tier_candidates: Dict[str, List[str]],
    warnings: List[str],
    model_selection_mode: str,
    available_models_source: List[str],
) -> Dict[str, Any]:
    chat_only = bool(context.get("chatOnly", False))
    if chat_only:
        return {
            "chatOnly": True,
            "reason": "chat-only: no code/file/command action requested",
            "dispatchOrder": [],
            "assignments": [],
            "provider": provider,
            "availableModelsCount": len(available_models),
            "availableModelsSource": available_models_source,
            "modelSelectionMode": model_selection_mode,
            "tierCandidates": tier_candidates,
            "warnings": warnings,
            "finalApproval": {
                "role": "leader",
                "tier": "tier_top",
                "model": _tier_model("tier_top", model_map),
            },
        }

    lane = triage.get("lane", "strict")
    task_type = triage.get("taskType", "feature")

    analysis_tier = triage.get("analysisTier", "tier_mid")
    executor_tier = triage.get("executorTier", "tier_mid")
    review_tier = triage.get("reviewTier", "tier_mid")

    needs_reviewer = bool(triage.get("needsReviewer", False))

    assignments: List[Dict[str, Any]] = []
    dispatch_order: List[str] = []

    def add_role(role: str, tier: str, reason: str) -> None:
        assignments.append(
            {
                "role": role,
                "tier": tier,
                "model": _tier_model(tier, model_map),
                "reason": reason,
            }
        )
        dispatch_order.append(role)

    if lane == "quick":
        if task_type == "investigation":
            add_role("analyzer", analysis_tier, "quick investigation minimal path")
        elif task_type == "review":
            add_role("reviewer", review_tier, "quick review minimal path")
        else:
            add_role("implementer", executor_tier, "quick implementation minimal path")

        if needs_reviewer and "reviewer" not in dispatch_order:
            add_role("reviewer", review_tier, "review explicitly requested or risk uncertain")
    else:
        add_role("analyzer", analysis_tier, "non-quick analysis stage")
        add_role("implementer", executor_tier, "non-quick implementation stage")
        add_role("reviewer", review_tier, "non-quick review gate")

    return {
        "chatOnly": False,
        "provider": provider,
        "availableModelsCount": len(available_models),
        "availableModelsSource": available_models_source,
        "modelSelectionMode": model_selection_mode,
        "tierCandidates": tier_candidates,
        "warnings": warnings,
        "lane": lane,
        "taskType": task_type,
        "dispatchOrder": dispatch_order,
        "assignments": assignments,
        "finalApproval": {
            "role": "leader",
            "tier": "tier_top",
            "model": _tier_model("tier_top", model_map),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Route subagent dispatch and model choice from triage JSON, with provider-aware model discovery and tiering"
    )
    parser.add_argument(
        "--provider",
        default="",
        help="Provider name (openai/openrouter/anthropic/ollama). If omitted, auto-detect from config/env",
    )
    default_leader_model = (
        os.getenv("OPENCODE_LEADER_MODEL", "")
        or os.getenv("OPENCODE_ORCHESTRATOR_MODEL", "")
        or "gpt-5.4"
    )
    parser.add_argument(
        "--leader-model",
        default=default_leader_model,
        help="Top-tier model used by leader (default: gpt-5.4)",
    )
    parser.add_argument(
        "--lead-model",
        dest="leader_model",
        help="Deprecated alias of --leader-model",
    )
    parser.add_argument(
        "--triage-json",
        required=True,
        help="Triage JSON object string",
    )
    parser.add_argument(
        "--context-json",
        default="{}",
        help='Optional context JSON, e.g. {"chatOnly": true}',
    )
    parser.add_argument(
        "--available-models-json",
        default="",
        help='Optional JSON array of model IDs, e.g. ["gpt-5.4","gpt-5.4-mini"]',
    )
    parser.add_argument(
        "--discover-openai-models",
        action="store_true",
        help="Discover available models from OpenAI API using OPENAI_API_KEY",
    )
    parser.add_argument(
        "--discover-models",
        action="store_true",
        help="Discover available models for detected provider",
    )
    parser.add_argument(
        "--auto-detect-config",
        action="store_true",
        help="Read local opencode config to infer provider and configured models",
    )
    parser.add_argument(
        "--config-path",
        default="",
        help="Optional opencode config path. Defaults to ~/.config/opencode/opencode.json",
    )
    parser.add_argument(
        "--fail-on-empty-models",
        action="store_true",
        help="Fail when no available models can be detected/provided",
    )

    args = parser.parse_args()

    try:
        triage = _parse_json(args.triage_json, "triage-json")
        context = _parse_json(args.context_json, "context-json")

        warnings: List[str] = []
        config_obj: Dict[str, Any] = {}
        model_sources: List[str] = []
        config_dir = (
            Path(args.config_path).expanduser().parent
            if args.config_path
            else Path.home() / ".config" / "opencode"
        )
        data_dir = Path.home() / ".local" / "share" / "opencode"
        cache_dir = Path.home() / ".cache" / "opencode"
        settings_obj = load_settings(default_settings_path_for_config(args.config_path))
        has_allowlist = has_explicit_allowed_providers(settings_obj)
        allowed_providers = read_allowed_providers(settings_obj)
        detected_candidates = detect_provider_candidates(config_dir, data_dir, cache_dir)
        provider_catalog = load_provider_catalog(cache_dir)

        if args.auto_detect_config:
            config_obj = load_local_opencode_config(args.config_path)
            if not config_obj:
                warnings.append(
                    f"no opencode config found at {args.config_path or '~/.config/opencode/opencode.json'}"
                )

        current_provider = detect_provider(config_obj, args.provider)
        config_provider = detect_config_provider(config_obj)
        config_models: List[str] = []
        if config_provider:
            config_models = detect_models_from_config(config_obj)
        current_provider_has_usable_models = bool(
            current_provider
            and (
                provider_catalog.get(current_provider)
                or (config_provider and config_provider == current_provider and config_models)
            )
        )
        provider, allowlist_warnings = resolve_effective_provider(
            current_provider=current_provider,
            provider_arg=args.provider,
            allowed_providers=allowed_providers,
            has_allowlist=has_allowlist,
            detected_candidates=detected_candidates,
            provider_catalog=provider_catalog,
            current_provider_has_usable_models=current_provider_has_usable_models,
        )
        warnings.extend(allowlist_warnings)

        available_models: List[str] = list(provider_catalog.get(provider, []))
        if available_models:
            model_sources.append("cache")

        if config_provider and config_provider == provider:
            if config_models:
                model_sources.append("config")
            available_models = list(dict.fromkeys(available_models + config_models))

        if args.available_models_json:
            explicit_models = _parse_json_list(args.available_models_json, "available-models-json")
            available_models = list(dict.fromkeys(explicit_models + available_models))
            if explicit_models:
                model_sources.append("cli")

        if args.discover_openai_models:
            if provider != "openai":
                raise ValueError("--discover-openai-models only supports provider=openai")
            api_key = os.getenv("OPENAI_API_KEY", "")
            if not api_key:
                raise ValueError("OPENAI_API_KEY is required for --discover-openai-models")
            discovered = discover_openai_models(api_key)
            available_models = list(dict.fromkeys(available_models + discovered))
            if discovered:
                model_sources.append("openai-discovery")

        if args.discover_models:
            discovered, discover_warnings = discover_provider_models(provider)
            warnings.extend(discover_warnings)
            available_models = list(dict.fromkeys(available_models + discovered))
            if discovered:
                model_sources.append(f"{provider}-discovery")

        ensure_provider_has_usable_models(has_allowlist, available_models)

        if not available_models:
            warnings.append("no available models detected; routing uses fallback defaults")
            if args.fail_on_empty_models:
                raise ValueError("no available models detected and --fail-on-empty-models is set")

        model_selection_mode = "available-models" if available_models else "fallback-defaults"

        tier_candidates = build_tier_candidates(provider, available_models)

        model_map = build_model_map(
            provider=provider,
            available_models=available_models,
            leader_model=args.leader_model,
        )

        result = build_dispatch(
            triage=triage,
            context=context,
            model_map=model_map,
            provider=provider,
            available_models=available_models,
            tier_candidates=tier_candidates,
            warnings=warnings,
            model_selection_mode=model_selection_mode,
            available_models_source=sorted(set(model_sources)),
        )
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
