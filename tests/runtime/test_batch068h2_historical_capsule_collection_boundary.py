from __future__ import annotations

import json
from pathlib import Path

from controllergate.core.semantic_runtime_v3 import RUNTIME_STEPS, TOPOLOGY_META_GATES, execute_runtime_path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/post_v2_37_hardening_batch068h2_tld_brot_bulb_topology_runtime_historical_capsule_recovery"


def load(name):
    return json.loads((OUT / name).read_text(encoding="utf-8"))


def test_runtime_transitions_always_record_topology_gate_context():
    facts = {step: {"requested_gate_decision": "BLOCK" if step == "decision_time_provider_resolution" else "PASS", "candidate_id": "candidate", "decision_time_evidence": True, "artifact_custody_status": "PASS", "source_approved": True, "candidate_class": "approved_external_source", "seed_ready": True, "workspace_mutation_count": 0, "isolated_runtime": True, "provider_lock_status": "PASS", "command_argv": ["python"], "test_tree_hash_match": True, "candidate_sha": "a" * 40, "runner_target_mixed": False, "orthology_dimensions": {}, "ast_scope_authorized": True, "elbow_classification": "closed", "decision_time_only": True, "outcome_blind": True, "baseline_drift": False, "canonical_state_mutated": False, "output_contract_hash": "a" * 64, "claim_boundary_status": "PASS", "duplicate_replay": "NOT_RUN", "repair_count_increment": False, "runtime_activation_allowed": False, "fixed_commit_used": False, "later_commit_used": False, "gold_patch_used": False, "future_test_used": False, "hidden_benchmark_state_used": False} for step in RUNTIME_STEPS}
    records = execute_runtime_path("candidate", "0" * 64, facts)
    assert len(records) == 13
    assert all(record["topology_gates_evaluated"] == list(TOPOLOGY_META_GATES) for record in records)
    assert all("proof_matrix_hash" in record for record in records)


def test_historical_provider_arms_and_cutoff_claims_are_separate():
    capsule = load("nbclient_historical_capsule.json")
    arms = {item["arm"]: item for item in capsule["provider_arms"]}
    assert arms["observed_historical_environment"]["exact_observed_environment_established"] is False
    assert arms["cutoff_compatible_transitive_lock"]["classification"] == "cutoff_compatible_not_observed_exact"
    assert arms["cutoff_compatible_transitive_lock"]["post_cutoff_selected_artifact_count"] == 0
    assert arms["current_declared_lock"]["classification"] == "diagnostic_only_not_decision_time_reproduction"


def test_warning_localization_has_no_reproduction_authority():
    warning = load("nbclient_warning_promotion_basin.json")
    assert warning["is_issue316_target_failure"] is False
    assert warning["warning_suppression_authority"] == "non_authoritative_basin_localization"
    assert warning["warning_suppression_establishes_reproduction"] is False


def test_collection_is_not_run_while_historical_capsule_is_partial():
    collection = load("nbclient_collection_decision.json")
    assert collection["collection_run_1"] == collection["collection_run_2"] == "NOT_RUN"
    assert collection["test_bodies_executed"] == collection["target_tests_executed"] == 0
    assert collection["workspace_mutations"] == collection["test_tree_mutations"] == 0


def test_source_wheel_and_mixed_origin_modes_remain_distinct():
    assert load("nbclient_source_mode_identity.json")["status"] == "PASS"
    assert load("nbclient_wheel_mode_identity.json")["status"] == "NOT_RUN"
    assert load("nbclient_mixed_mode_identity.json")["status"] == "BLOCK"


def test_upstream_blocked_collection_is_not_an_executed_failure():
    semantics = load("batch068h1_status_semantics_reconciliation.json")
    counts = load("batch068h1_failed_branch_count_reconciliation.json")
    assert semantics["collection_attempt_2_operation_status"] == "NOT_RUN"
    assert semantics["reported_as_executed_collection_failure"] is False
    assert (counts["executed_failed_branch_count"], counts["upstream_blocked_branch_count"], counts["total_closed_branch_count"]) == (1, 1, 2)
