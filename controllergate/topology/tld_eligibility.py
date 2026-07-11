from __future__ import annotations

import math
from typing import Any


def classify_parent(parent: dict[str, Any], rms_by_n: dict[int, float], *, minimum_deltas_pass: bool) -> dict[str, Any]:
    if parent.get("is_null") is True or parent.get("eligible") is not True or not parent.get("provenance_complete", False):
        return {"status": "INELIGIBLE", "classification": "ineligible_degenerate_omega", "reason": "parent_identity_or_provenance_ineligible"}
    omega = parent.get("omega_numeric") or parent.get("omega") or []
    if len(set(map(str, omega))) <= 1:
        return {"status": "INELIGIBLE", "classification": "ineligible_degenerate_omega", "reason": "degenerate_omega"}
    if not minimum_deltas_pass:
        return {"status": "INELIGIBLE", "classification": "ineligible_minimum_deltas", "reason": "minimum_deltas_gate_failed"}
    finite = {n: value for n, value in rms_by_n.items() if math.isfinite(value)}
    if not finite:
        return {"status": "INELIGIBLE", "classification": "ineligible_nonfinite", "reason": "no_finite_rms"}
    if len(finite) < 3:
        return {"status": "INELIGIBLE", "classification": "ineligible_insufficient_N", "reason": "fewer_than_three_finite_N"}
    if max(finite.values()) - min(finite.values()) <= 1e-15:
        return {"status": "INELIGIBLE", "classification": "ineligible_flatline", "reason": "zero_rms_variance"}
    return {"status": "PASS", "classification": "eligible_parent", "reason": None}
