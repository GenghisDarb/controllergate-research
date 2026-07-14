from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def verify_collection(path: str | Path, requested_node: str, *, return_code: int, source_hash_before: str, source_hash_after: str, test_hash_before: str, test_hash_after: str) -> dict[str, Any]:
    target = Path(path)
    if return_code != 0 or not target.is_file():
        return {"status": "BLOCK", "blocker": "structured_collection_missing_or_failed"}
    try:
        payload = json.loads(target.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return {"status": "BLOCK", "blocker": "structured_collection_payload_invalid"}
    nodes = payload.get("nodes", [])
    errors = []
    if payload.get("internal_error"):
        errors.append("collection_internal_error")
    if requested_node not in nodes:
        errors.append("requested_node_missing")
    if source_hash_before != source_hash_after or test_hash_before != test_hash_after:
        errors.append("collection_mutated_source_or_tests")
    return {"status": "PASS" if not errors else "BLOCK", "requested_node": requested_node, "node_count": len(nodes), "errors": errors}
