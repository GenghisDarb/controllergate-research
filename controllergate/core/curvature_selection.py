from __future__ import annotations


def route_direct_score(route: dict[str, object]) -> float:
    return float(route.get("failure_proximity_score", 0.0)) + float(route.get("traceback_centrality", 0.0))


def route_curvature_score(route: dict[str, object]) -> float:
    positive = (
        float(route.get("failure_proximity_score", 0.0))
        + float(route.get("traceback_centrality", 0.0))
        + float(route.get("import_graph_centrality", 0.0))
        + float(route.get("ast_closure_centrality", 0.0))
        + float(route.get("alternative_route_availability", 0.0))
        + float(route.get("target_intent_reachability_score", 0.0))
        + float(route.get("status_code_weight", 0.0))
    )
    penalty = float(route.get("dependency_spread_penalty", 0.0)) + float(route.get("environment_precondition_friction_penalty", 0.0))
    return positive - penalty


def select_two_winners(routes: list[dict[str, object]]) -> dict[str, object]:
    if not routes:
        return {
            "status": "BLOCK",
            "blocker": "curvature_selection_missing",
            "winner_linear": None,
            "winner_curvature": None,
            "candidate_diversity_score": 0,
        }
    enriched = [
        {
            **route,
            "direct_score": route_direct_score(route),
            "curvature_score": route_curvature_score(route),
        }
        for route in routes
    ]
    linear = max(enriched, key=lambda item: (float(item["direct_score"]), str(item.get("source_path")), str(item.get("function_or_class"))))
    curvature = max(enriched, key=lambda item: (float(item["curvature_score"]), str(item.get("source_path")), str(item.get("function_or_class"))))
    diversity = 1 if (linear.get("source_path"), linear.get("function_or_class")) != (curvature.get("source_path"), curvature.get("function_or_class")) else 0
    return {
        "status": "PASS",
        "blocker": None,
        "winner_linear": linear,
        "winner_curvature": curvature,
        "candidate_diversity_score": diversity,
        "routing_diversity_low": diversity == 0,
    }


def two_winner_delta(before: dict[str, object], after: dict[str, object]) -> dict[str, object]:
    reason_codes: list[str] = []
    for key, reason in [
        ("winner_linear", "winner_linear_changed"),
        ("winner_curvature", "winner_curvature_changed"),
    ]:
        left = before.get(key) or {}
        right = after.get(key) or {}
        if isinstance(left, dict) and isinstance(right, dict):
            if (left.get("source_path"), left.get("function_or_class")) != (right.get("source_path"), right.get("function_or_class")):
                reason_codes.append(reason)
    return {
        "status": "PASS",
        "routing_delta_detected": bool(reason_codes),
        "routing_delta_reason_codes": reason_codes,
        "blocker": None if reason_codes else "active_memory_routing_delta_not_established",
    }


def global_curvature_logic_policy() -> dict[str, object]:
    return {
        "status": "PASS",
        "required_for": [
            "candidate difficulty/admission decisions",
            "prospective memory eligibility",
            "route diversity evaluation",
            "patchable source subset ranking",
            "two-winner source selection",
            "memory-weighted route selection",
            "bounded fragment patch planning",
            "null ensemble perturbation validity",
            "no-overreach risk evaluation",
            "memory-separation claim eligibility",
            "technical validation readiness claims",
        ],
        "optional_for": [
            "artifact ingest",
            "byte-custody verification",
            "registry validation",
            "command manifest validation",
            "workspace purity checks",
            "environment lock checks",
        ],
        "forbidden_as_replacement_for": [
            "exact commit verification",
            "source/test provenance",
            "pre-repair replay",
            "target validation",
            "duplicate replay",
            "no-overreach validation",
            "SHA256 custody",
        ],
        "claim_boundary": "curvature can route choices but cannot replace evidence",
    }


def curvature_feature_vector_schema() -> dict[str, object]:
    fields = [
        "candidate_id",
        "candidate_class",
        "repo_url",
        "source_commit_sha",
        "native_or_issue_derived",
        "target_command_width",
        "source_file_count_in_trace",
        "source_function_count_in_trace",
        "import_graph_source_file_count",
        "ast_closure_source_file_count",
        "patchable_source_file_count",
        "patchable_source_function_count",
        "alternative_route_count",
        "interlock_invariant_count",
        "dependency_spread_score",
        "precondition_friction_score",
        "environment_lock_status",
        "command_manifest_status",
        "workspace_purity_status",
        "baseline_drift_status",
        "target_intent_reachability_status",
        "semantic_failure_signature_status",
        "issue_derived_risk_status",
        "null_expected_difficulty",
        "memory_feature_mappability",
        "flatline_risk",
        "escape_boundary_risk",
        "basin_stability_score",
        "curvature_eligibility_status",
        "blocker_if_ineligible",
    ]
    return {"status": "PASS", "required_fields": fields}


