from __future__ import annotations


def verify_preconditions(rows: list[dict[str, object]]) -> dict[str, object]:
    blockers = [row for row in rows if row.get("failure_classification") == "declared_secondary_cofactor_unpinned_lock_required"]
    drift = [row for row in rows if row.get("lock_status") == "PROVIDER_DRIFT_DETECTED"]
    return {
        "status": "BLOCK" if blockers or drift else "PASS",
        "blockers": blockers,
        "provider_drift": drift,
        "source_code_evidence_inferred_from_provider_drift": False,
    }
