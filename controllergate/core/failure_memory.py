from __future__ import annotations

from typing import Iterable

STATUS_CODE_TAXONOMY = [
    "OVERFLOW",
    "FLATLINE",
    "PINNED_EDGE",
    "MONOTONE_SLOPE",
    "ENVIRONMENT_FAILURE",
    "COLLECTION_FAILURE",
    "PRECONDITION_UNRESOLVED",
    "TARGET_INTENT_NOT_REACHED",
    "PATCHABLE_SOURCE_EMPTY",
    "NO_PATCH_GENERATED",
    "PATCH_SAFETY_FAILED",
    "TARGET_VALIDATION_FAILED",
    "DUPLICATE_REPLAY_FAILED",
    "NO_OVERREACH_FAILED",
    "TARGET_VALIDATION_PASSED",
    "DUPLICATE_REPLAY_PASSED",
    "REPAIR_SUCCESS",
]


def normalize_status_code(code: str) -> str:
    normalized = code.strip().upper()
    if normalized not in STATUS_CODE_TAXONOMY:
        raise ValueError(f"unknown status code: {code}")
    return normalized


def build_status_code_inventory(records: Iterable[dict[str, object]]) -> dict[str, object]:
    items = []
    for record in records:
        code = normalize_status_code(str(record["status_code"]))
        items.append(
            {
                "status_code": code,
                "candidate_id": record.get("candidate_id"),
                "evidence_path": record.get("evidence_path"),
                "evidence_sha256": record.get("evidence_sha256"),
                "source_path": record.get("source_path"),
                "function_or_class": record.get("function_or_class"),
                "decision_time_safe": record.get("decision_time_safe") is True,
                "uses_patch_bytes_or_rationale": record.get("uses_patch_bytes_or_rationale") is True,
                "reason": record.get("reason"),
            }
        )
    return {"status": "PASS", "taxonomy": STATUS_CODE_TAXONOMY, "records": items}


def relevant_records_for_candidate(inventory: dict[str, object], candidate_id: str) -> list[dict[str, object]]:
    records = inventory.get("records", [])
    return [item for item in records if isinstance(item, dict) and item.get("candidate_id") == candidate_id]
