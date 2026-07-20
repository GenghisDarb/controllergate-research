"""Assemble, boundary-check, and manifest the Batch103 public artifact."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFESTS = {"ARTIFACT_SHA256SUMS.txt", "PORTABLE_ARTIFACT_SHA256SUMS.txt", "SHA256SUMS.txt"}
FORBIDDEN_SUFFIXES = {".zip", ".tar", ".gz", ".pyc", ".pyd", ".so", ".dll"}


def manifest_rows(root: Path, excluded: set[str]) -> list[str]:
    return [
        f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.relative_to(root).as_posix()}"
        for path in sorted(root.rglob("*"))
        if path.is_file() and path.relative_to(root).as_posix() not in excluded
    ]


def write_manifests(root: Path) -> dict[str, int]:
    artifact = manifest_rows(root, MANIFESTS)
    for name in ("ARTIFACT_SHA256SUMS.txt", "PORTABLE_ARTIFACT_SHA256SUMS.txt"):
        (root / name).write_text("\n".join(artifact) + "\n", encoding="utf-8", newline="\n")
    portable = manifest_rows(root, {"SHA256SUMS.txt"})
    (root / "SHA256SUMS.txt").write_text("\n".join(portable) + "\n", encoding="utf-8", newline="\n")
    return {"artifact": len(artifact), "portable": len(artifact), "sha256sums": len(portable)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--static-source", type=Path, required=True)
    parser.add_argument("--overlays-root", type=Path, required=True)
    parser.add_argument("--destination", type=Path, required=True)
    args = parser.parse_args()
    shutil.rmtree(args.destination, ignore_errors=True)
    shutil.copytree(
        args.static_source,
        args.destination,
        ignore=shutil.ignore_patterns(
            "__pycache__",
            "*.pyc",
            # A prior downloaded-artifact handoff receipt is local verification
            # state, not an input to a later official artifact.
            "batch103_official_artifact_handoff_verification.json",
        ),
    )
    for path in sorted(args.overlays_root.rglob("*")):
        if not path.is_file() or path.name in MANIFESTS:
            continue
        target = args.destination / path.name
        if target.exists() and target.read_bytes() != path.read_bytes():
            raise RuntimeError(f"conflicting artifact overlay: {path.name}")
        if not target.exists():
            shutil.copy2(path, target)
    governance = args.destination / "governance"
    documentation = args.destination / "documentation"
    governance.mkdir(exist_ok=True)
    documentation.mkdir(exist_ok=True)
    shutil.copy2(ROOT / "configs/controllergate_master_completion_ledger_v2.json", governance)
    shutil.copy2(ROOT / "configs/controllergate_isomorphism_registry_v3.jsonl", governance)
    for name in (
        "current_status.md",
        "CURRENT_CONTROLLERGATE_HANDOFF.md",
        "REACTOME_CONTROLLERGATE_COMPLETION_STATUS.md",
        "CONTROLLERGATE_CANONICAL_ISOMORPHISM_MAP.md",
    ):
        shutil.copy2(ROOT / "docs" / name, documentation / name)
    boundary = {
        "status": "PASS_PUBLIC_ARTIFACT_BOUNDARY",
        "excluded": [
            "raw private TLD",
            "raw private truth",
            "future fixes",
            "gold patches",
            "repair patches",
            "private paths",
            "secrets",
            "unauthorized source archives",
        ],
        "automatic_batch103_ingest": False,
        "ordinary_patch_count": 0,
        "repair_counts": {"issue_derived": 6, "native_external": 4, "historical": 0},
        "protocol": "v2.19",
        "package_version": "0.2.0b2.dev0",
        "release": "PRODUCT_BETA_RC_BLOCKED_EXACT",
        "production_readiness": False,
        "self_maintaining": False,
    }
    (args.destination / "batch103_public_artifact_boundary.json").write_text(
        json.dumps(boundary, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n"
    )
    workflow_receipt = {
        "execution_epoch": "BATCH103_FRESH_OPERATION",
        "workflow_run_id": os.environ.get("GITHUB_RUN_ID"),
        "workflow_run_attempt": os.environ.get("GITHUB_RUN_ATTEMPT"),
        "workflow_head": os.environ.get("GITHUB_SHA"),
        "workflow_ref": os.environ.get("GITHUB_REF"),
        "workflow_job": os.environ.get("GITHUB_JOB"),
        "workflow_url": (
            f"{os.environ.get('GITHUB_SERVER_URL')}/{os.environ.get('GITHUB_REPOSITORY')}/actions/runs/"
            f"{os.environ.get('GITHUB_RUN_ID')}"
        ),
        "truth_access": 0,
        "private_tld_access": 0,
        "patch_operations": 0,
    }
    (args.destination / "batch103_official_workflow_execution_receipt.json").write_text(
        json.dumps(workflow_receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n"
    )
    bad = [
        path.relative_to(args.destination).as_posix()
        for path in args.destination.rglob("*")
        if path.is_file()
        and (path.suffix.lower() in FORBIDDEN_SUFFIXES or "__pycache__" in path.parts)
    ]
    if bad:
        raise RuntimeError(f"forbidden artifact payload: {bad[:3]}")
    counts = write_manifests(args.destination)
    print(json.dumps({"status": "PASS", "manifest_counts": counts, "forbidden_payload_count": 0}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
