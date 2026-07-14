from __future__ import annotations

import math


def normalize(weights: dict[str, float]) -> dict[str, float]:
    if any(value < 0 for value in weights.values()):
        raise ValueError("negative probability weight")
    total = sum(weights.values())
    if total <= 0:
        raise ValueError("positive probability mass required")
    return {key: value / total for key, value in weights.items()}


def entropy(probabilities: dict[str, float]) -> float:
    normalized = normalize(probabilities)
    return -sum(value * math.log(value, 2) for value in normalized.values() if value > 0)


def expected_information_gain(
    prior: dict[str, float], likelihoods: dict[str, dict[str, float]]
) -> tuple[float, dict[str, object]]:
    p = normalize(prior)
    prior_entropy = entropy(p)
    expected_posterior_entropy = 0.0
    outcomes: dict[str, object] = {}
    for outcome, by_hypothesis in sorted(likelihoods.items()):
        outcome_probability = sum(p[hypothesis] * by_hypothesis.get(hypothesis, 0.0) for hypothesis in p)
        if outcome_probability <= 0:
            continue
        posterior = normalize(
            {
                hypothesis: p[hypothesis] * by_hypothesis.get(hypothesis, 0.0)
                for hypothesis in p
            }
        )
        posterior_entropy = entropy(posterior)
        expected_posterior_entropy += outcome_probability * posterior_entropy
        outcomes[outcome] = {
            "outcome_probability": outcome_probability,
            "posterior": posterior,
            "posterior_entropy": posterior_entropy,
        }
    information_gain = prior_entropy - expected_posterior_entropy
    return information_gain, {
        "expected_posterior_entropy": expected_posterior_entropy,
        "information_gain": information_gain,
        "outcomes": outcomes,
        "prior": p,
        "prior_entropy": prior_entropy,
    }
