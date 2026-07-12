from __future__ import annotations

from typing import Any


CONFIDENCE = {"exact_issue_node": 0, "source_verified_symbol_to_test_target": 1, "exact_issue_file": 2, "traceback_derived_target": 2, "bounded_project_native_target": 3}


def rank_candidate(record: dict[str, Any]) -> tuple[int, str]:
    score = 0
    score += CONFIDENCE.get(record.get("target", {}).get("confidence_class"), 20)
    score += 0 if record.get("command", {}).get("status") == "PASS" else 20
    score += 0 if record.get("provider_feasibility") == "hash_lockable_python_provider" else 20
    score += 2 if record.get("contamination", {}).get("classification") == "SOFT_RISK" else 0
    score += min(10, int(record.get("provider_complexity", 0)))
    return score, str(record.get("candidate_id"))


def rank_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(records, key=rank_candidate)
