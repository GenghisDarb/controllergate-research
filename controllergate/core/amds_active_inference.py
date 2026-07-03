from __future__ import annotations

from typing import Any

from .information_gain_probe import build_probe_candidate_registry, probe_selection_status


def amds_active_inference_policy() -> dict[str, Any]:
    return {
        "status": "PASS",
        "maintains_probe_queue": True,
        "allowed_outputs": [
            "candidate_probe_queue",
            "seed_quality_score",
            "dependency_lock_need_score",
            "target_intent_risk_score",
            "route_diversity_score",
            "expected_information_gain_score",
            "next_probe_recommendation",
            "replacement_seed_recommendation_if_needed",
        ],
        "forbidden_outputs": [
            "repair_success_claim",
            "memory_lift_claim",
            "native_repair_count_increment",
            "issue_derived_repair_feasibility_claim",
            "production_readiness_claim",
        ],
    }


def amds_probe_queue(feature_vector: dict[str, Any]) -> dict[str, Any]:
    registry = build_probe_candidate_registry(feature_vector)
    selection = probe_selection_status(feature_vector)
    blocked = feature_vector.get("dependency_lock_status") != "PASS"
    return {
        "status": "PASS",
        "candidate_status": "blocked_on_manual_dependency_lock" if blocked else "ready_for_next_probe",
        "candidate_probe_queue": registry,
        "seed_quality_score": 4,
        "dependency_lock_need_score": 10 if blocked else 0,
        "target_intent_risk_score": 8 if blocked else 4,
        "route_diversity_score": feature_vector.get("curvature_route_diversity_score", 0),
        "expected_information_gain_score": feature_vector.get("expected_information_gain", 0),
        "next_probe_recommendation": selection.get("selected_probe_type"),
        "replacement_seed_recommendation_if_needed": "replace_seed" if blocked else None,
        "repair_success_claim": False,
        "memory_lift_claim": False,
        "native_repair_count_increment": False,
        "issue_derived_repair_feasibility_claim": False,
        "production_readiness_claim": False,
    }
