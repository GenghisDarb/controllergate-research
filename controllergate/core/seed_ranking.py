from __future__ import annotations

from typing import Any

ACTIVE_PROMOTION_STATUSES = {
    "approved_for_pre_repair_replay_attempt",
    "approved_for_provider_capsule_probe",
    "approved_for_command_boundary_probe",
}


def candidate_seed_risk_score_schema() -> dict[str, Any]:
    return {
        "status": "PASS",
        "score_direction": "lower_is_better",
        "routing_only": True,
        "score_is_not_repair_proof": True,
        "factors": [
            "issue_derived_confidence",
            "candidate_sha_availability",
            "harness_origin_clarity",
            "command_boundary_clarity",
            "provider_capsule_feasibility",
            "workspace_purity_feasibility",
            "runner_target_simplicity",
            "version_origin_risk",
            "source_topology_clarity",
            "expected_pre_repair_replay_cost",
            "gold_fixed_future_leakage_risk",
            "issue_comment_fix_leakage_risk",
            "test_mutation_temptation_risk",
            "provider_backend_unavailable_risk",
            "cross_family_homology_usefulness",
            "non_ansible_memory_opportunity",
            "future_pre_repair_materialization_probability",
            "future_source_only_patch_gate_probability",
        ],
    }


def score_seed(record: dict[str, Any]) -> dict[str, Any]:
    score = 50
    reasons: list[str] = []
    status = str(record.get("promotion_status", ""))
    if status in ACTIVE_PROMOTION_STATUSES:
        score -= 25
        reasons.append("active_future_probe_status")
    if record.get("issue_derived_status") == "issue_derived_lead":
        score -= 8
        reasons.append("issue_derived_lead")
    if record.get("candidate_sha_status") == "sha40_recorded":
        score -= 8
        reasons.append("sha40_recorded")
    if "low" in str(record.get("version_origin_risk", "")):
        score -= 4
        reasons.append("low_version_origin_risk")
    if record.get("already_counted_status") == "already_counted_repair":
        score += 100
        reasons.append("already_counted_excluded")
    if record.get("parked_candidate_status") != "not_parked":
        score += 90
        reasons.append("parked_candidate_excluded")
    if record.get("probe_only_status") != "not_probe_only":
        score += 50
        reasons.append("probe_only_excluded")
    if status == "approved_for_command_boundary_probe":
        score -= 4
        reasons.append("command_boundary_probe_ready")
    if status == "approved_for_provider_capsule_probe":
        score -= 2
        reasons.append("provider_capsule_probe_ready")
    return {
        "candidate_id": record.get("candidate_id"),
        "risk_score": score,
        "score_reasons": reasons,
        "promotion_status": status,
        "score_is_routing_only": True,
    }


def rank_seeds(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    scored = [(score_seed(record), record) for record in records]
    scored.sort(key=lambda item: (item[0]["risk_score"], str(item[1].get("candidate_id"))))
    ranking: list[dict[str, Any]] = []
    for rank, (score, record) in enumerate(scored, start=1):
        not_top_reason = None if rank == 1 else "ranked_lower_by_wrapper_readiness_score"
        ranking.append(
            {
                "rank": rank,
                "candidate_id": record.get("candidate_id"),
                "repo_url": record.get("repo_url"),
                "risk_score": score["risk_score"],
                "score_reasons": score["score_reasons"],
                "reason_for_rank": "wrapper_readiness_lowest_risk" if rank == 1 else "wrapper_readiness_order",
                "promotion_status": record.get("promotion_status"),
                "next_batch_recommended": record.get("allowed_next_action"),
                "exact_blocker_if_not_top": not_top_reason or record.get("promotion_blocker"),
                "why_not_patch_now": "Batch068 is seed intake and routing only; patch generation is forbidden.",
                "claim_boundary": {
                    "patch_generated": False,
                    "patch_applied": False,
                    "duplicate_replay_run": False,
                    "count_gate_run": False,
                    "repair_count_increment": False,
                },
            }
        )
    return ranking
