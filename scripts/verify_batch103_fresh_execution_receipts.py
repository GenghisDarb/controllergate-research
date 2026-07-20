"""Verify Batch103 receipts against one current workflow run and HEAD."""

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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--receipts", type=Path, required=True)
    parser.add_argument("--workflow-run-id", required=True)
    parser.add_argument("--workflow-head", required=True)
    args = parser.parse_args()
    rows = [
        json.loads(line)
        for line in args.receipts.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    results = [
        {
            "execution_receipt_id": row.get("execution_receipt_id"),
            "blockers": verify_batch103_fresh_execution_receipt(
                row,
                current_workflow_run_id=args.workflow_run_id,
                current_workflow_head=args.workflow_head,
            ),
        }
        for row in rows
    ]
    result = {
        "status": "PASS" if rows and all(not row["blockers"] for row in results) else "BLOCK",
        "receipt_count": len(rows),
        "results": results,
    }
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
