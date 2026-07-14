from __future__ import annotations

HYPOTHESES = (
    "source_owned_behavior_defect",
    "provider_owned",
    "environment_owned",
    "platform_owned",
    "network_or_transport_owned",
    "harness_owned",
    "test_or_expectation_fragility",
    "mixed_failure",
    "insufficient_evidence",
)


def uniform_distribution() -> dict[str, float]:
    probability = 1.0 / len(HYPOTHESES)
    return {hypothesis: probability for hypothesis in HYPOTHESES}


def validate_distribution(distribution: dict[str, float]) -> None:
    if set(distribution) != set(HYPOTHESES):
        raise ValueError("hypothesis_space_mismatch")
    if any(value < 0 for value in distribution.values()):
        raise ValueError("negative_probability")
    if abs(sum(distribution.values()) - 1.0) > 1e-9:
        raise ValueError("probability_sum_mismatch")
