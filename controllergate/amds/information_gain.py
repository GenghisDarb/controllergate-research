from __future__ import annotations

import math


def entropy(distribution: dict[str, float]) -> float:
    return -sum(value * math.log2(value) for value in distribution.values() if value > 0)


def expected_information_gain(
    prior: dict[str, float], observation_posteriors: dict[str, tuple[float, dict[str, float]]]
) -> float:
    return entropy(prior) - sum(weight * entropy(posterior) for weight, posterior in observation_posteriors.values())


def cost_adjusted_utility(information_gain: float, total_probe_cost: float, epsilon: float = 1e-9) -> float:
    return information_gain / max(total_probe_cost, epsilon)
