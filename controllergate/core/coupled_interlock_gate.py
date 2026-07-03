from __future__ import annotations

from typing import Any


def coupled_interlock_extension_gate_policy() -> dict[str, Any]:
    return {
        "status": "PASS",
        "requires_at_least_two_coupled_projections": True,
        "requires_computed_interlock_invariants": True,
        "diagnostic_only_without_invariants": True,
        "blocker_without_invariants": "coupled_interlock_used_without_invariants",
    }


def evaluate_coupled_interlock_gate(invariants: list[dict[str, Any]] | None) -> dict[str, Any]:
    invariants = invariants or []
    valid = [item for item in invariants if item.get("interlock_validated") is True]
    active = len(valid) >= 1
    return {
        "status": "PASS" if active else "BLOCK",
        "coupled_interlock_extension_active": active,
        "interlock_invariant_count": len(invariants),
        "validated_interlock_invariant_count": len(valid),
        "diagnostic_only": not active,
        "blocker": None if active else "coupled_interlock_used_without_invariants",
    }
