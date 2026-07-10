from __future__ import annotations

from controllergate.core.evidence import hash_record

from .types import CouplingEdge, LocalBrotGraph, TotBrotGraph


def build_coupled_tot_brot(graphs: tuple[LocalBrotGraph, ...], orthology: dict[tuple[str, str], dict[str, object]] | None = None) -> TotBrotGraph:
    orthology = orthology or {}
    edges: list[CouplingEdge] = []
    for left, right in zip(graphs, graphs[1:]):
        evidence = orthology.get((left.candidate_id, right.candidate_id), {})
        matched = tuple(str(item) for item in evidence.get("matched_dimensions", ()))
        conflicts = tuple(str(item) for item in evidence.get("conflicting_dimensions", ()))
        transfer = bool(matched) and not conflicts and bool(evidence.get("typed_evidence", False))
        edges.append(CouplingEdge(left.candidate_id, right.candidate_id, str(evidence.get("coupling_type", "proof_path_structure")),
            (hash_record(evidence),), matched + conflicts, matched, conflicts, float(evidence.get("confidence", 0.5)), transfer,
            None if transfer else "typed_evidence_bearing_orthology_not_established", "blocked" if not transfer else "bounded", "PASS"))
    return TotBrotGraph(tuple(graph.candidate_id for graph in graphs), tuple(edges))
