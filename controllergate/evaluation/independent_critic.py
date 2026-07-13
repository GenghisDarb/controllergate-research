from __future__ import annotations

from typing import Any

from controllergate.core.evidence import hash_record


def recompute_from_raw(raw_records: list[dict[str, Any]]) -> dict[str, Any]:
    coordinates = []
    for record in raw_records:
        provider = record.get("provider_manifest", {})
        duplicate = record.get("duplicate_replay", {})
        count = record.get("count_gate", {})
        failure_reproduced = duplicate.get("status") == "CANDIDATE_FAILURE_REPRODUCED"
        network_boundary_passed = duplicate.get("network_denial_verified") is True
        coordinates.append({
            "candidate_id": record["candidate_id"],
            "provider_verified": provider.get("verification_status") == "PASS",
            "duplicate_failure_admitted": failure_reproduced and network_boundary_passed,
            "repair_counted": count.get("status") == "COUNTED",
            "exact_blocker": record.get("exact_blocker"),
        })
    result: dict[str, Any] = {"evaluator": "independent_critic", "coordinates": coordinates, "hardcoded_all_pass": False}
    result["report_hash"] = hash_record(result)
    return result
