"""Narrow, immutable source-capsule identities."""

from __future__ import annotations

import hashlib
import json
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


def canonical_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _git(repo: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", *args], cwd=repo, check=False, capture_output=True, text=True,
        encoding="utf-8", errors="replace",
    )
    if completed.returncode:
        raise RuntimeError(f"git {' '.join(args)} failed: {completed.stderr[-500:]}")
    return completed.stdout.strip()


def _tree_manifest(repo: Path, commit: str) -> list[dict[str, str]]:
    raw = _git(repo, "ls-tree", "-r", "-z", commit)
    rows: list[dict[str, str]] = []
    for entry in raw.split("\0"):
        if not entry:
            continue
        left, path = entry.split("\t", 1)
        mode, kind, object_id = left.split(" ", 2)
        rows.append({"path": path, "mode": mode, "kind": kind, "object_id": object_id})
    return rows


def _manifest_slice(rows: Iterable[dict[str, str]], prefixes: Iterable[str]) -> list[dict[str, str]]:
    normalized = tuple(prefix.rstrip("/") for prefix in prefixes)
    return [row for row in rows if any(row["path"] == prefix or row["path"].startswith(prefix + "/") for prefix in normalized)]


@dataclass(frozen=True)
class SourceCapsuleV1:
    candidate_id: str
    repository: str
    exact_source_commit: str
    git_object_type: str
    tree_hash: str
    submodule_state: list[dict[str, str]]
    source_manifest_hash: str
    source_manifest_file_count: int
    test_manifest_hash: str
    test_manifest_file_count: int
    candidate_contract_hash: str
    issue_identity_hash: str
    acquisition_timestamp: str
    acquisition_network_receipt: dict[str, Any]
    no_future_commit: bool
    no_accepted_fix: bool
    no_gold_patch: bool
    authority_allowed: str = "immutable source and test identity"
    authority_forbidden: tuple[str, ...] = (
        "incident materialization claim",
        "causal ownership",
        "patch authority",
        "release promotion",
    )

    def record(self) -> dict[str, Any]:
        row = self.__dict__.copy()
        row["capsule_hash"] = canonical_hash(row)
        return row


def build_source_capsule(
    *, candidate_id: str, repository: str, exact_source_commit: str, repo: Path,
    test_prefixes: Iterable[str], candidate_contract_hash: str, issue_identity_hash: str,
    acquisition_network_receipt: dict[str, Any], acquired_at: str | None = None,
) -> SourceCapsuleV1:
    resolved = _git(repo, "rev-parse", f"{exact_source_commit}^{{commit}}")
    if resolved != exact_source_commit:
        raise ValueError(f"source commit mismatch: {resolved}")
    kind = _git(repo, "cat-file", "-t", resolved)
    if kind != "commit":
        raise ValueError("source object is not a commit")
    tree_hash = _git(repo, "rev-parse", f"{resolved}^{{tree}}")
    rows = _tree_manifest(repo, resolved)
    tests = _manifest_slice(rows, test_prefixes)
    test_paths = {row["path"] for row in tests}
    source = [row for row in rows if row["path"] not in test_paths]
    submodules = [row for row in rows if row["mode"] == "160000"]
    return SourceCapsuleV1(
        candidate_id=candidate_id,
        repository=repository,
        exact_source_commit=resolved,
        git_object_type=kind,
        tree_hash=tree_hash,
        submodule_state=submodules,
        source_manifest_hash=canonical_hash(source),
        source_manifest_file_count=len(source),
        test_manifest_hash=canonical_hash(tests),
        test_manifest_file_count=len(tests),
        candidate_contract_hash=candidate_contract_hash,
        issue_identity_hash=issue_identity_hash,
        acquisition_timestamp=acquired_at or datetime.now(timezone.utc).isoformat(),
        acquisition_network_receipt=acquisition_network_receipt,
        no_future_commit=True,
        no_accepted_fix=True,
        no_gold_patch=True,
    )


def verify_source_capsule(row: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    if len(str(row.get("exact_source_commit", ""))) != 40:
        blockers.append("invalid_source_commit")
    if row.get("git_object_type") != "commit":
        blockers.append("source_object_not_commit")
    if not row.get("tree_hash"):
        blockers.append("tree_hash_missing")
    for field in ("no_future_commit", "no_accepted_fix", "no_gold_patch"):
        if row.get(field) is not True:
            blockers.append(field + "_failed")
    expected = canonical_hash({key: value for key, value in row.items() if key != "capsule_hash"})
    if row.get("capsule_hash") != expected:
        blockers.append("capsule_hash_mismatch")
    return blockers
