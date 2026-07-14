from __future__ import annotations

from pathlib import Path

from .provider_dependency_graph import graph_from_wheels


def resolve_provider(wheel_dir: Path) -> dict[str, object]:
    graph = graph_from_wheels(wheel_dir)
    return {"state": graph["state"], "graph": graph,
            "exact_blocker": None if not graph["missing_runtime_dependencies"] else "provider_transitive_dependency_closure_incomplete"}
