from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum

from .stable_identity import stable_hash


class Phase(str, Enum):
    INTAKE = "INTAKE"
    MATERIALIZATION = "MATERIALIZATION"
    DIAGNOSIS = "DIAGNOSIS"
    CAUSAL_COMMIT = "CAUSAL_COMMIT"
    LICENSING = "LICENSING"
    INTERVENTION = "INTERVENTION"
    VALIDATION = "VALIDATION"
    DUPLICATE_REPLAY = "DUPLICATE_REPLAY"
    CANARY = "CANARY"
    RELEASE_REVIEW = "RELEASE_REVIEW"
    QUIESCENT_WAITING_FOR_EVIDENCE = "QUIESCENT_WAITING_FOR_EVIDENCE"
    FAILED_TERMINAL = "FAILED_TERMINAL"
    ROLLED_BACK = "ROLLED_BACK"


@dataclass
class Checkpoint:
    checkpoint_id: str
    phase: Phase
    sensor: str
    raw_signal_hash: str
    transducer: str
    effector: str
    blocked_transition: str
    release_condition: str
    reversibility: str
    evidence_hash: str
    reopen_condition: str
    resolved: bool = False

    @property
    def inhibitor_token(self) -> str | None:
        if self.resolved:
            return None
        return stable_hash({"type": "GLOBAL_TRANSITION_INHIBITOR_TOKEN", "checkpoint": self.checkpoint_id,
                            "transition": self.blocked_transition, "evidence": self.evidence_hash})


class CheckpointEngine:
    def __init__(self) -> None:
        self.checkpoints: dict[str, Checkpoint] = {}
        self.spent_authorizations: set[str] = set()

    def register(self, checkpoint: Checkpoint) -> None:
        if checkpoint.checkpoint_id in self.checkpoints:
            raise ValueError("checkpoint identity already registered")
        self.checkpoints[checkpoint.checkpoint_id] = checkpoint

    def resolve(self, checkpoint_id: str, evidence_hash: str) -> None:
        checkpoint = self.checkpoints[checkpoint_id]
        if evidence_hash != checkpoint.evidence_hash:
            raise ValueError("checkpoint evidence mismatch")
        checkpoint.resolved = True

    def transition_allowed(self, transition: str) -> dict[str, object]:
        blockers = [cp for cp in self.checkpoints.values() if cp.blocked_transition == transition and not cp.resolved]
        return {"allowed": not blockers, "blockers": [cp.checkpoint_id for cp in blockers],
                "inhibitor_tokens": [cp.inhibitor_token for cp in blockers],
                "status": "PASS" if not blockers else "BLOCK"}

    def consume_once(self, authorization: str) -> None:
        if authorization in self.spent_authorizations:
            raise ValueError("single-use authorization already consumed")
        self.spent_authorizations.add(authorization)

    def record(self) -> list[dict[str, object]]:
        return [{**asdict(cp), "phase": cp.phase.value, "inhibitor_token": cp.inhibitor_token} for cp in self.checkpoints.values()]
