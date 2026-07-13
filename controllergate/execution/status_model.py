from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class StatusModel:
    operation_status: str
    evidence_status: str
    gate_decision: str
    candidate_state: str

    def as_dict(self) -> dict[str, str]:
        return {
            "operation_status": self.operation_status,
            "evidence_status": self.evidence_status,
            "gate_decision": self.gate_decision,
            "candidate_state": self.candidate_state,
        }
