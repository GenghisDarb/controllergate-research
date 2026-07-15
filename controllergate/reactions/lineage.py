from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Iterable

from .stable_identity import stable_hash


@dataclass(frozen=True)
class LineageNode:
    node_id: str
    node_type: str
    parent_ids: tuple[str, ...]
    creation_event: str
    source_compartment: str
    destination_compartment: str
    evidence_grade: str
    author: str
    reviewer: str
    revision_reason: str
    retired: bool = False

    @property
    def node_hash(self) -> str:
        return stable_hash(asdict(self))


class LineageGraph:
    def __init__(self) -> None:
        self.nodes: dict[str, LineageNode] = {}

    def add(self, node: LineageNode) -> None:
        if node.node_id in self.nodes:
            raise ValueError("lineage node already exists")
        if any(parent not in self.nodes for parent in node.parent_ids):
            raise ValueError("lineage parent missing")
        parent_types = {self.nodes[parent].node_type for parent in node.parent_ids}
        if node.node_type == "decision" and {"decision_time_evidence", "sealed_truth"} <= parent_types:
            raise ValueError("decision-time and sealed-truth parents cannot be combined")
        self.nodes[node.node_id] = node

    def verify(self) -> dict[str, object]:
        missing = [(node.node_id, parent) for node in self.nodes.values() for parent in node.parent_ids if parent not in self.nodes]
        return {"status": "PASS" if not missing else "BLOCK", "missing_parents": missing,
                "node_count": len(self.nodes), "graph_hash": stable_hash([asdict(node) for node in self.nodes.values()])}


def inherited_state_handover(records: Iterable[dict[str, object]]) -> dict[str, object]:
    retained = []
    degraded = []
    for record in records:
        if record.get("type") in {"protocol", "schema", "verified_component", "claim_boundary", "proof_count_authority", "safety_invariant"}:
            retained.append(record)
        else:
            degraded.append(record)
    prepared = stable_hash({"retained": retained, "degraded": degraded})
    return {"prepared_state": "AUTHORITY_HANDOVER_PREPARED", "committed_state": "AUTHORITY_HANDOVER_COMMITTED",
            "retained": retained, "degraded_or_quarantined": degraded, "handover_hash": prepared}
