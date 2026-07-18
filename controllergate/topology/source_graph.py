from __future__ import annotations

import ast
import hashlib
from pathlib import Path
from typing import Iterable

from controllergate.state.integrity import canonical_hash


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compile_python_source_graph(root: Path, tracked_paths: Iterable[str]) -> dict[str, object]:
    """Compile a receipt-bound static graph from an acquired source tree.

    Syntax failures remain explicit nodes.  They never disappear from the
    denominator and they never imply causal authority.
    """
    nodes: list[dict[str, object]] = []
    edges: list[dict[str, object]] = []
    failures: list[dict[str, str]] = []
    for relative in sorted(set(tracked_paths)):
        path = root / relative
        if not path.is_file():
            failures.append({"path": relative, "reason": "tracked_path_missing"})
            continue
        file_hash = _sha(path)
        file_id = f"file:{relative}"
        nodes.append({"node_id": file_id, "node_class": "SOURCE_FILE", "path": relative, "sha256": file_hash})
        if path.suffix != ".py":
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"), filename=relative)
        except SyntaxError as exc:
            failures.append({"path": relative, "reason": f"syntax_error:{exc.lineno}"})
            continue
        module_id = f"module:{relative}"
        nodes.append({"node_id": module_id, "node_class": "MODULE", "path": relative, "sha256": file_hash})
        edges.append({"source": file_id, "target": module_id, "edge_class": "PARSES_AS", "evidence_sha256": file_hash})
        for item in ast.walk(tree):
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                kind = "CLASS" if isinstance(item, ast.ClassDef) else "FUNCTION"
                node_id = f"{kind.lower()}:{relative}:{item.name}:{item.lineno}"
                nodes.append({"node_id": node_id, "node_class": kind, "path": relative, "name": item.name, "line": item.lineno, "sha256": file_hash})
                edges.append({"source": module_id, "target": node_id, "edge_class": "DECLARES", "evidence_sha256": file_hash})
            elif isinstance(item, (ast.Import, ast.ImportFrom)):
                names = [alias.name for alias in item.names]
                prefix = item.module if isinstance(item, ast.ImportFrom) else None
                for name in names:
                    imported = f"{prefix}.{name}" if prefix else name
                    target = f"import:{imported}"
                    nodes.append({"node_id": target, "node_class": "IMPORT", "name": imported})
                    edges.append({"source": module_id, "target": target, "edge_class": "IMPORTS", "evidence_sha256": file_hash, "line": getattr(item, "lineno", None)})
            elif isinstance(item, ast.Call):
                target_name = None
                if isinstance(item.func, ast.Name):
                    target_name = item.func.id
                elif isinstance(item.func, ast.Attribute):
                    target_name = item.func.attr
                if target_name:
                    target = f"call:{target_name}"
                    nodes.append({"node_id": target, "node_class": "CALL_TARGET", "name": target_name})
                    edges.append({"source": module_id, "target": target, "edge_class": "CALLS", "evidence_sha256": file_hash, "line": getattr(item, "lineno", None)})
    unique_nodes = {str(row["node_id"]): row for row in nodes}
    record = {"nodes": [unique_nodes[key] for key in sorted(unique_nodes)], "edges": sorted(edges, key=lambda row: (str(row["source"]), str(row["target"]), str(row["edge_class"]), int(row.get("line") or 0))), "parse_failures": failures, "tracked_path_count": len(set(tracked_paths))}
    return {**record, "graph_hash": canonical_hash(record), "authority_allowed": "topology hypothesis generation", "authority_forbidden": ["terminal class", "repair", "count"]}
