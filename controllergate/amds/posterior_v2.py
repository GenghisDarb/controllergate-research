from __future__ import annotations


def bayes_update(prior: dict[str, float], likelihood: dict[str, float]) -> dict[str, float]:
    values = {key: prior[key] * likelihood.get(key, 0.0) for key in prior}
    total = sum(values.values())
    if total <= 0:
        raise ValueError("zero_evidence_posterior")
    return {key: value / total for key, value in values.items()}
