from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Orientation:
    reference_role: str
    incident_role: str
    normal_role: str
    patched_role: str
    time_role: str
    source_hash: str
    provider_hash: str
    proof_parent: str

    def validate(self) -> None:
        if self.reference_role == self.incident_role or self.normal_role == self.patched_role:
            raise ValueError("orientation roles must remain distinct")
        if self.time_role not in {"decision_time", "outcome_time"}:
            raise ValueError("invalid time role")
