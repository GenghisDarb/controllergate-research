from controllergate.core.curvature_selection import select_two_winners


def test_two_winner_policy_records_low_diversity_when_winners_match():
    result = select_two_winners(
        [
            {
                "source_path": "src/pkg/only.py",
                "function_or_class": "repair",
                "failure_proximity_score": 3,
                "traceback_centrality": 3,
            }
        ]
    )
    assert result["winner_linear"]["source_path"] == "src/pkg/only.py"
    assert result["winner_curvature"]["source_path"] == "src/pkg/only.py"
    assert result["routing_diversity_low"] is True


def test_two_winner_policy_blocks_when_no_routes_exist():
    result = select_two_winners([])
    assert result["status"] == "BLOCK"
    assert result["blocker"] == "curvature_selection_missing"
