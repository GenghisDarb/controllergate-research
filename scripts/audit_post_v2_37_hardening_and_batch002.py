from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from controllergate.core.manifests import verify_manifest
from controllergate.core.artifact_hygiene import audit_artifact_payload

POST_DIR = Path("outputs/post_v2_37_hardening_001")
BATCH_DIR = Path("outputs/clean_replication_batch_002")
BATCH003_DIR = Path("outputs/clean_replication_batch_003")
BATCH004_DIR = Path("outputs/clean_replication_batch_004")
BATCH005_DIR = Path("outputs/clean_replication_batch_005")
BATCH006_DIR = Path("outputs/clean_replication_batch_006")
BATCH007_DIR = Path("outputs/clean_replication_batch_007")
BATCH008_DIR = Path("outputs/clean_replication_batch_008")
BATCH009_DIR = Path("outputs/clean_replication_batch_009")
BATCH010_DIR = Path("outputs/clean_replication_batch_010")
PAYLOAD_DIR = Path("artifact_payload/post_v2_37_hardening_batch010_active_memory_routing")

POST_REQUIRED = [
    "workspace_transport_integrity_policy.json",
    "post_v2_37_hardening_artifact_verification.json",
    "artifact_pycache_payload_audit.json",
    "batch002_mixed_mode_failure_diagnosis.json",
    "corrected_batch002_artifact_verification.json",
    "batch002_real_acquisition_gap_diagnosis.json",
    "real_leads_artifact_verification.json",
    "batch002_environment_resolution_gap_diagnosis.json",
    "batch002_environment_resolution_artifact_verification.json",
    "batch002_repair_generation_gap_diagnosis.json",
    "batch002_repair_generation_artifact_verification.json",
    "second_external_repair_ingest_summary.json",
    "repair_episode_registry_update_report.json",
    "artifact_packaging_correction_report.json",
    "artifact_payload_manifest_report.json",
    "readme_status_update_report.json",
    "public_docs_accuracy_audit.json",
    "operational_gate_matrix_status.json",
    "public_language_audit_expanded.json",
    "workspace_transport_integrity_log.json",
    "transport_boundary_audit.json",
    "homeostasis_risk_policy.json",
    "homeostasis_risk_state.json",
    "starvation_pressure_log.json",
    "version_sprawl_pressure_log.json",
    "public_claim_pressure_log.json",
    "bounded_exploration_budget_policy.json",
    "bounded_exploration_budget_trace.json",
    "context_boundary_policy.json",
    "context_boundary_map.json",
    "context_boundary_rejection_ledger.json",
    "environment_normalization_policy.json",
    "environment_normalization_log.json",
    "issue_derived_evidence_class_policy.json",
    "issue_text_temporal_guard_policy.json",
    "issue_derived_latent_knowledge_risk_disclosure.json",
    "bugsinpy_relaxation_research_status.json",
    "operational_gate_completion_status.json",
    "v3_0_readiness_scorecard_update.json",
    "matched_null_artifact_verification.json",
    "third_external_repair_ingest_summary.json",
    "equal_performance_memory_claim_boundary.json",
    "matched_null_lessons_learned.json",
    "batch003_memory_challenge_artifact_verification.json",
    "batch003_challenge_candidate_failure_diagnosis.json",
    "native_vs_issue_derived_status_after_batch003.json",
    "batch004_artifact_verification.json",
    "batch004_source_materialization_gap_diagnosis.json",
    "batch004_issue_lead_gap_diagnosis.json",
    "batch007_target_reachability_artifact_verification.json",
    "batch007_declared_precondition_gap_diagnosis.json",
    "batch008_declared_formatter_extra_recommendation.json",
    "batch008_declared_precondition_artifact_verification.json",
    "fourth_external_native_repair_ingest_summary.json",
    "batch008_null_ensemble_gap_diagnosis.json",
    "batch009_patch_quarantine_recommendation.json",
    "batch009_patch_quarantined_matched_null_artifact_verification.json",
    "batch009_passive_memory_diagnosis.json",
    "batch010_active_memory_routing_recommendation.json",
    "final_report_post_v2_37_hardening_001.json",
    "consolidated_state_post_v2_37_hardening_001.json",
    "campaign_summary.md",
    "SHA256SUMS.txt",
]

BATCH004_REQUIRED = [
    "consolidated_state_clean_replication_batch_004.json",
    "batch004_dual_track_acquisition_policy.json",
    "native_challenge_acquisition_policy.json",
    "issue_derived_harness_policy.json",
    "context_boundary_pinning_policy.json",
    "homeostasis_risk_policy_batch004.json",
    "bounded_exploration_budget_batch004.json",
    "native_challenge_lead_pool.json",
    "native_challenge_attempts.json",
    "native_challenge_rejection_ledger.json",
    "native_challenge_verified_candidates.json",
    "issue_derived_lead_pool.json",
    "issue_derived_attempts.json",
    "issue_derived_rejection_ledger.json",
    "issue_derived_verified_candidates.json",
    "issue_text_temporal_guard_batch004.json",
    "issue_derived_latent_knowledge_risk_disclosure_batch004.json",
    "memory_enabled_run_results.json",
    "null_ensemble_run_results.json",
    "null_ensemble_summary.json",
    "matched_null_ensemble_separation_score_result.json",
    "memory_separation_claim_evaluation.json",
    "repair_successes.json",
    "native_issue_derived_count_separation.json",
    "claim_boundary.json",
    "homeostasis_risk_state.json",
    "bounded_exploration_budget_trace.json",
    "candidate_starvation_pressure_log.json",
    "context_boundary_map.json",
    "campaign_summary.md",
    "SHA256SUMS.txt",
]

BATCH005_REQUIRED = [
    "campaign_summary.md",
    "consolidated_state_clean_replication_batch_005.json",
    "source_materialization_policy.json",
    "source_materialization_log.json",
    "native_challenge_retry_attempts.json",
    "native_challenge_node_discovery.json",
    "native_challenge_collection_attempts.json",
    "native_challenge_failure_replay_attempts.json",
    "native_challenge_verified_candidates.json",
    "native_challenge_rejection_ledger.json",
    "dependency_resolution_summary.json",
    "target_node_selection_policy.json",
    "target_node_semantic_intent_filter.json",
    "target_node_replay_selection.json",
    "non_intent_failure_classification.json",
    "targeted_issue_seed_intake_report.json",
    "targeted_issue_text_hash.json",
    "targeted_issue_text_temporal_guard.json",
    "targeted_issue_latent_knowledge_risk_disclosure.json",
    "targeted_issue_harness_generation_policy.json",
    "targeted_issue_harness_context_manifest.json",
    "targeted_issue_harness_firewall_audit.json",
    "targeted_issue_harness_verification_result.json",
    "targeted_issue_source_context_filter_map.json",
    "targeted_issue_context_boundary_map.json",
    "targeted_issue_interlock_invariant_map.json",
    "issue_derived_lead_discovery_policy.json",
    "issue_derived_lead_pool.json",
    "issue_derived_attempts.json",
    "issue_derived_rejection_ledger.json",
    "issue_derived_verified_candidates.json",
    "memory_enabled_run_results.json",
    "null_ensemble_run_results.json",
    "null_ensemble_summary.json",
    "matched_null_ensemble_separation_score_result.json",
    "memory_separation_claim_evaluation.json",
    "repair_successes.json",
    "no_overreach_validation.json",
    "stage_interface_contract.json",
    "repairability_basin_source_ranking.json",
    "patchable_source_subset.json",
    "pre_generation_context_state_snapshot.json",
    "repair_intent_lock.json",
    "patch_context_alignment_audit.json",
    "post_patch_constraint_revalidation.json",
    "source_stack_extraction_policy.json",
    "source_stack_extraction_result.json",
    "import_graph_extraction_result.json",
    "ast_closure_extraction_result.json",
    "patchable_source_subset_derivation.json",
    "patchable_source_ranking_corrected.csv",
    "repair_generator_capability_status_corrected.json",
    "no_patch_reason_taxonomy.json",
    "corrected_native_repair_attempt.json",
    "corrected_pre_generation_context_state_snapshot.json",
    "corrected_patch_context_alignment_audit.json",
    "corrected_patch_safety_result.json",
    "corrected_target_validation_result.json",
    "corrected_duplicate_replay_result.json",
    "corrected_no_overreach_validation.json",
    "corrected_null_ensemble_run_results.json",
    "corrected_null_ensemble_summary.json",
    "corrected_matched_null_ensemble_separation_score.json",
    "corrected_memory_separation_claim_evaluation.json",
    "notebooklm_advice_traceability_status.json",
    "notebooklm_advice_carry_forward_blockers.json",
    "operational_gate_matrix_crosscheck.json",
    "carry_forward_blocker_policy.json",
    "carry_forward_blocker_register.json",
    "no_silent_completion_audit.json",
    "claim_boundary.json",
    "SHA256SUMS.txt",
]

BATCH006_REQUIRED = [
    "campaign_summary.md",
    "consolidated_state_clean_replication_batch_006.json",
    "bounded_fragment_patch_policy.json",
    "fragment_patch_candidate_plan.json",
    "fragment_patch_candidates.json",
    "fragment_safety_audits.json",
    "fragment_assembly_seal.json",
    "coupled_dependency_interlock_map.json",
    "interlock_invariant_candidates.json",
    "dual_projection_consistency_check.json",
    "pre_generation_context_state_snapshot_batch006.json",
    "pre_generation_prompt_lock_batch006.json",
    "patch_context_alignment_audit_batch006.json",
    "failure_memory_weighting_trace_batch006.json",
    "memory_separation_claim_evaluation_batch006.json",
    "proof_chain_lock_batch006.json",
    "claim_boundary.json",
    "notebooklm_advice_traceability_status.json",
    "carry_forward_blocker_register.json",
    "SHA256SUMS.txt",
]

BATCH007_REQUIRED = [
    "campaign_summary.md",
    "consolidated_state_clean_replication_batch_007.json",
    "target_intent_reachability_policy.json",
    "target_intent_reachability_map.json",
    "precondition_failure_classification.json",
    "precondition_resolution_plan.json",
    "precondition_resolution_attempts.json",
    "formatter_dependency_probe.json",
    "entrypoint_probe.json",
    "target_replay_after_precondition_resolution.json",
    "dual_projection_recheck_batch007.json",
    "environment_precondition_resolution_policy.json",
    "project_metadata_dependency_scan.json",
    "declared_extras_scan.json",
    "install_strategy_matrix.json",
    "formatter_entrypoint_resolution_attempts.json",
    "import_probe_results.json",
    "precondition_resolution_log_hashes.json",
    "source_facing_projection_recheck.json",
    "test_facing_projection_recheck.json",
    "fragment_patch_candidate_plan_batch007.json",
    "fragment_patch_candidates_batch007.json",
    "fragment_safety_audits_batch007.json",
    "fragment_assembly_seal_batch007.json",
    "candidate_retirement_decision.json",
    "memory_separation_claim_evaluation_batch007.json",
    "claim_boundary.json",
    "notebooklm_advice_traceability_status.json",
    "carry_forward_blocker_register.json",
    "proof_chain_lock_batch007.json",
    "trace_feedback_alignment_policy.json",
    "trace_feedback_alignment_map.json",
    "projected_vs_observed_runtime_path.json",
    "runtime_path_dissonance_report.json",
    "trace_feedback_alignment_status.json",
    "trace_feedback_loop_policy.json",
    "trace_feedback_loop_attempts.json",
    "trace_feedback_loop_final_decision.json",
    "completion_decision_ladder.json",
    "system_interlock_completion_status.json",
    "interdependent_gate_status_vector.json",
    "precondition_to_source_context_feedback.json",
    "repair_generator_trace_consumption_audit.json",
    "null_ensemble_trace_alignment_audit.json",
    "SHA256SUMS.txt",
]

BATCH008_REQUIRED = [
    "campaign_summary.md",
    "consolidated_state_clean_replication_batch_008.json",
    "runtime_workspace_materialization_policy.json",
    "runtime_workspace_materialization_log.json",
    "declared_formatter_extra_scan.json",
    "declared_formatter_extra_install_attempts.json",
    "formatter_import_probe_after_declared_extras.json",
    "entrypoint_resolution_after_declared_extras.json",
    "target_replay_after_declared_extras.json",
    "target_intent_reachability_after_declared_extras.json",
    "dual_projection_recheck_batch008.json",
    "trace_feedback_alignment_status_batch008.json",
    "source_stack_after_declared_extras.json",
    "patchable_source_subset_after_declared_extras.json",
    "coupled_dependency_interlock_map_batch008.json",
    "dual_projection_consistency_after_declared_extras.json",
    "bounded_fragment_patch_policy_batch008.json",
    "fragment_patch_candidates_batch008.json",
    "fragment_safety_audits_batch008.json",
    "assembled_patch_batch008.diff",
    "assembled_patch_batch008_sha256.txt",
    "target_validation_result_batch008.json",
    "duplicate_replay_result_batch008.json",
    "no_overreach_validation_batch008.json",
    "proof_chain_lock_batch008.json",
    "candidate_retirement_decision_batch008.json",
    "targeted_issue_seed_fallback_batch008.json",
    "memory_separation_claim_evaluation_batch008.json",
    "notebooklm_advice_traceability_status.json",
    "carry_forward_blocker_register.json",
    "claim_boundary.json",
    "SHA256SUMS.txt",
]

BATCH009_REQUIRED = [
    "campaign_summary.md",
    "consolidated_state_clean_replication_batch_009.json",
    "patch_artifact_quarantine_policy.json",
    "patch_artifact_denylist.json",
    "patch_artifact_quarantine_audit.json",
    "arm_context_access_manifest.json",
    "arm_a_context_manifest.json",
    "null_ensemble_context_manifests.json",
    "pre_patch_context_reconstruction.json",
    "pre_patch_target_replay_batch009.json",
    "pre_patch_semantic_failure_signature_batch009.json",
    "pre_patch_source_subset_batch009.json",
    "pre_patch_environment_plan_batch009.json",
    "arm_a_memory_enabled_policy.json",
    "arm_a_failure_memory_weighting_trace.json",
    "arm_a_repair_generation_result.json",
    "null_ensemble_policy.json",
    "null_ensemble_run_results.json",
    "null_ensemble_summary.json",
    "null_ensemble_patch_quarantine_audits.json",
    "matched_null_calibration_score_result.json",
    "matched_null_score_inputs.json",
    "matched_null_score_audit.json",
    "memory_separation_claim_evaluation_batch009.json",
    "retrospective_calibration_registry_note.json",
    "prospective_memory_lift_requirement.json",
    "claim_boundary.json",
    "notebooklm_advice_traceability_status.json",
    "carry_forward_blocker_register.json",
    "SHA256SUMS.txt",
]

BATCH010_REQUIRED = [
    "campaign_summary.md",
    "consolidated_state_clean_replication_batch_010.json",
    "status_code_weighting_policy.json",
    "status_code_evidence_inventory.json",
    "status_code_to_weight_map.json",
    "failure_memory_source_marker_map.json",
    "high_pass_source_ranking_filter.json",
    "two_candidate_selection_policy.json",
    "strict_minimum_delta_policy.json",
    "baseline_source_ranking.json",
    "memory_weighted_source_ranking.json",
    "routing_delta_report.json",
    "routing_delta_audit.json",
    "context_selection_delta_report.json",
    "generation_strategy_delta_report.json",
    "high_pass_filter_application.json",
    "masked_or_downranked_context_paths.json",
    "admitted_alternative_paths.json",
    "active_memory_repair_attempt.json",
    "null_ensemble_rerun_results.json",
    "null_ensemble_rerun_summary.json",
    "null_ensemble_memory_exclusion_audit.json",
    "matched_null_score_result_batch010.json",
    "matched_null_score_audit_batch010.json",
    "memory_routing_diagnostic_evaluation_batch010.json",
    "prospective_memory_lift_requirement_update.json",
    "claim_boundary.json",
    "notebooklm_advice_traceability_status.json",
    "carry_forward_blocker_register.json",
    "SHA256SUMS.txt",
]

BATCH003_REQUIRED = [
    "consolidated_state_clean_replication_batch_003.json",
    "matched_null_ensemble_policy.json",
    "matched_null_ensemble_seed_policy.json",
    "matched_null_ensemble_score_definition.json",
    "null_generation_audit.json",
    "memory_enabled_policy.json",
    "memory_disabled_policy.json",
    "challenge_candidate_acquisition_policy.json",
    "challenge_candidate_difficulty_band.json",
    "challenge_candidate_lead_pool.json",
    "challenge_candidate_attempts.json",
    "challenge_candidate_rejection_ledger.json",
    "candidate_verification_attempts.json",
    "verified_challenge_candidates.json",
    "challenge_candidate_admission_decisions.json",
    "repairability_basin_scores_batch003.csv",
    "memory_enabled_run_results.json",
    "null_ensemble_run_results.json",
    "null_ensemble_summary.json",
    "matched_null_ensemble_separation_score_result.json",
    "memory_separation_claim_evaluation.json",
    "repair_successes.json",
    "native_issue_derived_count_separation.json",
    "claim_boundary.json",
    "failure_memory_active_routing_audit.json",
    "failure_memory_marker_usage.json",
    "failure_memory_routing_delta.json",
    "campaign_summary.md",
    "SHA256SUMS.txt",
]

