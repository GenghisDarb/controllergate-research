from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))
from controllergate.evidence.fresh_execution_attestation_v1 import verify_fresh_execution_receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--receipts", required=True)
    parser.add_argument("--workflow-run-id", required=True)
    parser.add_argument("--workflow-head", required=True)
    parser.add_argument("--output")
    args = parser.parse_args()
    rows = [json.loads(line) for line in Path(args.receipts).read_text(encoding="utf-8").splitlines() if line.strip()]
    results = [{"execution_receipt_id": row.get("execution_receipt_id"), "blockers": verify_fresh_execution_receipt(row, current_workflow_run_id=args.workflow_run_id, current_workflow_head=args.workflow_head)} for row in rows]
    audit = {"status": "PASS" if rows and all(not row["blockers"] for row in results) else "BLOCK", "fresh_receipt_count": len(rows),
             "inherited_records_counted_as_fresh": sum("inherited_execution_rejected" in row["blockers"] for row in results),
             "fresh_records_lacking_broker_operations": sum("broker_operation_missing" in row["blockers"] for row in results), "results": results}
    if args.output:
        Path(args.output).write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(audit, sort_keys=True))
    return 0 if audit["status"] == "PASS" else 1


if __name__ == "__main__": raise SystemExit(main())
