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
    "noxfile.py",
]


def sha256_bytes(data: bytes) -> str:
    return sha256(data).hexdigest()


def metadata_hashes(root: str | Path) -> list[dict[str, Any]]:
    root_path = Path(root)
    records: list[dict[str, Any]] = []
    for rel in DEPENDENCY_METADATA_FILES:
        path = root_path / rel
        if path.is_file():
            data = path.read_bytes()
            records.append({"path": rel, "sha256": sha256_bytes(data), "byte_size": len(data)})
    return records


def classify_dependency_precondition(observed_failure: str, declared_ranges: list[str]) -> dict[str, Any]:
    broad_markers = [">=", "*", "any", ""]
    underconstrained = not declared_ranges or any(any(marker in spec for marker in broad_markers) and "==" not in spec for spec in declared_ranges)
    api_mismatch = "unsupported operand type(s) for /: 'tuple' and 'str'" in observed_failure or "dependency API mismatch" in observed_failure
    if api_mismatch:
        classification = "dependency_era_mismatch_candidate"
        blocker = "dependency_api_precondition_unresolved"
    elif underconstrained:
        classification = "dependency_range_underconstrained"
        blocker = "dependency_era_lock_unavailable"
    else:
        classification = "unknown"
        blocker = None
    return {
        "status": "BLOCK" if blocker else "PASS",
        "classification": classification,
        "dependency_range_underconstrained": underconstrained,
        "dependency_api_precondition_unresolved": api_mismatch,
        "prefer_environment_restoration_before_code_repair": True,
        "latest_unrestricted_dependency_resolution_allowed": False,
        "source_patch_authorized": False,
        "blocker": blocker,
    }


def dependency_era_policy() -> dict[str, Any]:
    return {
        "status": "PASS",
        "allowed_resolution_methods": [
            "selected_source_commit_pinned_metadata",
            "selected_source_commit_metadata_with_release_at_or_before_issue_time",
            "manual_git_tracked_decision_time_lock",
            "selected_source_commit_ci_metadata",
            "selected_source_commit_tox_or_nox_metadata",
        ],
        "forbidden_resolution_methods": [
            "latest_unrestricted_pip_resolution",
            "fixed_later_commit_dependency_metadata",
            "pr_patch_dependency_metadata",
            "gold_patch_dependency_metadata",
            "future_tests",
            "hidden_benchmark_state",
        ],
        "patch_before_target_behavior_allowed": False,
    }