BATCH_REQUIRED = [
    "consolidated_state_clean_replication_batch_002.json",
    "campaign_summary.md",
    "candidate_source_mode_trace.json",
    "lead_pool_intake_report.json",
    "curated_seed_intake_report.json",
    "metadata_probe_attempts.json",
    "issue_derived_attempts.json",
    "environment_resolution_attempts.json",
    "environment_resolution_policy.json",
    "environment_failure_classification.json",
    "dependency_install_logs_manifest.json",
    "candidate_verification_attempts.json",
    "candidate_rejection_ledger.json",
    "verified_candidates.json",
    "repair_attempts.json",
    "repair_successes.json",
    "clean_repair_generation_policy.json",
    "verified_candidate_repair_queue.json",
    "repair_context_capsules.json",
    "patchable_source_subsets.json",
    "source_patch_generation_attempts.json",
    "patch_safety_results.json",
    "target_validation_results.json",
    "duplicate_replay_results.json",
    "no_overreach_regression_results.json",
    "source_context_handoff_audit.json",
    "generation_validation_reconciliation_trace.json",
    "structural_repair_routing_map.json",
    "stage_interface_contract.json",
    "repairability_basin_selection.json",
    "patchable_source_ranking.csv",
    "pre_generation_context_state_lock.json",
    "patch_context_alignment_audit.json",
    "post_patch_constraint_revalidation.json",
    "no_overreach_validation.json",
    "repair_generator_capability_status.json",
    "matched_null_results.json",
    "memory_lift_evaluation.json",
    "baseline_registry_snapshot_before_matched_null.json",
    "proof_chain_lock_for_second_repair.json",
    "second_repair_claim_boundary.json",
    "darker_stdin_filename_pre_repair_replay.json",
    "darker_stdin_filename_semantic_failure_signature.json",
    "darker_stdin_filename_structural_repair_routing_map.json",
    "darker_stdin_filename_patchable_source_subset.json",
    "darker_stdin_filename_pre_generation_context_state_lock.json",
    "darker_stdin_filename_stage_interface_contract.json",
    "failure_memory_weighting_policy.json",
    "failure_memory_status_code_taxonomy.json",
    "arm_a_active_failure_memory_weighting.json",
    "arm_a_failure_memory_weight_trace.json",
    "arm_b_memory_disabled_exclusion_audit.json",
    "arm_b_memory_exclusion_audit.json",
    "failure_memory_weight_delta_report.json",
    "arm_a_pre_generation_context_state_snapshot.json",
    "arm_b_pre_generation_context_state_snapshot.json",
    "arm_a_repair_intent_lock.json",
    "arm_b_repair_intent_lock.json",
    "matched_null_arm_a_memory_enabled_plan.json",
    "matched_null_arm_b_memory_disabled_plan.json",
    "matched_null_arm_a_results.json",
    "matched_null_arm_b_results.json",
    "arm_a_patch.diff",
    "arm_b_patch.diff",
    "arm_a_patch_sha256.txt",
    "arm_b_patch_sha256.txt",
    "arm_a_target_validation.json",
    "arm_b_target_validation.json",
    "arm_a_duplicate_replay.json",
    "arm_b_duplicate_replay.json",
    "arm_a_post_patch_constraint_revalidation.json",
    "arm_b_post_patch_constraint_revalidation.json",
    "arm_a_no_overreach_validation.json",
    "arm_b_no_overreach_validation.json",
    "post_patch_constraint_revalidation_darker_stdin_filename.json",
    "no_overreach_validation_darker_stdin_filename.json",
    "interlock_invariant_revalidation.json",
    "homeostasis_risk_state_matched_null.json",
    "bounded_exploration_budget_matched_null.json",
    "active_probe_escalation_trace.json",
    "matched_null_score_inputs.json",
    "matched_null_score_formula.json",
    "matched_null_score_audit.json",
    "matched_null_separation_score_result.json",
    "memory_lift_claim_evaluation.json",
    "null_generation_audit.json",
    "native_issue_derived_count_separation.json",
    "claim_boundary.json",
    "SHA256SUMS.txt",
]


def blocked_terms() -> list[str]:
    return [
        "chromo" + "somal",
        "TO" + "RUS",
        "TL" + "D",
        "A" + "GI",
        "observer" + "-state",
        "RNA " + "primase",
        "Meta" + "-cell",
        "Klein " + "bottle",
        "Klein " + "twist",
        "Betti" + "-number",
        "cym" + "atics",
        "res" + "onance",
        "recursion" + "-constant",
        "bio" + "logical",
        "meta" + "phorical",
        "OS" + "QN",
        "N" + "\u2248",
        "chro" + "matin",
        "epi" + "genetic",
    ]


def read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def fail(message: str) -> int:
    print(f"FAIL: {message}")
    return 1


def require_files(root: Path, files: list[str]) -> list[str]:
    return [rel for rel in files if not (root / rel).is_file()]


def command_passes(command: list[str]) -> bool:
    completed = subprocess.run(command, text=True, capture_output=True)
    if completed.returncode != 0:
        print(completed.stdout)
        print(completed.stderr)
    return completed.returncode == 0


def load_lead_pool(path: Path = Path("inputs/clean_replication_batch_002_lead_pool.json")) -> dict[str, object]:
    if not path.is_file():
        return {"status": "MISSING", "leads": [], "lead_count": 0}
    data = read_json(path)
    leads = data.get("leads", [])
    return {"status": "PASS", "leads": leads if isinstance(leads, list) else [], "lead_count": len(leads) if isinstance(leads, list) else 0}


def audit_real_acquisition_records(
    lead_pool: dict[str, object],
    metadata_attempts: list[dict[str, object]],
    issue_attempts: list[dict[str, object]],
    candidate_attempts: list[dict[str, object]],
    batch: dict[str, object],
) -> list[str]:
    errors: list[str] = []
    leads = lead_pool.get("leads", [])
    if not isinstance(leads, list):
        leads = []
    native_leads = [
        lead
        for lead in leads
        if isinstance(lead, dict)
        and lead.get("allowed_candidate_class") in {"native", "either"}
        and lead.get("lead_type") in {"repo_metadata", "commit_hint"}
    ]
    if any("py_bugger_issue_65" in json.dumps(item, sort_keys=True) for item in [*leads, *candidate_attempts]):
        errors.append("py_bugger_issue_65 reused as a new lead")
    if not leads and batch.get("exact_blocker") != "clean_replication_batch_002_lead_pool_empty":
        errors.append("lead pool empty without clean_replication_batch_002_lead_pool_empty blocker")
    if metadata_attempts and all(item.get("repo") == "offline_local_metadata_lead_pool" for item in metadata_attempts):
        errors.append("metadata_probe placeholder pool counted as acquisition")
    if issue_attempts and all(item.get("issue_lead") == "offline_local_issue_lead_pool" for item in issue_attempts):
        errors.append("issue_derived placeholder pool counted as acquisition")
    if native_leads and not any(item.get("lead_id") for item in candidate_attempts):
        errors.append("no real lead_id appears in candidate verification attempts")
    if native_leads and not metadata_attempts:
        errors.append("native lead pool present but metadata_probe_attempts empty")
    if metadata_attempts:
        if any(item.get("git_clone_status") == "PASS" for item in metadata_attempts) and not any(item.get("checkout_attempted") is True for item in metadata_attempts):
            errors.append("metadata_probe clone passed but no checkout was attempted")
        if all(item.get("checkout_attempted") is False for item in metadata_attempts) and any(not item.get("blocker") for item in metadata_attempts):
            errors.append("metadata_probe checkout false for every lead without specific blockers")
        if any(item.get("lead_id") and item.get("git_clone_attempted") is not True for item in metadata_attempts):
            errors.append("real metadata lead missing git clone attempt")
    if any(item.get("mode") == "issue_derived" and not item.get("lead_id") for item in candidate_attempts):
        errors.append("issue_derived no-lead placeholder counted as real candidate verification attempt")
    allowed_blockers = {
        "clean_replication_batch_002_lead_pool_empty",
        "metadata_probe_network_unavailable",
        "metadata_probe_no_verified_candidates",
        "metadata_probe_no_verified_candidates_after_environment_resolution",
        "clean_replication_batch_002_no_repair_successes_after_environment_resolution",
        "issue_derived_no_safe_leads",
        "clean_replication_batch_002_no_verified_candidates",
        "environment_dependency_install_failed",
        "environment_dependency_undeclared",
        "environment_editable_install_failed",
        "environment_declared_extra_missing",
        "environment_python_version_incompatible",
        "environment_collection_failed_after_resolution",
        "clean_replication_batch_002_no_repair_successes_after_environment_resolution",
        "clean_repair_no_safe_source_patch_generated",
        "clean_repair_patch_safety_failed",
        "target_validation_failed",
        "duplicate_clean_replay_failed",
        "stage_interface_contract_failed",
        "source_context_handoff_failed",
        "no_patchable_source_subset",
        "repair_generation_ignored_structural_routing",
        "patch_context_alignment_failed",
        "post_patch_constraint_revalidation_failed",
        "no_overreach_new_failure_detected",
        "no_overreach_regression_environment_limited",
    }
    if batch.get("exact_blocker") is None and batch.get("status") == "PASS":
        return errors
    if batch.get("exact_blocker") not in allowed_blockers:
        errors.append(f"unexpected batch002 blocker: {batch.get('exact_blocker')}")
    return errors


def audit_environment_resolution_records(metadata_attempts: list[dict[str, object]], batch: dict[str, object]) -> list[str]:
    errors: list[str] = []
    real_metadata = [item for item in metadata_attempts if item.get("lead_id")]
    for item in real_metadata:
        if item.get("environment_resolution_attempted") is not True:
            errors.append(f"{item.get('lead_id')}: environment_resolution_not_attempted")
        if item.get("environment_resolution_attempted") is True and not item.get("install_strategy_attempts"):
            errors.append(f"{item.get('lead_id')}: install strategy attempts missing")
        if item.get("environment_resolution_attempted") is True and item.get("import_probe_attempted") is not True:
            errors.append(f"{item.get('lead_id')}: import probe not recorded")
        if item.get("collection_attempted") is True and item.get("environment_resolution_attempted") is not True:
            errors.append(f"{item.get('lead_id')}: collection occurred before environment resolution")
        text = json.dumps(item, sort_keys=True)
        if ("ModuleNotFoundError" in text or "No module named" in text) and item.get("environment_resolution_attempted") is not True:
            errors.append(f"{item.get('lead_id')}: ModuleNotFoundError accepted without environment resolution")
        if str(item.get("blocker", "")).startswith("metadata_probe_collection_failed"):
            errors.append(f"{item.get('lead_id')}: old collection blocker used after environment resolution")
        if item.get("environment_resolution_attempted") is True and item.get("blocker") == "metadata_probe_collection_failed":
            errors.append(f"{item.get('lead_id')}: candidate/environment failure not separated")
    allowed_after_environment = {
        "metadata_probe_no_verified_candidates_after_environment_resolution",
        "environment_dependency_install_failed",
        "environment_dependency_undeclared",
        "environment_editable_install_failed",
        "environment_declared_extra_missing",
        "environment_python_version_incompatible",
        "environment_collection_failed_after_resolution",
        "metadata_probe_network_unavailable",
        "clean_replication_batch_002_no_verified_candidates",
        "clean_replication_batch_002_no_repair_successes_after_environment_resolution",
    }
    if real_metadata and all(item.get("environment_resolution_attempted") is True for item in real_metadata):
        if batch.get("exact_blocker") is None and batch.get("status") == "PASS":
            return errors
        if batch.get("exact_blocker") not in allowed_after_environment:
            errors.append(f"batch blocker does not reflect environment-aware acquisition: {batch.get('exact_blocker')}")
    return errors


def audit_repair_generation_records(batch: dict[str, object]) -> list[str]:
    errors: list[str] = []
    verified = read_json(BATCH_DIR / "verified_candidates.json")
    queue = read_json(BATCH_DIR / "verified_candidate_repair_queue.json")
    routing = read_json(BATCH_DIR / "structural_repair_routing_map.json")
    capsules = read_json(BATCH_DIR / "repair_context_capsules.json")
    subsets = read_json(BATCH_DIR / "patchable_source_subsets.json")
    generation = read_json(BATCH_DIR / "source_patch_generation_attempts.json")
    safety = read_json(BATCH_DIR / "patch_safety_results.json")
    validation = read_json(BATCH_DIR / "target_validation_results.json")
    duplicate = read_json(BATCH_DIR / "duplicate_replay_results.json")
    handoff = read_json(BATCH_DIR / "source_context_handoff_audit.json")
    trace = read_json(BATCH_DIR / "generation_validation_reconciliation_trace.json")
    stage_contract = read_json(BATCH_DIR / "stage_interface_contract.json")
    basin = read_json(BATCH_DIR / "repairability_basin_selection.json")
    locks = read_json(BATCH_DIR / "pre_generation_context_state_lock.json")
    alignment = read_json(BATCH_DIR / "patch_context_alignment_audit.json")
    revalidation = read_json(BATCH_DIR / "post_patch_constraint_revalidation.json")
    overreach = read_json(BATCH_DIR / "no_overreach_validation.json")
    capability = read_json(BATCH_DIR / "repair_generator_capability_status.json")
    policy = read_json(BATCH_DIR / "clean_repair_generation_policy.json")
    ranking_csv = BATCH_DIR / "patchable_source_ranking.csv"
    if policy.get("status") != "PASS" or policy.get("fixed_later_gold_pr_patch_content_forbidden") is not True:
        errors.append("clean repair generation policy invalid")
    verified_native = [item for item in verified if item.get("decision") == "verified_native_candidate_pending_repair"]
    if len(verified_native) != 2:
        errors.append("two verified native candidates not preserved")
    if len(queue) != len(verified_native):
        errors.append("repair queue does not contain the verified native candidates")
    queued_ids = {item.get("candidate_id") for item in queue}
    if queued_ids != {"darker_non_ascii_drop_changes", "darker_stdin_filename"}:
        errors.append(f"unexpected repair queue candidate ids: {sorted(queued_ids)}")
    if not ranking_csv.is_file() or "candidate_id,file_path" not in ranking_csv.read_text(encoding="utf-8").splitlines()[0]:
        errors.append("patchable source ranking CSV missing or malformed")
    attempted_count = max(1, len(generation), len(capability))
    for collection, name in [
        (routing, "structural repair routing map"),
        (capsules, "repair context capsules"),
        (subsets, "patchable source subsets"),
        (stage_contract, "stage interface contract"),
        (basin, "repairability basin selection"),
        (locks, "pre-generation context-state lock"),
        (capability, "repair generator capability status"),
    ]:
        if not isinstance(collection, list) or len(collection) < attempted_count:
            errors.append(f"{name} missing for attempted candidates")
    for contract in stage_contract:
        if contract.get("status") != "PASS":
            errors.append(f"{contract.get('candidate_id')}: stage_interface_contract_failed")
    for lock in locks:
        if not lock.get("pre_generation_context_state_lock_hash"):
            errors.append(f"{lock.get('candidate_id')}: context-state lock hash missing")
        if not lock.get("allowed_source_files"):
            errors.append(f"{lock.get('candidate_id')}: context-state lock allowed source files missing")
        attestation = lock.get("forbidden_evidence_attestation", {})
        if any(attestation.get(key) is not False for key in ["fixed_commits_used", "later_commits_used", "pr_patch_contents_used", "gold_patches_used", "issue_solution_comments_used"]):
            errors.append(f"{lock.get('candidate_id')}: forbidden evidence attestation failed")
    for item in routing:
        if item.get("repair_routing_decision") != "admit_patchable_subset":
            errors.append(f"{item.get('candidate_id')}: no_patchable_source_subset")
        if not item.get("patchable_source_subset"):
            errors.append(f"{item.get('candidate_id')}: patchable source subset missing in routing")
    for item in subsets:
        paths = item.get("patchable_source_files", [])
        if item.get("status") != "PASS" or not paths:
            errors.append(f"{item.get('candidate_id')}: patchable source subset failed")
        for path in paths:
            if str(path).startswith(("tests/", "test/", "src/darker/tests/", "configs/", ".github/", "outputs/", "scripts/", "docs/")):
                errors.append(f"{item.get('candidate_id')}: forbidden patchable path {path}")
    generated_ids = {item.get("candidate_id") for item in generation}
    if not generated_ids.issubset(queued_ids):
        errors.append("patch generation occurred for an unverified candidate")
    for item in capability:
        if item.get("generator_invoked") is not True:
            errors.append(f"{item.get('candidate_id')}: clean_repair_generator_not_implemented")
        if item.get("blocker") == "clean_repair_generator_not_implemented":
            errors.append(f"{item.get('candidate_id')}: generator still reported no-op implementation")
    generated = [item for item in generation if item.get("patch_candidate_generated") is True]
    for item in generated:
        if item.get("candidate_id") not in queued_ids:
            errors.append("generated patch for candidate outside repair queue")
        if item.get("patch_sha256") is None:
            errors.append(f"{item.get('candidate_id')}: generated patch missing SHA256")
        for path in item.get("patch_file_paths", []):
            if str(path) not in next((lock.get("allowed_source_files", []) for lock in locks if lock.get("candidate_id") == item.get("candidate_id")), []):
                errors.append(f"{item.get('candidate_id')}: repair_generation_ignored_structural_routing")
    if generated and not safety:
        errors.append("patch generated without patch safety result")
    for item in safety:
        if item.get("status") != "PASS":
            errors.append(f"{item.get('candidate_id')}: clean_repair_patch_safety_failed")
        if item.get("tests_modified") is not False or item.get("support_files_modified") is not False or item.get("config_workflow_registry_audit_modified") is not False:
            errors.append(f"{item.get('candidate_id')}: forbidden file mutation in patch safety")
    if generated and not alignment:
        errors.append("patch generated without patch context alignment audit")
    for item in alignment:
        if item.get("status") != "PASS":
            errors.append(f"{item.get('candidate_id')}: patch_context_alignment_failed")
    for item in validation:
        if item.get("status") == "PASS" and item.get("exit_code") != 0:
            errors.append(f"{item.get('candidate_id')}: target validation PASS without exit status 0")
    for item in duplicate:
        if item.get("status") == "PASS" and (item.get("passes") != 3 or item.get("total") != 3):
            errors.append(f"{item.get('candidate_id')}: duplicate replay PASS without 3/3")
    for item in revalidation:
        if item.get("status") == "PASS" and item.get("same_patch_bytes_across_replays") is not True:
            errors.append(f"{item.get('candidate_id')}: post-patch revalidation missing same patch bytes")
    for item in overreach:
        if item.get("stronger_robustness_claim_allowed") is not False:
            errors.append(f"{item.get('candidate_id')}: no-overreach allowed stronger claim")
        if item.get("new_failures_detected") is not False:
            errors.append(f"{item.get('candidate_id')}: no_overreach_new_failure_detected")
    if generated and not handoff:
        errors.append("source context handoff audit missing for generated patch")
    for item in handoff:
        if not item.get("context_capsule_hash") or not item.get("patchable_subset_hash"):
            errors.append(f"{item.get('verified_candidate_id')}: source_context_handoff_failed")
    for item in trace:
        if item.get("verification_stage_status") != "PASS":
            errors.append(f"{item.get('candidate_id')}: reconciliation trace missing verification PASS")
    return errors


