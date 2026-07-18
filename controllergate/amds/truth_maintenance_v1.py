from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Iterable, Mapping

from controllergate.topology.causal_hypergraph import CellState


def identity(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()


@dataclass(frozen=True)
class VerifiedCausalFactV1:
    candidate_id: str
    run_id: str
    frame_id: str
    subject_id: str
    state_proposal: CellState
    raw_observation_parents: tuple[str, ...]
    verifier_rule_id: str
    verifier_execution_receipt: str
    independent_evidence_parents: tuple[str, ...]
    scope: str
    confidence_mode: str
    provisional_branch: str
    reopen_condition: str
    fact_id: str = ""

    def __post_init__(self) -> None:
        if not self.raw_observation_parents or not self.verifier_execution_receipt:
            raise ValueError("causal fact proposal requires raw observations and executed verifier")
        if self.confidence_mode not in {"deterministic/direct", "calibrated/inferred"}:
            raise ValueError("unsupported confidence mode")
        object.__setattr__(self, "fact_id", f"fact:{identity([self.subject_id, self.state_proposal.value, self.raw_observation_parents, self.verifier_execution_receipt])}")

    def record(self) -> dict[str, Any]:
        value = asdict(self); value["state_proposal"] = self.state_proposal.value; return value


class TruthMaintenanceV1:
    def __init__(self, initial: Mapping[str, CellState], constraints: Iterable[Mapping[str, Any]]) -> None:
        self.states = dict(initial); self.constraints = list(constraints); self.checkpoints = [dict(self.states)]
        self.events: list[dict[str, Any]] = []; self.failed_branches: list[dict[str, Any]] = []; self.nogoods: set[str] = set(); self.spent_nonces: set[str] = set()

    def apply(self, fact: VerifiedCausalFactV1, *, nonce: str) -> dict[str, Any]:
        branch_key = identity([fact.subject_id, fact.state_proposal.value, fact.raw_observation_parents])
        if branch_key in self.nogoods:
            event = {"event": "repeated_branch_rejected", "branch_key": branch_key, "fact_id": fact.fact_id}; self.events.append(event); return event
        if nonce in self.spent_nonces:
            raise ValueError("spent nonce cannot be reused")
        self.spent_nonces.add(nonce)
        current = self.states.get(fact.subject_id, CellState.UNRESOLVED)
        opposing = {CellState.VERIFIED_TRUE: CellState.VERIFIED_FALSE, CellState.VERIFIED_FALSE: CellState.VERIFIED_TRUE, CellState.INFERRED_TRUE: CellState.INFERRED_FALSE, CellState.INFERRED_FALSE: CellState.INFERRED_TRUE}
        if opposing.get(current) == fact.state_proposal or opposing.get(fact.state_proposal) == current:
            conflict = {"event": "observation_driven_contradiction", "subject_id": fact.subject_id, "existing": current.value, "proposed": fact.state_proposal.value, "fact_id": fact.fact_id, "minimal_conflicting_assumptions": [current.value, fact.fact_id], "branch_key": branch_key}
            self.states[fact.subject_id] = CellState.CONTRADICTED
            self.failed_branches.append(conflict); self.nogoods.add(branch_key); self.events.append(conflict)
            restored = dict(self.checkpoints[-1]); self.states = restored
            self.events.append({"event": "checkpoint_restored", "branch_key": branch_key, "spent_nonce_preserved": True})
            return conflict
        self.states[fact.subject_id] = fact.state_proposal
        self.checkpoints.append(dict(self.states)); event = {"event": "provisional_fact_applied", "fact_id": fact.fact_id, "subject_id": fact.subject_id, "state": fact.state_proposal.value}; self.events.append(event)
        self._fixed_point()
        return event

    def _fixed_point(self) -> None:
        changed = True
        while changed:
            changed = False
            for rule in self.constraints:
                subjects = tuple(rule.get("subject_ids", ()))
                if len(subjects) != 2: continue
                left, right = subjects; relation = rule.get("relation")
                if relation == "MUTUALLY_EXCLUSIVE" and self.states.get(left) == CellState.VERIFIED_TRUE and self.states.get(right) == CellState.UNRESOLVED:
                    self.states[right] = CellState.INFERRED_FALSE; changed = True
                if relation == "CO_DEPENDENT" and self.states.get(left) == CellState.VERIFIED_TRUE and self.states.get(right) == CellState.UNRESOLVED:
                    self.states[right] = CellState.INFERRED_TRUE; changed = True
        self.events.append({"event": "truth_maintenance_fixed_point", "state_hash": identity({key: value.value for key, value in self.states.items()})})

    def result(self) -> dict[str, Any]:
        return {"states": {key: value.value for key, value in self.states.items()}, "events": self.events, "failed_branches": self.failed_branches, "nogoods": sorted(self.nogoods), "spent_nonce_count": len(self.spent_nonces), "status": "PASS"}
