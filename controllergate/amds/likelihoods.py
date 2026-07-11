from __future__ import annotations


def deterministic_binary_likelihood(targeted: list[str], all_hypotheses: list[str]) -> dict:
    return {h:{"positive":1.0 if h in targeted else 0.0,"negative":0.0 if h in targeted else 1.0,"classification":"deterministic_probe_contract"} for h in all_hypotheses}
