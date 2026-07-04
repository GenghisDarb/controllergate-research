from __future__ import annotations

from pathlib import Path
from typing import Any

from .evidence import hash_record, sha256_file


SOURCE_REPO_URL = "https://github.com/akaihola/darker"
SOURCE_COMMIT_SHA = "a2d13656adfaa010fb6c7339087f3347ad2b815a"
RELEVANT_SOURCE_PATHS = [
    "setup.cfg",
    "src/darker/__main__.py",
    "src/darker/main.py",
    "src/darker/git.py",
    "src/darker/command_line.py",
]


def provider_source_checkout_policy() -> dict[str, Any]:
    return {
        "status": "PASS",
        "repo_url": SOURCE_REPO_URL,
        "source_commit_sha": SOURCE_COMMIT_SHA,
        "provider_workspace_only": True,
        "fixed_later_gold_pr_evidence_allowed": False,
        "full_source_tree_copy_to_repo_allowed": False,
        "network_policy": "allowed_for_exact_source_commit_checkout_only",
    }


def source_tree_manifest(source_root: str | Path) -> dict[str, Any]:
    root = Path(source_root)
    records = []
    missing = []
    for rel in RELEVANT_SOURCE_PATHS:
        path = root / rel
        if path.is_file():
            records.append({"path": rel, "sha256": sha256_file(path), "size_bytes": path.stat().st_size})
        else:
            missing.append(rel)
    manifest = {
        "status": "PASS" if not missing else "BLOCK",
        "source_root_recorded": False,
        "relevant_file_count": len(records),
        "records": records,
        "missing_relevant_paths": missing,
        "full_source_tree_copied_to_repo": False,
        "blocker": None if not missing else "provider_source_tree_manifest_failed",
    }
    return {**manifest, "manifest_sha256": hash_record(manifest)}
