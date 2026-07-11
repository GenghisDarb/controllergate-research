from __future__ import annotations


def structural_uniform_prior(hypothesis_ids: list[str]) -> dict:
    probability = 1.0 / len(hypothesis_ids) if hypothesis_ids else 0.0
    return {"classification":"structural_uniform_uncalibrated_prior","probabilities":{h:probability for h in hypothesis_ids},"calibrated":False}
