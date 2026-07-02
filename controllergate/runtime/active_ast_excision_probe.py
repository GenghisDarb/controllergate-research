from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

from .isolated_repair_sandbox import validate_sandbox_path


def traceback_linked_nodes(source: str) -> list[dict[str, Any]]:
    tree = ast.parse(source)
    nodes: list[dict[str, Any]] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            nodes.append({"name": node.name, "lineno": node.lineno, "node_type": type(node).__name__})
    return sorted(nodes, key=lambda item: (int(item["lineno"]), str(item["name"])))


def plan_excision_probe(source_path: str | Path, source: str, sandbox_path: str | Path, repo_root: str | Path) -> dict[str, Any]:
    validation = validate_sandbox_path(sandbox_path, repo_root)
    nodes = traceback_linked_nodes(source)
    status = "PASS" if validation["status"] == "PASS" and nodes else "BLOCK"
    return {
        "status": status,
        "source_path": str(source_path),
        "candidate_nodes": nodes,
        "sandbox_only": True,
        "real_source_tree_modified": False,
        "repair_authorized_from_probe_alone": False,
        "classification": "inconclusive" if status == "PASS" else "catastrophic_cascade",
        "blocker": None if status == "PASS" else "active_ast_excision_probe_requires_sandbox_and_node",
    }
