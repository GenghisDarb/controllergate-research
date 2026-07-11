from __future__ import annotations

import math


def winner_n_argmin(rms_by_n: dict[int, float]) -> dict[str, object]:
    finite = [(n, value) for n, value in rms_by_n.items() if math.isfinite(value)]
    if not finite:
        return {"status": "NOT_ESTABLISHED", "winner_N_argmin": None, "blocker": "no_eligible_finite_rms"}
    minimum = min(value for _, value in finite)
    winners = sorted(n for n, value in finite if value == minimum)
    return {"status": "PASS", "winner_N_argmin": winners[0], "tie_policy": "smallest_N", "minimum_rms": minimum, "tied_candidates": winners}


def proposed_second_difference_elbow_v1_software_diagnostic_noncanonical(rms_by_n: dict[int, float]) -> dict[str, object]:
    return {"status": "NOT_RUN", "canonical": False, "diagnostic_name": "proposed_second_difference_elbow_v1_software_diagnostic_noncanonical", "blocker": "proposal_not_ratified", "winner_N_elbow": None}
