"""Truth-blind, nonauthorizing Reactome-guided causal planner."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Iterable, Mapping


FORBIDDEN_INPUT_KEYS = {
    "truth",
    "private_truth",
    "sealed_truth",
    "gold_patch",
    "future_fix",
    "ownership_label",
}


def canonical_hash(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


@dataclass(frozen=True)
class ReactomePlannerDecisionV1:
    candidate: str
    current_maintenance_state: Mapping[str, Any]
    source_rpir_parents: tuple[str, ...]
    missing_prerequisites: tuple[str, ...]
    blocked_reactions: tuple[str, ...]
    legal_reaction_analogues: tuple[str, ...]
    alternative_pathways: tuple[str, ...]
    selected_intervention: str | None
    rejected_interventions: tuple[str, ...]
    selection_rationale: str
    expected_information_gain: float
    cost: int
    budget: int
    truth_access: int
    tld_access: int
    authority_allowed: str
    authority_forbidden: tuple[str, ...]
    decision_hash: str

    def record(self) -> dict[str, Any]:
        return asdict(self)


def _reject_forbidden_state(state: Mapping[str, Any]) -> None:
    forbidden = FORBIDDEN_INPUT_KEYS.intersection(key.lower() for key in state)
    if forbidden:
        raise ValueError(f"forbidden planner input: {sorted(forbidden)}")


def plan_intervention(
    *,
    candidate: str,
    maintenance_state: Mapping[str, Any],
    public_rpir_relations: Iterable[Mapping[str, Any]],
    legal_interventions: Iterable[Mapping[str, Any]],
    budget: int,
) -> ReactomePlannerDecisionV1:
    """Select one registered legal intervention without opening outcomes."""
    _reject_forbidden_state(maintenance_state)
    if budget < 0:
        raise ValueError("budget must be nonnegative")
    relations = list(public_rpir_relations)
    actions = list(legal_interventions)
    for relation in relations:
        _reject_forbidden_state(relation)
    for action in actions:
        _reject_forbidden_state(action)
        if "intervention_id" not in action:
            raise ValueError("legal interventions require intervention_id")
        if action.get("legal") is not True:
            raise ValueError("planner inventory contains an illegal intervention")
    parents = tuple(
        sorted(
            {
                str(relation["source_hash"])
                for relation in relations
                if relation.get("source_hash")
            }
        )
    )
    missing = tuple(
        sorted(
            {
                str(value)
                for relation in relations
                for value in relation.get("missing_prerequisites", [])
            }
        )
    )
    blocked = tuple(
        sorted(
            {
                str(relation.get("reaction"))
                for relation in relations
                if relation.get("blocked") is True and relation.get("reaction")
            }
        )
    )
    alternatives = tuple(
        sorted(
            {
                str(value)
                for relation in relations
                for value in relation.get("alternative_pathways", [])
            }
        )
    )
    affordable = [action for action in actions if int(action.get("cost", 1)) <= budget]
    ranked = sorted(
        affordable,
        key=lambda action: (
            -float(action.get("expected_information_gain", 0.0)),
            int(action.get("cost", 1)),
            str(action["intervention_id"]),
        ),
    )
    selected = str(ranked[0]["intervention_id"]) if ranked else None
    rejected = tuple(
        str(action["intervention_id"])
        for action in actions
        if str(action["intervention_id"]) != selected
    )
    expected_gain = float(ranked[0].get("expected_information_gain", 0.0)) if ranked else 0.0
    cost = int(ranked[0].get("cost", 1)) if ranked else 0
    analogue_ids = tuple(str(action["intervention_id"]) for action in actions)
    rationale = (
        "highest preregistered information gain among affordable legal interventions"
        if selected
        else "safe termination: no affordable legal intervention remains"
    )
    unhashed = {
        "candidate": candidate,
        "current_maintenance_state": dict(maintenance_state),
        "source_rpir_parents": parents,
        "missing_prerequisites": missing,
        "blocked_reactions": blocked,
        "legal_reaction_analogues": analogue_ids,
        "alternative_pathways": alternatives,
        "selected_intervention": selected,
        "rejected_interventions": rejected,
        "selection_rationale": rationale,
        "expected_information_gain": expected_gain,
        "cost": cost,
        "budget": budget,
        "truth_access": 0,
        "tld_access": 0,
        "authority_allowed": "order one already-registered legal public intervention",
        "authority_forbidden": (
            "causal fact",
            "ownership",
            "dependency invention",
            "fixture invention",
            "source-path invention",
            "illegal probe",
            "patch",
            "repair count",
            "release promotion",
        ),
    }
    return ReactomePlannerDecisionV1(
        **unhashed, decision_hash=canonical_hash(unhashed)
    )
