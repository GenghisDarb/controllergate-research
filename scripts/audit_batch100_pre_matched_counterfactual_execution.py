from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


FINDINGS = (
    ("B100-001", "batch099_not_officially_ingested_at_start", "configs/batch099_master_completion_ledger.json"),
    ("B100-002", "long_term_goals_missing_from_historical_ledger", "configs/batch099_master_completion_ledger.json"),
    ("B100-003", "no_new_paired_candidate_operations", ".github/workflows/post_v2_37_hardening_batch099_causal_differential_intervention_contradiction_root_closure.yml"),
    ("B100-004", "generic_not_candidate_bound_contracts", "outputs/post_v2_37_hardening_batch099_causal_differential_intervention_contradiction_root_closure_master_completion_ledger/causal_differential/batch099_matched_counterfactual_probe_contracts_v1.jsonl"),
    ("B100-005", "existing_pairs_confounded", "outputs/post_v2_37_hardening_batch099_causal_differential_intervention_contradiction_root_closure_master_completion_ledger/causal_differential/batch099_existing_counterfactual_pair_audit_v1.jsonl"),
    ("B100-006", "candidate_name_causal_family_heuristic", "controllergate/amds/causal_differential_v9.py"),
    ("B100-007", "string_changed_dimension_heuristic", "controllergate/amds/causal_differential_v9.py"),
    ("B100-008", "seven_incidents_not_materialized", "outputs/post_v2_37_hardening_batch099_causal_differential_intervention_contradiction_root_closure_master_completion_ledger/causal_differential/batch099_existing_counterfactual_pair_audit_v1.jsonl"),
    ("B100-009", "darker_git_boundary_missing", "configs/batch098_candidate_contracts_v2.jsonl"),
    ("B100-010", "py_bugger_cli_incident_missing", "configs/batch098_candidate_contracts_v2.jsonl"),
    ("B100-011", "cloudpickle_exact_nodes_missing", "configs/batch098_candidate_contracts_v2.jsonl"),
    ("B100-012", "freezegun_exact_nodes_missing", "configs/batch098_candidate_contracts_v2.jsonl"),
    ("B100-013", "pytest_collection_failure_not_incident", "configs/batch098_candidate_contracts_v2.jsonl"),
    ("B100-014", "openbb_target_not_run", "configs/batch098_candidate_contracts_v2.jsonl"),
    ("B100-015", "poetry_windows_path_incident_missing", "configs/batch098_candidate_contracts_v2.jsonl"),
    ("B100-016", "execution_and_incident_provider_conflated", "configs/batch098_candidate_contracts_v2.jsonl"),
    ("B100-017", "poetry_platform_mismatch", "configs/batch098_candidate_contracts_v2.jsonl"),
    ("B100-018", "cloudpickle_provider_series_mismatch", "configs/batch098_candidate_contracts_v2.jsonl"),
    ("B100-019", "freezegun_microrelease_mismatch", "configs/batch098_candidate_contracts_v2.jsonl"),
    ("B100-020", "audioread_beta_provider_control_missing", "configs/batch098_candidate_contracts_v2.jsonl"),
    ("B100-021", "source_provider_capsule_registry_missing", "configs/batch099_master_completion_ledger.json"),
    ("B100-022", "candidate_bound_intervention_registry_missing", "configs/batch099_master_completion_ledger.json"),
    ("B100-023", "single_changed_dimension_unproven", "outputs/post_v2_37_hardening_batch099_causal_differential_intervention_contradiction_root_closure_master_completion_ledger/causal_differential/batch099_existing_counterfactual_pair_audit_v1.jsonl"),
    ("B100-024", "duplicate_clean_replay_missing", "configs/batch099_master_completion_ledger.json"),
    ("B100-025", "order_carryover_control_missing", "configs/batch099_master_completion_ledger.json"),
    ("B100-026", "factorial_interaction_design_missing", "configs/batch099_master_completion_ledger.json"),
    ("B100-027", "ownership_alternative_exclusion_missing", "configs/batch099_master_completion_ledger.json"),
    ("B100-028", "public_workflow_no_paired_interventions", ".github/workflows/post_v2_37_hardening_batch099_causal_differential_intervention_contradiction_root_closure.yml"),
    ("B100-029", "arm_outcome_vault_missing", "configs/batch099_master_completion_ledger.json"),
    ("B100-030", "architecture_gain_unevaluable", "outputs/post_v2_37_hardening_batch099_causal_differential_intervention_contradiction_root_closure_master_completion_ledger/causal_differential/batch099_architecture_component_gain_gate.json"),
    ("B100-031", "private_scoring_not_counterfactual_aware", "scripts/finalize_batch099_private_calibration.py"),
    ("B100-032", "future_goal_persistence_missing", "configs/batch099_master_completion_ledger.json"),
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository", default=".")
    parser.add_argument("--output", required=True)
    parser.add_argument("--commit", default="c9646cdf5f9e321d179397082d9fa9439c15c196")
    args = parser.parse_args()
    root = Path(args.repository).resolve()
    findings = []
    for finding_id, symbol, relative in FINDINGS:
        path = root / relative
        digest = hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
        findings.append({"finding_id": finding_id, "commit": args.commit, "path": relative, "symbol": symbol, "line_range": "relevant evidence object", "raw_evidence_sha256": digest, "risk": symbol.replace("_", " "), "required_correction": "candidate-bound executed matched-counterfactual evidence with explicit custody and authority boundaries", "red_to_green_test": f"test_{symbol}"})
    result = {"status": "BATCH100_PRE_MATCHED_COUNTERFACTUAL_EXECUTION_FAIL_EXPECTED", "finding_count": len(findings), "findings": findings, "authority_allowed": "expected-red implementation gate", "authority_forbidden": ["scientific pass", "ownership", "patch", "repair count", "release"]}
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(result["status"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
