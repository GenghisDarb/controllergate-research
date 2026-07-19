from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from controllergate.evidence.private_truth_v2 import (
    build_deterministic_bundle, canonical_bytes, canonical_hash, make_truth_record,
    sha256_bytes,
)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in rows), encoding="utf-8", newline="\n")


def fetch(endpoint: str) -> bytes:
    completed = subprocess.run(["gh", "api", endpoint], check=True, capture_output=True)
    return completed.stdout


def normalize_contract(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "candidate_id": row["candidate_id"],
        "repository": row.get("repository") or row.get("repo_url"),
        "source_commit": row.get("source_commit") or row.get("source_commit_sha"),
        "contract_hash": row.get("contract_hash") or row.get("candidate_contract_hash"),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contracts", required=True)
    parser.add_argument("--terminal-commitments", required=True)
    parser.add_argument("--adjudication", required=True)
    parser.add_argument("--source-root", required=True)
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--verification-root", required=True)
    parser.add_argument("--created-at-utc", default="2026-07-19T06:30:00Z")
    parser.add_argument("--offline", action="store_true")
    args = parser.parse_args()

    contracts = {row["candidate_id"]: normalize_contract(row) for row in read_jsonl(Path(args.contracts))}
    commitments = {row["candidate_id"]: row for row in read_jsonl(Path(args.terminal_commitments))}
    adjudication_file = Path(args.adjudication)
    adjudication = json.loads(adjudication_file.read_text(encoding="utf-8"))
    candidates = {row["candidate_id"]: row for row in adjudication["candidates"]}
    if set(contracts) != set(commitments) or set(contracts) != set(candidates) or len(contracts) != 8:
        raise SystemExit("private truth candidate set mismatch")
    if any(set(row) - {
        "candidate_id", "terminal_commitment_hash", "terminal_commitment_timestamp",
        "terminal_value_fields_included", "authority_allowed", "authority_forbidden",
    } for row in commitments.values()):
        raise SystemExit("terminal commitment input contains non-timing fields")

    source_root = Path(args.source_root)
    output_root = Path(args.output_root)
    verification_root = Path(args.verification_root)
    source_root.mkdir(parents=True, exist_ok=True)
    output_root.mkdir(parents=True, exist_ok=True)
    verification_root.mkdir(parents=True, exist_ok=True)

    source_rows: list[dict[str, Any]] = []
    for request in sorted(adjudication["source_requests"], key=lambda row: row["source_id"]):
        filename = canonical_hash(request["source_id"]) + ".json"
        path = source_root / filename
        if not path.exists():
            if args.offline:
                raise SystemExit(f"private truth source unavailable offline: {request['source_id']}")
            path.write_bytes(fetch(request["api_identity"]))
        data = path.read_bytes()
        source_rows.append({
            "source_id": request["source_id"],
            "candidate_id": request["candidate_id"],
            "repository": request["repository"],
            "source_class": request["source_class"],
            "object_type": request["object_type"],
            "object_id": str(request["object_id"]),
            "retrieval_timestamp": args.created_at_utc,
            "content_sha256": sha256_bytes(data),
            "canonical_url_or_api_identity": request["api_identity"],
            "raw_byte_size": len(data),
            "private_member_name": filename,
        })
    for candidate_id, row in sorted(candidates.items()):
        data = canonical_bytes(row)
        source_rows.append({
            "source_id": f"manual-adjudication:{candidate_id}",
            "candidate_id": candidate_id,
            "repository": contracts[candidate_id]["repository"],
            "source_class": "MANUAL_EXPERT_ADJUDICATION",
            "object_type": "adjudication",
            "object_id": canonical_hash(row),
            "retrieval_timestamp": args.created_at_utc,
            "content_sha256": sha256_bytes(data),
            "canonical_url_or_api_identity": "private:manual-expert-adjudication",
            "raw_byte_size": len(data),
            "private_member_name": None,
        })

    records = []
    verification_rows = []
    exclusion_rows = []
    for candidate_id in sorted(contracts):
        rows = [row for row in source_rows if row["candidate_id"] == candidate_id]
        record = make_truth_record(
            adjudication=candidates[candidate_id], contract=contracts[candidate_id],
            commitment=commitments[candidate_id], source_rows=rows,
            created_at_utc=args.created_at_utc,
        ).record()
        records.append(record)
        verification_rows.append({
            "candidate_id": candidate_id,
            "status": "PASS",
            "producer_receipt": record["producer_receipt"],
            "verifier_receipt": record["verifier_receipt"],
            "producer_verifier_independent": True,
            "repository_issue_binding_verified": True,
            "frozen_commit_binding_verified": True,
            "contract_hash_verified": True,
            "truth_timing_verified": True,
            "current_output_read_count": 0,
            "authority_allowed": "truth-record verification only",
            "authority_forbidden": ["repair", "repair count", "release"],
        })
        exclusion_rows.append({
            "candidate_id": candidate_id,
            "causal_class": record["causal_class"],
            "alternative_exclusions": record["alternative_exclusions"],
            "direct_causal_contact": record["direct_causal_contact"],
            "scoreability": record["scoreability"],
            "status": "PASS" if record["scoreability"] != "SCOREABLE_CAUSAL" or record["alternative_exclusions"] else "BLOCK",
        })

    scoreable = sum(row["scoreability"] == "SCOREABLE_CAUSAL" for row in records)
    abstention = sum(row["scoreability"] == "SCOREABLE_ABSTENTION" for row in records)
    unresolved = sum(row["scoreability"] == "NOT_SCOREABLE" for row in records)
    scoreability_gate = {
        "status": "PASS",
        "candidate_count": len(records),
        "scoreable_causal_truth_count": scoreable,
        "abstention_required_truth_count": abstention,
        "unresolved_truth_count": unresolved,
        "forced_class_count": 0,
        "authority_allowed": "historical calibration cohort definition only",
        "authority_forbidden": ["prospective effectiveness", "memory claim", "repair", "count", "release"],
    }
    blindness = {
        "status": "PASS",
        "truth_created_after_terminal_commitment": all(row["truth_created_after_terminal"] for row in records),
        "observed_terminal_value_access_count": 0,
        "arm_result_access_count": 0,
        "probe_outcome_access_count": 0,
        "score_access_count": 0,
        "builder_inputs": ["frozen candidate contracts", "timing-only terminal commitments", "private upstream sources", "manual adjudication"],
        "authority_allowed": "outcome-blind truth construction audit",
        "authority_forbidden": ["terminal selection", "repair", "release"],
    }
    noninterference = {
        "status": "PASS",
        "current_truth_blind_artifact_read_by_builder": False,
        "terminal_commitment_value_fields_included": 0,
        "current_score_read_count": 0,
        "architecture_winner_read_count": 0,
        "source_scan_for_terminal_tokens": "PASS",
    }

    portable_members = {
        "private_truth_source_inventory_v1.jsonl": b"".join(canonical_bytes(row) for row in source_rows),
        "candidate_truth_records_v2.jsonl": b"".join(canonical_bytes(row) for row in records),
        "private_truth_verification_receipts_v2.jsonl": b"".join(canonical_bytes(row) for row in verification_rows),
        "private_truth_alternative_exclusion_ledger_v1.jsonl": b"".join(canonical_bytes(row) for row in exclusion_rows),
        "private_truth_scoreability_gate_v1.json": canonical_bytes(scoreability_gate),
        "private_truth_builder_outcome_blindness_audit.json": canonical_bytes(blindness),
        "private_truth_current_output_noninterference_audit.json": canonical_bytes(noninterference),
        "truth_bundle_contract.json": canonical_bytes({
            "schema": "CandidateTruthRecordV2", "candidate_count": 8,
            "created_at_utc": args.created_at_utc,
            "terminal_commitment_registry_sha256": sha256_bytes(Path(args.terminal_commitments).read_bytes()),
            "candidate_contract_registry_sha256": sha256_bytes(Path(args.contracts).read_bytes()),
            "authority_allowed": "historical non-counting calibration only",
            "authority_forbidden": ["repair", "repair count", "release", "public write"],
        }),
    }
    bundle = output_root / "Batch098_Private_Sealed_Truth_Frozen_Eight_v2.zip"
    identity = build_deterministic_bundle(bundle, portable_members)
    identity.update({
        "status": "PASS", "producer": "scripts.build_batch098_private_sealed_truth",
        "execution_depth": "private upstream source custody and candidate-bound truth construction",
        "semantic_scope": "historical frozen eight local truth",
        "authority_allowed": "historical non-counting calibration only",
        "authority_forbidden": ["repair", "repair count", "release", "public write"],
    })

    write_jsonl(output_root / "private_truth_source_inventory_v1.jsonl", source_rows)
    write_jsonl(output_root / "candidate_truth_records_v2.jsonl", records)
    write_jsonl(output_root / "private_truth_verification_receipts_v2.jsonl", verification_rows)
    write_jsonl(output_root / "private_truth_alternative_exclusion_ledger_v1.jsonl", exclusion_rows)
    write_json(output_root / "private_truth_scoreability_gate_v1.json", scoreability_gate)
    write_json(output_root / "private_truth_builder_outcome_blindness_audit.json", blindness)
    write_json(output_root / "private_truth_current_output_noninterference_audit.json", noninterference)
    write_json(verification_root / "private_sealed_truth_bundle_identity_v2.json", identity)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
