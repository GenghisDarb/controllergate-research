from __future__ import annotations

from typing import Any


CONFIDENCE_BY_SOURCE_CLASS = {
    "explicit_issue_reproduction_commit_verified": "exact_reproduction_commit",
    "manual_artifact_buggy_commit_verified": "exact_reproduction_commit",
    "benchmark_manifest_commit_verified": "exact_reproduction_commit",
    "release_tag_explicitly_referenced_by_issue_verified": "strong_versioned_release_commit",
    "latest_release_tag_before_issue_created_verified": "strong_versioned_release_commit",
    "latest_default_branch_commit_before_issue_created_verified": "decision_time_epoch_snapshot_commit",
    "prior_approved_registry_commit_verified": "exact_reproduction_commit",
    "sha_unresolved_request_only": "unresolved_sha_required",
}

TIER2_ALLOWED_CONFIDENCE = {
    "exact_reproduction_commit",
    "strong_versioned_release_commit",
    "decision_time_epoch_snapshot_commit",
}


def sha_resolution_confidence_schema() -> dict[str, Any]:
    return {
        "status": "PASS",
        "confidence_levels": [
            "exact_reproduction_commit",
            "strong_versioned_release_commit",
            "decision_time_epoch_snapshot_commit",
            "weak_sha_hint_requires_manual_review",
            "unresolved_sha_required",
            "rejected_forbidden_source",
        ],
        "tier2_allowed_confidence_levels": sorted(TIER2_ALLOWED_CONFIDENCE),
        "patch_authority_from_sha_resolution_allowed": False,
        "test_execution_from_sha_resolution_allowed": False,
        "audit_status": "PASS",
    }


def classify_sha_resolution(sha_source_class: str, *, commit_resolves: bool) -> dict[str, Any]:
    confidence = CONFIDENCE_BY_SOURCE_CLASS.get(sha_source_class, "weak_sha_hint_requires_manual_review")
    tier2_allowed = commit_resolves and confidence in TIER2_ALLOWED_CONFIDENCE
    return {
        "status": "PASS",
        "sha_source_class": sha_source_class,
        "confidence": confidence,
        "tier2_allowed": tier2_allowed,
        "tier": 2 if tier2_allowed else 1,
        "tier_label": "Tier 2b decision-time epoch snapshot" if confidence == "decision_time_epoch_snapshot_commit" else "Tier 2a explicit or release commit" if tier2_allowed else "Tier 1 SHA unresolved",
        "allowed_use": "metadata_scan_and_command_orthology_dry_run_only" if tier2_allowed else "source_identity_tracking_only",
        "forbidden_use": ["patch_generation", "test_execution", "count_gate", "memory_lift_claim", "full_scoring"],
        "audit_status": "PASS",
    }
