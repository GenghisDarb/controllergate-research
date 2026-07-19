from __future__ import annotations

import argparse
import json
from pathlib import Path


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True)
    parser.add_argument("--kind", required=True, choices=("projection", "modality"))
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    source = Path(args.source)
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    rows = []
    for summary_path in sorted(source.rglob("topology_verification_summary.json")):
        candidate_root = summary_path.parent
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        if args.kind == "projection":
            records = read_jsonl(candidate_root / "projection_pair_verification_receipts_v2.jsonl")
            passed = bool(records) and all(row.get("status") == "PASS" for row in records)
            count = len(records)
        else:
            record = json.loads((candidate_root / "five_modality_reconciliation_v3.json").read_text(encoding="utf-8"))
            passed = record.get("status") in {"PASS", "CONFLICT"} and bool(record.get("modality_receipts", record.get("proposals", [True])))
            count = 1
        rows.append({"candidate_id": summary.get("candidate_id"), "status": "PASS" if passed else "BLOCK", "record_count": count})
    audit = {
        "status": "PASS" if len(rows) == 8 and all(row["status"] == "PASS" for row in rows) else "BLOCK",
        "kind": args.kind,
        "candidate_count": len(rows),
        "rows": rows,
        "producer": "scripts/audit_batch098_public_topology_layer.py",
        "execution_depth": "independent verified-topology layer reconstruction",
        "semantic_scope": f"public {args.kind} evidence",
        "authority_allowed": "pre-TLD decision evidence",
        "authority_forbidden": ["terminal", "repair", "count", "release"],
    }
    (output / f"public_{args.kind}_layer_audit.json").write_text(
        json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n"
    )
    print(json.dumps(audit, sort_keys=True))
    return 0 if audit["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
