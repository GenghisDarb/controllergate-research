from controllergate.core.curvature_selection import null_ensemble_curvature_fairness_audit


def test_null_curvature_fairness_not_run_without_ensemble():
    result = null_ensemble_curvature_fairness_audit(ensemble_runs=False, arm_a_vector_hash=None, null_vector_hashes=[])

    assert result["status"] == "NOT_RUN"
