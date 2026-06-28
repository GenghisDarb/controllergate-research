from __future__ import annotations

from controllergate.core.budget import budget_exhausted, create_budget, spend_budget


def test_budget_decrements_and_blocks():
    budget = create_budget(1)
    spend_budget(budget, "candidate_verification_attempt")
    assert not budget_exhausted(budget)
    spend_budget(budget, "test_command_probe")
    assert budget_exhausted(budget)
    assert budget["blocker"] == "exploration_budget_exhausted"