def audit_matched_null_records(batch: dict[str, object]) -> list[str]:
    errors: list[str] = []
    official_repair_artifact = read_json(POST_DIR / "batch002_repair_generation_artifact_verification.json")
    if official_repair_artifact.get("status") != "PASS":
        errors.append("repair-generation artifact verification not PASS")
    if official_repair_artifact.get("actual_sha256") != "64e6e0ec76bf05857aa03f1b5cd0608060e9bb114f1f74981608a3a45710d9b5":
        errors.append("repair-generation artifact SHA mismatch")
    second_summary = read_json(POST_DIR / "second_external_repair_ingest_summary.json")
    if second_summary.get("confirmed_external_native_repair_episode") != "darker_non_ascii_drop_changes":
        errors.append("second external repair ingest summary does not lock darker_non_ascii_drop_changes")
    registry_report = read_json(POST_DIR / "repair_episode_registry_update_report.json")
    if registry_report.get("status") != "PASS" or registry_report.get("candidate_id") != "darker_non_ascii_drop_changes":
        errors.append("second repair registry update report invalid")

    baseline = read_json(BATCH_DIR / "baseline_registry_snapshot_before_matched_null.json")
    proof = read_json(BATCH_DIR / "proof_chain_lock_for_second_repair.json")
    second_claim = read_json(BATCH_DIR / "second_repair_claim_boundary.json")
    if baseline.get("status") != "PASS":
        errors.append("baseline registry snapshot before matched-null missing PASS")
    if proof.get("status") != "PASS" or not proof.get("proof_chain_hash"):
        errors.append("proof-chain lock for second repair invalid")
    if second_claim.get("status") != "PASS" or second_claim.get("stronger_robustness_claim_allowed") is not False:
        errors.append("second repair claim boundary invalid")

    pre_replay = read_json(BATCH_DIR / "darker_stdin_filename_pre_repair_replay.json")
    semantic = read_json(BATCH_DIR / "darker_stdin_filename_semantic_failure_signature.json")
    routing = read_json(BATCH_DIR / "darker_stdin_filename_structural_repair_routing_map.json")
    subset = read_json(BATCH_DIR / "darker_stdin_filename_patchable_source_subset.json")
    lock = read_json(BATCH_DIR / "darker_stdin_filename_pre_generation_context_state_lock.json")
    stage = read_json(BATCH_DIR / "darker_stdin_filename_stage_interface_contract.json")
    if pre_replay.get("status") != "PRE_PATCH_FAILURE_OBSERVED":
        errors.append("darker_stdin_filename pre-repair replay was not reproduced")
    if semantic.get("status") != "PASS" or not semantic.get("semantic_failure_signature_hash"):
        errors.append("darker_stdin_filename semantic failure signature missing")
    if routing.get("repair_routing_decision") != "admit_patchable_subset":
        errors.append("darker_stdin_filename structural routing did not admit source subset")
    if subset.get("status") != "PASS" or "src/darker/config.py" not in subset.get("patchable_source_files", []):
        errors.append("darker_stdin_filename patchable source subset invalid")
    if not lock.get("pre_generation_context_state_lock_hash"):
        errors.append("darker_stdin_filename context-state lock missing")
    if stage.get("status") != "PASS":
        errors.append("darker_stdin_filename stage interface contract failed")

    taxonomy = read_json(BATCH_DIR / "failure_memory_status_code_taxonomy.json")
    arm_a_weight = read_json(BATCH_DIR / "arm_a_active_failure_memory_weighting.json")
    arm_b_exclusion = read_json(BATCH_DIR / "arm_b_memory_disabled_exclusion_audit.json")
    delta = read_json(BATCH_DIR / "failure_memory_weight_delta_report.json")
    if taxonomy.get("status") != "PASS" or not taxonomy.get("codes"):
        errors.append("failure-memory status-code taxonomy invalid")
    if arm_a_weight.get("status") != "PASS":
        errors.append("Arm A active failure-memory weighting missing PASS")
    if arm_a_weight.get("failure_memory_markers_passive") is True and batch.get("preliminary_single_candidate_memory_separation_evidence") is True:
        errors.append("passive memory markers produced preliminary memory separation claim")
    if arm_a_weight.get("failure_memory_markers_passive") is False and not arm_a_weight.get("routing_decisions_affected"):
        errors.append("Arm A weighting marked active without routing effect")
    if arm_b_exclusion.get("status") != "PASS":
        errors.append("Arm B memory exclusion audit failed")
    for forbidden in ["memory_ledger_opened", "successful_patch_bytes_opened", "successful_patch_rationales_opened", "memory_weighted_routing_applied"]:
        if arm_b_exclusion.get(forbidden) is not False:
            errors.append(f"Arm B contamination detected: {forbidden}")
    if delta.get("status") != "PASS":
        errors.append("failure-memory weight delta report invalid")

    arm_a = read_json(BATCH_DIR / "matched_null_arm_a_results.json")
    arm_b = read_json(BATCH_DIR / "matched_null_arm_b_results.json")
    for arm, name in [(arm_a, "Arm A"), (arm_b, "Arm B")]:
        if arm.get("candidate_id") != "darker_stdin_filename":
            errors.append(f"{name} candidate mismatch")
        if arm.get("repo_url") != "https://github.com/akaihola/darker":
            errors.append(f"{name} repo mismatch")
        if arm.get("commit_sha") != "6ecafca023a354fe7d9539d1d20bf10391bdb24a":
            errors.append(f"{name} commit mismatch")
        if arm.get("target_test_path") != "src/darker/tests/test_main_stdin_filename.py":
            errors.append(f"{name} target test mismatch")
        if arm.get("patch_generated") is not True or arm.get("patch_authorized") is not True:
            errors.append(f"{name} patch was not generated and authorized")
        if arm.get("patch_safety", {}).get("status") != "PASS":
            errors.append(f"{name} patch safety failed")
        if arm.get("target_validation_status") != "PASS":
            errors.append(f"{name} target validation failed")
        if arm.get("duplicate_replay_status") != "PASS":
            errors.append(f"{name} duplicate replay failed")
        if arm.get("no_overreach_status") != "PASS":
            errors.append(f"{name} no-overreach failed")
    for path_name in [
        "arm_a_pre_generation_context_state_snapshot.json",
        "arm_b_pre_generation_context_state_snapshot.json",
        "arm_a_repair_intent_lock.json",
        "arm_b_repair_intent_lock.json",
    ]:
        data = read_json(BATCH_DIR / path_name)
        if data.get("status") != "PASS":
            errors.append(f"{path_name} did not PASS")
    for path_name in [
        "arm_a_post_patch_constraint_revalidation.json",
        "arm_b_post_patch_constraint_revalidation.json",
        "arm_a_no_overreach_validation.json",
        "arm_b_no_overreach_validation.json",
    ]:
        data = read_json(BATCH_DIR / path_name)
        if data.get("status") != "PASS":
            errors.append(f"{path_name} did not PASS")
    interlock = read_json(BATCH_DIR / "interlock_invariant_revalidation.json")
    if not isinstance(interlock, list) or not interlock or any(item.get("status") != "PASS" for item in interlock if item):
        errors.append("interlock invariant revalidation failed")
    homeostasis = read_json(BATCH_DIR / "homeostasis_risk_state_matched_null.json")
    budget = read_json(BATCH_DIR / "bounded_exploration_budget_matched_null.json")
    if homeostasis.get("status") != "PASS":
        errors.append("matched-null homeostasis risk state failed")
    if budget.get("status") != "PASS":
        errors.append("matched-null bounded exploration budget failed")
    score_inputs = read_json(BATCH_DIR / "matched_null_score_inputs.json")
    score_formula = read_json(BATCH_DIR / "matched_null_score_formula.json")
    score_audit = read_json(BATCH_DIR / "matched_null_score_audit.json")
    score = read_json(BATCH_DIR / "matched_null_separation_score_result.json")
    if score_inputs.get("status") != "PASS" or score_formula.get("status") != "PASS" or score_audit.get("status") != "PASS":
        errors.append("matched-null score evidence invalid")
    if score.get("matched_null_separation_score") != 0.0:
        errors.append("expected equal-performance matched-null score of 0.0")
    if score.get("preliminary_single_candidate_memory_separation_evidence") is not False:
        errors.append("preliminary memory separation overclaimed")
    memory_claim = read_json(BATCH_DIR / "memory_lift_claim_evaluation.json")
    if memory_claim.get("full_memory_lift_status") != "undemonstrated":
        errors.append("full memory lift overclaimed")
    if memory_claim.get("preliminary_single_candidate_memory_separation_evidence") is not False:
        errors.append("memory lift claim evaluation overclaimed preliminary evidence")
    registry = read_json(Path("configs/external_repair_episode_registry.json"))
    episodes = registry.get("episodes", [])
    if not any(isinstance(item, dict) and item.get("candidate_id") == "darker_stdin_filename" and item.get("scoreable") is True for item in episodes):
        errors.append("darker_stdin_filename missing from repair episode registry")
    if batch.get("full_scoring") != "NOT_RUN/disallowed":
        errors.append("full scoring boundary changed")
    if batch.get("self_maintaining_software") != "false/not_demonstrated":
        errors.append("self-maintaining software overclaim")
    if batch.get("issue_derived_repair_successes_count") != 0:
        errors.append("issue-derived repairs incremented unexpectedly")
    return errors


def audit_phase_a_ingest_records() -> list[str]:
    errors: list[str] = []
    verification = read_json(POST_DIR / "matched_null_artifact_verification.json")
    ingest = read_json(POST_DIR / "third_external_repair_ingest_summary.json")
    equal = read_json(POST_DIR / "equal_performance_memory_claim_boundary.json")
    lessons = read_json(POST_DIR / "matched_null_lessons_learned.json")
    if verification.get("status") != "PASS":
        errors.append("matched-null artifact verification not PASS")
    if verification.get("actual_sha256") != "8124be2c04533b0b22e5136c683bfdf2f457c961baefff8f19c55860df61532d":
        errors.append("matched-null artifact SHA mismatch")
    if verification.get("actual_size_bytes") not in {145764, "145764"}:
        errors.append("matched-null artifact size mismatch")
    if verification.get("unsafe_path_count") != 0 or verification.get("duplicate_path_count") != 0:
        errors.append("matched-null artifact path safety failed")
    if ingest.get("confirmed_external_native_repair_episode") != "darker_stdin_filename":
        errors.append("third external repair ingest summary invalid")
    if equal.get("matched_null_separation_score") != 0.0:
        errors.append("equal-performance boundary score changed")
    if equal.get("preliminary_single_candidate_memory_separation_evidence") is not False:
        errors.append("equal-performance boundary overclaimed memory separation")
    if equal.get("memory_lift") != "undemonstrated_equal_performance":
        errors.append("equal-performance memory status mismatch")
    if lessons.get("status") != "PASS":
        errors.append("matched-null lessons record not PASS")
    batch003 = read_json(POST_DIR / "batch003_memory_challenge_artifact_verification.json")
    diagnosis = read_json(POST_DIR / "batch003_challenge_candidate_failure_diagnosis.json")
    native_issue = read_json(POST_DIR / "native_vs_issue_derived_status_after_batch003.json")
    if batch003.get("status") != "PASS":
        errors.append("batch003 memory-challenge artifact verification not PASS")
    if batch003.get("actual_sha256") != "5bbdd68ff31d4f2311d38c92d553c9aa6499e6c1ddf4bb7054aa4a6d02f6613d":
        errors.append("batch003 artifact SHA mismatch")
    if batch003.get("actual_size_bytes") not in {166649, "166649"}:
        errors.append("batch003 artifact size mismatch")
    if batch003.get("zip_entry_count") != 166:
        errors.append("batch003 artifact entry count mismatch")
    if batch003.get("challenge_candidates_attempted_count") != 3 or batch003.get("challenge_candidates_verified_count") != 0:
        errors.append("batch003 challenge counts mismatch")
    if batch003.get("exact_blocker") != "clean_replication_batch_003_no_verified_challenge_candidate":
        errors.append("batch003 blocker mismatch in official verification")
    if diagnosis.get("matched_null_ensemble_run_status") != "NOT_RUN":
        errors.append("batch003 diagnosis says ensemble ran")
    if diagnosis.get("memory_separation_claimed") is not False:
        errors.append("batch003 diagnosis overclaimed memory separation")
    if native_issue.get("confirmed_external_native_repair_episodes") != 3 or native_issue.get("confirmed_issue_derived_repair_episodes") != 0:
        errors.append("batch003 native/issue-derived carry-forward counts invalid")
    batch004_artifact = read_json(POST_DIR / "batch004_artifact_verification.json")
    batch004_gap = read_json(POST_DIR / "batch004_source_materialization_gap_diagnosis.json")
    issue_gap = read_json(POST_DIR / "batch004_issue_lead_gap_diagnosis.json")
    if batch004_artifact.get("status") != "PASS":
        errors.append("batch004 artifact verification not PASS")
    if batch004_artifact.get("actual_sha256") != "9dcc1fd59c566acf1891ddd62ba667756ed9f5589342d99bbb24a33c1951c64b":
        errors.append("batch004 artifact SHA mismatch")
    if batch004_artifact.get("actual_size_bytes") not in {186032, "186032"}:
        errors.append("batch004 artifact size mismatch")
    if batch004_artifact.get("zip_entry_count") != 200 or batch004_artifact.get("artifact_sha256sums_checked") != 199:
        errors.append("batch004 artifact entry or manifest count mismatch")
    if batch004_artifact.get("native_challenge_leads_attempted_count") != 1 or batch004_artifact.get("native_challenge_candidates_verified_count") != 0:
        errors.append("batch004 native challenge counts mismatch")
    if batch004_artifact.get("issue_derived_leads_attempted_count") != 0 or batch004_artifact.get("issue_derived_candidates_verified_count") != 0:
        errors.append("batch004 issue-derived counts mismatch")
    if batch004_artifact.get("exact_blocker") != "batch004_no_native_or_issue_derived_challenge_candidate_verified":
        errors.append("batch004 blocker mismatch")
    if batch004_gap.get("source_tree_materialized_in_batch004") is not False or batch004_gap.get("corrected_action") != "perform_ephemeral_source_checkout_before_ast_and_node_discovery":
        errors.append("batch004 source materialization gap diagnosis invalid")
    if issue_gap.get("fallback_activated_after_native_failure") is not True or issue_gap.get("issue_derived_lead_count") != 0:
        errors.append("batch004 issue lead gap diagnosis invalid")
    batch008_verification = read_json(POST_DIR / "batch008_declared_precondition_artifact_verification.json")
    fourth = read_json(POST_DIR / "fourth_external_native_repair_ingest_summary.json")
    batch008_gap = read_json(POST_DIR / "batch008_null_ensemble_gap_diagnosis.json")
    batch009_recommendation = read_json(POST_DIR / "batch009_patch_quarantine_recommendation.json")
    if batch008_verification.get("status") != "PASS":
        errors.append("batch008 official artifact verification not PASS")
    if batch008_verification.get("actual_sha256") != "5153354832807c467b7cd097162e5dfb62f22227889a4b61f5b1a6a0e77951f0":
        errors.append("batch008 official artifact SHA mismatch")
    if batch008_verification.get("actual_size") != 305537 or batch008_verification.get("entry_count") != 384:
        errors.append("batch008 official artifact size or entry count mismatch")
    if batch008_verification.get("unsafe_path_count") != 0 or batch008_verification.get("duplicate_path_count") != 0 or batch008_verification.get("pycache_pyc_count") != 0:
        errors.append("batch008 official artifact path/cache safety failed")
    if fourth.get("confirmed_external_native_repair_episode_count") != 4 or fourth.get("issue_derived_repair_episode_count") != 0:
        errors.append("fourth external native repair summary count invalid")
    if fourth.get("patch_sha256") != "a1d68d46fe2a796a0424bd784e8b7edf1145d710df99dd28973d6ab328ad6ea3":
        errors.append("fourth external native repair patch SHA mismatch")
    if batch008_gap.get("null_ensemble_run_count") != 0 or batch008_gap.get("memory_separation_evidence") is not False:
        errors.append("batch008 null ensemble gap diagnosis overclaimed")
    if batch009_recommendation.get("status") != "READY_FOR_BATCH009_RETROSPECTIVE_CALIBRATION":
        errors.append("batch009 patch quarantine recommendation missing")
    batch009_verification = read_json(POST_DIR / "batch009_patch_quarantined_matched_null_artifact_verification.json")
    passive_diagnosis = read_json(POST_DIR / "batch009_passive_memory_diagnosis.json")
    batch010_recommendation = read_json(POST_DIR / "batch010_active_memory_routing_recommendation.json")
    if batch009_verification.get("status") != "PASS":
        errors.append("batch009 artifact verification not PASS")
    if batch009_verification.get("actual_sha256") != "2fb48b3df92ba7aac9b07b6f82d288755209fa6fe868f2ecf18be757b1f3f249":
        errors.append("batch009 artifact SHA mismatch")
    if batch009_verification.get("actual_size") != 325952 or batch009_verification.get("entry_count") != 418:
        errors.append("batch009 artifact size or entry count mismatch")
    if batch009_verification.get("unsafe_path_count") != 0 or batch009_verification.get("duplicate_path_count") != 0 or batch009_verification.get("pycache_pyc_count") != 0:
        errors.append("batch009 artifact path/cache safety failed")
    required_records = batch009_verification.get("required_batch009_records_verified", {})
    if not isinstance(required_records, dict) or not all(required_records.values()):
        errors.append("batch009 required records were not all verified")
    if passive_diagnosis.get("status") != "PASS":
        errors.append("batch009 passive memory diagnosis not PASS")
    if passive_diagnosis.get("patch_quarantine_passed") is not True:
        errors.append("batch009 passive diagnosis missing patch quarantine PASS")
    if passive_diagnosis.get("null_ensemble_run_count") != 5 or passive_diagnosis.get("null_ensemble_failed_count") != 5:
        errors.append("batch009 passive diagnosis null ensemble counts invalid")
    if passive_diagnosis.get("arm_a_patch_generated") is not False or passive_diagnosis.get("arm_a_routing_delta_detected") is not False:
        errors.append("batch009 passive diagnosis overstates Arm A")
    if passive_diagnosis.get("matched_null_score") != 0.0 or passive_diagnosis.get("prospective_memory_lift") != "not_demonstrated":
        errors.append("batch009 passive diagnosis overclaims memory evidence")
    if batch010_recommendation.get("status") != "READY_FOR_BATCH010_ACTIVE_MEMORY_ROUTING_CALIBRATION":
        errors.append("batch010 active routing recommendation missing")
    boundary = batch010_recommendation.get("required_claim_boundary", {})
    if not isinstance(boundary, dict) or boundary.get("full_scoring") != "NOT_RUN/disallowed" or boundary.get("self_maintaining_software") != "false/not_demonstrated":
        errors.append("batch010 recommendation claim boundary invalid")
    return errors


