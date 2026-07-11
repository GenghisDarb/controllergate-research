from __future__ import annotations

from pathlib import Path
from typing import Any

from controllergate.core.evidence import hash_record, sha256_file


FORBIDDEN_PARTS = {"tests", "test", "fixtures", ".github", "workflows"}


def verify_patch_plan(plan: dict[str, Any], *, source_root: str | Path, candidate_id: str, candidate_sha: str) -> dict[str, Any]:
    root = Path(source_root).resolve()
    unsigned = {key: value for key, value in plan.items() if key != "plan_hash"}
    if plan.get("plan_hash") != hash_record(unsigned):
        return {"status": "BLOCK", "blocker": "patch_plan_hash_invalid"}
    if plan.get("candidate_id") != candidate_id or plan.get("candidate_sha") != candidate_sha:
        return {"status": "BLOCK", "blocker": "patch_plan_candidate_mismatch"}
    operations = list(plan.get("operations") or [])
    if not operations:
        return {"status": "BLOCK", "blocker": "patch_plan_operations_missing"}
    for operation in operations:
        rel = Path(str(operation.get("path", "")))
        target = (root / rel).resolve()
        if root not in target.parents or any(part in FORBIDDEN_PARTS for part in rel.parts):
            return {"status": "BLOCK", "blocker": "patch_plan_path_forbidden"}
        if not target.is_file() or sha256_file(target) != operation.get("precondition_sha256"):
            return {"status": "BLOCK", "blocker": "patch_plan_precondition_mismatch"}
        if operation.get("operation") not in {"replace_text", "replace_ast_span"}:
            return {"status": "BLOCK", "blocker": "patch_plan_operation_forbidden"}
    return {"status": "PASS", "operation_count": len(operations)}


def execute_patch_plan(plan: dict[str, Any], *, source_root: str | Path, candidate_id: str, candidate_sha: str) -> dict[str, Any]:
    verified = verify_patch_plan(plan, source_root=source_root, candidate_id=candidate_id, candidate_sha=candidate_sha)
    if verified["status"] != "PASS":
        return verified
    root = Path(source_root).resolve()
    changed: list[str] = []
    for operation in plan["operations"]:
        target = root / operation["path"]
        text = target.read_text(encoding="utf-8")
        before = str(operation["before"])
        if text.count(before) != 1:
            return {"status": "BLOCK", "blocker": "patch_plan_match_not_unique", "path": operation["path"]}
        target.write_text(text.replace(before, str(operation["after"]), 1), encoding="utf-8", newline="\n")
        changed.append(str(operation["path"]))
    return {"status": "PASS", "changed_files": sorted(changed), "plan_hash": plan["plan_hash"]}
