from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

from controllergate.core.evidence import hash_record


def extrude_source_tree(candidate_id: str, source_root: Path | None, evidence_hashes: list[str]) -> dict[str, Any]:
    if source_root is None or not source_root.is_dir():
        return {"candidate_id": candidate_id, "status": "BLOCK", "parse_status": "NOT_RUN", "blocker": "verified_candidate_source_tree_not_materialized", "source_file_inventory": [], "module_graph": [], "symbol_definition_index": [], "symbol_reference_index": [], "call_contact_graph": [], "unresolved_dynamic_dispatch_edges": [], "evidence_hashes": evidence_hashes, "tests_only_contact_accepted": False}
    files = sorted(path for path in source_root.rglob("*.py") if ".git" not in path.parts and "tests" not in path.parts)
    definitions = []; references = []; blocked = []
    for path in files:
        try: tree = ast.parse(path.read_text(encoding="utf-8"))
        except (SyntaxError, UnicodeError): blocked.append(path.relative_to(source_root).as_posix()); continue
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)): definitions.append({"path": path.relative_to(source_root).as_posix(), "symbol": node.name, "line": node.lineno})
            elif isinstance(node, ast.Name): references.append({"path": path.relative_to(source_root).as_posix(), "symbol": node.id, "line": node.lineno})
    result = {"candidate_id": candidate_id, "status": "PASS" if files and not blocked else "PARTIAL", "parse_status": "PASS" if files and not blocked else "PARTIAL", "source_file_inventory": [path.relative_to(source_root).as_posix() for path in files], "module_graph": [], "symbol_definition_index": definitions, "symbol_reference_index": references, "call_contact_graph": [], "parse_blocked_files": blocked, "unresolved_dynamic_dispatch_edges": [], "evidence_hashes": evidence_hashes, "tests_only_contact_accepted": False}
    result["analysis_hash"] = hash_record(result); return result
