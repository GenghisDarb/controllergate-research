from __future__ import annotations

from typing import Any

from .evidence import hash_record


def build_command_evidence_graph(
    *, candidate_sha: str, sources: list[dict[str, Any]], commands: list[dict[str, Any]]
) -> dict[str, Any]:
    ordered_sources = sorted(sources, key=lambda item: (str(item.get("path", "")), str(item.get("sha256", ""))))
    ordered_commands = sorted(
        commands,
        key=lambda item: (str(item.get("source_path", "")), tuple(item.get("argv") or [])),
    )
    graph = {
        "candidate_sha": candidate_sha,
        "source_nodes": ordered_sources,
        "command_nodes": ordered_commands,
        "edges": [
            {"source_path": item.get("source_path"), "argv": item.get("argv"), "relation": "declares_or_corroborates"}
            for item in ordered_commands
        ],
        "forbidden_sources_used": [],
    }
    graph["graph_hash"] = hash_record(graph)
    return graph


def provenance_matches(graph: dict[str, Any], candidate_sha: str) -> bool:
    return graph.get("candidate_sha") == candidate_sha and not graph.get("forbidden_sources_used")
