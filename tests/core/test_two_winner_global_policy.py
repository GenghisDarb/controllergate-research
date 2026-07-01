from controllergate.core.curvature_selection import two_winner_decision_record


def test_two_winner_record_blocks_empty_routes():
    result = two_winner_decision_record([])

    assert result["status"] == "BLOCK"
    assert result["blocker"] == "curvature_selection_missing"
