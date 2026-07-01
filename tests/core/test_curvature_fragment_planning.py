from controllergate.core.curvature_selection import curvature_fragment_plan


def test_curvature_fragment_plan_not_run_without_repair_run():
    result = curvature_fragment_plan(None, interlock_count=0, repair_runs=False)

    assert result["status"] == "NOT_RUN"
    assert result["fragments"] == []
