from __future__ import annotations

import math


def entropy_nats(probabilities: dict[str,float]) -> float:
    return -sum(p*math.log(p) for p in probabilities.values() if p>0)


def bayes_update(prior: dict[str,float], likelihood: dict[str,float]) -> dict[str,float]:
    raw={k:prior.get(k,0.0)*likelihood.get(k,0.0) for k in prior}; total=sum(raw.values())
    return {k:(v/total if total else prior.get(k,0.0)) for k,v in raw.items()}
