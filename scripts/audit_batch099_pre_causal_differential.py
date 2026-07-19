from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


FINDINGS = (
    ("B099-CDI-001", "contact_is_ownership", "public_provisional_facts_v2.jsonl", "Contact-shaped probe partitions directly create ownership-class facts."),
    ("B099-CDI-002", "false_mutual_exclusion", "public_failed_branches_v2.jsonl", "Coexisting ownership contacts are treated as mutually exclusive."),
    ("B099-CDI-003", "no_counterfactual_pairs", "arm_probe_inventory_comparison_v2.json", "No probe contract binds a changed dimension and held invariants to paired operations."),
    ("B099-CDI-004", "no_evidence_hierarchy", "controller_audit_terminal_contract_v2.json", "The terminal contract does not distinguish contact, sensitivity, necessity, sufficiency, interaction, and ownership."),
    ("B099-CDI-005", "mixed_failure_unmeasured", "public_failed_branches_v2.jsonl", "Multiple active classes have no factorial interaction test."),
    ("B099-CDI-006", "symmetric_contradictions", "public_failed_branches_v2.jsonl", "Every candidate has the same 54-contradiction shape."),
    ("B099-CDI-007", "zero_causal_coverage", "controller_audit_terminal_records_v2.jsonl", "All eighty policies terminate with insufficient evidence."),
    ("B099-CDI-008", "architecture_gain_unmeasured", "arm_probe_inventory_comparison_v2.json", "Component additions are not tied to a preregistered causal-performance improvement."),
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ingest-root", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--commit", required=True)
    args = parser.parse_args()
    ingest = Path(args.ingest_root)
    extracted = ingest / "extracted_public_artifact"
    receipt = ingest / "ingest_receipts" / "batch098_official_ingest_receipt.json"
    failures = [name for _, _, name, _ in FINDINGS if not (extracted / name).is_file()]
    findings = [
        {
            "finding_id": finding_id,
            "commit": args.commit,
            "path": f"batch098_official_ingest/extracted_public_artifact/{path}",
            "symbol": symbol,
            "line_range": "whole evidence object",
            "raw_evidence_sha256": hashlib.sha256((extracted / path).read_bytes()).hexdigest(),
            "risk": risk,
            "required_correction": "Introduce matched differential evidence and level-aware constraint semantics.",
            "red_to_green_test": f"test_{symbol}",
        }
        for finding_id, symbol, path, risk in FINDINGS
    ]
    result = {
        "status": "BATCH099_PRE_CAUSAL_DIFFERENTIAL_FAIL_EXPECTED" if not failures else "BLOCK",
        "finding_count": len(findings),
        "findings": findings,
        "official_ingest_receipt_sha256": hashlib.sha256(receipt.read_bytes()).hexdigest(),
        "missing_inputs": failures,
        "authority_allowed": "expected-red implementation gate only",
        "authority_forbidden": ["scientific pass", "repair", "repair count", "release"],
    }
    Path(args.output).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(result["status"])
    return 0 if result["status"].endswith("FAIL_EXPECTED") else 1


if __name__ == "__main__":
    raise SystemExit(main())
