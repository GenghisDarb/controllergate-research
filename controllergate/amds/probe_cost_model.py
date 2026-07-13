from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any


FROZEN_COST_WEIGHTS: dict[str, float] = {
    "wall_time": 1.0,
    "compute": 0.8,
    "provider_rebuild_requirement": 3.0,
    "subprocess_requirement": 0.7,
    "environment_rebuild_requirement": 2.5,
    "manual_review_burden": 2.0,
    "mutation_risk": 4.0,
}


def calculate_probe_cost(
    dimensions: Mapping[str, float | int | bool], *, evidence_value: float
) -> dict[str, Any]:
    raw = sum(float(dimensions.get(name, 0)) * weight for name, weight in FROZEN_COST_WEIGHTS.items())
    cost = max(raw, 1e-9)
    gain_per_cost = float(evidence_value) / cost
    return {
        "cost": round(cost, 6),
        "evidence_value": float(evidence_value),
        "expected_causal_closure_gain_per_unit_cost": round(gain_per_cost, 9),
        "dimensions": {name: dimensions.get(name, 0) for name in FROZEN_COST_WEIGHTS},
        "weights": dict(FROZEN_COST_WEIGHTS),
    }


def select_cost_sensitive_probe(probes: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    scored: list[dict[str, Any]] = []
    for probe in probes:
        score = calculate_probe_cost(
            probe.get("cost_dimensions", {}), evidence_value=float(probe.get("evidence_value", 0.0))
        )
        scored.append({**dict(probe), **score})
    scored.sort(key=lambda row: (-row["expected_causal_closure_gain_per_unit_cost"], str(row.get("probe_id", ""))))
    return {
        "status": "PASS" if scored else "BLOCK",
        "selected_probe": scored[0] if scored else None,
        "ranking": scored,
        "objective": "expected_causal_closure_gain_per_unit_cost",
        "probe_count_is_not_sole_objective": True,
    }
