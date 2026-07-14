from __future__ import annotations

from dataclasses import dataclass, field

from controllergate.state.integrity import canonical_hash


@dataclass(frozen=True)
class BoardCheckpoint:
    checkpoint_id: str
    active_hypotheses: tuple[str, ...]
    event_count: int
    parent_checkpoint_id: str | None


@dataclass
class BranchLedger:
    candidate_id: str
    run_id: str
    checkpoints: list[BoardCheckpoint] = field(default_factory=list)
    failed_branches: list[dict[str, object]] = field(default_factory=list)
    spent_nonces: set[str] = field(default_factory=set)
    backtrack_count: int = 0
    contradiction_count: int = 0

    def checkpoint(self, active_hypotheses: set[str], event_count: int) -> BoardCheckpoint:
        parent = self.checkpoints[-1].checkpoint_id if self.checkpoints else None
        checkpoint_id = canonical_hash(
            {
                "active_hypotheses": sorted(active_hypotheses),
                "candidate_id": self.candidate_id,
                "event_count": event_count,
                "parent": parent,
                "run_id": self.run_id,
            }
        )
        value = BoardCheckpoint(checkpoint_id, tuple(sorted(active_hypotheses)), event_count, parent)
        self.checkpoints.append(value)
        return value

    def spend_nonce(self, nonce: str) -> None:
        if nonce in self.spent_nonces:
            raise ValueError("duplicate nonce rejected")
        self.spent_nonces.add(nonce)

    def contradiction(
        self,
        *,
        assumptions: list[str],
        evidence_hashes: list[str],
        operation_identity: str,
        reopen_condition: str,
    ) -> set[str]:
        self.contradiction_count += 1
        self.backtrack_count += 1
        if not self.checkpoints:
            raise RuntimeError("contradiction requires a sealed checkpoint")
        parent = self.checkpoints[-1]
        record: dict[str, object] = {
            "assumptions": assumptions,
            "branch_closed": True,
            "candidate_id": self.candidate_id,
            "count_increment": False,
            "evidence_hashes": evidence_hashes,
            "next_legal_action": "resume_from_last_consistent_checkpoint",
            "operation_identity": operation_identity,
            "parent_checkpoint": parent.checkpoint_id,
            "reopen_condition": reopen_condition,
            "run_id": self.run_id,
            "success_token_minted": False,
        }
        record["branch_hash"] = canonical_hash(record)
        self.failed_branches.append(record)
        return set(parent.active_hypotheses)