def audit_batch004_records() -> list[str]:
    errors: list[str] = []
    state = read_json(BATCH004_DIR / "consolidated_state_clean_replication_batch_004.json")
    policy = read_json(BATCH004_DIR / "batch004_dual_track_acquisition_policy.json")
    native_policy = read_json(BATCH004_DIR / "native_challenge_acquisition_policy.json")
    issue_policy = read_json(BATCH004_DIR / "issue_derived_harness_policy.json")
    native_leads = read_json(BATCH004_DIR / "native_challenge_lead_pool.json")
    native_attempts = read_json(BATCH004_DIR / "native_challenge_attempts.json")
    native_verified = read_json(BATCH004_DIR / "native_challenge_verified_candidates.json")
    issue_pool = read_json(BATCH004_DIR / "issue_derived_lead_pool.json")
    issue_attempts = read_json(BATCH004_DIR / "issue_derived_attempts.json")
    issue_verified = read_json(BATCH004_DIR / "issue_derived_verified_candidates.json")
    temporal = read_json(BATCH004_DIR / "issue_text_temporal_guard_batch004.json")
    latent = read_json(BATCH004_DIR / "issue_derived_latent_knowledge_risk_disclosure_batch004.json")
    memory_run = read_json(BATCH004_DIR / "memory_enabled_run_results.json")
    null_runs = read_json(BATCH004_DIR / "null_ensemble_run_results.json")
    null_summary = read_json(BATCH004_DIR / "null_ensemble_summary.json")
    score = read_json(BATCH004_DIR / "matched_null_ensemble_separation_score_result.json")
    claim = read_json(BATCH004_DIR / "memory_separation_claim_evaluation.json")
    repairs = read_json(BATCH004_DIR / "repair_successes.json")
    separation = read_json(BATCH004_DIR / "native_issue_derived_count_separation.json")
    boundary = read_json(BATCH004_DIR / "claim_boundary.json")
    risk = read_json(BATCH004_DIR / "homeostasis_risk_state.json")
    budget = read_json(BATCH004_DIR / "bounded_exploration_budget_trace.json")
    context = read_json(BATCH004_DIR / "context_boundary_map.json")
    if policy.get("track_order") != ["native_challenge_acquisition", "issue_derived_ephemeral_reproduction_harness_fallback"]:
        errors.append("batch004 track order invalid")
    if policy.get("issue_derived_fallback_only_after_native_failure") is not True:
        errors.append("issue-derived fallback not gated on native failure")
    if state.get("native_track_attempted_first") is not True or state.get("issue_derived_fallback_activated") is not True:
        errors.append("batch004 did not record native-first then fallback")
    if state.get("exact_blocker") != "batch004_no_native_or_issue_derived_challenge_candidate_verified":
        errors.append("batch004 exact blocker mismatch")
    if set(native_policy.get("already_repaired_candidate_ids_forbidden", [])) != {"py_bugger_issue_65", "darker_non_ascii_drop_changes", "darker_stdin_filename"}:
        errors.append("batch004 repaired-candidate exclusion invalid")
    if native_leads.get("lead_count") != 1:
        errors.append("batch004 native lead pool count invalid")
    if not isinstance(native_attempts, list) or len(native_attempts) != 1:
        errors.append("batch004 native attempts invalid")
    else:
        attempt = native_attempts[0]
        if attempt.get("candidate_id") != "darker_skip_glob_failing_test":
            errors.append("batch004 did not retry darker_skip_glob lead")
        if attempt.get("prior_blocker") != "command_cannot_collect_target":
            errors.append("batch004 native attempt prior blocker invalid")
        required_flags = [
            "environment_resolution_attempted_in_prior_evidence",
            "target_test_file_exists_in_prior_evidence",
            "file_collection_attempted",
            "project_pytest_invocation_considered",
            "safe_pythonpath_layout_considered",
            "ast_node_discovery_attempted",
            "command_cannot_collect_target_finalized_after_improved_collection",
        ]
        for flag in required_flags:
            if attempt.get(flag) is not True:
                errors.append(f"batch004 native attempt missing improved collection flag {flag}")
        if attempt.get("node_level_command_attempted_count", 0) < 1 and attempt.get("node_level_command_safely_blocked") is not True:
            errors.append("batch004 native attempt rejected without node-level attempt or safe block")
        if attempt.get("fixed_later_gold_pr_patch_content_used") is not False:
            errors.append("batch004 native attempt used forbidden patch evidence")
    if native_verified != []:
        errors.append("batch004 should not have native verified candidates")
    if issue_policy.get("increments_native_count") is not False:
        errors.append("issue-derived policy increments native count")
    if issue_policy.get("issue_text_hash_required_if_used") is not True or issue_policy.get("generated_harness_hash_required_if_used") is not True:
        errors.append("issue-derived hash requirements missing")
    if issue_pool.get("lead_count") != 0:
        errors.append("batch004 issue-derived lead pool unexpectedly non-empty")
    if not isinstance(issue_attempts, list) or not issue_attempts:
        errors.append("batch004 issue-derived fallback attempt missing")
    else:
        issue_attempt = issue_attempts[0]
        if issue_attempt.get("fallback_activated_after_native_failure") is not True:
            errors.append("issue-derived fallback not activated after native failure")
        if issue_attempt.get("candidate_class") != "issue_derived_reproduction_candidate":
            errors.append("issue-derived candidate class invalid")
        if issue_attempt.get("harness_generation_attempted") is not False:
            errors.append("issue-derived harness generated without safe lead")
        if issue_attempt.get("issue_text_hash") is not None or issue_attempt.get("generated_harness_hash") is not None:
            errors.append("issue-derived hashes recorded despite no harness")
        if issue_attempt.get("fixed_later_gold_pr_patch_content_used") is not False:
            errors.append("issue-derived attempt used forbidden patch evidence")
    if issue_verified != []:
        errors.append("batch004 should not have issue-derived verified candidates")
    if temporal.get("issue_text_hash_required_if_harness_used") is not True or temporal.get("solution_guidance_forbidden") is not True:
        errors.append("issue temporal guard invalid")
    if latent.get("cryptographic_absence_of_latent_knowledge_claimed") is not False:
        errors.append("latent knowledge disclosure overclaimed")
    if memory_run.get("status") != "NOT_RUN" or null_summary.get("status") != "NOT_RUN" or null_runs != []:
        errors.append("batch004 repair/null ensemble ran without verified candidate")
    if score.get("status") != "NOT_COMPUTED" or score.get("preliminary_single_candidate_memory_separation_evidence") is not False:
        errors.append("batch004 matched-null score overclaimed")
    if claim.get("preliminary_single_candidate_memory_separation_evidence") is not False:
        errors.append("batch004 memory claim overclaimed")
    if repairs != []:
        errors.append("batch004 repair successes should be empty")
    if separation.get("issue_derived_repairs_count_as_native") is not False:
        errors.append("batch004 issue-derived counts as native")
    if boundary.get("full_scoring") != "NOT_RUN/disallowed":
        errors.append("batch004 full scoring changed")
    if boundary.get("self_maintaining_software") != "false/not_demonstrated":
        errors.append("batch004 self-maintaining software overclaim")
    if boundary.get("technical_validation_release_readiness") != "not_ready":
        errors.append("batch004 release readiness overclaim")
    if risk.get("status") != "PASS" or budget.get("status") != "PASS" or context.get("status") != "PASS":
        errors.append("batch004 risk/budget/context records invalid")
    return errors


def audit_batch005_records() -> list[str]:
    errors: list[str] = []
    state = read_json(BATCH005_DIR / "consolidated_state_clean_replication_batch_005.json")
    materialization = read_json(BATCH005_DIR / "source_materialization_log.json")
    policy = read_json(BATCH005_DIR / "source_materialization_policy.json")
    attempts = read_json(BATCH005_DIR / "native_challenge_retry_attempts.json")
    nodes = read_json(BATCH005_DIR / "native_challenge_node_discovery.json")
    collection = read_json(BATCH005_DIR / "native_challenge_collection_attempts.json")
    replay = read_json(BATCH005_DIR / "native_challenge_failure_replay_attempts.json")
    verified = read_json(BATCH005_DIR / "native_challenge_verified_candidates.json")
    targeted = read_json(BATCH005_DIR / "targeted_issue_seed_intake_report.json")
    text_hash = read_json(BATCH005_DIR / "targeted_issue_text_hash.json")
    firewall = read_json(BATCH005_DIR / "targeted_issue_harness_firewall_audit.json")
    context_filter = read_json(BATCH005_DIR / "targeted_issue_source_context_filter_map.json")
    issue_policy = read_json(BATCH005_DIR / "issue_derived_lead_discovery_policy.json")
    issue_pool = read_json(BATCH005_DIR / "issue_derived_lead_pool.json")
    issue_attempts = read_json(BATCH005_DIR / "issue_derived_attempts.json")
    issue_verified = read_json(BATCH005_DIR / "issue_derived_verified_candidates.json")
    memory = read_json(BATCH005_DIR / "memory_enabled_run_results.json")
    null_runs = read_json(BATCH005_DIR / "null_ensemble_run_results.json")
    null_summary = read_json(BATCH005_DIR / "null_ensemble_summary.json")
    score = read_json(BATCH005_DIR / "matched_null_ensemble_separation_score_result.json")
    claim = read_json(BATCH005_DIR / "claim_boundary.json")
    target_filter = read_json(BATCH005_DIR / "target_node_semantic_intent_filter.json")
    target_replay = read_json(BATCH005_DIR / "target_node_replay_selection.json")
    non_intent = read_json(BATCH005_DIR / "non_intent_failure_classification.json")
    source_stack = read_json(BATCH005_DIR / "source_stack_extraction_result.json")
    import_graph = read_json(BATCH005_DIR / "import_graph_extraction_result.json")
    ast_closure = read_json(BATCH005_DIR / "ast_closure_extraction_result.json")
    subset_derivation = read_json(BATCH005_DIR / "patchable_source_subset_derivation.json")
    corrected_capability = read_json(BATCH005_DIR / "repair_generator_capability_status_corrected.json")
    taxonomy = read_json(BATCH005_DIR / "no_patch_reason_taxonomy.json")
    corrected_attempt = read_json(BATCH005_DIR / "corrected_native_repair_attempt.json")
    corrected_null = read_json(BATCH005_DIR / "corrected_null_ensemble_summary.json")
    if policy.get("ephemeral_checkout_required") is not True or policy.get("commit_checkout_exact_only") is not True:
        errors.append("batch005 source materialization policy invalid")
    if materialization.get("workspace_path") != "<ephemeral_root>":
        errors.append("batch005 materialization path not redacted")
    if materialization.get("runtime_workspace_outside_repo") is not True or materialization.get("runtime_workspace_outside_onedrive") is not True:
        errors.append("batch005 materialization workspace boundary invalid")
    if materialization.get("fixed_later_gold_pr_patch_content_used") is not False:
        errors.append("batch005 materialization used forbidden evidence")
    if materialization.get("source_materialized") is not True:
        errors.append("batch005 did not materialize source")
    if materialization.get("commit_sha") != "bd28cdc3e1a56f2d2a6e25d6ca75a7cc41e71f75":
        errors.append("batch005 materialized wrong commit")
    if materialization.get("target_test_path_exists") is not True:
        errors.append("batch005 target test missing after materialization")
    if not materialization.get("environment_files"):
        errors.append("batch005 environment files missing")
    if nodes.get("status") != "PASS" or not nodes.get("nodes"):
        errors.append("batch005 AST/node discovery missing")
    if not isinstance(attempts, list) or len(attempts) != 1:
        errors.append("batch005 native retry attempt missing")
    else:
        attempt = attempts[0]
        if attempt.get("source_materialized") is not True:
            errors.append("batch005 native attempt did not record source materialization")
        if attempt.get("ast_node_discovery_attempted_from_materialized_source") is not True:
            errors.append("batch005 native attempt did not use materialized AST discovery")
        if attempt.get("collection_attempted_from_materialized_source") is not True and materialization.get("source_materialized") is True:
            if attempt.get("blocker") not in {"native_challenge_command_cannot_collect_target_after_materialization", "environment_dependency_install_failed"}:
                errors.append("batch005 collection not attempted without precise blocker")
        if attempt.get("fixed_later_gold_pr_patch_content_used") is not False:
            errors.append("batch005 native attempt used forbidden evidence")
    if not isinstance(collection, list) or not collection:
        errors.append("batch005 collection record missing")
    if target_filter.get("selected_node") != "src/darker/tests/test_main_isort.py::test_isort_respects_skip_glob":
        errors.append("batch005 intended target node was not selected")
    if target_filter.get("status") != "PASS" and any("test_isort_respects_skip_glob" in str(node) for node in nodes.get("nodes", [])):
        errors.append("batch005 target semantic filter failed despite intended node discovery")
    if non_intent.get("primary_failure_source") != "selected_intended_node_only":
        errors.append("batch005 non-intent failures are not separated")
    if taxonomy.get("status") != "PASS" or "clean_repair_no_safe_source_patch_generated" != taxonomy.get("no_safe_patch_blocker"):
        errors.append("batch005 no-patch taxonomy invalid")
    if verified and target_replay.get("status") != "PASS":
        errors.append("batch005 verified native candidate without intended target replay PASS")
    if verified and any(item.get("commit_sha") != materialization.get("commit_sha") for item in verified):
        errors.append("batch005 verified native candidate identity mismatch")
    if not verified and state.get("native_challenge_candidate_verified") is not False:
        errors.append("batch005 native verification state mismatch")
    if verified:
        if source_stack.get("status") != "PASS":
            errors.append("batch005 source stack extraction did not PASS for verified target")
        if import_graph.get("status") != "PASS" and not source_stack.get("project_source_frames"):
            errors.append("batch005 import graph and source stack both missing for verified target")
        if ast_closure.get("status") != "PASS":
            errors.append("batch005 AST closure extraction did not PASS for verified target")
        if source_stack.get("project_source_frames") and subset_derivation.get("status") != "PASS":
            errors.append("batch005 project source frames did not produce a patchable subset")
        if subset_derivation.get("status") == "PASS":
            paths = subset_derivation.get("patchable_source_files", [])
            if not paths:
                errors.append("batch005 patchable source subset PASS without files")
            for path in paths:
                if str(path).startswith(("tests/", "test/", "src/darker/tests/", "configs/", ".github/", "outputs/", "scripts/", "docs/")):
                    errors.append(f"batch005 forbidden corrected patchable path {path}")
            if corrected_capability.get("generator_invoked") is not True:
                errors.append("batch005 generator not invoked after corrected patchable subset")
        if memory.get("patch_generated") is not True and null_runs:
            errors.append("batch005 null ensemble ran without memory-enabled patch success")
        if memory.get("patch_generated") is not True and corrected_null.get("status") != "NOT_RUN":
            errors.append("batch005 corrected null ensemble did not remain NOT_RUN after memory failure")
    else:
        if corrected_attempt.get("status") != "NOT_RUN":
            errors.append("batch005 corrected repair attempt ran without verified native target")
        if corrected_capability.get("generator_invoked") is True:
            errors.append("batch005 corrected generator invoked without verified target")
    if state.get("targeted_issue_seed_present") != targeted.get("targeted_issue_derived_seed_present"):
        errors.append("batch005 targeted issue seed state mismatch")
    if targeted.get("targeted_issue_derived_seed_present") is False and text_hash.get("issue_text_sha256") is not None:
        errors.append("batch005 issue text hash present without seed")
    if firewall.get("forbidden_evidence_used") is not False or firewall.get("generated_harness_classified_as_native_test") is not False:
        errors.append("batch005 targeted harness firewall invalid")
    if targeted.get("targeted_issue_derived_seed_present") and context_filter.get("forbidden_context_used") is not False:
        errors.append("batch005 targeted source context used forbidden context")
    if issue_policy.get("runs_only_after_native_failure") is not True or issue_policy.get("runs_after_targeted_seed_intake") is not True:
        errors.append("batch005 issue discovery policy invalid")
    if state.get("native_challenge_candidate_verified") is False and targeted.get("status") == "NOT_RUN_NO_TARGETED_SEED":
        if state.get("issue_derived_discovery_attempted") is not False:
            errors.append("batch005 claimed issue-derived discovery without targeted seed")
        if issue_attempts:
            errors.append("batch005 issue-derived attempts recorded without targeted seed")
    if issue_verified != []:
        errors.append("batch005 should not verify issue-derived candidate in current evidence")
    if issue_pool.get("lead_count", 0) == 0 and state.get("issue_derived_discovery_attempted") is True:
        rejections = read_json(BATCH005_DIR / "issue_derived_rejection_ledger.json")
        blockers = {item.get("blocker") for item in rejections if isinstance(item, dict)}
        if not blockers & {"issue_derived_no_safe_leads", "issue_derived_discovery_network_unavailable"}:
            errors.append("batch005 zero issue leads without allowed discovery blocker")
    if state.get("confirmed_external_native_repair_episodes") != 3 + int(state.get("repair_successes_count", 0)):
        errors.append("batch005 native repair episode count invalid")
    if state.get("confirmed_issue_derived_repair_episodes") != state.get("additional_issue_derived_repair_feasibility_count"):
        errors.append("batch005 issue-derived count invalid")
    if memory.get("patch_generated") is True and not verified:
        errors.append("batch005 generated patch without verified native candidate")
    if null_summary.get("null_ensemble_success_rate") == 1.0 and score.get("matched_null_ensemble_separation_score") != 0.0:
        errors.append("batch005 null success rate 1.0 did not force score 0")
    if claim.get("full_scoring") != "NOT_RUN/disallowed":
        errors.append("batch005 full scoring changed")
    if claim.get("self_maintaining_software") != "false/not_demonstrated":
        errors.append("batch005 self-maintaining overclaim")
    if claim.get("technical_validation_release_readiness") != "not_ready":
        errors.append("batch005 release readiness overclaim")
    if claim.get("issue_derived_evidence_remains_separate") is not True:
        errors.append("batch005 issue-derived evidence boundary invalid")
    return errors


