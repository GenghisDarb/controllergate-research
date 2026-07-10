from __future__ import annotations

from typing import Any


def runtime_wrapper_activation_watchdog(
    *,
    issue_derived_repair_count: int,
    threshold: int = 20,
    evidence: dict[str, bool] | None = None,
) -> dict[str, Any]:
    required = [
        "minimum_repository_diversity_met",
        "minimum_ecosystem_language_diversity_met",
        "prospective_matched_null_evidence_pass",
        "sandbox_replay_pass",
        "rollback_target_available",
        "signed_artifact_available",
        "operator_policy_authorizes_live_change",
        "zero_unresolved_custody_failures",
        "zero_decision_time_outcome_leakage",
        "zero_label_gold_patch_leakage",
        "canary_deployment_evidence",
        "post_deployment_health_verification",
        "automatic_rollback_demonstration",
    ]
    observed = dict(evidence or {})
    floor_met = issue_derived_repair_count >= threshold
    missing = ([] if floor_met else ["issue_derived_repair_floor_met"]) + [name for name in required if observed.get(name) is not True]
    evidence_vector_complete = not missing
    return {
        "status": "PASS",
        "activation_state": (
            "activation_threshold_not_met"
            if not floor_met
            else "requires_separately_authorized_live_runtime_lane"
            if evidence_vector_complete
            else "activation_evidence_vector_incomplete"
        ),
        "issue_derived_repair_count": issue_derived_repair_count,
        "activation_threshold_issue_derived_repairs": threshold,
        "issue_derived_repair_floor_met": floor_met,
        "repair_count_is_necessary_but_not_sufficient": True,
        "required_evidence_conditions": required,
        "observed_evidence": observed,
        "missing_evidence_vector": missing,
        "conjunctive_evidence_vector_complete": evidence_vector_complete,
        "runtime_wrapper_activation_allowed": False,
        "hard_warning_for_next_stage": evidence_vector_complete,
        "current_batch_may_activate_runtime_connectors": False,
        "live_device_repair_enabled": False,
        "self_maintaining_software_claim_allowed": False,
        "audit_status": "PASS",
    }