def curvature_feature_vector(candidate: dict[str, object]) -> dict[str, object]:
    alternative_route_count = int(candidate.get("alternative_route_count", 0))
    patchable_source_file_count = int(candidate.get("patchable_source_file_count", 0))
    flatline_risk = str(candidate.get("flatline_risk", "unknown"))
    if patchable_source_file_count == 0:
        eligibility = "BLOCK"
        blocker = "curvature_no_patchable_basin"
    elif alternative_route_count < 2 and candidate.get("candidate_class") == "prospective_memory_candidate":
        eligibility = "BLOCK"
        blocker = "curvature_insufficient_route_diversity_for_memory"
    elif flatline_risk == "high":
        eligibility = "BLOCK"
        blocker = "curvature_flatline_signal_rejected"
    else:
        eligibility = "PASS"
        blocker = None
    defaults = {
        "candidate_id": None,
        "candidate_class": None,
        "repo_url": None,
        "source_commit_sha": None,
        "native_or_issue_derived": "unknown",
        "target_command_width": "unknown",
        "source_file_count_in_trace": 0,
        "source_function_count_in_trace": 0,
        "import_graph_source_file_count": 0,
        "ast_closure_source_file_count": 0,
        "patchable_source_file_count": patchable_source_file_count,
        "patchable_source_function_count": int(candidate.get("patchable_source_function_count", 0)),
        "alternative_route_count": alternative_route_count,
        "interlock_invariant_count": int(candidate.get("interlock_invariant_count", 0)),
        "dependency_spread_score": int(candidate.get("dependency_spread_score", 0)),
        "precondition_friction_score": int(candidate.get("precondition_friction_score", 0)),
        "environment_lock_status": candidate.get("environment_lock_status", "unknown"),
        "command_manifest_status": candidate.get("command_manifest_status", "unknown"),
        "workspace_purity_status": candidate.get("workspace_purity_status", "unknown"),
        "baseline_drift_status": candidate.get("baseline_drift_status", "unknown"),
        "target_intent_reachability_status": candidate.get("target_intent_reachability_status", "unknown"),
        "semantic_failure_signature_status": candidate.get("semantic_failure_signature_status", "unknown"),
        "issue_derived_risk_status": candidate.get("issue_derived_risk_status", "not_issue_derived"),
        "null_expected_difficulty": candidate.get("null_expected_difficulty", "unknown"),
        "memory_feature_mappability": candidate.get("memory_feature_mappability", "unknown"),
        "flatline_risk": flatline_risk,
        "escape_boundary_risk": candidate.get("escape_boundary_risk", "unknown"),
        "basin_stability_score": int(candidate.get("basin_stability_score", 0)),
        "curvature_eligibility_status": eligibility,
        "blocker_if_ineligible": blocker,
    }
    defaults.update({key: candidate[key] for key in defaults if key in candidate})
    defaults["curvature_eligibility_status"] = eligibility
    defaults["blocker_if_ineligible"] = blocker
    return defaults


def basin_stability_check_policy() -> dict[str, object]:
    return {
        "status": "PASS",
        "repair_only_minimum_alternative_route_count": 1,
        "prospective_memory_minimum_alternative_route_count": 2,
        "blockers": [
            "curvature_no_patchable_basin",
            "curvature_insufficient_route_diversity_for_memory",
            "curvature_basin_obscured_by_precondition",
            "curvature_flatline_signal_rejected",
        ],
    }


