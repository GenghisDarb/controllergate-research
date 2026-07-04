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
BATCH011_DIR = Path("outputs/clean_replication_batch_011")
BATCH012_DIR = Path("outputs/clean_replication_batch_012")
BATCH013_DIR = Path("outputs/clean_replication_batch_013")
BATCH014_DIR = Path("outputs/clean_replication_batch_014")
BATCH015_DIR = Path("outputs/clean_replication_batch_015")
BATCH016_DIR = Path("outputs/clean_replication_batch_016")
BATCH017_DIR = Path("outputs/clean_replication_batch_017")
BATCH018_DIR = Path("outputs/clean_replication_batch_018")
BATCH019_DIR = Path("outputs/clean_replication_batch_019")
BATCH020_DIR = Path("outputs/clean_replication_batch_020")
BATCH021_DIR = Path("outputs/clean_replication_batch_021")
BATCH022_DIR = Path("outputs/clean_replication_batch_022")
BATCH023_DIR = Path("outputs/clean_replication_batch_023")
PAYLOAD_DIR = Path("artifact_payload/post_v2_37_hardening_batch023_bounded_docker_provider_thin")

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
    "batch010_active_memory_routing_artifact_verification.json",
    "batch010_no_routing_delta_diagnosis.json",
    "batch011_prospective_memory_challenge_recommendation.json",
    "batch011_prospective_memory_challenge_artifact_verification.json",
    "batch011_no_fresh_candidate_diagnosis.json",
    "batch012_targeted_seed_recommendation.json",
    "batch012_targeted_seed_artifact_verification.json",
    "batch012_missing_seed_diagnosis.json",
    "batch013_acquisition_lock_recommendation.json",
    "batch019_active_search_geometry_artifact_verification.json",
    "batch019_active_search_geometry_ingest_summary.json",
    "batch020_manual_lock_materialization_recommendation.json",
    "batch020_manual_lock_materialization_artifact_verification.json",
    "batch020_manual_lock_materialization_ingest_summary.json",
    "batch021_dynamic_era_materialization_recommendation.json",
    "batch021_dynamic_era_materialization_artifact_verification.json",
    "batch021_dynamic_era_materialization_ingest_summary.json",
    "batch022_docker_provider_and_psa82_recommendation.json",
    "batch022_docker_era_psa82_artifact_verification.json",
    "batch022_docker_era_psa82_ingest_summary.json",
    "batch023_bounded_docker_provider_recommendation.json",
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

BATCH011_REQUIRED = [
    "campaign_summary.md",
    "consolidated_state_clean_replication_batch_011.json",
    "prospective_memory_challenge_policy.json",
    "prospective_memory_eligibility_gate.json",
    "candidate_difficulty_band_policy.json",
    "fresh_candidate_lead_pool.json",
    "fresh_candidate_attempts.json",
    "fresh_candidate_rejection_ledger.json",
    "retired_memory_challenge_candidates.json",
    "darker_skip_glob_memory_challenge_retirement.json",
    "fresh_candidate_source_mode_trace.json",
    "native_candidate_attempts.json",
    "issue_derived_candidate_attempts.json",
    "candidate_verification_attempts.json",
    "candidate_admission_decisions.json",
    "curvature_selection_policy.json",
    "two_winner_source_selection_policy.json",
    "strict_minimum_delta_policy_batch011.json",
    "candidate_curvature_scores.json",
    "source_route_curvature_scores.json",
    "prospective_experiment_preregistration.json",
    "memory_enabled_policy_batch011.json",
    "memory_disabled_null_ensemble_policy_batch011.json",
    "prospective_patch_artifact_quarantine_policy.json",
    "memory_enabled_run_results.json",
    "null_ensemble_run_results.json",
    "null_ensemble_summary.json",
    "matched_null_ensemble_separation_score.json",
    "prospective_memory_lift_evaluation.json",
    "repair_successes.json",
    "claim_boundary.json",
    "notebooklm_advice_traceability_status.json",
    "carry_forward_blocker_register.json",
    "SHA256SUMS.txt",
]

BATCH012_REQUIRED = [
    "campaign_summary.md",
    "consolidated_state_clean_replication_batch_012.json",
    "targeted_seed_presence_check.json",
    "targeted_seed_schema_validation.json",
    "targeted_seed_forbidden_evidence_audit.json",
    "targeted_seed_intake_report.json",
    "targeted_seed_required_next_action.md",
    "native_verification_result.json",
    "issue_derived_harness_policy.json",
    "issue_derived_harness_verification_result.json",
    "prospective_memory_eligibility_gate.json",
    "route_diversity_status.json",
    "status_feature_mappability.json",
    "matched_null_ensemble_summary.json",
    "repair_only_fallback_summary.json",
    "claim_boundary.json",
    "notebooklm_advice_traceability_status.json",
    "carry_forward_blocker_register.json",
    "SHA256SUMS.txt",
]

BATCH013_REQUIRED = [
    "campaign_summary.md",
    "consolidated_state_clean_replication_batch_013.json",
    "acquisition_lock_stack_policy.json",
    "source_commit_environment_lock_policy.json",
    "source_commit_environment_lock_summary.json",
    "target_command_manifest_policy.json",
    "target_command_manifest_summary.json",
    "fresh_workspace_purity_policy.json",
    "workspace_purity_report.json",
    "baseline_registry_drift_precheck_policy.json",
    "baseline_registry_snapshot_batch013.json",
    "baseline_registry_drift_precheck.json",
    "rollback_block_ledger_policy.json",
    "rollback_block_ledger_audit.json",
    "acquisition_lock_stack_status.json",
    "targeted_seed_presence_check.json",
    "targeted_seed_schema_validation.json",
    "targeted_seed_forbidden_evidence_audit.json",
    "targeted_seed_intake_report.json",
    "targeted_seed_next_action.json",
    "targeted_seed_required_next_action.md",
    "targeted_seed_git_tracking_audit.json",
    "targeted_seed_workflow_visibility_audit.json",
    "batch013_gate_chain_policy.json",
    "batch013_gate_chain_execution_trace.json",
    "batch013_gate_dependency_audit.json",
    "active_context_filtering_policy.json",
    "active_context_filter_manifest.json",
    "memory_enabled_context_before_filter.json",
    "memory_enabled_context_after_filter.json",
    "context_filter_delta_audit.json",
    "curvature_heuristic_freeze.json",
    "curvature_score_formula.json",
    "curvature_thresholds.json",
    "proof_obligations_ledger.json",
    "five_locks_curvature_cross_gate.json",
    "issue_derived_temporal_and_classification_audit.json",
    "global_curvature_logic_policy.json",
    "curvature_logic_enforcement_status.json",
    "curvature_trace_audit.json",
    "curvature_feature_vector_schema.json",
    "candidate_curvature_feature_vectors.json",
    "basin_stability_check_policy.json",
    "basin_stability_scores.json",
    "two_winner_global_policy.json",
    "two_winner_decision_records.json",
    "curvature_memory_routing_policy.json",
    "curvature_memory_routing_audit.json",
    "curvature_fragment_planning_policy.json",
    "curvature_fragment_plan.json",
    "null_ensemble_curvature_fairness_policy.json",
    "null_ensemble_curvature_fairness_audit.json",
    "curvature_claim_boundary.json",
    "native_verification_result.json",
    "issue_derived_harness_policy.json",
    "issue_derived_harness_verification_result.json",
    "prospective_memory_eligibility_gate.json",
    "route_diversity_status.json",
    "status_feature_mappability.json",
    "matched_null_ensemble_summary.json",
    "repair_only_fallback_summary.json",
    "claim_boundary.json",
    "notebooklm_advice_traceability_status.json",
    "carry_forward_blocker_register.json",
    "SHA256SUMS.txt",
]

BATCH014_REQUIRED = [
    "campaign_summary.md",
    "consolidated_state_clean_replication_batch_014.json",
    "targeted_seed_path_resolution.json",
    "targeted_seed_git_tracking_audit.json",
    "targeted_seed_workflow_visibility_audit.json",
    "targeted_seed_schema_validation.json",
    "targeted_seed_forbidden_evidence_audit.json",
    "targeted_seed_intake_report.json",
    "seed_schema_harmonization_policy.json",
    "seed_schema_harmonization_result.json",
    "normalized_targeted_seed_record.json",
    "issue_text_solution_section_firewall_policy.json",
    "issue_text_solution_section_firewall_audit.json",
    "redacted_issue_snapshot_hash.json",
    "dataset_lead_firewall_policy.json",
    "dataset_lead_firewall_audit.json",
    "proposed_native_seed_verification_guard.json",
    "darker_issue_112_native_seed_verification.json",
    "native_seed_downgrade_decision.json",
    "native_to_issue_derived_downgrade_report.json",
    "issue112_redacted_snapshot_policy.json",
    "issue112_redacted_snapshot_audit.json",
    "issue112_solution_section_exclusion_audit.json",
    "issue112_external_command_manifest.json",
    "issue112_claim_boundary.json",
    "source_commit_selection.json",
    "source_checkout_audit.json",
    "workspace_purity_report.json",
    "source_commit_environment_lock_summary.json",
    "target_command_manifest_summary.json",
    "baseline_registry_drift_precheck.json",
    "rollback_block_ledger_audit.json",
    "acquisition_lock_stack_status.json",
    "batch014_gate_chain_execution_trace.json",
    "batch014_gate_dependency_audit.json",
    "issue_text_hash.json",
    "issue_text_temporal_guard.json",
    "issue_derived_latent_knowledge_risk_disclosure.json",
    "issue_derived_harness_context_manifest.json",
    "issue_derived_harness_firewall_audit.json",
    "issue_derived_ephemeral_harness.py",
    "issue_derived_harness_sha256.txt",
    "issue_derived_harness_verification_result.json",
    "issue_derived_temporal_and_classification_audit.json",
    "global_curvature_logic_policy.json",
    "curvature_feature_vector_schema.json",
    "candidate_curvature_feature_vectors.json",
    "basin_stability_scores.json",
    "two_winner_decision_records.json",
    "five_locks_curvature_cross_gate.json",
    "prospective_memory_eligibility_gate.json",
    "curvature_claim_boundary.json",
    "repair_only_fallback_status.json",
    "matched_null_ensemble_summary.json",
    "proof_obligations_ledger.json",
    "notebooklm_advice_traceability_status.json",
    "carry_forward_blocker_register.json",
    "SHA256SUMS.txt",
]

BATCH015_REQUIRED = [
    "campaign_summary.md",
    "consolidated_state_clean_replication_batch_015.json",
    "latest_artifact_boundary_status.json",
    "validation_path_continuity_status.json",
    "claim_boundary_batch015.json",
    "repair_episode_count_preservation.json",
    "native_issue_derived_count_boundary.json",
    "full_scoring_boundary.json",
    "memory_lift_boundary.json",
    "self_maintaining_boundary.json",
    "runtime_wrapper_architecture_policy.json",
    "runtime_incident_capture_schema.json",
    "execution_boundary_gateway_policy.json",
    "isolated_repair_sandbox_policy.json",
    "dependency_drift_chaperone_policy.json",
    "active_ast_excision_probe_policy.json",
    "syntax_micro_rollback_policy.json",
    "predictive_degradation_telemetry_policy.json",
    "compute_budget_safe_stop_policy.json",
    "blue_green_deployment_policy.json",
    "proof_to_action_compiler_policy.json",
    "runtime_wrapper_mvp_status.json",
    "lock_sequence_operation_registry_status.json",
    "lock_sequence_operation_examples.json",
    "lock_sequence_claim_boundary.json",
    "four_lock_operation_grammar.json",
    "runtime_curvature_integration_policy.json",
    "post_patch_constraint_revalidation_policy.json",
    "no_overreach_runtime_policy.json",
    "runtime_curvature_claim_boundary.json",
    "controllergate_claim_tier_status.json",
    "controllergate_capability_catalog_status.json",
    "marketing_claim_boundary.json",
    "structure_first_compiler_roadmap_status.json",
    "future_agentic_admissibility_compiler_status.json",
    "skeptics_acceptance_checklist_status.json",
    "SHA256SUMS.txt",
]

BATCH016_REQUIRED = [
    "campaign_summary.md",
    "consolidated_state_clean_replication_batch_016.json",
    "batch015_boundary_preservation.json",
    "claim_boundary_batch016.json",
    "target_intent_signature_policy.json",
    "darker_issue112_target_intent_signature.json",
    "target_intent_alignment_audit.json",
    "runtime_incident_issue112_mismatch.json",
    "runtime_incident_bundle_hash.json",
    "proof_to_action_issue112_mismatch.json",
    "dependency_era_chaperone_policy.json",
    "darker_issue112_dependency_era_audit.json",
    "dependency_precondition_classification.json",
    "environment_restore_plan_issue112.json",
    "issue112_command_variant_policy.json",
    "issue112_command_variant_matrix.json",
    "issue112_environment_variant_matrix.json",
    "issue112_variant_results.json",
    "source_commit_window_policy.json",
    "source_commit_window_candidates.json",
    "source_commit_window_results.json",
    "issue_derived_harness_correction_policy.json",
    "issue_derived_harness_v2_context_manifest.json",
    "issue_derived_harness_v2_verification_result.json",
    "candidate_curvature_feature_vectors.json",
    "basin_stability_scores.json",
    "two_winner_decision_records.json",
    "prospective_memory_eligibility_gate.json",
    "curvature_claim_boundary.json",
    "repair_only_fallback_status.json",
    "issue_derived_repair_feasibility_status.json",
    "issue_derived_matched_null_diagnostic_status.json",
    "proof_obligations_ledger.json",
    "rollback_block_ledger_audit.json",
    "compute_budget_safe_stop_batch016.json",
    "controllergate_claim_tier_update.json",
    "controllergate_capability_catalog_update.json",
    "SHA256SUMS.txt",
]

BATCH017_REQUIRED = [
    "campaign_summary.md",
    "consolidated_state_clean_replication_batch_017.json",
    "batch016_boundary_preservation.json",
    "batch015_runtime_scaffold_preservation.json",
    "claim_boundary_batch017.json",
    "artifact_packaging_policy.json",
    "thin_artifact_packaging_policy.json",
    "artifact_lineage_index.json",
    "evidence_carry_forward_manifest.json",
    "artifact_payload_budget.json",
    "artifact_minimality_audit.json",
    "lineage_equivalence_audit.json",
    "dependency_era_resolution_policy.json",
    "decision_time_dependency_evidence_policy.json",
    "dependency_resolution_forbidden_sources.json",
    "dependency_era_resolution_audit.json",
    "dependency_metadata_inventory.json",
    "dependency_constraint_candidates.json",
    "dependency_release_time_audit.json",
    "decision_time_dependency_lock_candidate.json",
    "decision_time_dependency_lock_status.json",
    "manual_dependency_lock_presence_check.json",
    "manual_dependency_lock_git_tracking_audit.json",
    "manual_dependency_lock_schema_validation.json",
    "manual_dependency_lock_decision_time_audit.json",
    "issue112_command_variant_policy.json",
    "issue112_environment_variant_matrix.json",
    "issue112_dependency_resolved_variant_results.json",
    "source_commit_window_policy.json",
    "source_commit_window_candidates.json",
    "source_commit_window_results.json",
    "darker_issue112_target_intent_signature_retry.json",
    "target_intent_alignment_retry_audit.json",
    "issue_derived_harness_v3_policy.json",
    "issue_derived_harness_v3_context_manifest.json",
    "issue_derived_harness_v3_verification_result.json",
    "candidate_curvature_feature_vectors.json",
    "basin_stability_scores.json",
    "two_winner_decision_records.json",
    "prospective_memory_eligibility_gate.json",
    "curvature_claim_boundary.json",
    "repair_only_fallback_status.json",
    "issue_derived_repair_feasibility_status.json",
    "issue_derived_matched_null_diagnostic_status.json",
    "darker_issue112_candidate_viability_decision.json",
    "manual_dependency_lock_request.md",
    "manual_seed_refinement_request.md",
    "proof_obligations_ledger.json",
    "rollback_block_ledger_audit.json",
    "compute_budget_safe_stop_batch017.json",
    "controllergate_claim_tier_update.json",
    "controllergate_capability_catalog_update.json",
    "SHA256SUMS.txt",
]

BATCH018_REQUIRED = [
    "campaign_summary.md",
    "consolidated_state_clean_replication_batch_018.json",
    "batch017_boundary_preservation.json",
    "thin_artifact_lineage_preservation.json",
    "claim_boundary_batch018.json",
    "issue_timestamp_reconciliation_policy.json",
    "darker_issue112_timestamp_reconciliation.json",
    "dependency_cutoff_decision.json",
    "manual_dependency_lock_presence_check.json",
    "manual_dependency_lock_git_tracking_audit.json",
    "manual_dependency_lock_schema_validation.json",
    "manual_dependency_lock_decision_time_audit.json",
    "manual_requirements_support_file_audit.json",
    "manual_dependency_lock_normalization_result.json",
    "manual_dependency_lock_request.md",
    "manual_dependency_lock_schema_template.json",
    "manual_dependency_lock_next_action.json",
    "decision_time_dependency_lock_validation.json",
    "dependency_version_evidence_audit.json",
    "dependency_cutoff_compliance_audit.json",
    "dependency_resolution_forbidden_sources_audit.json",
    "manual_lock_environment_materialization_policy.json",
    "manual_lock_environment_materialization_log.json",
    "manual_lock_environment_hash.json",
    "workspace_purity_report.json",
    "acquisition_lock_stack_status.json",
    "issue112_command_variant_policy.json",
    "issue112_manual_lock_variant_results.json",
    "darker_issue112_target_intent_signature_retry.json",
    "target_intent_alignment_retry_audit.json",
    "source_commit_window_policy.json",
    "source_commit_window_candidates.json",
    "source_commit_window_results.json",
    "issue_derived_harness_v4_policy.json",
    "issue_derived_harness_v4_context_manifest.json",
    "issue_derived_harness_v4_verification_result.json",
    "candidate_curvature_feature_vectors.json",
    "basin_stability_scores.json",
    "two_winner_decision_records.json",
    "prospective_memory_eligibility_gate.json",
    "curvature_claim_boundary.json",
    "repair_only_fallback_status.json",
    "issue_derived_repair_feasibility_status.json",
    "issue_derived_matched_null_diagnostic_status.json",
    "darker_issue112_candidate_viability_decision.json",
    "proof_obligations_ledger.json",
    "rollback_block_ledger_audit.json",
    "compute_budget_safe_stop_batch018.json",
    "artifact_packaging_policy.json",
    "thin_artifact_packaging_policy.json",
    "artifact_lineage_index.json",
    "evidence_carry_forward_manifest.json",
    "artifact_payload_budget.json",
    "artifact_minimality_audit.json",
    "lineage_equivalence_audit.json",
    "controllergate_claim_tier_update.json",
    "controllergate_capability_catalog_update.json",
    "SHA256SUMS.txt",
]

BATCH019_REQUIRED = [
    "campaign_summary.md",
    "consolidated_state_clean_replication_batch_019.json",
    "batch018_boundary_preservation.json",
    "manual_dependency_lock_blocker_carry_forward.json",
    "claim_boundary_batch019.json",
    "manual_dependency_lock_watch_status.json",
    "manual_dependency_lock_next_action.json",
    "active_search_space_geometry_policy.json",
    "search_space_geometry_schema.json",
    "structural_defect_boundary_policy.json",
    "stable_candidate_region_policy.json",
    "recovery_candidate_path_policy.json",
    "information_gain_probe_selection_policy.json",
    "amds_active_inference_integration_policy.json",
    "active_search_space_geometry_status.json",
    "search_space_feature_vector_schema.json",
    "search_space_feature_vector_examples.json",
    "search_space_feature_vector_status.json",
    "information_gain_probe_policy.json",
    "probe_candidate_registry.json",
    "probe_selection_decision_records.json",
    "probe_budget_policy_batch019.json",
    "probe_selection_status.json",
    "structural_defect_boundary_schema.json",
    "structural_defect_boundary_examples.json",
    "structural_defect_boundary_status.json",
    "recovery_path_ranking_policy.json",
    "recovery_candidate_path_examples.json",
    "recovery_path_ranking_status.json",
    "single_system_scope_gate_policy.json",
    "coupled_interlock_extension_gate_policy.json",
    "single_system_vs_interlock_scope_audit.json",
    "amds_active_inference_policy.json",
    "amds_candidate_radar_schema.json",
    "amds_active_probe_queue.json",
    "amds_active_inference_status.json",
    "replacement_seed_request_policy.json",
    "replacement_seed_request_template.json",
    "replacement_seed_quality_gate.json",
    "curvature_active_geometry_integration_policy.json",
    "curvature_probe_selection_integration.json",
    "curvature_claim_boundary_batch019.json",
    "artifact_packaging_policy.json",
    "thin_artifact_packaging_policy.json",
    "artifact_lineage_index.json",
    "evidence_carry_forward_manifest.json",
    "artifact_payload_budget.json",
    "artifact_minimality_audit.json",
    "lineage_equivalence_audit.json",
    "controllergate_claim_tier_update.json",
    "controllergate_capability_catalog_update.json",
    "SHA256SUMS.txt",
]

BATCH020_REQUIRED = [
    "campaign_summary.md",
    "consolidated_state_clean_replication_batch_020.json",
    "batch019_boundary_preservation.json",
    "active_search_geometry_preservation.json",
    "manual_dependency_lock_watch_preservation.json",
    "claim_boundary_batch020.json",
    "manual_dependency_lock_presence_check.json",
    "manual_dependency_lock_git_tracking_audit.json",
    "manual_dependency_lock_schema_validation.json",
    "manual_dependency_lock_decision_time_audit.json",
    "manual_dependency_lock_sha256_audit.json",
    "manual_requirements_support_file_audit.json",
    "manual_dependency_lock_validation_status.json",
    "semantic_drift_guardrail_policy.json",
    "public_language_audit_batch020.json",
    "operational_translation_audit_batch020.json",
    "activation_order_guardrail_policy.json",
    "activation_order_audit_batch020.json",
    "rollback_ghost_state_policy.json",
    "rollback_block_ledger_audit.json",
    "proof_obligations_ledger.json",
    "dependency_overlap_grouping_policy.json",
    "dependency_overlap_groups.json",
    "dependency_overlap_audit.json",
    "consistency_reassertion_policy.json",
    "consistency_reassertion_audit.json",
    "feature_vector_reassertion_batch020.json",
    "failure_taxonomy_policy.json",
    "failure_taxonomy_batch020.json",
    "precision_failure_log_batch020.json",
    "manual_lock_environment_materialization_policy.json",
    "manual_lock_environment_materialization_log.json",
    "manual_lock_environment_hash.json",
    "workspace_purity_report.json",
    "acquisition_lock_stack_status.json",
    "issue112_command_variant_policy.json",
    "issue112_manual_lock_variant_results.json",
    "darker_issue112_target_intent_signature_retry.json",
    "target_intent_alignment_retry_audit.json",
    "issue_derived_harness_v5_policy.json",
    "issue_derived_harness_v5_context_manifest.json",
    "issue_derived_harness_v5_verification_result.json",
    "candidate_curvature_feature_vectors.json",
    "basin_stability_scores.json",
    "two_winner_decision_records.json",
    "prospective_memory_eligibility_gate.json",
    "curvature_claim_boundary.json",
    "active_search_geometry_execution_trace.json",
    "repair_only_fallback_status.json",
    "issue_derived_repair_feasibility_status.json",
    "issue_derived_matched_null_diagnostic_status.json",
    "darker_issue112_candidate_viability_decision.json",
    "next_probe_or_seed_decision.json",
    "artifact_packaging_policy.json",
    "thin_artifact_packaging_policy.json",
    "artifact_lineage_index.json",
    "evidence_carry_forward_manifest.json",
    "artifact_payload_budget.json",
    "artifact_minimality_audit.json",
    "lineage_equivalence_audit.json",
    "controllergate_claim_tier_update.json",
    "controllergate_capability_catalog_update.json",
    "SHA256SUMS.txt",
]

