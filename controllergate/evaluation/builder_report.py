from __future__ import annotations

from typing import Any

from controllergate.core.evidence import hash_record


def build_report(candidate_records: list[dict[str, Any]]) -> dict[str, Any]:
    coordinates = []
    for record in candidate_records:
        coordinates.append({
            "candidate_id": record["candidate_id"],
            "provider_verified": record.get("provider_verified") is True,
            "duplicate_failure_admitted": record.get("duplicate_failure_admitted") is True,
            "repair_counted": record.get("repair_counted") is True,
            "exact_blocker": record.get("exact_blocker"),
        })
    result: dict[str, Any] = {"evaluator": "builder", "coordinates": coordinates, "hardcoded_all_pass": False}
    result["report_hash"] = hash_record(result)
    return result

