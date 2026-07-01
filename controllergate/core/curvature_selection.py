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
