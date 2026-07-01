from __future__ import annotations

REPAIRED_CANDIDATE_IDS = {
    "py_bugger_issue_65",
    "darker_non_ascii_drop_changes",
    "darker_stdin_filename",
    "darker_skip_glob_failing_test",
}


def is_fresh_candidate(candidate_id: str, repaired_ids: set[str] | None = None) -> bool:
    denied = repaired_ids if repaired_ids is not None else REPAIRED_CANDIDATE_IDS
    return candidate_id not in denied


def route_diversity_status(
    *,
    source_file_count: int,
    function_or_class_count: int,
    distinct_strategy_count: int = 0,
) -> dict[str, object]:
    route_count = max(source_file_count, function_or_class_count, distinct_strategy_count)
    status = "PASS" if route_count >= 2 else "BLOCK"
    return {
        "status": status,
        "route_count": route_count,
        "source_file_count": source_file_count,
        "function_or_class_count": function_or_class_count,
        "distinct_strategy_count": distinct_strategy_count,
        "blocker": None if status == "PASS" else "prospective_memory_no_patchable_alternatives",
    }


def mappable_status_feature_status(features: list[dict[str, object]]) -> dict[str, object]:
    mapped = [
        feature
        for feature in features
        if feature.get("decision_time_safe") is True
        and feature.get("uses_patch_bytes_or_rationale") is not True
        and bool(feature.get("source_path") or feature.get("context_path") or feature.get("function_or_class"))
    ]
    return {
        "status": "PASS" if mapped else "BLOCK",
        "mapped_feature_count": len(mapped),
        "blocker": None if mapped else "prospective_memory_no_mappable_status_features",
    }


def evaluate_prospective_memory_eligibility(candidate: dict[str, object]) -> dict[str, object]:
    candidate_id = str(candidate.get("candidate_id", ""))
    if not is_fresh_candidate(candidate_id):
        return {
            "status": "BLOCK",
            "eligible": False,
            "candidate_id": candidate_id,
            "blocker": "prospective_memory_candidate_not_fresh",
        }
    if candidate.get("native_candidate") is not True:
        return {
            "status": "BLOCK",
            "eligible": False,
            "candidate_id": candidate_id,
            "blocker": "prospective_memory_eligibility_not_met",
        }
    if candidate.get("pre_repair_failure_reproduced") is not True:
        return {
            "status": "BLOCK",
            "eligible": False,
            "candidate_id": candidate_id,
            "blocker": "batch011_no_fresh_candidate_verified",
        }
    diversity = route_diversity_status(
        source_file_count=int(candidate.get("source_file_count", 0)),
        function_or_class_count=int(candidate.get("function_or_class_count", 0)),
        distinct_strategy_count=int(candidate.get("distinct_strategy_count", 0)),
    )
    if diversity["status"] != "PASS":
        return {
            "status": "BLOCK",
            "eligible": False,
            "candidate_id": candidate_id,
            "blocker": diversity["blocker"],
        }
    mappable = mappable_status_feature_status(list(candidate.get("status_features", [])))
    if mappable["status"] != "PASS":
        return {
            "status": "BLOCK",
            "eligible": False,
            "candidate_id": candidate_id,
            "blocker": mappable["blocker"],
        }
    if candidate.get("too_trivial") is True:
        return {
            "status": "BLOCK",
            "eligible": False,
            "candidate_id": candidate_id,
            "blocker": "prospective_memory_candidate_too_trivial",
        }
    if candidate.get("too_unbounded") is True:
        return {
            "status": "BLOCK",
            "eligible": False,
            "candidate_id": candidate_id,
            "blocker": "prospective_memory_candidate_too_unbounded",
        }
    return {
        "status": "PASS",
        "eligible": True,
        "candidate_id": candidate_id,
        "blocker": None,
        "route_diversity": diversity,
        "mappable_status_features": mappable,
    }


def preregistration_order_status(events: list[str]) -> dict[str, object]:
    patch_events = {"patch_generated", "patch_applied", "patch_validated"}
    preregistered = "prospective_experiment_preregistered" in events
    first_patch_index = min((events.index(event) for event in events if event in patch_events), default=None)
    prereg_index = events.index("prospective_experiment_preregistered") if preregistered else None
    violation = first_patch_index is not None and (prereg_index is None or first_patch_index < prereg_index)
    return {
        "status": "PASS" if not violation else "BLOCK",
        "blocker": None if not violation else "prospective_preregistration_violation",
        "preregistered_before_patch": not violation,
    }


def repair_only_fallback_evaluation(*, attempted: bool, repair_succeeded: bool) -> dict[str, object]:
    return {
        "status": "PASS",
        "repair_only_fallback_attempted": attempted,
        "additional_external_repair_acquired": bool(attempted and repair_succeeded),
        "preliminary_prospective_single_candidate_memory_separation_evidence": False,
        "prospective_memory_lift_status": "not_demonstrated",
    }
