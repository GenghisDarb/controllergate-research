from __future__ import annotations

from copy import deepcopy
from typing import Any

from .evidence import hash_record


NON_SEMANTIC_FIELDS = {"generated_at", "observed_at", "timestamp"}


def semantic_record(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: semantic_record(item) for key, item in sorted(value.items()) if key not in NON_SEMANTIC_FIELDS and key != "state_hash"}
    if isinstance(value, list):
        return [semantic_record(item) for item in value]
    return value


def attach_state_hash(state: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(state)
    result["state_hash"] = hash_record(semantic_record(result))
    return result


def verify_state_hash(state: dict[str, Any]) -> bool:
    return state.get("state_hash") == hash_record(semantic_record(state))