def basin_stability_score(candidate: dict[str, object], *, experiment_class: str) -> dict[str, object]:
    if candidate.get("target_failure_reproduces") is not True:
        return {"status": "BLOCK", "basin_stability_score": 0, "blocker": "curvature_flatline_signal_rejected"}
    if candidate.get("semantic_failure_signature_exists") is not True:
        return {"status": "BLOCK", "basin_stability_score": 0, "blocker": "curvature_flatline_signal_rejected"}
    if candidate.get("environment_precondition_only") is True:
        return {"status": "BLOCK", "basin_stability_score": 0, "blocker": "curvature_basin_obscured_by_precondition"}
    patchable_count = int(candidate.get("patchable_source_file_count", 0))
    route_count = int(candidate.get("alternative_route_count", 0))
    if patchable_count == 0:
        return {"status": "BLOCK", "basin_stability_score": 0, "blocker": "curvature_no_patchable_basin"}
    if experiment_class == "prospective_memory" and route_count < 2:
        return {"status": "BLOCK", "basin_stability_score": route_count, "blocker": "curvature_insufficient_route_diversity_for_memory"}
    return {"status": "PASS", "basin_stability_score": patchable_count + route_count, "blocker": None}


def two_winner_global_policy() -> dict[str, object]:
    return {
        "status": "PASS",
        "applies_to": [
            "candidate source route selection",
            "patchable source ranking",
            "fragment target selection",
            "memory-weighted source ranking",
            "null ensemble route perturbation validation",
        ],
        "blocker_if_memory_route_not_separable": "curvature_no_separable_memory_route",
    }


def two_winner_decision_record(routes: list[dict[str, object]], *, memory_changed_selection: bool = False) -> dict[str, object]:
    winners = select_two_winners(routes)
    linear = winners.get("winner_linear")
    curved = winners.get("winner_curvature")
    same = linear == curved
    return {
        "status": winners["status"],
        "winner_linear": linear,
        "winner_curvature": curved,
        "selected_route": curved or linear,
        "selection_reason": "curvature_winner_preferred_when_available",
        "route_diversity_status": "PASS" if not same and winners["status"] == "PASS" else "LOW",
        "winner_linear_equals_winner_curvature": same,
        "curvature_changed_selection": not same,
        "memory_changed_selection": memory_changed_selection,
        "valid_for_repair_only": winners["status"] == "PASS",
        "valid_for_prospective_memory": winners["status"] == "PASS" and not same,
        "blocker": None if winners["status"] == "PASS" and not same else ("curvature_no_separable_memory_route" if winners["status"] == "PASS" else winners["blocker"]),
    }


def curvature_memory_routing_policy() -> dict[str, object]:
    return {
        "status": "PASS",
        "requires_mapped_status_feature": True,
        "requires_route_diversity": True,
        "requires_strict_minimum_delta": True,
        "forbidden_patch_memory_used": False,
        "blockers": [
            "curvature_memory_routing_delta_not_established",
            "curvature_memory_feature_unmapped",
            "curvature_memory_used_forbidden_patch_artifact",
        ],
    }


def curvature_memory_routing_audit(
    baseline: dict[str, object],
    memory_weighted: dict[str, object],
    *,
    evidence_hashes: list[str],
    feature_mapped: bool,
    forbidden_patch_memory_used: bool = False,
) -> dict[str, object]:
    if forbidden_patch_memory_used:
        blocker = "curvature_memory_used_forbidden_patch_artifact"
    elif not feature_mapped:
        blocker = "curvature_memory_feature_unmapped"
    else:
        changed = (
            baseline.get("winner_linear") != memory_weighted.get("winner_linear")
            or baseline.get("winner_curvature") != memory_weighted.get("winner_curvature")
            or baseline.get("selected_route") != memory_weighted.get("selected_route")
        )
        blocker = None if changed else "curvature_memory_routing_delta_not_established"
    return {
        "status": "PASS" if blocker is None else "BLOCK",
        "baseline_winner_linear": baseline.get("winner_linear"),
        "baseline_winner_curvature": baseline.get("winner_curvature"),
        "memory_weighted_winner_linear": memory_weighted.get("winner_linear"),
        "memory_weighted_winner_curvature": memory_weighted.get("winner_curvature"),
        "routing_delta_detected": blocker is None,
        "delta_type": "route_or_context_delta" if blocker is None else "none_or_scalar_only",
        "delta_reason_codes": ["curvature_route_changed"] if blocker is None else [],
        "evidence_hashes": evidence_hashes,
        "forbidden_patch_memory_used": forbidden_patch_memory_used,
        "blocker": blocker,
    }