BATCH021_REQUIRED = [
    "campaign_summary.md",
    "consolidated_state_clean_replication_batch_021.json",
    "batch020_boundary_preservation.json",
    "manual_dependency_lock_validation_preservation.json",
    "environment_materialization_blocker_preservation.json",
    "claim_boundary_batch021.json",
    "dynamic_era_materialization_policy.json",
    "runtime_provider_registry.json",
    "runtime_provider_selection_policy.json",
    "runtime_provider_selection_decision.json",
    "runtime_version_gate_policy.json",
    "runtime_version_gate_audit.json",
    "containerized_era_runtime_policy.json",
    "dynamic_era_materialization_status.json",
    "runtime_provider_preflight_matrix.json",
    "runtime_provider_preflight_results.json",
    "python37_runtime_provider_status.json",
    "runtime_provider_custody_audit.json",
    "hosted_runtime_adapter_status.json",
    "self_hosted_runtime_plan.json",
    "containerized_workflow_plan.json",
    "containerized_workflow_execution_policy.json",
    "containerized_runtime_security_policy.json",
    "batch021_manual_lock_revalidation_under_provider.json",
    "provider_lock_install_plan.json",
    "provider_lock_install_log.json",
    "provider_lock_install_hash.json",
    "selected_provider_environment_materialization_log.json",
    "selected_provider_environment_hash.json",
    "issue112_runtime_provider_command_variant_matrix.json",
    "issue112_runtime_provider_target_intent_retry.json",
    "target_intent_alignment_retry_under_provider_audit.json",
    "runtime_provider_target_signature_comparison.json",
    "issue_derived_harness_v6_policy.json",
    "issue_derived_harness_v6_context_manifest.json",
    "issue_derived_harness_v6_verification_result.json",
    "issue_derived_harness_v6_claim_boundary.json",
    "candidate_curvature_feature_vectors.json",
    "basin_stability_scores.json",
    "two_winner_decision_records.json",
    "prospective_memory_eligibility_gate.json",
    "curvature_claim_boundary.json",
    "route_diversity_status.json",
    "status_feature_mappability.json",
    "repair_only_fallback_status.json",
    "issue_derived_repair_feasibility_status.json",
    "issue_derived_matched_null_diagnostic_status.json",
    "post_patch_constraint_revalidation.json",
    "no_overreach_validation.json",
    "darker_issue112_candidate_viability_decision.json",
    "next_probe_or_seed_decision.json",
    "runtime_provider_next_action.json",
    "proof_obligations_ledger.json",
    "rollback_block_ledger_audit.json",
    "compute_budget_safe_stop_batch021.json",
    "failure_taxonomy_batch021.json",
    "precision_failure_log_batch021.json",
    "semantic_drift_guardrail_batch021.json",
    "activation_order_guardrail_batch021.json",
    "rollback_ghost_state_guardrail_batch021.json",
    "dependency_overlap_grouping_batch021.json",
    "consistency_reassertion_batch021.json",
    "artifact_packaging_policy.json",
    "thin_artifact_packaging_policy.json",
    "artifact_lineage_index.json",
    "evidence_carry_forward_manifest.json",
    "artifact_payload_budget.json",
    "artifact_minimality_audit.json",
    "lineage_equivalence_audit.json",
    "controllergate_claim_tier_update.json",
    "controllergate_capability_catalog_update.json",
    "public_language_audit_batch021.json",
    "SHA256SUMS.txt",
]

BATCH022_REQUIRED = [
    "campaign_summary.md",
    "consolidated_state_clean_replication_batch_022.json",
    "batch021_boundary_preservation.json",
    "runtime_provider_blocker_preservation.json",
    "claim_boundary_batch022.json",
    "psa82_package_presence_check.json",
    "psa82_package_quarantine_policy.json",
    "psa82_package_artifact_verification.json",
    "psa82_final_locked_manifest_audit.json",
    "psa82_legacy_manifest_stale_audit.json",
    "psa82_pyc_payload_audit.json",
    "psa82_adapter_claim_boundary.json",
    "structured_fragility_audit_policy.json",
    "permutation_null_audit_policy.json",
    "patch_structure_sensitivity_policy.json",
    "psa82_to_controllergate_adapter_mapping.json",
    "structured_fragility_claim_boundary.json",
    "structured_fragility_audit_status.json",
    "docker_runtime_provider_policy.json",
    "runtime_provider_registry_batch022.json",
    "runtime_provider_selection_decision_batch022.json",
    "python37_docker_provider_preflight.json",
    "runtime_version_gate_audit_batch022.json",
    "container_security_policy_batch022.json",
    "docker_provider_status.json",
    "containerized_workflow_plan.json",
    "containerized_workflow_execution_policy.json",
    "containerized_workflow_audit.json",
    "manual_dependency_lock_provider_revalidation.json",
    "manual_dependency_lock_provider_install_plan.json",
    "manual_dependency_lock_provider_install_log.json",
    "manual_dependency_lock_installed_freeze.json",
    "manual_dependency_lock_installed_hashes.json",
    "manual_dependency_lock_provider_install_status.json",
    "manual_lock_environment_materialization_policy.json",
    "manual_lock_environment_materialization_log.json",
    "manual_lock_environment_hash.json",
    "workspace_purity_report.json",
    "acquisition_lock_stack_status.json",
    "issue112_command_variant_policy.json",
    "issue112_provider_variant_results.json",
    "darker_issue112_target_intent_signature_retry.json",
    "target_intent_alignment_retry_audit.json",
    "issue_derived_harness_v7_policy.json",
    "issue_derived_harness_v7_context_manifest.json",
    "issue_derived_harness_v7_verification_result.json",
    "candidate_curvature_feature_vectors.json",
    "basin_stability_scores.json",
    "two_winner_decision_records.json",
    "prospective_memory_eligibility_gate.json",
    "curvature_claim_boundary.json",
    "active_search_geometry_execution_trace.json",
    "repair_only_fallback_status.json",
    "issue_derived_repair_feasibility_status.json",
    "issue_derived_matched_null_diagnostic_status.json",
    "post_patch_constraint_revalidation.json",
    "no_overreach_validation.json",
    "structured_fragility_audit_run_policy.json",
    "structured_fragility_audit_results.json",
    "permutation_null_audit_results.json",
    "patch_structure_sensitivity_results.json",
    "darker_issue112_candidate_viability_decision.json",
    "next_probe_or_seed_decision.json",
    "runtime_provider_next_action.json",
    "proof_obligations_ledger.json",
    "rollback_block_ledger_audit.json",
    "compute_budget_safe_stop_batch022.json",
    "failure_taxonomy_batch022.json",
    "precision_failure_log_batch022.json",
    "semantic_drift_guardrail_status.json",
    "activation_order_guardrail_status.json",
    "rollback_ghost_state_guardrail_status.json",
    "dependency_overlap_grouping_status.json",
    "consistency_reassertion_status.json",
    "artifact_packaging_policy.json",
    "thin_artifact_packaging_policy.json",
    "artifact_lineage_index.json",
    "evidence_carry_forward_manifest.json",
    "artifact_payload_budget.json",
    "artifact_minimality_audit.json",
    "lineage_equivalence_audit.json",
    "controllergate_claim_tier_update.json",
    "controllergate_capability_catalog_update.json",
    "public_language_audit_batch022.json",
    "SHA256SUMS.txt",
]

