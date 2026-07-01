from __future__ import annotations


def prospective_memory_lift_requirement() -> dict[str, object]:
    return {
        "status": "PASS",
        "fresh_candidate_required": True,
        "matched_null_rules_pre_registered_before_successful_patch": True,
        "same_candidate_commit_command_environment": True,
        "null_arm_denies_failure_memory_and_successful_patch": True,
        "full_memory_lift_claim_allowed": False,
    }


def evaluate_retrospective_memory_claim(
    *,
    score: float | None,
    routing_delta_detected: bool,
    retrospective: bool,
) -> dict[str, object]:
    diagnostic = bool(retrospective and routing_delta_detected and score is not None and score >= 0.95)
    return {
        "status": "PASS",
        "retrospective_single_candidate_memory_separation_diagnostic": diagnostic,
        "prospective_memory_lift_status": "not_demonstrated",
        "full_memory_lift_claimed": False,
        "reason": "retrospective calibration cannot establish prospective memory lift",
    }