def audit_batch006_records() -> list[str]:
    errors: list[str] = []
    for name in BATCH006_REQUIRED:
        if not (BATCH006_DIR / name).is_file():
            errors.append(f"batch006 missing required file {name}")
    if errors:
        return errors
    manifest = verify_manifest(BATCH006_DIR)
    if manifest.get("status") != "PASS":
        errors.append(f"batch006 manifest failed: {manifest}")
    state = read_json(BATCH006_DIR / "consolidated_state_clean_replication_batch_006.json")
    policy = read_json(BATCH006_DIR / "bounded_fragment_patch_policy.json")
    plan = read_json(BATCH006_DIR / "fragment_patch_candidate_plan.json")
    candidates = read_json(BATCH006_DIR / "fragment_patch_candidates.json")
    safety = read_json(BATCH006_DIR / "fragment_safety_audits.json")
    seal = read_json(BATCH006_DIR / "fragment_assembly_seal.json")
    interlock = read_json(BATCH006_DIR / "coupled_dependency_interlock_map.json")
    invariants = read_json(BATCH006_DIR / "interlock_invariant_candidates.json")
    dual = read_json(BATCH006_DIR / "dual_projection_consistency_check.json")
    snapshot = read_json(BATCH006_DIR / "pre_generation_context_state_snapshot_batch006.json")
    lock = read_json(BATCH006_DIR / "pre_generation_prompt_lock_batch006.json")
    alignment = read_json(BATCH006_DIR / "patch_context_alignment_audit_batch006.json")
    memory = read_json(BATCH006_DIR / "failure_memory_weighting_trace_batch006.json")
    memory_claim = read_json(BATCH006_DIR / "memory_separation_claim_evaluation_batch006.json")
    proof = read_json(BATCH006_DIR / "proof_chain_lock_batch006.json")
    claim = read_json(BATCH006_DIR / "claim_boundary.json")
    traceability = read_json(BATCH006_DIR / "notebooklm_advice_traceability_status.json")
    blockers = read_json(BATCH006_DIR / "carry_forward_blocker_register.json")
    expected_candidate = "darker_skip_glob_failing_test"
    if state.get("candidate_id") != expected_candidate or plan.get("candidate_id") != expected_candidate:
        errors.append("batch006 candidate identity changed")
    if state.get("commit_sha") != "bd28cdc3e1a56f2d2a6e25d6ca75a7cc41e71f75":
        errors.append("batch006 commit identity changed")
    if policy.get("status") != "PASS" or policy.get("source_only_repair_required") is not True:
        errors.append("batch006 bounded fragment patch policy invalid")
    if int(policy.get("max_fragments", 0)) > 3 or int(policy.get("max_modified_files", 0)) > 3 or int(policy.get("max_changed_lines", 0)) > 50:
        errors.append("batch006 fragment caps too broad")
    if interlock.get("status") != "PASS" or int(interlock.get("admitted_source_count", 0)) < 1:
        errors.append("batch006 interlock map missing admitted source records")
    if invariants.get("status") != "PASS":
        errors.append("batch006 interlock invariant candidates invalid")
    if lock.get("pre_generation_lock_created_before_fragment_bytes") is not True or snapshot.get("patch_bytes_exist_at_lock_time") is not False:
        errors.append("batch006 pre-generation lock ordering invalid")
    if plan.get("status") != "BLOCK" or plan.get("blocker") != "fragment_patch_plan_not_generated":
        errors.append("batch006 fragment plan should block with fragment_patch_plan_not_generated")
    if plan.get("fragment_plan_authorized") is not False:
        errors.append("batch006 fragment plan authorized unexpectedly")
    if candidates.get("fragments") != []:
        errors.append("batch006 generated fragments despite blocked plan")
    if safety.get("status") != "NOT_RUN" or seal.get("status") != "BLOCK":
        errors.append("batch006 safety/assembly status invalid for no-fragment block")
    if seal.get("assembled_patch") or seal.get("assembled_patch_sha256"):
        errors.append("batch006 assembled patch recorded despite block")
    if dual.get("status") != "BLOCK" or dual.get("patch_admissible") is not False:
        errors.append("batch006 dual projection did not block inadmissible patch")
    if alignment.get("status") != "NOT_RUN" or alignment.get("forbidden_evidence_used") is not False:
        errors.append("batch006 alignment should remain NOT_RUN without forbidden evidence")
    if memory.get("failure_memory_markers_passive") is not True:
        errors.append("batch006 failure memory should be passive")
    if memory_claim.get("preliminary_single_candidate_memory_separation_evidence") is not False:
        errors.append("batch006 overclaimed memory separation")
    if state.get("null_ensemble_run_count") != 0:
        errors.append("batch006 null ensemble ran without comparable endpoint")
    if state.get("assembled_patch_generated") is not False or state.get("additional_native_external_repair_acquired") is not False:
        errors.append("batch006 overclaimed repair acquisition")
    if proof.get("status") != "PASS" or proof.get("hash_chain_valid") is not True:
        errors.append("batch006 proof chain invalid")
    if claim.get("full_scoring") != "NOT_RUN/disallowed":
        errors.append("batch006 full scoring boundary changed")
    if claim.get("full_memory_lift_status") != "undemonstrated":
        errors.append("batch006 full memory lift overclaim")
    if claim.get("self_maintaining_software") != "false/not_demonstrated":
        errors.append("batch006 self-maintaining overclaim")
    if traceability.get("status") != "PASS" or traceability.get("silent_completion") is not False:
        errors.append("batch006 traceability status invalid")
    if blockers.get("status") != "PASS" or not blockers.get("blockers"):
        errors.append("batch006 carry-forward blocker register missing")
    optional_patch_outputs = [
        "assembled_patch.diff",
        "assembled_patch_sha256.txt",
        "post_patch_constraint_revalidation_batch006.json",
        "no_overreach_validation_batch006.json",
        "target_validation_result_batch006.json",
        "duplicate_replay_result_batch006.json",
        "null_ensemble_run_results_batch006.json",
        "matched_null_ensemble_separation_score_batch006.json",
    ]
    for name in optional_patch_outputs:
        if (BATCH006_DIR / name).exists():
            errors.append(f"batch006 optional patch-success output present despite no patch: {name}")
    return errors


def audit_batch007_records() -> list[str]:
    errors: list[str] = []
    for name in BATCH007_REQUIRED:
        if not (BATCH007_DIR / name).is_file():
            errors.append(f"batch007 missing required file {name}")
    if errors:
        return errors
    manifest = verify_manifest(BATCH007_DIR)
    if manifest.get("status") != "PASS":
        errors.append(f"batch007 manifest failed: {manifest}")

    state = read_json(BATCH007_DIR / "consolidated_state_clean_replication_batch_007.json")
    policy = read_json(BATCH007_DIR / "target_intent_reachability_policy.json")
    target_map = read_json(BATCH007_DIR / "target_intent_reachability_map.json")
    classification = read_json(BATCH007_DIR / "precondition_failure_classification.json")
    env_policy = read_json(BATCH007_DIR / "environment_precondition_resolution_policy.json")
    metadata = read_json(BATCH007_DIR / "project_metadata_dependency_scan.json")
    extras = read_json(BATCH007_DIR / "declared_extras_scan.json")
    install_matrix = read_json(BATCH007_DIR / "install_strategy_matrix.json")
    attempts = read_json(BATCH007_DIR / "precondition_resolution_attempts.json")
    formatter_probe = read_json(BATCH007_DIR / "formatter_dependency_probe.json")
    entrypoint_probe = read_json(BATCH007_DIR / "entrypoint_probe.json")
    replay_after = read_json(BATCH007_DIR / "target_replay_after_precondition_resolution.json")
    projected = read_json(BATCH007_DIR / "projected_vs_observed_runtime_path.json")
    dissonance = read_json(BATCH007_DIR / "runtime_path_dissonance_report.json")
    trace_policy = read_json(BATCH007_DIR / "trace_feedback_alignment_policy.json")
    trace_map = read_json(BATCH007_DIR / "trace_feedback_alignment_map.json")
    trace_status = read_json(BATCH007_DIR / "trace_feedback_alignment_status.json")
    loop_policy = read_json(BATCH007_DIR / "trace_feedback_loop_policy.json")
    loop_attempts = read_json(BATCH007_DIR / "trace_feedback_loop_attempts.json")
    loop_decision = read_json(BATCH007_DIR / "trace_feedback_loop_final_decision.json")
    dual = read_json(BATCH007_DIR / "dual_projection_recheck_batch007.json")
    source_recheck = read_json(BATCH007_DIR / "source_facing_projection_recheck.json")
    test_recheck = read_json(BATCH007_DIR / "test_facing_projection_recheck.json")
    feedback = read_json(BATCH007_DIR / "precondition_to_source_context_feedback.json")
    plan = read_json(BATCH007_DIR / "fragment_patch_candidate_plan_batch007.json")
    candidates = read_json(BATCH007_DIR / "fragment_patch_candidates_batch007.json")
    safety = read_json(BATCH007_DIR / "fragment_safety_audits_batch007.json")
    seal = read_json(BATCH007_DIR / "fragment_assembly_seal_batch007.json")
    generator = read_json(BATCH007_DIR / "repair_generator_trace_consumption_audit.json")
    null_alignment = read_json(BATCH007_DIR / "null_ensemble_trace_alignment_audit.json")
    ladder = read_json(BATCH007_DIR / "completion_decision_ladder.json")
    retirement = read_json(BATCH007_DIR / "candidate_retirement_decision.json")
    vector = read_json(BATCH007_DIR / "interdependent_gate_status_vector.json")
    system_status = read_json(BATCH007_DIR / "system_interlock_completion_status.json")
    memory = read_json(BATCH007_DIR / "memory_separation_claim_evaluation_batch007.json")
    claim = read_json(BATCH007_DIR / "claim_boundary.json")
    traceability = read_json(BATCH007_DIR / "notebooklm_advice_traceability_status.json")
    proof = read_json(BATCH007_DIR / "proof_chain_lock_batch007.json")

    expected_candidate = "darker_skip_glob_failing_test"
    expected_blocker = "target_precondition_unresolved"
    if state.get("candidate_id") != expected_candidate or target_map.get("candidate_id") != expected_candidate:
        errors.append("batch007 candidate identity changed")
    if policy.get("status") != "PASS" or policy.get("target_behavior_required_before_patch_generation") is not True:
        errors.append("batch007 target-intent policy invalid")
    if target_map.get("runtime_path_classification") != "precondition_failure_before_target_behavior":
        errors.append("batch007 target-intent classification mismatch")
    if target_map.get("target_behavior_reached") is not False or projected.get("target_behavior_reached") is not False:
        errors.append("batch007 target behavior should not be reached")
    if classification.get("source_bug_classification_authorized") is not False:
        errors.append("batch007 authorized source bug classification before target behavior")
    if classification.get("classification") != "entrypoint_resolution_failure":
        errors.append("batch007 precondition classification mismatch")
    if env_policy.get("uses_only_checked_out_project_metadata") is not True or env_policy.get("fixed_later_gold_pr_evidence_used") is not False:
        errors.append("batch007 environment policy invalid")
    if metadata.get("formatter_dependency_declared_as_extra") is not True or extras.get("black_extra_declared") is not True:
        errors.append("batch007 declared formatter dependency evidence missing")
    strategies = install_matrix.get("strategies", [])
    if not isinstance(strategies, list) or not strategies:
        errors.append("batch007 install strategy matrix missing")
    if install_matrix.get("undeclared_dependency_install_used") is not False:
        errors.append("batch007 used undeclared dependency install")
    if not any(item.get("command") == "python -m pip install -e .[black]" and item.get("declared_or_baseline") is True for item in strategies if isinstance(item, dict)):
        errors.append("batch007 black declared extra strategy missing")
    if formatter_probe.get("status") != "BLOCK" or entrypoint_probe.get("status") != "BLOCK":
        errors.append("batch007 formatter/entrypoint probes should block")
    if replay_after.get("status") != "NOT_RUN" or replay_after.get("blocker") != expected_blocker:
        errors.append("batch007 replay after precondition should remain blocked/not run")
    if dissonance.get("status") != "BLOCK" or trace_status.get("aligned_target_behavior_reached") is not False:
        errors.append("batch007 trace-feedback dissonance should block alignment")
    if trace_policy.get("patch_generation_requires") != "aligned_target_behavior_reached":
        errors.append("batch007 trace-feedback policy invalid")
    if trace_map.get("generated_patch_path") is not None or trace_map.get("post_patch_validation_path") is not None:
        errors.append("batch007 trace map recorded patch/validation path despite no patch")
    if loop_policy.get("stop_after_first_mismatch") is not False:
        errors.append("batch007 feedback loop stopped after first mismatch")
    if not isinstance(loop_attempts, list) or len(loop_attempts) < 2:
        errors.append("batch007 feedback loop did not record the allowed next step")
    if loop_decision.get("final_decision") != "candidate_retired_precondition_unresolved":
        errors.append("batch007 feedback loop final decision mismatch")
    rechecks = dual.get("rechecks", [])
    if not isinstance(rechecks, list) or len(rechecks) < 3:
        errors.append("batch007 dual projection recheck was not iterative")
    if dual.get("fragment_plan_authorized") is not False or any(item.get("fragment_plan_authorized") is not False for item in rechecks if isinstance(item, dict)):
        errors.append("batch007 fragment plan authorized despite blocked projection")
    if source_recheck.get("source_repair_point_admissible") is not False or test_recheck.get("target_behavior_reached") is not False:
        errors.append("batch007 projection recheck overclaimed source or target readiness")
    if feedback.get("stale_source_context_reused") is not False:
        errors.append("batch007 reused stale source context after precondition analysis")
    if plan.get("fragment_plan_authorized") is not False or candidates.get("fragments") != []:
        errors.append("batch007 generated fragment candidates without reachability")
    if safety.get("status") != "NOT_RUN" or seal.get("assembled_patch_generated") is not False:
        errors.append("batch007 safety/assembly should remain not run")
    if generator.get("generator_ran") is not False or generator.get("status") != "NOT_RUN":
        errors.append("batch007 repair generator ran without aligned trace")
    if null_alignment.get("null_ensemble_ran") is not False or null_alignment.get("status") != "NOT_RUN":
        errors.append("batch007 null ensemble ran without comparable endpoint")
    if ladder.get("completion_decision") != "candidate_retired_precondition_unresolved":
        errors.append("batch007 completion decision invalid")
    if retirement.get("retired") is not True or retirement.get("blocker") != expected_blocker:
        errors.append("batch007 candidate retirement decision invalid")
    if vector.get("status") != "PASS" or vector.get("downstream_gate_violation") is not False:
        errors.append("batch007 interdependent gate vector invalid")
    gates = vector.get("gates", [])
    if isinstance(gates, list):
        seen_block = False
        for gate in gates:
            status = gate.get("status") if isinstance(gate, dict) else None
            if seen_block and status == "PASS":
                errors.append("batch007 downstream gate passed after upstream block")
                break
            if status in {"BLOCK", "FAILED"}:
                seen_block = True
    if system_status.get("completion_decision") != "candidate_retired_precondition_unresolved":
        errors.append("batch007 system completion status mismatch")
    if memory.get("preliminary_single_candidate_memory_separation_evidence") is not False:
        errors.append("batch007 memory separation overclaim")
    if claim.get("full_scoring") != "NOT_RUN/disallowed":
        errors.append("batch007 full scoring boundary changed")
    if claim.get("full_memory_lift_status") != "undemonstrated":
        errors.append("batch007 memory lift overclaim")
    if claim.get("self_maintaining_software") != "false/not_demonstrated":
        errors.append("batch007 self-maintaining software overclaim")
    if traceability.get("status") != "PASS" or traceability.get("silent_completion") is not False:
        errors.append("batch007 traceability/silent-completion status invalid")
    if proof.get("status") != "PASS" or proof.get("hash_chain_valid") is not True:
        errors.append("batch007 proof chain invalid")
    if state.get("exact_blocker") != expected_blocker:
        errors.append("batch007 exact blocker mismatch")
    if state.get("fragment_generation_authorized") is not False or state.get("assembled_patch_generated") is not False:
        errors.append("batch007 overclaimed patch authorization")
    if state.get("target_validation_status") != "NOT_RUN" or state.get("duplicate_replay_status") != "NOT_RUN":
        errors.append("batch007 validation/replay should remain NOT_RUN")
    if state.get("preliminary_single_candidate_memory_separation_evidence") is not False:
        errors.append("batch007 preliminary memory evidence overclaimed")
    return errors


