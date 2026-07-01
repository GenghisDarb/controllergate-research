from controllergate.core.curvature_selection import select_two_winners, two_winner_delta


def test_curvature_selection_records_linear_and_curvature_winners():
    result = select_two_winners(
        [
            {
                "source_path": "src/pkg/direct.py",
                "function_or_class": "direct",
                "failure_proximity_score": 5,
                "traceback_centrality": 4,
                "dependency_spread_penalty": 4,
            },
            {
                "source_path": "src/pkg/balanced.py",
                "function_or_class": "balanced",
                "failure_proximity_score": 4,
                "traceback_centrality": 3,
                "import_graph_centrality": 3,
                "ast_closure_centrality": 3,
                "alternative_route_availability": 2,
            },
        ]
    )
    assert result["status"] == "PASS"
    assert result["winner_linear"]["source_path"] == "src/pkg/direct.py"
    assert result["winner_curvature"]["source_path"] == "src/pkg/balanced.py"
    assert result["candidate_diversity_score"] == 1


def test_arbitrary_source_shuffling_does_not_count_as_memory_delta():
    before = select_two_winners([
        {"source_path": "src/pkg/a.py", "function_or_class": "a", "failure_proximity_score": 1}
    ])
    after = select_two_winners([
        {"source_path": "src/pkg/a.py", "function_or_class": "a", "failure_proximity_score": 1, "metadata_note": "changed"}
    ])
    delta = two_winner_delta(before, after)
    assert delta["routing_delta_detected"] is False
    assert delta["blocker"] == "active_memory_routing_delta_not_established"
