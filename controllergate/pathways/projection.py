from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from .stable_identity import stable_identity, state_hash


@dataclass(frozen=True)
class Projection:
    source_pathway_id: str
    source_pathway_version: int
    target_pathway_id: str
    knowledge_status: Literal["STRUCTURALLY_PROJECTED", "INFERRED_FROM_PATHWAY"]
    mapped_event_pairs: tuple[tuple[str, str], ...]
    unmapped_source_events: tuple[str, ...]
    unmapped_target_events: tuple[str, ...]
    matched_edge_types: tuple[str, ...]
    compartment_compatibility: float
    regulation_compatibility: float
    normal_incident_compatibility: float
    projection_confidence: float | Literal["NOT_ESTABLISHED"]
    projection_evidence_hash: str
    independent_verifier: str
    review_state: Literal["PASS", "BLOCK", "MANUAL_REVIEW"]

    @property
    def projection_id(self) -> str:
        return stable_identity("projection", {"source": self.source_pathway_id, "target": self.target_pathway_id, "mapped": self.mapped_event_pairs})

    def to_record(self) -> dict[str, Any]:
        record = {
            "projection_id": self.projection_id,
            "source_pathway_stable_id": self.source_pathway_id,
            "source_pathway_version": self.source_pathway_version,
            "target_candidate_pathway_id": self.target_pathway_id,
            "knowledge_status": self.knowledge_status,
            "mapped_event_pairs": [list(item) for item in self.mapped_event_pairs],
            "unmapped_source_events": list(self.unmapped_source_events),
            "unmapped_target_events": list(self.unmapped_target_events),
            "matched_edge_types": list(self.matched_edge_types),
            "compartment_compatibility": self.compartment_compatibility,
            "regulation_compatibility": self.regulation_compatibility,
            "normal_incident_compatibility": self.normal_incident_compatibility,
            "projection_confidence": self.projection_confidence,
            "projection_evidence_hash": self.projection_evidence_hash,
            "independent_verifier": self.independent_verifier,
            "review_state": self.review_state,
            "allowed_influences": ["probe_ranking", "probe_selection", "safe_abstention_recommendation"],
            "forbidden_influences": ["ground_truth", "patch_content", "patch_authorization", "count_gate"],
        }
        record["state_hash"] = state_hash(record)
        return record
