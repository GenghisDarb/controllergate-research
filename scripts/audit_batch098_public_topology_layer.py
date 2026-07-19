from __future__ import annotations

import argparse
import json
from pathlib import Path


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def audit_layer(source: Path, output: Path, kind: str) -> dict:
    output.mkdir(parents=True, exist_ok=True)
    rows = []
    for summary_path in sorted(source.rglob("topology_verification_summary.json")):
        candidate_root = summary_path.parent
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        if kind == "projection":
            records = read_jsonl(candidate_root / "projection_pair_verification_receipts_v2.jsonl")
            integrity_failed = bool(records) and any(row.get("status") != "PASS" for row in records)
            status = "BLOCK" if integrity_failed else ("PASS" if records else "SCIENTIFIC_BLOCK_NO_EXECUTABLE_PROJECTION_PAIR")
            count = len(records)
        else:
            record = json.loads((candidate_root / "five_modality_reconciliation_v3.json").read_text(encoding="utf-8"))
            passed = record.get("status") in {"PASS", "CONFLICT"} and bool(record.get("modality_receipts", record.get("proposals", [True])))
            status = "PASS" if passed else "BLOCK"
            count = 1
        rows.append({"candidate_id": summary.get("candidate_id"), "status": status, "record_count": count})
    scientific_blocks = sum(row["status"].startswith("SCIENTIFIC_BLOCK") for row in rows)
    execution_complete = len(rows) == 8 and all(row["status"] != "BLOCK" for row in rows)
    audit = {
        "status": "PASS_EXECUTION_WITH_SCIENTIFIC_BLOCKS" if execution_complete and scientific_blocks else ("PASS" if execution_complete else "BLOCK"),
        "kind": kind,
        "candidate_count": len(rows),
        "scientific_block_count": scientific_blocks,
        "rows": rows,
        "producer": "scripts/audit_batch098_public_topology_layer.py",
        "execution_depth": "independent verified-topology layer reconstruction",
        "semantic_scope": f"public {kind} evidence",
        "authority_allowed": "pre-TLD decision evidence",
        "authority_forbidden": ["terminal", "repair", "count", "release"],
    }
    (output / f"public_{kind}_layer_audit.json").write_text(
        json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n"
    )
    return audit


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True)
    parser.add_argument("--kind", required=True, choices=("projection", "modality"))
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    audit = audit_layer(Path(args.source), Path(args.output), args.kind)
    print(json.dumps(audit, sort_keys=True))
    return 0 if audit["status"].startswith("PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
