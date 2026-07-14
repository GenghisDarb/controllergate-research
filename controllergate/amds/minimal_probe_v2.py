from __future__ import annotations

from dataclasses import asdict
from typing import Callable

from controllergate.reactions.stable_identity import stable_hash

from .constraint_elimination import eliminate
from .hypothesis_space_v2 import HYPOTHESES
from .information_gain import cost_adjusted_utility, entropy, expected_information_gain
from .probe_contract_v2 import ProbeContractV2


TERMINAL_CLASSES = {
    "source_owned_behavior_defect",
    "provider_owned",
    "environment_owned",
    "platform_owned",
    "network_or_transport_owned",
    "harness_owned",
    "test_or_expectation_fragility",
    "mixed_failure",
}


def select_probe(
    probes: list[ProbeContractV2],
    unresolved_contacts: set[str],
    likelihood_model: dict[str, object],
    prior: dict[str, float] | None = None,
) -> dict[str, object]:
    legal = [probe for probe in probes if probe.evidence_contact in unresolved_contacts and probe.validate()["status"] == "PASS"]
    if not legal:
        raise ValueError("no_authorized_unresolved_probe")
    if likelihood_model.get("status") != "CALIBRATED_NON_HOLDOUT_FAMILIES":
        selected = min(legal, key=lambda probe: (probe.total_cost, probe.probe_id))
        return {
            "selection_method": "deterministic_constraint_elimination",
            "likelihood_status": "LIKELIHOOD_NOT_CALIBRATED",
            "selected_probe": selected.probe_id,
            "predicted_information_gain": None,
            "entropy_before": None,
            "selection_rationale": "lowest-cost authorized probe over an unresolved repair-critical contact",
        }
    if prior is None:
        raise ValueError("calibrated_selection_requires_prior")
    scored: list[tuple[float, ProbeContractV2, float]] = []
    likelihoods = likelihood_model["likelihoods"]
    for probe in legal:
        observations: dict[str, tuple[float, dict[str, float]]] = {}
        for observation in probe.possible_observation_classes:
            unnormalized = {
                hypothesis: prior[hypothesis]
                * likelihoods.get(f"{probe.probe_id}|{hypothesis}", {}).get(observation, 0.0)
                for hypothesis in prior
            }
            evidence = sum(unnormalized.values())
            if evidence > 0:
                observations[observation] = (evidence, {key: value / evidence for key, value in unnormalized.items()})
        if not observations:
            continue
        total_weight = sum(weight for weight, _ in observations.values())
        normalized = {key: (weight / total_weight, posterior) for key, (weight, posterior) in observations.items()}
        gain = expected_information_gain(prior, normalized)
        scored.append((cost_adjusted_utility(gain, probe.total_cost), probe, gain))
    if not scored:
        raise ValueError("calibrated_model_has_no_usable_probe_likelihood")
    utility, selected, gain = max(scored, key=lambda row: (row[0], row[1].probe_id))
    return {
        "selection_method": "calibrated_information_gain",
        "likelihood_status": likelihood_model["status"],
        "selected_probe": selected.probe_id,
        "predicted_information_gain": gain,
        "entropy_before": entropy(prior),
        "cost_adjusted_utility": utility,
        "selection_rationale": "highest authorized cost-adjusted expected information gain",
    }


def run_sequence(
    probes: list[ProbeContractV2],
    executor: Callable[[ProbeContractV2], dict[str, object]],
    elimination_rules: dict[str, set[str]],
    *,
    budget: int,
    likelihood_model: dict[str, object],
) -> dict[str, object]:
    unresolved_hypotheses = set(HYPOTHESES)
    unresolved_contacts = {probe.evidence_contact for probe in probes}
    observations: list[dict[str, object]] = []
    terminal_class: str | None = None
    for _ in range(budget):
        selection = select_probe(probes, unresolved_contacts, likelihood_model)
        probe = next(probe for probe in probes if probe.probe_id == selection["selected_probe"])
        result = executor(probe)
        observation = str(result["observation_class"])
        eliminated = eliminate(unresolved_hypotheses, observation, elimination_rules)
        unresolved_hypotheses = set(eliminated["unresolved_hypotheses"])
        unresolved_contacts.discard(probe.evidence_contact)
        terminal = result.get("terminal_class")
        if terminal in TERMINAL_CLASSES:
            terminal_class = str(terminal)
        record = {
            **selection,
            "probe": asdict(probe),
            "observation_class": observation,
            "direct_evidence": result.get("direct_evidence", []),
            "evidence_hash": stable_hash(result.get("direct_evidence", [])),
            "constraints_eliminated": eliminated["constraints_eliminated"],
            "unresolved_hypotheses": eliminated["unresolved_hypotheses"],
            "entropy_after": None,
            "realized_information_gain": None,
            "probe_cost": probe.total_cost,
        }
        observations.append(record)
        decisive_crypto = bool(result.get("decisive_cryptographic_fact"))
        if terminal_class and (len(observations) >= 2 or decisive_crypto):
            break
        if not unresolved_hypotheses or not unresolved_contacts:
            break
    return {
        "probe_count": len(observations),
        "observations": observations,
        "terminal_class": terminal_class or "insufficient_evidence",
        "closure_reason": "direct_terminal_evidence" if terminal_class else ("budget_exhausted" if len(observations) == budget else "alternatives_excluded"),
        "safe_abstention": terminal_class is None,
    }
