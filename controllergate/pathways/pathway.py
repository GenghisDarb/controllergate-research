from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .event import Event
from .stable_identity import stable_identity, state_hash, versioned_identity_record


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
    normal_reference_pathway: str | None = None
    incident_variant_pathway: str | None = None
    historical_aliases: tuple[str, ...] = ()
    replacement_pathway: str | None = None
    release_membership: str = "batch077"

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
            "normal_reference_pathway": self.normal_reference_pathway,
            "incident_variant_pathway": self.incident_variant_pathway,
        }
        record.update(versioned_identity_record("pathway", {"pathway_id": self.pathway_id, "episode_id": self.episode_id}, version=self.pathway_version, historical_aliases=self.historical_aliases, replacement_identity=self.replacement_pathway, release_membership=self.release_membership))
        record["pathway_hash"] = state_hash(record)
        return record


def cycle_safe_composition(graph: dict[str, list[dict[str, str]]], start: str, *, max_depth: int = 64) -> dict[str, Any]:
    visited: set[str] = set()
    included: list[dict[str, str]] = []
    excluded: list[dict[str, Any]] = []

    def visit(node: str, depth: int, active: tuple[str, ...]) -> None:
        if depth > max_depth:
            excluded.append({"source": active[-1] if active else start, "target": node, "edge_type": "depth_limit", "reason": "maximum_traversal_depth", "cycle_proof": list(active), "available_as_non_composition_reference": True})
            return
        visited.add(node)
        for edge in graph.get(node, []):
            target = edge["target"]
            edge_type = edge.get("edge_type", "composition")
            if target in active or target == node:
                excluded.append({"source": node, "target": target, "edge_type": edge_type, "reason": "cycle_detected", "cycle_proof": list(active + (node, target)), "available_as_non_composition_reference": True})
                continue
            included.append({"source": node, "target": target, "edge_type": edge_type})
            if target not in visited:
                visit(target, depth + 1, active + (node,))

    visit(start, 0, ())
    return {"status": "PASS", "start": start, "max_depth": max_depth, "visited": sorted(visited), "included_edges": included, "excluded_edges": excluded, "silent_edge_deletion": False}
