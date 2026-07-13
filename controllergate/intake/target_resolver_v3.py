from __future__ import annotations

from pathlib import Path
from typing import Any

from .native_target_verifier import verify_native_target


def resolve_target_v3(source_root: Path, *, exact_target: str | None, issue_reproducer: str | None = None, evidence_path: str | None = None) -> dict[str, Any]:
    if issue_reproducer and not exact_target:
        return {"status": "PASS", "lane": "ISSUE_DERIVED_REPRODUCER_LANE", "reproducer": issue_reproducer, "native_target_promoted": False}
    if not exact_target or "::" not in exact_target:
        return {"status": "BLOCK", "blocker": "exact_native_target_required", "native_target_promoted": False}
    path, node = exact_target.split("::", 1)
    result = verify_native_target(source_root, path, node, evidence_path=evidence_path)
    result["lane"] = result.pop("correct_lane")
    result["native_target_promoted"] = result["status"] == "PASS"
    return result
