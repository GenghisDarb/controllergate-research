from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class DependencyGraph:
    nodes: dict[str, dict[str, object]] = field(default_factory=dict)
    edges: list[dict[str, object]] = field(default_factory=list)

    def add_node(self, name: str, **metadata: object) -> None: self.nodes[name] = {"name": name, **metadata}
    def add_edge(self, parent: str, child: str, requirement: str, dependency_class: str) -> None: self.edges.append({"parent": parent, "child": child, "requirement": requirement, "dependency_class": dependency_class})
    def as_dict(self) -> dict[str, object]: return {"nodes": list(self.nodes.values()), "edges": self.edges, "node_count": len(self.nodes), "edge_count": len(self.edges)}
