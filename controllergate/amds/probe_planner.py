from __future__ import annotations

from dataclasses import asdict
from typing import Any
from .posterior import entropy_nats
from .types import ProbeCandidate


def expected_information_gain(prior: dict[str,float], outcomes: dict[str,dict[str,float]]) -> float | None:
    if not outcomes: return None
    before=entropy_nats(prior); expected=0.0; total_weight=0.0
    for probability, posterior in ((v.get("probability"),v.get("posterior")) for v in outcomes.values()):
        if probability is None or posterior is None: return None
        expected += float(probability)*entropy_nats(posterior); total_weight += float(probability)
    return before-expected if abs(total_weight-1.0)<1e-9 else None


def rank_probes(probes: list[ProbeCandidate], prior: dict[str,float], likelihood_registry: dict[str,Any]) -> list[dict[str,Any]]:
    ranked=[]
    for probe in probes:
        ig=expected_information_gain(prior, likelihood_registry.get(probe.probe_id,{}))
        utility=None if ig is None else ig-probe.execution_cost*0.05-probe.security_risk-probe.mutation_risk
        ranked.append({**asdict(probe),"expected_information_gain_nats":ig,"utility":utility,"prior_classification":"structural_uniform_uncalibrated_prior"})
    return sorted(ranked,key=lambda p:(p["utility"] is None,-(p["utility"] or 0),p["probe_id"]))