def audit_batch008_records() -> list[str]:
    errors: list[str] = []
    for name in BATCH008_REQUIRED:
        if not (BATCH008_DIR / name).is_file():
            errors.append(f"batch008 missing required file {name}")
    if errors:
        return errors
    manifest = verify_manifest(BATCH008_DIR)
    if manifest.get("status") != "PASS":
        errors.append(f"batch008 manifest failed: {manifest}")

    artifact = read_json(POST_DIR / "batch007_target_reachability_artifact_verification.json")
    gap = read_json(POST_DIR / "batch007_declared_precondition_gap_diagnosis.json")
    recommendation = read_json(POST_DIR / "batch008_declared_formatter_extra_recommendation.json")
    if artifact.get("status") != "PASS" or artifact.get("artifact_source") != "manual_download_local_file":
        errors.append("batch007 artifact ingest verification missing or not manual")
    if artifact.get("actual_sha256") != "f05c7d4605aaba9e27445ed1de0c770b75df68a3cd173796a47623f945428fc7":
        errors.append("batch007 artifact SHA mismatch")
    if artifact.get("actual_size_bytes") != 278040 or artifact.get("artifact_id") != 7970646051:
        errors.append("batch007 artifact identity mismatch")
    if gap.get("batch007_declared_black_extra_detected") is not True or gap.get("batch007_black_extra_executed") is not False:
        errors.append("batch007 declared-precondition gap not recorded")
    if recommendation.get("recommended_batch") != "clean_replication_batch_008" or recommendation.get("runtime_workspace_required") is not True:
        errors.append("batch008 corrective action missing")

    state = read_json(BATCH008_DIR / "consolidated_state_clean_replication_batch_008.json")
    policy = read_json(BATCH008_DIR / "runtime_workspace_materialization_policy.json")
    materialization = read_json(BATCH008_DIR / "runtime_workspace_materialization_log.json")
    scan = read_json(BATCH008_DIR / "declared_formatter_extra_scan.json")
    installs = read_json(BATCH008_DIR / "declared_formatter_extra_install_attempts.json")
    imports = read_json(BATCH008_DIR / "formatter_import_probe_after_declared_extras.json")
    entrypoint = read_json(BATCH008_DIR / "entrypoint_resolution_after_declared_extras.json")
    replay = read_json(BATCH008_DIR / "target_replay_after_declared_extras.json")
    reachability = read_json(BATCH008_DIR / "target_intent_reachability_after_declared_extras.json")
    dual = read_json(BATCH008_DIR / "dual_projection_recheck_batch008.json")
    trace = read_json(BATCH008_DIR / "trace_feedback_alignment_status_batch008.json")
    source_stack = read_json(BATCH008_DIR / "source_stack_after_declared_extras.json")
    subset = read_json(BATCH008_DIR / "patchable_source_subset_after_declared_extras.json")
    interlock = read_json(BATCH008_DIR / "coupled_dependency_interlock_map_batch008.json")
    dual_consistency = read_json(BATCH008_DIR / "dual_projection_consistency_after_declared_extras.json")
    patch_policy = read_json(BATCH008_DIR / "bounded_fragment_patch_policy_batch008.json")
    fragments = read_json(BATCH008_DIR / "fragment_patch_candidates_batch008.json")
    safety = read_json(BATCH008_DIR / "fragment_safety_audits_batch008.json")
    validation = read_json(BATCH008_DIR / "target_validation_result_batch008.json")
    duplicate = read_json(BATCH008_DIR / "duplicate_replay_result_batch008.json")
    no_overreach = read_json(BATCH008_DIR / "no_overreach_validation_batch008.json")
    proof = read_json(BATCH008_DIR / "proof_chain_lock_batch008.json")
    retirement = read_json(BATCH008_DIR / "candidate_retirement_decision_batch008.json")
    issue_seed = read_json(BATCH008_DIR / "targeted_issue_seed_fallback_batch008.json")
    memory = read_json(BATCH008_DIR / "memory_separation_claim_evaluation_batch008.json")
    traceability = read_json(BATCH008_DIR / "notebooklm_advice_traceability_status.json")
    blockers = read_json(BATCH008_DIR / "carry_forward_blocker_register.json")
    claim = read_json(BATCH008_DIR / "claim_boundary.json")
    patch_text = (BATCH008_DIR / "assembled_patch_batch008.diff").read_text(encoding="utf-8")
    patch_sha = (BATCH008_DIR / "assembled_patch_batch008_sha256.txt").read_text(encoding="utf-8").strip()

    expected_candidate = "darker_skip_glob_failing_test"
    if state.get("candidate_id") != expected_candidate or materialization.get("candidate_id") != expected_candidate:
        errors.append("batch008 candidate identity changed")
    if state.get("commit_sha") != "bd28cdc3e1a56f2d2a6e25d6ca75a7cc41e71f75":
        errors.append("batch008 commit identity changed")
    if policy.get("fixed_later_gold_pr_evidence_forbidden") is not True:
        errors.append("batch008 workspace policy does not forbid fixed/later/gold/PR evidence")
    if materialization.get("status") != "PASS" or materialization.get("workspace_classification") != "workspace_materialized_decision_time_safe":
        errors.append("batch008 runtime workspace materialization did not pass")
    if materialization.get("workspace_outside_live_repo") is not True or materialization.get("workspace_outside_onedrive") is not True:
        errors.append("batch008 workspace location guard failed")
    if materialization.get("target_test_exists") is not True or "pyproject.toml" not in materialization.get("environment_files", []):
        errors.append("batch008 target or environment file missing")
    if materialization.get("fixed_later_gold_pr_evidence_used") is not False or materialization.get("tests_fixtures_expectations_mutated") is not False:
        errors.append("batch008 forbidden evidence or mutation recorded")
    if scan.get("status") != "PASS" or scan.get("black_declared") is not True or scan.get("isort_declared") is not True:
        errors.append("batch008 declared formatter extra scan failed")
    if "pytest>=6.2.0" not in scan.get("declared_target_test_tool_specs", []) or "pytest-kwparametrize>=0.0.3" not in scan.get("declared_target_test_tool_specs", []):
        errors.append("batch008 declared target-test tooling evidence missing")
    attempts = installs.get("attempts", [])
    required_commands = {
        ".[isort]",
        ".[black]",
        ".[isort,black]",
    }
    seen_commands = {
        item.get("command", [])[-1]
        for item in attempts
        if isinstance(item, dict) and isinstance(item.get("command"), list) and item.get("command")
    }
    if installs.get("status") != "PASS" or not required_commands.issubset(seen_commands):
        errors.append("batch008 declared formatter extra installs did not pass")
    if installs.get("undeclared_dependency_install_used") is not False:
        errors.append("batch008 undeclared dependency install used")
    if imports.get("status") != "PASS" or entrypoint.get("status") != "PASS" or entrypoint.get("create_formatter_black_resolves") is not True:
        errors.append("batch008 formatter import or entrypoint probe failed")
    if replay.get("status") != "target_behavior_reached_and_failed":
        errors.append("batch008 pre-patch target replay did not reach intended failing behavior")
    if replay.get("pre_patch") is not True or replay.get("returncode") == 0:
        errors.append("batch008 replay must be failing pre-patch evidence")
    if reachability.get("target_behavior_reached") is not True or reachability.get("fragment_generation_may_run") is not True:
        errors.append("batch008 target reachability did not authorize fragment generation")
    if dual.get("status") != "PASS" or trace.get("status") != "PASS":
        errors.append("batch008 dual projection or trace alignment did not pass")
    if source_stack.get("status") != "PASS" or subset.get("status") != "PASS":
        errors.append("batch008 source stack or patchable subset missing")
    if subset.get("allowed_patchable_files") != ["src/darker/import_sorting.py"]:
        errors.append("batch008 patchable subset changed")
    if interlock.get("status") != "PASS" or dual_consistency.get("status") != "PASS":
        errors.append("batch008 interlock/dual consistency failed")
    if patch_policy.get("status") != "PASS" or int(patch_policy.get("max_final_patches", 0)) != 1:
        errors.append("batch008 patch policy invalid")
    if fragments.get("status") != "PASS" or int(fragments.get("fragment_count", 0)) > 3:
        errors.append("batch008 fragment candidate count invalid")
    if safety.get("status") != "PASS" or safety.get("source_only") is not True or safety.get("non_degenerate") is not True:
        errors.append("batch008 patch safety failed")
    if safety.get("modified_files") != ["src/darker/import_sorting.py"]:
        errors.append("batch008 patch touched unauthorized files")
    if "FileSkipSetting" not in patch_text or "file_path" not in patch_text:
        errors.append("batch008 patch missing expected semantic delta")
    if patch_sha != safety.get("patch_sha256"):
        errors.append("batch008 patch SHA record mismatch")
    if validation.get("status") != "PASS" or validation.get("returncode") != 0:
        errors.append("batch008 target validation failed")
    if duplicate.get("status") != "PASS" or duplicate.get("passes") != 3:
        errors.append("batch008 duplicate replay failed")
    if no_overreach.get("status") != "PASS" or no_overreach.get("returncode") != 0:
        errors.append("batch008 no-overreach validation failed")
    if proof.get("status") != "PASS" or proof.get("hash_chain_valid") is not True:
        errors.append("batch008 proof chain invalid")
    if retirement.get("completion_decision") != "repair_success" or retirement.get("retired") is not False:
        errors.append("batch008 candidate retirement/success decision invalid")
    if issue_seed.get("status") != "NOT_RUN" or issue_seed.get("targeted_issue_seed_present") is not False:
        errors.append("batch008 issue-derived fallback should not run after native success")
    if memory.get("preliminary_single_candidate_memory_separation_evidence") is not False or memory.get("null_ensemble_run_count") != 0:
        errors.append("batch008 memory separation overclaim")
    if traceability.get("status") != "PASS" or traceability.get("silent_completion") is not False:
        errors.append("batch008 traceability invalid")
    if blockers.get("status") != "PASS":
        errors.append("batch008 carry-forward blocker register invalid")
    if claim.get("full_scoring") != "NOT_RUN/disallowed" or claim.get("self_maintaining_software") != "false/not_demonstrated":
        errors.append("batch008 claim boundary changed")
    if claim.get("full_memory_lift_status") != "undemonstrated":
        errors.append("batch008 memory lift overclaim")
    if state.get("additional_native_external_repair_acquired") is not True:
        errors.append("batch008 did not record successful additional native repair")
    if state.get("target_validation_status") != "PASS" or state.get("duplicate_replay_status") != "PASS" or state.get("no_overreach_status") != "PASS":
        errors.append("batch008 final validation statuses are not PASS")
    registry = read_json(Path("configs/external_repair_episode_registry.json"))
    episodes = registry.get("episodes", [])
    registry_entry = next((item for item in episodes if isinstance(item, dict) and item.get("candidate_id") == expected_candidate), None)
    if not registry_entry or registry_entry.get("scoreable") is not True:
        errors.append("batch008 successful repair missing from external repair episode registry")
    elif registry_entry.get("semantic_failure_signature_hash") != state.get("semantic_failure_signature_hash"):
        errors.append("batch008 registry semantic failure signature hash mismatch")
    return errors


def audit_batch009_records() -> list[str]:
    errors: list[str] = []
    for name in BATCH009_REQUIRED:
        if not (BATCH009_DIR / name).is_file():
            errors.append(f"batch009 missing required file {name}")
    if errors:
        return errors
    manifest = verify_manifest(BATCH009_DIR)
    if manifest.get("status") != "PASS":
        errors.append(f"batch009 manifest failed: {manifest}")
    state = read_json(BATCH009_DIR / "consolidated_state_clean_replication_batch_009.json")
    denylist = read_json(BATCH009_DIR / "patch_artifact_denylist.json")
    quarantine = read_json(BATCH009_DIR / "patch_artifact_quarantine_audit.json")
    arm_manifest = read_json(BATCH009_DIR / "arm_a_context_manifest.json")
    null_manifests = read_json(BATCH009_DIR / "null_ensemble_context_manifests.json")
    context = read_json(BATCH009_DIR / "pre_patch_context_reconstruction.json")
    replay = read_json(BATCH009_DIR / "pre_patch_target_replay_batch009.json")
    source_subset = read_json(BATCH009_DIR / "pre_patch_source_subset_batch009.json")
    env_plan = read_json(BATCH009_DIR / "pre_patch_environment_plan_batch009.json")
    arm_policy = read_json(BATCH009_DIR / "arm_a_memory_enabled_policy.json")
    arm_trace = read_json(BATCH009_DIR / "arm_a_failure_memory_weighting_trace.json")
    arm_result = read_json(BATCH009_DIR / "arm_a_repair_generation_result.json")
    null_policy = read_json(BATCH009_DIR / "null_ensemble_policy.json")
    null_results = read_json(BATCH009_DIR / "null_ensemble_run_results.json")
    null_summary = read_json(BATCH009_DIR / "null_ensemble_summary.json")
    null_quarantine = read_json(BATCH009_DIR / "null_ensemble_patch_quarantine_audits.json")
    score_inputs = read_json(BATCH009_DIR / "matched_null_score_inputs.json")
    score = read_json(BATCH009_DIR / "matched_null_calibration_score_result.json")
    score_audit = read_json(BATCH009_DIR / "matched_null_score_audit.json")
    memory = read_json(BATCH009_DIR / "memory_separation_claim_evaluation_batch009.json")
    registry_note = read_json(BATCH009_DIR / "retrospective_calibration_registry_note.json")
    prospective = read_json(BATCH009_DIR / "prospective_memory_lift_requirement.json")
    claim = read_json(BATCH009_DIR / "claim_boundary.json")
    traceability = read_json(BATCH009_DIR / "notebooklm_advice_traceability_status.json")
    denied = set(denylist.get("denylist", []))
    required_denied = {
        "outputs/clean_replication_batch_008/assembled_patch_batch008.diff",
        "outputs/clean_replication_batch_008/assembled_patch_batch008_sha256.txt",
        "outputs/clean_replication_batch_008/fragment_patch_candidates_batch008.json",
        "outputs/clean_replication_batch_008/fragment_safety_audits_batch008.json",
        "outputs/clean_replication_batch_008/proof_chain_lock_batch008.json",
        "outputs/clean_replication_batch_008/target_validation_result_batch008.json",
        "outputs/clean_replication_batch_008/duplicate_replay_result_batch008.json",
    }
    if denylist.get("status") != "PASS" or not required_denied.issubset(denied):
        errors.append("batch009 patch denylist incomplete")
    if quarantine.get("status") != "PASS":
        errors.append("matched_null_patch_quarantine_failed")
    if arm_manifest.get("reads_successful_patch") is not False or arm_manifest.get("reads_patch_rationale") is not False:
        errors.append("arm_a_patch_artifact_contamination_detected")
    for item in null_manifests.get("manifests", []):
        if item.get("uses_failure_memory") is not False:
            errors.append("null_memory_contamination_detected")
        if item.get("reads_successful_patch") is not False or item.get("reads_patch_rationale") is not False:
            errors.append("null_patch_artifact_contamination_detected")
    if context.get("reconstructed_from_source_commit") is not True or context.get("batch008_patch_artifacts_read") is not False:
        errors.append("batch009 pre-patch context not safely reconstructed")
    if replay.get("status") != "target_behavior_reached_and_failed" or replay.get("target_behavior_reached") is not True:
        errors.append("batch009_pre_patch_replay_not_reproduced")
    if source_subset.get("allowed_patchable_files") != ["src/darker/import_sorting.py"]:
        errors.append("batch009 source subset mismatch")
    if env_plan.get("undeclared_dependency_install_allowed") is not False:
        errors.append("batch009 environment plan allows undeclared install")
    if arm_policy.get("successful_batch008_patch_access_allowed") is not False:
        errors.append("arm A policy allows successful patch access")
    if arm_trace.get("routing_delta_detected") is not False or arm_trace.get("failure_memory_markers_passive") is not True:
        errors.append("batch009 passive routing delta changed")
    if arm_result.get("patch_generated") is not False or arm_result.get("patch_artifact_quarantine_passed") is not True:
        errors.append("batch009 arm A result invalid")
    if null_policy.get("size") != 5 or null_policy.get("uses_failure_memory") is not False:
        errors.append("batch009 null policy invalid")
    runs = null_results.get("run_results", [])
    if not isinstance(runs, list) or len(runs) != 5:
        errors.append("batch009 null ensemble size mismatch")
    if any(item.get("patch_generated") is not False for item in runs if isinstance(item, dict)):
        errors.append("batch009 null run generated patch unexpectedly")
    if null_summary.get("null_ensemble_run_count") != 5 or null_summary.get("null_success_rate") != 0.0:
        errors.append("batch009 null summary invalid")
    if null_quarantine.get("all_null_runs_denied_patch_artifacts") is not True or null_quarantine.get("all_null_runs_denied_failure_memory") is not True:
        errors.append("batch009 null quarantine audit invalid")
    if score_inputs.get("quarantine_passed") is not True or score_inputs.get("arms_comparable") is not True:
        errors.append("matched_null_arms_not_comparable")
    if score.get("matched_null_ensemble_separation_score") != 0.0:
        errors.append("batch009 score must be zero for passive routing")
    if score.get("retrospective_single_candidate_memory_separation_diagnostic") is not False:
        errors.append("retrospective_calibration_overclaimed")
    if score_audit.get("retrospective_not_prospective") is not True:
        errors.append("batch009 score audit missing retrospective boundary")
    if memory.get("retrospective_single_candidate_memory_separation_diagnostic") is not False:
        errors.append("batch009 memory separation overclaimed")
    if memory.get("prospective_memory_lift_status") != "not_demonstrated":
        errors.append("prospective_memory_lift_overclaimed")
    if registry_note.get("does_not_add_repair_episode") is not True or registry_note.get("confirmed_external_native_repair_episode_count_remains") != 4:
        errors.append("batch009 registry note increments repair count")
    if prospective.get("fresh_candidate_required") is not True:
        errors.append("batch009 prospective requirement invalid")
    if claim.get("retrospective_calibration_only") is not True or claim.get("full_scoring") != "NOT_RUN/disallowed":
        errors.append("batch009 claim boundary invalid")
    if claim.get("self_maintaining_software") != "false/not_demonstrated":
        errors.append("batch009 self-maintaining overclaim")
    if traceability.get("patch_artifact_quarantine") != "implemented_active":
        errors.append("batch009 traceability missing quarantine")
    if state.get("batch009_adds_repair_episode") is not False or state.get("confirmed_external_native_repair_episode_count") != 4:
        errors.append("batch009 state increments repair count")
    episodes = read_json(Path("configs/external_repair_episode_registry.json")).get("episodes", [])
    matches = [item for item in episodes if isinstance(item, dict) and item.get("candidate_id") == "darker_skip_glob_failing_test"]
    if len(matches) != 1:
        errors.append("batch009 duplicated darker_skip_glob repair episode")
    return errors


