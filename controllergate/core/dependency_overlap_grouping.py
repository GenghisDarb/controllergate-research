from __future__ import annotations

from typing import Any


GROUP_RULES: dict[str, set[str]] = {
    "package_tooling": {"pip", "setuptools", "wheel"},
    "formatter_toolchain": {"black", "pathspec", "regex", "typed-ast", "mypy-extensions", "appdirs"},
    "cli_runtime": {"click", "typing-extensions"},
    "parser_config": {"toml"},
}


def dependency_overlap_groups(packages: list[dict[str, Any]]) -> dict[str, Any]:
    """Group coupled dependencies so routing does not double-count them."""
    package_names = [str(package.get("name", "")).lower() for package in packages if isinstance(package, dict)]
    grouped: list[dict[str, Any]] = []
    assigned: set[str] = set()
    for group_id, members in GROUP_RULES.items():
        present = sorted(name for name in package_names if name in members)
        if present:
            grouped.append(
                {
                    "group_id": group_id,
                    "dependency_names": present,
                    "grouping_basis": "toolchain_role_or_shared_failure_surface",
                    "may_be_weighted_independently": False,
                }
            )
            assigned.update(present)
    ungrouped = sorted(name for name in package_names if name and name not in assigned)
    if ungrouped:
        grouped.append(
            {
                "group_id": "ungrouped_declared_dependencies",
                "dependency_names": ungrouped,
                "grouping_basis": "declared_but_no_known_overlap_group",
                "may_be_weighted_independently": True,
            }
        )
    return {
        "status": "PASS",
        "candidate_id": "darker_issue_112_relative_git_dir",
        "dependency_count": len(package_names),
        "groups": grouped,
        "double_count_detected": False,
        "used_as_repair_evidence": False,
    }


def dependency_overlap_audit(group_record: dict[str, Any]) -> dict[str, Any]:
    groups = group_record.get("groups", [])
    seen: set[str] = set()
    duplicate_names: set[str] = set()
    for group in groups if isinstance(groups, list) else []:
        for name in group.get("dependency_names", []) if isinstance(group, dict) else []:
            if name in seen:
                duplicate_names.add(str(name))
            seen.add(str(name))
    return {
        "status": "PASS" if not duplicate_names and group_record.get("used_as_repair_evidence") is False else "BLOCK",
        "duplicate_dependency_names": sorted(duplicate_names),
        "dependency_overlap_double_count_detected": bool(duplicate_names),
        "dependency_grouping_used_as_repair_evidence": group_record.get("used_as_repair_evidence") is not False,
        "blocker": None
        if not duplicate_names and group_record.get("used_as_repair_evidence") is False
        else "dependency_overlap_double_count_detected",
    }
