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
