"""Classify active and immutable historical BROT terminology usages."""

from __future__ import annotations

import hashlib
import json
import subprocess
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs/post_v2_37_hardening_batch103_reactome_isomorphism_causal_planning_gain_exact_materialization"
TERMS = {
    "TORUS-BROT": "CANONICAL_TORUS_BROT",
    "ToT-BULB": "CANONICAL_TOT_BULB",
    "ToT-BROT": "CANONICAL_TOT_BROT",
}


def canonical_hash(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def classification(path: str, term: str) -> str:
    lowered = path.lower()
    historical = (
        path.startswith("outputs/")
        or "/batch" in lowered
        or Path(path).name.lower().startswith("batch")
        or "historical" in lowered
    )
    if historical:
        return "HISTORICAL_MISLABEL"
    return TERMS[term]


def main() -> int:
    tracked = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    ).stdout.splitlines()
    usages = []
    receipts = []
    for relative in tracked:
        if relative.startswith(
            "outputs/post_v2_37_hardening_batch103_reactome_isomorphism_causal_planning_gain_exact_materialization/"
        ):
            continue
        if not relative.endswith((".py", ".json", ".jsonl", ".md", ".yml", ".yaml")):
            continue
        path = ROOT / relative
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeDecodeError):
            continue
        for number, line in enumerate(lines, 1):
            for term in TERMS:
                if term not in line:
                    continue
                row = {
                    "path": relative,
                    "line": number,
                    "term": term,
                    "classification": classification(relative, term),
                    "immutable_historical_evidence_renamed": False,
                }
                row["usage_hash"] = canonical_hash(row)
                usages.append(row)
                if row["classification"] == "HISTORICAL_MISLABEL":
                    receipt = {
                        "usage_hash": row["usage_hash"],
                        "historical_path": relative,
                        "historical_line": number,
                        "historical_term": term,
                        "current_translation": TERMS[term],
                        "historical_bytes_mutated": False,
                    }
                    receipt["receipt_hash"] = canonical_hash(receipt)
                    receipts.append(receipt)
    counts = Counter(row["classification"] for row in usages)
    unsupported = counts["AMBIGUOUS"] + counts["UNSUPPORTED"]
    result = {
        "status": "PASS" if usages and unsupported == 0 else "BLOCK",
        "usage_count": len(usages),
        "classification_distribution": dict(sorted(counts.items())),
        "historical_translation_receipt_count": len(receipts),
        "ambiguous_or_unsupported_count": unsupported,
        "usages": usages,
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "brot_tot_brot_tot_bulb_terminology_audit_v2.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n"
    )
    with (OUT / "brot_historical_translation_receipts_v2.jsonl").open(
        "w", encoding="utf-8", newline="\n"
    ) as handle:
        for receipt in receipts:
            handle.write(json.dumps(receipt, sort_keys=True, separators=(",", ":")) + "\n")
    print(json.dumps({key: result[key] for key in ("status", "usage_count", "classification_distribution", "historical_translation_receipt_count")}, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
