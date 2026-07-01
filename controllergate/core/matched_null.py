from __future__ import annotations


def define_memory_enabled_arm(candidate_id: str) -> dict[str, object]:
    return {"arm": "memory_enabled_controllergate", "candidate_id": candidate_id}


def define_memory_disabled_arm(candidate_id: str) -> dict[str, object]:
    return {"arm": "memory_disabled_matched_null", "candidate_id": candidate_id}


def enforce_same_candidate_environment(left: dict[str, object], right: dict[str, object]) -> bool:
    keys = ["candidate_id", "repo_url", "commit_sha", "target_command", "environment_hash"]
    return all(left.get(key) == right.get(key) for key in keys)


def enforce_null_arm_memory_exclusion(arm: dict[str, object]) -> bool:
    return arm.get("uses_failure_memory") is not True and arm.get("reads_successful_patch") is not True


def matched_null_separation_score(a: dict[str, float], b: dict[str, float]) -> float:
    return max(0.0, min(1.0, a.get("score", 0.0) - b.get("score", 0.0)))


def memory_lift_claim_evaluation(score: float, threshold: float = 0.95) -> dict[str, object]:
    return {"preliminary_memory_lift_evidence": score >= threshold, "full_memory_lift_claimed": False}


def retrospective_matched_null_calibration_score(
    *,
    quarantine_passed: bool,
    arms_comparable: bool,
    arm_a_succeeded: bool,
    null_success_rate: float,
    routing_delta_detected: bool,
) -> dict[str, object]:
    if not quarantine_passed:
        return {"status": "BLOCK", "score_computed": False, "blocker": "matched_null_patch_quarantine_failed"}
    if not arms_comparable:
        return {"status": "BLOCK", "score_computed": False, "blocker": "matched_null_arms_not_comparable"}
    if not arm_a_succeeded:
        score = 0.0
    elif null_success_rate >= 1.0:
        score = 0.0
    elif not routing_delta_detected:
        score = 0.0
    else:
        score = max(0.0, min(1.0, 1.0 - null_success_rate))
    return {
        "status": "PASS",
        "score_computed": True,
        "matched_null_ensemble_separation_score": score,
        "retrospective_single_candidate_memory_separation_diagnostic": score >= 0.95,
        "prospective_memory_lift": "not_claimed",
    }


def null_ensemble_success_rate(results: list[dict[str, object]]) -> float:
    if not results:
        return 0.0
    successes = [
        result for result in results
        if result.get("target_validation_status") == "PASS" and result.get("duplicate_replay_status") == "PASS"
    ]
    return len(successes) / len(results)
