from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class InterlockInput:
    interlock_id: str
    candidate_id: str
    prior_state: str
    proposed_next_state: str
    evidence: dict[str, Any]
    evidence_hashes: tuple[str, ...]


@dataclass(frozen=True)
class InterlockOutput:
    interlock_id: str
    handler_name: str
    decision: str
    protected_fact: str
    blocker: str | None
    reopen_conditions: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class InterlockVerification:
    interlock_id: str
    verifier_name: str
    status: str
    recomputed_fact: bool
    errors: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class InterlockTransition:
    event_id: str
    candidate_id: str
    prior_state_hash: str
    raw_input_hashes: tuple[str, ...]
    interlocks_evaluated: tuple[str, ...]
    interlock_decisions: tuple[dict[str, Any], ...]
    handler_result: dict[str, Any]
    independent_verifier_result: dict[str, Any]
    operation_status: str
    evidence_status: str
    gate_decision: str
    candidate_state: str
    blocker: str | None
    next_action: str
    reopen_conditions: tuple[str, ...]
    post_state_hash: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)
