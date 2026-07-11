from __future__ import annotations


def stop_reason(*, isolated: bool, legal_remaining: int, information_gain: float, floor: float, budget_used: int, budget_limit: int, interlock_blocked: bool) -> str | None:
    if isolated: return "causal_family_isolated"
    if interlock_blocked: return "interlock_blocked"
    if legal_remaining == 0: return "legal_probes_exhausted"
    if information_gain < floor: return "information_gain_floor_not_met"
    if budget_used >= budget_limit: return "resource_budget_reached"
    return None
