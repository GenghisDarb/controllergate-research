from controllergate.core.curvature_selection import curvature_heuristic_freeze, curvature_score_formula, curvature_thresholds


def test_curvature_heuristic_freeze_versions_formula_and_thresholds():
    freeze = curvature_heuristic_freeze()

    assert freeze["formula_frozen_before_seed_intake"] is True
    assert curvature_score_formula()["formula_version"] == freeze["formula_version"]
    assert curvature_thresholds()["formula_version"] == freeze["formula_version"]
