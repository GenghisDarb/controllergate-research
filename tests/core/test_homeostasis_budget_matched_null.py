from __future__ import annotations

from controllergate.core.clean_repair import matched_null_budget_state, matched_null_homeostasis_state


def test_budget_exhaustion_blocks_cleanly():
    events = ["micro_reversal"] * 7
    result = matched_null_budget_state("arm_a", events)

    assert result["status"] == "BLOCK"
    assert result["blocker"] == "bounded_exploration_budget_exhausted"


def test_homeostasis_state_passes_bounded_arm_budgets():
    arm = matched_null_budget_state("arm_a", ["pre_repair_replay", "patch_generation"])
    result = matched_null_homeostasis_state([arm])

    assert result["status"] == "PASS"
    assert result["risk_temperature"] <= result["risk_threshold"]
