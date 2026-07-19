#!/usr/bin/env python3
"""Acquire only registered source commits and emit narrow source capsules."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from controllergate.evidence.incident_identity_v2 import canonical_hash
from controllergate.evidence.source_capsule_v1 import build_source_capsule, verify_source_capsule


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in rows), encoding="utf-8", newline="\n")


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n", encoding="utf-8", newline="\n")


def run(argv: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(argv, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace", check=False)
    if result.returncode:
        raise RuntimeError(f"{' '.join(argv)} failed: {result.stderr[-500:]}")
    return result


def acquire(repository: str, commit: str, destination: Path) -> dict:
    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True)
    commands = [
        ["git", "init", "--quiet", str(destination)],
        ["git", "-C", str(destination), "remote", "add", "origin", repository],
        ["git", "-C", str(destination), "-c", "protocol.version=2", "fetch", "--quiet", "--depth=1", "--filter=blob:none", "origin", commit],
    ]
    receipts = []
    for argv in commands:
        result = run(argv)
        receipts.append({
            "argv_hash": hashlib.sha256(json.dumps(argv).encode()).hexdigest(),
            "return_code": result.returncode,
            "stdout_sha256": hashlib.sha256(result.stdout.encode()).hexdigest(),
            "stderr_sha256": hashlib.sha256(result.stderr.encode()).hexdigest(),
        })
    run(["git", "-C", str(destination), "update-ref", "refs/heads/batch100-frozen", "FETCH_HEAD"])
    return {
        "phase": "ACQUISITION_PHASE",
        "network_policy": "bounded_read_only_acquisition",
        "repository": repository,
        "requested_commit": commit,
        "command_receipts": receipts,
        "receipt_hash": canonical_hash(receipts),
        "authority_allowed": "source-object acquisition only",
        "authority_forbidden": ["future commit", "accepted fix", "gold patch", "candidate execution"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contracts", type=Path, default=Path("configs/candidate_execution_contracts_v2.jsonl"))
    parser.add_argument("--incident-identities", type=Path, default=Path("configs/batch100_incident_identity_registry_v2.jsonl"))
    parser.add_argument("--runtime-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()
    contracts = read_jsonl(args.contracts)
    incidents = {row["candidate_id"]: row for row in read_jsonl(args.incident_identities)}
    wanted = set(incidents)
    selected = [row for row in contracts if row["candidate_id"] in wanted]
    if len(selected) != len(wanted):
        raise SystemExit("candidate contract coverage incomplete")
    rows: list[dict] = []
    blockers: list[dict] = []
    acquired_at = datetime.now(timezone.utc).isoformat()
    for contract in selected:
        candidate_id = contract["candidate_id"]
        destination = args.runtime_root / "source-capsules" / candidate_id
        try:
            receipt = acquire(contract["repository"], contract["source_commit"], destination)
            capsule = build_source_capsule(
                candidate_id=candidate_id,
                repository=contract["repository"],
                exact_source_commit=contract["source_commit"],
                repo=destination,
                test_prefixes=contract["target_paths"],
                candidate_contract_hash=contract["contract_hash"],
                issue_identity_hash=incidents[candidate_id]["identity_hash"],
                acquisition_network_receipt=receipt,
                acquired_at=acquired_at,
            ).record()
            errors = verify_source_capsule(capsule)
            if errors:
                blockers.append({"candidate_id": candidate_id, "blockers": errors})
            rows.append(capsule)
        except Exception as exc:  # an exact per-candidate blocker is evidence, not a fabricated capsule
            blockers.append({"candidate_id": candidate_id, "blockers": ["SOURCE_CAPSULE_ACQUISITION_BLOCKED"], "detail": str(exc)})
    write_jsonl(args.output_root / "source_capsule_registry_v1.jsonl", rows)
    covered = {row["candidate_id"] for row in rows}
    audit = {
        "status": "PASS" if len(covered) == len(wanted) and not blockers else "BLOCK",
        "required_candidate_count": len(wanted),
        "capsule_count": len(rows),
        "covered_candidate_ids": sorted(covered),
        "blockers": blockers,
        "source_mutation_count": 0,
        "producer": "scripts/build_batch100_source_capsules.py",
        "execution_depth": "exact Git object and tree identity",
        "semantic_scope": "source custody only",
        "authority_allowed": "source and test identity",
        "authority_forbidden": ["incident materialization", "causal ownership", "patch", "release"],
    }
    write_json(args.output_root / "capsule_source_integrity_audit.json", audit)
    write_json(args.output_root / "capsule_future_commit_exclusion_audit.json", {**audit, "status": "PASS" if all(row["no_future_commit"] for row in rows) else "BLOCK", "check": "no_future_commit"})
    write_json(args.output_root / "capsule_gold_patch_exclusion_audit.json", {**audit, "status": "PASS" if all(row["no_gold_patch"] and row["no_accepted_fix"] for row in rows) else "BLOCK", "check": "no_gold_patch_or_accepted_fix"})
    return 0 if audit["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
