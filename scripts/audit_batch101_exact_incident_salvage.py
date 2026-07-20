#!/usr/bin/env python3
"""Independent bounded audit for Batch101 public evidence."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs/post_v2_37_hardening_batch101_canonical_semantic_replay_exact_incident_salvage_ownership_closure"


def read_json(name: str) -> dict:
    return json.loads((OUT / name).read_text(encoding="utf-8"))


def rows(name: str) -> list[dict]:
    return [json.loads(line) for line in (OUT / name).read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> int:
    errors = []
    required = [
        "batch101_registered_cell_execution_ledger_v1.jsonl", "raw_execution_observations_v1.jsonl",
        "canonical_semantic_observations_v1.jsonl", "predicate_evaluation_receipts_v1.jsonl",
        "pair_validity_receipts_v3.jsonl", "provider_exactness_receipts_v3.jsonl",
        "matched_counterfactual_evidence_v3.jsonl", "controller_audit_counterfactual_terminal_records_v4.jsonl",
        "architecture_component_gain_gate_v3.json", "batch101_claim_boundary.json", "batch101_consolidated_state.json",
        "critic/batch101_semantic_mutation_campaign_summary.json", "campaign_summary.md",
    ]
    for name in required:
        if not (OUT / name).is_file() or (OUT / name).stat().st_size == 0:
            errors.append(f"missing_or_empty:{name}")
    if not errors:
        ledger = rows("batch101_registered_cell_execution_ledger_v1.jsonl")
        if len(ledger) != 33 or sum(row["execution_status"] == "EXECUTED" for row in ledger) != 28 or sum(row["execution_status"] == "BLOCKED" for row in ledger) != 5:
            errors.append("registered_cell_accounting_mismatch")
        if len(rows("raw_execution_observations_v1.jsonl")) != 56:
            errors.append("raw_replay_count_mismatch")
        if any(row.get("ownership_supported") for row in rows("matched_counterfactual_evidence_v3.jsonl")):
            errors.append("unsupported_ownership")
        if {row["terminal_class"] for row in rows("controller_audit_counterfactual_terminal_records_v4.jsonl")} != {"INSUFFICIENT_EVIDENCE"}:
            errors.append("terminal_overclaim")
        mutation = read_json("critic/batch101_semantic_mutation_campaign_summary.json")
        if mutation["semantic_mutations_executed"] < 60 or mutation["semantic_mutations_rejected"] != mutation["semantic_mutations_executed"]:
            errors.append("mutation_campaign_incomplete")
        claim = read_json("batch101_claim_boundary.json")
        if claim["status"] != "PRODUCT_BETA_BLOCKED_EXACT" or claim["issue_derived_repair_count"] != 6 or claim["native_external_repair_count"] != 4 or claim["historical_increment"] != 0:
            errors.append("claim_boundary_changed")
        if claim["production_readiness"] is not False or claim["self_maintaining_software"] != "false/not_demonstrated":
            errors.append("release_overclaim")
    status = "PASS" if not errors else "BLOCK"
    print(json.dumps({"status": status, "errors": errors}, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
