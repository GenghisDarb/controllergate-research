from __future__ import annotations

from typing import Any


FAILURE_TAXONOMY_CATEGORIES = [
    "reference_core_regression",
    "dependency_lock_absent",
    "dependency_lock_invalid",
    "dependency_materialization_failed",
    "dependency_overlap_unresolved",
    "target_intent_not_reached",
    "target_intent_precondition_failure",
    "source_topology_not_legible",
    "bounded_materialization_failed",
    "activation_order_blocked",
    "repair_preflight_blocked",
    "topology_aware_patch_failed",
    "duplicate_replay_failed",
    "post_patch_constraint_failed",
    "no_overreach_failed",
    "rollback_ledger_blocked",
    "proof_lock_failed",
    "issue_derived_evidence_class_blocked",
    "coupled_interlock_invariant_missing",
    "semantic_drift_public_language_violation",
    "unknown_boundary",
]


BLOCKER_TO_CATEGORY = {
    "manual_dependency_lock_absent": "dependency_lock_absent",
    "manual_dependency_lock_schema_invalid": "dependency_lock_invalid",
    "manual_dependency_lock_placeholder_detected": "dependency_lock_invalid",
    "manual_dependency_lock_missing_evidence_basis": "dependency_lock_invalid",
    "manual_dependency_lock_uses_future_evidence": "dependency_lock_invalid",
    "manual_lock_environment_materialization_failed": "dependency_materialization_failed",
    "dependency_materialization_failed": "dependency_materialization_failed",
    "workspace_purity_failed": "bounded_materialization_failed",
    "target_intent_alignment_not_reached": "target_intent_not_reached",
    "target_intent_precondition_failure": "target_intent_precondition_failure",
    "activation_order_violation": "activation_order_blocked",
    "rollback_ghost_state_detected": "rollback_ledger_blocked",
    "dependency_overlap_double_count_detected": "dependency_overlap_unresolved",
    "issue_derived_harness_v5_verification_failed": "issue_derived_evidence_class_blocked",
    "coupled_interlock_used_without_invariants": "coupled_interlock_invariant_missing",
}


def classify_failure(blocker: str | None) -> dict[str, Any]:
    category = BLOCKER_TO_CATEGORY.get(blocker or "", "unknown_boundary")
    return {
        "status": "PASS" if category != "unknown_boundary" else "BLOCK",
        "blocker": blocker,
        "taxonomy_class": category,
        "generic_failure_used": False,
        "feeds_recovery_path_ranking": True,
    }


def failure_taxonomy_policy() -> dict[str, Any]:
    return {
        "status": "PASS",
        "required_categories": FAILURE_TAXONOMY_CATEGORIES,
        "generic_blocker_allowed_without_taxonomy": False,
        "feeds_recovery_path_ranking": True,
    }
