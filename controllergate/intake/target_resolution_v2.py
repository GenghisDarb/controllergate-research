from __future__ import annotations

from pathlib import Path
from typing import Any

from controllergate.core.evidence import hash_record
from controllergate.intake.target_resolver import resolve_target


def resolve_target_v2(source_root: Path, evidence_text: str, candidate_sha: str) -> dict[str, Any]:
    before = sorted(path.relative_to(source_root).as_posix() for path in source_root.rglob("*.py") if "test" in path.name.lower())
    result = resolve_target(source_root, evidence_text, candidate_sha)
    attempts = [
        {"method": "issue_exact_node", "executed": True},
        {"method": "traceback_or_issue_file", "executed": result.get("source_evidence") != "issue_node"},
        {"method": "bounded_source_symbol_search", "executed": result.get("status") != "PASS" or result.get("confidence_class") == "source_verified_symbol_to_test_target"},
    ]
    record = {
        **result,
        "attempts": attempts,
        "candidate_test_file_count": len(before),
        "target_exists": bool(result.get("status") == "PASS" and (source_root / str(result.get("target_file", ""))).is_file()),
        "source_tree_only": True,
    }
    if not record["target_exists"]:
        record["status"] = "BLOCK"
        record.setdefault("blocker", "source_verified_native_target_unresolved")
    record["resolution_hash"] = hash_record(record)
    return record
