from controllergate.runtime.compute_budget import ComputeBudget


def test_compute_budget_produces_safe_stop_after_exhaustion():
    budget = ComputeBudget(max_probes=1, max_patch_fragments=1, max_null_attempts=1, max_retries=0, max_runtime_seconds=10)
    budget.spend("probes")
    result = budget.spend("probes")
    assert result["status"] == "SAFE_STOP"
    assert result["blocker"] == "safe_stop_budget_exceeded"
    assert result["workspace_quarantine_required"] is True
