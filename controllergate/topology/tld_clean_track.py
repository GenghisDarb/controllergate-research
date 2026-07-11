from __future__ import annotations

import math
from typing import Any

from .tld_closure_mode import proposed_second_difference_elbow_v1_software_diagnostic_noncanonical, winner_n_argmin
from .tld_eligibility import classify_parent
from .tld_flatline import flatline_diagnostics


def rms_n_difference(omega: list[float], n: int, minimum_deltas: int) -> float:
    deltas = [omega[index + n] - omega[index] for index in range(len(omega) - n)]
    if len(deltas) < minimum_deltas:
        return math.nan
    return math.sqrt(sum(value * value for value in deltas) / len(deltas))


def evaluate_parent(parent: dict[str, Any], n_list: list[int], minimum_deltas: int) -> dict[str, Any]:
    omega = [float(value) for value in parent.get("omega_numeric", [])]
    rms = {n: rms_n_difference(omega, n, minimum_deltas) for n in n_list}
    minimum_pass = any(math.isfinite(value) for value in rms.values())
    eligibility = classify_parent(parent, rms, minimum_deltas_pass=minimum_pass)
    argmin = winner_n_argmin(rms) if eligibility["status"] == "PASS" else {"status": "NOT_ESTABLISHED", "winner_N_argmin": None, "blocker": eligibility["classification"]}
    elbow = proposed_second_difference_elbow_v1_software_diagnostic_noncanonical(rms)
    return {"ladder_id": parent["ladder_id"], "candidate_id": parent["candidate_id"], "rms_metric_family": "N_difference_RMS", "rms_by_N": {str(key): value if math.isfinite(value) else None for key, value in rms.items()}, "eligibility": eligibility, "flatline": flatline_diagnostics(rms), "winner_N_argmin": argmin, "winner_N_elbow": {"status": "NOT_ESTABLISHED", "winner_N_elbow": None, "blocker": "historical_elbow_formula_not_recovered"}, "noncanonical_elbow_diagnostic": elbow, "repair_authority": False}
