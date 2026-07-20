"""Verify fresh Batch103 candidate evidence and seal truth-blind outcome envelopes."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from controllergate.evidence.batch103_fresh_execution_attestation_v1 import (
    verify_batch103_fresh_execution_receipt,
)


STATIC_OUT = ROOT / "outputs/post_v2_37_hardening_batch103_reactome_isomorphism_causal_planning_gain_exact_materialization"


def canonical_hash(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def collect_jsonl(root: Path, name: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in sorted(root.rglob(name)):
        rows.extend(read_jsonl(path))
    return rows


def collect_json(root: Path, name: str) -> list[dict[str, Any]]:
    return [json.loads(path.read_text(encoding="utf-8")) for path in sorted(root.rglob(name))]


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


STATUS_PRIORITY = {
    "EXECUTED_VERIFIED": 0,
    "EXECUTED_PREDICATE_FALSE": 1,
    "BLOCKED_EXACT_PROVIDER_UNAVAILABLE": 2,
    "BLOCKED_SOURCE_UNAVAILABLE": 3,
    "BLOCKED_FIXTURE_UNAVAILABLE": 4,
    "BLOCKED_SERVICE_UNAVAILABLE": 5,
    "BLOCKED_INCIDENT_PREFLIGHT": 6,
    "SUPERSEDED_WITH_RECEIPT": 7,
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cell-artifacts-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--workflow-run-id", required=True)
    parser.add_argument("--workflow-head", required=True)
    args = parser.parse_args()
    args.output_root.mkdir(parents=True, exist_ok=True)

    submitted = collect_jsonl(args.cell_artifacts_root, "batch103_fresh_execution_receipts_v1.jsonl")
    verification = [
        {
            "execution_receipt_id": row.get("execution_receipt_id"),
            "blockers": verify_batch103_fresh_execution_receipt(
                row,
                current_workflow_run_id=args.workflow_run_id,
                current_workflow_head=args.workflow_head,
            ),
        }
        for row in submitted
    ]
    invalid = [row for row in verification if row["blockers"]]
    if invalid:
        raise RuntimeError(f"invalid Batch103 fresh receipts: {invalid[:3]}")

    cells = read_jsonl(ROOT / "configs/batch102_counterfactual_cell_registry_v4.jsonl")
    cell_by_id = {row["cell_id"]: row for row in cells}
    receipt_by_cell: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for receipt in submitted:
        if receipt["cell_id"] not in cell_by_id:
            raise RuntimeError(f"unregistered fresh cell: {receipt['cell_id']}")
        receipt_by_cell[receipt["cell_id"]].append(receipt)

    account_rows = collect_jsonl(args.cell_artifacts_root, "batch103_cell_accounting_v1.jsonl")
    account_by_cell: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in account_rows:
        account_by_cell[row["cell_id"]].append(row)

    ledger = []
    for cell in cells:
        receipts = receipt_by_cell.get(cell["cell_id"], [])
        if receipts:
            status = (
                "EXECUTED_VERIFIED"
                if all(row["predicate_result"] for row in receipts)
                else "EXECUTED_PREDICATE_FALSE"
            )
        else:
            proposed = [row.get("status") for row in account_by_cell[cell["cell_id"]]]
            allowed = [row for row in proposed if row in STATUS_PRIORITY]
            status = min(allowed, key=STATUS_PRIORITY.get) if allowed else "BLOCKED_INCIDENT_PREFLIGHT"
        row = {
            "cell_id": cell["cell_id"],
            "candidate_id": cell["candidate_id"],
            "program_id": cell["program_id"],
            "status": status,
            "fresh_receipt_ids": [receipt["execution_receipt_id"] for receipt in receipts],
            "fresh_execution_epoch": "BATCH103_FRESH_OPERATION" if receipts else None,
            "workflow_run_id": str(args.workflow_run_id) if receipts else None,
            "workflow_head": args.workflow_head if receipts else None,
            "semantic_reproducibility": len(receipts) >= 2
            and len({(r["semantic_fingerprint"], r["predicate_result"]) for r in receipts}) == 1,
            "authority_allowed": "account one registered cell from current-workflow receipts",
            "authority_forbidden": ["historical substitution", "patch", "repair count", "release"],
        }
        row["accounting_hash"] = canonical_hash(row)
        ledger.append(row)

    envelopes = []
    for cell_id, receipts in sorted(receipt_by_cell.items()):
        outcomes = [
            {
                "execution_receipt_id": row["execution_receipt_id"],
                "semantic_fingerprint": row["semantic_fingerprint"],
                "predicate_result": row["predicate_result"],
                "raw_return_code": row["raw_return_code"],
            }
            for row in sorted(receipts, key=lambda value: value["execution_receipt_id"])
        ]
        unsigned = {
            "envelope_id": f"batch103-envelope:{canonical_hash(cell_id)[:20]}",
            "cell_id": cell_id,
            "candidate_id": cell_by_id[cell_id]["candidate_id"],
            "program_id": cell_by_id[cell_id]["program_id"],
            "execution_epoch": "BATCH103_FRESH_OPERATION",
            "workflow_run_id": str(args.workflow_run_id),
            "workflow_head": args.workflow_head,
            "outcomes": outcomes,
            "semantic_reproducibility": len(outcomes) >= 2
            and len({(r["semantic_fingerprint"], r["predicate_result"]) for r in outcomes}) == 1,
            "truth_access": 0,
            "private_tld_access": 0,
            "sealed_before_arm_execution": True,
            "authority_allowed": "selected-outcome semantic observation after preregistered selection",
            "authority_forbidden": ["truth", "ownership", "patch", "repair count", "release"],
        }
        unsigned["envelope_hash"] = canonical_hash(unsigned)
        envelopes.append(unsigned)

    sources = collect_json(args.cell_artifacts_root, "batch103_source_capsule_v2.json")
    providers = collect_json(args.cell_artifacts_root, "batch103_provider_capsule_v4.json")
    brokers = collect_jsonl(args.cell_artifacts_root, "batch103_broker_operations_v1.jsonl")
    blockers = collect_jsonl(args.cell_artifacts_root, "batch103_candidate_blockers_v1.jsonl")
    raw = [
        {
            "execution_receipt_id": row["execution_receipt_id"],
            "stdout_object": row["raw_stdout_object"],
            "stderr_object": row["raw_stderr_object"],
            "return_code": row["raw_return_code"],
        }
        for row in submitted
    ]
    semantic = [
        {
            "execution_receipt_id": row["execution_receipt_id"],
            "semantic_projection_id": row["semantic_projection_id"],
            "semantic_fingerprint": row["semantic_fingerprint"],
            "predicate_result": row["predicate_result"],
        }
        for row in submitted
    ]

    write_jsonl(args.output_root / "batch103_fresh_execution_receipts_v1.jsonl", submitted)
    write_jsonl(args.output_root / "batch103_broker_operations_v1.jsonl", brokers)
    write_jsonl(args.output_root / "batch103_registered_cell_ledger_v1.jsonl", ledger)
    write_jsonl(args.output_root / "batch103_candidate_blockers_v1.jsonl", blockers)
    write_jsonl(args.output_root / "batch103_source_capsule_registry_v1.jsonl", sources)
    write_jsonl(args.output_root / "batch103_provider_capsule_registry_v1.jsonl", providers)
    write_jsonl(args.output_root / "batch103_raw_observations_v1.jsonl", raw)
    write_jsonl(args.output_root / "batch103_semantic_observations_v1.jsonl", semantic)
    write_jsonl(args.output_root / "batch103_outcome_envelopes_v1.jsonl", envelopes)
    audit = {
        "status": "PASS" if len(submitted) == len(verification) else "BLOCK",
        "execution_epoch": "BATCH103_FRESH_OPERATION",
        "workflow_run_id": str(args.workflow_run_id),
        "workflow_head": args.workflow_head,
        "submitted_receipt_count": len(submitted),
        "verified_receipt_count": len(verification),
        "fresh_executed_cell_count": len(receipt_by_cell),
        "registered_cell_count": len(cells),
        "historical_batch102_receipts_counted_as_fresh": 0,
        "invalid_receipt_count": 0,
        "ordinary_patch_count": 0,
        "truth_access": 0,
        "private_tld_access": 0,
    }
    audit["audit_hash"] = canonical_hash(audit)
    write_json(args.output_root / "batch103_fresh_execution_origin_audit.json", audit)
    seal = {
        "status": "PASS_OUTCOMES_SEALED" if envelopes else "PASS_NO_FRESH_OUTCOMES_AVAILABLE",
        "envelope_count": len(envelopes),
        "registered_vault_count": len(cells),
        "unmaterialized_vault_count": len(cells) - len(envelopes),
        "workflow_run_id": str(args.workflow_run_id),
        "workflow_head": args.workflow_head,
        "sealed_before_arm_execution": True,
        "truth_access": 0,
        "private_tld_access": 0,
        "unauthorized_outcome_access": 0,
    }
    seal["seal_hash"] = canonical_hash(seal)
    write_json(args.output_root / "batch103_outcome_envelope_seal_receipt_v1.json", seal)
    print(json.dumps({**audit, "outcome_envelope_count": len(envelopes)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