BATCH023_REQUIRED = [
    "campaign_summary.md",
    "consolidated_state_clean_replication_batch_023.json",
    "batch022_boundary_preservation.json",
    "docker_provider_blocker_preservation.json",
    "claim_boundary_batch023.json",
    "docker_provider_activation_policy.json",
    "docker_provider_activation_gate.json",
    "docker_provider_enablement_audit.json",
    "github_actions_provider_bridge_policy.json",
    "github_actions_provider_bridge_audit.json",
    "provider_credentials_isolation_audit.json",
    "provider_workspace_transport_audit.json",
    "python37_provider_preflight_policy.json",
    "python37_provider_preflight_results.json",
    "runtime_version_gate_audit_batch023.json",
    "docker_provider_status_batch023.json",
    "psa82_local_package_presence_check.json",
    "psa82_local_package_quarantine_summary.json",
    "psa82_final_locked_manifest_summary.json",
    "psa82_legacy_manifest_status.json",
    "psa82_pyc_quarantine_summary.json",
    "psa82_adapter_claim_boundary.json",
    "structured_fragility_audit_policy.json",
    "permutation_null_audit_policy.json",
    "patch_structure_sensitivity_policy.json",
    "structured_fragility_audit_status.json",
    "manual_dependency_lock_provider_revalidation.json",
    "manual_dependency_lock_provider_install_plan.json",
    "manual_dependency_lock_provider_install_log.json",
    "manual_dependency_lock_installed_freeze.json",
    "manual_dependency_lock_installed_hashes.json",
    "manual_dependency_lock_provider_install_status.json",
    "manual_lock_environment_materialization_policy.json",
    "manual_lock_environment_materialization_log.json",
    "manual_lock_environment_hash.json",
    "workspace_purity_report.json",
    "acquisition_lock_stack_status.json",
    "issue112_command_variant_policy.json",
    "issue112_provider_variant_results.json",
    "darker_issue112_target_intent_signature_retry.json",
    "target_intent_alignment_retry_audit.json",
    "issue_derived_harness_v8_policy.json",
    "issue_derived_harness_v8_context_manifest.json",
    "issue_derived_harness_v8_verification_result.json",
    "candidate_curvature_feature_vectors.json",
    "basin_stability_scores.json",
    "two_winner_decision_records.json",
    "prospective_memory_eligibility_gate.json",
    "curvature_claim_boundary.json",
    "active_search_geometry_execution_trace.json",
    "repair_only_fallback_status.json",
    "issue_derived_repair_feasibility_status.json",
    "issue_derived_matched_null_diagnostic_status.json",
    "post_patch_constraint_revalidation.json",
    "no_overreach_validation.json",
    "darker_issue112_candidate_viability_decision.json",
    "next_probe_or_seed_decision.json",
    "runtime_provider_next_action.json",
    "proof_obligations_ledger.json",
    "rollback_block_ledger_audit.json",
    "compute_budget_safe_stop_batch023.json",
    "failure_taxonomy_batch023.json",
    "precision_failure_log_batch023.json",
    "semantic_drift_guardrail_status.json",
    "activation_order_guardrail_status.json",
    "rollback_ghost_state_guardrail_status.json",
    "dependency_overlap_grouping_status.json",
    "consistency_reassertion_status.json",
    "artifact_packaging_policy.json",
    "thin_artifact_packaging_policy.json",
    "artifact_lineage_index.json",
    "evidence_carry_forward_manifest.json",
    "artifact_payload_budget.json",
    "artifact_minimality_audit.json",
    "lineage_equivalence_audit.json",
    "controllergate_claim_tier_update.json",
    "controllergate_capability_catalog_update.json",
    "public_language_audit_batch023.json",
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
        "telo" + "merase",
        "ribo" + "some",
        "nuclear " + "pore",
        "mi" + "totic spindle",
        "snow" + "flake",
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
    batch010_verification = read_json(POST_DIR / "batch010_active_memory_routing_artifact_verification.json")
    no_delta = read_json(POST_DIR / "batch010_no_routing_delta_diagnosis.json")
    batch011_recommendation = read_json(POST_DIR / "batch011_prospective_memory_challenge_recommendation.json")
    batch011_verification = read_json(POST_DIR / "batch011_prospective_memory_challenge_artifact_verification.json")
    no_fresh = read_json(POST_DIR / "batch011_no_fresh_candidate_diagnosis.json")
    batch012_recommendation = read_json(POST_DIR / "batch012_targeted_seed_recommendation.json")
    if batch010_verification.get("status") != "PASS":
        errors.append("batch010 artifact verification not PASS")
    if batch010_verification.get("actual_sha256") != "7737e503d9325bb42fa8db84a650e9ee72d23bcf0d3201482f80f6976ebf005d":
        errors.append("batch010 artifact SHA mismatch")
    if batch010_verification.get("actual_size") != 344744 or batch010_verification.get("entry_count") != 451:
        errors.append("batch010 artifact size or entry count mismatch")
    if batch010_verification.get("unsafe_path_count") != 0 or batch010_verification.get("duplicate_path_count") != 0 or batch010_verification.get("pycache_pyc_count") != 0:
        errors.append("batch010 artifact path/cache safety failed")
    batch010_records = batch010_verification.get("required_batch010_records_verified", {})
    if not isinstance(batch010_records, dict) or not all(batch010_records.values()):
        errors.append("batch010 required records were not all verified")
    if no_delta.get("status") != "PASS" or no_delta.get("status_code_weighting_ran") is not True:
        errors.append("batch010 no-routing-delta diagnosis invalid")
    if no_delta.get("routing_delta_detected") is not False or no_delta.get("routing_delta_reason_codes") != []:
        errors.append("batch010 no-routing-delta diagnosis overstates routing delta")
    if no_delta.get("baseline_source_ranking_hash") != no_delta.get("memory_weighted_source_ranking_hash"):
        errors.append("batch010 no-routing-delta diagnosis hash mismatch")
    if no_delta.get("retirement_required_for_memory_lift_claims") is not True or no_delta.get("further_memory_lift_attempts_without_new_features_allowed") is not False:
        errors.append("batch010 no-routing-delta diagnosis missing retirement boundary")
    if batch011_recommendation.get("status") != "READY_FOR_BATCH011_PROSPECTIVE_MEMORY_CHALLENGE":
        errors.append("batch011 prospective memory challenge recommendation missing")
    batch011_boundary = batch011_recommendation.get("claim_boundary", {})
    if not isinstance(batch011_boundary, dict) or batch011_boundary.get("full_scoring") != "NOT_RUN/disallowed" or batch011_boundary.get("self_maintaining_software") != "false/not_demonstrated":
        errors.append("batch011 recommendation claim boundary invalid")
    if batch011_verification.get("status") != "PASS":
        errors.append("batch011 artifact verification not PASS")
    if batch011_verification.get("artifact_sha256") != "65303892666866b083df8a3e11675e6b14f79a3a257d61620ab4b62d4ce58617":
        errors.append("batch011 artifact SHA mismatch")
    if batch011_verification.get("artifact_size_bytes") != 367179 or batch011_verification.get("zip_entry_count") != 488:
        errors.append("batch011 artifact size or entry count mismatch")
    if batch011_verification.get("unsafe_path_count") != 0 or batch011_verification.get("duplicate_path_count") != 0 or batch011_verification.get("pycache_pyc_payload_count") != 0:
        errors.append("batch011 artifact path/cache safety failed")
    if batch011_verification.get("artifact_level_manifest_checked") != 487 or batch011_verification.get("artifact_level_manifest_failures") != 0:
        errors.append("batch011 artifact manifest verification mismatch")
    output_checks = batch011_verification.get("output_manifest_checks", {})
    if not isinstance(output_checks, dict):
        errors.append("batch011 output manifest checks missing")
    else:
        expected_counts = {
            "post_v2_37_hardening_001": 74,
            "clean_replication_batch_002": 88,
            "clean_replication_batch_003": 28,
            "clean_replication_batch_004": 30,
            "clean_replication_batch_005": 71,
            "clean_replication_batch_006": 19,
            "clean_replication_batch_007": 44,
            "clean_replication_batch_008": 31,
            "clean_replication_batch_009": 29,
            "clean_replication_batch_010": 29,
            "clean_replication_batch_011": 33,
        }
        for root, expected_count in expected_counts.items():
            check = output_checks.get(root, {})
            if not isinstance(check, dict) or check.get("checked") != expected_count or check.get("failures") != 0:
                errors.append(f"batch011 output manifest check invalid for {root}")
    if no_fresh.get("status") != "PASS" or no_fresh.get("batch011_exact_blocker") != "batch011_no_fresh_candidate_verified":
        errors.append("batch011 no-fresh-candidate diagnosis invalid")
    if no_fresh.get("retrospective_candidate_retirement_passed") is not True or no_fresh.get("automated_fresh_candidate_attempts_verified") is not False:
        errors.append("batch011 no-fresh diagnosis status mismatch")
    if no_fresh.get("fresh_candidates_attempted") != 2 or no_fresh.get("prospective_memory_eligibility") != "BLOCK":
        errors.append("batch011 no-fresh diagnosis count/eligibility mismatch")
    if no_fresh.get("targeted_prospective_seed_required") is not True or no_fresh.get("existing_candidate_pool_exhausted_for_prospective_memory_challenge") is not True:
        errors.append("batch011 no-fresh diagnosis missing targeted-seed requirement")
    if batch012_recommendation.get("status") != "READY_FOR_BATCH012_TARGETED_PROSPECTIVE_SEED_INTAKE":
        errors.append("batch012 targeted seed recommendation missing")
    if batch012_recommendation.get("required_seed_path") != "external_seeds_pending/targeted_prospective_seed_batch012.json":
        errors.append("batch012 targeted seed path mismatch")
    batch012_artifact = read_json(POST_DIR / "batch012_targeted_seed_artifact_verification.json")
    batch012_missing = read_json(POST_DIR / "batch012_missing_seed_diagnosis.json")
    batch013_recommendation = read_json(POST_DIR / "batch013_acquisition_lock_recommendation.json")
    if batch012_artifact.get("status") != "PASS":
        errors.append("batch012 targeted-seed artifact verification not PASS")
    if batch012_artifact.get("artifact_sha256") != "0d6820881aee827bf594817eca99d67c60279d824e669e421238f80c50060dd2":
        errors.append("batch012 targeted-seed artifact SHA mismatch")
    if batch012_artifact.get("artifact_size_bytes") != 384028 or batch012_artifact.get("file_entry_count") != 521:
        errors.append("batch012 targeted-seed artifact size or entry count mismatch")
    if batch012_artifact.get("unsafe_path_count") != 0 or batch012_artifact.get("duplicate_path_count") != 0 or batch012_artifact.get("pycache_pyc_payload_count") != 0:
        errors.append("batch012 targeted-seed artifact path/cache safety failed")
    if batch012_artifact.get("artifact_level_manifest_failures") != 0:
        errors.append("batch012 targeted-seed artifact manifest verification failed")
    if batch012_missing.get("status") != "PASS" or batch012_missing.get("batch012_exact_blocker") != "targeted_prospective_seed_missing_or_invalid":
        errors.append("batch012 missing-seed diagnosis invalid")
    if batch012_missing.get("native_verification_ran") is not False or batch012_missing.get("prospective_memory_experiment_ran") is not False:
        errors.append("batch012 missing-seed diagnosis says downstream gates ran")
    if batch013_recommendation.get("status") != "READY_FOR_BATCH013_ACQUISITION_LOCKS":
        errors.append("batch013 acquisition-lock recommendation missing")
    if batch013_recommendation.get("batch013_required_seed_path") != "external_seeds_pending/targeted_prospective_seed_batch013.json":
        errors.append("batch013 targeted seed path mismatch")
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


def audit_batch011_records() -> list[str]:
    errors: list[str] = []
    for name in BATCH011_REQUIRED:
        if not (BATCH011_DIR / name).is_file():
            errors.append(f"batch011 missing required file {name}")
    if errors:
        return errors
    manifest = verify_manifest(BATCH011_DIR)
    if manifest.get("status") != "PASS":
        errors.append(f"batch011 manifest failed: {manifest}")
    state = read_json(BATCH011_DIR / "consolidated_state_clean_replication_batch_011.json")
    policy = read_json(BATCH011_DIR / "prospective_memory_challenge_policy.json")
    eligibility = read_json(BATCH011_DIR / "prospective_memory_eligibility_gate.json")
    lead_pool = read_json(BATCH011_DIR / "fresh_candidate_lead_pool.json")
    attempts = read_json(BATCH011_DIR / "fresh_candidate_attempts.json")
    rejection = read_json(BATCH011_DIR / "fresh_candidate_rejection_ledger.json")
    retired = read_json(BATCH011_DIR / "retired_memory_challenge_candidates.json")
    skip_retirement = read_json(BATCH011_DIR / "darker_skip_glob_memory_challenge_retirement.json")
    source_trace = read_json(BATCH011_DIR / "fresh_candidate_source_mode_trace.json")
    native_attempts = read_json(BATCH011_DIR / "native_candidate_attempts.json")
    issue_attempts = read_json(BATCH011_DIR / "issue_derived_candidate_attempts.json")
    verification_attempts = read_json(BATCH011_DIR / "candidate_verification_attempts.json")
    admissions = read_json(BATCH011_DIR / "candidate_admission_decisions.json")
    curvature_policy = read_json(BATCH011_DIR / "curvature_selection_policy.json")
    two_winner_policy = read_json(BATCH011_DIR / "two_winner_source_selection_policy.json")
    strict_delta = read_json(BATCH011_DIR / "strict_minimum_delta_policy_batch011.json")
    curvature_scores = read_json(BATCH011_DIR / "candidate_curvature_scores.json")
    route_scores = read_json(BATCH011_DIR / "source_route_curvature_scores.json")
    prereg = read_json(BATCH011_DIR / "prospective_experiment_preregistration.json")
    memory_enabled = read_json(BATCH011_DIR / "memory_enabled_policy_batch011.json")
    memory_disabled = read_json(BATCH011_DIR / "memory_disabled_null_ensemble_policy_batch011.json")
    quarantine = read_json(BATCH011_DIR / "prospective_patch_artifact_quarantine_policy.json")
    memory_results = read_json(BATCH011_DIR / "memory_enabled_run_results.json")
    null_results = read_json(BATCH011_DIR / "null_ensemble_run_results.json")
    null_summary = read_json(BATCH011_DIR / "null_ensemble_summary.json")
    score = read_json(BATCH011_DIR / "matched_null_ensemble_separation_score.json")
    lift = read_json(BATCH011_DIR / "prospective_memory_lift_evaluation.json")
    successes = read_json(BATCH011_DIR / "repair_successes.json")
    claim = read_json(BATCH011_DIR / "claim_boundary.json")
    traceability = read_json(BATCH011_DIR / "notebooklm_advice_traceability_status.json")
    carry = read_json(BATCH011_DIR / "carry_forward_blocker_register.json")
    blocker = "batch011_no_fresh_candidate_verified"
    repaired_ids = {
        "py_bugger_issue_65",
        "darker_non_ascii_drop_changes",
        "darker_stdin_filename",
        "darker_skip_glob_failing_test",
    }
    if policy.get("status") != "PASS" or policy.get("requires_fresh_candidate") is not True:
        errors.append("prospective memory challenge policy invalid")
    if policy.get("forbids_repaired_candidate_reuse") is not True:
        errors.append("prospective_memory_candidate_not_fresh")
    if eligibility.get("status") != "BLOCK" or eligibility.get("blocker") != blocker:
        errors.append("batch011 eligibility blocker mismatch")
    if eligibility.get("eligible") is not False:
        errors.append("prospective memory eligibility overclaimed")
    if lead_pool.get("fresh_candidate_count") != 2:
        errors.append("batch011 expected two fresh lead-pool candidates")
    if not isinstance(attempts, list) or len(attempts) != 2:
        errors.append("batch011 fresh candidate attempts count mismatch")
    for item in attempts if isinstance(attempts, list) else []:
        if item.get("candidate_id") in repaired_ids:
            errors.append("retired_memory_challenge_candidate_reused")
        if item.get("fresh_candidate") is not True:
            errors.append("batch011 fresh attempt missing fresh marker")
        if item.get("fresh_candidate_verified") is not False:
            errors.append("batch011 unexpectedly verified a fresh candidate")
        if item.get("failure_replay_status") != "PASSING_PRE_PATCH_NOT_A_FAILURE":
            errors.append("batch011 fresh attempt blocker changed")
        if item.get("verification_source_sha256") != read_json(BATCH011_DIR / "prospective_memory_eligibility_gate.json").get("candidate_verification_source_sha256"):
            errors.append("batch011 attempt source hash mismatch")
    rejection_ids = {item.get("candidate_id") for item in rejection if isinstance(item, dict)}
    if not repaired_ids.issubset(rejection_ids):
        errors.append("prior repaired candidates not rejected")
    if not any(isinstance(item, dict) and item.get("rejection_reason") == blocker for item in rejection):
        errors.append("batch011 fresh rejection blocker missing")
    retired_items = retired.get("retired_candidates", [])
    retired_ids = {item.get("candidate_id") for item in retired_items if isinstance(item, dict)}
    if retired.get("status") != "PASS" or not repaired_ids.issubset(retired_ids):
        errors.append("retired memory challenge candidates record invalid")
    if skip_retirement.get("candidate_id") != "darker_skip_glob_failing_test" or skip_retirement.get("retired_from_new_memory_lift_attempts") is not True:
        errors.append("darker_skip_glob retirement missing")
    if skip_retirement.get("blocker_if_reused") != "retired_memory_challenge_candidate_reused":
        errors.append("retired candidate reuse blocker missing")
    if source_trace[0].get("attempted") is not True or source_trace[1].get("attempted") is not False:
        errors.append("batch011 source mode trace invalid")
    if native_attempts != attempts or verification_attempts != attempts:
        errors.append("batch011 native/verification attempts diverge")
    if issue_attempts != []:
        errors.append("batch011 issue-derived path unexpectedly attempted")
    if not isinstance(admissions, list) or not admissions:
        errors.append("batch011 admission decisions missing")
    if any(item.get("admission_decision") in {"admitted_native_candidate", "admitted_issue_derived_candidate"} for item in admissions if isinstance(item, dict)):
        errors.append("candidate admitted despite no verified fresh failure")
    if curvature_policy.get("status") != "PASS" or two_winner_policy.get("status") != "PASS":
        errors.append("curvature or two-winner policy missing")
    if strict_delta.get("status") != "PASS" or strict_delta.get("arbitrary_score_or_metadata_shuffle_rejected") is not True:
        errors.append("strict minimum-delta policy invalid")
    if curvature_scores.get("status") != "NOT_RUN" or curvature_scores.get("blocker") != blocker:
        errors.append("batch011 curvature scores should not run without verified candidate")
    if route_scores.get("status") != "NOT_RUN" or route_scores.get("blocker") != blocker:
        errors.append("batch011 source route scores should not run without verified candidate")
    if prereg.get("status") != "NOT_RUN" or prereg.get("patch_generated_before_preregistration") is not False:
        errors.append("prospective preregistration record invalid")
    if memory_enabled.get("status") != "NOT_RUN" or memory_disabled.get("status") != "NOT_RUN":
        errors.append("matched-null policies should remain not run")
    if quarantine.get("status") != "PASS" or quarantine.get("patch_artifacts_not_created") is not True:
        errors.append("batch011 patch artifact quarantine invalid")
    if memory_results.get("status") != "NOT_RUN" or null_results.get("status") != "NOT_RUN":
        errors.append("memory-enabled or null arm ran without eligibility")
    if null_summary.get("null_ensemble_run_count") != 0 or null_summary.get("null_success_rate") is not None:
        errors.append("null ensemble summary invalid")
    if score.get("score_computed") is not False or score.get("matched_null_ensemble_separation_score") is not None:
        errors.append("matched-null score computed without candidate")
    if lift.get("preliminary_prospective_single_candidate_memory_separation_evidence") is not False:
        errors.append("prospective memory lift overclaimed")
    if lift.get("prospective_memory_lift_status") != "not_demonstrated" or lift.get("blocker") != blocker:
        errors.append("prospective memory lift blocker mismatch")
    if successes != []:
        errors.append("batch011 repair success recorded without authorized run")
    if claim.get("full_scoring") != "NOT_RUN/disallowed" or claim.get("full_memory_lift_claimed") is not False:
        errors.append("batch011 claim boundary overclaimed")
    if claim.get("self_maintaining_software") != "false/not_demonstrated":
        errors.append("batch011 self-maintaining overclaim")
    if claim.get("confirmed_native_repair_episode_count") != 4:
        errors.append("batch011 repair episode count changed")
    if state.get("status") != "BLOCK" or state.get("exact_blocker") != blocker:
        errors.append("batch011 state blocker mismatch")
    if state.get("fresh_candidates_attempted_count") != 2 or state.get("fresh_candidate_verified") is not False:
        errors.append("batch011 state fresh candidate count/status mismatch")
    if state.get("repair_only_fallback_attempted") is not False or state.get("additional_external_repair_acquired") is not False:
        errors.append("batch011 repair-only fallback over-ran")
    if state.get("confirmed_native_repair_episode_count") != 4:
        errors.append("batch011 state repair count changed")
    if traceability.get("status_code_feature_weighting") != "implemented_active":
        errors.append("Batch011 traceability missing status-code feature weighting")
    if traceability.get("curvature_based_candidate_selection") != "implemented_active":
        errors.append("Batch011 traceability missing curvature selection")
    if traceability.get("two_winner_source_selection") != "implemented_active":
        errors.append("Batch011 traceability missing two-winner selection")
    if traceability.get("active_failure_memory_routing") != "implemented_partial":
        errors.append("Batch011 active routing overclaimed")
    blockers = carry.get("blockers", [])
    if carry.get("status") != "PASS" or not any(isinstance(item, dict) and item.get("blocker") == blocker for item in blockers):
        errors.append("Batch011 carry-forward blocker missing")
    return errors


def audit_batch012_records() -> list[str]:
    errors: list[str] = []
    blocker = "targeted_prospective_seed_missing_or_invalid"
    for name in BATCH012_REQUIRED:
        if not (BATCH012_DIR / name).is_file():
            errors.append(f"batch012 missing required file {name}")
    if errors:
        return errors
    manifest = verify_manifest(BATCH012_DIR)
    if manifest.get("status") != "PASS":
        errors.append(f"batch012 manifest failed: {manifest}")
    state = read_json(BATCH012_DIR / "consolidated_state_clean_replication_batch_012.json")
    presence = read_json(BATCH012_DIR / "targeted_seed_presence_check.json")
    schema = read_json(BATCH012_DIR / "targeted_seed_schema_validation.json")
    forbidden = read_json(BATCH012_DIR / "targeted_seed_forbidden_evidence_audit.json")
    intake = read_json(BATCH012_DIR / "targeted_seed_intake_report.json")
    native = read_json(BATCH012_DIR / "native_verification_result.json")
    issue_policy = read_json(BATCH012_DIR / "issue_derived_harness_policy.json")
    issue_result = read_json(BATCH012_DIR / "issue_derived_harness_verification_result.json")
    eligibility = read_json(BATCH012_DIR / "prospective_memory_eligibility_gate.json")
    route = read_json(BATCH012_DIR / "route_diversity_status.json")
    mappable = read_json(BATCH012_DIR / "status_feature_mappability.json")
    matched = read_json(BATCH012_DIR / "matched_null_ensemble_summary.json")
    repair_only = read_json(BATCH012_DIR / "repair_only_fallback_summary.json")
    claim = read_json(BATCH012_DIR / "claim_boundary.json")
    traceability = read_json(BATCH012_DIR / "notebooklm_advice_traceability_status.json")
    carry = read_json(BATCH012_DIR / "carry_forward_blocker_register.json")
    next_action = (BATCH012_DIR / "targeted_seed_required_next_action.md").read_text(encoding="utf-8")
    if presence.get("status") != "BLOCK" or presence.get("seed_present") is not False or presence.get("blocker") != blocker:
        errors.append("batch012 targeted seed presence check did not block missing seed")
    if presence.get("automated_fresh_candidate_search_attempted") is not False:
        errors.append("batch012 attempted automated fresh candidate search")
    if schema.get("status") != "BLOCK" or schema.get("valid") is not False or schema.get("blocker") != blocker:
        errors.append("batch012 seed schema validation blocker mismatch")
    if forbidden.get("status") not in {"NOT_RUN", "BLOCK"} or forbidden.get("blocker") != blocker:
        errors.append("batch012 forbidden evidence audit did not stop on missing seed")
    if intake.get("status") != "BLOCK" or intake.get("exact_blocker") != blocker:
        errors.append("batch012 seed intake report did not record blocker")
    for field in ["native_verification_status", "issue_derived_verification_status", "matched_null_ensemble_status"]:
        if intake.get(field) != "NOT_RUN":
            errors.append(f"batch012 {field} should be NOT_RUN")
    if intake.get("repair_only_fallback_attempted") is not False:
        errors.append("batch012 repair-only fallback ran without seed")
    if native.get("status") != "NOT_RUN" or native.get("native_candidate_verified") is not False:
        errors.append("batch012 native verification ran without seed")
    if issue_policy.get("increments_native_repair_count") is not False:
        errors.append("batch012 issue-derived policy increments native count")
    if issue_result.get("status") != "NOT_RUN" or issue_result.get("increments_native_repair_count") is not False:
        errors.append("batch012 issue-derived verification ran or changed counts")
    if eligibility.get("status") != "NOT_RUN" or eligibility.get("eligible") is not False or eligibility.get("blocker") != blocker:
        errors.append("batch012 prospective eligibility should be NOT_RUN with missing seed")
    if route.get("status") != "NOT_RUN" or mappable.get("status") != "NOT_RUN":
        errors.append("batch012 route diversity or mappable status features ran")
    if matched.get("status") != "NOT_RUN" or matched.get("null_ensemble_run_count") != 0 or matched.get("matched_null_score") is not None:
        errors.append("batch012 matched-null ensemble ran or scored without seed")
    if repair_only.get("repair_only_fallback_attempted") is not False or repair_only.get("preliminary_prospective_single_candidate_memory_separation_evidence") is not False:
        errors.append("batch012 repair-only fallback overclaimed")
    if claim.get("full_scoring") != "NOT_RUN/disallowed" or claim.get("full_memory_lift_claimed") is not False:
        errors.append("batch012 claim boundary overclaimed")
    if claim.get("self_maintaining_software") != "false/not_demonstrated":
        errors.append("batch012 self-maintaining claim changed")
    if claim.get("confirmed_native_repair_episode_count") != 4 or claim.get("confirmed_issue_derived_repair_episode_count") != 0:
        errors.append("batch012 repair counts changed")
    if state.get("status") != "BLOCK" or state.get("exact_blocker") != blocker:
        errors.append("batch012 state blocker mismatch")
    expected_not_run = [
        "native_verification_status",
        "issue_derived_verification_status",
        "prospective_memory_eligibility_status",
        "route_diversity_status",
        "mappable_status_feature_status",
    ]
    for field in expected_not_run:
        if state.get(field) != "NOT_RUN":
            errors.append(f"batch012 state {field} should be NOT_RUN")
    if state.get("targeted_seed_present") is not False or state.get("targeted_seed_validation_status") != "BLOCK":
        errors.append("batch012 targeted seed state mismatch")
    if state.get("matched_null_ensemble_run_count") != 0 or state.get("matched_null_score") is not None:
        errors.append("batch012 matched-null state over-ran")
    if state.get("repair_only_fallback_attempted") is not False or state.get("additional_native_repair_acquired") is not False:
        errors.append("batch012 repair fallback state over-ran")
    if state.get("additional_issue_derived_repair_feasibility") is not False:
        errors.append("batch012 issue-derived repair feasibility overclaimed")
    if traceability.get("status") != "PASS" or traceability.get("blocker") != blocker:
        errors.append("batch012 traceability status missing blocker")
    blockers = carry.get("blockers", [])
    if carry.get("status") != "PASS" or not any(isinstance(item, dict) and item.get("blocker") == blocker for item in blockers):
        errors.append("batch012 carry-forward blocker missing")
    if blocker not in next_action or "external_seeds_pending/targeted_prospective_seed_batch012.json" not in next_action:
        errors.append("batch012 next-action file missing seed path or blocker")
    return errors


def audit_batch013_records() -> list[str]:
    errors: list[str] = []
    blocker = "targeted_prospective_seed_missing_or_invalid_after_locks_ready"
    for name in BATCH013_REQUIRED:
        if not (BATCH013_DIR / name).is_file():
            errors.append(f"batch013 missing required file {name}")
    if errors:
        return errors
    manifest = verify_manifest(BATCH013_DIR)
    if manifest.get("status") != "PASS":
        errors.append(f"batch013 manifest failed: {manifest}")
    state = read_json(BATCH013_DIR / "consolidated_state_clean_replication_batch_013.json")
    lock_stack = read_json(BATCH013_DIR / "acquisition_lock_stack_status.json")
    baseline = read_json(BATCH013_DIR / "baseline_registry_drift_precheck.json")
    env_lock = read_json(BATCH013_DIR / "source_commit_environment_lock_summary.json")
    command = read_json(BATCH013_DIR / "target_command_manifest_summary.json")
    workspace = read_json(BATCH013_DIR / "workspace_purity_report.json")
    presence = read_json(BATCH013_DIR / "targeted_seed_presence_check.json")
    schema = read_json(BATCH013_DIR / "targeted_seed_schema_validation.json")
    forbidden = read_json(BATCH013_DIR / "targeted_seed_forbidden_evidence_audit.json")
    intake = read_json(BATCH013_DIR / "targeted_seed_intake_report.json")
    git_tracking = read_json(BATCH013_DIR / "targeted_seed_git_tracking_audit.json")
    workflow_visibility = read_json(BATCH013_DIR / "targeted_seed_workflow_visibility_audit.json")
    gate_trace = read_json(BATCH013_DIR / "batch013_gate_chain_execution_trace.json")
    gate_audit = read_json(BATCH013_DIR / "batch013_gate_dependency_audit.json")
    rollback = read_json(BATCH013_DIR / "rollback_block_ledger_audit.json")
    proof = read_json(BATCH013_DIR / "proof_obligations_ledger.json")
    cross_gate = read_json(BATCH013_DIR / "five_locks_curvature_cross_gate.json")
    filtering = read_json(BATCH013_DIR / "active_context_filter_manifest.json")
    filter_delta = read_json(BATCH013_DIR / "context_filter_delta_audit.json")
    freeze = read_json(BATCH013_DIR / "curvature_heuristic_freeze.json")
    formula = read_json(BATCH013_DIR / "curvature_score_formula.json")
    thresholds = read_json(BATCH013_DIR / "curvature_thresholds.json")
    curvature_status = read_json(BATCH013_DIR / "curvature_logic_enforcement_status.json")
    curvature_vectors = read_json(BATCH013_DIR / "candidate_curvature_feature_vectors.json")
    basin = read_json(BATCH013_DIR / "basin_stability_scores.json")
    memory_routing = read_json(BATCH013_DIR / "curvature_memory_routing_audit.json")
    fragment_plan = read_json(BATCH013_DIR / "curvature_fragment_plan.json")
    null_fairness = read_json(BATCH013_DIR / "null_ensemble_curvature_fairness_audit.json")
    curvature_claim = read_json(BATCH013_DIR / "curvature_claim_boundary.json")
    issue_temporal = read_json(BATCH013_DIR / "issue_derived_temporal_and_classification_audit.json")
    native = read_json(BATCH013_DIR / "native_verification_result.json")
    issue_result = read_json(BATCH013_DIR / "issue_derived_harness_verification_result.json")
    eligibility = read_json(BATCH013_DIR / "prospective_memory_eligibility_gate.json")
    matched = read_json(BATCH013_DIR / "matched_null_ensemble_summary.json")
    repair_only = read_json(BATCH013_DIR / "repair_only_fallback_summary.json")
    claim = read_json(BATCH013_DIR / "claim_boundary.json")
    traceability = read_json(BATCH013_DIR / "notebooklm_advice_traceability_status.json")
    carry = read_json(BATCH013_DIR / "carry_forward_blocker_register.json")
    next_action = read_json(BATCH013_DIR / "targeted_seed_next_action.json")
    if state.get("status") != "BLOCK" or state.get("exact_blocker") != blocker:
        errors.append("batch013 state blocker mismatch")
    if lock_stack.get("locks_ready_before_seed_block") is not True or lock_stack.get("exact_blocker") != blocker:
        errors.append("batch013 lock stack did not become ready before seed block")
    for label, data in [
        ("baseline", baseline),
        ("environment lock", env_lock),
        ("command manifest", command),
        ("workspace purity", workspace),
    ]:
        if data.get("status") != "PASS":
            errors.append(f"batch013 {label} did not PASS before seed block")
    if baseline.get("confirmed_native_repair_count") != 4 or baseline.get("confirmed_issue_derived_repair_count") != 0:
        errors.append("batch013 baseline registry counts changed")
    if env_lock.get("lock_to_source_commit_status") != "READY_NO_SEED" or env_lock.get("source_acquisition_allowed") is not False:
        errors.append("batch013 environment lock should be ready without source acquisition")
    if command.get("target_command_manifest_status") != "READY_NO_SEED" or command.get("target_replay_allowed") is not False:
        errors.append("batch013 command manifest should be ready without replay")
    if workspace.get("workspace_purity_status") != "READY_NO_SEED" or workspace.get("workspace_created") is not False:
        errors.append("batch013 workspace should not be created without seed")
    if presence.get("status") != "BLOCK" or presence.get("seed_present") is not False or presence.get("blocker") != blocker:
        errors.append("batch013 targeted seed presence did not block after locks")
    if schema.get("status") != "BLOCK" or schema.get("valid") is not False or schema.get("blocker") != blocker:
        errors.append("batch013 schema validation blocker mismatch")
    if forbidden.get("status") != "NOT_RUN" or forbidden.get("blocker") != blocker:
        errors.append("batch013 forbidden-evidence audit should not run without seed")
    if intake.get("status") != "BLOCK" or intake.get("locks_completed_before_seed_block") is not True or intake.get("exact_blocker") != blocker:
        errors.append("batch013 seed intake report did not preserve lock-before-block order")
    if git_tracking.get("status") != "BLOCK" or git_tracking.get("file_exists") is not False or git_tracking.get("git_tracked") is not False:
        errors.append("batch013 git tracking audit should block missing seed")
    if workflow_visibility.get("status") != "BLOCK" or workflow_visibility.get("workflow_visible") is not True:
        errors.append("batch013 workflow visibility should identify configured seed path while blocking missing seed")
    if not isinstance(gate_trace, list) or len(gate_trace) < 5:
        errors.append("batch013 gate trace malformed")
    else:
        first_block = next((item for item in gate_trace if item.get("status") == "BLOCK"), {})
        if first_block.get("gate_id") != "targeted_seed_presence_and_git_tracking" or first_block.get("blocker") != blocker:
            errors.append("batch013 first blocking gate mismatch")
        downstream = [item for item in gate_trace if int(item.get("gate_index", 0)) > int(first_block.get("gate_index", 0) or 0)]
        if any(item.get("status") != "NOT_RUN" or item.get("blocked_by_gate") != "targeted_seed_presence_and_git_tracking" for item in downstream):
            errors.append("batch013 downstream gates ran after seed block")
    if gate_audit.get("status") != "PASS" or gate_audit.get("blocked_gate") != "targeted_seed_presence_and_git_tracking":
        errors.append("batch013 gate dependency audit failed")
    if rollback.get("status") != "PASS" or rollback.get("rollback_block_count") != 1:
        errors.append("batch013 rollback block ledger failed")
    entries = proof.get("entries", [])
    rollback_entries = [entry for entry in entries if isinstance(entry, dict) and entry.get("entry_type") == "ROLLBACK_BLOCK"]
    if proof.get("status") != "PASS" or not rollback_entries:
        errors.append("batch013 proof ledger missing rollback block")
    elif not rollback_entries[0].get("previous_state_hash") or rollback_entries[0].get("blocker") != blocker:
        errors.append("batch013 rollback block missing previous state hash or blocker")
    if cross_gate.get("status") != "PASS" or cross_gate.get("source_acquisition_allowed") is not False or cross_gate.get("repair_generation_allowed") is not False:
        errors.append("batch013 five-lock cross gate allowed downstream work")
    if filtering.get("status") != "NOT_RUN" or filter_delta.get("status") != "NOT_RUN":
        errors.append("batch013 active context filtering should not run without seed")
    if freeze.get("status") != "PASS" or freeze.get("formula_frozen_before_seed_intake") is not True:
        errors.append("batch013 scoring freeze missing")
    if formula.get("formula_version") != freeze.get("formula_version") or thresholds.get("formula_version") != freeze.get("formula_version"):
        errors.append("batch013 scoring formula/threshold version mismatch")
    if curvature_status.get("status") != "PASS_WITH_SEED_BLOCKED" or curvature_status.get("curvature_used_as_proof") is not False:
        errors.append("batch013 routing-score enforcement invalid")
    if curvature_vectors.get("status") != "NOT_RUN" or basin.get("status") != "NOT_RUN" or memory_routing.get("status") != "NOT_RUN":
        errors.append("batch013 routing-score candidate records ran without seed")
    if fragment_plan.get("status") != "NOT_RUN" or null_fairness.get("status") != "NOT_RUN":
        errors.append("batch013 fragment/null curvature records should be not run")
    if curvature_claim.get("memory_separation_claim_allowed") is not False or curvature_claim.get("full_memory_lift_claimed") is not False:
        errors.append("batch013 routing-score claim boundary overclaimed")
    if issue_temporal.get("status") != "PASS" or issue_temporal.get("issue_derived_not_classified_as_native") is not True:
        errors.append("batch013 issue-derived classification guard invalid")
    for label, data in [
        ("native", native),
        ("issue-derived", issue_result),
        ("eligibility", eligibility),
        ("matched-null", matched),
    ]:
        if data.get("status") != "NOT_RUN":
            errors.append(f"batch013 {label} ran without seed")
    if matched.get("null_ensemble_run_count") != 0 or matched.get("matched_null_score") is not None:
        errors.append("batch013 matched-null scored without seed")
    if repair_only.get("repair_only_fallback_attempted") is not False or repair_only.get("preliminary_prospective_single_candidate_memory_separation_evidence") is not False:
        errors.append("batch013 repair-only fallback overclaimed")
    if claim.get("full_scoring") != "NOT_RUN/disallowed" or claim.get("full_memory_lift_claimed") is not False:
        errors.append("batch013 claim boundary overclaimed")
    if claim.get("confirmed_native_repair_episode_count") != 4 or claim.get("confirmed_issue_derived_repair_episode_count") != 0:
        errors.append("batch013 repair counts changed")
    if traceability.get("status") != "PASS" or traceability.get("blocker") != blocker:
        errors.append("batch013 traceability missing blocker")
    blockers = carry.get("blockers", [])
    if carry.get("status") != "PASS" or not any(isinstance(item, dict) and item.get("blocker") == blocker for item in blockers):
        errors.append("batch013 carry-forward blocker missing")
    if next_action.get("next_allowed_action") != "commit_reviewed_targeted_prospective_seed_batch013" or next_action.get("required_git_status") != "tracked":
        errors.append("batch013 next action did not require tracked seed")
    return errors


def audit_batch014_records() -> list[str]:
    errors: list[str] = []
    for name in BATCH014_REQUIRED:
        if not (BATCH014_DIR / name).is_file():
            errors.append(f"batch014 missing required file {name}")
    if errors:
        return errors
    manifest = verify_manifest(BATCH014_DIR)
    if manifest.get("status") != "PASS":
        errors.append(f"batch014 manifest failed: {manifest}")
    state = read_json(BATCH014_DIR / "consolidated_state_clean_replication_batch_014.json")
    path_resolution = read_json(BATCH014_DIR / "targeted_seed_path_resolution.json")
    git_tracking = read_json(BATCH014_DIR / "targeted_seed_git_tracking_audit.json")
    workflow_visibility = read_json(BATCH014_DIR / "targeted_seed_workflow_visibility_audit.json")
    schema = read_json(BATCH014_DIR / "targeted_seed_schema_validation.json")
    harmonization = read_json(BATCH014_DIR / "seed_schema_harmonization_result.json")
    normalized = read_json(BATCH014_DIR / "normalized_targeted_seed_record.json")
    firewall = read_json(BATCH014_DIR / "issue_text_solution_section_firewall_audit.json")
    dataset = read_json(BATCH014_DIR / "dataset_lead_firewall_audit.json")
    native_guard = read_json(BATCH014_DIR / "proposed_native_seed_verification_guard.json")
    native_check = read_json(BATCH014_DIR / "darker_issue_112_native_seed_verification.json")
    downgrade = read_json(BATCH014_DIR / "native_to_issue_derived_downgrade_report.json")
    issue112_manifest = read_json(BATCH014_DIR / "issue112_external_command_manifest.json")
    issue112_claim = read_json(BATCH014_DIR / "issue112_claim_boundary.json")
    source_selection = read_json(BATCH014_DIR / "source_commit_selection.json")
    workspace = read_json(BATCH014_DIR / "workspace_purity_report.json")
    env_lock = read_json(BATCH014_DIR / "source_commit_environment_lock_summary.json")
    command = read_json(BATCH014_DIR / "target_command_manifest_summary.json")
    baseline = read_json(BATCH014_DIR / "baseline_registry_drift_precheck.json")
    rollback = read_json(BATCH014_DIR / "rollback_block_ledger_audit.json")
    lock_stack = read_json(BATCH014_DIR / "acquisition_lock_stack_status.json")
    gate_trace = read_json(BATCH014_DIR / "batch014_gate_chain_execution_trace.json")
    gate_dependency = read_json(BATCH014_DIR / "batch014_gate_dependency_audit.json")
    harness = read_json(BATCH014_DIR / "issue_derived_harness_verification_result.json")
    classification = read_json(BATCH014_DIR / "issue_derived_temporal_and_classification_audit.json")
    eligibility = read_json(BATCH014_DIR / "prospective_memory_eligibility_gate.json")
    curvature_claim = read_json(BATCH014_DIR / "curvature_claim_boundary.json")
    repair_only = read_json(BATCH014_DIR / "repair_only_fallback_status.json")
    matched = read_json(BATCH014_DIR / "matched_null_ensemble_summary.json")
    proof = read_json(BATCH014_DIR / "proof_obligations_ledger.json")
    traceability = read_json(BATCH014_DIR / "notebooklm_advice_traceability_status.json")

    if path_resolution.get("status") != "PASS" or path_resolution.get("seed_path_used") != "external_seeds_pending/targeted_prospective_seed_batch013.json":
        errors.append("batch014 canonical seed path was not used")
    if git_tracking.get("status") != "PASS" or git_tracking.get("git_tracked") is not True or git_tracking.get("committed_exactly") is not True:
        errors.append("batch014 seed is not committed and tracked")
    if workflow_visibility.get("status") != "PASS" or workflow_visibility.get("workflow_visible") is not True:
        errors.append("batch014 seed is not workflow-visible")
    if schema.get("status") != "PASS" or harmonization.get("status") != "PASS":
        errors.append("batch014 seed schema harmonization failed")
    if normalized.get("candidate_id") != "darker_issue_112_relative_git_dir" or normalized.get("candidate_class") != "issue_derived_reproduction_candidate":
        errors.append("batch014 normalized seed identity/class mismatch")
    if firewall.get("status") != "PASS" or firewall.get("redacted_issue_snapshot_used") is not True or firewall.get("forbidden_section_hits"):
        errors.append("batch014 redacted issue snapshot firewall failed")
    if dataset.get("status") != "PASS" or dataset.get("bugsinpy_global_block_active") is not True:
        errors.append("batch014 dataset lead firewall failed")
    if native_guard.get("applies_to_issue112") is not True or native_guard.get("native_claimed") is not False:
        errors.append("batch014 native guard did not identify issue #112 as issue-derived")
    if native_check.get("source_commit_sha_8f39377_required_commit_object_if_used") is not True:
        errors.append("batch014 issue #112 special commit guard missing")
    if downgrade.get("native_count_increment_allowed") is not False or downgrade.get("native_memory_claim_allowed") is not False:
        errors.append("batch014 native downgrade/count boundary failed")
    if issue112_manifest.get("forbidden_framework_state_used") is not False or "test_black_diff" in json.dumps(issue112_manifest):
        errors.append("batch014 issue #112 command manifest used forbidden/native target state")
    if issue112_claim.get("native_repair_count_increment_allowed") is not False or issue112_claim.get("native_memory_separation_claim_allowed") is not False:
        errors.append("batch014 issue #112 claim boundary overclaimed")
    if source_selection.get("status") != "PASS" or source_selection.get("object_type") != "commit":
        errors.append("batch014 source commit selection did not resolve a commit")
    for label, data in [("workspace", workspace), ("environment lock", env_lock), ("command manifest", command), ("baseline", baseline)]:
        if data.get("status") != "PASS":
            errors.append(f"batch014 {label} did not pass before replay")
    if rollback.get("status") != "PASS" or rollback.get("rollback_block_count", 0) < 1:
        errors.append("batch014 rollback block ledger missing")
    if lock_stack.get("five_locks_pass_before_replay") is not True:
        errors.append("batch014 replay occurred without five locks")
    if gate_dependency.get("status") != "PASS" or not isinstance(gate_trace, list):
        errors.append("batch014 gate-chain audit failed")
    if harness.get("candidate_class") != "issue_derived_reproduction_candidate" or harness.get("native_count_increment_allowed") is not False:
        errors.append("batch014 harness conflated evidence classes")
    if classification.get("increments_native_count") is not False:
        errors.append("batch014 issue-derived classification increments native count")
    if eligibility.get("native_memory_separation_allowed") is not False or matched.get("null_ensemble_run_count") != 0:
        errors.append("batch014 memory/matched-null boundary over-ran")
    if repair_only.get("repair_only_fallback_attempted") is not False:
        errors.append("batch014 repair-only fallback ran despite unverified issue-derived candidate")
    if curvature_claim.get("memory_separation_claim_allowed") is not False:
        errors.append("batch014 curvature claim boundary overclaimed")
    if state.get("confirmed_native_repair_episode_count") != 4 or state.get("confirmed_issue_derived_repair_episode_count") != 0:
        errors.append("batch014 repair counts changed incorrectly")
    if state.get("full_scoring") != "NOT_RUN/disallowed" or state.get("self_maintaining_software") != "false/not_demonstrated":
        errors.append("batch014 claim boundary changed")
    if not any(isinstance(item, dict) and item.get("entry_type") == "ROLLBACK_BLOCK" for item in proof):
        errors.append("batch014 proof ledger missing rollback block")
    if traceability.get("status") != "PASS":
        errors.append("batch014 traceability missing")
    return errors


def audit_batch015_records() -> list[str]:
    errors: list[str] = []
    for name in BATCH015_REQUIRED:
        if not (BATCH015_DIR / name).is_file():
            errors.append(f"batch015 missing required file {name}")
    if errors:
        return errors
    manifest = verify_manifest(BATCH015_DIR)
    if manifest.get("status") != "PASS":
        errors.append(f"batch015 manifest failed: {manifest}")

    state = read_json(BATCH015_DIR / "consolidated_state_clean_replication_batch_015.json")
    latest = read_json(BATCH015_DIR / "latest_artifact_boundary_status.json")
    validation = read_json(BATCH015_DIR / "validation_path_continuity_status.json")
    claim = read_json(BATCH015_DIR / "claim_boundary_batch015.json")
    preservation = read_json(BATCH015_DIR / "repair_episode_count_preservation.json")
    native_boundary = read_json(BATCH015_DIR / "native_issue_derived_count_boundary.json")
    runtime_status = read_json(BATCH015_DIR / "runtime_wrapper_mvp_status.json")
    boundary = read_json(BATCH015_DIR / "execution_boundary_gateway_policy.json")
    sandbox = read_json(BATCH015_DIR / "isolated_repair_sandbox_policy.json")
    drift = read_json(BATCH015_DIR / "dependency_drift_chaperone_policy.json")
    excision = read_json(BATCH015_DIR / "active_ast_excision_probe_policy.json")
    rollback = read_json(BATCH015_DIR / "syntax_micro_rollback_policy.json")
    telemetry = read_json(BATCH015_DIR / "predictive_degradation_telemetry_policy.json")
    budget = read_json(BATCH015_DIR / "compute_budget_safe_stop_policy.json")
    blue_green = read_json(BATCH015_DIR / "blue_green_deployment_policy.json")
    compiler = read_json(BATCH015_DIR / "proof_to_action_compiler_policy.json")
    grammar = read_json(BATCH015_DIR / "four_lock_operation_grammar.json")
    registry_status = read_json(BATCH015_DIR / "lock_sequence_operation_registry_status.json")
    registry = read_json(Path("configs/lock_sequence_operation_registry.json"))
    claim_tiers = read_json(Path("configs/controllergate_claim_tiers.json"))
    catalog = read_json(Path("configs/controllergate_capability_catalog.json"))
    marketing = read_json(BATCH015_DIR / "marketing_claim_boundary.json")
    roadmap = read_json(BATCH015_DIR / "structure_first_compiler_roadmap_status.json")
    agentic = read_json(BATCH015_DIR / "future_agentic_admissibility_compiler_status.json")

    runtime_modules = [
        "controllergate/runtime/__init__.py",
        "controllergate/runtime/incident_capture.py",
        "controllergate/runtime/execution_boundary_gateway.py",
        "controllergate/runtime/isolated_repair_sandbox.py",
        "controllergate/runtime/dependency_drift_chaperone.py",
        "controllergate/runtime/active_ast_excision_probe.py",
        "controllergate/runtime/syntax_micro_rollback.py",
        "controllergate/runtime/predictive_degradation_telemetry.py",
        "controllergate/runtime/compute_budget.py",
        "controllergate/runtime/blue_green_deployment.py",
        "controllergate/runtime/proof_to_action_compiler.py",
        "controllergate/runtime/runtime_claim_boundary.py",
    ]
    for rel in runtime_modules:
        if not Path(rel).is_file():
            errors.append(f"runtime_wrapper_scaffold_missing:{rel}")

    if latest.get("status") != "PASS" or latest.get("sha256") != "35ce9b24e8400b47e63d77672196b9016e65c849919110b36d0bece08b9c1aef":
        errors.append("batch015 latest artifact boundary missing or mismatched")
    if latest.get("ingested_output_evidence_only") is not True or latest.get("source_docs_tests_caches_or_archives_ingested") is not False:
        errors.append("batch015 artifact ingest scope invalid")
    if validation.get("confirmed_external_native_repair_episode_count") != 4 or validation.get("confirmed_issue_derived_repair_episode_count") != 0:
        errors.append("batch015 validation path counts changed")
    if preservation.get("native_repair_episode_count_before_batch015") != preservation.get("native_repair_episode_count_after_batch015"):
        errors.append("batch015 native repair count not preserved")
    if native_boundary.get("native_and_issue_derived_classes_separate") is not True:
        errors.append("batch015 evidence class boundary missing")
    if claim.get("full_scoring") != "NOT_RUN/disallowed" or claim.get("memory_lift") != "not_demonstrated":
        errors.append("batch015 full scoring or memory boundary changed")
    if claim.get("self_maintaining_software") != "false/not_demonstrated" or claim.get("hallucination_elimination") != "false/not_claimed":
        errors.append("batch015 overclaim boundary changed")
    if claim.get("production_runtime_wrapper") != "false/not_demonstrated" or claim.get("live_deployment_attempted") is not False:
        errors.append("batch015 live deployment or production runtime overclaim")
    if runtime_status.get("runtime_wrapper_mvp_status") != "scaffold_only":
        errors.append("runtime_wrapper_scaffold_missing")
    if boundary.get("status") != "PASS" or boundary.get("direct_runtime_mutation_allowed") is not False:
        errors.append("execution_boundary_gateway_missing")
    if sandbox.get("fresh_ephemeral_workspace_required") is not True or sandbox.get("outside_repo_required") is not True:
        errors.append("isolated_repair_sandbox_missing")
    if drift.get("undeclared_dependency_install_allowed") is not False:
        errors.append("dependency_chaperone_missing")
    if excision.get("sandbox_only") is not True or excision.get("repair_authorized_from_probe_alone") is not False:
        errors.append("active_ast_excision_probe_missing")
    if rollback.get("status") != "ROLLBACK" or rollback.get("accepted_repair_evidence") is not False:
        errors.append("syntax_micro_rollback_missing")
    if telemetry.get("autonomous_repair_scheduled") is not False or telemetry.get("fixture_weights", {}).get("autonomous_repair_triggered") is not False:
        errors.append("predictive_degradation_telemetry_missing")
    if budget.get("blocker") != "safe_stop_budget_exceeded":
        errors.append("compute_budget_safe_stop_missing")
    if blue_green.get("simulation_only") is not True or blue_green.get("live_deployment_attempted") is not False:
        errors.append("blue_green_deployment_missing")
    if compiler.get("status") != "PASS" or compiler.get("executes_unsafe_actions") is not False:
        errors.append("proof_to_action_compiler_missing")

    required_locks = {"provenance", "null", "perturbation", "projection"}
    if set(grammar.get("locks", [])) != required_locks:
        errors.append("four_lock_operation_grammar_missing")
    operations = registry.get("operations", {})
    expected_operations = {
        "evidence_admission",
        "causal_stress_test",
        "dual_projection_consistency",
        "repair_candidate_admission",
        "memory_separation_claim",
        "runtime_action_compilation",
        "rollback_required",
        "degradation_monitoring",
        "dependency_drift_classification",
        "safe_stop",
    }
    if registry_status.get("status") != "PASS" or set(operations) != expected_operations:
        errors.append("lock_sequence_registry_missing")
    if registry.get("lock_pair_classes", {}).get("structural_pair") != ["null", "perturbation"]:
        errors.append("lock-pair structural class missing")
    for name, record in operations.items():
        if not record.get("sequence") or not record.get("required_artifacts") or not record.get("blockers") or not record.get("claim_boundary"):
            errors.append(f"{name}: incomplete lock-sequence operation record")
    if "null" not in operations.get("memory_separation_claim", {}).get("sequence", []) or "perturbation" not in operations.get("memory_separation_claim", {}).get("sequence", []):
        errors.append("memory separation operation missing null or perturbation lock")
    if "projection" not in operations.get("runtime_action_compilation", {}).get("sequence", []):
        errors.append("runtime action compilation missing projection lock")

    if claim_tiers.get("untiered_capability_allowed") is not False:
        errors.append("claim_tier_system_missing")
    capabilities = catalog.get("capabilities", [])
    capability_ids = {item.get("capability_id") for item in capabilities if isinstance(item, dict)}
    required_capabilities = {
        "evidence_bound_repair_validation",
        "artifact_byte_custody",
        "registry_first_provenance",
        "matched_null_evaluation",
        "curvature_based_source_selection",
        "active_failure_memory_routing",
        "source_commit_environment_lock",
        "target_command_manifest",
        "fresh_workspace_purity",
        "baseline_registry_drift_precheck",
        "rollback_block_ledger",
        "runtime_incident_capture",
        "execution_boundary_gateway",
        "isolated_repair_sandbox",
        "dependency_drift_chaperone",
        "active_ast_excision_probe",
        "syntax_micro_rollback",
        "predictive_degradation_telemetry",
        "compute_budget_safe_stop",
        "cryptographic_blue_green_deployment",
        "proof_to_action_compiler",
        "lock_sequence_operation_registry",
        "structure_first_compiler_roadmap",
        "future_agentic_admissibility_compiler_integration",
    }
    batch016_catalog_extensions = {
        "target_intent_signature_alignment",
        "issue_derived_harness_verification",
        "dependency_era_resolution",
        "artifact_thin_packaging",
        "evidence_carry_forward_manifest",
    }
    batch018_catalog_extensions = {
        "manual_dependency_lock_intake",
        "issue_timestamp_reconciliation",
    }
    batch019_catalog_extensions = {
        "active_search_space_geometry",
        "information_gain_probe_selection",
        "structural_defect_boundary_classification",
        "recovery_candidate_path_ranking",
        "amds_active_inference_integration",
        "single_system_scope_gate",
        "coupled_interlock_extension_gate",
        "replacement_seed_request_scaffold",
        "manual_dependency_lock_watch",
    }
    batch020_catalog_extensions = {
        "manual_dependency_lock_validation",
        "manual_lock_environment_materialization",
        "target_intent_alignment_retry",
        "dependency_overlap_grouping",
        "semantic_drift_guardrail",
        "activation_order_guardrail",
        "rollback_ghost_state_guardrail",
        "consistency_reassertion",
        "precision_failure_taxonomy",
        "issue_derived_repair_feasibility",
    }
    batch021_catalog_extensions = {
        "dynamic_era_materialization",
        "runtime_provider_selection",
        "containerized_era_runtime",
        "hosted_runtime_adapter",
        "self_hosted_runtime_plan",
        "runtime_version_gate",
    }
    batch022_catalog_extensions = {
        "docker_era_materialization_provider",
        "python37_runtime_provider",
        "structured_fragility_audit",
        "permutation_null_audit",
        "patch_structure_sensitivity",
        "psa82_adapter_quarantine",
    }
    batch023_catalog_extensions = {
        "bounded_docker_provider_probe",
        "github_actions_provider_bridge",
        "python37_provider_preflight",
        "provider_credentials_isolation",
        "psa82_quarantine_summary",
        "structured_fragility_diagnostic",
    }
    allowed_capabilities = required_capabilities | batch016_catalog_extensions | batch018_catalog_extensions | batch019_catalog_extensions | batch020_catalog_extensions | batch021_catalog_extensions | batch022_catalog_extensions | batch023_catalog_extensions
    if not required_capabilities.issubset(capability_ids) or not capability_ids.issubset(allowed_capabilities):
        errors.append("capability_catalog_missing")
    if any("current_tier" not in item for item in capabilities if isinstance(item, dict)):
        errors.append("capability without claim tier")
    if marketing.get("forbidden_claims_not_made") is not True:
        errors.append("marketing_overclaim_detected")
    if roadmap.get("roadmap_only") is not True or roadmap.get("implemented_capability") is not False:
        errors.append("structural_compiler_overclaim_detected")
    if agentic.get("roadmap_only") is not True or agentic.get("integration_implemented") is not False:
        errors.append("agentic_compiler_overclaim_detected")

    readme = Path("README.md").read_text(encoding="utf-8")
    for required in ["What ControllerGate is", "What ControllerGate is not", "Claim Tier System", "Capability Catalog", "Skeptic's Acceptance Checklist", "Runtime-wrapper roadmap", "Safe public claims", "Forbidden claims"]:
        if required not in readme:
            errors.append(f"readme_claim_tier_missing:{required}")
    for path in [
        "docs/controllergate_claim_tiers.md",
        "docs/controllergate_positioning.md",
        "docs/claim_boundary.md",
        "docs/skeptics_acceptance_checklist.md",
        "docs/use_case_positioning.md",
        "docs/structure_first_compiler_roadmap.md",
        "docs/future_agentic_admissibility_compiler_integration.md",
    ]:
        if not Path(path).is_file():
            errors.append(f"batch015 doc missing:{path}")
    use_case = Path("docs/use_case_positioning.md").read_text(encoding="utf-8")
    if "deployment_readiness: false" not in use_case:
        errors.append("sector_deployment_overclaim_detected")
    if state.get("status") != "PASS_WITH_BATCH015_RUNTIME_SCAFFOLD":
        errors.append("batch015 state did not pass scaffold boundary")
    return errors


def audit_batch016_records() -> list[str]:
    errors: list[str] = []
    for name in BATCH016_REQUIRED:
        if not (BATCH016_DIR / name).is_file():
            errors.append(f"batch016 missing required file {name}")
    if errors:
        return errors
    manifest = verify_manifest(BATCH016_DIR)
    if manifest.get("status") != "PASS":
        errors.append(f"batch016 manifest failed: {manifest}")

    phase_a = read_json(POST_DIR / "batch015_runtime_wrapper_artifact_verification.json")
    ingest = read_json(POST_DIR / "batch015_runtime_wrapper_ingest_summary.json")
    state = read_json(BATCH016_DIR / "consolidated_state_clean_replication_batch_016.json")
    preservation = read_json(BATCH016_DIR / "batch015_boundary_preservation.json")
    claim = read_json(BATCH016_DIR / "claim_boundary_batch016.json")
    signature = read_json(BATCH016_DIR / "darker_issue112_target_intent_signature.json")
    alignment = read_json(BATCH016_DIR / "target_intent_alignment_audit.json")
    incident = read_json(BATCH016_DIR / "runtime_incident_issue112_mismatch.json")
    proof = read_json(BATCH016_DIR / "proof_to_action_issue112_mismatch.json")
    dep_policy = read_json(BATCH016_DIR / "dependency_era_chaperone_policy.json")
    dep_audit = read_json(BATCH016_DIR / "darker_issue112_dependency_era_audit.json")
    dep_class = read_json(BATCH016_DIR / "dependency_precondition_classification.json")
    restore = read_json(BATCH016_DIR / "environment_restore_plan_issue112.json")
    variant_results = read_json(BATCH016_DIR / "issue112_variant_results.json")
    window_policy = read_json(BATCH016_DIR / "source_commit_window_policy.json")
    window_candidates = read_json(BATCH016_DIR / "source_commit_window_candidates.json")
    harness_context = read_json(BATCH016_DIR / "issue_derived_harness_v2_context_manifest.json")
    harness_result = read_json(BATCH016_DIR / "issue_derived_harness_v2_verification_result.json")
    eligibility = read_json(BATCH016_DIR / "prospective_memory_eligibility_gate.json")
    repair = read_json(BATCH016_DIR / "repair_only_fallback_status.json")
    feasibility = read_json(BATCH016_DIR / "issue_derived_repair_feasibility_status.json")
    matched = read_json(BATCH016_DIR / "issue_derived_matched_null_diagnostic_status.json")
    ledger = read_json(BATCH016_DIR / "proof_obligations_ledger.json")
    rollback = read_json(BATCH016_DIR / "rollback_block_ledger_audit.json")
    safe_stop = read_json(BATCH016_DIR / "compute_budget_safe_stop_batch016.json")
    catalog = read_json(Path("configs/controllergate_capability_catalog.json"))

    if phase_a.get("status") != "PASS" or phase_a.get("sha256") != "08a656487044d4d6d0003a303da25c159881ab53a8ab59a0ac61ec2a02af600c":
        errors.append("Batch015 artifact not officially ingested")
    if ingest.get("status") != "PASS" or ingest.get("ingested_output_evidence_only") is not True:
        errors.append("Batch015 ingest summary invalid")
    if preservation.get("status") != "PASS" or preservation.get("batch015_status") != "PASS_WITH_BATCH015_RUNTIME_SCAFFOLD":
        errors.append("Batch015 boundary preservation failed")
    if claim.get("confirmed_native_repair_episode_count") != 4 or claim.get("confirmed_issue_derived_repair_episode_count") != 0:
        errors.append("Batch016 repair counts changed")
    if claim.get("full_scoring") != "NOT_RUN/disallowed" or claim.get("memory_lift") != "not_demonstrated":
        errors.append("Batch016 full scoring or memory boundary changed")
    if claim.get("self_maintaining_software") != "false/not_demonstrated" or claim.get("hallucination_elimination") != "false/not_claimed":
        errors.append("Batch016 overclaim boundary changed")
    if signature.get("any_failure_sufficient") is not False or not signature.get("positive_indicators"):
        errors.append("target_intent_signature_missing")
    if alignment.get("status") != "BLOCK" or alignment.get("target_intent_alignment") is not False:
        errors.append("target intent alignment should be blocked")
    if alignment.get("blocker") not in {"target_intent_precondition_failure", "issue_derived_harness_intent_mismatch"}:
        errors.append("unexpected target intent blocker")
    if "TypeError: unsupported operand type(s) for /: 'tuple' and 'str'" not in alignment.get("negative_precondition_hits", []):
        errors.append("observed Batch014 mismatch not recorded")
    if len(str(incident.get("incident_bundle_hash", ""))) != 64 or incident.get("observed_exception_class") != "TypeError":
        errors.append("runtime incident capture record missing for mismatch")
    if proof.get("action_type") not in {"environment_restore_required", "sandbox_probe_required", "manual_seed_refinement_required", "safe_stop_required"}:
        errors.append("proof-to-action compiler emitted invalid action after mismatch")
    for forbidden in ["patch_ready_for_review_emitted", "shadow_deploy_ready_emitted", "repair_candidate_admitted_emitted"]:
        if proof.get(forbidden) is not False:
            errors.append("patch_admitted_after_intent_mismatch")
    if dep_policy.get("status") != "PASS" or "latest_unrestricted_pip_resolution" not in dep_policy.get("forbidden_resolution_methods", []):
        errors.append("dependency-era chaperone policy missing")
    if dep_audit.get("latest_unrestricted_dependency_resolution_used") is not False or dep_audit.get("fixed_later_gold_pr_metadata_used") is not False:
        errors.append("dependency resolution used forbidden metadata")
    if dep_class.get("classification") != "dependency_era_mismatch_candidate" or dep_class.get("source_patch_authorized") is not False:
        errors.append("dependency precondition classification invalid")
    if restore.get("blocker") != "dependency_era_lock_unavailable":
        errors.append("dependency-era lock unavailable blocker missing")
    if variant_results.get("status") != "BLOCK" or variant_results.get("target_intent_alignment_reached") is not False:
        errors.append("target intent variant matrix invalid")
    for item in variant_results.get("variants", []):
        if not item.get("command_hash") or not item.get("environment_hash") or not item.get("dependency_metadata_hash"):
            errors.append("variant record missing hash fields")
    if window_policy.get("max_commits") != 10 or window_policy.get("post_issue_commits_allowed") is not False:
        errors.append("source commit window policy unbounded or post-issue allowed")
    if window_candidates.get("post_issue_commit_count") != 0:
        errors.append("source commit window used post-issue commit")
    if harness_context.get("solution_sections_used") is not False or harness_context.get("future_fixed_gold_pr_evidence_used") is not False:
        errors.append("harness v2 used forbidden evidence")
    if harness_result.get("harness_v2_generated") is not False or harness_result.get("target_intent_alignment") is not False:
        errors.append("issue-derived harness v2 verification should not pass")
    if eligibility.get("native_memory_eligibility") is not False:
        errors.append("memory_claim_from_issue_derived_evidence")
    if repair.get("repair_only_fallback_attempted") is not False or feasibility.get("issue_derived_repair_feasibility") is not False:
        errors.append("repair attempted without target-intent alignment")
    if matched.get("matched_null_diagnostic_run_count") != 0:
        errors.append("matched-null diagnostic ran without target-intent alignment")
    if not any(isinstance(item, dict) and item.get("entry_type") == "ROLLBACK_BLOCK" for item in ledger):
        errors.append("safe_stop_missing_after_block")
    if rollback.get("status") != "PASS" or rollback.get("rollback_block_count", 0) < 1:
        errors.append("rollback block ledger missing after block")
    if safe_stop.get("status") != "SAFE_STOP" or safe_stop.get("safe_stop_success") is not True:
        errors.append("safe-stop missing after target-intent failure")
    if state.get("status") != "PASS_WITH_BATCH016_SAFE_STOP":
        errors.append("Batch016 state did not safe-stop")
    if catalog.get("catalog_version") not in {"batch016", "batch017", "batch018", "batch019", "batch020", "batch021", "batch022", "batch023"}:
        errors.append("Batch016 capability catalog version missing")
    return errors


def audit_batch017_records() -> list[str]:
    errors: list[str] = []
    for name in BATCH017_REQUIRED:
        if not (BATCH017_DIR / name).is_file():
            errors.append(f"batch017 missing required file {name}")
    if errors:
        return errors
    manifest = verify_manifest(BATCH017_DIR)
    if manifest.get("status") != "PASS":
        errors.append(f"batch017 manifest failed: {manifest}")

    phase_a = read_json(POST_DIR / "batch016_target_intent_artifact_verification.json")
    ingest = read_json(POST_DIR / "batch016_target_intent_ingest_summary.json")
    state = read_json(BATCH017_DIR / "consolidated_state_clean_replication_batch_017.json")
    preservation = read_json(BATCH017_DIR / "batch016_boundary_preservation.json")
    scaffold = read_json(BATCH017_DIR / "batch015_runtime_scaffold_preservation.json")
    claim = read_json(BATCH017_DIR / "claim_boundary_batch017.json")
    packaging = read_json(BATCH017_DIR / "thin_artifact_packaging_policy.json")
    lineage = read_json(BATCH017_DIR / "artifact_lineage_index.json")
    carry = read_json(BATCH017_DIR / "evidence_carry_forward_manifest.json")
    budget = read_json(BATCH017_DIR / "artifact_payload_budget.json")
    minimality = read_json(BATCH017_DIR / "artifact_minimality_audit.json")
    equivalence = read_json(BATCH017_DIR / "lineage_equivalence_audit.json")
    dep_policy = read_json(BATCH017_DIR / "dependency_era_resolution_policy.json")
    evidence_policy = read_json(BATCH017_DIR / "decision_time_dependency_evidence_policy.json")
    forbidden = read_json(BATCH017_DIR / "dependency_resolution_forbidden_sources.json")
    dep_audit = read_json(BATCH017_DIR / "dependency_era_resolution_audit.json")
    release_audit = read_json(BATCH017_DIR / "dependency_release_time_audit.json")
    lock_status = read_json(BATCH017_DIR / "decision_time_dependency_lock_status.json")
    manual_presence = read_json(BATCH017_DIR / "manual_dependency_lock_presence_check.json")
    manual_tracking = read_json(BATCH017_DIR / "manual_dependency_lock_git_tracking_audit.json")
    manual_schema = read_json(BATCH017_DIR / "manual_dependency_lock_schema_validation.json")
    manual_dt = read_json(BATCH017_DIR / "manual_dependency_lock_decision_time_audit.json")
    variants = read_json(BATCH017_DIR / "issue112_dependency_resolved_variant_results.json")
    window_policy = read_json(BATCH017_DIR / "source_commit_window_policy.json")
    window_candidates = read_json(BATCH017_DIR / "source_commit_window_candidates.json")
    target_retry = read_json(BATCH017_DIR / "target_intent_alignment_retry_audit.json")
    harness_context = read_json(BATCH017_DIR / "issue_derived_harness_v3_context_manifest.json")
    harness_result = read_json(BATCH017_DIR / "issue_derived_harness_v3_verification_result.json")
    repair = read_json(BATCH017_DIR / "repair_only_fallback_status.json")
    feasibility = read_json(BATCH017_DIR / "issue_derived_repair_feasibility_status.json")
    matched = read_json(BATCH017_DIR / "issue_derived_matched_null_diagnostic_status.json")
    ledger = read_json(BATCH017_DIR / "proof_obligations_ledger.json")
    rollback = read_json(BATCH017_DIR / "rollback_block_ledger_audit.json")
    safe_stop = read_json(BATCH017_DIR / "compute_budget_safe_stop_batch017.json")
    catalog = read_json(Path("configs/controllergate_capability_catalog.json"))

    if phase_a.get("status") != "PASS" or phase_a.get("sha256") != "c9526a9ab21e5341c4f1a74428429ffb28b9ec964e2cfb7c0e697442b4ff131e":
        errors.append("Batch016 artifact not officially ingested")
    if ingest.get("status") != "PASS" or ingest.get("ingested_output_evidence_only") is not True:
        errors.append("Batch016 ingest summary invalid")
    if preservation.get("status") != "PASS" or preservation.get("batch016_exact_blocker") != "dependency_api_precondition_unresolved":
        errors.append("Batch016 boundary preservation failed")
    if scaffold.get("status") != "PASS" or not scaffold.get("preserved_scaffolds"):
        errors.append("Batch015 runtime scaffold preservation failed")
    if claim.get("confirmed_native_repair_episode_count") != 4 or claim.get("confirmed_issue_derived_repair_episode_count") != 0:
        errors.append("Batch017 repair counts changed")
    if claim.get("full_scoring") != "NOT_RUN/disallowed" or claim.get("memory_lift") != "not_demonstrated":
        errors.append("Batch017 full scoring or memory boundary changed")
    if claim.get("self_maintaining_software") != "false/not_demonstrated" or claim.get("hallucination_elimination") != "false/not_claimed":
        errors.append("Batch017 overclaim boundary changed")
    if claim.get("absolute_uncrashability") != "false/not_claimed" or claim.get("production_runtime_readiness") != "false/not_demonstrated":
        errors.append("Batch017 reliability or readiness overclaim")
    if packaging.get("status") != "PASS" or packaging.get("primary_artifact_name") != "post_v2_37_hardening_batch017_dependency_era_thin_artifacts":
        errors.append("thin_artifact_policy_missing")
    if lineage.get("status") != "PASS" or not lineage.get("prior_artifacts"):
        errors.append("artifact_lineage_index_missing")
    if carry.get("status") != "PASS" or carry.get("prior_batch_directories_recursively_packaged") is not False:
        errors.append("evidence_carry_forward_manifest_missing")
    if minimality.get("recursive_prior_batch_packaging_detected") is not False:
        errors.append("recursive_prior_batch_packaging_detected")
    if equivalence.get("thin_artifact_lineage_equivalence_failed") is not False:
        errors.append("thin_artifact_lineage_equivalence_failed")
    if budget.get("status") != "PASS" or int(budget.get("hard_primary_artifact_bytes", 0)) != 750000:
        errors.append("primary_artifact_budget_exceeded")
    if "latest_unrestricted_pip_resolution" not in dep_policy.get("forbidden_dependency_evidence", []):
        errors.append("dependency_era_resolution_policy_missing")
    if evidence_policy.get("unrecorded_local_state_allowed") is not False:
        errors.append("decision-time dependency policy allows unrecorded state")
    if "future_tests_or_lock_files" not in forbidden.get("forbidden_sources", []):
        errors.append("dependency forbidden sources incomplete")
    if dep_audit.get("latest_unrestricted_dependency_resolution_used") is not False or dep_audit.get("fixed_later_gold_pr_metadata_used") is not False:
        errors.append("dependency resolution used forbidden metadata")
    if release_audit.get("release_metadata_recorded") is not False or release_audit.get("blocker") != "dependency_release_metadata_unavailable":
        errors.append("dependency release metadata audit invalid")
    if lock_status.get("decision_time_dependency_lock_valid") is not False or lock_status.get("blocker") != "dependency_era_lock_unavailable":
        errors.append("decision-time dependency lock status invalid")
    if manual_presence.get("exists") is True:
        if manual_tracking.get("git_tracked") is not True or manual_schema.get("schema_valid") is not True or manual_dt.get("uses_future_evidence") is not False:
            errors.append("manual dependency lock invalid")
    if variants.get("target_intent_alignment_reached") is not False:
        errors.append("target intent unexpectedly reached without lock")
    for item in variants.get("variants", []):
        for field in ["command_hash", "environment_hash", "dependency_lock_hash", "raw_log_hash"]:
            if len(str(item.get(field, ""))) != 64:
                errors.append(f"variant missing hash field {field}")
    if window_policy.get("max_commits") != 10 or window_policy.get("post_issue_commits_allowed") is not False:
        errors.append("source commit window unbounded or post-issue allowed")
    if window_candidates.get("post_issue_commit_count") != 0:
        errors.append("source commit window used post-issue commit")
    if target_retry.get("target_intent_alignment") is not False or target_retry.get("patch_authorized") is not False:
        errors.append("target intent retry allowed patch")
    if harness_context.get("solution_sections_used") is not False or harness_context.get("future_fixed_gold_pr_evidence_used") is not False:
        errors.append("harness v3 used forbidden evidence")
    if harness_result.get("harness_v3_generated") is not False or harness_result.get("issue_derived_candidate_verified") is not False:
        errors.append("harness v3 verified without target intent")
    if repair.get("repair_only_fallback_attempted") is not False or feasibility.get("issue_derived_repair_feasibility") is not False:
        errors.append("repair attempted without target intent alignment")
    if matched.get("matched_null_diagnostic_run_count") != 0:
        errors.append("matched-null diagnostic ran without target intent alignment")
    if not any(isinstance(item, dict) and item.get("entry_type") == "ROLLBACK_BLOCK" for item in ledger):
        errors.append("safe_stop_missing_after_block")
    if rollback.get("rollback_block_count", 0) < 1 or safe_stop.get("safe_stop_success") is not True:
        errors.append("safe-stop or rollback invalid")
    if state.get("status") != "PASS_WITH_BATCH017_SAFE_STOP" or state.get("exact_blocker") != "dependency_era_lock_unavailable":
        errors.append("Batch017 state did not safe-stop at dependency lock")
    if catalog.get("catalog_version") not in {"batch017", "batch018", "batch019", "batch020", "batch021", "batch022", "batch023"}:
        errors.append("Batch017 capability catalog version missing")
    return errors


def audit_batch018_records() -> list[str]:
    errors: list[str] = []
    for name in BATCH018_REQUIRED:
        if not (BATCH018_DIR / name).is_file():
            errors.append(f"batch018 missing required file {name}")
    if errors:
        return errors
    manifest = verify_manifest(BATCH018_DIR)
    if manifest.get("status") != "PASS":
        errors.append(f"batch018 manifest failed: {manifest}")

    phase_a = read_json(POST_DIR / "batch017_dependency_era_artifact_verification.json")
    ingest = read_json(POST_DIR / "batch017_dependency_era_ingest_summary.json")
    state = read_json(BATCH018_DIR / "consolidated_state_clean_replication_batch_018.json")
    preservation = read_json(BATCH018_DIR / "batch017_boundary_preservation.json")
    lineage_preservation = read_json(BATCH018_DIR / "thin_artifact_lineage_preservation.json")
    claim = read_json(BATCH018_DIR / "claim_boundary_batch018.json")
    timestamp = read_json(BATCH018_DIR / "darker_issue112_timestamp_reconciliation.json")
    cutoff = read_json(BATCH018_DIR / "dependency_cutoff_decision.json")
    presence = read_json(BATCH018_DIR / "manual_dependency_lock_presence_check.json")
    tracking = read_json(BATCH018_DIR / "manual_dependency_lock_git_tracking_audit.json")
    schema = read_json(BATCH018_DIR / "manual_dependency_lock_schema_validation.json")
    decision_time = read_json(BATCH018_DIR / "manual_dependency_lock_decision_time_audit.json")
    support = read_json(BATCH018_DIR / "manual_requirements_support_file_audit.json")
    normalization = read_json(BATCH018_DIR / "manual_dependency_lock_normalization_result.json")
    validation = read_json(BATCH018_DIR / "decision_time_dependency_lock_validation.json")
    environment = read_json(BATCH018_DIR / "manual_lock_environment_materialization_log.json")
    target_retry = read_json(BATCH018_DIR / "target_intent_alignment_retry_audit.json")
    harness = read_json(BATCH018_DIR / "issue_derived_harness_v4_verification_result.json")
    repair = read_json(BATCH018_DIR / "repair_only_fallback_status.json")
    feasibility = read_json(BATCH018_DIR / "issue_derived_repair_feasibility_status.json")
    matched = read_json(BATCH018_DIR / "issue_derived_matched_null_diagnostic_status.json")
    ledger = read_json(BATCH018_DIR / "proof_obligations_ledger.json")
    rollback = read_json(BATCH018_DIR / "rollback_block_ledger_audit.json")
    safe_stop = read_json(BATCH018_DIR / "compute_budget_safe_stop_batch018.json")
    packaging = read_json(BATCH018_DIR / "thin_artifact_packaging_policy.json")
    lineage = read_json(BATCH018_DIR / "artifact_lineage_index.json")
    carry = read_json(BATCH018_DIR / "evidence_carry_forward_manifest.json")
    budget = read_json(BATCH018_DIR / "artifact_payload_budget.json")
    minimality = read_json(BATCH018_DIR / "artifact_minimality_audit.json")
    catalog = read_json(Path("configs/controllergate_capability_catalog.json"))

    if phase_a.get("status") != "PASS" or phase_a.get("actual_sha256") != "cf7f89bd1d93b2f85b574fa6b785b64abcea46478c724bb72aa33feac28c9555":
        errors.append("Batch017 artifact not officially ingested")
    if ingest.get("status") != "PASS" or ingest.get("ingested_only_output_evidence") is not True:
        errors.append("Batch017 ingest summary invalid")
    if preservation.get("status") != "PASS" or preservation.get("batch017_exact_blocker") != "dependency_era_lock_unavailable":
        errors.append("Batch017 boundary preservation failed")
    if lineage_preservation.get("status") != "PASS" or lineage_preservation.get("primary_artifact_remains_thin") is not True:
        errors.append("thin artifact lineage not preserved")
    if claim.get("confirmed_native_repair_episode_count") != 4 or claim.get("confirmed_issue_derived_repair_episode_count") != 0:
        errors.append("Batch018 repair counts changed")
    if claim.get("full_scoring") != "NOT_RUN/disallowed" or claim.get("memory_lift") != "not_demonstrated":
        errors.append("Batch018 full scoring or memory boundary changed")
    for field in ["self_maintaining_software", "hallucination_elimination", "absolute_uncrashability"]:
        if "claimed" in str(claim.get(field, "")).lower() and str(claim.get(field)) not in {"false/not_claimed"}:
            errors.append(f"Batch018 overclaim boundary changed: {field}")
    if timestamp.get("status") != "PASS" or timestamp.get("timestamp_conflict_detected") is not True:
        errors.append("issue timestamp reconciliation missing conflict record")
    if timestamp.get("dependency_cutoff_timestamp") != "2021-01-02T00:00:00Z":
        errors.append("dependency cutoff timestamp mismatch")
    if cutoff.get("post_issue_dependencies_allowed") is not False:
        errors.append("post-issue dependencies allowed")
    if presence.get("canonical_path") != "external_seeds_pending/dependency_locks/darker_issue112_dependency_lock.json":
        errors.append("canonical manual dependency lock path missing")
    if presence.get("canonical_json_present") is not False or presence.get("blocker") != "manual_dependency_lock_absent":
        errors.append("manual dependency lock absence not recorded")
    if support.get("txt_can_bypass_json_schema") is not False:
        errors.append("manual_requirements_txt_not_authoritative")
    if tracking.get("git_tracked") is not False or tracking.get("workflow_visible") is not False:
        errors.append("absent manual lock should not be tracked or workflow-visible")
    if schema.get("schema_valid") is not False or schema.get("blocker") != "manual_dependency_lock_absent":
        errors.append("manual dependency lock schema absence not recorded")
    if decision_time.get("latest_unrestricted_dependency_resolution_used") is not False or decision_time.get("fixed_later_gold_pr_evidence_used") is not False:
        errors.append("manual dependency lock used forbidden evidence")
    if normalization.get("authoritative_lock_available") is not False:
        errors.append("manual dependency lock normalization incorrectly authoritative")
    if validation.get("status") != "NOT_RUN":
        errors.append("dependency lock validation ran without manual lock")
    if environment.get("status") != "NOT_RUN":
        errors.append("environment materialization ran without manual lock")
    if target_retry.get("status") != "NOT_RUN" or target_retry.get("target_intent_alignment") is not False:
        errors.append("target-intent retry ran without manual lock")
    if harness.get("status") != "NOT_RUN":
        errors.append("harness v4 ran without target intent")
    if repair.get("repair_only_fallback_attempted") is not False or feasibility.get("issue_derived_repair_feasibility") is not False:
        errors.append("repair attempted without target-intent alignment")
    if matched.get("matched_null_diagnostic_run_count") != 0:
        errors.append("matched-null diagnostic ran without target-intent alignment")
    if not any(isinstance(item, dict) and item.get("entry_type") == "ROLLBACK_BLOCK" and item.get("blocker") == "manual_dependency_lock_absent" for item in ledger):
        errors.append("safe_stop_missing_after_block")
    if rollback.get("status") != "PASS" or rollback.get("rollback_block_count") != 1:
        errors.append("rollback block ledger invalid")
    if safe_stop.get("status") != "SAFE_STOP" or safe_stop.get("safe_stop_success") is not True:
        errors.append("compute budget safe-stop missing")
    if packaging.get("status") != "PASS" or packaging.get("recursive_prior_batch_packaging_allowed") is not False:
        errors.append("thin_artifact_policy_missing")
    if lineage.get("status") != "PASS" or not lineage.get("prior_artifacts"):
        errors.append("artifact_lineage_index_missing")
    if carry.get("status") != "PASS" or carry.get("carried_prior_evidence_by_reference") is not True:
        errors.append("evidence_carry_forward_manifest_missing")
    if minimality.get("recursive_prior_batch_packaging_detected") is not False:
        errors.append("recursive_prior_batch_packaging_detected")
    if budget.get("status") != "PASS" or int(budget.get("hard_primary_artifact_bytes", 0)) != 750000:
        errors.append("primary_artifact_budget_exceeded")
    if state.get("status") != "PASS_WITH_BATCH018_SAFE_STOP" or state.get("exact_blocker") != "manual_dependency_lock_absent":
        errors.append("Batch018 state did not safe-stop at manual lock")
    if catalog.get("catalog_version") not in {"batch018", "batch019", "batch020", "batch021", "batch022", "batch023"}:
        errors.append("Batch018 capability catalog version missing")
    return errors


def audit_batch019_records() -> list[str]:
    errors: list[str] = []
    for name in BATCH019_REQUIRED:
        if not (BATCH019_DIR / name).is_file():
            errors.append(f"batch019 missing required file {name}")
    if errors:
        return errors
    manifest = verify_manifest(BATCH019_DIR)
    if manifest.get("status") != "PASS":
        errors.append(f"batch019 manifest failed: {manifest}")

    phase_a = read_json(POST_DIR / "batch018_manual_dependency_lock_artifact_verification.json")
    ingest = read_json(POST_DIR / "batch018_manual_dependency_lock_ingest_summary.json")
    state = read_json(BATCH019_DIR / "consolidated_state_clean_replication_batch_019.json")
    preservation = read_json(BATCH019_DIR / "batch018_boundary_preservation.json")
    blocker = read_json(BATCH019_DIR / "manual_dependency_lock_blocker_carry_forward.json")
    claim = read_json(BATCH019_DIR / "claim_boundary_batch019.json")
    watch = read_json(BATCH019_DIR / "manual_dependency_lock_watch_status.json")
    geometry_policy = read_json(BATCH019_DIR / "active_search_space_geometry_policy.json")
    geometry_status = read_json(BATCH019_DIR / "active_search_space_geometry_status.json")
    vector_schema = read_json(BATCH019_DIR / "search_space_feature_vector_schema.json")
    vector_status = read_json(BATCH019_DIR / "search_space_feature_vector_status.json")
    probe_policy = read_json(BATCH019_DIR / "information_gain_probe_policy.json")
    probe_decision = read_json(BATCH019_DIR / "probe_selection_decision_records.json")
    boundary = read_json(BATCH019_DIR / "structural_defect_boundary_status.json")
    recovery = read_json(BATCH019_DIR / "recovery_path_ranking_status.json")
    scope = read_json(BATCH019_DIR / "single_system_vs_interlock_scope_audit.json")
    amds = read_json(BATCH019_DIR / "amds_active_inference_status.json")
    amds_queue = read_json(BATCH019_DIR / "amds_active_probe_queue.json")
    replacement = read_json(BATCH019_DIR / "replacement_seed_quality_gate.json")
    curvature = read_json(BATCH019_DIR / "curvature_claim_boundary_batch019.json")
    packaging = read_json(BATCH019_DIR / "thin_artifact_packaging_policy.json")
    lineage = read_json(BATCH019_DIR / "artifact_lineage_index.json")
    carry = read_json(BATCH019_DIR / "evidence_carry_forward_manifest.json")
    budget = read_json(BATCH019_DIR / "artifact_payload_budget.json")
    minimality = read_json(BATCH019_DIR / "artifact_minimality_audit.json")
    catalog = read_json(Path("configs/controllergate_capability_catalog.json"))

    if phase_a.get("status") != "PASS" or phase_a.get("actual_sha256") != "fa248bdf8e4a78e758a02cdf05e465154006cd3a8f57b4533d359915432a9695":
        errors.append("Batch018 artifact not officially ingested")
    if ingest.get("status") != "PASS" or ingest.get("ingested_only_output_evidence") is not True:
        errors.append("Batch018 ingest summary invalid")
    if preservation.get("status") != "PASS" or preservation.get("batch018_exact_blocker") != "manual_dependency_lock_absent":
        errors.append("Batch018 boundary preservation failed")
    if preservation.get("batch019_repair_path_executed") is not False:
        errors.append("darker_repair_ran_without_manual_dependency_lock")
    if blocker.get("carried_blocker") != "manual_dependency_lock_absent" or blocker.get("repair_path_executed") is not False:
        errors.append("manual dependency lock blocker not carried forward")
    if watch.get("batch019_processes_lock") is not False:
        errors.append("Darker manual lock processed inside Batch019")
    if claim.get("native_repair_episode_count") != 4 or claim.get("issue_derived_repair_episode_count") != 0:
        errors.append("Batch019 repair counts changed")
    if claim.get("full_scoring") != "NOT_RUN/disallowed" or claim.get("memory_lift") != "not_demonstrated":
        errors.append("Batch019 full scoring or memory boundary changed")
    if claim.get("self_maintaining_software") != "false/not_demonstrated" or claim.get("hallucination_elimination") != "false/not_claimed":
        errors.append("Batch019 overclaim boundary changed")
    if geometry_policy.get("may_validate_repair") is not False or geometry_policy.get("may_replace_target_validation") is not False:
        errors.append("geometry_replaced_empirical_evidence_gate")
    if geometry_status.get("repair_validated") is not False or geometry_status.get("empirical_gates_replaced") is not False:
        errors.append("geometry_replaced_empirical_evidence_gate")
    if vector_schema.get("missing_evidence_must_be_explicit") is not True or not vector_status.get("missing_evidence"):
        errors.append("search_space_feature_vector_schema_missing")
    if probe_policy.get("selection_formula", {}).get("deterministic") is not True:
        errors.append("probe_selection_formula_missing")
    if probe_decision.get("status") != "PASS" or probe_decision.get("decision", {}).get("forbidden_evidence_used") is not False:
        errors.append("probe_selection_policy_missing")
    if boundary.get("boundary_class") != "dependency_precondition_boundary":
        errors.append("structural_defect_boundary_missing")
    if recovery.get("top_recovery_path") != "provide_manual_dependency_lock":
        errors.append("recovery_path_ranking_missing")
    if scope.get("status") != "PASS" or scope.get("conflated") is not False:
        errors.append("single_system_scope_gate_missing")
    coupled = scope.get("coupled_interlock", {})
    if coupled.get("coupled_interlock_extension_active") is not False or coupled.get("blocker") != "coupled_interlock_used_without_invariants":
        errors.append("coupled_interlock_used_without_invariants")
    if amds.get("status") != "PASS" or amds.get("repair_success_claim") is not False:
        errors.append("amds_active_inference_missing")
    if amds_queue.get("candidate_status") != "blocked_on_manual_dependency_lock":
        errors.append("Darker issue #112 not blocked on manual dependency lock")
    if replacement.get("contains_evidence_checklist") is not True or replacement.get("contains_forbidden_evidence_checklist") is not True:
        errors.append("replacement seed request scaffold invalid")
    if curvature.get("geometry_claim_can_override_evidence") is not False:
        errors.append("geometry_replaced_empirical_evidence_gate")
    if packaging.get("status") != "PASS" or packaging.get("recursive_prior_batch_packaging_allowed") is not False:
        errors.append("thin_artifact_policy_missing")
    if lineage.get("status") != "PASS" or not lineage.get("prior_artifacts"):
        errors.append("artifact_lineage_index_missing")
    if carry.get("status") != "PASS" or carry.get("carried_prior_evidence_by_reference") is not True:
        errors.append("evidence_carry_forward_manifest_missing")
    if minimality.get("recursive_prior_batch_packaging_detected") is not False:
        errors.append("recursive_prior_batch_packaging_detected")
    if budget.get("status") != "PASS" or int(budget.get("hard_primary_artifact_bytes", 0)) != 750000:
        errors.append("primary_artifact_budget_exceeded")
    if state.get("status") != "PASS_WITH_BATCH019_ACTIVE_SEARCH_GEOMETRY":
        errors.append("Batch019 state did not reach active search geometry boundary")
    if catalog.get("catalog_version") not in {"batch019", "batch020", "batch021", "batch022", "batch023"}:
        errors.append("Batch019 capability catalog version missing")
    return errors


def audit_batch020_records() -> list[str]:
    errors: list[str] = []
    for name in BATCH020_REQUIRED:
        if not (BATCH020_DIR / name).is_file():
            errors.append(f"batch020 missing required file {name}")
    if errors:
        return errors
    manifest = verify_manifest(BATCH020_DIR)
    if manifest.get("status") != "PASS":
        errors.append(f"batch020 manifest failed: {manifest}")

    phase_a = read_json(POST_DIR / "batch019_active_search_geometry_artifact_verification.json")
    ingest = read_json(POST_DIR / "batch019_active_search_geometry_ingest_summary.json")
    state = read_json(BATCH020_DIR / "consolidated_state_clean_replication_batch_020.json")
    preservation = read_json(BATCH020_DIR / "batch019_boundary_preservation.json")
    geometry = read_json(BATCH020_DIR / "active_search_geometry_preservation.json")
    watch = read_json(BATCH020_DIR / "manual_dependency_lock_watch_preservation.json")
    claim = read_json(BATCH020_DIR / "claim_boundary_batch020.json")
    presence = read_json(BATCH020_DIR / "manual_dependency_lock_presence_check.json")
    git_tracking = read_json(BATCH020_DIR / "manual_dependency_lock_git_tracking_audit.json")
    schema = read_json(BATCH020_DIR / "manual_dependency_lock_schema_validation.json")
    decision_time = read_json(BATCH020_DIR / "manual_dependency_lock_decision_time_audit.json")
    sha_audit = read_json(BATCH020_DIR / "manual_dependency_lock_sha256_audit.json")
    requirements = read_json(BATCH020_DIR / "manual_requirements_support_file_audit.json")
    validation = read_json(BATCH020_DIR / "manual_dependency_lock_validation_status.json")
    language = read_json(BATCH020_DIR / "public_language_audit_batch020.json")
    activation = read_json(BATCH020_DIR / "activation_order_audit_batch020.json")
    rollback = read_json(BATCH020_DIR / "rollback_block_ledger_audit.json")
    ledger = read_json(BATCH020_DIR / "proof_obligations_ledger.json")
    overlap = read_json(BATCH020_DIR / "dependency_overlap_audit.json")
    consistency = read_json(BATCH020_DIR / "consistency_reassertion_audit.json")
    taxonomy = read_json(BATCH020_DIR / "failure_taxonomy_batch020.json")
    precision = read_json(BATCH020_DIR / "precision_failure_log_batch020.json")
    materialization = read_json(BATCH020_DIR / "manual_lock_environment_materialization_log.json")
    environment_hash = read_json(BATCH020_DIR / "manual_lock_environment_hash.json")
    purity = read_json(BATCH020_DIR / "workspace_purity_report.json")
    lock_stack = read_json(BATCH020_DIR / "acquisition_lock_stack_status.json")
    variant_results = read_json(BATCH020_DIR / "issue112_manual_lock_variant_results.json")
    target_retry = read_json(BATCH020_DIR / "target_intent_alignment_retry_audit.json")
    harness = read_json(BATCH020_DIR / "issue_derived_harness_v5_verification_result.json")
    curvature = read_json(BATCH020_DIR / "curvature_claim_boundary.json")
    active_trace = read_json(BATCH020_DIR / "active_search_geometry_execution_trace.json")
    repair = read_json(BATCH020_DIR / "repair_only_fallback_status.json")
    feasibility = read_json(BATCH020_DIR / "issue_derived_repair_feasibility_status.json")
    diagnostic = read_json(BATCH020_DIR / "issue_derived_matched_null_diagnostic_status.json")
    viability = read_json(BATCH020_DIR / "darker_issue112_candidate_viability_decision.json")
    packaging = read_json(BATCH020_DIR / "thin_artifact_packaging_policy.json")
    lineage = read_json(BATCH020_DIR / "artifact_lineage_index.json")
    minimality = read_json(BATCH020_DIR / "artifact_minimality_audit.json")
    budget = read_json(BATCH020_DIR / "artifact_payload_budget.json")
    catalog = read_json(Path("configs/controllergate_capability_catalog.json"))

    if phase_a.get("status") != "PASS" or phase_a.get("actual_sha256") != "418b75bfd3f231f953dd5e85a9e5a37c9a1a5d5ae805e7181ac4221ad2477af3":
        errors.append("Batch019 artifact not officially ingested")
    if ingest.get("status") != "PASS" or ingest.get("source_files_ingested") is not False:
        errors.append("Batch019 ingest summary invalid")
    if preservation.get("status") != "PASS" or preservation.get("batch019_exact_blocker") != "manual_dependency_lock_available_for_batch020_or_later":
        errors.append("Batch019 boundary preservation failed")
    if geometry.get("may_replace_empirical_evidence") is not False:
        errors.append("geometry_replaced_empirical_evidence_gate")
    if watch.get("batch020_processes_lock") is not True:
        errors.append("manual dependency lock watch not advanced to Batch020 processing")
    if claim.get("native_repair_episode_count") != 4 or claim.get("issue_derived_repair_episode_count") != 0:
        errors.append("Batch020 repair counts changed")
    if claim.get("full_scoring") != "NOT_RUN/disallowed" or claim.get("memory_lift") != "not_demonstrated":
        errors.append("Batch020 full scoring or memory boundary changed")
    if claim.get("self_maintaining_software") != "false/not_demonstrated" or claim.get("hallucination_elimination") != "false/not_claimed":
        errors.append("Batch020 overclaim boundary changed")
    if presence.get("canonical_json_present") is not True:
        errors.append("manual_dependency_lock_absent")
    if git_tracking.get("git_tracked") is not True or git_tracking.get("workflow_visible") is not True:
        errors.append("manual_dependency_lock_not_visible_in_workflow")
    if schema.get("status") != "PASS" or schema.get("placeholder_paths"):
        errors.append("manual_dependency_lock_schema_invalid")
    if decision_time.get("status") != "PASS" or decision_time.get("latest_unrestricted_dependency_resolution_used") is not False:
        errors.append("manual_dependency_lock_uses_future_evidence")
    if sha_audit.get("current_sha256") != "108d961f89b603d3c6a7bcb374976992c3fadc80497bf967421cdea38aff248a":
        errors.append("manual_dependency_lock_sha_mismatch_unexplained")
    if requirements.get("txt_requirements_authoritative") is not False or requirements.get("canonical_json_authoritative") is not True:
        errors.append("manual_requirements_txt_not_authoritative")
    if validation.get("status") != "PASS" or validation.get("materialization_allowed") is not True:
        errors.append("manual dependency lock validation failed")
    if language.get("status") != "PASS":
        errors.append("semantic_drift_public_language_violation")
    if activation.get("repair_activated_without_target_intent") is not False or activation.get("repair_activated_without_bounded_materialization") is not False:
        errors.append("activation_order_violation")
    if materialization.get("lock_validation_status") != "PASS":
        errors.append("environment materialization did not use validated lock")
    if materialization.get("status") == "BLOCK":
        if materialization.get("blocker") != "manual_lock_environment_materialization_failed":
            errors.append("manual_lock_environment_materialization_failed")
        if rollback.get("rollback_block_count", 0) < 1 or not ledger.get("entries"):
            errors.append("rollback_block_missing")
        if target_retry.get("status") != "NOT_RUN" or harness.get("status") != "NOT_RUN":
            errors.append("downstream gate ran after materialization block")
    if materialization.get("source_mutation_performed") is not False or materialization.get("undeclared_dependency_install_attempted") is not False:
        errors.append("manual lock materialization mutated forbidden state")
    if environment_hash.get("environment_materialized") is not False and materialization.get("status") == "BLOCK":
        errors.append("environment hash claims materialized after block")
    if purity.get("source_mutation_detected") is not False:
        errors.append("workspace_purity_failed")
    if lock_stack.get("repair_allowed") is not False:
        errors.append("repair_activated_without_target_intent")
    if variant_results.get("status") != "NOT_RUN" or target_retry.get("repair_authorized") is not False:
        errors.append("repair_activated_without_bounded_materialization")
    if overlap.get("status") != "PASS":
        errors.append("dependency_overlap_grouping_missing")
    if consistency.get("status") != "PASS" or consistency.get("stale_vectors_detected") is not False:
        errors.append("consistency_reassertion_missing")
    if taxonomy.get("taxonomy_class") == "unknown_boundary" or precision.get("generic_failure_used") is not False:
        errors.append("generic_failure_taxonomy_degradation")
    if curvature.get("curvature_can_replace_evidence") is not False or active_trace.get("empirical_evidence_replaced") is not False:
        errors.append("geometry_replaced_empirical_evidence_gate")
    if repair.get("repair_only_fallback_attempted") is not False or feasibility.get("issue_derived_repair_feasibility") is not False:
        errors.append("repair_attempted_without_target_intent_alignment")
    if diagnostic.get("matched_null_diagnostic_run_count") != 0:
        errors.append("memory_claim_from_issue_derived_evidence")
    if viability.get("decision") != "continue_with_manual_dependency_lock_revision_required":
        errors.append("Batch020 viability decision mismatch")
    if packaging.get("recursive_prior_batch_packaging_allowed") is not False:
        errors.append("thin artifact policy missing")
    if lineage.get("status") != "PASS" or not lineage.get("prior_artifacts"):
        errors.append("artifact lineage index missing")
    if minimality.get("recursive_prior_batch_packaging_detected") is not False:
        errors.append("recursive_prior_batch_packaging_detected")
    if budget.get("status") != "PASS" or int(budget.get("hard_primary_artifact_bytes", 0)) != 750000:
        errors.append("primary_artifact_budget_exceeded")
    if state.get("status") != "PASS_WITH_BATCH020_MANUAL_LOCK_VALIDATED_ENVIRONMENT_BLOCKED":
        errors.append("Batch020 state mismatch")
    if state.get("exact_blocker") != "manual_lock_environment_materialization_failed":
        errors.append("Batch020 exact blocker mismatch")
    if catalog.get("catalog_version") not in {"batch020", "batch021", "batch022", "batch023"}:
        errors.append("Batch020 capability catalog version missing")
    return errors


def audit_batch021_records() -> list[str]:
    errors: list[str] = []
    for name in BATCH021_REQUIRED:
        if not (BATCH021_DIR / name).is_file():
            errors.append(f"batch021 missing required file {name}")
    if errors:
        return errors
    manifest = verify_manifest(BATCH021_DIR)
    if manifest.get("status") != "PASS":
        errors.append(f"batch021 manifest failed: {manifest}")
    phase_a = read_json(POST_DIR / "batch020_manual_lock_materialization_artifact_verification.json")
    ingest = read_json(POST_DIR / "batch020_manual_lock_materialization_ingest_summary.json")
    recommendation = read_json(POST_DIR / "batch021_dynamic_era_materialization_recommendation.json")
    state = read_json(BATCH021_DIR / "consolidated_state_clean_replication_batch_021.json")
    preservation = read_json(BATCH021_DIR / "batch020_boundary_preservation.json")
    lock = read_json(BATCH021_DIR / "manual_dependency_lock_validation_preservation.json")
    blocker_preservation = read_json(BATCH021_DIR / "environment_materialization_blocker_preservation.json")
    claim = read_json(BATCH021_DIR / "claim_boundary_batch021.json")
    registry = read_json(BATCH021_DIR / "runtime_provider_registry.json")
    selection = read_json(BATCH021_DIR / "runtime_provider_selection_decision.json")
    version_gate = read_json(BATCH021_DIR / "runtime_version_gate_audit.json")
    materialization = read_json(BATCH021_DIR / "dynamic_era_materialization_status.json")
    preflight = read_json(BATCH021_DIR / "runtime_provider_preflight_results.json")
    provider_status = read_json(BATCH021_DIR / "python37_runtime_provider_status.json")
    custody = read_json(BATCH021_DIR / "runtime_provider_custody_audit.json")
    hosted = read_json(BATCH021_DIR / "hosted_runtime_adapter_status.json")
    self_hosted = read_json(BATCH021_DIR / "self_hosted_runtime_plan.json")
    container_plan = read_json(BATCH021_DIR / "containerized_workflow_plan.json")
    install = read_json(BATCH021_DIR / "provider_lock_install_log.json")
    environment = read_json(BATCH021_DIR / "selected_provider_environment_materialization_log.json")
    target_retry = read_json(BATCH021_DIR / "target_intent_alignment_retry_under_provider_audit.json")
    harness = read_json(BATCH021_DIR / "issue_derived_harness_v6_verification_result.json")
    repair = read_json(BATCH021_DIR / "repair_only_fallback_status.json")
    feasibility = read_json(BATCH021_DIR / "issue_derived_repair_feasibility_status.json")
    diagnostic = read_json(BATCH021_DIR / "issue_derived_matched_null_diagnostic_status.json")
    viability = read_json(BATCH021_DIR / "darker_issue112_candidate_viability_decision.json")
    next_action = read_json(BATCH021_DIR / "runtime_provider_next_action.json")
    ledger = read_json(BATCH021_DIR / "proof_obligations_ledger.json")
    rollback = read_json(BATCH021_DIR / "rollback_block_ledger_audit.json")
    safe_stop = read_json(BATCH021_DIR / "compute_budget_safe_stop_batch021.json")
    activation = read_json(BATCH021_DIR / "activation_order_guardrail_batch021.json")
    taxonomy = read_json(BATCH021_DIR / "failure_taxonomy_batch021.json")
    minimality = read_json(BATCH021_DIR / "artifact_minimality_audit.json")
    budget = read_json(BATCH021_DIR / "artifact_payload_budget.json")
    language = read_json(BATCH021_DIR / "public_language_audit_batch021.json")
    catalog = read_json(Path("configs/controllergate_capability_catalog.json"))

    if phase_a.get("status") != "PASS" or phase_a.get("actual_sha256") != "d00ee1134862bcf83e6e979442d7e95fef3a1af1114049be9719cebdd36a84e8":
        errors.append("Batch020 official artifact verification not preserved")
    if phase_a.get("actual_size_bytes") != 136564 or phase_a.get("zip_entry_count") != 163:
        errors.append("Batch020 official artifact size or entry count mismatch")
    if ingest.get("status") != "PASS" or ingest.get("zip_tar_payload_ingested") is not False:
        errors.append("Batch020 ingest summary invalid")
    if recommendation.get("recommended_next_batch") != "clean_replication_batch_021" or recommendation.get("recommended_next_probe") != "runtime_provider_selection":
        errors.append("Batch021 recommendation missing")
    if preservation.get("status") != "PASS" or preservation.get("batch020_exact_blocker") != "manual_lock_environment_materialization_failed":
        errors.append("Batch020 boundary not preserved in Batch021")
    if lock.get("status") != "PASS" or not lock.get("manual_dependency_lock_sha256"):
        errors.append("manual dependency lock preservation failed")
    if blocker_preservation.get("carried_forward_blocker") != "manual_lock_environment_materialization_failed":
        errors.append("Batch020 materialization blocker not carried forward")
    if claim.get("native_repair_episode_count") != 4 or claim.get("issue_derived_repair_episode_count") != 0:
        errors.append("Batch021 repair counts changed")
    if claim.get("full_scoring") != "NOT_RUN/disallowed" or claim.get("memory_lift") != "not_demonstrated":
        errors.append("Batch021 full scoring or memory boundary changed")
    if claim.get("self_maintaining_software") != "false/not_demonstrated" or claim.get("production_runtime_readiness") != "false/not_demonstrated":
        errors.append("Batch021 overclaim boundary changed")
    if registry.get("label_only_provider_accepted") is not False:
        errors.append("runtime provider registry accepted label-only evidence")
    if selection.get("status") != "BLOCK" or selection.get("blocker") != "runtime_provider_exact_version_unavailable":
        errors.append("runtime provider selection blocker mismatch")
    if selection.get("decision") != "self_hosted_runtime_required" or selection.get("target_replay_allowed") is not False:
        errors.append("runtime provider selection decision invalid")
    if version_gate.get("status") != "BLOCK" or materialization.get("status") != "BLOCK":
        errors.append("runtime version/materialization gates did not block")
    if preflight.get("status") != "BLOCK" or provider_status.get("exact_provider_verified") is not False:
        errors.append("runtime provider preflight did not block on exact provider")
    if custody.get("label_only_provider_accepted") is not False or custody.get("target_replay_allowed") is not False:
        errors.append("runtime provider custody audit invalid")
    if hosted.get("status") != "UNVERIFIED" or container_plan.get("status") != "PLAN_ONLY":
        errors.append("hosted/container provider statuses invalid")
    if self_hosted.get("status") != "PLAN_READY":
        errors.append("self-hosted runtime plan missing")
    for record, label in [(install, "provider install"), (environment, "environment materialization"), (target_retry, "target retry")]:
        if record.get("status") != "NOT_RUN":
            errors.append(f"{label} ran without verified provider")
    if harness.get("harness_generated") is not False or repair.get("repair_only_fallback_attempted") is not False:
        errors.append("harness or repair ran without verified provider")
    if feasibility.get("issue_derived_repair_feasibility") is not False or diagnostic.get("matched_null_diagnostic_run_count") != 0:
        errors.append("issue-derived feasibility or matched-null diagnostic ran without verified provider")
    if viability.get("decision") != "self_hosted_runtime_required" or next_action.get("next_allowed_action") != "provide_verified_python37_runtime_provider_or_self_hosted_runner":
        errors.append("Batch021 next action mismatch")
    if rollback.get("status") != "PASS" or rollback.get("rollback_block_count", 0) < 1:
        errors.append("Batch021 rollback block missing")
    if not any(isinstance(item, dict) and item.get("entry_type") == "ROLLBACK_BLOCK" for item in ledger.get("entries", [])):
        errors.append("Batch021 proof ledger rollback block missing")
    if safe_stop.get("status") != "PASS" or safe_stop.get("safe_stop_success") is not True:
        errors.append("Batch021 safe-stop record invalid")
    if activation.get("order_preserved") is not True or activation.get("replay_executed") is not False or activation.get("repair_executed") is not False:
        errors.append("Batch021 activation order invalid")
    if taxonomy.get("taxonomy_class") != "runtime_provider_exact_version_unavailable":
        errors.append("Batch021 failure taxonomy mismatch")
    if state.get("status") != "PASS_WITH_BATCH021_RUNTIME_PROVIDER_SELF_HOSTED_PLAN":
        errors.append("Batch021 state mismatch")
    if state.get("exact_blocker") != "runtime_provider_exact_version_unavailable":
        errors.append("Batch021 exact blocker mismatch")
    if minimality.get("recursive_prior_batch_packaging_detected") is not False:
        errors.append("recursive_prior_batch_packaging_detected")
    if budget.get("status") != "PASS" or int(budget.get("hard_primary_artifact_bytes", 0)) != 750000:
        errors.append("primary_artifact_budget_exceeded")
    if language.get("status") != "PASS":
        errors.append("Batch021 public language audit failed")
    if catalog.get("catalog_version") not in {"batch021", "batch022", "batch023"}:
        errors.append("Batch021 capability catalog version missing")
    return errors


def audit_batch022_records() -> list[str]:
    errors: list[str] = []
    for name in BATCH022_REQUIRED:
        if not (BATCH022_DIR / name).is_file():
            errors.append(f"batch022 missing required file {name}")
    if errors:
        return errors
    manifest = verify_manifest(BATCH022_DIR)
    if manifest.get("status") != "PASS":
        errors.append(f"batch022 manifest failed: {manifest}")
    phase_a = read_json(POST_DIR / "batch021_dynamic_era_materialization_artifact_verification.json")
    ingest = read_json(POST_DIR / "batch021_dynamic_era_materialization_ingest_summary.json")
    recommendation = read_json(POST_DIR / "batch022_docker_provider_and_psa82_recommendation.json")
    state = read_json(BATCH022_DIR / "consolidated_state_clean_replication_batch_022.json")
    preservation = read_json(BATCH022_DIR / "batch021_boundary_preservation.json")
    blocker_preservation = read_json(BATCH022_DIR / "runtime_provider_blocker_preservation.json")
    claim = read_json(BATCH022_DIR / "claim_boundary_batch022.json")
    docker_policy = read_json(BATCH022_DIR / "docker_runtime_provider_policy.json")
    provider = read_json(BATCH022_DIR / "python37_docker_provider_preflight.json")
    version_gate = read_json(BATCH022_DIR / "runtime_version_gate_audit_batch022.json")
    security = read_json(BATCH022_DIR / "container_security_policy_batch022.json")
    workflow = read_json(BATCH022_DIR / "containerized_workflow_audit.json")
    lock_revalidation = read_json(BATCH022_DIR / "manual_dependency_lock_provider_revalidation.json")
    install = read_json(BATCH022_DIR / "manual_dependency_lock_provider_install_status.json")
    environment = read_json(BATCH022_DIR / "manual_lock_environment_materialization_log.json")
    target_retry = read_json(BATCH022_DIR / "target_intent_alignment_retry_audit.json")
    harness = read_json(BATCH022_DIR / "issue_derived_harness_v7_verification_result.json")
    repair = read_json(BATCH022_DIR / "repair_only_fallback_status.json")
    feasibility = read_json(BATCH022_DIR / "issue_derived_repair_feasibility_status.json")
    diagnostic = read_json(BATCH022_DIR / "issue_derived_matched_null_diagnostic_status.json")
    psa_presence = read_json(BATCH022_DIR / "psa82_package_presence_check.json")
    psa_policy = read_json(BATCH022_DIR / "psa82_package_quarantine_policy.json")
    psa_final = read_json(BATCH022_DIR / "psa82_final_locked_manifest_audit.json")
    psa_legacy = read_json(BATCH022_DIR / "psa82_legacy_manifest_stale_audit.json")
    psa_pyc = read_json(BATCH022_DIR / "psa82_pyc_payload_audit.json")
    psa_claim = read_json(BATCH022_DIR / "psa82_adapter_claim_boundary.json")
    fragility_policy = read_json(BATCH022_DIR / "structured_fragility_audit_policy.json")
    fragility_status = read_json(BATCH022_DIR / "structured_fragility_audit_status.json")
    fragility_results = read_json(BATCH022_DIR / "structured_fragility_audit_results.json")
    null_policy = read_json(BATCH022_DIR / "permutation_null_audit_policy.json")
    null_results = read_json(BATCH022_DIR / "permutation_null_audit_results.json")
    sensitivity_policy = read_json(BATCH022_DIR / "patch_structure_sensitivity_policy.json")
    sensitivity_results = read_json(BATCH022_DIR / "patch_structure_sensitivity_results.json")
    geometry = read_json(BATCH022_DIR / "active_search_geometry_execution_trace.json")
    curvature = read_json(BATCH022_DIR / "curvature_claim_boundary.json")
    ledger = read_json(BATCH022_DIR / "proof_obligations_ledger.json")
    rollback = read_json(BATCH022_DIR / "rollback_block_ledger_audit.json")
    safe_stop = read_json(BATCH022_DIR / "compute_budget_safe_stop_batch022.json")
    taxonomy = read_json(BATCH022_DIR / "failure_taxonomy_batch022.json")
    activation = read_json(BATCH022_DIR / "activation_order_guardrail_status.json")
    ghost = read_json(BATCH022_DIR / "rollback_ghost_state_guardrail_status.json")
    dependency = read_json(BATCH022_DIR / "dependency_overlap_grouping_status.json")
    consistency = read_json(BATCH022_DIR / "consistency_reassertion_status.json")
    minimality = read_json(BATCH022_DIR / "artifact_minimality_audit.json")
    budget = read_json(BATCH022_DIR / "artifact_payload_budget.json")
    language = read_json(BATCH022_DIR / "public_language_audit_batch022.json")
    catalog = read_json(Path("configs/controllergate_capability_catalog.json"))

    if phase_a.get("status") != "PASS" or phase_a.get("actual_sha256") != "f6fdb5bd5b942bdf5722ec2d1e58fd4a2603515f4ec125ea601ba4b60e905ee5":
        errors.append("Batch021 official artifact verification not preserved")
    if phase_a.get("actual_size_bytes") != 144180 or phase_a.get("zip_entry_count") != 176:
        errors.append("Batch021 artifact size or entry count mismatch")
    if ingest.get("status") != "PASS" or ingest.get("zip_tar_payload_ingested") is not False:
        errors.append("Batch021 ingest summary invalid")
    if recommendation.get("recommended_next_batch") != "clean_replication_batch_022":
        errors.append("Batch022 recommendation missing")
    if preservation.get("status") != "PASS" or preservation.get("batch021_exact_blocker") != "runtime_provider_exact_version_unavailable":
        errors.append("Batch021 boundary not preserved")
    if blocker_preservation.get("carried_blocker") != "runtime_provider_exact_version_unavailable":
        errors.append("Batch021 provider blocker not preserved")
    if claim.get("native_repair_episode_count") != 4 or claim.get("issue_derived_repair_episode_count") != 0:
        errors.append("Batch022 repair counts changed")
    if claim.get("full_scoring") != "NOT_RUN/disallowed" or claim.get("memory_lift") != "not_demonstrated":
        errors.append("Batch022 scoring or memory boundary changed")
    if claim.get("self_maintaining_software") != "false/not_demonstrated" or claim.get("hallucination_elimination") != "false/not_claimed" or claim.get("absolute_uncrashability") != "false/not_claimed":
        errors.append("Batch022 overclaim boundary changed")
    if docker_policy.get("actual_python_version_probe_required") is not True or docker_policy.get("image_label_only_allowed") is not False:
        errors.append("Docker provider policy missing exact runtime guard")
    if provider.get("provider_verified") is True and not provider.get("actual_python_version"):
        errors.append("provider verified without actual Python version")
    if provider.get("status") == "PASS" and version_gate.get("status") != "PASS":
        errors.append("provider passed while runtime version gate failed")
    if security.get("external_source_executed_with_write_credentials") is not False or security.get("secrets_exposed_to_external_source") is not False:
        errors.append("external source security policy invalid")
    if workflow.get("container_workspace_staged") is not False or workflow.get("secrets_exposed") is not False:
        errors.append("container workflow audit invalid")
    if lock_revalidation.get("canonical_lock_only") is not True or lock_revalidation.get("actual_sha256") != "108d961f89b603d3c6a7bcb374976992c3fadc80497bf967421cdea38aff248a":
        errors.append("manual dependency lock provider revalidation invalid")
    if provider.get("status") != "PASS":
        if install.get("status") != "NOT_RUN" or environment.get("status") != "NOT_RUN" or target_retry.get("status") != "NOT_RUN":
            errors.append("downstream provider gates ran after provider block")
    if harness.get("harness_generated") is not False or repair.get("repair_only_fallback_attempted") is not False:
        errors.append("harness or repair ran without target-intent alignment")
    if feasibility.get("issue_derived_repair_feasibility") is not False or diagnostic.get("matched_null_diagnostic_run_count") != 0:
        errors.append("issue-derived feasibility or matched-null diagnostic ran unexpectedly")
    if psa_policy.get("final_locked_manifest_authoritative") is not True or psa_policy.get("legacy_manifest_authoritative") is not False:
        errors.append("PSA-82 manifest authority policy invalid")
    if psa_presence.get("psa82_package_present") is True and psa_final.get("status") != "PASS":
        errors.append("PSA-82 final locked manifest failed")
    if psa_legacy.get("legacy_manifest_authoritative") is not False:
        errors.append("PSA-82 legacy manifest used as authoritative")
    if psa_pyc.get("pyc_payloads_quarantined") is not True or psa_pyc.get("pyc_payloads_ingested") is True:
        errors.append("PSA-82 pyc quarantine invalid")
    if psa_claim.get("controllergate_repair_evidence") is not False:
        errors.append("PSA-82 claim boundary overreach")
    if fragility_policy.get("diagnostic_only") is not True or fragility_policy.get("can_increment_repair_count") is not False:
        errors.append("Structured Fragility Audit policy invalid")
    if fragility_status.get("used_as_repair_evidence") is not False or fragility_results.get("used_as_repair_evidence") is not False:
        errors.append("Structured Fragility Audit used as repair evidence")
    if null_policy.get("preregistration_required") is not True or null_results.get("invalid_by_construction_null_count") != 0:
        errors.append("Permutation Null Audit policy/results invalid")
    if sensitivity_policy.get("can_replace_repair_validation") is not False or sensitivity_results.get("used_as_repair_evidence") is not False:
        errors.append("Patch-Structure Sensitivity overreach")
    if geometry.get("empirical_evidence_replaced") is not False or curvature.get("curvature_can_replace_evidence") is not False:
        errors.append("geometry or curvature replaced empirical evidence")
    if rollback.get("status") != "PASS" or rollback.get("rollback_block_count", 0) < 1:
        errors.append("Batch022 rollback block missing")
    if not any(isinstance(item, dict) and item.get("entry_type") == "ROLLBACK_BLOCK" for item in ledger.get("entries", [])):
        errors.append("Batch022 proof ledger rollback block missing")
    if safe_stop.get("status") != "PASS" or safe_stop.get("downstream_repair_ran") is not False:
        errors.append("Batch022 safe-stop invalid")
    if taxonomy.get("status") != "PASS" or taxonomy.get("taxonomy_class") not in {"docker_runtime_provider_unavailable", "runtime_provider_exact_version_unavailable"}:
        errors.append("Batch022 failure taxonomy invalid")
    if activation.get("order_preserved") is not True or activation.get("repair_before_target_intent") is not False:
        errors.append("Batch022 activation-order guardrail invalid")
    if ghost.get("downstream_state_contaminated") is not False:
        errors.append("Batch022 rollback ghost state detected")
    if dependency.get("may_override_provider_gate") is not False or consistency.get("claim_boundary_reasserted") is not True:
        errors.append("Batch022 dependency/consistency guardrail invalid")
    if state.get("status") != "PASS_WITH_BATCH022_DOCKER_PROVIDER_BLOCKED":
        errors.append("Batch022 state mismatch")
    if minimality.get("recursive_prior_batch_packaging_detected") is not False:
        errors.append("recursive_prior_batch_packaging_detected")
    if budget.get("status") != "PASS" or int(budget.get("hard_primary_artifact_bytes", 0)) != 750000:
        errors.append("primary_artifact_budget_exceeded")
    if language.get("status") != "PASS":
        errors.append("Batch022 public language audit failed")
    if catalog.get("catalog_version") not in {"batch022", "batch023"}:
        errors.append("Batch022 capability catalog version missing")
    return errors


def audit_batch023_records() -> list[str]:
    errors: list[str] = []
    for name in BATCH023_REQUIRED:
        if not (BATCH023_DIR / name).is_file():
            errors.append(f"batch023 missing required file {name}")
    if errors:
        return errors
    manifest = verify_manifest(BATCH023_DIR)
    if manifest.get("status") != "PASS":
        errors.append(f"batch023 manifest failed: {manifest}")
    phase_a = read_json(POST_DIR / "batch022_docker_era_psa82_artifact_verification.json")
    ingest = read_json(POST_DIR / "batch022_docker_era_psa82_ingest_summary.json")
    recommendation = read_json(POST_DIR / "batch023_bounded_docker_provider_recommendation.json")
    state = read_json(BATCH023_DIR / "consolidated_state_clean_replication_batch_023.json")
    preservation = read_json(BATCH023_DIR / "batch022_boundary_preservation.json")
    blocker_preservation = read_json(BATCH023_DIR / "docker_provider_blocker_preservation.json")
    claim = read_json(BATCH023_DIR / "claim_boundary_batch023.json")
    activation_policy = read_json(BATCH023_DIR / "docker_provider_activation_policy.json")
    activation_gate = read_json(BATCH023_DIR / "docker_provider_activation_gate.json")
    enablement = read_json(BATCH023_DIR / "docker_provider_enablement_audit.json")
    bridge_policy = read_json(BATCH023_DIR / "github_actions_provider_bridge_policy.json")
    bridge = read_json(BATCH023_DIR / "github_actions_provider_bridge_audit.json")
    credentials = read_json(BATCH023_DIR / "provider_credentials_isolation_audit.json")
    transport = read_json(BATCH023_DIR / "provider_workspace_transport_audit.json")
    provider = read_json(BATCH023_DIR / "python37_provider_preflight_results.json")
    version_gate = read_json(BATCH023_DIR / "runtime_version_gate_audit_batch023.json")
    docker_status = read_json(BATCH023_DIR / "docker_provider_status_batch023.json")
    lock_revalidation = read_json(BATCH023_DIR / "manual_dependency_lock_provider_revalidation.json")
    install = read_json(BATCH023_DIR / "manual_dependency_lock_provider_install_status.json")
    materialization = read_json(BATCH023_DIR / "manual_lock_environment_materialization_log.json")
    target_retry = read_json(BATCH023_DIR / "target_intent_alignment_retry_audit.json")
    harness = read_json(BATCH023_DIR / "issue_derived_harness_v8_verification_result.json")
    repair = read_json(BATCH023_DIR / "repair_only_fallback_status.json")
    feasibility = read_json(BATCH023_DIR / "issue_derived_repair_feasibility_status.json")
    diagnostic = read_json(BATCH023_DIR / "issue_derived_matched_null_diagnostic_status.json")
    psa_presence = read_json(BATCH023_DIR / "psa82_local_package_presence_check.json")
    psa_summary = read_json(BATCH023_DIR / "psa82_local_package_quarantine_summary.json")
    psa_final = read_json(BATCH023_DIR / "psa82_final_locked_manifest_summary.json")
    psa_legacy = read_json(BATCH023_DIR / "psa82_legacy_manifest_status.json")
    psa_pyc = read_json(BATCH023_DIR / "psa82_pyc_quarantine_summary.json")
    psa_claim = read_json(BATCH023_DIR / "psa82_adapter_claim_boundary.json")
    fragility = read_json(BATCH023_DIR / "structured_fragility_audit_status.json")
    null_policy = read_json(BATCH023_DIR / "permutation_null_audit_policy.json")
    sensitivity_policy = read_json(BATCH023_DIR / "patch_structure_sensitivity_policy.json")
    geometry = read_json(BATCH023_DIR / "active_search_geometry_execution_trace.json")
    curvature = read_json(BATCH023_DIR / "curvature_claim_boundary.json")
    ledger = read_json(BATCH023_DIR / "proof_obligations_ledger.json")
    rollback = read_json(BATCH023_DIR / "rollback_block_ledger_audit.json")
    safe_stop = read_json(BATCH023_DIR / "compute_budget_safe_stop_batch023.json")
    taxonomy = read_json(BATCH023_DIR / "failure_taxonomy_batch023.json")
    activation_order = read_json(BATCH023_DIR / "activation_order_guardrail_status.json")
    ghost = read_json(BATCH023_DIR / "rollback_ghost_state_guardrail_status.json")
    dependency = read_json(BATCH023_DIR / "dependency_overlap_grouping_status.json")
    consistency = read_json(BATCH023_DIR / "consistency_reassertion_status.json")
    minimality = read_json(BATCH023_DIR / "artifact_minimality_audit.json")
    budget = read_json(BATCH023_DIR / "artifact_payload_budget.json")
    language = read_json(BATCH023_DIR / "public_language_audit_batch023.json")
    catalog = read_json(Path("configs/controllergate_capability_catalog.json"))

    if phase_a.get("status") != "PASS" or phase_a.get("actual_sha256") != "e6e092ddd4519b6335975b98fe0f8eba6474850620af0c018191de10fa049b0f":
        errors.append("Batch022 artifact ingest verification invalid")
    if ingest.get("status") != "PASS" or ingest.get("zip_tar_payload_ingested") is not False:
        errors.append("Batch022 ingest summary invalid")
    if recommendation.get("recommended_next_batch") != "clean_replication_batch_023":
        errors.append("Batch023 recommendation missing")
    if preservation.get("status") != "PASS" or preservation.get("batch022_exact_blocker") != "docker_runtime_provider_unavailable":
        errors.append("Batch022 boundary not preserved")
    if blocker_preservation.get("carried_blocker") != "docker_runtime_provider_unavailable":
        errors.append("Batch022 Docker provider blocker not preserved")
    if claim.get("native_repair_episode_count") != 4 or claim.get("issue_derived_repair_episode_count") != 0:
        errors.append("Batch023 repair counts changed")
    if claim.get("full_scoring") != "NOT_RUN/disallowed" or claim.get("memory_lift") != "not_demonstrated":
        errors.append("Batch023 scoring or memory boundary changed")
    if claim.get("self_maintaining_software") != "false/not_demonstrated" or claim.get("hallucination_elimination") != "false/not_claimed" or claim.get("absolute_uncrashability") != "false/not_claimed":
        errors.append("Batch023 overclaim boundary changed")
    if activation_policy.get("bounded_probe_required") is not True or activation_policy.get("broad_docker_execution_allowed") is not False:
        errors.append("Batch023 activation policy invalid")
    if enablement.get("provider_probe_unbounded") is not False:
        errors.append("Batch023 provider probe unbounded")
    if bridge_policy.get("checkout_persist_credentials_required_false") is not True or bridge.get("workflow_provider_bridge_present") is not True:
        errors.append("Batch023 GitHub Actions provider bridge missing")
    if credentials.get("github_token_passed_to_provider") is not False or credentials.get("write_credentials_passed_to_provider") is not False or credentials.get("secrets_exposed_to_external_source") is not False:
        errors.append("Batch023 provider credential isolation failed")
    if provider.get("status") == "PASS":
        if not provider.get("actual_python_version") or not str(provider.get("actual_python_version")).startswith("3.7."):
            errors.append("Batch023 actual Python version missing or mismatched")
        if not provider.get("actual_pip_version"):
            errors.append("Batch023 actual pip version missing")
        if transport.get("status") != "PASS" or not transport.get("output_sha256"):
            errors.append("Batch023 provider output transport invalid")
        if version_gate.get("status") != "PASS":
            errors.append("Batch023 runtime version gate did not pass with provider")
    else:
        if activation_gate.get("enabled") is True and provider.get("blocker") not in {"docker_runtime_provider_unavailable", "python37_docker_provider_unavailable", "runtime_provider_python_version_mismatch", "python37_provider_unavailable"}:
            errors.append("Batch023 provider blocker invalid")
    if docker_status.get("actual_provider_python_version") != provider.get("actual_python_version"):
        errors.append("Batch023 Docker status/provider preflight mismatch")
    if lock_revalidation.get("actual_sha256") != "108d961f89b603d3c6a7bcb374976992c3fadc80497bf967421cdea38aff248a":
        errors.append("Batch023 manual dependency lock revalidation mismatch")
    if install.get("status") == "PASS" and provider.get("status") != "PASS":
        errors.append("Batch023 lock install passed before provider")
    if materialization.get("status") == "PASS" and install.get("status") != "PASS":
        errors.append("Batch023 materialization passed before install")
    if target_retry.get("target_intent_alignment") is True and materialization.get("status") != "PASS":
        errors.append("Batch023 target-intent passed before materialization")
    if harness.get("harness_generated") is True and target_retry.get("target_intent_alignment") is not True:
        errors.append("Batch023 harness generated before target-intent alignment")
    if repair.get("repair_only_fallback_attempted") is True and target_retry.get("target_intent_alignment") is not True:
        errors.append("Batch023 repair ran before target-intent alignment")
    if feasibility.get("issue_derived_repair_feasibility") is True and target_retry.get("target_intent_alignment") is not True:
        errors.append("Batch023 issue-derived feasibility overclaim")
    if diagnostic.get("native_memory_separation_claim_allowed") is not False:
        errors.append("Batch023 diagnostic allowed native memory claim")
    if psa_presence.get("psa82_package_present") is True:
        if psa_summary.get("full_package_committed") is not False or psa_final.get("status") != "PASS":
            errors.append("Batch023 PSA-82 quarantine summary invalid")
    if psa_legacy.get("legacy_manifest_authoritative") is not False or psa_pyc.get("pyc_payloads_quarantined") is not True or psa_claim.get("controllergate_repair_evidence") is not False:
        errors.append("Batch023 PSA-82 quarantine boundary invalid")
    if fragility.get("status") != "NOT_RUN_NO_PATCH_CANDIDATE":
        errors.append("Batch023 structured fragility status invalid")
    if not null_policy.get("allowed_nulls") or null_policy.get("preregistration_required") is not True or sensitivity_policy.get("diagnostic_only") is not True:
        errors.append("Batch023 diagnostic policies invalid")
    if geometry.get("empirical_evidence_replaced") is not False or curvature.get("curvature_can_replace_evidence") is not False:
        errors.append("Batch023 geometry or curvature replaced empirical evidence")
    if rollback.get("status") != "PASS" or rollback.get("rollback_block_count", 0) < 1:
        errors.append("Batch023 rollback block missing")
    if not any(isinstance(item, dict) and item.get("entry_type") == "ROLLBACK_BLOCK" for item in ledger.get("entries", [])):
        errors.append("Batch023 proof ledger rollback block missing")
    if safe_stop.get("status") != "PASS" or safe_stop.get("downstream_repair_ran") is not False:
        errors.append("Batch023 safe-stop invalid")
    if taxonomy.get("taxonomy_class") not in {"docker_provider_not_enabled", "docker_runtime_provider_unavailable", "python37_docker_provider_unavailable", "runtime_provider_python_version_mismatch", "manual_dependency_lock_provider_install_failed", "manual_lock_environment_materialization_failed", "target_intent_alignment_not_reached"}:
        errors.append("Batch023 failure taxonomy invalid")
    if activation_order.get("order_preserved") is not True or activation_order.get("repair_before_target_intent") is not False:
        errors.append("Batch023 activation-order guardrail invalid")
    if ghost.get("downstream_state_contaminated") is not False:
        errors.append("Batch023 rollback ghost state detected")
    if dependency.get("may_override_provider_gate") is not False or consistency.get("claim_boundary_reasserted") is not True:
        errors.append("Batch023 dependency/consistency guardrail invalid")
    if not str(state.get("status", "")).startswith("PASS_WITH_BATCH023_"):
        errors.append("Batch023 state mismatch")
    if state.get("full_scoring") != "NOT_RUN/disallowed" or state.get("self_maintaining_software") != "false/not_demonstrated":
        errors.append("Batch023 claim boundary mismatch")
    if minimality.get("recursive_prior_batch_packaging_detected") is not False:
        errors.append("recursive_prior_batch_packaging_detected")
    if budget.get("status") != "PASS":
        errors.append("primary_artifact_budget_exceeded")
    if language.get("status") != "PASS":
        errors.append("Batch023 public language audit failed")
    if catalog.get("catalog_version") != "batch023":
        errors.append("Batch023 capability catalog version missing")
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
        Path("docs/claim_boundary.md"),
        Path("docs/memory_lift_definition.md"),
        Path("docs/public_release_readiness.md"),
        Path("docs/technical_validation_gap_report.md"),
        Path("docs/replication_protocol.md"),
        Path("docs/evidence_model.md"),
        Path("docs/operational_gate_matrix.md"),
        Path("docs/controllergate_positioning.md"),
        Path("docs/controllergate_claim_tiers.md"),
        Path("docs/skeptics_acceptance_checklist.md"),
        Path("docs/use_case_positioning.md"),
        Path("docs/structure_first_compiler_roadmap.md"),
        Path("docs/future_agentic_admissibility_compiler_integration.md"),
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
        Path("configs/clean_replication_batch_011.json"),
        Path("configs/clean_replication_batch_012.json"),
        Path("configs/clean_replication_batch_013.json"),
        Path("configs/clean_replication_batch_014.json"),
        Path("configs/clean_replication_batch_015.json"),
        Path("configs/clean_replication_batch_016.json"),
        Path("configs/clean_replication_batch_017.json"),
        Path("docs/artifact_packaging_policy.md"),
        Path("configs/lock_sequence_operation_registry.json"),
        Path("configs/controllergate_claim_tiers.json"),
        Path("configs/controllergate_capability_catalog.json"),
        Path("controllergate/core/failure_memory.py"),
        Path("controllergate/core/status_code_weighting.py"),
        Path("controllergate/core/source_ranking.py"),
        Path("controllergate/core/prospective_memory_challenge.py"),
        Path("controllergate/core/curvature_selection.py"),
        Path("controllergate/core/issue_derived_harness.py"),
        Path("controllergate/core/targeted_seed.py"),
        Path("controllergate/core/environment_lock.py"),
        Path("controllergate/core/command_manifest.py"),
        Path("controllergate/core/workspace_purity.py"),
        Path("controllergate/core/baseline_precheck.py"),
        Path("controllergate/core/rollback_ledger.py"),
        Path("controllergate/core/gate_chain.py"),
        Path("controllergate/core/active_context_filtering.py"),
        Path("controllergate/runtime/incident_capture.py"),
        Path("controllergate/runtime/execution_boundary_gateway.py"),
        Path("controllergate/runtime/isolated_repair_sandbox.py"),
        Path("controllergate/runtime/dependency_drift_chaperone.py"),
        Path("controllergate/runtime/active_ast_excision_probe.py"),
        Path("controllergate/runtime/syntax_micro_rollback.py"),
        Path("controllergate/runtime/predictive_degradation_telemetry.py"),
        Path("controllergate/runtime/compute_budget.py"),
        Path("controllergate/runtime/blue_green_deployment.py"),
        Path("controllergate/runtime/proof_to_action_compiler.py"),
        Path("controllergate/runtime/runtime_claim_boundary.py"),
        Path("controllergate_v1_7_beta/reports/critic_review_package/shareable_summary.md"),
        Path(".github/workflows/post_v2_37_hardening_and_batch002.yml"),
    ]
    paths.extend(sorted(BATCH010_DIR.glob("*.json")))
    paths.extend(sorted(BATCH010_DIR.glob("*.md")))
    paths.extend(sorted(BATCH011_DIR.glob("*.json")))
    paths.extend(sorted(BATCH011_DIR.glob("*.md")))
    paths.extend(sorted(BATCH012_DIR.glob("*.json")))
    paths.extend(sorted(BATCH012_DIR.glob("*.md")))
    paths.extend(sorted(BATCH013_DIR.glob("*.json")))
    paths.extend(sorted(BATCH013_DIR.glob("*.md")))
    paths.extend(sorted(BATCH014_DIR.glob("*.json")))
    paths.extend(sorted(BATCH014_DIR.glob("*.md")))
    paths.extend(sorted(BATCH015_DIR.glob("*.json")))
    paths.extend(sorted(BATCH015_DIR.glob("*.md")))
    paths.extend(sorted(BATCH016_DIR.glob("*.json")))
    paths.extend(sorted(BATCH016_DIR.glob("*.md")))
    paths.extend(sorted(BATCH017_DIR.glob("*.json")))
    paths.extend(sorted(BATCH017_DIR.glob("*.md")))
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
    "status_code_feature_weighting",
    "curvature_based_candidate_selection",
    "two_winner_source_selection",
    "prospective_memory_challenge",
    "targeted_prospective_seed_intake",
    "native_target_test_verification",
    "prospective_memory_eligibility_gate",
    "source_commit_environment_lock",
    "target_command_manifest",
    "fresh_workspace_purity_gate",
    "baseline_registry_drift_precheck",
    "rollback_block_ledger",
    "global_curvature_logic_enforcement",
    "curvature_feature_vector",
    "basin_stability_check",
    "two_winner_global_policy",
    "curvature_memory_routing",
    "curvature_fragment_planning",
    "null_ensemble_curvature_fairness",
    "curvature_claim_boundary",
    "batch013_gate_chain_binding",
    "targeted_seed_git_tracking",
    "active_context_filtering",
    "curvature_heuristic_freeze",
    "five_locks_curvature_cross_gate",
    "issue_derived_temporal_classification",
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
        + require_files(BATCH011_DIR, BATCH011_REQUIRED)
        + require_files(BATCH012_DIR, BATCH012_REQUIRED)
        + require_files(BATCH013_DIR, BATCH013_REQUIRED)
        + require_files(BATCH014_DIR, BATCH014_REQUIRED)
        + require_files(BATCH015_DIR, BATCH015_REQUIRED)
        + require_files(BATCH016_DIR, BATCH016_REQUIRED)
        + require_files(BATCH017_DIR, BATCH017_REQUIRED)
        + require_files(BATCH020_DIR, BATCH020_REQUIRED)
        + require_files(BATCH021_DIR, BATCH021_REQUIRED)
        + require_files(BATCH022_DIR, BATCH022_REQUIRED)
        + require_files(BATCH023_DIR, BATCH023_REQUIRED)
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
    if verify_manifest(BATCH011_DIR)["status"] != "PASS":
        return fail("batch011 manifest mismatch")
    if verify_manifest(BATCH012_DIR)["status"] != "PASS":
        return fail("batch012 manifest mismatch")
    if verify_manifest(BATCH013_DIR)["status"] != "PASS":
        return fail("batch013 manifest mismatch")
    if verify_manifest(BATCH014_DIR)["status"] != "PASS":
        return fail("batch014 manifest mismatch")
    if verify_manifest(BATCH015_DIR)["status"] != "PASS":
        return fail("batch015 manifest mismatch")
    if verify_manifest(BATCH016_DIR)["status"] != "PASS":
        return fail("batch016 manifest mismatch")
    if verify_manifest(BATCH017_DIR)["status"] != "PASS":
        return fail("batch017 manifest mismatch")
    if verify_manifest(BATCH018_DIR)["status"] != "PASS":
        return fail("batch018 manifest mismatch")
    if verify_manifest(BATCH019_DIR)["status"] != "PASS":
        return fail("batch019 manifest mismatch")
    if verify_manifest(BATCH020_DIR)["status"] != "PASS":
        return fail("batch020 manifest mismatch")
    if verify_manifest(BATCH021_DIR)["status"] != "PASS":
        return fail("batch021 manifest mismatch")
    if verify_manifest(BATCH022_DIR)["status"] != "PASS":
        return fail("batch022 manifest mismatch")
    if verify_manifest(BATCH023_DIR)["status"] != "PASS":
        return fail("batch023 manifest mismatch")
    if not command_passes([sys.executable, "-m", "pytest", "tests/core", "tests/runtime", "-q"]):
        return fail("core/runtime tests failed")
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
    if manifest_report.get("recursive_prior_batch_packaging_detected") is not False:
        return fail("recursive prior batch packaging detected")
    if int(manifest_report.get("payload_size_bytes", 0)) > 750000:
        return fail("primary artifact budget exceeded")
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
    batch011_errors = audit_batch011_records()
    if batch011_errors:
        return fail(f"batch011 audit failed: {batch011_errors}")
    batch012_errors = audit_batch012_records()
    if batch012_errors:
        return fail(f"batch012 audit failed: {batch012_errors}")
    batch013_errors = audit_batch013_records()
    if batch013_errors:
        return fail(f"batch013 audit failed: {batch013_errors}")
    batch014_errors = audit_batch014_records()
    if batch014_errors:
        return fail(f"batch014 audit failed: {batch014_errors}")
    batch015_errors = audit_batch015_records()
    if batch015_errors:
        return fail(f"batch015 audit failed: {batch015_errors}")
    batch016_errors = audit_batch016_records()
    if batch016_errors:
        return fail(f"batch016 audit failed: {batch016_errors}")
    batch017_errors = audit_batch017_records()
    if batch017_errors:
        return fail(f"batch017 audit failed: {batch017_errors}")
    batch018_errors = audit_batch018_records()
    if batch018_errors:
        return fail(f"batch018 audit failed: {batch018_errors}")
    batch019_errors = audit_batch019_records()
    if batch019_errors:
        return fail(f"batch019 audit failed: {batch019_errors}")
    batch020_errors = audit_batch020_records()
    if batch020_errors:
        return fail(f"batch020 audit failed: {batch020_errors}")
    batch021_errors = audit_batch021_records()
    if batch021_errors:
        return fail(f"batch021 audit failed: {batch021_errors}")
    batch022_errors = audit_batch022_records()
    if batch022_errors:
        return fail(f"batch022 audit failed: {batch022_errors}")
    batch023_errors = audit_batch023_records()
    if batch023_errors:
        return fail(f"batch023 audit failed: {batch023_errors}")
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
    if not str(final_report.get("status", "")).startswith("PASS_WITH_BATCH023_"):
        return fail("final report did not advance to Batch023 bounded Docker provider boundary")
    if final_report.get("exact_blocker") not in {"docker_provider_not_enabled", "docker_runtime_provider_unavailable", "python37_docker_provider_unavailable", "runtime_provider_python_version_mismatch", "manual_dependency_lock_provider_install_failed", "manual_lock_environment_materialization_failed", "target_intent_alignment_not_reached"}:
        return fail("final report latest validation blocker mismatch")
    if final_report.get("batch017_target_intent_alignment") is not False:
        return fail("final report Batch017 target-intent boundary mismatch")
    if final_report.get("batch017_recursive_prior_batch_packaging_detected") is not False:
        return fail("final report Batch017 thin artifact boundary mismatch")
    if final_report.get("batch018_manual_dependency_lock_status") != "ABSENT":
        return fail("final report Batch018 manual lock status mismatch")
    if final_report.get("batch018_target_intent_alignment") is not False:
        return fail("final report Batch018 target-intent boundary mismatch")
    if final_report.get("batch018_dependency_cutoff_timestamp") != "2021-01-02T00:00:00Z":
        return fail("final report Batch018 dependency cutoff mismatch")
    if final_report.get("batch019_active_search_space_geometry_status") != "PASS":
        return fail("final report Batch019 active search geometry status mismatch")
    if final_report.get("batch019_recommended_next_probe") != "dependency_lock_probe":
        return fail("final report Batch019 recommended next probe mismatch")
    if final_report.get("batch019_darker_issue112_status") != "blocked_on_manual_dependency_lock_watch_only":
        return fail("final report Batch019 Darker status mismatch")
    if final_report.get("batch020_manual_dependency_lock_validation_status") != "PASS":
        return fail("final report Batch020 manual lock validation mismatch")
    if final_report.get("batch020_environment_materialization_status") != "BLOCK":
        return fail("final report Batch020 environment materialization mismatch")
    if final_report.get("batch020_target_intent_alignment_status") != "NOT_RUN":
        return fail("final report Batch020 target-intent boundary mismatch")
    if final_report.get("batch020_harness_v5_generated") is not False:
        return fail("final report Batch020 harness boundary mismatch")
    if final_report.get("batch020_issue_derived_repair_feasibility") is not False:
        return fail("final report Batch020 issue-derived feasibility overclaim")
    if final_report.get("batch021_runtime_provider_selection_status") != "BLOCK":
        return fail("final report Batch021 runtime provider selection mismatch")
    if final_report.get("batch021_runtime_provider_selection_decision") != "self_hosted_runtime_required":
        return fail("final report Batch021 runtime provider decision mismatch")
    if final_report.get("batch021_python37_runtime_provider_status") != "BLOCK":
        return fail("final report Batch021 Python 3.7 provider status mismatch")
    if final_report.get("batch021_environment_materialization_status") != "NOT_RUN":
        return fail("final report Batch021 environment materialization boundary mismatch")
    if final_report.get("batch021_target_intent_alignment_status") != "NOT_RUN":
        return fail("final report Batch021 target-intent boundary mismatch")
    if final_report.get("batch021_harness_v6_generated") is not False:
        return fail("final report Batch021 harness boundary mismatch")
    if final_report.get("batch021_issue_derived_repair_feasibility") is not False:
        return fail("final report Batch021 issue-derived feasibility overclaim")
    if final_report.get("batch022_docker_runtime_provider_status") not in {"BLOCK", "PASS"}:
        return fail("final report Batch022 Docker provider status missing")
    if final_report.get("batch022_manual_dependency_lock_provider_install_status") != "NOT_RUN" and final_report.get("batch022_provider_preflight_status") != "PASS":
        return fail("final report Batch022 provider install boundary mismatch")
    if final_report.get("batch022_target_intent_alignment_status") != "NOT_RUN":
        return fail("final report Batch022 target-intent boundary mismatch")
    if final_report.get("batch022_harness_v7_generated") is not False:
        return fail("final report Batch022 harness boundary mismatch")
    if final_report.get("batch022_issue_derived_repair_feasibility") is not False:
        return fail("final report Batch022 issue-derived feasibility overclaim")
    if final_report.get("batch022_structured_fragility_audit_status") != "NOT_RUN_NO_PATCH_CANDIDATE":
        return fail("final report Batch022 structured fragility status mismatch")
    if final_report.get("batch023_docker_provider_activation_status") not in {"PASS", "BLOCK"}:
        return fail("final report Batch023 activation status missing")
    if final_report.get("batch023_github_actions_provider_bridge_status") != "PASS":
        return fail("final report Batch023 provider bridge status mismatch")
    if final_report.get("batch023_provider_preflight_status") not in {"PASS", "BLOCK"}:
        return fail("final report Batch023 provider preflight status missing")
    if final_report.get("batch023_provider_preflight_status") == "PASS":
        if not str(final_report.get("batch023_actual_provider_python_version", "")).startswith("3.7."):
            return fail("final report Batch023 actual Python version mismatch")
        if not final_report.get("batch023_actual_provider_pip_version"):
            return fail("final report Batch023 actual pip version missing")
    if final_report.get("batch023_provider_credentials_isolation_status") != "PASS":
        return fail("final report Batch023 credential isolation mismatch")
    if final_report.get("batch023_target_intent_alignment_status") != "NOT_RUN":
        return fail("final report Batch023 target-intent boundary mismatch")
    if final_report.get("batch023_harness_v8_generated") is not False:
        return fail("final report Batch023 harness boundary mismatch")
    if final_report.get("batch023_issue_derived_repair_feasibility") is not False:
        return fail("final report Batch023 issue-derived feasibility overclaim")
    if final_report.get("batch023_structured_fragility_diagnostic_status") != "NOT_RUN_NO_PATCH_CANDIDATE":
        return fail("final report Batch023 structured diagnostic status mismatch")
    if final_report.get("batch013_gate_chain_status") != "PASS":
        return fail("final report missing Batch013 gate-chain PASS")
    if final_report.get("public_claim_overreach_status") != "PASS":
        return fail("public claim pressure not PASS")
    hits = public_language_hits()
    if hits:
        return fail(f"public language audit failed: {hits}")

    print("post-v2.37 hardening and batch002 audit PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