def audit_batch010_records() -> list[str]:
    errors: list[str] = []
    for name in BATCH010_REQUIRED:
        if not (BATCH010_DIR / name).is_file():
            errors.append(f"batch010 missing required file {name}")
    if errors:
        return errors
    manifest = verify_manifest(BATCH010_DIR)
    if manifest.get("status") != "PASS":
        errors.append(f"batch010 manifest failed: {manifest}")
    state = read_json(BATCH010_DIR / "consolidated_state_clean_replication_batch_010.json")
    policy = read_json(BATCH010_DIR / "status_code_weighting_policy.json")
    inventory = read_json(BATCH010_DIR / "status_code_evidence_inventory.json")
    weight_map = read_json(BATCH010_DIR / "status_code_to_weight_map.json")
    source_marker = read_json(BATCH010_DIR / "failure_memory_source_marker_map.json")
    high_pass_policy = read_json(BATCH010_DIR / "high_pass_source_ranking_filter.json")
    two_candidate = read_json(BATCH010_DIR / "two_candidate_selection_policy.json")
    delta_policy = read_json(BATCH010_DIR / "strict_minimum_delta_policy.json")
    baseline = read_json(BATCH010_DIR / "baseline_source_ranking.json")
    weighted = read_json(BATCH010_DIR / "memory_weighted_source_ranking.json")
    delta = read_json(BATCH010_DIR / "routing_delta_report.json")
    delta_audit = read_json(BATCH010_DIR / "routing_delta_audit.json")
    context_delta = read_json(BATCH010_DIR / "context_selection_delta_report.json")
    generation_delta = read_json(BATCH010_DIR / "generation_strategy_delta_report.json")
    filter_application = read_json(BATCH010_DIR / "high_pass_filter_application.json")
    masked = read_json(BATCH010_DIR / "masked_or_downranked_context_paths.json")
    alternatives = read_json(BATCH010_DIR / "admitted_alternative_paths.json")
    active = read_json(BATCH010_DIR / "active_memory_repair_attempt.json")
    null_results = read_json(BATCH010_DIR / "null_ensemble_rerun_results.json")
    null_summary = read_json(BATCH010_DIR / "null_ensemble_rerun_summary.json")
    null_exclusion = read_json(BATCH010_DIR / "null_ensemble_memory_exclusion_audit.json")
    score = read_json(BATCH010_DIR / "matched_null_score_result_batch010.json")
    score_audit = read_json(BATCH010_DIR / "matched_null_score_audit_batch010.json")
    diagnostic = read_json(BATCH010_DIR / "memory_routing_diagnostic_evaluation_batch010.json")
    prospective = read_json(BATCH010_DIR / "prospective_memory_lift_requirement_update.json")
    claim = read_json(BATCH010_DIR / "claim_boundary.json")
    traceability = read_json(BATCH010_DIR / "notebooklm_advice_traceability_status.json")
    carry = read_json(BATCH010_DIR / "carry_forward_blocker_register.json")
    blocker = "active_memory_routing_delta_not_established"
    if policy.get("status") != "PASS" or policy.get("status_codes_affect_routing_only_when_mapped_to_evidence") is not True:
        errors.append("status_code_weighting_policy_missing")
    if policy.get("unmapped_codes_do_not_change_weights") is not True or policy.get("patch_bytes_and_rationale_forbidden_as_memory") is not True:
        errors.append("status code weighting policy weakens quarantine")
    records = inventory.get("records", [])
    if inventory.get("status") != "PASS" or not isinstance(records, list) or len(records) < 3:
        errors.append("status-code evidence inventory invalid")
    for record in records if isinstance(records, list) else []:
        if not isinstance(record, dict):
            errors.append("status-code evidence record malformed")
            continue
        for field in ["status_code", "candidate_id", "evidence_path", "evidence_sha256", "reason"]:
            if not record.get(field):
                errors.append(f"status-code evidence missing {field}")
        if record.get("decision_time_safe") is not True:
            errors.append("status-code evidence not decision-time safe")
    weights = weight_map.get("weights", [])
    if weight_map.get("status") != "PASS" or not isinstance(weights, list):
        errors.append("status code weight map invalid")
    for weight in weights if isinstance(weights, list) else []:
        if not isinstance(weight, dict):
            errors.append("weight record malformed")
            continue
        for field in ["status_code", "source_path", "evidence_path", "evidence_sha256", "reason", "weight_class"]:
            if not weight.get(field):
                errors.append(f"weight missing {field}")
    unmapped = weight_map.get("unmapped_records", [])
    excluded = weight_map.get("excluded_records", [])
    if source_marker.get("unmapped_status_count") != len(unmapped) or source_marker.get("excluded_patch_detail_count") != len(excluded):
        errors.append("failure memory source marker counts mismatch")
    if weight_map.get("no_relevant_memory_features_available") is not True or source_marker.get("no_relevant_memory_features_available") is not True:
        errors.append("no_relevant_memory_features_available not recorded")
    if not any(isinstance(item, dict) and item.get("unmapped_reason") == "no_legal_source_context_feature" for item in unmapped):
        errors.append("status_code_evidence_unmapped")
    if not any(isinstance(item, dict) and item.get("exclusion_reason") == "patch_detail_quarantine" for item in excluded):
        errors.append("high_pass_filter_uses_forbidden_patch_memory")
    if baseline.get("status") != "PASS" or weighted.get("status") != "PASS":
        errors.append("source ranking outputs invalid")
    if baseline.get("ranking_hash") != state.get("baseline_source_ranking_hash"):
        errors.append("baseline source ranking hash mismatch")
    if weighted.get("ranking_hash") != state.get("memory_weighted_source_ranking_hash"):
        errors.append("memory-weighted source ranking hash mismatch")
    if delta_policy.get("status") != "PASS" or delta_policy.get("metadata_only_delta_rejected") is not True:
        errors.append("strict minimum-delta policy invalid")
    if delta.get("routing_delta_detected") is not False or delta.get("blocker") != blocker:
        errors.append("routing delta report should block without measurable delta")
    if delta.get("routing_delta_reason_codes") != []:
        errors.append("forced_routing_delta_without_evidence")
    if delta_audit.get("status") != "PASS" or delta_audit.get("routing_delta_detected") is not False or delta_audit.get("forced_routing_delta_without_evidence") is not False:
        errors.append("routing delta audit invalid")
    if context_delta.get("context_changed") is not False or generation_delta.get("generation_strategy_changed") is not False:
        errors.append("context or generation delta was forced")
    if high_pass_policy.get("status") != "PASS" or high_pass_policy.get("forbidden_patch_memory_excluded") is not True:
        errors.append("high-pass source ranking policy invalid")
    admitted = filter_application.get("admitted", [])
    if filter_application.get("status") != "PASS" or not isinstance(admitted, list) or not admitted:
        errors.append("high_pass_filter_no_legal_source_remaining")
    if masked.get("status") != "PASS" or alternatives.get("status") != "PASS":
        errors.append("high-pass filter application records invalid")
    selection = two_candidate.get("selection", {})
    if two_candidate.get("status") != "PASS" or not isinstance(selection, dict) or not selection.get("primary_route"):
        errors.append("two-candidate selection missing primary route")
    if active.get("patch_generation_authorized") is not False or active.get("patch_generated") is not False:
        errors.append("routing delta false did not block memory-enabled patch authorization")
    if active.get("blocker") != blocker:
        errors.append("active memory repair attempt blocker mismatch")
    if (BATCH010_DIR / "active_memory_patch.diff").exists() or (BATCH010_DIR / "active_memory_patch_sha256.txt").exists():
        errors.append("active memory patch artifact exists despite blocked routing delta")
    if null_results.get("status") != "NOT_RUN" or null_summary.get("null_ensemble_run_count") != 0:
        errors.append("null ensemble reran without active routing delta")
    if null_exclusion.get("status") != "PASS" or null_exclusion.get("null_ensemble_read_failure_memory") is not False or null_exclusion.get("null_ensemble_read_patch_artifacts") is not False:
        errors.append("null ensemble memory exclusion audit invalid")
    if score.get("matched_null_ensemble_separation_score") != 0.0 or score.get("routing_delta_detected") is not False:
        errors.append("Batch010 matched-null score must remain zero without routing delta")
    if score_audit.get("retrospective_not_prospective") is not True or score_audit.get("overclaim_detected") is not False:
        errors.append("matched-null score audit overclaimed")
    if diagnostic.get("retrospective_single_candidate_memory_routing_diagnostic") is not False or diagnostic.get("memory_separation_evidence") is not False:
        errors.append("retrospective_diagnostic_overclaimed")
    if prospective.get("status") != "PASS" or prospective.get("fresh_candidate_required") is not True or prospective.get("full_memory_lift_claim_allowed") is not False:
        errors.append("prospective_memory_lift_overclaimed")
    if claim.get("prospective_memory_lift") != "not_demonstrated" or claim.get("full_memory_lift_claimed") is not False:
        errors.append("prospective memory lift claim boundary invalid")
    if claim.get("full_scoring") != "NOT_RUN/disallowed" or claim.get("self_maintaining_software") != "false/not_demonstrated":
        errors.append("Batch010 claim boundary overclaimed")
    if state.get("status") != "BLOCK" or state.get("exact_blocker") != blocker:
        errors.append("Batch010 state blocker mismatch")
    if state.get("active_memory_patch_generated") is not False or state.get("batch010_adds_repair_episode") is not False:
        errors.append("Batch010 state increments repair or patch generation")
    if state.get("confirmed_native_repair_episode_count") != 4:
        errors.append("Batch010 repair episode count changed")
    if traceability.get("failure_memory_weighting") != "implemented_partial" or traceability.get("failure_memory_weighting_blocker") != blocker:
        errors.append("Batch010 traceability overstates failure-memory weighting")
    if traceability.get("strict_minimum_delta_routing") != "implemented_active":
        errors.append("Batch010 traceability missing strict minimum-delta routing")
    blockers = carry.get("blockers", [])
    if carry.get("status") != "PASS" or not any(isinstance(item, dict) and item.get("blocker") == blocker for item in blockers):
        errors.append("Batch010 carry-forward blocker missing")
    episodes = read_json(Path("configs/external_repair_episode_registry.json")).get("episodes", [])
    matches = [item for item in episodes if isinstance(item, dict) and item.get("candidate_id") == "darker_skip_glob_failing_test"]
    if len(matches) != 1:
        errors.append("Batch010 duplicated darker_skip_glob repair episode")
    return errors


def audit_batch003_records() -> list[str]:
    errors: list[str] = []
    state = read_json(BATCH003_DIR / "consolidated_state_clean_replication_batch_003.json")
    policy = read_json(BATCH003_DIR / "matched_null_ensemble_policy.json")
    seed_policy = read_json(BATCH003_DIR / "matched_null_ensemble_seed_policy.json")
    score_definition = read_json(BATCH003_DIR / "matched_null_ensemble_score_definition.json")
    null_audit = read_json(BATCH003_DIR / "null_generation_audit.json")
    mem_enabled = read_json(BATCH003_DIR / "memory_enabled_policy.json")
    mem_disabled = read_json(BATCH003_DIR / "memory_disabled_policy.json")
    acquisition = read_json(BATCH003_DIR / "challenge_candidate_acquisition_policy.json")
    difficulty = read_json(BATCH003_DIR / "challenge_candidate_difficulty_band.json")
    lead_pool = read_json(BATCH003_DIR / "challenge_candidate_lead_pool.json")
    attempts = read_json(BATCH003_DIR / "challenge_candidate_attempts.json")
    verified = read_json(BATCH003_DIR / "verified_challenge_candidates.json")
    admissions = read_json(BATCH003_DIR / "challenge_candidate_admission_decisions.json")
    memory_run = read_json(BATCH003_DIR / "memory_enabled_run_results.json")
    null_runs = read_json(BATCH003_DIR / "null_ensemble_run_results.json")
    null_summary = read_json(BATCH003_DIR / "null_ensemble_summary.json")
    score = read_json(BATCH003_DIR / "matched_null_ensemble_separation_score_result.json")
    claim = read_json(BATCH003_DIR / "memory_separation_claim_evaluation.json")
    repair_successes = read_json(BATCH003_DIR / "repair_successes.json")
    separation = read_json(BATCH003_DIR / "native_issue_derived_count_separation.json")
    boundary = read_json(BATCH003_DIR / "claim_boundary.json")
    routing_audit = read_json(BATCH003_DIR / "failure_memory_active_routing_audit.json")
    marker_usage = read_json(BATCH003_DIR / "failure_memory_marker_usage.json")
    routing_delta = read_json(BATCH003_DIR / "failure_memory_routing_delta.json")
    if policy.get("status") != "PASS" or int(policy.get("null_ensemble_size", 0)) < 5:
        errors.append("matched-null ensemble policy invalid")
    if seed_policy.get("status") != "PASS" or len(seed_policy.get("seeds", [])) < 5:
        errors.append("matched-null seed policy invalid")
    for seed in seed_policy.get("seeds", []):
        if seed.get("memory_enabled") is not False:
            errors.append("null ensemble seed is not memory-disabled")
        if seed.get("candidate_commit_command_environment_patch_caps_changed") is not False:
            errors.append("null ensemble seed changed runtime invariants")
    if null_audit.get("status") != "PASS":
        errors.append("null generation audit failed")
    if mem_enabled.get("successful_patch_bytes_read") is not False or mem_enabled.get("prior_patches_copied") is not False:
        errors.append("memory-enabled policy allows prior patch leakage")
    if mem_disabled.get("may_read_failure_memory_weight_ledger") is not False:
        errors.append("memory-disabled policy can read memory ledger")
    if score_definition.get("full_memory_lift_claim_allowed") is not False:
        errors.append("score definition allows full memory-lift claim")
    forbidden_reuse = {"py_bugger_issue_65", "darker_non_ascii_drop_changes", "darker_stdin_filename"}
    if set(acquisition.get("candidate_ids_forbidden_as_new", [])) != forbidden_reuse:
        errors.append("batch003 forbidden candidate reuse set invalid")
    if any(item.get("candidate_id") in forbidden_reuse for item in attempts):
        errors.append("repaired candidate reused in batch003 attempts")
    if any(item.get("candidate_id") in forbidden_reuse for item in admissions):
        errors.append("repaired candidate reused in batch003 admissions")
    if lead_pool.get("lead_count") != len(attempts):
        errors.append("challenge lead pool count does not align with attempts")
    if difficulty.get("status") != "PASS" or not difficulty.get("records"):
        errors.append("challenge difficulty-band records missing")
    if len(admissions) != len(attempts):
        errors.append("admission decisions do not align with attempts")
    if verified:
        errors.append("batch003 verified a challenge candidate but repair experiment records are still NOT_RUN")
    if state.get("exact_blocker") != "clean_replication_batch_003_no_verified_challenge_candidate":
        errors.append("batch003 blocker mismatch")
    if memory_run.get("status") != "NOT_RUN" or null_summary.get("status") != "NOT_RUN":
        errors.append("batch003 experiment ran without a verified challenge candidate")
    if null_runs != []:
        errors.append("null ensemble run results should be empty when blocked before repair experiment")
    if score.get("status") != "NOT_COMPUTED" or score.get("preliminary_single_candidate_memory_separation_evidence") is not False:
        errors.append("batch003 score overclaimed or computed without comparable runs")
    if claim.get("preliminary_single_candidate_memory_separation_evidence") is not False:
        errors.append("batch003 claim evaluation overclaimed preliminary evidence")
    if claim.get("memory_lift") != "undemonstrated_equal_performance":
        errors.append("batch003 memory status mismatch")
    if repair_successes != []:
        errors.append("batch003 repair successes must be empty when no challenge candidate verifies")
    if separation.get("issue_derived_repairs_count_as_native") is not False:
        errors.append("issue-derived count separation invalid")
    if boundary.get("full_scoring") != "NOT_RUN/disallowed":
        errors.append("batch003 full scoring boundary changed")
    if boundary.get("self_maintaining_software") != "false/not_demonstrated":
        errors.append("batch003 self-maintaining software overclaim")
    if boundary.get("technical_validation_release_readiness") != "not_ready":
        errors.append("batch003 release readiness overclaim")
    if routing_audit.get("status") != "PASS" or marker_usage.get("memory_ledger_loaded") is not True:
        errors.append("failure-memory active routing audit invalid")
    if routing_delta.get("routing_delta_active") is not False or routing_delta.get("blocker") != "no_relevant_failure_memory_available":
        errors.append("batch003 routing delta should be passive without a verified challenge candidate")
    csv_header = (BATCH003_DIR / "repairability_basin_scores_batch003.csv").read_text(encoding="utf-8").splitlines()[0]
    if "repairability_score" not in csv_header or "admission_decision" not in csv_header:
        errors.append("batch003 repairability CSV malformed")
    return errors


def public_language_hits() -> list[str]:
    paths = [
        Path("README.md"),
        Path("docs/current_status.md"),
        Path("docs/capability_inventory.md"),
        Path("docs/claim_boundaries.md"),
        Path("docs/public_release_readiness.md"),
        Path("docs/technical_validation_gap_report.md"),
        Path("docs/replication_protocol.md"),
        Path("docs/evidence_model.md"),
        Path("docs/operational_gate_matrix.md"),
        Path("docs/notebooklm_advice_traceability.md"),
        Path("configs/operational_gate_matrix.json"),
        Path("configs/notebooklm_advice_traceability_matrix.json"),
        Path("configs/clean_replication_batch_003.json"),
        Path("configs/clean_replication_batch_004.json"),
        Path("configs/clean_replication_batch_005.json"),
        Path("configs/clean_replication_batch_006.json"),
        Path("configs/clean_replication_batch_007.json"),
        Path("configs/clean_replication_batch_008.json"),
        Path("configs/clean_replication_batch_009.json"),
        Path("configs/clean_replication_batch_010.json"),
        Path("controllergate/core/failure_memory.py"),
        Path("controllergate/core/status_code_weighting.py"),
        Path("controllergate/core/source_ranking.py"),
        Path("controllergate_v1_7_beta/reports/critic_review_package/shareable_summary.md"),
        Path(".github/workflows/post_v2_37_hardening_and_batch002.yml"),
    ]
    paths.extend(sorted(BATCH010_DIR.glob("*.json")))
    paths.extend(sorted(BATCH010_DIR.glob("*.md")))
    hits: list[str] = []
    for path in paths:
        if not path.is_file():
            hits.append(f"missing:{path.as_posix()}")
            continue
        text = path.read_text(encoding="utf-8")
        for term in blocked_terms():
            if term in text:
                hits.append(f"{path.as_posix()}:{term}")
    return hits


