from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .event import Event
from .stable_identity import stable_identity, state_hash


@dataclass(frozen=True)
class Pathway:
    episode_id: str
    pathway_version: int
    events: tuple[Event, ...]
    branch_points: tuple[dict[str, Any], ...] = ()
    blockers: tuple[str, ...] = ()
    terminal_state: str = "UNKNOWN"
    terminal_ownership: str = "insufficient_evidence"
    safe_abstention: bool = True
    proof_references: tuple[str, ...] = ()
    probe_cost: int = 0

    @property
    def pathway_id(self) -> str:
        return stable_identity("pathway", {"episode_id": self.episode_id, "version": self.pathway_version})

    def to_record(self) -> dict[str, Any]:
        event_records = [event.to_record() for event in self.events]
        record = {
            "pathway_id": self.pathway_id,
            "pathway_version": self.pathway_version,
            "episode_id": self.episode_id,
            "events": event_records,
            "event_type_sequence": [event["event_type"] for event in event_records],
            "compartment_transition_sequence": [event["compartment"] for event in event_records],
            "branch_points": list(self.branch_points),
            "blockers": list(self.blockers),
            "terminal_state": self.terminal_state,
            "terminal_ownership": self.terminal_ownership,
            "safe_abstention": self.safe_abstention,
            "proof_references": list(self.proof_references),
            "probe_cost": self.probe_cost,
        }
        record["pathway_hash"] = state_hash(record)
        return record
