"""Full source identities acquired during a declared workflow epoch."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any, Iterable


_SHA40 = re.compile(r"^[0-9a-f]{40}$")


def canonical_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, encoding="utf-8", errors="replace", check=False)
    if result.returncode:
        raise RuntimeError(result.stderr[-1000:])
    return result.stdout.strip()


def build_source_capsule_v2(
    *, candidate_id: str, repository: str, exact_source_commit: str, repo: Path,
    test_prefixes: Iterable[str], issue_cutoff: str, acquisition_broker_receipt: dict[str, Any],
    network_budget: dict[str, Any], tag: str | None = None,
) -> dict[str, Any]:
    resolved = _git(repo, "rev-parse", f"{exact_source_commit}^{{commit}}")
    if resolved != exact_source_commit or not _SHA40.fullmatch(resolved):
        raise ValueError("exact source commit did not resolve byte-for-byte")
    tree = _git(repo, "rev-parse", f"{resolved}^{{tree}}")
    raw = _git(repo, "ls-tree", "-r", resolved)
    inventory = []
    for line in raw.splitlines():
        left, path = line.split("\t", 1)
        mode, kind, object_id = left.split(" ", 2)
        inventory.append({"mode": mode, "kind": kind, "object_id": object_id, "path": path})
    prefixes = tuple(value.rstrip("/") for value in test_prefixes)
    tests = [row for row in inventory if any(row["path"] == value or row["path"].startswith(value + "/") for value in prefixes)]
    submodules = [row for row in inventory if row["mode"] == "160000"]
    row: dict[str, Any] = {
        "capsule_version": "Batch102SourceCapsuleV2", "candidate_id": candidate_id,
        "repository": repository, "full_commit_sha": resolved, "tag": tag, "tree_sha": tree,
        "git_object_inventory_hash": canonical_hash(inventory), "git_object_count": len(inventory),
        "submodule_state": submodules, "version_metadata": {"describe": _git(repo, "describe", "--always", "--dirty=forbidden")},
        "source_manifest_hash": canonical_hash(inventory), "test_node_manifest_hash": canonical_hash(tests),
        "test_node_count": len(tests), "issue_cutoff": issue_cutoff,
        "future_commit_exclusion": True, "gold_patch_exclusion": True, "accepted_fix_exclusion": True,
        "acquisition_broker_receipt": acquisition_broker_receipt, "network_budget": network_budget,
        "authority_allowed": "source and test custody for the current execution epoch",
        "authority_forbidden": ["incident claim", "causal ownership", "patch", "repair count", "release promotion"],
    }
    row["source_capsule_hash"] = canonical_hash(row)
    return row


def verify_source_capsule_v2(row: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    if row.get("capsule_version") != "Batch102SourceCapsuleV2": blockers.append("capsule_version_mismatch")
    if not _SHA40.fullmatch(str(row.get("full_commit_sha", ""))): blockers.append("full_commit_sha_invalid")
    if not row.get("tree_sha") or not row.get("git_object_inventory_hash"): blockers.append("source_identity_incomplete")
    if not row.get("acquisition_broker_receipt", {}).get("operation_id"): blockers.append("acquisition_broker_receipt_missing")
    for field in ("future_commit_exclusion", "gold_patch_exclusion", "accepted_fix_exclusion"):
        if row.get(field) is not True: blockers.append(field + "_failed")
    expected = canonical_hash({key: value for key, value in row.items() if key != "source_capsule_hash"})
    if row.get("source_capsule_hash") != expected: blockers.append("source_capsule_hash_mismatch")
    return blockers
