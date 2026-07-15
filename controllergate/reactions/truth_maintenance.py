from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Iterable

from .stable_identity import stable_hash


class EpistemicState(str, Enum):
    TRUE_DIRECT = "TRUE_DIRECT"
    FALSE_DIRECT = "FALSE_DIRECT"
    TRUE_INFERRED = "TRUE_INFERRED"
    FALSE_INFERRED = "FALSE_INFERRED"
    UNKNOWN = "UNKNOWN"
    CONTRADICTED = "CONTRADICTED"
    REJECTED = "REJECTED"


TRUE = {EpistemicState.TRUE_DIRECT, EpistemicState.TRUE_INFERRED}
FALSE = {EpistemicState.FALSE_DIRECT, EpistemicState.FALSE_INFERRED}


@dataclass
class Fact:
    fact_id: str
    candidate_id: str
    run_id: str
    frame_hash: str
    state: EpistemicState
    evidence_hashes: tuple[str, ...] = ()
    derivation_parents: tuple[str, ...] = ()
    verifier: str = ""
    compartment: str = "decision_frame"
    retracted: bool = False

    @property
    def fact_hash(self) -> str:
        value = asdict(self); value["state"] = self.state.value
        return stable_hash(value)


@dataclass(frozen=True)
class Constraint:
    constraint_id: str
    kind: str
    members: tuple[str, ...]
    k: int | None = None
    hard: bool = True
    inference_allowed: bool = True


class TruthMaintenanceSystem:
    def __init__(self, facts: Iterable[Fact], constraints: Iterable[Constraint]) -> None:
        self.facts = {fact.fact_id: fact for fact in facts}
        self.constraints = list(constraints)
        self.deductions: list[dict[str, object]] = []
        self.contradictions: list[dict[str, object]] = []
        self.nogoods: list[dict[str, object]] = []

    def _set(self, fact_id: str, state: EpistemicState, constraint: Constraint) -> bool:
        fact = self.facts[fact_id]
        if fact.state == state:
            return False
        if fact.state in TRUE and state in FALSE or fact.state in FALSE and state in TRUE:
            self._contradict(constraint, [fact_id])
            return False
        if fact.state is not EpistemicState.UNKNOWN:
            return False
        fact.state = state
        fact.derivation_parents = (constraint.constraint_id,)
        self.deductions.append({"fact_id": fact_id, "state": state.value, "constraint_id": constraint.constraint_id})
        return True

    def _contradict(self, constraint: Constraint, facts: list[str]) -> None:
        record = {"constraint_id": constraint.constraint_id, "facts": facts,
                  "states": {fact: self.facts[fact].state.value for fact in facts}}
        record["contradiction_hash"] = stable_hash(record)
        if record not in self.contradictions:
            self.contradictions.append(record)

    def _apply(self, constraint: Constraint) -> bool:
        states = [self.facts[name].state for name in constraint.members]
        known_true = [name for name in constraint.members if self.facts[name].state in TRUE]
        known_false = [name for name in constraint.members if self.facts[name].state in FALSE]
        unknown = [name for name in constraint.members if self.facts[name].state is EpistemicState.UNKNOWN]
        changed = False
        if constraint.kind == "mutual_exclusion":
            if len(known_true) > 1 and constraint.hard:
                self._contradict(constraint, known_true)
            elif len(known_true) == 1 and constraint.inference_allowed:
                for name in unknown:
                    changed |= self._set(name, EpistemicState.FALSE_INFERRED, constraint)
        elif constraint.kind == "implication":
            antecedent, consequent = constraint.members
            a, b = self.facts[antecedent].state, self.facts[consequent].state
            if a in TRUE and b in FALSE:
                self._contradict(constraint, [antecedent, consequent])
            elif a in TRUE and b is EpistemicState.UNKNOWN and constraint.inference_allowed:
                changed |= self._set(consequent, EpistemicState.TRUE_INFERRED, constraint)
            # False or unknown antecedents intentionally do not imply a false consequent.
        elif constraint.kind in {"exactly_k", "at_most_k", "at_least_k"}:
            if constraint.k is None:
                raise ValueError("cardinality constraint requires k")
            k = constraint.k
            if constraint.kind in {"exactly_k", "at_most_k"} and len(known_true) > k:
                self._contradict(constraint, known_true)
            if constraint.kind in {"exactly_k", "at_least_k"} and len(known_true) + len(unknown) < k:
                self._contradict(constraint, known_false + unknown)
            if constraint.inference_allowed:
                if constraint.kind in {"exactly_k", "at_most_k"} and len(known_true) == k:
                    for name in unknown:
                        changed |= self._set(name, EpistemicState.FALSE_INFERRED, constraint)
                if constraint.kind in {"exactly_k", "at_least_k"} and k - len(known_true) == len(unknown):
                    for name in unknown:
                        changed |= self._set(name, EpistemicState.TRUE_INFERRED, constraint)
        elif constraint.kind == "prerequisite":
            prerequisite, later = constraint.members
            if self.facts[later].state in TRUE and self.facts[prerequisite].state not in TRUE:
                self._contradict(constraint, [prerequisite, later])
        elif constraint.kind == "identity_equality":
            direct_values = {self.facts[name].evidence_hashes for name in constraint.members if self.facts[name].state in TRUE}
            if len(direct_values) > 1:
                self._contradict(constraint, list(constraint.members))
        else:
            raise ValueError(f"unknown constraint kind: {constraint.kind}")
        return changed

    def fixed_point(self) -> dict[str, object]:
        rounds = 0
        changed = True
        while changed:
            rounds += 1
            changed = any(self._apply(constraint) for constraint in self.constraints)
            if rounds > max(2, len(self.facts) * 2):
                raise RuntimeError("truth maintenance did not converge")
        if self.contradictions:
            assumptions = sorted({fact for row in self.contradictions for fact in row["facts"]})
            nogood = {"assumptions": assumptions, "contradiction_hashes": [row["contradiction_hash"] for row in self.contradictions]}
            nogood["nogood_hash"] = stable_hash(nogood)
            self.nogoods.append(nogood)
        return {"status": "CONTRADICTED" if self.contradictions else "PASS", "rounds": rounds,
                "facts": [{**asdict(fact), "state": fact.state.value, "fact_hash": fact.fact_hash} for fact in self.facts.values()],
                "deductions": self.deductions, "contradictions": self.contradictions, "nogoods": self.nogoods}

    def backtrack(self) -> dict[str, object]:
        retracted = []
        for fact in self.facts.values():
            if fact.state in {EpistemicState.TRUE_INFERRED, EpistemicState.FALSE_INFERRED}:
                fact.retracted = True
                fact.state = EpistemicState.UNKNOWN
                retracted.append(fact.fact_id)
        return {"status": "BACKTRACKED", "direct_evidence_preserved": True,
                "retracted_inferred_facts": sorted(retracted), "learned_nogood_count": len(self.nogoods)}