REQUIRED_NOTEBOOKLM_ADVICE_IDS = {
    "artifact_byte_custody",
    "workspace_transport_integrity",
    "external_candidate_registry",
    "baseline_registry_snapshot",
    "semantic_failure_signature",
    "structural_navigation_map",
    "active_probe_router",
    "candidate_admission_decision_map",
    "coupled_dependency_projection_map",
    "interlock_invariant_map",
    "target_intent_reachability_gate",
    "formatter_dependency_precondition_resolution",
    "declared_precondition_materialization",
    "trace_feedback_alignment_gate",
    "dual_projection_recheck",
    "issue_derived_harness",
    "issue_text_temporal_guard",
    "issue_derived_latent_risk",
    "matched_null_comparison_arms",
    "matched_null_ensemble",
    "active_failure_memory_routing",
    "high_pass_source_ranking_filter",
    "two_candidate_selection_policy",
    "strict_minimum_delta_routing",
    "prospective_memory_lift_requirement",
    "failure_memory_weighting",
    "duplicate_clean_replay",
    "no_overreach_validation",
    "bounded_micro_reversal",
    "bounded_exploration_budget",
    "execution_environment_normalization",
    "context_boundary_pinning",
    "public_claim_boundary_audit",
    "bugsinpy_global_block",
    "cryptographic_evidence_ledger_sealing",
    "public_release_readiness_gate",
    "v3_readiness_gate",
}


def audit_notebooklm_traceability_records() -> list[str]:
    errors: list[str] = []
    matrix_path = Path("configs/notebooklm_advice_traceability_matrix.json")
    doc_path = Path("docs/notebooklm_advice_traceability.md")
    if not matrix_path.is_file():
        return ["notebooklm traceability matrix missing"]
    if not doc_path.is_file():
        errors.append("notebooklm traceability doc missing")
    matrix = read_json(matrix_path)
    entries = matrix.get("entries", [])
    if not isinstance(entries, list):
        return ["notebooklm traceability entries malformed"]
    by_id = {entry.get("advice_id"): entry for entry in entries if isinstance(entry, dict)}
    missing = sorted(REQUIRED_NOTEBOOKLM_ADVICE_IDS - set(by_id))
    if missing:
        errors.append(f"missing notebooklm advice entries: {missing}")
    operational = read_json(Path("configs/operational_gate_matrix.json"))
    gate_names = {str(gate.get("neutral_gate_name")) for gate in operational.get("gates", []) if isinstance(gate, dict)}
    crosscheck = read_json(BATCH005_DIR / "operational_gate_matrix_crosscheck.json")
    carry = read_json(BATCH005_DIR / "carry_forward_blocker_register.json")
    no_silent = read_json(BATCH005_DIR / "no_silent_completion_audit.json")
    status = read_json(BATCH005_DIR / "notebooklm_advice_traceability_status.json")
    if crosscheck.get("status") != "PASS":
        errors.append("notebooklm_advice_traceability_gap")
    if no_silent.get("status") != "PASS":
        errors.append("gate_marked_active_without_evidence")
    if status.get("status") != "PASS":
        errors.append("notebooklm traceability status not PASS")
    carry_by_id = {item.get("advice_id"): item for item in carry if isinstance(item, dict)}
    for advice_id, entry in by_id.items():
        if not entry.get("status"):
            errors.append(f"{advice_id}: missing status")
        if not entry.get("public_engineering_name"):
            errors.append(f"{advice_id}: missing public engineering name")
        if entry.get("status") == "implemented_active":
            for field in [
                "current_repo_mechanism",
                "required_outputs",
                "required_modules_or_scripts",
                "required_audit_assertions",
                "blocker_if_missing",
                "evidence_paths",
            ]:
                if not entry.get(field):
                    errors.append(f"{advice_id}: active entry missing {field}")
        if entry.get("status") != "implemented_active":
            if not carry_by_id.get(advice_id):
                errors.append(f"{advice_id}: deferred_gate_missing_carry_forward_blocker")
            elif not carry_by_id[advice_id].get("next_allowed_lane") or not carry_by_id[advice_id].get("blocker"):
                errors.append(f"{advice_id}: carry-forward blocker incomplete")
        if entry.get("operational_gate_name") not in gate_names and entry.get("status") not in {"deferred_with_blocker", "rejected_with_reason"}:
            errors.append(f"{advice_id}: missing operational gate cross-reference")
    issue_entry = by_id.get("issue_derived_harness", {})
    batch005_state = read_json(BATCH005_DIR / "consolidated_state_clean_replication_batch_005.json")
    if (
        batch005_state.get("issue_derived_candidate_verified") is not True
        and issue_entry.get("status") == "implemented_active"
    ):
        errors.append("issue-derived harness over-marked as active")
    memory_entry = by_id.get("failure_memory_weighting", {})
    if memory_entry.get("status") == "implemented_active":
        delta = read_json(BATCH_DIR / "arm_a_active_failure_memory_weighting.json") if (BATCH_DIR / "arm_a_active_failure_memory_weighting.json").is_file() else {}
        if delta.get("failure_memory_markers_passive") is not False:
            errors.append("failure-memory weighting over-marked as active without routing delta")
    for path in [
        Path("README.md"),
        Path("docs/current_status.md"),
        Path("docs/capability_inventory.md"),
        Path("docs/public_release_readiness.md"),
        Path("docs/technical_validation_gap_report.md"),
        Path("docs/operational_gate_matrix.md"),
    ]:
        text = path.read_text(encoding="utf-8")
        if "Current operational gate status" not in text:
            errors.append(f"{path.as_posix()}: public_docs_gate_status_mismatch")
    return errors


def main() -> int:
    missing = (
        require_files(POST_DIR, POST_REQUIRED)
        + require_files(BATCH_DIR, BATCH_REQUIRED)
        + require_files(BATCH003_DIR, BATCH003_REQUIRED)
        + require_files(BATCH004_DIR, BATCH004_REQUIRED)
        + require_files(BATCH005_DIR, BATCH005_REQUIRED)
        + require_files(BATCH006_DIR, BATCH006_REQUIRED)
        + require_files(BATCH007_DIR, BATCH007_REQUIRED)
        + require_files(BATCH008_DIR, BATCH008_REQUIRED)
        + require_files(BATCH009_DIR, BATCH009_REQUIRED)
        + require_files(BATCH010_DIR, BATCH010_REQUIRED)
    )
    if missing:
        return fail(f"missing required files: {missing}")
    if verify_manifest(POST_DIR)["status"] != "PASS":
        return fail("post hardening manifest mismatch")
    if verify_manifest(BATCH_DIR)["status"] != "PASS":
        return fail("batch002 manifest mismatch")
    if verify_manifest(BATCH003_DIR)["status"] != "PASS":
        return fail("batch003 manifest mismatch")
    if verify_manifest(BATCH004_DIR)["status"] != "PASS":
        return fail("batch004 manifest mismatch")
    if verify_manifest(BATCH005_DIR)["status"] != "PASS":
        return fail("batch005 manifest mismatch")
    if verify_manifest(BATCH006_DIR)["status"] != "PASS":
        return fail("batch006 manifest mismatch")
    if verify_manifest(BATCH007_DIR)["status"] != "PASS":
        return fail("batch007 manifest mismatch")
    if verify_manifest(BATCH008_DIR)["status"] != "PASS":
        return fail("batch008 manifest mismatch")
    if verify_manifest(BATCH009_DIR)["status"] != "PASS":
        return fail("batch009 manifest mismatch")
    if verify_manifest(BATCH010_DIR)["status"] != "PASS":
        return fail("batch010 manifest mismatch")
    if not command_passes([sys.executable, "-m", "pytest", "tests/core", "-q"]):
        return fail("core tests failed")
    if not command_passes([sys.executable, "scripts/audit_v2_37_core_consolidation_and_clean_replication.py"]):
        return fail("v2.37 audit failed")

    records = read_json(POST_DIR / "workspace_transport_integrity_log.json").get("transfer_records")
    if not isinstance(records, list):
        return fail("transport integrity log invalid")
    for record in records:
        if not isinstance(record, dict):
            return fail("transport record malformed")
        for field in ["source_path", "destination_path", "source_sha256", "destination_sha256", "transfer_reason", "allowlist_class", "transport_decision"]:
            if not record.get(field):
                return fail(f"transport record missing {field}")
        if record.get("transport_decision") != "PASS":
            return fail("transport_integrity_breach")

    if read_json(POST_DIR / "transport_boundary_audit.json").get("forbidden_payload_count") != 0:
        return fail("forbidden payload recorded")
    if read_json(POST_DIR / "bounded_exploration_budget_trace.json").get("status") != "PASS":
        return fail("bounded exploration budget trace blocked unexpectedly")
    if read_json(POST_DIR / "environment_normalization_log.json").get("status") != "PASS":
        return fail("environment normalization unsafe")
    if read_json(POST_DIR / "issue_derived_evidence_class_policy.json").get("increments_native_count") is not False:
        return fail("issue-derived evidence class increments native count")
    if read_json(POST_DIR / "bugsinpy_relaxation_research_status.json").get("global_block_active") is not True:
        return fail("BugsInPy global block relaxed")
    official = read_json(POST_DIR / "post_v2_37_hardening_artifact_verification.json")
    if official.get("status") != "PASS":
        return fail("post-v2.37 artifact verification not PASS")
    if official.get("zip_sha256") != "6e0dcb44607dd8a23661b7bff30448e36db561477e99d2bee0689494cb505f1b":
        return fail("post-v2.37 artifact SHA mismatch")
    pycache_audit = read_json(POST_DIR / "artifact_pycache_payload_audit.json")
    if pycache_audit.get("pycache_pyc_payload_count") != 26:
        return fail("expected prior artifact cache payload audit mismatch")
    diagnosis = read_json(POST_DIR / "batch002_mixed_mode_failure_diagnosis.json")
    if diagnosis.get("metadata_probe_attempted") is not False or diagnosis.get("issue_derived_fallback_attempted") is not False:
        return fail("batch002 prior failure diagnosis invalid")
    packaging = read_json(POST_DIR / "artifact_packaging_correction_report.json")
    if packaging.get("status") != "PASS":
        return fail("artifact packaging correction report not PASS")
    manifest_report = read_json(POST_DIR / "artifact_payload_manifest_report.json")
    if manifest_report.get("status") != "PASS" or manifest_report.get("cache_payload_count") != 0:
        return fail("artifact payload manifest report invalid")
    readme_report = read_json(POST_DIR / "readme_status_update_report.json")
    docs_report = read_json(POST_DIR / "public_docs_accuracy_audit.json")
    matrix_status = read_json(POST_DIR / "operational_gate_matrix_status.json")
    language_expanded = read_json(POST_DIR / "public_language_audit_expanded.json")
    env_artifact = read_json(POST_DIR / "batch002_environment_resolution_artifact_verification.json")
    repair_gap = read_json(POST_DIR / "batch002_repair_generation_gap_diagnosis.json")
    if env_artifact.get("status") != "PASS" or env_artifact.get("sha256_match") is not True:
        return fail("environment-resolution artifact verification not PASS")
    if repair_gap.get("two_native_candidates_verified") is not True or repair_gap.get("immediate_blocker") != "clean_protocol_source_patch_generation_source_context_handoff":
        return fail("repair generation gap diagnosis invalid")
    if readme_report.get("status") != "PASS":
        return fail("README status update report failed")
    if docs_report.get("status") != "PASS":
        return fail("public docs accuracy audit failed")
    if matrix_status.get("status") != "PASS" or int(matrix_status.get("gate_count", 0)) < 26:
        return fail("operational gate matrix status failed")
    if language_expanded.get("status") != "PASS":
        return fail("expanded public language audit failed")
    phase_a_errors = audit_phase_a_ingest_records()
    if phase_a_errors:
        return fail(f"phase A ingest audit failed: {phase_a_errors}")
    payload_audit = audit_artifact_payload(PAYLOAD_DIR)
    if payload_audit["status"] != "PASS":
        return fail(f"artifact payload hygiene failed: {payload_audit}")

    batch = read_json(BATCH_DIR / "consolidated_state_clean_replication_batch_002.json")
    trace = read_json(BATCH_DIR / "candidate_source_mode_trace.json")
    trace_by_mode = {item.get("mode"): item for item in trace if isinstance(item, dict)}
    if trace_by_mode.get("curated_seed", {}).get("attempted") is not True:
        return fail("curated_seed not attempted")
    if trace_by_mode.get("metadata_probe", {}).get("attempted") is not True:
        return fail("metadata_probe not attempted")
    if trace_by_mode.get("issue_derived", {}).get("attempted") is not True:
        return fail("issue_derived fallback not attempted")
    attempts = read_json(BATCH_DIR / "candidate_verification_attempts.json")
    if not isinstance(attempts, list) or not attempts:
        return fail("candidate_verification_attempts must not be empty when modes are enabled")
    if any("py_bugger_issue_65" in json.dumps(item, sort_keys=True) for item in attempts):
        return fail("py_bugger_issue_65 reused as a new candidate")
    metadata_attempts = read_json(BATCH_DIR / "metadata_probe_attempts.json")
    issue_attempts = read_json(BATCH_DIR / "issue_derived_attempts.json")
    if not metadata_attempts and batch.get("exact_blocker") != "clean_replication_batch_002_lead_pool_empty":
        return fail("metadata probe attempt record invalid")
    if not issue_attempts and batch.get("exact_blocker") != "clean_replication_batch_002_lead_pool_empty":
        return fail("issue-derived attempt record invalid")
    real_acquisition_errors = audit_real_acquisition_records(load_lead_pool(), metadata_attempts, issue_attempts, attempts, batch)
    if real_acquisition_errors:
        return fail(f"real acquisition audit failed: {real_acquisition_errors}")
    env_attempts = read_json(BATCH_DIR / "environment_resolution_attempts.json")
    env_policy = read_json(BATCH_DIR / "environment_resolution_policy.json")
    env_classification = read_json(BATCH_DIR / "environment_failure_classification.json")
    install_manifest = read_json(BATCH_DIR / "dependency_install_logs_manifest.json")
    if env_policy.get("status") != "PASS" or env_policy.get("undeclared_arbitrary_dependency_install_allowed") is not False:
        return fail("environment resolution policy invalid")
    if not isinstance(env_attempts, list) or len(env_attempts) != len(metadata_attempts):
        return fail("environment resolution attempts do not align with metadata attempts")
    if not isinstance(env_classification, list) or not isinstance(install_manifest, list):
        return fail("environment classification or install log manifest invalid")
    environment_errors = audit_environment_resolution_records(metadata_attempts, batch)
    if environment_errors:
        return fail(f"environment resolution audit failed: {environment_errors}")
    repair_errors = audit_repair_generation_records(batch)
    if repair_errors:
        return fail(f"repair generation audit failed: {repair_errors}")
    matched_null_errors = audit_matched_null_records(batch)
    if matched_null_errors:
        return fail(f"matched-null audit failed: {matched_null_errors}")
    batch003_errors = audit_batch003_records()
    if batch003_errors:
        return fail(f"batch003 audit failed: {batch003_errors}")
    batch004_errors = audit_batch004_records()
    if batch004_errors:
        return fail(f"batch004 audit failed: {batch004_errors}")
    batch005_errors = audit_batch005_records()
    if batch005_errors:
        return fail(f"batch005 audit failed: {batch005_errors}")
    batch006_errors = audit_batch006_records()
    if batch006_errors:
        return fail(f"batch006 audit failed: {batch006_errors}")
    batch007_errors = audit_batch007_records()
    if batch007_errors:
        return fail(f"batch007 audit failed: {batch007_errors}")
    batch008_errors = audit_batch008_records()
    if batch008_errors:
        return fail(f"batch008 audit failed: {batch008_errors}")
    batch009_errors = audit_batch009_records()
    if batch009_errors:
        return fail(f"batch009 audit failed: {batch009_errors}")
    batch010_errors = audit_batch010_records()
    if batch010_errors:
        return fail(f"batch010 audit failed: {batch010_errors}")
    traceability_errors = audit_notebooklm_traceability_records()
    if traceability_errors:
        return fail(f"notebooklm traceability audit failed: {traceability_errors}")
    repair_attempts = read_json(BATCH_DIR / "repair_attempts.json")
    verified_native_count = int(batch.get("native_candidates_verified_count", 0))
    if verified_native_count and (not isinstance(repair_attempts, list) or not repair_attempts):
        return fail("verified native candidates require recorded clean repair attempts")
    if isinstance(repair_attempts, list):
        for item in repair_attempts:
            if item.get("source_only_repair_attempted") is not True:
                return fail("repair attempt missing source-only marker")
            if item.get("tests_modified") is not False or item.get("support_files_modified") is not False or item.get("config_workflow_registry_audit_modified") is not False:
                return fail("repair attempt mutated forbidden files")
            if item.get("source_mutation_performed") is True and item.get("patch_authorized") is not True:
                return fail("source mutation occurred without patch authorization")
    success_count = int(batch.get("native_repair_successes_count", 0))
    if success_count:
        duplicate_pass = read_json(BATCH_DIR / "duplicate_replay_results.json")
        validation_pass = read_json(BATCH_DIR / "target_validation_results.json")
        if not any(item.get("status") == "PASS" for item in duplicate_pass):
            return fail("native repair success without duplicate replay PASS")
        if not any(item.get("status") == "PASS" and item.get("exit_code") == 0 for item in validation_pass):
            return fail("native repair success without target validation exit 0")
    if batch.get("additional_native_external_repairs_acquired_count") != success_count:
        return fail("additional native repair count does not match repair successes")
    if success_count:
        episode_registry = read_json(Path("configs/external_repair_episode_registry.json"))
        episodes = episode_registry.get("episodes", [])
        if not any(isinstance(item, dict) and item.get("candidate_id") == "darker_non_ascii_drop_changes" and item.get("scoreable") is True for item in episodes):
            return fail("successful batch002 repair missing from external repair episode registry")
    zero_count_fields = [
        "issue_derived_candidates_verified_count",
        "additional_issue_derived_repairs_acquired_count",
        "issue_derived_repair_successes_count",
    ]
    for field in zero_count_fields:
        if batch.get(field) != 0:
            return fail(f"batch002 {field} changed unexpectedly")
    if batch.get("full_scoring") != "NOT_RUN/disallowed":
        return fail("full scoring boundary changed")
    if batch.get("memory_lift") not in {"undemonstrated", "undemonstrated_equal_performance"}:
        return fail("memory lift overclaim")
    if batch.get("self_maintaining_software") != "false/not_demonstrated":
        return fail("self-maintaining software overclaim")

    final_report = read_json(POST_DIR / "final_report_post_v2_37_hardening_001.json")
    if final_report.get("public_claim_overreach_status") != "PASS":
        return fail("public claim pressure not PASS")
    hits = public_language_hits()
    if hits:
        return fail(f"public language audit failed: {hits}")

    print("post-v2.37 hardening and batch002 audit PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
