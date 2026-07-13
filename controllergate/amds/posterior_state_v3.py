from __future__ import annotations

import math
from typing import Any

from controllergate.core.evidence import hash_record

HYPOTHESES = (
    "source_owned_behavior_defect", "environment_owned", "test_expectation_fragility",
    "interpreter_behavior_change", "harness_owned", "resource_timeout", "mixed_failure", "insufficient_evidence",
)


def initialize_posterior(*, memory_condition: str = "NO_MEMORY", prior_overrides: dict[str, float] | None = None) -> dict[str, Any]:
    priors = {name: 1.0 / len(HYPOTHESES) for name in HYPOTHESES}
    if prior_overrides:
        priors.update(prior_overrides)
        total = sum(priors.values())
        priors = {key: value / total for key, value in priors.items()}
    state = {name: {"state": "OPEN", "prior_classification": memory_condition, "prior_value": priors[name], "evidence_support": [], "evidence_refutation": [], "posterior_value": priors[name], "last_update": "INITIALIZED", "reopen_conditions": ["new_verified_evidence"]} for name in HYPOTHESES}
    return {"memory_condition": memory_condition, "hypotheses": state, "state_hash": hash_record(state)}


def entropy(state: dict[str, Any]) -> float:
    values = [float(item["posterior_value"]) for item in state["hypotheses"].values() if float(item["posterior_value"]) > 0]
    return -sum(value * math.log2(value) for value in values)


def apply_observation(state: dict[str, Any], *, evidence_hash: str, supported: list[str], refuted: list[str], likelihood_basis: str) -> dict[str, Any]:
    before = entropy(state); changed = False
    for name, item in state["hypotheses"].items():
        if name in supported:
            item["evidence_support"].append(evidence_hash); item["state"] = "SUPPORTED"; changed = True
        if name in refuted:
            item["evidence_refutation"].append(evidence_hash); item["state"] = "REFUTED"; item["posterior_value"] = 0.0; changed = True
        item["last_update"] = evidence_hash if name in supported or name in refuted else "PRESERVED_WITHOUT_APPLICABLE_EVIDENCE"
    total = sum(float(item["posterior_value"]) for item in state["hypotheses"].values())
    if total:
        for item in state["hypotheses"].values(): item["posterior_value"] = float(item["posterior_value"]) / total
    state["state_hash"] = hash_record(state["hypotheses"])
    after = entropy(state)
    return {"state": state, "informative": changed, "noninformative_preservation": not changed, "entropy_before": before, "entropy_after": after, "likelihood_basis": likelihood_basis}
