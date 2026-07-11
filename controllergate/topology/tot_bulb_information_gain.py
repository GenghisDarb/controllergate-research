from __future__ import annotations


def score_probe(probe: dict[str, object]) -> float:
    return round(
        3.0 * float(probe.get("expected_information_gain", 0.0))
        + 2.0 * float(probe.get("evidence_quality", 0.0))
        + float(probe.get("orthology_value", 0.0))
        + float(probe.get("reversibility", 0.0))
        - float(probe.get("execution_cost", 0.0))
        - 2.0 * float(probe.get("security_risk", 0.0))
        - 2.0 * float(probe.get("mutation_risk", 0.0)), 9)
