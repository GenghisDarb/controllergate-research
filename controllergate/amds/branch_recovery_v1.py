from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Iterable, Mapping


BRANCH_STATES = {"CLOSED", "REOPEN_ELIGIBLE", "REOPENED", "PERMANENTLY_BLOCKED"}


def canonical_assumptions(values: Iterable[Mapping[str, Any]]) -> tuple[str, ...]:
    normalized = [json.dumps(dict(value), sort_keys=True, separators=(",", ":"), default=str) for value in values]
    return tuple(sorted(set(normalized)))


def semantic_nogood_id(values: Iterable[Mapping[str, Any]]) -> str:
    canonical = canonical_assumptions(values)
    return "nogood:" + hashlib.sha256(json.dumps(canonical, separators=(",", ":")).encode()).hexdigest()


@dataclass(frozen=True)
class FailedBranchV1:
    branch_id: str
    candidate_id: str
    run_id: str
    frame_hash: str
    observer_state_hash: str
    parent_branch_id: str
    checkpoint_hash: str
    minimal_conflicting_assumption_set: tuple[str, ...]
    closing_observation_ids: tuple[str, ...]
    closing_fact_ids: tuple[str, ...]
    closing_evidence_hash: str
    nogood_id: str
    spent_probe_nonces: tuple[str, ...]
    affected_cell_ids: tuple[str, ...]
    affected_edge_ids: tuple[str, ...]
    affected_region_ids: tuple[str, ...]
    rollback_state_hash: str
    cleanup_state: str
    recovery_region: str
    reopen_condition: str
    branch_state: str
    authority_allowed: tuple[str, ...]
    authority_forbidden: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.recovery_region or not self.reopen_condition:
            raise ValueError("failed branch requires recovery_region and reopen_condition")
        if self.branch_state not in BRANCH_STATES:
            raise ValueError("invalid failed-branch state")
        if not self.minimal_conflicting_assumption_set or not self.nogood_id:
            raise ValueError("failed branch requires canonical conflicting assumptions and nogood")

    def record(self) -> dict[str, Any]:
        return asdict(self)


class NogoodStoreV1:
    def __init__(self) -> None:
        self.nogoods: dict[str, tuple[str, ...]] = {}
        self.spent_nonces: set[str] = set()
        self.branches: dict[str, FailedBranchV1] = {}

    def close_branch(self, branch: FailedBranchV1) -> None:
        if branch.branch_id in self.branches:
            raise ValueError("failed branch cannot be silently replaced or deleted")
        expected = "nogood:" + hashlib.sha256(json.dumps(branch.minimal_conflicting_assumption_set, separators=(",", ":")).encode()).hexdigest()
        if branch.nogood_id != expected:
            raise ValueError("nogood is not canonical over semantic assumptions")
        self.branches[branch.branch_id] = branch
        self.nogoods[branch.nogood_id] = branch.minimal_conflicting_assumption_set
        self.spent_nonces.update(branch.spent_probe_nonces)

    def authorize_branch(self, assumptions: Iterable[Mapping[str, Any]], nonce: str, prerequisite_nogoods: Iterable[str] = ()) -> dict[str, Any]:
        nogood = semantic_nogood_id(assumptions)
        reasons = []
        if nogood in self.nogoods:
            reasons.append("semantic_nogood_repetition")
        if nonce in self.spent_nonces:
            reasons.append("spent_nonce_reuse")
        if set(prerequisite_nogoods).intersection(self.nogoods):
            reasons.append("prerequisites_recreate_closed_branch")
        return {"status": "REJECTED" if reasons else "AUTHORIZED", "nogood_id": nogood, "reasons": reasons, "authority_forbidden": ["terminal transfer", "source ownership", "repair license", "count mutation"]}

    def delete(self, branch_id: str) -> None:
        raise ValueError(f"failed branch deletion forbidden: {branch_id}")
