from __future__ import annotations

EVENT_COSTS = {
    "candidate_verification_attempt": 1,
    "repo_clone": 2,
    "dependency_install_attempt": 2,
    "test_command_probe": 1,
    "issue_derived_harness_generation": 2,
    "repair_fork": 3,
    "micro_reversal": 1,
    "duplicate_replay_run": 1,
}


def create_budget(max_units: int) -> dict[str, object]:
    return {"max_units": max_units, "remaining_units": max_units, "events": [], "status": "PASS", "blocker": None}


def spend_budget(budget: dict[str, object], event_type: str, reason: str = "") -> dict[str, object]:
    cost = int(EVENT_COSTS[event_type])
    remaining = int(budget.get("remaining_units", 0)) - cost
    event = {"event_type": event_type, "cost": cost, "reason": reason, "remaining_after": remaining}
    budget.setdefault("events", []).append(event)
    budget["remaining_units"] = remaining
    if remaining < 0:
        budget["status"] = "BLOCK"
        budget["blocker"] = "exploration_budget_exhausted"
    return budget


def budget_exhausted(budget: dict[str, object]) -> bool:
    return budget.get("blocker") == "exploration_budget_exhausted" or int(budget.get("remaining_units", 0)) < 0
