#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
from typing import Any, Dict, List


SETTINGS_NAMESPACE = "doTheThing"


def _load_json_obj(path: Path) -> Dict[str, Any]:
    if not path.exists() or not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _load_settings_obj(path: Path) -> Dict[str, Any]:
    if not path.exists() or not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise SystemExit("invalid settings.json: expected a JSON object") from exc
    if not isinstance(payload, dict):
        raise SystemExit("invalid settings.json: expected a JSON object")
    return payload


def load_settings(path: Path) -> Dict[str, Any]:
    return _load_settings_obj(path)


def _load_json_list(raw: str) -> List[str]:
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SystemExit(
            "allowed providers must be a JSON array of non-empty strings"
        ) from exc
    if not isinstance(payload, list):
        raise SystemExit("allowed providers must be a JSON array of non-empty strings")
    for item in payload:
        if not isinstance(item, str) or not item:
            raise SystemExit(
                "allowed providers must be a JSON array of non-empty strings"
            )
    return payload


def detect_provider_candidates(
    config_dir: Path, data_dir: Path, cache_dir: Path
) -> List[str]:
    auth_obj = _load_json_obj(data_dir / "auth.json")
    models_obj = _load_json_obj(cache_dir / "models.json")
    config_obj = _load_json_obj(config_dir / "opencode.json")

    candidates: List[str] = []
    seen = set()

    for source in (auth_obj, models_obj):
        for provider in source.keys():
            if isinstance(provider, str) and provider and provider not in seen:
                seen.add(provider)
                candidates.append(provider)

    active_provider = config_obj.get("provider")
    if (
        isinstance(active_provider, str)
        and active_provider
        and active_provider not in seen
    ):
        seen.add(active_provider)
        candidates.append(active_provider)

    candidates.sort()
    if (
        isinstance(active_provider, str)
        and active_provider
        and active_provider in candidates
    ):
        candidates.remove(active_provider)
        candidates.insert(0, active_provider)
    return candidates


def read_allowed_providers(settings_obj: Dict[str, Any]) -> List[str]:
    pack_obj = settings_obj.get(SETTINGS_NAMESPACE)
    if pack_obj is None:
        return []
    if not isinstance(pack_obj, dict):
        raise SystemExit(
            f"invalid settings.json: expected {SETTINGS_NAMESPACE} to be a JSON object"
        )
    if "allowedProviders" not in pack_obj:
        return []
    raw = pack_obj.get("allowedProviders")
    if not isinstance(raw, list):
        raise SystemExit(
            "invalid settings.json: expected allowedProviders to be a JSON array"
        )
    if any(not isinstance(item, str) or not item for item in raw):
        raise SystemExit(
            "invalid settings.json: expected allowedProviders entries to be non-empty strings"
        )
    return list(raw)


def has_explicit_allowed_providers(settings_obj: Dict[str, Any]) -> bool:
    pack_obj = settings_obj.get(SETTINGS_NAMESPACE)
    if pack_obj is None:
        return False
    if not isinstance(pack_obj, dict):
        raise SystemExit(
            f"invalid settings.json: expected {SETTINGS_NAMESPACE} to be a JSON object"
        )
    return "allowedProviders" in pack_obj


def merge_allowed_providers(
    settings_obj: Dict[str, Any], allowed: List[str]
) -> Dict[str, Any]:
    merged = dict(settings_obj)
    pack_obj = merged.get(SETTINGS_NAMESPACE)
    if not isinstance(pack_obj, dict):
        pack_obj = {}
    else:
        pack_obj = dict(pack_obj)
    pack_obj["allowedProviders"] = list(allowed)
    merged[SETTINGS_NAMESPACE] = pack_obj
    return merged


def _read_settings(path: Path) -> Dict[str, Any]:
    # Pack-owned settings must fail clearly when corrupted; provider detection stays permissive.
    return _load_settings_obj(path)


def _validate_settings_shape(settings_obj: Dict[str, Any]) -> None:
    pack_obj = settings_obj.get(SETTINGS_NAMESPACE)
    if pack_obj is None:
        return
    if not isinstance(pack_obj, dict):
        raise SystemExit(
            f"invalid settings.json: expected {SETTINGS_NAMESPACE} to be a JSON object"
        )
    if "allowedProviders" not in pack_obj:
        return
    allowed = pack_obj.get("allowedProviders")
    if not isinstance(allowed, list):
        raise SystemExit(
            "invalid settings.json: expected allowedProviders to be a JSON array"
        )
    if any(not isinstance(item, str) or not item for item in allowed):
        raise SystemExit(
            "invalid settings.json: expected allowedProviders entries to be non-empty strings"
        )


def _write_settings(path: Path, settings_obj: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(settings_obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def _resolve_cli_action(args: argparse.Namespace) -> str:
    actions = [
        "detect" if args.detect_providers else "",
        "print" if args.print_allowed_providers else "",
        "set" if args.set_allowed_providers_json else "",
    ]
    selected = [action for action in actions if action]
    if len(selected) != 1:
        raise SystemExit(
            "choose one action: specify exactly one of --detect-providers, --print-allowed-providers, or --set-allowed-providers-json"
        )
    return selected[0]


def main() -> int:
    parser = argparse.ArgumentParser(description="Pack-scoped provider policy helper")
    parser.add_argument(
        "--config-dir", default=str(Path.home() / ".config" / "opencode")
    )
    parser.add_argument(
        "--data-dir", default=str(Path.home() / ".local" / "share" / "opencode")
    )
    parser.add_argument("--cache-dir", default=str(Path.home() / ".cache" / "opencode"))
    parser.add_argument("--settings-path", default="")
    parser.add_argument("--detect-providers", action="store_true")
    parser.add_argument("--print-allowed-providers", action="store_true")
    parser.add_argument("--set-allowed-providers-json", default="")
    args = parser.parse_args()

    config_dir = Path(args.config_dir)
    data_dir = Path(args.data_dir)
    cache_dir = Path(args.cache_dir)
    settings_path = (
        Path(args.settings_path) if args.settings_path else config_dir / "settings.json"
    )
    action = _resolve_cli_action(args)

    if action == "detect":
        print(json.dumps(detect_provider_candidates(config_dir, data_dir, cache_dir)))
        return 0

    settings_obj = _read_settings(settings_path)
    _validate_settings_shape(settings_obj)

    if action == "print":
        print(json.dumps(read_allowed_providers(settings_obj)))
        return 0

    if action == "set":
        allowed = _load_json_list(args.set_allowed_providers_json)
        _write_settings(settings_path, merge_allowed_providers(settings_obj, allowed))
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
