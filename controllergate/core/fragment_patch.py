from __future__ import annotations

import hashlib
import json
from collections import Counter
from typing import Any


FORBIDDEN_PATCH_PREFIXES = (
    "tests/",
    "test/",
    "src/darker/tests/",
    "configs/",
    ".github/",
    "outputs/",
    "scripts/",
    "docs/",
    "controllergate_v1_7_beta/reports/",
)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def stable_hash(value: Any) -> str:
    return sha256_text(json.dumps(value, sort_keys=True, separators=(",", ":"), default=str))


def path_is_allowed_source(path: str, allowed_source_files: set[str]) -> bool:
    normalized = path.replace("\\", "/")
    return (
        normalized.endswith(".py")
        and normalized in allowed_source_files
        and not any(normalized.startswith(prefix) for prefix in FORBIDDEN_PATCH_PREFIXES)
    )


def changed_line_count(diff_text: str) -> int:
    return sum(
        1
        for line in diff_text.splitlines()
        if line.startswith(("+", "-")) and not line.startswith(("+++", "---"))
    )


def audit_fragment(
    fragment: dict[str, Any],
    *,
    allowed_source_files: set[str],
    max_changed_lines: int = 50,
) -> dict[str, Any]:
    target_file = str(fragment.get("target_file", ""))
    diff_hunk = str(fragment.get("diff_hunk", ""))
    line_count = changed_line_count(diff_hunk)
    source_only = path_is_allowed_source(target_file, allowed_source_files)
    non_empty = bool(diff_hunk.strip())
    status = "PASS" if source_only and non_empty and line_count <= max_changed_lines else "BLOCK"
    blocker = None
    if not source_only:
        blocker = "fragment_forbidden_patch_target"
    elif not non_empty:
        blocker = "fragment_empty_diff"
    elif line_count > max_changed_lines:
        blocker = "fragment_line_cap_exceeded"
    return {
        "fragment_id": fragment.get("fragment_id"),
        "candidate_id": fragment.get("candidate_id"),
        "target_file": target_file,
        "source_only": source_only,
        "changed_line_count": line_count,
        "status": status,
        "blocker": blocker,
        "fragment_sha256": sha256_text(diff_hunk) if diff_hunk else None,
    }


def fragments_conflict(fragments: list[dict[str, Any]]) -> bool:
    keys = [
        (
            str(fragment.get("target_file", "")),
            str(fragment.get("target_function_or_class", "")),
            str(fragment.get("context_hash", "")),
        )
        for fragment in fragments
    ]
    return any(count > 1 for count in Counter(keys).values())


def assemble_fragments(
    fragments: list[dict[str, Any]],
    *,
    allowed_source_files: set[str],
    max_fragments: int = 3,
    max_files: int = 3,
    max_changed_lines: int = 50,
    max_functions: int = 3,
) -> dict[str, Any]:
    audits = [
        audit_fragment(fragment, allowed_source_files=allowed_source_files, max_changed_lines=max_changed_lines)
        for fragment in fragments
    ]
    files = {str(fragment.get("target_file", "")) for fragment in fragments}
    functions = {str(fragment.get("target_function_or_class", "")) for fragment in fragments if fragment.get("target_function_or_class")}
    total_changed = sum(int(audit["changed_line_count"]) for audit in audits)
    conflict = fragments_conflict(fragments)
    status = (
        "PASS"
        if fragments
        and len(fragments) <= max_fragments
        and len(files) <= max_files
        and len(functions) <= max_functions
        and total_changed <= max_changed_lines
        and not conflict
        and all(audit["status"] == "PASS" for audit in audits)
        else "BLOCK"
    )
    blocker = None
    if not fragments:
        blocker = "fragment_patch_plan_not_generated"
    elif len(fragments) > max_fragments or len(files) > max_files or len(functions) > max_functions or total_changed > max_changed_lines:
        blocker = "fragment_assembly_cap_exceeded"
    elif conflict:
        blocker = "fragment_assembly_failed"
    elif any(audit["status"] != "PASS" for audit in audits):
        blocker = "assembled_patch_safety_failed"
    diff = "\n".join(str(fragment.get("diff_hunk", "")).rstrip() for fragment in fragments if fragment.get("diff_hunk")).rstrip()
    if diff:
        diff += "\n"
    return {
        "status": status,
        "blocker": blocker,
        "fragment_count": len(fragments),
        "modified_file_count": len(files),
        "modified_function_count": len(functions),
        "changed_line_count": total_changed,
        "conflict_detected": conflict,
        "fragment_audits": audits,
        "assembled_patch": diff if status == "PASS" else "",
        "assembled_patch_sha256": sha256_text(diff) if status == "PASS" else None,
    }


def memory_separation_allowed(*, routing_delta_active: bool, separation_score: float | None, threshold: float = 0.95) -> bool:
    return bool(routing_delta_active and separation_score is not None and separation_score >= threshold)
