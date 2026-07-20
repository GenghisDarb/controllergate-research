"""Audit all Batch103 candidate slices before outcome envelopes are sealed."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from controllergate.evidence.batch103_fresh_execution_attestation_v1 import (
    verify_batch103_fresh_execution_receipt,
)


def rows(path: Path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--workflow-run-id", required=True)
    parser.add_argument("--workflow-head", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    summaries = [json.loads(path.read_text(encoding="utf-8")) for path in sorted(args.root.rglob("batch103_slice_summary.json"))]
    receipts = [row for path in sorted(args.root.rglob("batch103_fresh_execution_receipts_v1.jsonl")) for row in rows(path)]
    accounts = [row for path in sorted(args.root.rglob("batch103_cell_accounting_v1.jsonl")) for row in rows(path)]
    expected_cells = {row["cell_id"] for row in rows(ROOT / "configs/batch102_counterfactual_cell_registry_v4.jsonl")}
    errors = []
    if len(summaries) != 12:
        errors.append(f"candidate_slice_count:{len(summaries)}")
    if any(row.get("execution_epoch") != "BATCH103_FRESH_OPERATION" for row in summaries):
        errors.append("non_batch103_slice_epoch")
    if {row["cell_id"] for row in accounts} != expected_cells:
        errors.append("registered_cell_accounting_incomplete")
    for receipt in receipts:
        blockers = verify_batch103_fresh_execution_receipt(
            receipt,
            current_workflow_run_id=args.workflow_run_id,
            current_workflow_head=args.workflow_head,
        )
        if blockers:
            errors.append(f"{receipt.get('execution_receipt_id')}:{blockers}")
    result = {
        "status": "PASS" if not errors else "BLOCK",
        "slice_count": len(summaries),
        "candidate_count": len({row["candidate_id"] for row in summaries}),
        "fresh_receipt_count": len(receipts),
        "accounted_cell_count": len({row["cell_id"] for row in accounts}),
        "execution_epoch": "BATCH103_FRESH_OPERATION",
        "workflow_run_id": str(args.workflow_run_id),
        "workflow_head": args.workflow_head,
        "historical_receipts_accepted": 0,
        "truth_access": 0,
        "patch_operations": 0,
        "errors": errors,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
