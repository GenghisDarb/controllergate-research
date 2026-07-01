from controllergate.core.curvature_selection import basin_stability_score


def test_basin_stability_blocks_flatline_without_replay():
    result = basin_stability_score(
        {"target_failure_reproduces": False, "semantic_failure_signature_exists": False},
        experiment_class="prospective_memory",
    )

    assert result["status"] == "BLOCK"
    assert result["blocker"] == "curvature_flatline_signal_rejected"
