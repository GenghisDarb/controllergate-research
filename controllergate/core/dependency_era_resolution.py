from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path
from typing import Any

DEPENDENCY_METADATA_FILES = [
    "pyproject.toml",
    "setup.cfg",
    "setup.py",
    "requirements.txt",
    "requirements-dev.txt",
    "tox.ini",
    "nox.ini",
    "noxfile.py",
    ".github/workflows/ci.yml",
    ".github/workflows/test.yml",
]

FORBIDDEN_DEPENDENCY_SOURCES = [
    "latest_unrestricted_pip_resolution",
    "fixed_later_commit_dependency_metadata",
    "post_issue_dependency_metadata_without_diagnostic_label",
    "pr_patch_dependency_metadata",
    "gold_patch_dependency_metadata",
    "future_tests_or_lock_files",
    "hidden_benchmark_state",
    "unrecorded_package_metadata",
    "undocumented_local_machine_state",
]

ALLOWED_DEPENDENCY_SOURCES = [
    "selected_source_commit_dependency_metadata",
    "selected_source_commit_declared_pins",
    "selected_source_commit_ci_metadata",
    "package_release_at_or_before_issue_created_at_with_recorded_metadata",
    "git_tracked_manual_decision_time_dependency_lock",
    "bounded_pre_issue_source_commit_window",
]


def stable_hash(value: Any) -> str:
    return sha256(json.dumps(value, sort_keys=True, default=str).encode("utf-8")).hexdigest()


def dependency_era_resolution_policy() -> dict[str, Any]:
    return {
        "status": "PASS",
        "allowed_dependency_evidence": ALLOWED_DEPENDENCY_SOURCES,
        "forbidden_dependency_evidence": FORBIDDEN_DEPENDENCY_SOURCES,
        "environment_restoration_precedes_source_patch": True,
        "latest_unrestricted_dependency_resolution_allowed": False,
        "patch_authorized_without_target_intent_alignment": False,
        "blocker_if_unresolved": "dependency_era_lock_unavailable",
    }


def decision_time_dependency_evidence_policy() -> dict[str, Any]:
    return {
        "status": "PASS",
        "release_metadata_required_when_unpinned_versions_are_used": True,
        "release_metadata_must_be_at_or_before_issue_created_at": True,
        "manual_lock_must_be_git_tracked": True,
        "manual_lock_must_be_workflow_visible": True,
        "unrecorded_local_state_allowed": False,
    }


def dependency_resolution_forbidden_sources() -> dict[str, Any]:
    return {
        "status": "PASS",
        "forbidden_sources": FORBIDDEN_DEPENDENCY_SOURCES,
        "blockers": [
            "dependency_resolution_used_future_metadata",
            "dependency_resolution_unrecorded",
            "manual_dependency_lock_uses_future_evidence",
        ],
    }


def inventory_dependency_metadata(root: str | Path) -> list[dict[str, Any]]:
    root_path = Path(root)
    records: list[dict[str, Any]] = []
    for rel in DEPENDENCY_METADATA_FILES:
        path = root_path / rel
        if path.is_file():
            data = path.read_bytes()
            records.append({"path": rel, "sha256": sha256(data).hexdigest(), "byte_size": len(data)})
    return records


def classify_dependency_lock_candidate(
    *,
    declared_ranges: list[str],
    release_metadata_records: list[dict[str, Any]],
    manual_lock_record: dict[str, Any] | None = None,
) -> dict[str, Any]:
    manual_lock_record = manual_lock_record or {}
    underconstrained = not declared_ranges or any((">=" in spec or "*" in spec) and "==" not in spec for spec in declared_ranges)
    manual_lock_valid = bool(manual_lock_record.get("status") == "PASS" and manual_lock_record.get("git_tracked") is True and manual_lock_record.get("workflow_visible") is True)
    release_metadata_recorded = bool(release_metadata_records)
    if manual_lock_valid:
        status = "PASS"
        blocker = None
    elif underconstrained and not release_metadata_recorded:
        status = "BLOCK"
        blocker = "dependency_era_lock_unavailable"
    else:
        status = "BLOCK"
        blocker = "decision_time_dependency_lock_invalid"
    return {
        "status": status,
        "declared_ranges": declared_ranges,
        "dependency_range_underconstrained": underconstrained,
        "release_metadata_recorded": release_metadata_recorded,
        "manual_dependency_lock_used": manual_lock_valid,
        "decision_time_dependency_lock_valid": status == "PASS",
        "blocker": blocker,
        "source_patch_authorized": False,
    }


def manual_dependency_lock_schema_valid(record: dict[str, Any]) -> bool:
    if not isinstance(record, dict):
        return False
    if record.get("candidate_id") not in {"darker_issue_112_relative_git_dir", "darker_issue_112"}:
        return False
    packages = record.get("packages")
    if not isinstance(packages, list) or not packages:
        return False
    for package in packages:
        if not isinstance(package, dict):
            return False
        if not package.get("name") or not package.get("version"):
            return False
        if not package.get("decision_time_safe_evidence"):
            return False
    return True


def target_intent_retry_policy() -> dict[str, Any]:
    return {
        "status": "PASS",
        "positive_indicators_required": True,
        "any_failure_sufficient": False,
        "negative_precondition_indicators_block": True,
        "patch_authorized_without_alignment": False,
    }
