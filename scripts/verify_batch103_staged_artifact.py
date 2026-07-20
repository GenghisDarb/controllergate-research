"""Independently verify Batch103 artifact paths, manifests, and required payload."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path, PurePosixPath


MANIFESTS = ("ARTIFACT_SHA256SUMS.txt", "PORTABLE_ARTIFACT_SHA256SUMS.txt", "SHA256SUMS.txt")
FORBIDDEN = {".zip", ".tar", ".gz", ".pyc", ".pyd", ".so", ".dll"}
REQUIRED = {
    "batch102_official_ingest/ingest_receipts/batch102_official_ingest_receipt.json",
    "batch103_pre_isomorphism_reactome_closure_expected_failure.json",
    "canonical_isomorphism_errata_lock_v3.json",
    "reactome_completion_status_v1.json",
    "reactome_planner_arm_contracts_v1.jsonl",
    "batch103_fresh_execution_origin_audit.json",
    "batch103_outcome_envelope_seal_receipt_v1.json",
    "reactome_planner_gain_metrics_v1.json",
    "batch103_causal_evidence_summary_v1.json",
    "batch103_controller_audit_terminal_records_v1.jsonl",
    "batch103_source_ownership_proof_registry_v1.json",
    "batch103_independent_critic_summary_v1.json",
    "batch103_public_artifact_boundary.json",
    "batch103_official_workflow_execution_receipt.json",
    "governance/controllergate_master_completion_ledger_v2.json",
}


def parse(path: Path) -> tuple[dict[str, str], list[str]]:
    rows = {}
    errors = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        match = re.fullmatch(r"([0-9a-f]{64})  (.+)", line)
        if not match:
            errors.append(f"malformed:{path.name}:{number}")
            continue
        digest, rel = match.groups()
        if rel in rows:
            errors.append(f"duplicate:{path.name}:{rel}")
        rows[rel] = digest
    return rows, errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    files = {path.relative_to(args.root).as_posix(): path for path in args.root.rglob("*") if path.is_file()}
    errors = [f"missing_required:{name}" for name in sorted(REQUIRED - set(files))]
    unsafe = [rel for rel in files if PurePosixPath(rel).is_absolute() or ".." in PurePosixPath(rel).parts or "\\" in rel]
    forbidden = [rel for rel, path in files.items() if path.suffix.lower() in FORBIDDEN or "__pycache__" in PurePosixPath(rel).parts]
    errors.extend(f"unsafe:{rel}" for rel in unsafe)
    errors.extend(f"forbidden:{rel}" for rel in forbidden)
    reports = {}
    for name in MANIFESTS:
        rows, malformed = parse(args.root / name)
        expected = set(files) - (set(MANIFESTS) if name != "SHA256SUMS.txt" else {"SHA256SUMS.txt"})
        missing = sorted(expected - set(rows))
        extra = sorted(set(rows) - expected)
        mismatch = sorted(
            rel for rel, digest in rows.items()
            if rel in files and hashlib.sha256(files[rel].read_bytes()).hexdigest() != digest
        )
        self_entries = [rel for rel in rows if rel == name]
        errors += malformed
        errors += [f"missing:{name}:{rel}" for rel in missing]
        errors += [f"extra:{name}:{rel}" for rel in extra]
        errors += [f"mismatch:{name}:{rel}" for rel in mismatch]
        errors += [f"self:{name}:{rel}" for rel in self_entries]
        reports[name] = {
            "entry_count": len(rows),
            "expected_count": len(expected),
            "missing_count": len(missing),
            "extra_count": len(extra),
            "mismatch_count": len(mismatch),
            "self_entry_count": len(self_entries),
        }
    result = {
        "status": "PASS" if not errors else "BLOCK",
        "file_count": len(files),
        "unsafe_path_count": len(unsafe),
        "forbidden_payload_count": len(forbidden),
        "reports": reports,
        "errors": errors,
        "authority_allowed": "independent Batch103 staged public payload verification",
        "authority_forbidden": ["automatic ingest", "historical rewrite", "patch", "repair count", "release"],
    }
    print(json.dumps(result, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
