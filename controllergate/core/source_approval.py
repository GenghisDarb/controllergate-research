from __future__ import annotations

APPROVED_SOURCE_CLASSES = {"curated_manual", "approved_external_source", "curated_manual_custody"}


def evaluate_source_approval(record: dict[str, object]) -> dict[str, object]:
    source_class = record.get("source_class")
    approved = record.get("approval_status") == "approved" and source_class in APPROVED_SOURCE_CLASSES
    probe_only = record.get("probe_only") is True
    already_counted = record.get("already_counted") is True
    blocker = None
    if probe_only or already_counted or not approved:
        blocker = "manual_artifact_custody_or_external_source_approval_required_for_new_unused_candidate_seed"
    return {
        "status": "PASS" if approved and not probe_only and not already_counted else "BLOCK",
        "approved_for_candidate_inventory": approved and not probe_only and not already_counted,
        "blocker": blocker,
    }


def source_approval_gate_policy() -> dict[str, object]:
    return {
        "status": "PASS",
        "probe_sources_require_promotion": True,
        "manual_artifact_custody_requires_hash_and_manifest_verification": True,
        "already_counted_repairs_excluded_from_active_inventory": True,
        "zero_approved_candidates_is_not_repair_failure": True,
    }
