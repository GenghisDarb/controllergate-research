from __future__ import annotations

from collections import defaultdict
from typing import Iterable


MIN_FAMILIES = 3
MIN_OBSERVATIONS = 12


def calibrate_likelihoods(rows: Iterable[dict[str, str]], holdout_family: str) -> dict[str, object]:
    training = [row for row in rows if row.get("repository_family") != holdout_family]
    families = {row.get("repository_family") for row in training if row.get("repository_family")}
    if len(families) < MIN_FAMILIES or len(training) < MIN_OBSERVATIONS:
        return {
            "status": "LIKELIHOOD_NOT_CALIBRATED",
            "holdout_family": holdout_family,
            "training_family_count": len(families),
            "training_observation_count": len(training),
            "likelihoods": {},
        }
    counts: dict[tuple[str, str], dict[str, int]] = defaultdict(lambda: defaultdict(int))
    totals: dict[tuple[str, str], int] = defaultdict(int)
    for row in training:
        key = (row["probe_id"], row["hypothesis"])
        counts[key][row["observation"]] += 1
        totals[key] += 1
    likelihoods = {
        f"{probe}|{hypothesis}": {
            observation: count / totals[(probe, hypothesis)] for observation, count in observations.items()
        }
        for (probe, hypothesis), observations in counts.items()
    }
    return {
        "status": "CALIBRATED_NON_HOLDOUT_FAMILIES",
        "holdout_family": holdout_family,
        "training_family_count": len(families),
        "training_observation_count": len(training),
        "likelihoods": likelihoods,
    }
