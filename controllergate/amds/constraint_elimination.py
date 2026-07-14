from __future__ import annotations


def eliminate(
    unresolved: set[str], observation: str, elimination_rules: dict[str, set[str]]
) -> dict[str, object]:
    removed = sorted(unresolved & elimination_rules.get(observation, set()))
    remaining = sorted(unresolved - set(removed))
    return {"constraints_eliminated": removed, "unresolved_hypotheses": remaining}
