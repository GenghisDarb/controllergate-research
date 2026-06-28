from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_external_candidate_registry(path: str | Path = "configs/external_candidate_registry.json") -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def validate_external_candidate_registry(registry: dict[str, Any] | None = None) -> dict[str, Any]:
    if registry is None:
        registry = load_external_candidate_registry()
    candidates = registry.get("candidates", [])
    ids = [item.get("candidate_id") for item in candidates if isinstance(item, dict)]
    duplicate = len(ids) != len(set(ids))
    return {
        "registry_validation_status": "PASS" if isinstance(candidates, list) and not duplicate else "FAIL",
        "candidate_count": len(candidates) if isinstance(candidates, list) else 0,
        "valid_reviewed_candidate_count": count_reviewed_native_candidates(registry),
    }


def reject_duplicate_candidate_id(registry: dict[str, Any], candidate_id: str) -> bool:
    return any(item.get("candidate_id") == candidate_id for item in registry.get("candidates", []) if isinstance(item, dict))


def add_candidate_entry(registry: dict[str, Any], entry: dict[str, Any]) -> dict[str, Any]:
    if reject_duplicate_candidate_id(registry, str(entry.get("candidate_id"))):
        raise ValueError("duplicate candidate_id")
    registry.setdefault("candidates", []).append(entry)
    return registry


def count_reviewed_native_candidates(registry: dict[str, Any]) -> int:
    return sum(
        1
        for item in registry.get("candidates", [])
        if isinstance(item, dict)
        and item.get("registry_review_status") == "reviewed"
        and item.get("candidate_class", "native_buggy_tree_test_candidate") != "issue_derived_reproduction_candidate"
    )


def count_reviewed_issue_derived_candidates(registry: dict[str, Any]) -> int:
    return sum(
        1
        for item in registry.get("candidates", [])
        if isinstance(item, dict)
        and item.get("registry_review_status") == "reviewed"
        and item.get("candidate_class") == "issue_derived_reproduction_candidate"
    )