def curvature_fragment_planning_policy() -> dict[str, object]:
    return {
        "status": "PASS",
        "curvature_route_required": True,
        "interlock_invariant_required": True,
        "blockers": [
            "curvature_fragment_route_missing",
            "curvature_fragment_interlock_missing",
            "curvature_fragment_flatline_risk_unresolved",
            "curvature_fragment_source_context_stale",
        ],
    }


def curvature_fragment_plan(route: dict[str, object] | None, *, interlock_count: int, repair_runs: bool) -> dict[str, object]:
    if not repair_runs:
        return {"status": "NOT_RUN", "fragments": [], "blocker": None}
    if not route:
        return {"status": "BLOCK", "fragments": [], "blocker": "curvature_fragment_route_missing"}
    if interlock_count <= 0:
        return {"status": "BLOCK", "fragments": [], "blocker": "curvature_fragment_interlock_missing"}
    return {
        "status": "PASS",
        "fragments": [
            {
                "target_source_file": route.get("source_path"),
                "target_function_or_class": route.get("function_or_class"),
                "winner_source_route": route,
                "curvature_reason_codes": ["curvature_route_selected"],
                "interlock_invariant_references": list(range(interlock_count)),
                "expected_target_projection": "bounded_target_projection",
                "expected_source_projection": "bounded_source_projection",
                "no_overreach_risk_score": 0,
            }
        ],
        "blocker": None,
    }


def null_ensemble_curvature_fairness_policy() -> dict[str, object]:
    return {
        "status": "PASS",
        "same_curvature_feature_vector_required": True,
        "same_two_winner_policy_required": True,
        "failure_memory_weighting_allowed_in_null": False,
        "blocker": "null_curvature_fairness_failed",
    }


def null_ensemble_curvature_fairness_audit(*, ensemble_runs: bool, arm_a_vector_hash: str | None, null_vector_hashes: list[str]) -> dict[str, object]:
    if not ensemble_runs:
        return {"status": "NOT_RUN", "blocker": None, "null_curvature_fairness_passed": False}
    passed = bool(arm_a_vector_hash) and all(value == arm_a_vector_hash for value in null_vector_hashes)
    return {
        "status": "PASS" if passed else "BLOCK",
        "blocker": None if passed else "null_curvature_fairness_failed",
        "null_curvature_fairness_passed": passed,
    }


def curvature_claim_boundary(*, route_diversity_exists: bool, routing_delta_scalar_only: bool, null_curvature_fair: bool, repair_only: bool, issue_derived: bool) -> dict[str, object]:
    violation = (
        not route_diversity_exists
        or routing_delta_scalar_only
        or not null_curvature_fair
        or repair_only
        or issue_derived
    )
    return {
        "status": "BLOCK" if violation else "PASS",
        "memory_separation_claim_allowed": not violation,
        "full_memory_lift_claimed": False,
        "technical_validation_claimed": False,
        "self_maintaining_software": "false/not_demonstrated",
        "blocker": "curvature_claim_boundary_violation" if violation else None,
    }


def curvature_heuristic_freeze() -> dict[str, object]:
    return {
        "status": "PASS",
        "formula_version": "batch013_curvature_score_v1",
        "formula_frozen_before_seed_intake": True,
        "thresholds_frozen_before_seed_intake": True,
        "post_hoc_weight_changes_allowed": False,
        "blocker_if_changed_after_seed": "curvature_heuristic_post_hoc_change_detected",
    }


def curvature_score_formula() -> dict[str, object]:
    return {
        "status": "PASS",
        "formula_version": "batch013_curvature_score_v1",
        "score": "failure_proximity + traceback_centrality + import_graph_centrality + ast_closure_centrality + alternative_route_availability + target_intent_reachability + status_code_weight - dependency_spread_penalty - environment_precondition_friction_penalty",
        "inputs": [
            "failure_proximity_score",
            "traceback_centrality",
            "import_graph_centrality",
            "ast_closure_centrality",
            "alternative_route_availability",
            "target_intent_reachability_score",
            "status_code_weight",
            "dependency_spread_penalty",
            "environment_precondition_friction_penalty",
        ],
    }


def curvature_thresholds() -> dict[str, object]:
    return {
        "status": "PASS",
        "formula_version": "batch013_curvature_score_v1",
        "repair_only_minimum_patchable_source_file_count": 1,
        "prospective_memory_minimum_alternative_route_count": 2,
        "max_allowed_flatline_risk": "medium",
        "high_escape_boundary_risk_blocks_memory_claim": True,
    }
