from __future__ import annotations

from typing import Any


RECOVERY_PATH_TYPES = [
    "provide_manual_dependency_lock",
    "refine_seed_issue_snapshot",
    "replace_seed",
    "run_source_commit_window",
    "run_command_variant_matrix",
    "run_dependency_lock_materialization",
    "run_target_intent_retry",
    "run_issue_derived_harness_correction",
    "run_repair_only_fallback",
    "run_matched_null_diagnostic",
    "retire_candidate",
]


def recovery_path_ranking_policy() -> dict[str, Any]:
    return {
        "status": "PASS",
        "allowed_recovery_path_types": RECOVERY_PATH_TYPES,
        "repair_paths_require_empirical_gate_pass": True,
        "ranking_inputs": [
            "blocker_severity",
            "evidence_completeness",
            "expected_information_gain",
            "expected_compute_cost",
            "expected_provenance_risk",
            "likelihood_of_target_intent_recovery",
            "likelihood_of_issue_derived_verification",
            "claim_boundary_restrictions",
            "manual_input_required",
        ],
    }


def rank_recovery_paths(*, dependency_lock_status: str, target_intent_alignment: bool) -> dict[str, Any]:
    if dependency_lock_status != "PASS":
        paths = [
            {"rank": 1, "path_type": "provide_manual_dependency_lock", "score": 10, "repair_related": False, "blocked": False},
            {"rank": 2, "path_type": "replace_seed", "score": 5, "repair_related": False, "blocked": False},
            {"rank": 3, "path_type": "run_target_intent_retry", "score": 0, "repair_related": True, "blocked": True, "blocker": "manual_dependency_lock_absent"},
            {"rank": 4, "path_type": "run_repair_only_fallback", "score": 0, "repair_related": True, "blocked": True, "blocker": "manual_dependency_lock_absent"},
        ]
    elif not target_intent_alignment:
        paths = [
            {"rank": 1, "path_type": "run_target_intent_retry", "score": 8, "repair_related": False, "blocked": False},
            {"rank": 2, "path_type": "run_command_variant_matrix", "score": 6, "repair_related": False, "blocked": False},
            {"rank": 3, "path_type": "run_repair_only_fallback", "score": 0, "repair_related": True, "blocked": True, "blocker": "target_intent_alignment_not_reached"},
        ]
    else:
        paths = [{"rank": 1, "path_type": "run_issue_derived_harness_correction", "score": 7, "repair_related": False, "blocked": False}]
    return {"status": "PASS", "paths": paths, "top_recovery_path": paths[0]["path_type"]}


def recovery_candidate_path_policy() -> dict[str, Any]:
    return {"status": "PASS", "paths_are_recommendations": True, "paths_validate_repair": False}
