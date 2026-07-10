from __future__ import annotations

from .failure_family import FailureFamilyEdge, FailureFamilyNode


class FailureFamilyGraph:
    def __init__(self) -> None:
        self.nodes: dict[str, FailureFamilyNode] = {}
        self.edges: list[FailureFamilyEdge] = []

    def add(self, node: FailureFamilyNode, evidence_hash: str) -> None:
        if node.family_id in self.nodes:
            raise ValueError("duplicate family_id")
        if node.depth < 0:
            raise ValueError("negative depth")
        if node.parent_family_id is not None:
            parent = self.nodes.get(node.parent_family_id)
            if parent is None or node.depth != parent.depth + 1:
                raise ValueError("invalid family ancestry")
            self.edges.append(FailureFamilyEdge(parent.family_id, node.family_id, evidence_hash))
        elif node.depth != 0:
            raise ValueError("root depth must be zero")
        self.nodes[node.family_id] = node

    @property
    def max_depth(self) -> int:
        return max((node.depth for node in self.nodes.values()), default=-1)

    def as_dict(self):
        return {"nodes": [node.as_dict() for node in self.nodes.values()], "edges": [edge.as_dict() for edge in self.edges], "maximum_depth": self.max_depth}
