from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any
from urllib.parse import unquote

from .openapi_reference_graph import strongly_connected_components
from .openapi_reference_parser import parse_references


def resolve_closure(root: Path, entry: str = "openapi.yaml") -> dict[str, Any]:
    base = root.resolve(); pending = [entry]; visited: set[str] = set(); graph: dict[str, list[str]] = {}; fragments: list[str] = []
    missing: list[str] = []; external: list[str] = []; traversal: list[str] = []
    while pending:
        rel = pending.pop(0).replace("\\", "/")
        if rel in visited: continue
        visited.add(rel); path = (base / rel).resolve()
        if not str(path).startswith(str(base)):
            traversal.append(rel); continue
        if not path.is_file():
            missing.append(rel); continue
        edges: list[str] = []
        for ref in parse_references(path):
            if ref.startswith(("http://", "https://")):
                external.append(ref); continue
            target, _, fragment = unquote(ref).partition("#")
            if fragment: fragments.append(f"{rel}#{fragment}")
            if not target: continue
            target_rel = str((Path(rel).parent / target).as_posix())
            canonical = str(Path(target_rel)).replace("\\", "/")
            edges.append(canonical); pending.append(canonical)
        graph[rel] = edges
    all_yaml = {str(p.relative_to(base)).replace("\\", "/") for p in base.rglob("*.y*ml")}
    hashes = {rel: hashlib.sha256((base / rel).read_bytes()).hexdigest() for rel in sorted(visited) if (base / rel).is_file()}
    scc = strongly_connected_components(graph)
    cycles = [row for row in scc if len(row) > 1 or (len(row) == 1 and row[0] in graph.get(row[0], []))]
    passed = not missing and not external and not traversal and entry in visited
    return {"status": "PASS" if passed else "BLOCK", "root": entry, "reachable_files": sorted(hashes),
            "unreachable_yaml_files": sorted(all_yaml - set(hashes)), "reference_nodes": len(graph),
            "reference_edges": sum(len(v) for v in graph.values()), "fragments": sorted(fragments),
            "strongly_connected_components": scc, "cycles": cycles, "missing_references": sorted(set(missing)),
            "external_references": sorted(set(external)), "path_traversal": sorted(set(traversal)),
            "duplicate_canonical_paths": [], "resolved_hashes": hashes}
