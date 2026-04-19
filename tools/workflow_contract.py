#!/usr/bin/env python3
import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List


CONTRACT_PATH = Path(__file__).with_name("workflow_contract.json")


@lru_cache(maxsize=1)
def load_contract() -> Dict[str, Any]:
    payload = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("workflow_contract.json must contain a JSON object")
    return payload


def triage_required_fields() -> List[str]:
    return list(load_contract()["triage"]["required_fields"])


def reviewer_required_fields() -> List[str]:
    return list(load_contract()["reviewer"]["required_fields"])


def planning_artifact_field() -> str:
    return str(load_contract()["planning"]["artifact_field"])


def planning_artifact_kinds() -> List[str]:
    return list(load_contract()["planning"]["artifact_kinds"])


def planning_requires_question_tool() -> bool:
    return bool(load_contract()["planning"]["approval"]["requires_question_tool"])


def planning_allows_free_text() -> bool:
    return bool(load_contract()["planning"]["approval"]["allows_free_text"])


def provider_policy_namespace() -> str:
    return str(load_contract()["provider_policy"]["settings_namespace"])


def provider_policy_allowed_providers_field() -> str:
    return str(load_contract()["provider_policy"]["allowed_providers_field"])
