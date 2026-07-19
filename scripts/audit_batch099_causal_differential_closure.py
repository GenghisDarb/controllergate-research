from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def lines(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", required=True)
    args = parser.parse_args()
    root = Path(args.output_root)
    ingest = root / "batch098_official_ingest"
    causal = root / "causal_differential"
    receipt = ingest / "ingest_receipts" / "batch098_official_ingest_receipt.json"
    receipt_hash = hashlib.sha256(receipt.read_bytes()).hexdigest()
    roots = lines(causal / "batch099_contradiction_root_map_v1.jsonl")
    facts = lines(causal / "batch099_provisional_fact_causal_evidence_map_v1.jsonl")
    pairs = lines(causal / "batch099_existing_counterfactual_pair_audit_v1.jsonl")
    terminals = lines(causal / "batch099_corrected_terminal_records_v1.jsonl")
    replay = load(causal / "batch099_corrected_semantic_replay_summary.json")
    gate = load(causal / "batch099_counterfactual_adequacy_gate.json")
    decision = load(causal / "batch099_scientific_decision.json")
    checks = {
        "official_ingest": load(receipt)["ingest_status"] == "PASS_OFFICIAL_BATCH098_ARTIFACT_INGEST",
        "root_count": len(roots) == 432,
        "root_classification": all(row["root_classification"] == "false_mutual_exclusion" for row in roots),
        "fact_count": len(facts) == 504,
        "contact_not_ownership": all(row["evidence_level"] == "CONTACT_VERIFIED" and not row["ownership_supported"] for row in facts),
        "matched_pairs_audited": len(pairs) >= 8,
        "ownership_not_overpromoted": gate["ownership_supporting_pair_count"] == 0,
        "corrected_contradictions": replay["genuine_contradiction_count"] == 0 and replay["false_mutual_exclusion_count_after_correction"] == 0,
        "terminal_count": len(terminals) == 80,
        "honest_abstention": all(row["terminal_class"] == "INSUFFICIENT_EVIDENCE" for row in terminals),
        "scientific_block": decision["status"] == "SCIENTIFIC_BLOCK",
        "claim_boundary": decision["claim_boundary"]["release_decision"] == "PRODUCT_BETA_RC_BLOCKED_EXACT",
        "no_actuation": decision["ordinary_patch_count"] == 0 and decision["historical_increment"] == 0,
        "ingest_binding": all(load(path).get("official_ingest_receipt_sha256", receipt_hash) == receipt_hash for path in causal.glob("*.json")),
    }
    result = {"status": "PASS" if all(checks.values()) else "BLOCK", "checks": checks, "active_blockers": decision["active_blockers"]}
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
