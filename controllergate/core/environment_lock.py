from __future__ import annotations

import hashlib
from pathlib import Path


ENVIRONMENT_LOCK_ANCHORS = [
    "pyproject.toml",
    "setup.py",
    "setup.cfg",
    "requirements.txt",
    "requirements-dev.txt",
    "tox.ini",
    "noxfile.py",
    "Pipfile.lock",
    "poetry.lock",
    "Dockerfile",
]


def source_commit_environment_lock_policy() -> dict[str, object]:
    return {
        "status": "PASS",
        "lock_required_before_replay": True,
        "acceptable_lock_anchors": ENVIRONMENT_LOCK_ANCHORS,
        "undeclared_dependency_install_allowed": False,
        "blockers": [
            "source_commit_environment_lock_missing",
            "source_commit_environment_lock_mismatch",
            "undeclared_dependency_install_requested",
        ],
    }


def environment_lock_hash(paths: list[str]) -> str | None:
    if not paths:
        return None
    digest = hashlib.sha256()
    for value in sorted(paths):
        digest.update(value.encode("utf-8"))
        digest.update(b"\n")
    return digest.hexdigest()


def summarize_source_commit_environment_lock(
    *,
    source_commit_sha: str | None,
    environment_lock_source_paths: list[str],
    seed_present: bool,
) -> dict[str, object]:
    if not seed_present:
        return {
            "status": "PASS",
            "lock_to_source_commit_status": "READY_NO_SEED",
            "source_commit_sha": None,
            "environment_lock_source_paths": [],
            "environment_lock_sha256": None,
            "environment_lock_metadata_absent": False,
            "source_acquisition_allowed": False,
            "blocker": None,
        }
    if not source_commit_sha:
        return {
            "status": "BLOCK",
            "lock_to_source_commit_status": "SOURCE_COMMIT_MISSING",
            "source_commit_sha": None,
            "environment_lock_source_paths": environment_lock_source_paths,
            "environment_lock_sha256": environment_lock_hash(environment_lock_source_paths),
            "environment_lock_metadata_absent": not bool(environment_lock_source_paths),
            "source_acquisition_allowed": False,
            "blocker": "source_commit_environment_lock_missing",
        }
    if not environment_lock_source_paths:
        return {
            "status": "BLOCK",
            "lock_to_source_commit_status": "ENVIRONMENT_LOCK_METADATA_ABSENT",
            "source_commit_sha": source_commit_sha,
            "environment_lock_source_paths": [],
            "environment_lock_sha256": None,
            "environment_lock_metadata_absent": True,
            "source_acquisition_allowed": False,
            "blocker": "source_commit_environment_lock_missing",
        }
    return {
        "status": "PASS",
        "lock_to_source_commit_status": "PASS",
        "source_commit_sha": source_commit_sha,
        "environment_lock_source_paths": environment_lock_source_paths,
        "environment_lock_sha256": environment_lock_hash(environment_lock_source_paths),
        "environment_lock_metadata_absent": False,
        "source_acquisition_allowed": True,
        "blocker": None,
    }


def source_acquisition_allowed(lock_summary: dict[str, object]) -> bool:
    return lock_summary.get("status") == "PASS" and lock_summary.get("source_acquisition_allowed") is True
