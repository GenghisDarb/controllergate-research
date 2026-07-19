"""Audit Batch100 custody, causal evidence, critic, and immutable claim boundaries."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "outputs/post_v2_37_hardening_batch100_matched_counterfactual_execution_causal_ownership_architecture_gain_master_roadmap_lock"


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--pre-execution", action="store_true")
    args = parser.parse_args()
    out = args.output_root
    errors: list[str] = []
    ingest = out / "batch099_official_ingest/ingest_receipts/batch099_official_ingest_receipt.json"
    if hashlib.sha256(ingest.read_bytes()).hexdigest() != "55f9549fe1bf9d0d417980686434daf2c5336195b0955bd7acdd3452c428f2f3":
        errors.append("batch099_ingest_receipt_identity_mismatch")
    ledger = read_json(ROOT / "configs/controllergate_master_completion_ledger_v2.json")
    if len(ledger.get("goals", [])) != 21:
        errors.append("master_ledger_goal_count_mismatch")
    protocol_paths = [
        "historical_cohort_expansion_protocol_v1.json", "abstention_required_cohort_protocol_v1.json",
        "mixed_failure_cohort_protocol_v1.json", "prospective_validation_protocol_v1.json",
        "memory_lift_validation_protocol_v1.json", "protected_repair_protocol_v1.json",
        "external_replication_protocol_v1.json", "product_beta_exit_criteria_v1.json",
        "self_maintaining_software_evidence_protocol_v1.json",
    ]
    for name in protocol_paths:
        path = ROOT / "configs" / name
        if not path.is_file() or read_json(path).get("status") != "PROTOCOL_READY":
            errors.append(f"protocol_not_ready:{name}")
    programs = read_jsonl(ROOT / "configs/batch100_candidate_counterfactual_programs_v2.jsonl")
    cells = read_jsonl(ROOT / "configs/batch100_counterfactual_cell_registry_v2.jsonl")
    if len(programs) != 9 or len(cells) != 32:
        errors.append("counterfactual_contract_counts_mismatch")
    if args.pre_execution:
        print(json.dumps({"status": "PASS" if not errors else "BLOCK", "errors": errors, "program_count": len(programs), "cell_count": len(cells)}, sort_keys=True))
        return 0 if not errors else 1
    required = [
        "matched_counterfactual_evidence_v2.jsonl", "controller_audit_counterfactual_terminal_records_v3.jsonl",
        "counterfactual_outcome_vault_registry_v1.jsonl", "arm_counterfactual_execution_receipts_v1.jsonl",
        "baseline_counterfactual_execution_receipts_v1.jsonl", "batch100_claim_boundary.json",
        "batch100_consolidated_state.json", "critic/batch100_semantic_mutation_campaign_summary.json",
        "SHA256SUMS.txt", "campaign_summary.md",
    ]
    for rel in required:
        if not (out / rel).is_file() or (out / rel).stat().st_size == 0:
            errors.append(f"required_output_missing_or_empty:{rel}")
    if not errors:
        state = read_json(out / "batch100_consolidated_state.json")
        claim = read_json(out / "batch100_claim_boundary.json")
        critic = read_json(out / "critic/batch100_semantic_mutation_campaign_summary.json")
        if state.get("patch_operations") != 0 or state.get("repair_count_increment") != 0 or state.get("historical_increment") != 0:
            errors.append("forbidden_actuation_or_count_mutation")
        if state.get("truth_access_during_public_execution") != 0 or state.get("private_tld_access_during_candidate_execution") != 0:
            errors.append("private_evidence_public_execution_leak")
        if claim.get("status") != "PRODUCT_BETA_BLOCKED_EXACT" or claim.get("production_readiness") is not False:
            errors.append("release_boundary_overclaim")
        if critic.get("semantic_mutations_executed", 0) < 50 or critic.get("semantic_mutations_rejected") != critic.get("semantic_mutations_executed"):
            errors.append("mutation_campaign_incomplete")
        for row in read_jsonl(out / "matched_counterfactual_evidence_v2.jsonl"):
            if row.get("ownership_supported") and not (row.get("necessity_supported") or row.get("sufficiency_supported")):
                errors.append("sensitivity_promoted_to_ownership")
    print(json.dumps({"status": "PASS" if not errors else "BLOCK", "errors": errors, "program_count": len(programs), "cell_count": len(cells)}, sort_keys=True))
    return 0 if not errors else 1

if __name__ == "__main__":
    raise SystemExit(main())
