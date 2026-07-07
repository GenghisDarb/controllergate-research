from __future__ import annotations

import json
import hashlib
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
BATCH024_DIR = Path("outputs/clean_replication_batch_024")
BATCH025_DIR = Path("outputs/clean_replication_batch_025")
BATCH026_DIR = Path("outputs/clean_replication_batch_026")
BATCH027_DIR = Path("outputs/clean_replication_batch_027")
BATCH028_DIR = Path("outputs/clean_replication_batch_028")
BATCH029_DIR = Path("outputs/clean_replication_batch_029")
BATCH030_DIR = Path("outputs/clean_replication_batch_030")
BATCH031_DIR = Path("outputs/clean_replication_batch_031")
BATCH032_DIR = Path("outputs/clean_replication_batch_032")
BATCH033_DIR = Path("outputs/clean_replication_batch_033")
BATCH034_DIR = Path("outputs/clean_replication_batch_034")
BATCH035_DIR = Path("outputs/clean_replication_batch_035")
BATCH036_DIR = Path("outputs/clean_replication_batch_036")
BATCH037_DIR = Path("outputs/clean_replication_batch_037")
BATCH038_DIR = Path("outputs/clean_replication_batch_038")
BATCH039_DIR = Path("outputs/clean_replication_batch_039")
BATCH040_DIR = Path("outputs/clean_replication_batch_040")
BATCH041_DIR = Path("outputs/clean_replication_batch_041")
BATCH042_DIR = Path("outputs/clean_replication_batch_042")
BATCH043_DIR = Path("outputs/clean_replication_batch_043")
BATCH044_DIR = Path("outputs/clean_replication_batch_044")
BATCH045_DIR = Path("outputs/clean_replication_batch_045")
BATCH046_DIR = Path("outputs/clean_replication_batch_046")
BATCH047_DIR = Path("outputs/clean_replication_batch_047")
PAYLOAD_DIR = Path("artifact_payload/post_v2_37_hardening_batch047_tot_bulb_probe_execution")

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
    "batch023_bounded_docker_provider_artifact_verification.json",
    "batch023_bounded_docker_provider_ingest_summary.json",
    "batch024_provider_workspace_bridge_recommendation.json",
    "batch024_artifact_ingest_summary.json",
    "batch024_artifact_verification.json",
    "batch024_status_correction.json",
    "batch025_artifact_ingest_summary.json",
    "batch025_artifact_verification.json",
    "batch025_status_correction.json",
    "batch026_artifact_ingest_summary.json",
    "batch026_artifact_verification.json",
    "batch026_harness_state_inconsistency_audit.json",
    "batch027_artifact_ingest_summary.json",
    "batch027_artifact_verification.json",
    "batch027_execution_telemetry_precision_audit.json",
    "batch028_artifact_ingest_summary.json",
    "batch028_artifact_verification.json",
    "batch028_execution_telemetry_precision_audit.json",
    "batch029_artifact_ingest_summary.json",
    "batch029_artifact_verification.json",
    "batch029_blocker_precision_audit.json",
    "batch030_artifact_ingest_summary.json",
    "batch030_artifact_verification.json",
    "batch030_blocker_precision_audit.json",
    "batch031_artifact_ingest_summary.json",
    "batch031_artifact_verification.json",
    "batch032_artifact_ingest_summary.json",
    "batch032_artifact_verification.json",
    "batch033_artifact_ingest_summary.json",
    "batch033_artifact_verification.json",
    "batch034_artifact_ingest_summary.json",
    "batch034_artifact_verification.json",
    "batch035_artifact_ingest_summary.json",
    "batch035_artifact_verification.json",
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

BATCH024_REQUIRED = [
    "campaign_summary.md",
    "consolidated_state_clean_replication_batch_024.json",
    "batch023_boundary_preservation.json",
    "provider_preflight_preservation.json",
    "provider_install_preservation.json",
    "claim_boundary_batch024.json",
    "provider_workspace_bridge_policy.json",
    "provider_input_bundle_manifest.json",
    "provider_output_bundle_manifest.json",
    "provider_workspace_transport_audit.json",
    "provider_workspace_cleanup_audit.json",
    "provider_workspace_bridge_status.json",
    "provider_source_checkout_policy.json",
    "provider_source_checkout_audit.json",
    "provider_source_tree_manifest.json",
    "provider_source_commit_verification.json",
    "manual_lock_environment_materialization_policy.json",
    "manual_lock_environment_materialization_log.json",
    "manual_lock_environment_hash.json",
    "provider_installed_package_freeze.json",
    "provider_installed_package_hashes.json",
    "workspace_purity_report.json",
    "acquisition_lock_stack_status.json",
    "issue112_command_variant_policy.json",
    "issue112_provider_variant_results.json",
    "darker_issue112_target_intent_signature_retry.json",
    "target_intent_alignment_retry_audit.json",
    "issue_derived_harness_v9_policy.json",
    "issue_derived_harness_v9_context_manifest.json",
    "issue_derived_harness_v9_verification_result.json",
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
    "provider_workspace_bridge_next_action.json",
    "proof_obligations_ledger.json",
    "rollback_block_ledger_audit.json",
    "compute_budget_safe_stop_batch024.json",
    "failure_taxonomy_batch024.json",
    "precision_failure_log_batch024.json",
    "semantic_drift_guardrail_status.json",
    "activation_order_guardrail_status.json",
    "rollback_ghost_state_guardrail_status.json",
    "dependency_overlap_grouping_status.json",
    "consistency_reassertion_status.json",
    "public_language_audit_batch024.json",
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

BATCH025_REQUIRED = [
    "batch024_artifact_ingest_summary.json",
    "batch024_artifact_verification.json",
    "batch024_status_correction.json",
    "provider_command_context_diagnosis.json",
    "provider_git_context_audit.json",
    "provider_target_intent_variant_policy.json",
    "provider_target_intent_variant_results.json",
    "target_intent_alignment_batch025.json",
    "issue_derived_harness_v9_generation_gate.json",
    "issue_derived_repair_feasibility_batch025.json",
    "claim_boundary_batch025.json",
    "proof_obligations_ledger_batch025.json",
    "consolidated_state_clean_replication_batch_025.json",
    "campaign_summary.md",
    "public_language_audit_batch025.json",
    "artifact_packaging_policy.json",
    "artifact_payload_budget.json",
    "artifact_minimality_audit.json",
    "SHA256SUMS.txt",
]

BATCH026_REQUIRED = [
    "batch025_artifact_ingest_summary.json",
    "batch025_artifact_verification.json",
    "batch025_status_correction.json",
    "batch026_harness_v9_generation_policy.json",
    "batch026_harness_v9_generation_result.json",
    "batch026_harness_v9_pre_repair_verification.json",
    "batch026_target_intent_preservation.json",
    "batch026_decision_time_evidence_firewall.json",
    "issue_derived_repair_feasibility_batch026.json",
    "claim_boundary_batch026.json",
    "proof_obligations_ledger_batch026.json",
    "consolidated_state_clean_replication_batch_026.json",
    "issue_derived_ephemeral_harness_v9.py",
    "campaign_summary.md",
    "public_language_audit_batch026.json",
    "artifact_packaging_policy.json",
    "artifact_payload_budget.json",
    "artifact_minimality_audit.json",
    "SHA256SUMS.txt",
]

BATCH027_REQUIRED = [
    "batch026_artifact_ingest_summary.json",
    "batch026_artifact_verification.json",
    "batch026_harness_state_inconsistency_audit.json",
    "batch027_harness_v9_state_reconciliation.json",
    "batch027_harness_v9_execution_policy.json",
    "batch027_harness_v9_execution_result.json",
    "batch027_harness_v9_pre_repair_verification.json",
    "batch027_provider_command_context_audit.json",
    "batch027_decision_time_evidence_firewall.json",
    "issue_derived_repair_feasibility_batch027.json",
    "claim_boundary_batch027.json",
    "proof_obligations_ledger_batch027.json",
    "consolidated_state_clean_replication_batch_027.json",
    "campaign_summary.md",
    "public_language_audit_batch027.json",
    "artifact_packaging_policy.json",
    "artifact_payload_budget.json",
    "artifact_minimality_audit.json",
    "SHA256SUMS.txt",
]

BATCH028_REQUIRED = [
    "batch027_artifact_ingest_summary.json",
    "batch027_artifact_verification.json",
    "batch027_execution_telemetry_precision_audit.json",
    "batch028_harness_v9_payload_rehydration_policy.json",
    "batch028_harness_v9_payload_rehydration_result.json",
    "batch028_harness_v9_execution_policy.json",
    "batch028_provider_command_context_audit.json",
    "batch028_harness_v9_execution_result.json",
    "batch028_harness_v9_pre_repair_verification.json",
    "batch028_decision_time_evidence_firewall.json",
    "issue_derived_repair_feasibility_batch028.json",
    "claim_boundary_batch028.json",
    "proof_obligations_ledger_batch028.json",
    "consolidated_state_clean_replication_batch_028.json",
    "issue_derived_ephemeral_harness_v9.py",
    "campaign_summary.md",
    "public_language_audit_batch028.json",
    "artifact_packaging_policy.json",
    "artifact_payload_budget.json",
    "artifact_minimality_audit.json",
    "SHA256SUMS.txt",
]

BATCH029_REQUIRED = [
    "batch028_artifact_ingest_summary.json",
    "batch028_artifact_verification.json",
    "batch028_execution_telemetry_precision_audit.json",
    "batch029_harness_v9_execution_policy.json",
    "batch029_harness_payload_integrity_check.json",
    "batch029_provider_command_context_audit.json",
    "batch029_harness_v9_execution_result.json",
    "batch029_harness_v9_pre_repair_verification.json",
    "batch029_target_intent_match_report.json",
    "batch029_decision_time_evidence_firewall.json",
    "issue_derived_repair_feasibility_batch029.json",
    "claim_boundary_batch029.json",
    "proof_obligations_ledger_batch029.json",
    "consolidated_state_clean_replication_batch_029.json",
    "campaign_summary.md",
    "public_language_audit_batch029.json",
    "artifact_packaging_policy.json",
    "artifact_payload_budget.json",
    "artifact_minimality_audit.json",
    "SHA256SUMS.txt",
]

BATCH030_REQUIRED = [
    "batch029_artifact_ingest_summary.json",
    "batch029_artifact_verification.json",
    "batch029_blocker_precision_audit.json",
    "batch030_gate_predicate_correction.json",
    "batch030_harness_payload_availability.json",
    "batch030_harness_payload_integrity_check.json",
    "batch030_provider_command_context_audit.json",
    "batch030_harness_v9_execution_policy.json",
    "batch030_harness_v9_execution_result.json",
    "batch030_harness_v9_pre_repair_verification.json",
    "batch030_target_intent_match_report.json",
    "batch030_decision_time_evidence_firewall.json",
    "issue_derived_repair_feasibility_batch030.json",
    "claim_boundary_batch030.json",
    "proof_obligations_ledger_batch030.json",
    "consolidated_state_clean_replication_batch_030.json",
    "issue_derived_ephemeral_harness_v9.py",
    "campaign_summary.md",
    "public_language_audit_batch030.json",
    "artifact_packaging_policy.json",
    "artifact_payload_budget.json",
    "artifact_minimality_audit.json",
    "SHA256SUMS.txt",
]

BATCH031_REQUIRED = [
    "batch030_artifact_ingest_summary.json",
    "batch030_artifact_verification.json",
    "batch030_blocker_precision_audit.json",
    "batch031_provider_source_commit_predicate_audit.json",
    "batch031_harness_payload_availability.json",
    "batch031_harness_payload_integrity_check.json",
    "batch031_provider_command_context_audit.json",
    "batch031_harness_v9_execution_policy.json",
    "batch031_harness_v9_execution_result.json",
    "batch031_harness_v9_pre_repair_verification.json",
    "batch031_target_intent_match_report.json",
    "batch031_decision_time_evidence_firewall.json",
    "issue_derived_repair_feasibility_batch031.json",
    "claim_boundary_batch031.json",
    "proof_obligations_ledger_batch031.json",
    "consolidated_state_clean_replication_batch_031.json",
    "issue_derived_ephemeral_harness_v9.py",
    "campaign_summary.md",
    "public_language_audit_batch031.json",
    "artifact_packaging_policy.json",
    "artifact_payload_budget.json",
    "artifact_minimality_audit.json",
    "SHA256SUMS.txt",
]

BATCH032_REQUIRED = [
    "batch031_artifact_ingest_summary.json",
    "batch031_artifact_verification.json",
    "batch031_execution_result_classification.json",
    "batch032_safe_directory_precondition_policy.json",
    "batch032_safe_directory_precondition_classification.json",
    "batch032_provider_environment_normalization.json",
    "batch032_provider_command_context_audit.json",
    "batch032_harness_v9_execution_policy.json",
    "batch032_harness_v9_execution_result.json",
    "batch032_harness_v9_pre_repair_verification.json",
    "batch032_harness_design_triage.json",
    "batch032_decision_time_evidence_firewall.json",
    "issue_derived_repair_feasibility_batch032.json",
    "claim_boundary_batch032.json",
    "proof_obligations_ledger_batch032.json",
    "consolidated_state_clean_replication_batch_032.json",
    "campaign_summary.md",
    "public_language_audit_batch032.json",
    "artifact_packaging_policy.json",
    "artifact_payload_budget.json",
    "artifact_minimality_audit.json",
    "SHA256SUMS.txt",
]

BATCH033_REQUIRED = [
    "batch032_artifact_ingest_summary.json",
    "batch032_artifact_verification.json",
    "batch032_target_not_reproduced_summary.json",
    "batch033_issue_seed_retargeting_policy.json",
    "batch033_issue_seed_retargeting_analysis.json",
    "batch033_harness_v10_design_policy.json",
    "batch033_harness_v10_generation_result.json",
    "batch033_decision_time_evidence_firewall.json",
    "issue_derived_repair_feasibility_batch033.json",
    "claim_boundary_batch033.json",
    "proof_obligations_ledger_batch033.json",
    "consolidated_state_clean_replication_batch_033.json",
    "campaign_summary.md",
    "public_language_audit_batch033.json",
    "artifact_packaging_policy.json",
    "artifact_payload_budget.json",
    "artifact_minimality_audit.json",
    "SHA256SUMS.txt",
]

BATCH034_REQUIRED = [
    "batch033_artifact_ingest_summary.json",
    "batch033_artifact_verification.json",
    "batch033_retargeting_design_summary.json",
    "batch034_harness_v10_materialization_policy.json",
    "batch034_harness_v10_materialization_result.json",
    "batch034_relative_git_dir_issue_stimulus_policy.json",
    "batch034_provider_command_context_audit.json",
    "batch034_harness_v10_execution_policy.json",
    "batch034_harness_v10_execution_result.json",
    "batch034_harness_v10_pre_repair_verification.json",
    "batch034_target_intent_match_report.json",
    "batch034_decision_time_evidence_firewall.json",
    "issue_derived_repair_feasibility_batch034.json",
    "claim_boundary_batch034.json",
    "proof_obligations_ledger_batch034.json",
    "consolidated_state_clean_replication_batch_034.json",
    "campaign_summary.md",
    "public_language_audit_batch034.json",
    "artifact_packaging_policy.json",
    "artifact_payload_budget.json",
    "artifact_minimality_audit.json",
    "issue_derived_ephemeral_harness_v10.py",
    "SHA256SUMS.txt",
]

BATCH035_REQUIRED = [
    "batch034_artifact_ingest_summary.json",
    "batch034_artifact_verification.json",
    "batch034_v10_verification_preservation.json",
    "batch035_repair_authorization_gate.json",
    "batch035_candidate_generation_policy.json",
    "batch035_source_inspection_summary.json",
    "batch035_repair_candidate_generation_result.json",
    "batch035_source_only_patch_candidate.diff",
    "batch035_decision_time_evidence_firewall.json",
    "batch035_patch_application_result.json",
    "batch035_patch_scope_audit.json",
    "batch035_post_repair_target_replay.json",
    "batch035_duplicate_clean_replay.json",
    "batch035_issue_derived_repair_validation.json",
    "batch035_controller_audit_closure_check.json",
    "batch035_psa82_permutation_null_diagnostic.json",
    "batch035_structured_fragility_diagnostic.json",
    "issue_derived_repair_feasibility_batch035.json",
    "claim_boundary_batch035.json",
    "proof_obligations_ledger_batch035.json",
    "consolidated_state_clean_replication_batch_035.json",
    "campaign_summary.md",
    "public_language_audit_batch035.json",
    "artifact_packaging_policy.json",
    "artifact_payload_budget.json",
    "artifact_minimality_audit.json",
    "SHA256SUMS.txt",
]

BATCH036_REQUIRED = [
    "batch035_artifact_ingest_summary.json",
    "batch035_artifact_verification.json",
    "batch035_repair_attempt_preservation.json",
    "batch036_post_repair_failure_decomposition.json",
    "batch036_source_inspection_refinement_summary.json",
    "batch036_candidate_v2_generation_policy.json",
    "batch036_repair_candidate_v2_generation_result.json",
    "batch036_source_only_patch_candidate_v2.diff",
    "batch036_decision_time_evidence_firewall.json",
    "batch036_patch_v2_application_result.json",
    "batch036_post_repair_target_replay_v2.json",
    "batch036_duplicate_clean_replay_v2.json",
    "batch036_issue_derived_repair_validation.json",
    "batch036_controller_audit_closure_check.json",
    "batch036_psa82_permutation_null_diagnostic.json",
    "batch036_structured_fragility_diagnostic.json",
    "issue_derived_repair_feasibility_batch036.json",
    "claim_boundary_batch036.json",
    "proof_obligations_ledger_batch036.json",
    "consolidated_state_clean_replication_batch_036.json",
    "campaign_summary.md",
    "public_language_audit_batch036.json",
    "artifact_packaging_policy.json",
    "artifact_payload_budget.json",
    "artifact_minimality_audit.json",
    "SHA256SUMS.txt",
]

BATCH037_REQUIRED = [
    "batch036_artifact_ingest_summary.json",
    "batch036_artifact_verification.json",
    "batch036_candidate_v2_preservation.json",
    "batch037_provider_execution_substage_diagnosis.json",
    "batch037_patch_v2_application_result.json",
    "batch037_patch_v2_scope_audit.json",
    "batch037_post_repair_target_replay_v2.json",
    "batch037_duplicate_clean_replay_v2.json",
    "batch037_issue_derived_repair_validation.json",
    "batch037_controller_audit_closure_check.json",
    "batch037_psa82_permutation_null_diagnostic.json",
    "batch037_structured_fragility_diagnostic.json",
    "issue_derived_repair_feasibility_batch037.json",
    "claim_boundary_batch037.json",
    "proof_obligations_ledger_batch037.json",
    "consolidated_state_clean_replication_batch_037.json",
    "campaign_summary.md",
    "public_language_audit_batch037.json",
    "artifact_payload_budget.json",
    "artifact_minimality_audit.json",
    "SHA256SUMS.txt",
]

BATCH038_GOVERNANCE_FILE = "batch038_reactome_" + "chromo" + "somal_governance_audit.json"
BATCH038_BOUNDARY_FILE = "batch038_" + "bio" + "logical_isomorphism_boundary.json"
BATCH039_GOVERNANCE_CONTINUITY_FILE = "batch039_reactome_" + "chromo" + "somal_governance_continuity_audit.json"
BATCH039_BOUNDARY_FILE = "batch039_" + "bio" + "logical_isomorphism_boundary.json"

BATCH038_REQUIRED = [
    "batch037_artifact_ingest_summary.json",
    "batch037_artifact_verification.json",
    "batch037_official_boundary_preservation.json",
    BATCH038_GOVERNANCE_FILE,
    "batch038_stable_identity_map.json",
    "batch038_blocker_lineage_map.json",
    "batch038_execution_compartment_registry.json",
    "batch038_cofactor_materialization_registry.json",
    "batch038_not_run_reason_registry.json",
    "batch038_failed_repair_branch_record.json",
    "batch038_step_activation_ring.json",
    "batch038_compartmentalized_repair_stage_audit.json",
    "batch038_no_floating_update_audit.json",
    "batch038_command_telemetry_sanitization_audit.json",
    "batch038_expected_output_contract.json",
    "batch038_independent_verifier_summary.json",
    "batch038_psa82_diagnostic_boundary.json",
    BATCH038_BOUNDARY_FILE,
    "batch038_stale_blocker_retirement_registry.json",
    "batch038_patch_serialization_failure_analysis.json",
    "batch038_corrected_patch_generation_policy.json",
    "batch038_corrected_source_only_patch_candidate.diff",
    "batch038_corrected_patch_integrity.json",
    "batch038_corrected_patch_apply_check.json",
    "batch038_corrected_patch_application_result.json",
    "batch038_corrected_patch_scope_audit.json",
    "batch038_post_repair_target_replay.json",
    "batch038_duplicate_clean_replay.json",
    "batch038_issue_derived_repair_validation.json",
    "issue_derived_repair_feasibility_batch038.json",
    "claim_boundary_batch038.json",
    "proof_obligations_ledger_batch038.json",
    "consolidated_state_clean_replication_batch_038.json",
    "campaign_summary.md",
    "public_language_audit_batch038.json",
    "artifact_payload_budget.json",
    "artifact_minimality_audit.json",
    "SHA256SUMS.txt",
]

BATCH039_REQUIRED = [
    "batch038_artifact_ingest_summary.json",
    "batch038_artifact_verification.json",
    "batch038_target_resolution_preservation.json",
    "batch038_governance_artifact_preservation.json",
    BATCH039_GOVERNANCE_CONTINUITY_FILE,
    "batch039_stable_identity_map_update.json",
    "batch039_blocker_lineage_map_update.json",
    "batch039_execution_compartment_registry_update.json",
    "batch039_cofactor_materialization_registry_update.json",
    "batch039_secondary_cofactor_governance_model.json",
    "batch039_general_cofactor_materialization_policy.json",
    "batch039_not_run_reason_registry.json",
    "batch039_failed_branch_or_precondition_record.json",
    "batch039_step_activation_ring.json",
    "batch039_compartmentalized_repair_stage_audit.json",
    "batch039_no_floating_update_audit.json",
    "batch039_command_telemetry_sanitization_audit.json",
    "batch039_expected_output_contract.json",
    "batch039_psa82_diagnostic_boundary.json",
    BATCH039_BOUNDARY_FILE,
    "batch039_declared_linter_cofactor_verification.json",
    "batch039_declared_linter_materialization_policy.json",
    "batch039_declared_linter_materialization_result.json",
    "batch039_corrected_patch_preservation.json",
    "batch039_post_repair_target_replay_under_cofactor_governance.json",
    "batch039_secondary_cofactor_chain_update.json",
    "batch039_duplicate_clean_replay_under_cofactor_governance.json",
    "batch039_issue_derived_repair_validation.json",
    "issue_derived_repair_feasibility_batch039.json",
    "claim_boundary_batch039.json",
    "proof_obligations_ledger_batch039.json",
    "consolidated_state_clean_replication_batch_039.json",
    "campaign_summary.md",
    "public_language_audit_batch039.json",
    "artifact_payload_budget.json",
    "artifact_minimality_audit.json",
    "SHA256SUMS.txt",
]

BATCH040_GOVERNANCE_CONTINUITY_FILE = "batch040_reactome_" + "chromo" + "somal_governance_continuity_audit.json"
BATCH040_BOUNDARY_FILE = "batch040_" + "bio" + "logical_isomorphism_boundary.json"

BATCH040_REQUIRED = [
    "batch039_artifact_ingest_summary.json",
    "batch039_artifact_verification.json",
    "batch039_secondary_cofactor_governance_preservation.json",
    "batch039_target_resolution_preservation.json",
    BATCH040_GOVERNANCE_CONTINUITY_FILE,
    "batch040_stable_identity_map_update.json",
    "batch040_blocker_lineage_map_update.json",
    "batch040_execution_compartment_registry_update.json",
    "batch040_cofactor_materialization_registry_update.json",
    "batch040_secondary_cofactor_governance_model_update.json",
    "batch040_not_run_reason_registry.json",
    "batch040_failed_branch_or_precondition_record.json",
    "batch040_step_activation_ring.json",
    "batch040_compartmentalized_repair_stage_audit.json",
    "batch040_no_floating_update_audit.json",
    "batch040_command_telemetry_sanitization_audit.json",
    "batch040_expected_output_contract.json",
    "batch040_psa82_diagnostic_boundary.json",
    BATCH040_BOUNDARY_FILE,
    "batch040_reviewed_cofactor_lock_policy.json",
    "batch040_pylint_lock_discovery_policy.json",
    "batch040_pylint_provider_lock_discovery_result.json",
    "batch040_pylint_provider_lock.json",
    "batch040_pylint_lock_review.json",
    "batch040_provider_only_cofactor_materialization_policy.json",
    "batch040_provider_only_cofactor_materialization_result.json",
    "batch040_pylint_executable_verification.json",
    "batch040_corrected_patch_preservation.json",
    "batch040_post_repair_target_replay_with_reviewed_cofactor_lock.json",
    "batch040_secondary_cofactor_chain_update.json",
    "batch040_duplicate_clean_replay_with_reviewed_cofactor_lock.json",
    "batch040_issue_derived_repair_validation.json",
    "issue_derived_repair_feasibility_batch040.json",
    "claim_boundary_batch040.json",
    "proof_obligations_ledger_batch040.json",
    "consolidated_state_clean_replication_batch_040.json",
    "campaign_summary.md",
    "public_language_audit_batch040.json",
    "artifact_payload_budget.json",
    "artifact_minimality_audit.json",
    "SHA256SUMS.txt",
]

BATCH041_GOVERNANCE_CONTINUITY_FILE = "batch041_reactome_" + "chromo" + "somal_governance_continuity_audit.json"

BATCH041_REQUIRED = [
    "batch040_artifact_ingest_summary.json",
    "batch040_artifact_verification.json",
    "batch040_artifact_internal_status_preservation.json",
    "batch040_local_vs_artifact_blocker_reconciliation.json",
    "batch040_target_resolution_preservation.json",
    "batch040_secondary_cofactor_governance_preservation.json",
    BATCH041_GOVERNANCE_CONTINUITY_FILE,
    "batch041_stable_identity_integrity_audit.json",
    "batch041_stable_identity_map_update.json",
    "batch041_proof_ledger_referrer_audit.json",
    "batch041_cofactor_lock_provenance_audit.json",
    "batch041_dependency_drift_audit.json",
    "batch041_secondary_cofactor_chain_budget.json",
    "batch041_replay_classification_matrix.json",
    "batch041_included_excluded_diagnostics_registry.json",
    "batch041_validation_activation_audit.json",
    "batch041_transport_export_equivalence_audit.json",
    "batch041_evidence_origin_classification.json",
    "batch041_lock_completion_policy.json",
    "batch041_pylint_lock_completion_result.json",
    "batch041_pylint_provider_lock_v2.json",
    "batch041_pylint_lock_v2_review.json",
    "batch041_provider_only_cofactor_materialization_result.json",
    "batch041_pylint_executable_verification.json",
    "batch041_corrected_patch_preservation.json",
    "batch041_post_repair_target_replay_with_lock_v2.json",
    "batch041_duplicate_clean_replay_with_lock_v2.json",
    "batch041_issue_derived_repair_validation.json",
    "issue_derived_repair_feasibility_batch041.json",
    "claim_boundary_batch041.json",
    "proof_obligations_ledger_batch041.json",
    "consolidated_state_clean_replication_batch_041.json",
    "campaign_summary.md",
    "public_language_audit_batch041.json",
    "batch041_not_run_reason_registry.json",
    "artifact_payload_budget.json",
    "artifact_minimality_audit.json",
    "SHA256SUMS.txt",
]

BATCH042_GOVERNANCE_CONTINUITY_FILE = "batch042_reactome_" + "chromo" + "somal_governance_continuity_audit.json"
BATCH042_BOUNDARY_FILE = "batch042_" + "bio" + "logical_isomorphism_boundary.json"

BATCH042_REQUIRED = [
    "batch041_artifact_ingest_summary.json",
    "batch041_artifact_verification.json",
    "batch041_repair_validation_preservation.json",
    "batch041_replay_and_duplicate_replay_preservation.json",
    "batch042_issue_derived_episode_count_gate.json",
    BATCH042_GOVERNANCE_CONTINUITY_FILE,
    "batch042_stable_identity_lineage_lock.json",
    "batch042_proof_ledger_validation_lock.json",
    "batch042_replay_classification_preservation.json",
    "batch042_included_excluded_diagnostics_registry.json",
    "batch042_psa82_diagnostic_boundary.json",
    BATCH042_BOUNDARY_FILE,
    "batch042_stale_blocker_retirement_registry.json",
    "issue_derived_repair_feasibility_batch042.json",
    "claim_boundary_batch042.json",
    "proof_obligations_ledger_batch042.json",
    "consolidated_state_clean_replication_batch_042.json",
    "campaign_summary.md",
    "public_language_audit_batch042.json",
    "artifact_payload_budget.json",
    "artifact_minimality_audit.json",
    "SHA256SUMS.txt",
]

BATCH043_PROTOCOLIZATION_FILE = "batch043_reactome_" + "chromo" + "somal_protocolization_audit.json"
BATCH043_REQUIRED = [
    "batch042_artifact_ingest_summary.json",
    "batch042_artifact_verification.json",
    "batch042_count_lock_preservation.json",
    "batch042_claim_boundary_preservation.json",
    "batch043_issue_derived_repair_episode_001_canonical_record.json",
    BATCH043_PROTOCOLIZATION_FILE,
    "batch043_isomorphic_coverage_matrix.json",
    "batch043_issue_derived_repair_episode_schema.json",
    "batch043_reusable_protocol_guardrail_update.json",
    "batch043_stale_blocker_and_lane_closure_audit.json",
    "issue_derived_repair_feasibility_batch043.json",
    "claim_boundary_batch043.json",
    "proof_obligations_ledger_batch043.json",
    "consolidated_state_clean_replication_batch_043.json",
    "campaign_summary.md",
    "public_language_audit_batch043.json",
    "artifact_payload_budget.json",
    "artifact_minimality_audit.json",
    "SHA256SUMS.txt",
]

BATCH044_REQUIRED = [
    "batch043_artifact_ingest_summary.json",
    "batch043_artifact_verification.json",
    "batch043_episode_canonicalization_preservation.json",
    "batch043_claim_boundary_preservation.json",
    "batch044_standing_guardrail_enforcement_registry.json",
    "batch044_isomorphic_coverage_enforcement_audit.json",
    "batch044_future_issue_derived_lane_eligibility_schema.json",
    "batch044_next_issue_seed_selection_gate.json",
    "batch044_protocol_version_boundary.json",
    "issue_derived_repair_feasibility_batch044.json",
    "claim_boundary_batch044.json",
    "proof_obligations_ledger_batch044.json",
    "consolidated_state_clean_replication_batch_044.json",
    "campaign_summary.md",
    "public_language_audit_batch044.json",
    "artifact_payload_budget.json",
    "artifact_minimality_audit.json",
    "SHA256SUMS.txt",
]

BATCH045_REQUIRED = [
    "batch044_artifact_ingest_summary.json",
    "batch044_artifact_verification.json",
    "batch044_guardrail_enforcement_preservation.json",
    "batch044_seed_selection_authorization_preservation.json",
    "batch044_claim_boundary_preservation.json",
    "batch045_protocol_candidate_v2_14_review.json",
    "batch045_reactome_" + "chromo" + "somal_guardrail_regression_audit.json",
    "batch045_scoped_next_issue_seed_discovery_policy.json",
    "batch045_next_issue_seed_candidate_discovery_gate.json",
    "batch045_issue_seed_candidate_inventory.json",
    "issue_derived_repair_feasibility_batch045.json",
    "claim_boundary_batch045.json",
    "proof_obligations_ledger_batch045.json",
    "consolidated_state_clean_replication_batch_045.json",
    "campaign_summary.md",
    "public_language_audit_batch045.json",
    "artifact_payload_budget.json",
    "artifact_minimality_audit.json",
    "SHA256SUMS.txt",
]

BATCH046_REQUIRED = [
    "batch045_artifact_ingest_summary.json",
    "batch045_artifact_verification.json",
    "batch045_protocol_candidate_preservation.json",
    "batch045_seed_inventory_preservation.json",
    "batch045_claim_boundary_preservation.json",
    "batch046_protocol_v2_14_promotion_decision.json",
    "batch046_brot_bulb_isomorphism_boundary_lock.json",
    "batch046_torus_brot_single_system_environment_map.json",
    "batch046_tot_brot_coupled_family_blocker_graph.json",
    "batch046_tot_bulb_environment_probe_design.json",
    "batch046_environment_bug_locator_eligibility_gate.json",
    "batch046_bounded_environment_probe_inventory.json",
    "batch046_seed_discovery_expansion_policy.json",
    "issue_derived_repair_feasibility_batch046.json",
    "claim_boundary_batch046.json",
    "proof_obligations_ledger_batch046.json",
    "consolidated_state_clean_replication_batch_046.json",
    "campaign_summary.md",
    "public_language_audit_batch046.json",
    "artifact_payload_budget.json",
    "artifact_minimality_audit.json",
    "SHA256SUMS.txt",
]

BATCH047_REQUIRED = [
    "batch046_artifact_ingest_summary.json",
    "batch046_artifact_verification.json",
    "batch046_brot_bulb_locator_preservation.json",
    "batch046_claim_boundary_preservation.json",
    "batch047_source_registry_for_bounded_probe_execution.json",
    "batch047_tot_bulb_probe_execution_policy.json",
    "batch047_tot_bulb_probe_execution_results.json",
    "batch047_torus_brot_probe_interpretation.json",
    "batch047_tot_brot_coupled_probe_interpretation.json",
    "batch047_issue_seed_candidate_inventory.json",
    "batch047_protocol_v2_14_boundary_preservation.json",
    "issue_derived_repair_feasibility_batch047.json",
    "claim_boundary_batch047.json",
    "proof_obligations_ledger_batch047.json",
    "consolidated_state_clean_replication_batch_047.json",
    "campaign_summary.md",
    "public_language_audit_batch047.json",
    "artifact_payload_budget.json",
    "artifact_minimality_audit.json",
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


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


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
    batch024_catalog_extensions = {
        "provider_workspace_bridge",
        "provider_input_bundle",
        "provider_output_bundle",
        "provider_source_checkout",
        "provider_source_materialization",
    }
    allowed_capabilities = required_capabilities | batch016_catalog_extensions | batch018_catalog_extensions | batch019_catalog_extensions | batch020_catalog_extensions | batch021_catalog_extensions | batch022_catalog_extensions | batch023_catalog_extensions | batch024_catalog_extensions
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
    if catalog.get("catalog_version") not in {"batch016", "batch017", "batch018", "batch019", "batch020", "batch021", "batch022", "batch023", "batch024"}:
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
    if catalog.get("catalog_version") not in {"batch017", "batch018", "batch019", "batch020", "batch021", "batch022", "batch023", "batch024"}:
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
    if catalog.get("catalog_version") not in {"batch018", "batch019", "batch020", "batch021", "batch022", "batch023", "batch024"}:
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
    if catalog.get("catalog_version") not in {"batch019", "batch020", "batch021", "batch022", "batch023", "batch024"}:
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
    if catalog.get("catalog_version") not in {"batch020", "batch021", "batch022", "batch023", "batch024"}:
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
    if catalog.get("catalog_version") not in {"batch021", "batch022", "batch023", "batch024"}:
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
    if catalog.get("catalog_version") not in {"batch022", "batch023", "batch024"}:
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
    if catalog.get("catalog_version") not in {"batch023", "batch024"}:
        errors.append("Batch023 capability catalog version missing")
    return errors


def audit_batch024_records() -> list[str]:
    errors: list[str] = []
    for name in BATCH024_REQUIRED:
        if not (BATCH024_DIR / name).is_file():
            errors.append(f"batch024 missing required file {name}")
    if errors:
        return errors
    manifest = verify_manifest(BATCH024_DIR)
    if manifest.get("status") != "PASS":
        errors.append(f"batch024 manifest failed: {manifest}")

    phase_a = read_json(POST_DIR / "batch023_bounded_docker_provider_artifact_verification.json")
    ingest = read_json(POST_DIR / "batch023_bounded_docker_provider_ingest_summary.json")
    recommendation = read_json(POST_DIR / "batch024_provider_workspace_bridge_recommendation.json")
    batch023 = read_json(BATCH023_DIR / "consolidated_state_clean_replication_batch_023.json")
    state = read_json(BATCH024_DIR / "consolidated_state_clean_replication_batch_024.json")
    preservation = read_json(BATCH024_DIR / "batch023_boundary_preservation.json")
    preflight_preservation = read_json(BATCH024_DIR / "provider_preflight_preservation.json")
    install_preservation = read_json(BATCH024_DIR / "provider_install_preservation.json")
    claim = read_json(BATCH024_DIR / "claim_boundary_batch024.json")
    bridge_policy = read_json(BATCH024_DIR / "provider_workspace_bridge_policy.json")
    input_bundle = read_json(BATCH024_DIR / "provider_input_bundle_manifest.json")
    output_bundle = read_json(BATCH024_DIR / "provider_output_bundle_manifest.json")
    transport = read_json(BATCH024_DIR / "provider_workspace_transport_audit.json")
    cleanup = read_json(BATCH024_DIR / "provider_workspace_cleanup_audit.json")
    bridge_status = read_json(BATCH024_DIR / "provider_workspace_bridge_status.json")
    source_policy = read_json(BATCH024_DIR / "provider_source_checkout_policy.json")
    source_checkout = read_json(BATCH024_DIR / "provider_source_checkout_audit.json")
    source_manifest = read_json(BATCH024_DIR / "provider_source_tree_manifest.json")
    source_commit = read_json(BATCH024_DIR / "provider_source_commit_verification.json")
    materialization_policy = read_json(BATCH024_DIR / "manual_lock_environment_materialization_policy.json")
    materialization = read_json(BATCH024_DIR / "manual_lock_environment_materialization_log.json")
    environment_hash = read_json(BATCH024_DIR / "manual_lock_environment_hash.json")
    freeze = read_json(BATCH024_DIR / "provider_installed_package_freeze.json")
    freeze_hashes = read_json(BATCH024_DIR / "provider_installed_package_hashes.json")
    workspace = read_json(BATCH024_DIR / "workspace_purity_report.json")
    locks = read_json(BATCH024_DIR / "acquisition_lock_stack_status.json")
    variant_policy = read_json(BATCH024_DIR / "issue112_command_variant_policy.json")
    variants = read_json(BATCH024_DIR / "issue112_provider_variant_results.json")
    target_signature = read_json(BATCH024_DIR / "darker_issue112_target_intent_signature_retry.json")
    target_retry = read_json(BATCH024_DIR / "target_intent_alignment_retry_audit.json")
    harness_policy = read_json(BATCH024_DIR / "issue_derived_harness_v9_policy.json")
    harness_context = read_json(BATCH024_DIR / "issue_derived_harness_v9_context_manifest.json")
    harness = read_json(BATCH024_DIR / "issue_derived_harness_v9_verification_result.json")
    curvature = read_json(BATCH024_DIR / "curvature_claim_boundary.json")
    geometry = read_json(BATCH024_DIR / "active_search_geometry_execution_trace.json")
    repair = read_json(BATCH024_DIR / "repair_only_fallback_status.json")
    feasibility = read_json(BATCH024_DIR / "issue_derived_repair_feasibility_status.json")
    diagnostic = read_json(BATCH024_DIR / "issue_derived_matched_null_diagnostic_status.json")
    fragility_policy = read_json(BATCH024_DIR / "structured_fragility_audit_run_policy.json")
    fragility = read_json(BATCH024_DIR / "structured_fragility_audit_results.json")
    nulls = read_json(BATCH024_DIR / "permutation_null_audit_results.json")
    sensitivity = read_json(BATCH024_DIR / "patch_structure_sensitivity_results.json")
    decision = read_json(BATCH024_DIR / "darker_issue112_candidate_viability_decision.json")
    next_action = read_json(BATCH024_DIR / "provider_workspace_bridge_next_action.json")
    ledger = read_json(BATCH024_DIR / "proof_obligations_ledger.json")
    rollback = read_json(BATCH024_DIR / "rollback_block_ledger_audit.json")
    safe_stop = read_json(BATCH024_DIR / "compute_budget_safe_stop_batch024.json")
    taxonomy = read_json(BATCH024_DIR / "failure_taxonomy_batch024.json")
    activation_order = read_json(BATCH024_DIR / "activation_order_guardrail_status.json")
    ghost = read_json(BATCH024_DIR / "rollback_ghost_state_guardrail_status.json")
    dependency = read_json(BATCH024_DIR / "dependency_overlap_grouping_status.json")
    consistency = read_json(BATCH024_DIR / "consistency_reassertion_status.json")
    language = read_json(BATCH024_DIR / "public_language_audit_batch024.json")
    minimality = read_json(BATCH024_DIR / "artifact_minimality_audit.json")
    budget = read_json(BATCH024_DIR / "artifact_payload_budget.json")
    lineage = read_json(BATCH024_DIR / "artifact_lineage_index.json")
    carry = read_json(BATCH024_DIR / "evidence_carry_forward_manifest.json")
    catalog = read_json(Path("configs/controllergate_capability_catalog.json"))

    if phase_a.get("status") != "PASS" or phase_a.get("actual_sha256") != "d058f32fba6fb8dec669f7ab906eeec042d175a3f6ed81e52cd833354de4b375":
        errors.append("Batch023 official artifact verification invalid")
    if phase_a.get("actual_entry_count") != 188 or phase_a.get("manifest_failures") != 0 or phase_a.get("pycache_pyc_entry_count") != 0:
        errors.append("Batch023 official artifact hygiene invalid")
    if ingest.get("status") != "PASS" or ingest.get("archives_ingested") is not False:
        errors.append("Batch023 ingest summary invalid")
    if recommendation.get("recommended_next_batch") != "clean_replication_batch_024":
        errors.append("Batch024 recommendation missing")
    if batch023.get("status") != "PASS_WITH_BATCH023_MATERIALIZATION_BLOCKED" or batch023.get("exact_blocker") != "manual_lock_environment_materialization_failed":
        errors.append("Batch023 official boundary not preserved")
    if preservation.get("status") != "PASS" or preservation.get("batch023_exact_blocker") != "manual_lock_environment_materialization_failed":
        errors.append("Batch024 boundary preservation invalid")
    if preflight_preservation.get("batch023_provider_preflight_status") != "PASS" or not str(preflight_preservation.get("batch023_actual_provider_python_version", "")).startswith("3.7."):
        errors.append("Batch024 provider preflight preservation invalid")
    if install_preservation.get("batch023_manual_dependency_lock_provider_install_status") != "PASS":
        errors.append("Batch024 provider install preservation invalid")
    if claim.get("native_repair_episode_count") != 4 or claim.get("issue_derived_repair_episode_count") != 0:
        errors.append("Batch024 repair counts changed")
    if claim.get("full_scoring") != "NOT_RUN/disallowed" or claim.get("memory_lift") != "not_demonstrated":
        errors.append("Batch024 scoring or memory boundary changed")
    if claim.get("self_maintaining_software") != "false/not_demonstrated" or claim.get("hallucination_elimination") != "false/not_claimed" or claim.get("absolute_uncrashability") != "false/not_claimed":
        errors.append("Batch024 overclaim boundary changed")
    if bridge_policy.get("write_credentials_allowed") is not False or bridge_policy.get("secrets_allowed") is not False:
        errors.append("Batch024 provider bridge policy exposes credentials or secrets")
    if input_bundle.get("status") != "PASS" or input_bundle.get("forbidden_keys_present"):
        errors.append("provider_input_bundle_invalid")
    if input_bundle.get("write_credentials_included") is not False or input_bundle.get("secrets_included") is not False:
        errors.append("provider_input_contains_forbidden_data")
    if output_bundle.get("status") != "PASS" or output_bundle.get("forbidden_keys_present"):
        errors.append("provider_output_bundle_invalid")
    if output_bundle.get("contains_credentials") is not False or output_bundle.get("contains_secrets") is not False or output_bundle.get("contains_full_external_checkout") is not False:
        errors.append("provider_output_contains_forbidden_data")
    if transport.get("workspace_outside_repo") is not True or transport.get("write_credentials_mounted") is not False or transport.get("secrets_mounted") is not False:
        errors.append("provider_workspace_transport_unverified")
    if cleanup.get("status") != "PASS" or cleanup.get("removed") is not True:
        errors.append("provider_workspace_cleanup_failed")
    if bridge_status.get("status") == "PASS":
        if source_checkout.get("status") not in {"PASS", "BLOCK"}:
            errors.append("provider bridge passed without source checkout attempt")
    if source_policy.get("source_commit_sha") != "a2d13656adfaa010fb6c7339087f3347ad2b815a" or source_policy.get("full_source_tree_copy_to_repo_allowed") is not False:
        errors.append("Batch024 source checkout policy invalid")
    if source_checkout.get("status") == "PASS":
        if source_checkout.get("head_sha") != "a2d13656adfaa010fb6c7339087f3347ad2b815a" or source_checkout.get("git_object_type") != "commit":
            errors.append("provider_source_commit_mismatch")
        if source_manifest.get("status") != "PASS" or source_manifest.get("full_source_tree_copied_to_repo") is not False:
            errors.append("provider_source_tree_manifest_failed")
        if source_commit.get("commit_verified") is not True:
            errors.append("provider_source_commit_unresolved")
    if materialization_policy.get("undeclared_dependency_install_allowed") is not False or materialization_policy.get("source_mutation_allowed") is not False:
        errors.append("Batch024 materialization policy invalid")
    if materialization.get("status") == "PASS" and source_checkout.get("status") != "PASS":
        errors.append("source install passed before source checkout")
    if materialization.get("status") == "PASS" and freeze.get("status") != "PASS":
        errors.append("source materialization passed without package freeze")
    if freeze.get("status") == "PASS" and not freeze_hashes.get("freeze_sha256"):
        errors.append("freeze hash missing")
    if workspace.get("provider_workspace_committed") is not False or workspace.get("source_checkout_leaked_to_repo") is not False:
        errors.append("provider_source_checkout_leaked_to_repo")
    if target_retry.get("target_intent_alignment") is True and materialization.get("status") != "PASS":
        errors.append("target-intent retry ran before materialization")
    if target_signature.get("negative_precondition_indicator_seen") is True and target_retry.get("target_intent_alignment") is True:
        errors.append("target-intent accepted precondition failure")
    if harness_policy.get("future_fixed_gold_pr_evidence_forbidden") is not True:
        errors.append("Batch024 harness v9 policy invalid")
    if harness.get("harness_generated") is True and target_retry.get("target_intent_alignment") is not True:
        errors.append("Batch024 harness generated before target-intent alignment")
    if harness_context.get("status") != "NOT_RUN" and target_retry.get("target_intent_alignment") is not True:
        errors.append("Batch024 harness context ran before target-intent alignment")
    if repair.get("repair_only_fallback_attempted") is True and target_retry.get("target_intent_alignment") is not True:
        errors.append("repair_attempted_without_target_intent_alignment")
    if feasibility.get("issue_derived_repair_feasibility") is True and target_retry.get("target_intent_alignment") is not True:
        errors.append("Batch024 issue-derived feasibility overclaim")
    if diagnostic.get("native_memory_separation_claim_allowed") is not False:
        errors.append("memory_claim_from_issue_derived_evidence")
    if fragility_policy.get("diagnostic_only") is not True or fragility.get("repair_evidence") is not False or nulls.get("repair_evidence") is not False or sensitivity.get("repair_evidence") is not False:
        errors.append("structured_fragility_used_as_repair_evidence")
    if geometry.get("empirical_evidence_replaced") is not False or curvature.get("curvature_can_replace_evidence") is not False:
        errors.append("geometry_replaced_empirical_evidence_gate")
    if decision.get("decision") == "target_intent_alignment_reached" and target_retry.get("target_intent_alignment") is not True:
        errors.append("candidate decision overreached target-intent")
    if not next_action.get("next_allowed_action"):
        errors.append("Batch024 next action missing")
    if rollback.get("status") != "PASS" or rollback.get("rollback_block_count", 0) < 1:
        errors.append("Batch024 rollback block missing")
    if not any(isinstance(item, dict) and item.get("entry_type") == "ROLLBACK_BLOCK" for item in ledger.get("entries", [])):
        errors.append("Batch024 proof ledger rollback block missing")
    if safe_stop.get("status") != "PASS" or safe_stop.get("downstream_repair_ran") is not False:
        errors.append("Batch024 safe-stop invalid")
    allowed_blockers = {
        "provider_workspace_bridge_missing",
        "provider_input_bundle_invalid",
        "provider_output_bundle_invalid",
        "provider_workspace_transport_unverified",
        "provider_workspace_cleanup_failed",
        "docker_runtime_provider_unavailable",
        "provider_source_checkout_failed",
        "provider_source_commit_unresolved",
        "provider_source_commit_mismatch",
        "provider_source_tree_manifest_failed",
        "manual_lock_environment_materialization_failed",
        "source_install_failed",
        "source_install_required_undeclared_dependency",
        "target_intent_alignment_not_reached",
        "target_intent_precondition_failure",
        "issue_derived_harness_v9_verification_failed",
    }
    if taxonomy.get("taxonomy_class") not in allowed_blockers:
        errors.append("Batch024 failure taxonomy invalid")
    if activation_order.get("order_preserved") is not True or activation_order.get("repair_before_target_intent") is not False:
        errors.append("activation_order_violation")
    if ghost.get("downstream_state_contaminated") is not False:
        errors.append("rollback_ghost_state_detected")
    if dependency.get("may_override_provider_gate") is not False or consistency.get("claim_boundary_reasserted") is not True:
        errors.append("Batch024 dependency/consistency guardrail invalid")
    if not str(state.get("status", "")).startswith("PASS_WITH_BATCH024_"):
        errors.append("Batch024 state mismatch")
    if state.get("full_scoring") != "NOT_RUN/disallowed" or state.get("self_maintaining_software") != "false/not_demonstrated":
        errors.append("Batch024 claim boundary mismatch")
    if state.get("native_repair_episode_count") != 4 or state.get("issue_derived_repair_episode_count") != 0:
        errors.append("Batch024 state repair counts changed")
    if language.get("status") != "PASS":
        errors.append("Batch024 public language audit failed")
    if minimality.get("recursive_prior_batch_packaging_detected") is not False:
        errors.append("recursive_prior_batch_packaging_detected")
    if budget.get("status") != "PASS":
        errors.append("primary_artifact_budget_exceeded")
    if lineage.get("current_batch") != "clean_replication_batch_024" or carry.get("carried_prior_evidence_by_reference") is not True:
        errors.append("Batch024 lineage/carry-forward invalid")
    if catalog.get("catalog_version") != "batch024":
        errors.append("Batch024 capability catalog version missing")
    if not variant_policy.get("allowed_variants"):
        errors.append("Batch024 command variant policy missing")
    if variants.get("status") == "PASS" and target_retry.get("target_intent_alignment") is not True:
        errors.append("Batch024 variant result passed without target alignment")
    if environment_hash.get("status") == "PASS" and not environment_hash.get("environment_hash"):
        errors.append("Batch024 environment hash missing")
    return errors


def audit_batch025_records() -> list[str]:
    errors: list[str] = []
    for name in BATCH025_REQUIRED:
        if not (BATCH025_DIR / name).is_file():
            errors.append(f"batch025 missing required file {name}")
    if errors:
        return errors
    manifest = verify_manifest(BATCH025_DIR)
    if manifest.get("status") != "PASS":
        errors.append(f"batch025 manifest failed: {manifest}")

    batch024_state = read_json(BATCH024_DIR / "consolidated_state_clean_replication_batch_024.json")
    batch024_source_manifest = read_json(BATCH024_DIR / "provider_source_tree_manifest.json")
    post_ingest = read_json(POST_DIR / "batch024_artifact_ingest_summary.json")
    post_verification = read_json(POST_DIR / "batch024_artifact_verification.json")
    post_correction = read_json(POST_DIR / "batch024_status_correction.json")
    ingest = read_json(BATCH025_DIR / "batch024_artifact_ingest_summary.json")
    verification = read_json(BATCH025_DIR / "batch024_artifact_verification.json")
    correction = read_json(BATCH025_DIR / "batch024_status_correction.json")
    state = read_json(BATCH025_DIR / "consolidated_state_clean_replication_batch_025.json")
    context = read_json(BATCH025_DIR / "provider_command_context_diagnosis.json")
    git_context = read_json(BATCH025_DIR / "provider_git_context_audit.json")
    variant_policy = read_json(BATCH025_DIR / "provider_target_intent_variant_policy.json")
    variants = read_json(BATCH025_DIR / "provider_target_intent_variant_results.json")
    target = read_json(BATCH025_DIR / "target_intent_alignment_batch025.json")
    harness_gate = read_json(BATCH025_DIR / "issue_derived_harness_v9_generation_gate.json")
    feasibility = read_json(BATCH025_DIR / "issue_derived_repair_feasibility_batch025.json")
    claim = read_json(BATCH025_DIR / "claim_boundary_batch025.json")
    ledger = read_json(BATCH025_DIR / "proof_obligations_ledger_batch025.json")
    language = read_json(BATCH025_DIR / "public_language_audit_batch025.json")
    minimality = read_json(BATCH025_DIR / "artifact_minimality_audit.json")
    budget = read_json(BATCH025_DIR / "artifact_payload_budget.json")
    batch025_post_verification = read_json(POST_DIR / "batch025_artifact_verification.json")
    batch025_post_ingest = read_json(POST_DIR / "batch025_artifact_ingest_summary.json")
    batch025_post_correction = read_json(POST_DIR / "batch025_status_correction.json")

    if post_verification.get("status") != "PASS" or verification.get("status") != "PASS":
        errors.append("Batch024 artifact verification not PASS")
    if post_verification.get("actual_sha256") != "f3dc35a47ceb0fa7d313038110f800dfaa5849d8ba614001070aa031ba3ea1ad":
        errors.append("Batch024 artifact SHA mismatch")
    if post_verification.get("zip_entry_count") != 181 or post_verification.get("unsafe_path_count") != 0 or post_verification.get("duplicate_path_count") != 0:
        errors.append("Batch024 artifact ZIP hygiene mismatch")
    if post_ingest.get("status") != "PASS" or ingest.get("status") != "PASS" or ingest.get("archives_ingested") is not False:
        errors.append("Batch024 artifact ingest summary invalid")
    if correction.get("corrected_batch024_status") != "PASS_WITH_BATCH024_TARGET_INTENT_BLOCKED":
        errors.append("Batch024 status correction missing")
    if correction.get("corrected_exact_blocker") != "target_intent_alignment_not_reached":
        errors.append("Batch024 exact blocker correction missing")
    if batch024_state.get("status") == "PASS_WITH_BATCH024_PROVIDER_BRIDGE_BLOCKED":
        errors.append("Batch024 still reported as provider-bridge-blocked")
    if batch024_state.get("exact_blocker") == "docker_runtime_provider_unavailable":
        errors.append("Batch024 stale Docker blocker carried forward")
    if batch024_state.get("status") != "PASS_WITH_BATCH024_TARGET_INTENT_BLOCKED" or batch024_state.get("exact_blocker") != "target_intent_alignment_not_reached":
        errors.append("Batch024 official target-intent boundary not preserved")
    source_paths = [item.get("path") for item in batch024_source_manifest.get("records", []) if isinstance(item, dict)]
    if "src/darker/main.py" in source_paths or "src/darker/main.py" in batch024_source_manifest.get("missing_relevant_paths", []):
        errors.append("src/darker/main.py is incorrectly required")

    target_pass = target.get("target_intent_alignment") is True
    if target_pass:
        if context.get("status") != "PASS":
            errors.append("Target-Intent Alignment claimed without provider command context PASS")
        if git_context.get("status") != "PASS":
            errors.append("Target-Intent Alignment claimed without provider Git context PASS")
        for field in ["provider_execution_cwd", "provider_source_root"]:
            if not context.get(field):
                errors.append(f"Target-Intent Alignment missing {field}")
        if git_context.get("git_dir_exists") is not True or git_context.get("head_matches_expected") is not True:
            errors.append("Target-Intent Alignment missing .git or HEAD verification")
        if not variants.get("variants"):
            errors.append("Target-Intent Alignment claimed without variant results")
    if target.get("status") == "PASS" and not target_pass:
        errors.append("Target-Intent Alignment status/pass mismatch")
    if variant_policy.get("bounded_command_context_variants_only") is not True:
        errors.append("Batch025 variant policy is not bounded")
    if harness_gate.get("harness_v9_generated") is True and not target_pass:
        errors.append("harness v9 generated before Target-Intent Alignment")
    if feasibility.get("issue_derived_repair_feasibility") is True and harness_gate.get("harness_v9_generated") is not True:
        errors.append("issue-derived repair feasibility claimed before harness verification")
    if claim.get("repair_ran") is not False or claim.get("matched_null_ran") is not False:
        errors.append("Batch025 repair or matched-null ran unexpectedly")
    if claim.get("psa82_permutation_null_ran") is not False or claim.get("structured_fragility_diagnostic_ran") is not False:
        errors.append("Batch025 downstream diagnostic ran without patch candidate")
    if claim.get("native_repair_episode_count") != 4 or claim.get("issue_derived_repair_episode_count") != 0:
        errors.append("Batch025 repair counts changed")
    if claim.get("full_scoring") != "NOT_RUN/disallowed" or claim.get("memory_lift") != "not_demonstrated":
        errors.append("Batch025 scoring or memory boundary changed")
    if claim.get("self_maintaining_software") != "false/not_demonstrated":
        errors.append("Batch025 self-maintaining claim changed")
    if state.get("current_protocol") != "v2.13":
        errors.append("Batch025 current protocol changed")
    if not str(state.get("status", "")).startswith("PASS_WITH_BATCH025_"):
        errors.append("Batch025 state mismatch")
    if batch025_post_verification.get("status") != "PASS":
        errors.append("Batch025 artifact verification missing or not PASS")
    if batch025_post_verification.get("artifact_sha256") != "c3830498c52188c01ec341d5c97fcd9c2df0cfbe042ef55baf01ba61b9b7b1eb":
        errors.append("Batch025 artifact SHA mismatch")
    if batch025_post_verification.get("artifact_size_bytes") != 132523 or batch025_post_verification.get("zip_entry_count") != 134:
        errors.append("Batch025 artifact size or entry count mismatch")
    if batch025_post_verification.get("unsafe_path_count") != 0 or batch025_post_verification.get("duplicate_path_count") != 0:
        errors.append("Batch025 artifact ZIP hygiene mismatch")
    if batch025_post_verification.get("manifest_failure_count") != 0:
        errors.append("Batch025 artifact manifest failures detected")
    if batch025_post_ingest.get("status") != "PASS":
        errors.append("Batch025 artifact ingest summary missing or not PASS")
    if batch025_post_correction.get("status") != "PASS":
        errors.append("Batch025 status correction missing or not PASS")
    if state.get("status") == "PASS_WITH_BATCH025_PROVIDER_CONTEXT_BLOCKED":
        errors.append("Batch025 still reported as provider-context-blocked after official ingest")
    if state.get("exact_blocker") == "docker_runtime_provider_unavailable":
        errors.append("Batch025 stale Docker blocker carried forward after official ingest")
    if state.get("status") != "PASS_WITH_BATCH025_TARGET_INTENT_ALIGNED":
        errors.append("Batch025 official target-intent-aligned status not preserved")
    if state.get("exact_blocker") != "issue_derived_harness_v9_generation_pending_after_target_intent_alignment":
        errors.append("Batch025 official harness-v9 pending blocker not preserved")
    if state.get("target_intent_alignment_status") != "PASS":
        errors.append("Batch025 Target-Intent Alignment regressed")
    if ledger.get("status") != "PASS" or ledger.get("repair_or_matched_null_before_target_intent") is not False:
        errors.append("Batch025 proof ledger invalid")
    if language.get("status") != "PASS":
        errors.append("Batch025 public language audit failed")
    if minimality.get("recursive_prior_batch_packaging_detected") is not False:
        errors.append("Batch025 recursive prior batch packaging detected")
    if budget.get("status") != "PASS":
        errors.append("Batch025 artifact budget failed")
    return errors


def audit_batch026_records() -> list[str]:
    errors: list[str] = []
    for name in BATCH026_REQUIRED:
        if not (BATCH026_DIR / name).is_file():
            errors.append(f"batch026 missing required file {name}")
    if errors:
        return errors
    manifest = verify_manifest(BATCH026_DIR)
    if manifest.get("status") != "PASS":
        errors.append(f"batch026 manifest failed: {manifest}")

    batch025_state = read_json(BATCH025_DIR / "consolidated_state_clean_replication_batch_025.json")
    state = read_json(BATCH026_DIR / "consolidated_state_clean_replication_batch_026.json")
    ingest = read_json(BATCH026_DIR / "batch025_artifact_ingest_summary.json")
    verification = read_json(BATCH026_DIR / "batch025_artifact_verification.json")
    correction = read_json(BATCH026_DIR / "batch025_status_correction.json")
    policy = read_json(BATCH026_DIR / "batch026_harness_v9_generation_policy.json")
    generation = read_json(BATCH026_DIR / "batch026_harness_v9_generation_result.json")
    pre_repair = read_json(BATCH026_DIR / "batch026_harness_v9_pre_repair_verification.json")
    preservation = read_json(BATCH026_DIR / "batch026_target_intent_preservation.json")
    firewall = read_json(BATCH026_DIR / "batch026_decision_time_evidence_firewall.json")
    feasibility = read_json(BATCH026_DIR / "issue_derived_repair_feasibility_batch026.json")
    claim = read_json(BATCH026_DIR / "claim_boundary_batch026.json")
    ledger = read_json(BATCH026_DIR / "proof_obligations_ledger_batch026.json")
    language = read_json(BATCH026_DIR / "public_language_audit_batch026.json")
    minimality = read_json(BATCH026_DIR / "artifact_minimality_audit.json")
    budget = read_json(BATCH026_DIR / "artifact_payload_budget.json")
    batch026_post_verification = read_json(POST_DIR / "batch026_artifact_verification.json")
    batch026_post_ingest = read_json(POST_DIR / "batch026_artifact_ingest_summary.json")
    batch026_inconsistency = read_json(POST_DIR / "batch026_harness_state_inconsistency_audit.json")

    if ingest.get("status") != "PASS" or verification.get("status") != "PASS" or correction.get("status") != "PASS":
        errors.append("Batch026 did not carry Batch025 ingest verification records")
    if verification.get("artifact_sha256") != "c3830498c52188c01ec341d5c97fcd9c2df0cfbe042ef55baf01ba61b9b7b1eb":
        errors.append("Batch026 Batch025 artifact SHA mismatch")
    if batch025_state.get("status") != "PASS_WITH_BATCH025_TARGET_INTENT_ALIGNED":
        errors.append("Batch026 prerequisite Batch025 state is not target-intent-aligned")
    if batch025_state.get("exact_blocker") == "docker_runtime_provider_unavailable":
        errors.append("Batch026 carried stale Batch025 Docker blocker")
    if batch025_state.get("target_intent_alignment_status") != "PASS":
        errors.append("Batch026 prerequisite Target-Intent Alignment not PASS")
    if policy.get("batch025_target_intent_alignment_officially_ingested") is not True:
        errors.append("Batch026 harness policy does not require official Batch025 alignment")
    if policy.get("relative_git_dir_active_command_context_allowed") is not False:
        errors.append("Batch026 policy allows relative Git directory active command context")
    if generation.get("relative_git_dir_active_command_context_used") is True or pre_repair.get("relative_git_dir_active_command_context_used") is True:
        errors.append("Batch026 used relative Git directory as active command context")
    if preservation.get("stale_provider_context_blocker_carried_forward") is True:
        errors.append("Batch026 target-intent preservation carried stale provider blocker")
    if preservation.get("batch025_target_intent_alignment_status") != "PASS":
        errors.append("Batch026 Target-Intent Alignment preservation failed")
    if firewall.get("fixed_revision_accessed") is not False or firewall.get("gold_patch_accessed") is not False or firewall.get("future_pr_accessed") is not False or firewall.get("later_outcome_evidence_accessed") is not False:
        errors.append("Batch026 forbidden evidence firewall failed")
    if generation.get("source_mutated") is True or generation.get("tests_mutated") is True:
        errors.append("Batch026 harness generation mutated source or tests")
    harness_verified = pre_repair.get("status") == "PASS" and pre_repair.get("target_aligned_pre_repair_failure_reproduced") is True
    if feasibility.get("issue_derived_repair_feasibility") is True and not harness_verified:
        errors.append("Batch026 issue-derived repair feasibility claimed before harness verification")
    if claim.get("repair_ran") is not False or claim.get("patch_generated") is not False:
        errors.append("Batch026 repair or patch generation ran unexpectedly")
    if claim.get("matched_null_ran") is not False:
        errors.append("Batch026 matched-null ran unexpectedly")
    if claim.get("psa82_permutation_null_ran") is not False or claim.get("structured_fragility_diagnostic_ran") is not False:
        errors.append("Batch026 downstream diagnostic ran without patch candidate")
    if state.get("patch_generated") is not False or state.get("patch_authorized") is not False or state.get("patch_attempted") is not False:
        errors.append("Batch026 patch boundary changed")
    if state.get("matched_null_diagnostic_run_count") != 0:
        errors.append("Batch026 matched-null diagnostic count changed")
    if state.get("native_repair_episode_count") != 4 or state.get("issue_derived_repair_episode_count") != 0:
        errors.append("Batch026 repair counts changed")
    if state.get("full_scoring") != "NOT_RUN/disallowed" or state.get("memory_lift") != "not_demonstrated":
        errors.append("Batch026 scoring or memory boundary changed")
    if state.get("self_maintaining_software") != "false/not_demonstrated":
        errors.append("Batch026 self-maintaining claim changed")
    if state.get("current_protocol") != "v2.13":
        errors.append("Batch026 current protocol changed")
    if not str(state.get("status", "")).startswith("PASS_WITH_BATCH026_"):
        errors.append("Batch026 state mismatch")
    if batch026_post_verification.get("status") != "PASS":
        errors.append("Batch026 artifact verification missing or not PASS")
    if batch026_post_verification.get("artifact_sha256") != "1606f12d73789380e8de100d71de6919bbdb291ba42f6a52951be0aad7e88a9b":
        errors.append("Batch026 artifact SHA mismatch")
    if batch026_post_verification.get("artifact_size_bytes") != 134913 or batch026_post_verification.get("zip_entry_count") != 137:
        errors.append("Batch026 artifact size or entry count mismatch")
    if batch026_post_verification.get("unsafe_path_count") != 0 or batch026_post_verification.get("duplicate_path_count") != 0:
        errors.append("Batch026 artifact ZIP hygiene mismatch")
    if batch026_post_verification.get("manifest_failure_count") != 0:
        errors.append("Batch026 artifact manifest failures detected")
    if batch026_post_ingest.get("status") != "PASS":
        errors.append("Batch026 artifact ingest summary missing or not PASS")
    if batch026_inconsistency.get("audit_note") != "harness_v9_state_inconsistent_or_unexecuted":
        errors.append("Batch026 harness-state inconsistency was not recorded")
    if batch026_inconsistency.get("harness_file_exists") is not True:
        errors.append("Batch026 inconsistency audit missing harness file evidence")
    if generation.get("status") == "NOT_RUN" and pre_repair.get("status") == "NOT_RUN" and batch026_inconsistency.get("executed_harness_telemetry_present") is not False:
        errors.append("Batch026 inconsistency audit did not preserve unexecuted telemetry finding")
    if ledger.get("status") != "PASS" or ledger.get("repair_or_patch_before_harness_v9_verification") is not False:
        errors.append("Batch026 proof ledger invalid")
    if ledger.get("matched_null_without_patch_candidate") is not False:
        errors.append("Batch026 matched-null proof ledger boundary invalid")
    if language.get("status") != "PASS":
        errors.append("Batch026 public language audit failed")
    if minimality.get("recursive_prior_batch_packaging_detected") is not False:
        errors.append("Batch026 recursive prior batch packaging detected")
    if budget.get("status") != "PASS":
        errors.append("Batch026 artifact budget failed")
    return errors


def audit_batch027_records() -> list[str]:
    errors: list[str] = []
    for name in BATCH027_REQUIRED:
        if not (BATCH027_DIR / name).is_file():
            errors.append(f"batch027 missing required file {name}")
    if errors:
        return errors
    manifest = verify_manifest(BATCH027_DIR)
    if manifest.get("status") != "PASS":
        errors.append(f"batch027 manifest failed: {manifest}")

    batch026_state = read_json(BATCH026_DIR / "consolidated_state_clean_replication_batch_026.json")
    state = read_json(BATCH027_DIR / "consolidated_state_clean_replication_batch_027.json")
    ingest = read_json(BATCH027_DIR / "batch026_artifact_ingest_summary.json")
    verification = read_json(BATCH027_DIR / "batch026_artifact_verification.json")
    inconsistency = read_json(BATCH027_DIR / "batch026_harness_state_inconsistency_audit.json")
    reconciliation = read_json(BATCH027_DIR / "batch027_harness_v9_state_reconciliation.json")
    policy = read_json(BATCH027_DIR / "batch027_harness_v9_execution_policy.json")
    execution = read_json(BATCH027_DIR / "batch027_harness_v9_execution_result.json")
    pre_repair = read_json(BATCH027_DIR / "batch027_harness_v9_pre_repair_verification.json")
    provider_context = read_json(BATCH027_DIR / "batch027_provider_command_context_audit.json")
    firewall = read_json(BATCH027_DIR / "batch027_decision_time_evidence_firewall.json")
    feasibility = read_json(BATCH027_DIR / "issue_derived_repair_feasibility_batch027.json")
    claim = read_json(BATCH027_DIR / "claim_boundary_batch027.json")
    ledger = read_json(BATCH027_DIR / "proof_obligations_ledger_batch027.json")
    language = read_json(BATCH027_DIR / "public_language_audit_batch027.json")
    minimality = read_json(BATCH027_DIR / "artifact_minimality_audit.json")
    budget = read_json(BATCH027_DIR / "artifact_payload_budget.json")

    if ingest.get("status") != "PASS" or verification.get("status") != "PASS":
        errors.append("Batch027 did not record Batch026 artifact custody before logic")
    if verification.get("artifact_sha256") != "1606f12d73789380e8de100d71de6919bbdb291ba42f6a52951be0aad7e88a9b":
        errors.append("Batch027 Batch026 artifact SHA mismatch")
    if inconsistency.get("audit_note") != "harness_v9_state_inconsistent_or_unexecuted":
        errors.append("Batch027 ignored Batch026 harness-state inconsistency")
    if reconciliation.get("harness_file_exists") is not True:
        errors.append("Batch027 reconciliation missing harness file evidence")
    if reconciliation.get("classification") not in {"generated_but_unexecuted_harness", "executed_harness_result_recorded"}:
        errors.append("Batch027 harness-state classification invalid")
    if reconciliation.get("classification") == "executed_harness_result_recorded" and inconsistency.get("executed_harness_telemetry_present") is False:
        errors.append("Batch027 incorrectly treated Batch026 as already executed")
    if batch026_state.get("status") != "PASS_WITH_BATCH026_HARNESS_V9_BLOCKED":
        errors.append("Batch027 prerequisite Batch026 state mismatch")
    if policy.get("requires_batch026_artifact_custody") is not True or policy.get("requires_harness_state_reconciliation") is not True:
        errors.append("Batch027 policy missing custody or reconciliation requirement")
    if policy.get("relative_git_dir_active_command_context_allowed") is not False:
        errors.append("Batch027 policy allows relative Git directory active command context")
    if provider_context.get("relative_git_dir_active_command_context_used") is True or execution.get("relative_git_dir_active_command_context_used") is True or pre_repair.get("relative_git_dir_active_command_context_used") is True:
        errors.append("Batch027 used relative Git directory as active command context")
    if execution.get("status") == "PASS":
        if not execution.get("command") or execution.get("command") == "NOT_RUN":
            errors.append("Batch027 execution PASS without command")
        if execution.get("returncode") is None:
            errors.append("Batch027 execution PASS without return code")
        if not execution.get("stdout_sha256") or not execution.get("stderr_sha256"):
            errors.append("Batch027 execution PASS without stdout/stderr hashes")
    if provider_context.get("status") == "PASS":
        if provider_context.get("provider_source_root") is None or provider_context.get("git_dir_path") is None:
            errors.append("Batch027 provider context missing source root or .git path")
        if provider_context.get("absolute_git_dir") is None or provider_context.get("absolute_git_work_tree") is None:
            errors.append("Batch027 provider context missing absolute Git environment")
    if firewall.get("fixed_revision_accessed") is not False or firewall.get("gold_patch_accessed") is not False or firewall.get("future_pr_accessed") is not False or firewall.get("later_outcome_evidence_accessed") is not False:
        errors.append("Batch027 forbidden evidence firewall failed")
    if execution.get("source_mutated") is True or execution.get("tests_mutated") is True:
        errors.append("Batch027 harness execution mutated source or tests")
    harness_verified = pre_repair.get("status") == "PASS" and pre_repair.get("target_aligned_pre_repair_failure_reproduced") is True
    if feasibility.get("issue_derived_repair_feasibility") is True and not harness_verified:
        errors.append("Batch027 issue-derived repair feasibility claimed before harness verification")
    if claim.get("repair_ran") is not False or claim.get("patch_generated") is not False:
        errors.append("Batch027 repair or patch generation ran unexpectedly")
    if claim.get("matched_null_ran") is not False:
        errors.append("Batch027 matched-null ran unexpectedly")
    if claim.get("psa82_permutation_null_ran") is not False or claim.get("structured_fragility_diagnostic_ran") is not False:
        errors.append("Batch027 downstream diagnostic ran without patch candidate")
    if state.get("patch_generated") is not False or state.get("patch_authorized") is not False or state.get("patch_attempted") is not False:
        errors.append("Batch027 patch boundary changed")
    if state.get("matched_null_diagnostic_run_count") != 0:
        errors.append("Batch027 matched-null diagnostic count changed")
    if state.get("native_repair_episode_count") != 4 or state.get("issue_derived_repair_episode_count") != 0:
        errors.append("Batch027 repair counts changed")
    if state.get("full_scoring") != "NOT_RUN/disallowed" or state.get("memory_lift") != "not_demonstrated":
        errors.append("Batch027 scoring or memory boundary changed")
    if state.get("self_maintaining_software") != "false/not_demonstrated":
        errors.append("Batch027 self-maintaining claim changed")
    if state.get("current_protocol") != "v2.13":
        errors.append("Batch027 current protocol changed")
    if not str(state.get("status", "")).startswith("PASS_WITH_BATCH027_"):
        errors.append("Batch027 state mismatch")
    if ledger.get("status") != "PASS" or ledger.get("repair_or_patch_before_harness_v9_verification") is not False:
        errors.append("Batch027 proof ledger invalid")
    if ledger.get("matched_null_without_patch_candidate") is not False:
        errors.append("Batch027 matched-null proof ledger boundary invalid")
    if language.get("status") != "PASS":
        errors.append("Batch027 public language audit failed")
    if minimality.get("recursive_prior_batch_packaging_detected") is not False:
        errors.append("Batch027 recursive prior batch packaging detected")
    if budget.get("status") != "PASS":
        errors.append("Batch027 artifact budget failed")
    return errors


def audit_batch028_records() -> list[str]:
    errors: list[str] = []
    for name in BATCH028_REQUIRED:
        if not (BATCH028_DIR / name).is_file():
            errors.append(f"batch028 missing required file {name}")
    if errors:
        return errors
    manifest = verify_manifest(BATCH028_DIR)
    if manifest.get("status") != "PASS":
        errors.append(f"batch028 manifest failed: {manifest}")

    batch027_state = read_json(BATCH027_DIR / "consolidated_state_clean_replication_batch_027.json")
    state = read_json(BATCH028_DIR / "consolidated_state_clean_replication_batch_028.json")
    ingest = read_json(BATCH028_DIR / "batch027_artifact_ingest_summary.json")
    verification = read_json(BATCH028_DIR / "batch027_artifact_verification.json")
    precision = read_json(BATCH028_DIR / "batch027_execution_telemetry_precision_audit.json")
    post_verification = read_json(POST_DIR / "batch027_artifact_verification.json")
    post_precision = read_json(POST_DIR / "batch027_execution_telemetry_precision_audit.json")
    payload_policy = read_json(BATCH028_DIR / "batch028_harness_v9_payload_rehydration_policy.json")
    payload_result = read_json(BATCH028_DIR / "batch028_harness_v9_payload_rehydration_result.json")
    execution_policy = read_json(BATCH028_DIR / "batch028_harness_v9_execution_policy.json")
    provider_context = read_json(BATCH028_DIR / "batch028_provider_command_context_audit.json")
    execution = read_json(BATCH028_DIR / "batch028_harness_v9_execution_result.json")
    pre_repair = read_json(BATCH028_DIR / "batch028_harness_v9_pre_repair_verification.json")
    firewall = read_json(BATCH028_DIR / "batch028_decision_time_evidence_firewall.json")
    feasibility = read_json(BATCH028_DIR / "issue_derived_repair_feasibility_batch028.json")
    claim = read_json(BATCH028_DIR / "claim_boundary_batch028.json")
    ledger = read_json(BATCH028_DIR / "proof_obligations_ledger_batch028.json")
    language = read_json(BATCH028_DIR / "public_language_audit_batch028.json")
    minimality = read_json(BATCH028_DIR / "artifact_minimality_audit.json")
    budget = read_json(BATCH028_DIR / "artifact_payload_budget.json")

    if ingest.get("status") != "PASS" or verification.get("status") != "PASS":
        errors.append("Batch028 did not record Batch027 artifact custody before logic")
    if verification.get("artifact_sha256") != "75821ad1080d3457425318d45e198e43b1776eddc7f13188c820998c2bf6476f":
        errors.append("Batch028 Batch027 artifact SHA mismatch")
    if verification.get("artifact_size_bytes") != 136721 or verification.get("zip_entry_count") != 140:
        errors.append("Batch028 Batch027 artifact size or entry count mismatch")
    if verification.get("artifact_level_manifest_failures") != 0 or verification.get("batch027_manifest_failures") != 0 or verification.get("post_boundary_manifest_failures") != 0:
        errors.append("Batch028 Batch027 manifest verification failed")
    if verification.get("codex_downloaded_artifact") is not False or verification.get("zip_tar_payload_ingested") is not False:
        errors.append("Batch028 violated manual artifact boundary")
    if post_verification.get("artifact_sha256") != verification.get("artifact_sha256"):
        errors.append("Batch028 post boundary Batch027 verification mismatch")
    if precision.get("status") != "PASS" or post_precision.get("status") != "PASS":
        errors.append("Batch028 ignored Batch027 telemetry precision audit")
    if precision.get("failure_not_reproduced_language_supported_by_execution_telemetry") is not False:
        errors.append("Batch028 precision audit treated unexecuted Batch027 blocker as telemetry")
    if batch027_state.get("harness_v9_executed") is not False or batch027_state.get("harness_v9_execution_status") != "NOT_RUN":
        errors.append("Batch028 prerequisite Batch027 official unexecuted state mismatch")
    if state.get("batch027_status_preserved") != "PASS_WITH_BATCH027_HARNESS_V9_EXECUTION_BLOCKED":
        errors.append("Batch028 did not preserve Batch027 official boundary")
    if payload_policy.get("harness_hash_required_before_execution") is not True:
        errors.append("Batch028 payload policy does not require harness hash before execution")
    if payload_result.get("status") != "PASS" or payload_result.get("method") not in {"rehydrated", "regenerated"}:
        errors.append("Batch028 cannot identify whether harness payload was rehydrated or regenerated")
    if payload_result.get("final_harness_sha256") != "da098a46ef7efea42f2c9b35451b51f66038d58b6675fe386868338a3b3e0c01":
        errors.append("Batch028 harness payload SHA mismatch")
    if not payload_result.get("final_harness_path") or not (BATCH028_DIR / "issue_derived_ephemeral_harness_v9.py").is_file():
        errors.append("Batch028 harness payload path missing")
    if execution_policy.get("requires_batch027_artifact_custody") is not True or execution_policy.get("requires_harness_hash_before_execution") is not True:
        errors.append("Batch028 execution policy missing custody or hash requirement")
    if execution_policy.get("relative_git_dir_active_command_context_allowed") is not False:
        errors.append("Batch028 execution policy allows relative Git directory active command context")
    if provider_context.get("relative_git_dir_active_command_context_used") is True or execution.get("relative_git_dir_active_command_context_used") is True or pre_repair.get("relative_git_dir_active_command_context_used") is True:
        errors.append("Batch028 used relative Git directory as active command context")
    if firewall.get("fixed_revision_accessed") is not False or firewall.get("gold_patch_accessed") is not False or firewall.get("future_pr_accessed") is not False or firewall.get("later_outcome_evidence_accessed") is not False:
        errors.append("Batch028 forbidden evidence firewall failed")
    harness_executed = execution.get("status") in {"PASS", "BLOCK"} and execution.get("command") != "NOT_RUN"
    if harness_executed:
        if execution.get("returncode") is None:
            errors.append("Batch028 executed harness without return code")
        if not execution.get("stdout_sha256") or not execution.get("stderr_sha256"):
            errors.append("Batch028 executed harness without stdout/stderr hashes")
        if not execution.get("cwd"):
            errors.append("Batch028 executed harness without cwd")
    if state.get("exact_blocker") == "issue_derived_harness_v9_target_aligned_failure_not_reproduced_under_approved_context" and not harness_executed:
        errors.append("Batch028 claimed target failure not reproduced without executed telemetry")
    if provider_context.get("status") == "PASS":
        if provider_context.get("provider_source_root") is None or provider_context.get("git_dir_path") is None:
            errors.append("Batch028 provider context missing source root or .git path")
        if provider_context.get("absolute_git_dir") is None or provider_context.get("absolute_git_work_tree") is None:
            errors.append("Batch028 provider context missing absolute Git environment")
    if execution.get("source_mutated") is True or execution.get("tests_mutated") is True:
        errors.append("Batch028 harness execution mutated source or tests")
    harness_verified = pre_repair.get("status") == "PASS" and pre_repair.get("target_aligned_pre_repair_failure_reproduced") is True
    if feasibility.get("issue_derived_repair_feasibility") is True and not harness_verified:
        errors.append("Batch028 issue-derived repair feasibility claimed before harness verification")
    if claim.get("repair_ran") is not False or claim.get("patch_generated") is not False:
        errors.append("Batch028 repair or patch generation ran unexpectedly")
    if claim.get("matched_null_ran") is not False:
        errors.append("Batch028 matched-null ran unexpectedly")
    if claim.get("psa82_permutation_null_ran") is not False or claim.get("structured_fragility_diagnostic_ran") is not False:
        errors.append("Batch028 downstream diagnostic ran without patch candidate")
    if state.get("patch_generated") is not False or state.get("patch_authorized") is not False or state.get("patch_attempted") is not False:
        errors.append("Batch028 patch boundary changed")
    if state.get("matched_null_diagnostic_run_count") != 0:
        errors.append("Batch028 matched-null diagnostic count changed")
    if state.get("native_repair_episode_count") != 4 or state.get("issue_derived_repair_episode_count") != 0:
        errors.append("Batch028 repair counts changed")
    if state.get("full_scoring") != "NOT_RUN/disallowed" or state.get("memory_lift") != "not_demonstrated":
        errors.append("Batch028 scoring or memory boundary changed")
    if state.get("self_maintaining_software") != "false/not_demonstrated":
        errors.append("Batch028 self-maintaining claim changed")
    if state.get("current_protocol") != "v2.13":
        errors.append("Batch028 current protocol changed")
    if not str(state.get("status", "")).startswith("PASS_WITH_BATCH028_"):
        errors.append("Batch028 state mismatch")
    if ledger.get("status") != "PASS" or ledger.get("repair_or_patch_before_harness_v9_verification") is not False:
        errors.append("Batch028 proof ledger invalid")
    if ledger.get("matched_null_without_patch_candidate") is not False:
        errors.append("Batch028 matched-null proof ledger boundary invalid")
    if language.get("status") != "PASS":
        errors.append("Batch028 public language audit failed")
    if minimality.get("recursive_prior_batch_packaging_detected") is not False:
        errors.append("Batch028 recursive prior batch packaging detected")
    if budget.get("status") != "PASS":
        errors.append("Batch028 artifact budget failed")
    return errors


def audit_batch029_records() -> list[str]:
    errors: list[str] = []
    for name in BATCH029_REQUIRED:
        if not (BATCH029_DIR / name).is_file():
            errors.append(f"batch029 missing required file {name}")
    if errors:
        return errors
    manifest = verify_manifest(BATCH029_DIR)
    if manifest.get("status") != "PASS":
        errors.append(f"batch029 manifest failed: {manifest}")

    batch028_state = read_json(BATCH028_DIR / "consolidated_state_clean_replication_batch_028.json")
    state = read_json(BATCH029_DIR / "consolidated_state_clean_replication_batch_029.json")
    ingest = read_json(BATCH029_DIR / "batch028_artifact_ingest_summary.json")
    verification = read_json(BATCH029_DIR / "batch028_artifact_verification.json")
    precision = read_json(BATCH029_DIR / "batch028_execution_telemetry_precision_audit.json")
    post_verification = read_json(POST_DIR / "batch028_artifact_verification.json")
    post_precision = read_json(POST_DIR / "batch028_execution_telemetry_precision_audit.json")
    policy = read_json(BATCH029_DIR / "batch029_harness_v9_execution_policy.json")
    integrity = read_json(BATCH029_DIR / "batch029_harness_payload_integrity_check.json")
    provider_context = read_json(BATCH029_DIR / "batch029_provider_command_context_audit.json")
    execution = read_json(BATCH029_DIR / "batch029_harness_v9_execution_result.json")
    pre_repair = read_json(BATCH029_DIR / "batch029_harness_v9_pre_repair_verification.json")
    target_report = read_json(BATCH029_DIR / "batch029_target_intent_match_report.json")
    firewall = read_json(BATCH029_DIR / "batch029_decision_time_evidence_firewall.json")
    feasibility = read_json(BATCH029_DIR / "issue_derived_repair_feasibility_batch029.json")
    claim = read_json(BATCH029_DIR / "claim_boundary_batch029.json")
    ledger = read_json(BATCH029_DIR / "proof_obligations_ledger_batch029.json")
    language = read_json(BATCH029_DIR / "public_language_audit_batch029.json")
    minimality = read_json(BATCH029_DIR / "artifact_minimality_audit.json")
    budget = read_json(BATCH029_DIR / "artifact_payload_budget.json")

    if ingest.get("status") != "PASS" or verification.get("status") != "PASS":
        errors.append("Batch029 did not record Batch028 artifact custody before logic")
    if verification.get("artifact_sha256") != "490d50448d97eb3947f70a399fee9a1439a6c091bb659dd86e8c5a28c724201c":
        errors.append("Batch029 Batch028 artifact SHA mismatch")
    if verification.get("artifact_size_bytes") != 141704 or verification.get("zip_entry_count") != 145:
        errors.append("Batch029 Batch028 artifact size or entry count mismatch")
    if verification.get("artifact_level_manifest_failures") != 0 or verification.get("batch028_manifest_failures") != 0 or verification.get("post_boundary_manifest_failures") != 0:
        errors.append("Batch029 Batch028 manifest verification failed")
    if verification.get("codex_downloaded_artifact") is not False or verification.get("zip_tar_payload_ingested") is not False:
        errors.append("Batch029 violated manual artifact boundary")
    if post_verification.get("artifact_sha256") != verification.get("artifact_sha256"):
        errors.append("Batch029 post boundary Batch028 verification mismatch")
    if precision.get("status") != "PASS" or post_precision.get("status") != "PASS":
        errors.append("Batch029 ignored Batch028 telemetry precision audit")
    if precision.get("provider_harness_v9_execution_failed_supported_by_executed_harness_telemetry") is not False:
        errors.append("Batch029 precision audit treated unexecuted Batch028 blocker as telemetry")
    if batch028_state.get("harness_v9_executed") is not False or batch028_state.get("harness_v9_execution_status") != "NOT_RUN":
        errors.append("Batch029 prerequisite Batch028 official unexecuted state mismatch")
    if state.get("batch028_status_preserved") != "PASS_WITH_BATCH028_HARNESS_V9_EXECUTION_BLOCKED":
        errors.append("Batch029 did not preserve Batch028 official boundary")
    if policy.get("requires_batch028_artifact_custody") is not True or policy.get("requires_harness_sha256_before_execution") is not True:
        errors.append("Batch029 policy missing custody or harness SHA requirement")
    if policy.get("relative_git_dir_active_command_context_allowed") is not False:
        errors.append("Batch029 execution policy allows relative Git directory active command context")
    if integrity.get("status") != "PASS" or integrity.get("verified_before_execution") is not True:
        errors.append("Batch029 harness SHA256 was not verified before execution")
    if integrity.get("observed_harness_sha256") != "da098a46ef7efea42f2c9b35451b51f66038d58b6675fe386868338a3b3e0c01":
        errors.append("Batch029 harness payload SHA mismatch")
    if provider_context.get("relative_git_dir_active_command_context_used") is True or execution.get("relative_git_dir_active_command_context_used") is True or pre_repair.get("relative_git_dir_active_command_context_used") is True:
        errors.append("Batch029 used relative Git directory as active command context")
    if firewall.get("fixed_revision_accessed") is not False or firewall.get("gold_patch_accessed") is not False or firewall.get("future_pr_accessed") is not False or firewall.get("later_outcome_evidence_accessed") is not False:
        errors.append("Batch029 forbidden evidence firewall failed")
    harness_executed = execution.get("status") in {"PASS", "BLOCK"} and execution.get("command") != "NOT_RUN"
    if harness_executed:
        if execution.get("returncode") is None:
            errors.append("Batch029 executed harness without return code")
        if not execution.get("stdout_sha256") or not execution.get("stderr_sha256"):
            errors.append("Batch029 executed harness without stdout/stderr hashes")
        if not execution.get("cwd"):
            errors.append("Batch029 executed harness without cwd")
        if state.get("provider_source_head_verified") is not True:
            errors.append("Batch029 executed harness without selected source HEAD verification")
    if state.get("exact_blocker") == "issue_derived_harness_v9_target_aligned_failure_not_reproduced_under_approved_context" and not harness_executed:
        errors.append("Batch029 claimed target failure not reproduced without executed telemetry")
    if provider_context.get("status") == "PASS":
        if provider_context.get("provider_source_root") is None or provider_context.get("git_dir_path") is None:
            errors.append("Batch029 provider context missing source root or .git path")
        if provider_context.get("absolute_git_dir") is None or provider_context.get("absolute_git_work_tree") is None:
            errors.append("Batch029 provider context missing absolute Git environment")
    if execution.get("source_mutated") is True or execution.get("tests_mutated") is True:
        errors.append("Batch029 harness execution mutated source or tests")
    harness_verified = pre_repair.get("status") == "PASS" and pre_repair.get("target_aligned_pre_repair_failure_reproduced") is True
    if target_report.get("target_intent_matching_result") is True and not harness_verified:
        errors.append("Batch029 target-intent report overclaimed without pre-repair verification")
    if feasibility.get("issue_derived_repair_feasibility") is True and not harness_verified:
        errors.append("Batch029 issue-derived repair feasibility claimed before harness verification")
    if claim.get("repair_ran") is not False or claim.get("patch_generated") is not False or claim.get("patch_authorized") is not False or claim.get("patch_attempted") is not False:
        errors.append("Batch029 repair or patch generation ran unexpectedly")
    if claim.get("matched_null_ran") is not False:
        errors.append("Batch029 matched-null ran unexpectedly")
    if claim.get("psa82_permutation_null_ran") is not False or claim.get("structured_fragility_diagnostic_ran") is not False:
        errors.append("Batch029 downstream diagnostic ran without patch candidate")
    if state.get("patch_generated") is not False or state.get("patch_authorized") is not False or state.get("patch_attempted") is not False:
        errors.append("Batch029 patch boundary changed")
    if state.get("matched_null_diagnostic_run_count") != 0:
        errors.append("Batch029 matched-null diagnostic count changed")
    if state.get("native_repair_episode_count") != 4 or state.get("issue_derived_repair_episode_count") != 0:
        errors.append("Batch029 repair counts changed")
    if state.get("full_scoring") != "NOT_RUN/disallowed" or state.get("memory_lift") != "not_demonstrated":
        errors.append("Batch029 scoring or memory boundary changed")
    if state.get("self_maintaining_software") != "false/not_demonstrated":
        errors.append("Batch029 self-maintaining claim changed")
    if state.get("current_protocol") != "v2.13":
        errors.append("Batch029 current protocol changed")
    if not str(state.get("status", "")).startswith("PASS_WITH_BATCH029_"):
        errors.append("Batch029 state mismatch")
    if ledger.get("status") != "PASS" or ledger.get("repair_or_patch_before_harness_v9_verification") is not False:
        errors.append("Batch029 proof ledger invalid")
    if ledger.get("matched_null_without_patch_candidate") is not False:
        errors.append("Batch029 matched-null proof ledger boundary invalid")
    if language.get("status") != "PASS":
        errors.append("Batch029 public language audit failed")
    if minimality.get("recursive_prior_batch_packaging_detected") is not False:
        errors.append("Batch029 recursive prior batch packaging detected")
    if budget.get("status") != "PASS":
        errors.append("Batch029 artifact budget failed")
    return errors


def audit_batch030_records() -> list[str]:
    errors: list[str] = []
    for name in BATCH030_REQUIRED:
        if not (BATCH030_DIR / name).is_file():
            errors.append(f"batch030 missing required file {name}")
    if errors:
        return errors
    manifest = verify_manifest(BATCH030_DIR)
    if manifest.get("status") != "PASS":
        errors.append(f"batch030 manifest failed: {manifest}")

    batch029_state = read_json(BATCH029_DIR / "consolidated_state_clean_replication_batch_029.json")
    state = read_json(BATCH030_DIR / "consolidated_state_clean_replication_batch_030.json")
    ingest = read_json(BATCH030_DIR / "batch029_artifact_ingest_summary.json")
    verification = read_json(BATCH030_DIR / "batch029_artifact_verification.json")
    precision = read_json(BATCH030_DIR / "batch029_blocker_precision_audit.json")
    post_verification = read_json(POST_DIR / "batch029_artifact_verification.json")
    post_precision = read_json(POST_DIR / "batch029_blocker_precision_audit.json")
    correction = read_json(BATCH030_DIR / "batch030_gate_predicate_correction.json")
    availability = read_json(BATCH030_DIR / "batch030_harness_payload_availability.json")
    integrity = read_json(BATCH030_DIR / "batch030_harness_payload_integrity_check.json")
    provider_context = read_json(BATCH030_DIR / "batch030_provider_command_context_audit.json")
    policy = read_json(BATCH030_DIR / "batch030_harness_v9_execution_policy.json")
    execution = read_json(BATCH030_DIR / "batch030_harness_v9_execution_result.json")
    pre_repair = read_json(BATCH030_DIR / "batch030_harness_v9_pre_repair_verification.json")
    target_report = read_json(BATCH030_DIR / "batch030_target_intent_match_report.json")
    firewall = read_json(BATCH030_DIR / "batch030_decision_time_evidence_firewall.json")
    feasibility = read_json(BATCH030_DIR / "issue_derived_repair_feasibility_batch030.json")
    claim = read_json(BATCH030_DIR / "claim_boundary_batch030.json")
    ledger = read_json(BATCH030_DIR / "proof_obligations_ledger_batch030.json")
    language = read_json(BATCH030_DIR / "public_language_audit_batch030.json")
    minimality = read_json(BATCH030_DIR / "artifact_minimality_audit.json")
    budget = read_json(BATCH030_DIR / "artifact_payload_budget.json")

    if ingest.get("status") != "PASS" or verification.get("status") != "PASS":
        errors.append("Batch030 did not record Batch029 artifact custody before logic")
    if verification.get("artifact_sha256") != "f22242eaa3f38a960e1eb61b8fd1c56c7c7369e2fb6c20863116c5bfd7c8eb19":
        errors.append("Batch030 Batch029 artifact SHA mismatch")
    if verification.get("artifact_size_bytes") != 142519 or verification.get("zip_entry_count") != 147:
        errors.append("Batch030 Batch029 artifact size or entry count mismatch")
    if verification.get("artifact_level_manifest_failures") != 0 or verification.get("batch029_manifest_failures") != 0 or verification.get("post_boundary_manifest_failures") != 0:
        errors.append("Batch030 Batch029 manifest verification failed")
    if verification.get("codex_downloaded_artifact") is not False or verification.get("zip_tar_payload_ingested") is not False:
        errors.append("Batch030 violated manual artifact boundary")
    if post_verification.get("artifact_sha256") != verification.get("artifact_sha256"):
        errors.append("Batch030 post boundary Batch029 verification mismatch")
    if precision.get("status") != "PASS" or post_precision.get("status") != "PASS":
        errors.append("Batch030 did not examine Batch029 contradictory blocker")
    if precision.get("batch029_artifact_internal_blocker") != "batch028_artifact_custody_or_harness_integrity_missing":
        errors.append("Batch030 precision audit did not record Batch029 stale blocker")
    if precision.get("batch028_artifact_verification_status") != "PASS" or precision.get("harness_payload_integrity_status") != "PASS":
        errors.append("Batch030 precision audit failed to preserve Batch028 custody and harness integrity PASS")
    if batch029_state.get("harness_v9_executed") is not False or batch029_state.get("harness_v9_execution_status") != "NOT_RUN":
        errors.append("Batch030 prerequisite Batch029 unexecuted state mismatch")
    if state.get("batch029_status_preserved") != "PASS_WITH_BATCH029_HARNESS_V9_EXECUTION_BLOCKED":
        errors.append("Batch030 did not preserve Batch029 official boundary")
    if correction.get("status") != "PASS":
        errors.append("Batch030 gate predicate correction failed")
    if correction.get("incorrect_custody_or_integrity_blocker_suppressed") is not True:
        errors.append("Batch030 did not suppress stale custody/integrity blocker")
    if correction.get("batch028_artifact_verification_status") == "PASS" and correction.get("harness_payload_integrity_status") == "PASS":
        if correction.get("emitted_blocker") == "batch028_artifact_custody_or_harness_integrity_missing" or state.get("exact_blocker") == "batch028_artifact_custody_or_harness_integrity_missing":
            errors.append("Batch030 carried forward stale custody/integrity blocker")
    if availability.get("status") != "PASS" or availability.get("verified_before_execution") is not True:
        errors.append("Batch030 harness payload availability was not established before execution")
    if integrity.get("status") != "PASS" or integrity.get("verified_before_execution") is not True:
        errors.append("Batch030 harness SHA256 was not verified before execution")
    if integrity.get("observed_harness_sha256") != "da098a46ef7efea42f2c9b35451b51f66038d58b6675fe386868338a3b3e0c01":
        errors.append("Batch030 harness payload SHA mismatch")
    if policy.get("relative_git_dir_active_command_context_allowed") is not False:
        errors.append("Batch030 policy allows relative Git directory active command context")
    if provider_context.get("relative_git_dir_active_command_context_used") is True or execution.get("relative_git_dir_active_command_context_used") is True or pre_repair.get("relative_git_dir_active_command_context_used") is True:
        errors.append("Batch030 used relative Git directory as active command context")
    if firewall.get("fixed_revision_accessed") is not False or firewall.get("gold_patch_accessed") is not False or firewall.get("future_pr_accessed") is not False or firewall.get("later_outcome_evidence_accessed") is not False:
        errors.append("Batch030 forbidden evidence firewall failed")
    if sha_file := BATCH030_DIR / "issue_derived_ephemeral_harness_v9.py":
        if not sha_file.is_file():
            errors.append("Batch030 carried harness payload missing")
        elif read_json(BATCH030_DIR / "batch030_harness_payload_integrity_check.json").get("observed_harness_sha256") != "da098a46ef7efea42f2c9b35451b51f66038d58b6675fe386868338a3b3e0c01":
            errors.append("Batch030 carried harness payload hash not recorded")
    harness_executed = execution.get("status") in {"PASS", "BLOCK"} and execution.get("command") != "NOT_RUN"
    if harness_executed:
        if provider_context.get("status") == "NOT_RUN":
            errors.append("Batch030 provider command context remained NOT_RUN after execution claim")
        if execution.get("returncode") is None:
            errors.append("Batch030 executed harness without return code")
        if not execution.get("stdout_sha256") or not execution.get("stderr_sha256"):
            errors.append("Batch030 executed harness without stdout/stderr hashes")
        if not execution.get("cwd"):
            errors.append("Batch030 executed harness without cwd")
        if provider_context.get("selected_source_head_verified") is not True and state.get("provider_source_head_verified") is not True:
            errors.append("Batch030 executed harness without selected source HEAD verification")
    if state.get("exact_blocker") == "issue_derived_harness_v9_target_aligned_failure_not_reproduced_under_approved_context" and not harness_executed:
        errors.append("Batch030 claimed target failure not reproduced without executed telemetry")
    if target_report.get("target_intent_matching_result") is True and pre_repair.get("target_aligned_pre_repair_failure_reproduced") is not True:
        errors.append("Batch030 target-intent report overclaimed without pre-repair verification")
    if feasibility.get("issue_derived_repair_feasibility") is True and pre_repair.get("target_aligned_pre_repair_failure_reproduced") is not True:
        errors.append("Batch030 issue-derived repair feasibility claimed before harness verification")
    if claim.get("repair_ran") is not False or claim.get("patch_generated") is not False or claim.get("patch_authorized") is not False or claim.get("patch_attempted") is not False:
        errors.append("Batch030 repair or patch generation ran unexpectedly")
    if state.get("patch_generated") is not False or state.get("patch_authorized") is not False or state.get("patch_attempted") is not False:
        errors.append("Batch030 patch boundary changed")
    if claim.get("matched_null_ran") is not False or state.get("matched_null_diagnostic_run_count") != 0:
        errors.append("Batch030 matched-null ran unexpectedly")
    if claim.get("psa82_permutation_null_ran") is not False or claim.get("structured_fragility_diagnostic_ran") is not False:
        errors.append("Batch030 downstream diagnostic ran without patch candidate")
    if state.get("native_repair_episode_count") != 4 or claim.get("native_repair_episode_count") != 4:
        errors.append("Batch030 native repair count changed")
    if state.get("issue_derived_repair_episode_count") != 0 or claim.get("issue_derived_repair_episode_count") != 0:
        errors.append("Batch030 issue-derived repair count changed before feasibility repair validation")
    if state.get("full_scoring") != "NOT_RUN/disallowed" or claim.get("full_scoring") != "NOT_RUN/disallowed":
        errors.append("Batch030 full scoring boundary changed")
    if state.get("memory_lift") != "not_demonstrated" or state.get("self_maintaining_software") != "false/not_demonstrated":
        errors.append("Batch030 claim boundary changed")
    if state.get("current_protocol") != "v2.13":
        errors.append("Batch030 current protocol changed")
    if not str(state.get("status", "")).startswith("PASS_WITH_BATCH030_"):
        errors.append("Batch030 state mismatch")
    if ledger.get("status") != "PASS" or ledger.get("repair_or_patch_before_harness_v9_verification") is not False:
        errors.append("Batch030 proof ledger invalid")
    if ledger.get("matched_null_without_patch_candidate") is not False:
        errors.append("Batch030 matched-null proof ledger boundary invalid")
    if language.get("status") != "PASS":
        errors.append("Batch030 public language audit failed")
    if minimality.get("recursive_prior_batch_packaging_detected") is not False:
        errors.append("Batch030 recursive prior batch packaging detected")
    if budget.get("status") != "PASS":
        errors.append("Batch030 artifact budget failed")
    forbidden_tolerance_markers = ["1.45", "wiggle_room", "closure_tolerance", "residual_tolerance"]
    for path in list(BATCH030_DIR.glob("*.json")) + list(BATCH030_DIR.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        if any(marker in text for marker in forbidden_tolerance_markers):
            errors.append(f"Batch030 introduced forbidden tolerance marker in {path.name}")
    return errors


def audit_batch031_records() -> list[str]:
    errors: list[str] = []
    for name in BATCH031_REQUIRED:
        if not (BATCH031_DIR / name).is_file():
            errors.append(f"batch031 missing required file {name}")
    if errors:
        return errors
    manifest = verify_manifest(BATCH031_DIR)
    if manifest.get("status") != "PASS":
        errors.append(f"batch031 manifest failed: {manifest}")

    batch030_state = read_json(BATCH030_DIR / "consolidated_state_clean_replication_batch_030.json")
    state = read_json(BATCH031_DIR / "consolidated_state_clean_replication_batch_031.json")
    ingest = read_json(BATCH031_DIR / "batch030_artifact_ingest_summary.json")
    verification = read_json(BATCH031_DIR / "batch030_artifact_verification.json")
    precision = read_json(BATCH031_DIR / "batch030_blocker_precision_audit.json")
    post_verification = read_json(POST_DIR / "batch030_artifact_verification.json")
    post_precision = read_json(POST_DIR / "batch030_blocker_precision_audit.json")
    predicate = read_json(BATCH031_DIR / "batch031_provider_source_commit_predicate_audit.json")
    availability = read_json(BATCH031_DIR / "batch031_harness_payload_availability.json")
    integrity = read_json(BATCH031_DIR / "batch031_harness_payload_integrity_check.json")
    provider_context = read_json(BATCH031_DIR / "batch031_provider_command_context_audit.json")
    policy = read_json(BATCH031_DIR / "batch031_harness_v9_execution_policy.json")
    execution = read_json(BATCH031_DIR / "batch031_harness_v9_execution_result.json")
    pre_repair = read_json(BATCH031_DIR / "batch031_harness_v9_pre_repair_verification.json")
    target_report = read_json(BATCH031_DIR / "batch031_target_intent_match_report.json")
    firewall = read_json(BATCH031_DIR / "batch031_decision_time_evidence_firewall.json")
    feasibility = read_json(BATCH031_DIR / "issue_derived_repair_feasibility_batch031.json")
    claim = read_json(BATCH031_DIR / "claim_boundary_batch031.json")
    ledger = read_json(BATCH031_DIR / "proof_obligations_ledger_batch031.json")
    language = read_json(BATCH031_DIR / "public_language_audit_batch031.json")
    minimality = read_json(BATCH031_DIR / "artifact_minimality_audit.json")
    budget = read_json(BATCH031_DIR / "artifact_payload_budget.json")

    if ingest.get("status") != "PASS" or verification.get("status") != "PASS":
        errors.append("Batch031 did not record Batch030 artifact custody before logic")
    if verification.get("artifact_sha256") != "1513239dc6284757f0e6b2fe63312a1f6c9938eac66e58191c600e894cd3efb4":
        errors.append("Batch031 Batch030 artifact SHA mismatch")
    if verification.get("artifact_size_bytes") != 148275 or verification.get("zip_entry_count") != 153:
        errors.append("Batch031 Batch030 artifact size or entry count mismatch")
    if verification.get("artifact_level_manifest_failures") != 0 or verification.get("batch030_manifest_failures") != 0 or verification.get("post_boundary_manifest_failures") != 0:
        errors.append("Batch031 Batch030 manifest verification failed")
    if verification.get("codex_downloaded_artifact") is not False or verification.get("zip_tar_payload_ingested") is not False:
        errors.append("Batch031 violated manual artifact boundary")
    if post_verification.get("artifact_sha256") != verification.get("artifact_sha256"):
        errors.append("Batch031 post boundary Batch030 verification mismatch")
    if precision.get("status") != "PASS" or post_precision.get("status") != "PASS":
        errors.append("Batch031 did not examine Batch030 source predicate contradiction")
    if precision.get("batch030_artifact_internal_blocker") != "provider_source_commit_mismatch":
        errors.append("Batch031 precision audit did not record Batch030 source predicate blocker")
    if precision.get("provider_source_head_match") is not True:
        errors.append("Batch031 precision audit did not preserve matching Batch030 source HEAD evidence")
    if batch030_state.get("provider_source_head_verified") is not True or batch030_state.get("provider_source_head_sha") != "a2d13656adfaa010fb6c7339087f3347ad2b815a":
        errors.append("Batch031 prerequisite Batch030 source HEAD verification mismatch")
    if state.get("batch030_status_preserved") != "PASS_WITH_BATCH030_HARNESS_V9_EXECUTION_BLOCKED":
        errors.append("Batch031 did not preserve Batch030 official boundary")
    for key in ["expected_source_commit_sha", "observed_provider_source_head_sha", "provider_source_head_match", "provider_source_checkout_status", "git_rev_parse_head_return_code", "git_rev_parse_head_stdout_sha256", "git_rev_parse_head_stderr_sha256"]:
        if key not in predicate:
            errors.append(f"Batch031 source predicate missing {key}")
    if predicate.get("expected_source_commit_sha") != "a2d13656adfaa010fb6c7339087f3347ad2b815a":
        errors.append("Batch031 expected source commit mismatch")
    if predicate.get("observed_provider_source_head_sha") == predicate.get("expected_source_commit_sha"):
        if predicate.get("provider_source_commit_mismatch_emitted") is not False or state.get("exact_blocker") == "provider_source_commit_mismatch":
            errors.append("Batch031 emitted provider_source_commit_mismatch while expected and observed source HEAD match")
    if availability.get("status") != "PASS" or availability.get("verified_before_execution") is not True:
        errors.append("Batch031 harness payload availability was not established before execution")
    if integrity.get("status") != "PASS" or integrity.get("verified_before_execution") is not True:
        errors.append("Batch031 harness SHA256 was not verified before execution")
    if integrity.get("observed_harness_sha256") != "da098a46ef7efea42f2c9b35451b51f66038d58b6675fe386868338a3b3e0c01":
        errors.append("Batch031 harness payload SHA mismatch")
    if policy.get("relative_git_dir_active_command_context_allowed") is not False:
        errors.append("Batch031 policy allows relative Git directory active command context")
    if provider_context.get("relative_git_dir_active_command_context_used") is True or execution.get("relative_git_dir_active_command_context_used") is True or pre_repair.get("relative_git_dir_active_command_context_used") is True:
        errors.append("Batch031 used relative Git directory as active command context")
    if firewall.get("fixed_revision_accessed") is not False or firewall.get("gold_patch_accessed") is not False or firewall.get("future_pr_accessed") is not False or firewall.get("later_outcome_evidence_accessed") is not False:
        errors.append("Batch031 forbidden evidence firewall failed")
    harness_executed = execution.get("status") in {"PASS", "BLOCK"} and execution.get("command") != "NOT_RUN"
    if harness_executed:
        if provider_context.get("status") == "NOT_RUN":
            errors.append("Batch031 provider command context remained NOT_RUN after execution claim")
        if execution.get("returncode") is None:
            errors.append("Batch031 executed harness without return code")
        if not execution.get("stdout_sha256") or not execution.get("stderr_sha256"):
            errors.append("Batch031 executed harness without stdout/stderr hashes")
        if not execution.get("cwd"):
            errors.append("Batch031 executed harness without cwd")
        if provider_context.get("selected_source_head_verified") is not True and state.get("provider_source_head_verified") is not True:
            errors.append("Batch031 executed harness without selected source HEAD verification")
    if state.get("exact_blocker") == "issue_derived_harness_v9_target_aligned_failure_not_reproduced_under_approved_context" and not harness_executed:
        errors.append("Batch031 claimed target failure not reproduced without executed telemetry")
    if target_report.get("target_intent_matching_result") is True and pre_repair.get("target_aligned_pre_repair_failure_reproduced") is not True:
        errors.append("Batch031 target-intent report overclaimed without pre-repair verification")
    if feasibility.get("issue_derived_repair_feasibility") is True and pre_repair.get("target_aligned_pre_repair_failure_reproduced") is not True:
        errors.append("Batch031 issue-derived repair feasibility claimed before harness verification")
    if claim.get("repair_ran") is not False or claim.get("patch_generated") is not False or claim.get("patch_authorized") is not False or claim.get("patch_attempted") is not False:
        errors.append("Batch031 repair or patch generation ran unexpectedly")
    if claim.get("matched_null_ran") is not False or state.get("matched_null_diagnostic_run_count") != 0:
        errors.append("Batch031 matched-null ran unexpectedly")
    if claim.get("psa82_permutation_null_ran") is not False or claim.get("structured_fragility_diagnostic_ran") is not False:
        errors.append("Batch031 downstream diagnostic ran without patch candidate")
    if state.get("native_repair_episode_count") != 4 or claim.get("native_repair_episode_count") != 4:
        errors.append("Batch031 native repair count changed")
    if state.get("issue_derived_repair_episode_count") != 0 or claim.get("issue_derived_repair_episode_count") != 0:
        errors.append("Batch031 issue-derived repair count changed before feasibility repair validation")
    if state.get("full_scoring") != "NOT_RUN/disallowed" or claim.get("full_scoring") != "NOT_RUN/disallowed":
        errors.append("Batch031 full scoring boundary changed")
    if state.get("memory_lift") != "not_demonstrated" or state.get("self_maintaining_software") != "false/not_demonstrated":
        errors.append("Batch031 claim boundary changed")
    if state.get("current_protocol") != "v2.13":
        errors.append("Batch031 current protocol changed")
    if not str(state.get("status", "")).startswith("PASS_WITH_BATCH031_"):
        errors.append("Batch031 state mismatch")
    if ledger.get("status") != "PASS" or ledger.get("repair_or_patch_before_harness_v9_verification") is not False:
        errors.append("Batch031 proof ledger invalid")
    if ledger.get("matched_null_without_patch_candidate") is not False:
        errors.append("Batch031 matched-null proof ledger boundary invalid")
    if language.get("status") != "PASS":
        errors.append("Batch031 public language audit failed")
    if minimality.get("recursive_prior_batch_packaging_detected") is not False:
        errors.append("Batch031 recursive prior batch packaging detected")
    if budget.get("status") != "PASS":
        errors.append("Batch031 artifact budget failed")
    for path in list(BATCH031_DIR.glob("*.json")) + list(BATCH031_DIR.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        if any(marker in text for marker in ["1.45", "wiggle_room", "closure_tolerance", "residual_tolerance"]):
            errors.append(f"Batch031 introduced forbidden tolerance marker in {path.name}")
    return errors


def audit_batch032_records() -> list[str]:
    errors: list[str] = []
    for name in BATCH032_REQUIRED:
        if not (BATCH032_DIR / name).is_file():
            errors.append(f"batch032 missing required file {name}")
    if errors:
        return errors
    if verify_manifest(BATCH032_DIR).get("status") != "PASS":
        errors.append("batch032 manifest mismatch")

    batch031_state = read_json(BATCH031_DIR / "consolidated_state_clean_replication_batch_031.json")
    state = read_json(BATCH032_DIR / "consolidated_state_clean_replication_batch_032.json")
    ingest = read_json(BATCH032_DIR / "batch031_artifact_ingest_summary.json")
    verification = read_json(BATCH032_DIR / "batch031_artifact_verification.json")
    post_verification = read_json(POST_DIR / "batch031_artifact_verification.json")
    execution_classification = read_json(BATCH032_DIR / "batch031_execution_result_classification.json")
    safe_policy = read_json(BATCH032_DIR / "batch032_safe_directory_precondition_policy.json")
    safe_classification = read_json(BATCH032_DIR / "batch032_safe_directory_precondition_classification.json")
    normalization = read_json(BATCH032_DIR / "batch032_provider_environment_normalization.json")
    provider_context = read_json(BATCH032_DIR / "batch032_provider_command_context_audit.json")
    execution_policy = read_json(BATCH032_DIR / "batch032_harness_v9_execution_policy.json")
    execution = read_json(BATCH032_DIR / "batch032_harness_v9_execution_result.json")
    pre_repair = read_json(BATCH032_DIR / "batch032_harness_v9_pre_repair_verification.json")
    triage = read_json(BATCH032_DIR / "batch032_harness_design_triage.json")
    firewall = read_json(BATCH032_DIR / "batch032_decision_time_evidence_firewall.json")
    feasibility = read_json(BATCH032_DIR / "issue_derived_repair_feasibility_batch032.json")
    claim = read_json(BATCH032_DIR / "claim_boundary_batch032.json")
    ledger = read_json(BATCH032_DIR / "proof_obligations_ledger_batch032.json")
    language = read_json(BATCH032_DIR / "public_language_audit_batch032.json")
    minimality = read_json(BATCH032_DIR / "artifact_minimality_audit.json")
    budget = read_json(BATCH032_DIR / "artifact_payload_budget.json")

    if ingest.get("status") != "PASS" or verification.get("status") != "PASS":
        errors.append("Batch032 did not record Batch031 artifact custody before logic")
    if verification.get("artifact_sha256") != "2093598d0a08f9df46db6f4ff8c2ee22dbed8afbad8dc3b2483261dde637f537":
        errors.append("Batch032 Batch031 artifact digest mismatch")
    if verification.get("artifact_size_bytes") != 152375 or verification.get("zip_entry_count") != 156:
        errors.append("Batch032 Batch031 artifact size/entry count mismatch")
    if verification.get("manifest_failure_count") != 0 or verification.get("unsafe_path_count") != 0 or verification.get("duplicate_path_count") != 0:
        errors.append("Batch032 Batch031 artifact path/manifest custody failed")
    if verification != post_verification:
        errors.append("Batch032 post-level Batch031 artifact verification does not match batch-level record")
    if batch031_state.get("status") != "PASS_WITH_BATCH031_HARNESS_V9_EXECUTION_BLOCKED":
        errors.append("Batch032 did not preserve official Batch031 status")
    if batch031_state.get("harness_v9_executed") is not True or batch031_state.get("harness_v9_execution_status") != "PASS":
        errors.append("Batch032 requires official Batch031 executed harness telemetry")
    if batch031_state.get("harness_v9_verified") is not False or batch031_state.get("issue_derived_repair_feasibility") is not False:
        errors.append("Batch032 cannot start from already-verified Batch031 feasibility")

    if execution_classification.get("status") != "PASS" or safe_classification.get("status") != "PASS":
        errors.append("Batch032 safe-directory classification records are not PASS")
    variants = safe_classification.get("variant_classifications", [])
    source_root = next((item for item in variants if item.get("variant_id") == "source_root_no_git_dir_python_module"), {})
    if source_root.get("precondition_classification") != "provider_git_safe_directory_precondition":
        errors.append("Batch032 did not classify source-root safe.directory failure as provider precondition")
    if source_root.get("returncode") != 123:
        errors.append("Batch032 source-root Batch031 variant return code was not preserved")
    if not source_root.get("stderr_sha256"):
        errors.append("Batch032 source-root safe.directory stderr hash missing")
    if source_root.get("target_aligned_issue_failure") is not False or source_root.get("repair_target_counted") is not False:
        errors.append("Batch032 treated safe.directory precondition as target reproduction or repair target")
    required_terms = {"fatal: detected dubious ownership", "safe.directory", "dubious ownership in repository"}
    if not required_terms.issubset(set(safe_policy.get("environment_precondition_terms", []))):
        errors.append("Batch032 safe-directory precondition terms incomplete")
    if safe_policy.get("provider_git_safe_directory_precondition_is_target_reproduction") is not False:
        errors.append("Batch032 safe-directory policy permits target reproduction classification")

    provider_unavailable = state.get("exact_blocker") == "docker_runtime_provider_unavailable"
    if normalization.get("provider_only_environment_normalization") is not True:
        errors.append("Batch032 normalization is not recorded as provider-only")
    if normalization.get("source_mutation") is True or normalization.get("test_mutation") is True:
        errors.append("Batch032 safe.directory normalization mutated source or tests")
    if not provider_unavailable:
        if normalization.get("status") != "PASS":
            errors.append("Batch032 provider normalization did not pass when provider execution was available")
        if normalization.get("source_head_unchanged") is not True:
            errors.append("Batch032 selected source HEAD changed during normalization")
        if normalization.get("source_files_unchanged") is not True or normalization.get("tests_unchanged") is not True:
            errors.append("Batch032 source/test unchanged flags failed")
    if provider_context.get("relative_git_dir_active_command_context_used") is True or execution.get("relative_git_dir_active_command_context_used") is True or pre_repair.get("relative_git_dir_active_command_context_used") is True:
        errors.append("Batch032 used relative GIT_DIR=.git as an active command context")
    if execution_policy.get("relative_git_dir_active_command_context_allowed") is not False:
        errors.append("Batch032 execution policy allows relative GIT_DIR")
    if firewall.get("status") != "PASS":
        errors.append("Batch032 decision-time firewall failed")
    for key in ["fixed_revision_accessed", "gold_patch_accessed", "future_pr_accessed", "later_outcome_evidence_accessed"]:
        if firewall.get(key) is not False:
            errors.append(f"Batch032 forbidden evidence flag set: {key}")
    if claim.get("repair_ran") is not False or claim.get("patch_generated") is not False or claim.get("patch_authorized") is not False or claim.get("patch_attempted") is not False:
        errors.append("Batch032 ran repair or patch before target-aligned harness verification")
    if claim.get("matched_null_ran") is not False or claim.get("psa82_permutation_null_ran") is not False or claim.get("structured_fragility_diagnostic_ran") is not False:
        errors.append("Batch032 ran downstream diagnostics without patch candidate")
    if claim.get("native_repair_episode_count") != 4 or claim.get("issue_derived_repair_episode_count") != 0:
        errors.append("Batch032 changed repair episode counts")
    if claim.get("full_scoring") != "NOT_RUN/disallowed" or claim.get("memory_lift") != "not_demonstrated" or claim.get("self_maintaining_software") != "false/not_demonstrated":
        errors.append("Batch032 claim boundary overclaim")
    if state.get("current_protocol") != "v2.13":
        errors.append("Batch032 changed current protocol")
    if state.get("issue_derived_repair_feasibility") is True and pre_repair.get("target_aligned_pre_repair_failure_reproduced") is not True:
        errors.append("Batch032 issue-derived feasibility true without target-aligned verification")
    if feasibility.get("issue_derived_repair_feasibility") != state.get("issue_derived_repair_feasibility"):
        errors.append("Batch032 feasibility record disagrees with state")
    if triage.get("new_harness_or_fixture_created") is not False:
        errors.append("Batch032 created a new harness or fixture")
    if triage.get("repair_generation_authorized") is True and pre_repair.get("target_aligned_pre_repair_failure_reproduced") is not True:
        errors.append("Batch032 authorized repair generation without target-aligned failure")
    if ledger.get("hash_chain_valid") is not True or ledger.get("repair_or_patch_before_harness_v9_verification") is not False:
        errors.append("Batch032 proof ledger invalid")
    if language.get("status") != "PASS":
        errors.append("Batch032 public language audit failed")
    if minimality.get("status") != "PASS" or minimality.get("recursive_prior_batch_packaging_detected") is not False:
        errors.append("Batch032 artifact minimality failed")
    if budget.get("status") != "PASS":
        errors.append("Batch032 artifact budget failed")
    for path in list(BATCH032_DIR.glob("*.json")) + list(BATCH032_DIR.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        if any(marker in text for marker in ["1.45", "wiggle_room", "closure_tolerance", "residual_tolerance"]):
            errors.append(f"Batch032 introduced forbidden tolerance marker in {path.name}")
    return errors


def audit_batch033_records() -> list[str]:
    errors: list[str] = []
    for name in BATCH033_REQUIRED:
        if not (BATCH033_DIR / name).is_file():
            errors.append(f"batch033 missing required file {name}")
    if errors:
        return errors
    if verify_manifest(BATCH033_DIR).get("status") != "PASS":
        errors.append("batch033 manifest mismatch")

    batch032_state = read_json(BATCH032_DIR / "consolidated_state_clean_replication_batch_032.json")
    state = read_json(BATCH033_DIR / "consolidated_state_clean_replication_batch_033.json")
    ingest = read_json(BATCH033_DIR / "batch032_artifact_ingest_summary.json")
    verification = read_json(BATCH033_DIR / "batch032_artifact_verification.json")
    post_ingest = read_json(POST_DIR / "batch032_artifact_ingest_summary.json")
    post_verification = read_json(POST_DIR / "batch032_artifact_verification.json")
    target_summary = read_json(BATCH033_DIR / "batch032_target_not_reproduced_summary.json")
    policy = read_json(BATCH033_DIR / "batch033_issue_seed_retargeting_policy.json")
    analysis = read_json(BATCH033_DIR / "batch033_issue_seed_retargeting_analysis.json")
    v10_policy = read_json(BATCH033_DIR / "batch033_harness_v10_design_policy.json")
    generation = read_json(BATCH033_DIR / "batch033_harness_v10_generation_result.json")
    firewall = read_json(BATCH033_DIR / "batch033_decision_time_evidence_firewall.json")
    feasibility = read_json(BATCH033_DIR / "issue_derived_repair_feasibility_batch033.json")
    claim = read_json(BATCH033_DIR / "claim_boundary_batch033.json")
    ledger = read_json(BATCH033_DIR / "proof_obligations_ledger_batch033.json")
    language = read_json(BATCH033_DIR / "public_language_audit_batch033.json")
    minimality = read_json(BATCH033_DIR / "artifact_minimality_audit.json")
    budget = read_json(BATCH033_DIR / "artifact_payload_budget.json")

    if ingest.get("status") != "PASS" or verification.get("status") != "PASS":
        errors.append("Batch033 did not record Batch032 artifact custody before retargeting logic")
    if verification.get("artifact_name") != "post_v2_37_hardening_batch032_safe_directory_precondition_artifacts":
        errors.append("Batch033 Batch032 artifact name mismatch")
    if verification.get("artifact_id") != 8094822869 or verification.get("workflow_run_id") != 28751525030:
        errors.append("Batch033 Batch032 artifact identity mismatch")
    if verification.get("workflow_head_sha") != "2224875266501ce96011249bbe833c89314514e6":
        errors.append("Batch033 Batch032 head SHA mismatch")
    if verification.get("artifact_sha256") != "2c5fedb6d0003ba3cd8d54eefd4d3daa9355bae842aab60007a877db5c628000":
        errors.append("Batch033 Batch032 artifact digest mismatch")
    if verification.get("artifact_size_bytes") != 152417 or verification.get("zip_entry_count") != 157:
        errors.append("Batch033 Batch032 artifact size/entry count mismatch")
    if verification.get("unsafe_path_count") != 0 or verification.get("duplicate_path_count") != 0 or verification.get("pycache_pyc_payload_count") != 0:
        errors.append("Batch033 Batch032 artifact path hygiene failed")
    if verification.get("artifact_sha256sums_checked") != 156 or verification.get("batch032_sha256sums_checked") != 21 or verification.get("post_sha256sums_checked") != 133:
        errors.append("Batch033 Batch032 manifest coverage mismatch")
    if verification.get("manifest_failure_count") != 0:
        errors.append("Batch033 Batch032 manifest failures recorded")
    if ingest != post_ingest or verification != post_verification:
        errors.append("Batch033 post-level Batch032 custody records do not match batch-level records")

    if batch032_state.get("status") != "PASS_WITH_BATCH032_HARNESS_V9_TARGET_NOT_REPRODUCED":
        errors.append("Batch033 did not preserve official Batch032 status")
    if batch032_state.get("exact_blocker") != "issue_seed_not_reproduced_by_current_harness":
        errors.append("Batch033 did not preserve official Batch032 blocker")
    if state.get("batch032_status_preserved") != batch032_state.get("status"):
        errors.append("Batch033 state does not preserve Batch032 status")
    if state.get("batch032_exact_blocker_preserved") != batch032_state.get("exact_blocker"):
        errors.append("Batch033 state does not preserve Batch032 blocker")
    if target_summary.get("status") != "PASS":
        errors.append("Batch033 target-not-reproduced summary missing PASS")
    if target_summary.get("harness_v9_executed") is not True or target_summary.get("harness_v9_execution_status") != "PASS":
        errors.append("Batch033 target summary does not preserve v9 execution")
    if target_summary.get("harness_v9_verified") is not False or target_summary.get("target_intent_matching_result") is not False:
        errors.append("Batch033 target summary overstates v9 verification")
    if target_summary.get("issue_derived_repair_feasibility") is not False:
        errors.append("Batch033 target summary changed issue-derived feasibility")
    if target_summary.get("safe_directory_classification") != "provider_git_safe_directory_precondition":
        errors.append("Batch033 did not preserve safe.directory provider-precondition classification")
    if target_summary.get("safe_directory_is_target_reproduction") is not False:
        errors.append("Batch033 treated safe.directory as target reproduction")
    if target_summary.get("normalized_variants_all_return_zero") is not True:
        errors.append("Batch033 target summary does not preserve normalized zero-return variants")
    if target_summary.get("target_indicator_seen_after_normalization") is not False:
        errors.append("Batch033 target summary saw target indicator after normalization")

    valid_classifications = {
        "issue_requires_more_specific_decision_time_fixture",
        "issue_seed_not_reproduced_by_current_harness",
        "issue_derived_seed_retired_no_repair_feasibility",
        "issue_seed_retargeting_possible_from_allowed_evidence",
    }
    if policy.get("status") != "PASS" or analysis.get("status") != "PASS":
        errors.append("Batch033 retargeting policy/analysis not PASS")
    if analysis.get("classification") not in valid_classifications:
        errors.append("Batch033 retargeting classification invalid")
    if state.get("issue_seed_retargeting_classification") != analysis.get("classification"):
        errors.append("Batch033 state retargeting classification mismatch")
    if policy.get("repair_or_patch_authorized") is not False or policy.get("matched_null_authorized") is not False:
        errors.append("Batch033 retargeting policy authorized repair or matched-null")
    if policy.get("v10_execution_authorized_in_batch033") is not False:
        errors.append("Batch033 policy authorized v10 execution in Batch033")
    if analysis.get("forbidden_evidence_used") is not False:
        errors.append("Batch033 analysis used forbidden evidence")
    if analysis.get("repair_or_patch_authorized") is not False or analysis.get("issue_derived_repair_feasibility") is not False:
        errors.append("Batch033 analysis authorized repair/feasibility")

    if analysis.get("retargeting_possible_from_allowed_evidence") is True:
        if analysis.get("classification") != "issue_seed_retargeting_possible_from_allowed_evidence":
            errors.append("Batch033 retargeting possible without matching classification")
        if analysis.get("relative_git_dir_target_intent_variant_count", 0) <= 0:
            errors.append("Batch033 retargeting possible without relative-GIT_DIR target-intent evidence")
        if analysis.get("requires_separate_gated_v10_execution") is not True:
            errors.append("Batch033 retargeting possible without separate v10 gate")
        if v10_policy.get("status") != "PASS":
            errors.append("Batch033 v10 design policy not PASS")
        if generation.get("status") != "PASS_DESIGN_ONLY":
            errors.append("Batch033 v10 generation result is not design-only PASS")
        if generation.get("design_scaffold", {}).get("requires_separate_gated_execution") is not True:
            errors.append("Batch033 v10 scaffold lacks separate gate requirement")
        if not generation.get("allowed_evidence_hash"):
            errors.append("Batch033 v10 design missing allowed evidence hash")
    else:
        if state.get("status") != "PASS_WITH_BATCH033_ISSUE_DERIVED_SEED_RETIRED":
            errors.append("Batch033 retired-seed status mismatch")
        if v10_policy.get("status") != "NOT_RUN" or generation.get("status") != "NOT_RUN":
            errors.append("Batch033 v10 records should be NOT_RUN when retargeting is not possible")

    if generation.get("executable_harness_generated") is not False or generation.get("harness_v10_executed") is not False:
        errors.append("Batch033 generated or executed a v10 harness")
    if generation.get("command_logs_recorded") is not False or generation.get("target_intent_telemetry_recorded") is not False:
        errors.append("Batch033 claimed v10 execution telemetry without execution")
    if v10_policy.get("repair_or_patch_authorized") is not False or v10_policy.get("execution_in_batch033") is not False:
        errors.append("Batch033 v10 policy authorized execution or repair")

    if firewall.get("status") != "PASS":
        errors.append("Batch033 decision-time firewall failed")
    for key in [
        "fixed_revision_accessed",
        "gold_patch_accessed",
        "future_pr_accessed",
        "later_commit_message_accessed",
        "later_outcome_evidence_accessed",
        "fixed_version_patch_accessed",
        "solution_sections_used",
    ]:
        if firewall.get(key) is not False:
            errors.append(f"Batch033 forbidden evidence flag set: {key}")
    if feasibility.get("issue_derived_repair_feasibility") is not False or feasibility.get("repair_ran") is not False:
        errors.append("Batch033 feasibility record ran repair or set feasibility true")
    if feasibility.get("patch_generated") is not False or feasibility.get("matched_null_ran") is not False:
        errors.append("Batch033 feasibility record generated patch or matched-null")
    if claim.get("repair_ran") is not False or claim.get("patch_generated") is not False or claim.get("patch_authorized") is not False or claim.get("patch_attempted") is not False:
        errors.append("Batch033 claim boundary shows repair/patch activity")
    if claim.get("matched_null_ran") is not False or claim.get("psa82_permutation_null_ran") is not False or claim.get("structured_fragility_diagnostic_ran") is not False:
        errors.append("Batch033 claim boundary shows downstream diagnostics")
    if claim.get("native_repair_episode_count") != 4 or claim.get("issue_derived_repair_episode_count") != 0:
        errors.append("Batch033 repair episode counts changed")
    if claim.get("full_scoring") != "NOT_RUN/disallowed" or claim.get("memory_lift") != "not_demonstrated" or claim.get("self_maintaining_software") != "false/not_demonstrated":
        errors.append("Batch033 claim boundary overclaim")
    if claim.get("no_unregistered_tolerance_added") is not True:
        errors.append("Batch033 unregistered tolerance flag not true")
    if ledger.get("status") != "PASS" or ledger.get("hash_chain_valid") is not True:
        errors.append("Batch033 proof ledger invalid")
    if ledger.get("repair_or_patch_before_harness_verification") is not False or ledger.get("matched_null_without_patch_candidate") is not False:
        errors.append("Batch033 proof ledger permits forbidden downstream work")
    if language.get("status") != "PASS":
        errors.append("Batch033 public language audit failed")
    if minimality.get("status") != "PASS" or minimality.get("recursive_prior_batch_packaging_detected") is not False:
        errors.append("Batch033 artifact minimality failed")
    if budget.get("status") != "PASS":
        errors.append("Batch033 artifact budget failed")
    if state.get("current_protocol") != "v2.13":
        errors.append("Batch033 changed current protocol")
    if state.get("repair_ran") is not False or state.get("patch_generated") is not False or state.get("patch_authorized") is not False or state.get("patch_attempted") is not False:
        errors.append("Batch033 state shows repair or patch activity")
    if state.get("matched_null_diagnostic_run_count") != 0:
        errors.append("Batch033 state shows matched-null diagnostic activity")
    if state.get("psa82_permutation_null_status") != "NOT_RUN_NO_PATCH_CANDIDATE" or state.get("structured_fragility_diagnostic_status") != "NOT_RUN_NO_PATCH_CANDIDATE":
        errors.append("Batch033 state changed downstream diagnostic status")
    if state.get("native_repair_episode_count") != 4 or state.get("issue_derived_repair_episode_count") != 0:
        errors.append("Batch033 state repair episode counts changed")
    for path in list(BATCH033_DIR.glob("*.json")) + list(BATCH033_DIR.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        if any(marker in text for marker in ["1.45", "wiggle_room", "closure_tolerance", "residual_tolerance"]):
            errors.append(f"Batch033 introduced forbidden tolerance marker in {path.name}")
    return errors


def audit_batch034_records() -> list[str]:
    errors: list[str] = []
    for name in BATCH034_REQUIRED:
        if not (BATCH034_DIR / name).is_file():
            errors.append(f"batch034 missing required file {name}")
    if errors:
        return errors
    if verify_manifest(BATCH034_DIR).get("status") != "PASS":
        errors.append("batch034 manifest mismatch")

    batch033_state = read_json(BATCH033_DIR / "consolidated_state_clean_replication_batch_033.json")
    state = read_json(BATCH034_DIR / "consolidated_state_clean_replication_batch_034.json")
    ingest = read_json(BATCH034_DIR / "batch033_artifact_ingest_summary.json")
    verification = read_json(BATCH034_DIR / "batch033_artifact_verification.json")
    post_ingest = read_json(POST_DIR / "batch033_artifact_ingest_summary.json")
    post_verification = read_json(POST_DIR / "batch033_artifact_verification.json")
    design = read_json(BATCH034_DIR / "batch033_retargeting_design_summary.json")
    materialization_policy = read_json(BATCH034_DIR / "batch034_harness_v10_materialization_policy.json")
    materialization = read_json(BATCH034_DIR / "batch034_harness_v10_materialization_result.json")
    stimulus_policy = read_json(BATCH034_DIR / "batch034_relative_git_dir_issue_stimulus_policy.json")
    command_context = read_json(BATCH034_DIR / "batch034_provider_command_context_audit.json")
    execution_policy = read_json(BATCH034_DIR / "batch034_harness_v10_execution_policy.json")
    execution = read_json(BATCH034_DIR / "batch034_harness_v10_execution_result.json")
    pre_repair = read_json(BATCH034_DIR / "batch034_harness_v10_pre_repair_verification.json")
    target = read_json(BATCH034_DIR / "batch034_target_intent_match_report.json")
    firewall = read_json(BATCH034_DIR / "batch034_decision_time_evidence_firewall.json")
    feasibility = read_json(BATCH034_DIR / "issue_derived_repair_feasibility_batch034.json")
    claim = read_json(BATCH034_DIR / "claim_boundary_batch034.json")
    ledger = read_json(BATCH034_DIR / "proof_obligations_ledger_batch034.json")
    language = read_json(BATCH034_DIR / "public_language_audit_batch034.json")
    minimality = read_json(BATCH034_DIR / "artifact_minimality_audit.json")
    budget = read_json(BATCH034_DIR / "artifact_payload_budget.json")

    if ingest.get("status") != "PASS" or verification.get("status") != "PASS":
        errors.append("Batch034 did not record Batch033 artifact custody before v10 logic")
    expected_artifact = {
        "artifact_name": "post_v2_37_hardening_batch033_issue_seed_retargeting_artifacts",
        "artifact_id": 8095537459,
        "workflow_run_id": 28754057140,
        "workflow_head_sha": "03433a334ca2cae7947d5578acc9671841fde7a3",
        "artifact_sha256": "83921f4da10792d677fe4852ed2827cad961bf9f73598430530ef979762f310a",
        "artifact_size_bytes": 152879,
        "zip_entry_count": 155,
        "unsafe_path_count": 0,
        "duplicate_path_count": 0,
        "pycache_pyc_payload_count": 0,
        "artifact_sha256sums_checked": 154,
        "batch033_sha256sums_checked": 17,
        "post_sha256sums_checked": 135,
        "manifest_failure_count": 0,
    }
    for key, value in expected_artifact.items():
        if verification.get(key) != value:
            errors.append(f"Batch034 Batch033 artifact verification mismatch for {key}")
    if ingest.get("artifact_sha256") != expected_artifact["artifact_sha256"] or ingest.get("artifact_size_bytes") != 152879:
        errors.append("Batch034 Batch033 ingest identity mismatch")
    if ingest != post_ingest or verification != post_verification:
        errors.append("Batch034 post-level Batch033 custody records do not match batch-level records")

    if batch033_state.get("status") != "PASS_WITH_BATCH033_RETARGETING_DESIGN_ONLY":
        errors.append("Batch034 did not preserve official Batch033 status")
    if batch033_state.get("exact_blocker") != "issue_seed_retargeting_requires_separate_gated_v10_execution":
        errors.append("Batch034 did not preserve official Batch033 blocker")
    if state.get("batch033_status_preserved") != batch033_state.get("status"):
        errors.append("Batch034 state does not preserve Batch033 status")
    if state.get("batch033_exact_blocker_preserved") != batch033_state.get("exact_blocker"):
        errors.append("Batch034 state does not preserve Batch033 blocker")
    if design.get("status") != "PASS":
        errors.append("Batch034 design summary not PASS")
    if design.get("batch033_status") != "PASS_WITH_BATCH033_RETARGETING_DESIGN_ONLY":
        errors.append("Batch034 design summary ignored Batch033 design-only boundary")
    if design.get("batch033_exact_blocker") != "issue_seed_retargeting_requires_separate_gated_v10_execution":
        errors.append("Batch034 design summary blocker mismatch")
    if design.get("batch033_classification") != "issue_seed_retargeting_possible_from_allowed_evidence":
        errors.append("Batch034 design summary classification mismatch")
    if design.get("retargeting_possible_from_allowed_evidence") is not True:
        errors.append("Batch034 design summary did not preserve retargeting-possible classification")
    if design.get("harness_v10_design_policy_status") != "PASS" or design.get("harness_v10_generation_status") != "PASS_DESIGN_ONLY":
        errors.append("Batch034 design summary did not preserve v10 design-only records")
    if design.get("executable_v10_harness_generated_in_batch033") is not False or design.get("harness_v10_executed_in_batch033") is not False:
        errors.append("Batch034 design summary claims Batch033 generated/executed v10")
    if design.get("repair_or_patch_authorized_in_batch033") is not False:
        errors.append("Batch034 design summary authorized Batch033 repair")

    harness_path = Path(str(materialization.get("harness_path", "")))
    if materialization_policy.get("status") != "PASS" or materialization.get("status") != "PASS":
        errors.append("Batch034 v10 materialization not PASS")
    if materialization_policy.get("repair_or_patch_authorized") is not False:
        errors.append("Batch034 materialization policy authorized repair or patch")
    if materialization.get("executable_harness_generated") is not True:
        errors.append("Batch034 did not materialize executable v10 harness")
    if not harness_path.is_file():
        errors.append("Batch034 v10 harness path missing")
    elif materialization.get("harness_sha256") != sha256_file(harness_path):
        errors.append("Batch034 v10 harness SHA mismatch")
    if materialization.get("source_mutation") is not False or materialization.get("test_mutation") is not False:
        errors.append("Batch034 v10 materialization mutated source or tests")
    if materialization.get("decision_time_only") is not True:
        errors.append("Batch034 v10 materialization is not decision-time-only")
    if materialization.get("relative_git_dir_allowed_only_as_issue_stimulus") is not True:
        errors.append("Batch034 materialization did not constrain relative GIT_DIR to issue stimulus")

    if stimulus_policy.get("status") != "PASS":
        errors.append("Batch034 relative-GIT_DIR stimulus policy not PASS")
    if stimulus_policy.get("candidate_command") != "GIT_DIR=.git python -m darker --check src":
        errors.append("Batch034 v10 candidate command mismatch")
    if stimulus_policy.get("allowed_only_inside_v10_issue_stimulus_harness") is not True:
        errors.append("Batch034 did not restrict relative GIT_DIR to issue stimulus harness")
    if stimulus_policy.get("allowed_as_general_provider_context") is not False:
        errors.append("Batch034 allowed relative GIT_DIR as general provider context")

    if execution_policy.get("status") != "PASS":
        errors.append("Batch034 execution policy not PASS")
    if execution_policy.get("requires_v10_materialization_before_execution") is not True:
        errors.append("Batch034 execution policy does not require materialization before execution")
    if execution_policy.get("requires_selected_source_head") != "a2d13656adfaa010fb6c7339087f3347ad2b815a":
        errors.append("Batch034 execution policy selected source HEAD mismatch")
    if execution_policy.get("repair_authorized_in_batch034") is not False or execution_policy.get("patch_generation_authorized_in_batch034") is not False:
        errors.append("Batch034 execution policy authorized repair or patch")

    if command_context.get("relative_git_dir_general_provider_context_used") is True:
        errors.append("Batch034 used relative GIT_DIR as general provider context")
    if state.get("relative_git_dir_general_provider_context_used") is not False:
        errors.append("Batch034 state reports relative GIT_DIR as general provider context")
    if execution.get("relative_git_dir_general_provider_context_used") is not False:
        errors.append("Batch034 execution used relative GIT_DIR as general provider context")

    if firewall.get("status") != "PASS":
        errors.append("Batch034 decision-time evidence firewall failed")
    for key in [
        "fixed_revision_accessed",
        "gold_patch_accessed",
        "future_pr_accessed",
        "later_commit_message_accessed",
        "later_outcome_evidence_accessed",
        "fixed_version_patch_accessed",
        "solution_sections_used",
    ]:
        if firewall.get(key) is not False:
            errors.append(f"Batch034 forbidden evidence flag set: {key}")

    executed = state.get("harness_v10_executed") is True
    verified = state.get("harness_v10_verified") is True
    if executed:
        if state.get("source_head_verified_before_execution") is not True:
            errors.append("Batch034 executed v10 without verifying selected source HEAD")
        if command_context.get("status") != "PASS":
            errors.append("Batch034 command context not PASS despite execution")
        if execution.get("status") != "PASS" or execution.get("command") != "GIT_DIR=.git python -m darker --check src":
            errors.append("Batch034 execution result invalid")
        if not execution.get("stdout_sha256") or not execution.get("stderr_sha256"):
            errors.append("Batch034 execution missing stdout/stderr hashes")
        if pre_repair.get("harness_v10_executed") is not True:
            errors.append("Batch034 pre-repair verification did not record execution")
        if execution.get("relative_git_dir_issue_stimulus_used") is not True or pre_repair.get("relative_git_dir_issue_stimulus_used") is not True:
            errors.append("Batch034 execution did not record relative-GIT_DIR issue stimulus")
        if target.get("status") not in {"PASS", "BLOCK"}:
            errors.append("Batch034 target-intent report status invalid")
    else:
        if pre_repair.get("harness_v10_executed") is True:
            errors.append("Batch034 pre-repair verification claims execution but state does not")

    if verified:
        if pre_repair.get("status") != "PASS":
            errors.append("Batch034 verified v10 without PASS pre-repair verification")
        if feasibility.get("issue_derived_repair_feasibility") is not True or state.get("issue_derived_repair_feasibility") is not True:
            errors.append("Batch034 verified v10 without issue-derived feasibility")
        if state.get("exact_blocker") is not None:
            errors.append("Batch034 verified v10 but retained blocker")
    else:
        if feasibility.get("issue_derived_repair_feasibility") is not False or state.get("issue_derived_repair_feasibility") is not False:
            errors.append("Batch034 set feasibility without verified v10")
        if state.get("exact_blocker") not in {
            "docker_runtime_provider_unavailable",
            "provider_source_checkout_failed",
            "provider_harness_v10_execution_failed",
            "manual_lock_environment_materialization_failed",
            "safe_directory_normalization_failed",
            "harness_v10_file_missing",
            "issue_seed_not_reproduced_by_v10_harness",
            "harness_v10_execution_not_run",
            "provider_source_commit_mismatch",
            "harness_v10_execution_blocked",
        }:
            errors.append(f"Batch034 blocker invalid: {state.get('exact_blocker')}")

    for record_name, record in [
        ("state", state),
        ("claim", claim),
        ("feasibility", feasibility),
    ]:
        if record.get("repair_ran") is not False or record.get("patch_generated") is not False:
            errors.append(f"Batch034 {record_name} shows repair or patch activity")
        if record.get("matched_null_ran") is True:
            errors.append(f"Batch034 {record_name} shows matched-null activity")
    if state.get("patch_authorized") is not False or state.get("patch_attempted") is not False:
        errors.append("Batch034 state shows patch authorization/attempt")
    if state.get("matched_null_diagnostic_run_count") != 0:
        errors.append("Batch034 matched-null diagnostic ran")
    if state.get("psa82_permutation_null_status") != "NOT_RUN_NO_PATCH_CANDIDATE" or state.get("structured_fragility_diagnostic_status") != "NOT_RUN_NO_PATCH_CANDIDATE":
        errors.append("Batch034 downstream diagnostic status mismatch")
    if claim.get("psa82_permutation_null_ran") is not False or claim.get("structured_fragility_diagnostic_ran") is not False:
        errors.append("Batch034 claim boundary shows downstream diagnostic activity")
    if state.get("native_repair_episode_count") != 4 or state.get("issue_derived_repair_episode_count") != 0:
        errors.append("Batch034 repair episode counts changed")
    if claim.get("native_repair_episode_count") != 4 or claim.get("issue_derived_repair_episode_count") != 0:
        errors.append("Batch034 claim repair episode counts changed")
    if state.get("full_scoring") != "NOT_RUN/disallowed" or state.get("memory_lift") != "not_demonstrated" or state.get("self_maintaining_software") != "false/not_demonstrated":
        errors.append("Batch034 state overclaims")
    if claim.get("full_scoring") != "NOT_RUN/disallowed" or claim.get("memory_lift") != "not_demonstrated" or claim.get("self_maintaining_software") != "false/not_demonstrated":
        errors.append("Batch034 claim boundary overclaims")
    if state.get("current_protocol") != "v2.13":
        errors.append("Batch034 changed current protocol")
    if ledger.get("status") != "PASS" or ledger.get("hash_chain_valid") is not True:
        errors.append("Batch034 proof ledger invalid")
    if ledger.get("repair_or_patch_before_harness_v10_verification") is not False or ledger.get("matched_null_without_patch_candidate") is not False:
        errors.append("Batch034 proof ledger permits forbidden downstream work")
    if language.get("status") != "PASS":
        errors.append("Batch034 public language audit failed")
    if minimality.get("status") != "PASS" or minimality.get("recursive_prior_batch_packaging_detected") is not False:
        errors.append("Batch034 artifact minimality failed")
    if budget.get("status") != "PASS":
        errors.append("Batch034 artifact budget failed")
    for path in list(BATCH034_DIR.glob("*.json")) + list(BATCH034_DIR.glob("*.md")) + list(BATCH034_DIR.glob("*.py")):
        text = path.read_text(encoding="utf-8")
        if any(marker in text for marker in ["1.45", "wiggle_room", "closure_tolerance", "residual_tolerance"]):
            errors.append(f"Batch034 introduced forbidden tolerance marker in {path.name}")
    return errors


def audit_batch035_records() -> list[str]:
    errors: list[str] = []
    for name in BATCH035_REQUIRED:
        if not (BATCH035_DIR / name).is_file():
            errors.append(f"batch035 missing required file {name}")
    if errors:
        return errors
    if verify_manifest(BATCH035_DIR).get("status") != "PASS":
        errors.append("batch035 manifest mismatch")

    batch034_state = read_json(BATCH034_DIR / "consolidated_state_clean_replication_batch_034.json")
    state = read_json(BATCH035_DIR / "consolidated_state_clean_replication_batch_035.json")
    ingest = read_json(BATCH035_DIR / "batch034_artifact_ingest_summary.json")
    verification = read_json(BATCH035_DIR / "batch034_artifact_verification.json")
    post_ingest = read_json(POST_DIR / "batch034_artifact_ingest_summary.json")
    post_verification = read_json(POST_DIR / "batch034_artifact_verification.json")
    preservation = read_json(BATCH035_DIR / "batch034_v10_verification_preservation.json")
    authorization = read_json(BATCH035_DIR / "batch035_repair_authorization_gate.json")
    policy = read_json(BATCH035_DIR / "batch035_candidate_generation_policy.json")
    inspection = read_json(BATCH035_DIR / "batch035_source_inspection_summary.json")
    generation = read_json(BATCH035_DIR / "batch035_repair_candidate_generation_result.json")
    firewall = read_json(BATCH035_DIR / "batch035_decision_time_evidence_firewall.json")
    patch_application = read_json(BATCH035_DIR / "batch035_patch_application_result.json")
    patch_scope = read_json(BATCH035_DIR / "batch035_patch_scope_audit.json")
    post_repair = read_json(BATCH035_DIR / "batch035_post_repair_target_replay.json")
    duplicate = read_json(BATCH035_DIR / "batch035_duplicate_clean_replay.json")
    validation = read_json(BATCH035_DIR / "batch035_issue_derived_repair_validation.json")
    feasibility = read_json(BATCH035_DIR / "issue_derived_repair_feasibility_batch035.json")
    claim = read_json(BATCH035_DIR / "claim_boundary_batch035.json")
    ledger = read_json(BATCH035_DIR / "proof_obligations_ledger_batch035.json")
    closure = read_json(BATCH035_DIR / "batch035_controller_audit_closure_check.json")
    psa82 = read_json(BATCH035_DIR / "batch035_psa82_permutation_null_diagnostic.json")
    fragility = read_json(BATCH035_DIR / "batch035_structured_fragility_diagnostic.json")
    language = read_json(BATCH035_DIR / "public_language_audit_batch035.json")
    minimality = read_json(BATCH035_DIR / "artifact_minimality_audit.json")
    budget = read_json(BATCH035_DIR / "artifact_payload_budget.json")

    expected_artifact = {
        "artifact_name": "post_v2_37_hardening_batch034_v10_harness_execution_artifacts",
        "artifact_id": 8096378284,
        "workflow_run_id": 28756943601,
        "workflow_head_sha": "edebe0ac81361a0558965785445ff9fa3b188a17",
        "artifact_sha256": "2cbbc5b5c76acbe4186cd4f13a35ec99594a7acde93ce278eee27cae9db5978c",
        "artifact_size_bytes": 157369,
        "zip_entry_count": 162,
        "unsafe_path_count": 0,
        "duplicate_path_count": 0,
        "pycache_pyc_payload_count": 0,
        "artifact_sha256sums_checked": 161,
        "batch034_sha256sums_checked": 22,
        "post_sha256sums_checked": 137,
        "manifest_failure_count": 0,
    }
    if ingest.get("status") != "PASS" or verification.get("status") != "PASS":
        errors.append("Batch035 did not record Batch034 artifact custody before repair logic")
    for key, value in expected_artifact.items():
        if verification.get(key) != value:
            errors.append(f"Batch035 Batch034 artifact verification mismatch for {key}")
    if ingest.get("artifact_sha256") != expected_artifact["artifact_sha256"] or ingest.get("artifact_size_bytes") != 157369:
        errors.append("Batch035 Batch034 ingest identity mismatch")
    if ingest != post_ingest or verification != post_verification:
        errors.append("Batch035 post-level Batch034 custody records do not match batch-level records")

    if batch034_state.get("status") != "PASS_WITH_BATCH034_HARNESS_V10_VERIFIED_REPAIR_NOT_RUN":
        errors.append("Batch035 did not start from verified official Batch034 state")
    if batch034_state.get("harness_v10_verified") is not True or batch034_state.get("target_intent_matching_result") is not True:
        errors.append("Batch035 Batch034 v10 verification prerequisites not preserved")
    if preservation.get("status") != "PASS":
        errors.append("Batch035 v10 preservation record not PASS")
    if preservation.get("issue_derived_repair_feasibility") is not True:
        errors.append("Batch035 did not preserve Batch034 issue-derived feasibility")
    if preservation.get("issue_derived_repair_episode_count") != 0:
        errors.append("Batch035 did not preserve Batch034 zero issue-derived episode count before repair")
    if preservation.get("selected_source_commit") != "a2d13656adfaa010fb6c7339087f3347ad2b815a":
        errors.append("Batch035 selected source commit mismatch")
    if preservation.get("verified_issue_stimulus_command") != "GIT_DIR=.git python -m darker --check src":
        errors.append("Batch035 verified issue stimulus command mismatch")

    if authorization.get("status") != "PASS" or authorization.get("repair_authorized") is not True:
        errors.append("Batch035 repair authorization gate did not pass from verified v10 evidence")
    if authorization.get("source_only_required") is not True or authorization.get("tests_may_be_modified") is not False:
        errors.append("Batch035 repair authorization gate weakened patch scope")
    if policy.get("status") != "PASS" or policy.get("source_only_patch_required") is not True:
        errors.append("Batch035 candidate generation policy invalid")
    if policy.get("fixed_revision_inspection_allowed") is not False or policy.get("gold_patch_inspection_allowed") is not False or policy.get("future_pr_or_later_commit_evidence_allowed") is not False:
        errors.append("Batch035 candidate policy allowed forbidden evidence")
    if inspection.get("status") != "PASS" or "src/darker/git.py" not in inspection.get("inspected_files", []):
        errors.append("Batch035 source inspection did not identify localized source file")
    if generation.get("status") != "PASS" or generation.get("candidate_generated") is not True:
        errors.append("Batch035 source-only patch candidate not generated")
    patch_path = Path(str(generation.get("patch_path", "")))
    if not patch_path.is_file():
        errors.append("Batch035 patch candidate path missing")
    elif generation.get("patch_sha256") != sha256_file(patch_path):
        errors.append("Batch035 patch candidate SHA mismatch")
    if generation.get("patch_non_empty") is not True or not patch_path.read_text(encoding="utf-8").strip():
        errors.append("Batch035 empty patch candidate")
    if generation.get("touched_files") != ["src/darker/git.py"] or generation.get("source_only") is not True or generation.get("tests_modified") is not False:
        errors.append("Batch035 patch candidate scope invalid")
    if generation.get("targets_git_context_handling_under_relative_git_dir_issue_stimulus") is not True:
        errors.append("Batch035 patch candidate does not target verified issue stimulus")
    if generation.get("oracle_gold_future_evidence_used") is not False:
        errors.append("Batch035 patch generation used forbidden evidence")

    if firewall.get("status") != "PASS":
        errors.append("Batch035 decision-time firewall failed")
    for key in [
        "fixed_revision_accessed",
        "gold_patch_accessed",
        "future_pr_accessed",
        "later_commit_message_accessed",
        "later_outcome_evidence_accessed",
        "fixed_version_patch_accessed",
        "solution_sections_used",
    ]:
        if firewall.get(key) is not False:
            errors.append(f"Batch035 forbidden evidence flag set: {key}")

    repair_validated = state.get("issue_derived_repair_validated") is True
    if patch_application.get("status") == "PASS":
        if patch_application.get("touched_files") != ["src/darker/git.py"]:
            errors.append("Batch035 patch application touched unexpected files")
        if patch_scope.get("status") != "PASS" or patch_scope.get("source_only") is not True or patch_scope.get("tests_modified") is not False:
            errors.append("Batch035 patch scope audit failed")
        if post_repair.get("status") != "PASS":
            errors.append("Batch035 patch applied but post-repair replay did not record PASS status")
        if repair_validated:
            if post_repair.get("target_failure_resolved") is not True:
                errors.append("Batch035 validated repair without post-repair target pass")
            if duplicate.get("status") != "PASS" or duplicate.get("duplicate_replay_passed") is not True:
                errors.append("Batch035 validated repair without duplicate clean replay")
            if validation.get("status") != "PASS" or validation.get("issue_derived_repair_validated") is not True:
                errors.append("Batch035 validation record not PASS for validated repair")
    else:
        if repair_validated:
            errors.append("Batch035 validated repair without patch application")

    if validation.get("issue_derived_repair_episode_count_increment_candidate") is True:
        if validation.get("issue_derived_repair_validated") is not True or post_repair.get("target_failure_resolved") is not True or duplicate.get("duplicate_replay_passed") is not True:
            errors.append("Batch035 issue-derived count increment candidate lacks empirical replay chain")
    if state.get("issue_derived_repair_episode_count") not in {0, 1}:
        errors.append("Batch035 issue-derived repair episode count invalid")
    if state.get("issue_derived_repair_episode_count") == 1 and not repair_validated:
        errors.append("Batch035 incremented issue-derived count without validated repair")
    if claim.get("issue_derived_repair_episode_count") != state.get("issue_derived_repair_episode_count"):
        errors.append("Batch035 claim/state issue-derived count mismatch")
    if feasibility.get("issue_derived_repair_episode_count") != state.get("issue_derived_repair_episode_count"):
        errors.append("Batch035 feasibility/state issue-derived count mismatch")
    if state.get("native_repair_episode_count") != 4 or claim.get("native_repair_episode_count") != 4:
        errors.append("Batch035 native repair episode count changed")
    if state.get("full_scoring") != "NOT_RUN/disallowed" or state.get("memory_lift") != "not_demonstrated" or state.get("self_maintaining_software") != "false/not_demonstrated":
        errors.append("Batch035 state overclaims")
    if claim.get("full_scoring") != "NOT_RUN/disallowed" or claim.get("memory_lift") != "not_demonstrated" or claim.get("self_maintaining_software") != "false/not_demonstrated":
        errors.append("Batch035 claim boundary overclaims")
    if state.get("current_protocol") != "v2.13":
        errors.append("Batch035 changed current protocol")
    if state.get("matched_null_diagnostic_run_count") != 0:
        errors.append("Batch035 matched-null ran unexpectedly")
    if closure.get("pass_logic_changed") is not False:
        errors.append("Batch035 closure diagnostic changed pass logic")
    if psa82.get("diagnostic_replaced_empirical_gate") is not False or fragility.get("diagnostic_replaced_empirical_gate") is not False:
        errors.append("Batch035 diagnostics replaced empirical gates")
    if ledger.get("status") != "PASS" or ledger.get("hash_chain_valid") is not True:
        errors.append("Batch035 proof ledger invalid")
    if ledger.get("issue_derived_count_increment_without_validation") is not False or ledger.get("repair_success_claim_from_candidate_generation_alone") is not False or ledger.get("diagnostics_replaced_empirical_gates") is not False:
        errors.append("Batch035 proof ledger permits overclaim")
    if language.get("status") != "PASS":
        errors.append("Batch035 public language audit failed")
    if minimality.get("status") != "PASS" or minimality.get("recursive_prior_batch_packaging_detected") is not False:
        errors.append("Batch035 artifact minimality failed")
    if budget.get("status") != "PASS":
        errors.append("Batch035 artifact budget failed")
    for path in list(BATCH035_DIR.glob("*.json")) + list(BATCH035_DIR.glob("*.md")) + list(BATCH035_DIR.glob("*.py")) + list(BATCH035_DIR.glob("*.diff")):
        text = path.read_text(encoding="utf-8")
        if any(marker in text for marker in ["1.45", "wiggle_room", "closure_tolerance", "residual_tolerance"]):
            errors.append(f"Batch035 introduced forbidden tolerance marker in {path.name}")
    return errors


def audit_batch036_records() -> list[str]:
    errors: list[str] = []
    for name in BATCH036_REQUIRED:
        if not (BATCH036_DIR / name).is_file():
            errors.append(f"batch036 missing required file {name}")
    if errors:
        return errors
    if verify_manifest(BATCH036_DIR).get("status") != "PASS":
        errors.append("batch036 manifest mismatch")

    batch035_state = read_json(BATCH035_DIR / "consolidated_state_clean_replication_batch_035.json")
    state = read_json(BATCH036_DIR / "consolidated_state_clean_replication_batch_036.json")
    ingest = read_json(BATCH036_DIR / "batch035_artifact_ingest_summary.json")
    verification = read_json(BATCH036_DIR / "batch035_artifact_verification.json")
    post_ingest = read_json(POST_DIR / "batch035_artifact_ingest_summary.json")
    post_verification = read_json(POST_DIR / "batch035_artifact_verification.json")
    preservation = read_json(BATCH036_DIR / "batch035_repair_attempt_preservation.json")
    decomposition = read_json(BATCH036_DIR / "batch036_post_repair_failure_decomposition.json")
    inspection = read_json(BATCH036_DIR / "batch036_source_inspection_refinement_summary.json")
    policy = read_json(BATCH036_DIR / "batch036_candidate_v2_generation_policy.json")
    generation = read_json(BATCH036_DIR / "batch036_repair_candidate_v2_generation_result.json")
    firewall = read_json(BATCH036_DIR / "batch036_decision_time_evidence_firewall.json")
    patch_application = read_json(BATCH036_DIR / "batch036_patch_v2_application_result.json")
    post_repair = read_json(BATCH036_DIR / "batch036_post_repair_target_replay_v2.json")
    duplicate = read_json(BATCH036_DIR / "batch036_duplicate_clean_replay_v2.json")
    validation = read_json(BATCH036_DIR / "batch036_issue_derived_repair_validation.json")
    feasibility = read_json(BATCH036_DIR / "issue_derived_repair_feasibility_batch036.json")
    claim = read_json(BATCH036_DIR / "claim_boundary_batch036.json")
    ledger = read_json(BATCH036_DIR / "proof_obligations_ledger_batch036.json")
    closure = read_json(BATCH036_DIR / "batch036_controller_audit_closure_check.json")
    psa82 = read_json(BATCH036_DIR / "batch036_psa82_permutation_null_diagnostic.json")
    fragility = read_json(BATCH036_DIR / "batch036_structured_fragility_diagnostic.json")
    language = read_json(BATCH036_DIR / "public_language_audit_batch036.json")
    minimality = read_json(BATCH036_DIR / "artifact_minimality_audit.json")
    budget = read_json(BATCH036_DIR / "artifact_payload_budget.json")

    expected_artifact = {
        "artifact_name": "post_v2_37_hardening_batch035_gated_source_repair_artifacts",
        "artifact_id": 8097192645,
        "workflow_run_id": 28759801868,
        "workflow_head_sha": "7cf6196f5da13ab5c814a16276de799fd62d8059",
        "artifact_sha256": "7c9bdf55732b02e3b2365c5c538edcb6e5c583ea430345bd932b6b453939e9fd",
        "artifact_size_bytes": 160350,
        "zip_entry_count": 168,
        "unsafe_path_count": 0,
        "duplicate_path_count": 0,
        "pycache_pyc_payload_count": 0,
        "artifact_sha256sums_checked": 167,
        "batch035_sha256sums_checked": 26,
        "post_sha256sums_checked": 139,
        "manifest_failure_count": 0,
    }
    if ingest.get("status") != "PASS" or verification.get("status") != "PASS":
        errors.append("Batch036 did not record Batch035 artifact custody before Batch036 logic")
    for key, value in expected_artifact.items():
        if verification.get(key) != value:
            errors.append(f"Batch036 Batch035 artifact verification mismatch for {key}")
    if ingest.get("artifact_sha256") != expected_artifact["artifact_sha256"] or ingest.get("artifact_size_bytes") != 160350:
        errors.append("Batch036 Batch035 ingest identity mismatch")
    if ingest != post_ingest or verification != post_verification:
        errors.append("Batch036 post-level Batch035 custody records do not match batch-level records")

    if batch035_state.get("status") != "PASS_WITH_BATCH035_REPAIR_NOT_VALIDATED":
        errors.append("Batch036 did not start from the official attempted-repair Batch035 state")
    if batch035_state.get("exact_blocker") != "post_repair_target_not_resolved":
        errors.append("Batch036 did not preserve Batch035 exact blocker")
    if batch035_state.get("patch_application_status") != "PASS" or batch035_state.get("patch_scope_status") != "PASS":
        errors.append("Batch036 did not preserve Batch035 patch application/scope PASS")
    if batch035_state.get("issue_derived_repair_validated") is not False or batch035_state.get("issue_derived_repair_episode_count") != 0:
        errors.append("Batch036 did not preserve Batch035 non-success claim boundary")
    if preservation.get("status") != "PASS":
        errors.append("Batch036 repair attempt preservation not PASS")
    if preservation.get("patch_attempted") is not True or preservation.get("issue_derived_repair_validated") is not False:
        errors.append("Batch036 repair preservation misclassified Batch035 attempt")

    if decomposition.get("status") != "PASS":
        errors.append("Batch036 failure decomposition not PASS")
    if decomposition.get("classification") != "target_failure_still_present_with_secondary_linter_precondition":
        errors.append("Batch036 did not classify Batch035 replay as target failure plus secondary linter precondition")
    if decomposition.get("target_indicators_remain") is not True:
        errors.append("Batch036 lost remaining target indicators")
    observed_target = set(decomposition.get("target_indicator_terms_observed", []))
    if not {"Not a git repository", "not a git repository"}.intersection(observed_target):
        errors.append("Batch036 decomposition missing target Git terms")
    secondary = set(decomposition.get("secondary_linter_precondition_terms_observed", []))
    if not {"FileNotFoundError", "No such file or directory", "pylint"}.issubset(secondary):
        errors.append("Batch036 decomposition missing secondary linter terms")
    if decomposition.get("missing_pylint_treated_as_target_issue") is not False or decomposition.get("missing_pylint_treated_as_repair_success") is not False:
        errors.append("Batch036 treated missing pylint as target issue or repair success")
    if decomposition.get("git_fatal_occurs_before_linter_file_not_found") is not True:
        errors.append("Batch036 did not preserve failure ordering")

    if inspection.get("status") != "PASS":
        errors.append("Batch036 source inspection not PASS")
    call_sites = set(inspection.get("relevant_call_sites_inspected", []))
    required_sites = {
        "src/darker/git.py::git_get_content_at_revision",
        "src/darker/git.py::_git_check_output_lines",
        "src/darker/git.py::git_get_modified_files",
        "src/darker/linting.py::run_linter",
        "src/darker/__main__.py::format_edited_parts",
    }
    if not required_sites.issubset(call_sites):
        errors.append("Batch036 did not inspect all relevant Git/linter call sites")
    findings = inspection.get("batch035_failure_cause_findings", {})
    if findings.get("env_was_not_propagated_to_all_relevant_git_subprocesses") is not True:
        errors.append("Batch036 did not identify incomplete Git env propagation")
    if findings.get("linter_path_introduced_separate_declared_dependency_precondition") is not True:
        errors.append("Batch036 did not separate secondary linter precondition")
    if inspection.get("safe_localized_source_only_refinement_evident") is not True or inspection.get("candidate_v2_authorized") is not True:
        errors.append("Batch036 source inspection did not authorize the recorded v2 candidate")
    for key in ["forbidden_evidence_used", "fixed_revision_inspected", "gold_patch_inspected", "future_pr_or_later_commit_inspected"]:
        if inspection.get(key) is not False:
            errors.append(f"Batch036 source inspection used forbidden evidence flag: {key}")

    if policy.get("status") != "PASS" or policy.get("candidate_v2_patch_count") != 1:
        errors.append("Batch036 candidate v2 policy invalid")
    if policy.get("source_only_patch_required") is not True or policy.get("tests_may_be_modified") is not False:
        errors.append("Batch036 candidate v2 policy weakened scope")
    if policy.get("fixed_gold_future_later_evidence_allowed") is not False:
        errors.append("Batch036 candidate v2 policy allowed forbidden evidence")
    if generation.get("status") != "PASS" or generation.get("candidate_v2_generated") is not True:
        errors.append("Batch036 candidate v2 not generated")
    patch_path = Path(str(generation.get("patch_path", "")))
    if not patch_path.is_file():
        errors.append("Batch036 patch candidate v2 path missing")
    else:
        if generation.get("patch_sha256") != sha256_file(patch_path):
            errors.append("Batch036 patch candidate v2 SHA mismatch")
        if not patch_path.read_text(encoding="utf-8").strip():
            errors.append("Batch036 patch candidate v2 empty")
    if generation.get("touched_files") != ["src/darker/git.py"] or generation.get("source_only") is not True or generation.get("tests_modified") is not False:
        errors.append("Batch036 patch candidate v2 scope invalid")
    if generation.get("forbidden_evidence_used") is not False:
        errors.append("Batch036 candidate v2 used forbidden evidence")
    for key in [
        "fixed_revision_accessed",
        "gold_patch_accessed",
        "future_pr_accessed",
        "later_commit_message_accessed",
        "later_outcome_evidence_accessed",
        "fixed_version_patch_accessed",
        "solution_sections_used",
    ]:
        if firewall.get(key) is not False:
            errors.append(f"Batch036 forbidden evidence flag set: {key}")
    if firewall.get("status") != "PASS":
        errors.append("Batch036 decision-time evidence firewall failed")

    repair_validated = state.get("issue_derived_repair_validated") is True
    if patch_application.get("status") == "PASS":
        if patch_application.get("touched_files") != ["src/darker/git.py"]:
            errors.append("Batch036 patch v2 application touched unexpected files")
        if patch_application.get("source_only") is not True or patch_application.get("tests_modified") is not False:
            errors.append("Batch036 patch v2 application scope invalid")
        if post_repair.get("status") != "PASS":
            errors.append("Batch036 patch v2 applied without post-repair replay record")
    else:
        if repair_validated:
            errors.append("Batch036 validated without patch v2 application")

    if post_repair.get("classification") == "target_resolution_blocked_by_secondary_linter_precondition":
        if post_repair.get("target_failure_resolved") is not True:
            errors.append("Batch036 secondary-precondition classification lacks target resolution")
        if not post_repair.get("secondary_linter_precondition_terms_observed"):
            errors.append("Batch036 secondary-precondition classification lacks linter terms")
    if post_repair.get("classification") == "target_failure_still_present_with_secondary_linter_precondition":
        if post_repair.get("target_failure_resolved") is not False:
            errors.append("Batch036 target-still-present classification inconsistent")

    if validation.get("issue_derived_repair_episode_count_increment_candidate") is True:
        if validation.get("issue_derived_repair_validated") is not True or post_repair.get("target_replay_fully_passed") is not True or duplicate.get("duplicate_replay_passed") is not True:
            errors.append("Batch036 issue-derived count increment candidate lacks target plus duplicate replay")
    if repair_validated:
        if validation.get("status") != "PASS":
            errors.append("Batch036 validated repair without validation PASS")
        if post_repair.get("target_replay_fully_passed") is not True:
            errors.append("Batch036 validated repair without full post-repair target pass")
        if duplicate.get("status") != "PASS" or duplicate.get("duplicate_replay_passed") is not True:
            errors.append("Batch036 validated repair without duplicate clean replay")
        if state.get("issue_derived_repair_episode_count") != 1:
            errors.append("Batch036 validated repair did not increment issue-derived count")
    else:
        if state.get("issue_derived_repair_episode_count") != 0:
            errors.append("Batch036 incremented issue-derived count without validation")
        if feasibility.get("issue_derived_repair_episode_count") != 0 or claim.get("issue_derived_repair_episode_count") != 0:
            errors.append("Batch036 feasibility/claim incremented issue-derived count without validation")

    if claim.get("missing_pylint_treated_as_target_issue") is not False or claim.get("missing_pylint_treated_as_repair_success") is not False:
        errors.append("Batch036 claim boundary misclassified missing pylint")
    if claim.get("controller_audit_closure_gate_changed") is not False or claim.get("unregistered_closure_gate_exception_added") is not False:
        errors.append("Batch036 claim boundary introduced closure gate exception")
    if state.get("native_repair_episode_count") != 4 or claim.get("native_repair_episode_count") != 4:
        errors.append("Batch036 native repair episode count changed")
    if state.get("full_scoring") != "NOT_RUN/disallowed" or state.get("memory_lift") != "not_demonstrated" or state.get("self_maintaining_software") != "false/not_demonstrated":
        errors.append("Batch036 state overclaims")
    if claim.get("full_scoring") != "NOT_RUN/disallowed" or claim.get("memory_lift") != "not_demonstrated" or claim.get("self_maintaining_software") != "false/not_demonstrated":
        errors.append("Batch036 claim boundary overclaims")
    if state.get("current_protocol") != "v2.13":
        errors.append("Batch036 changed current protocol")
    if state.get("matched_null_diagnostic_run_count") != 0 or claim.get("matched_null_ran") is not False:
        errors.append("Batch036 matched-null ran unexpectedly")
    if closure.get("pass_logic_changed") is not False or closure.get("diagnostic_replaced_empirical_gate") is not False:
        errors.append("Batch036 ControllerAudit diagnostic replaced or changed pass logic")
    if psa82.get("diagnostic_replaced_empirical_gate") is not False or fragility.get("diagnostic_replaced_empirical_gate") is not False:
        errors.append("Batch036 diagnostics replaced empirical repair gates")
    if ledger.get("status") != "PASS" or ledger.get("hash_chain_valid") is not True:
        errors.append("Batch036 proof ledger invalid")
    if ledger.get("issue_derived_count_increment_without_validation") is not False or ledger.get("repair_success_claim_from_candidate_generation_alone") is not False or ledger.get("diagnostics_replaced_empirical_gates") is not False:
        errors.append("Batch036 proof ledger permits overclaim")
    if language.get("status") != "PASS":
        errors.append("Batch036 public language audit failed")
    if minimality.get("status") != "PASS" or minimality.get("recursive_prior_batch_packaging_detected") is not False:
        errors.append("Batch036 artifact minimality failed")
    if budget.get("status") != "PASS":
        errors.append("Batch036 artifact budget failed")
    for path in list(BATCH036_DIR.glob("*.json")) + list(BATCH036_DIR.glob("*.md")) + list(BATCH036_DIR.glob("*.py")) + list(BATCH036_DIR.glob("*.diff")):
        text = path.read_text(encoding="utf-8")
        if any(marker in text for marker in ["1.45", "wiggle_room", "closure_tolerance", "residual_tolerance"]):
            errors.append(f"Batch036 introduced forbidden tolerance marker in {path.name}")
    return errors


def audit_batch037_records() -> list[str]:
    errors: list[str] = []
    for name in BATCH037_REQUIRED:
        if not (BATCH037_DIR / name).is_file():
            errors.append(f"batch037 missing required file {name}")
    if errors:
        return errors
    if verify_manifest(BATCH037_DIR).get("status") != "PASS":
        errors.append("batch037 manifest mismatch")

    batch036_state = read_json(BATCH036_DIR / "consolidated_state_clean_replication_batch_036.json")
    state = read_json(BATCH037_DIR / "consolidated_state_clean_replication_batch_037.json")
    ingest = read_json(BATCH037_DIR / "batch036_artifact_ingest_summary.json")
    verification = read_json(BATCH037_DIR / "batch036_artifact_verification.json")
    preservation = read_json(BATCH037_DIR / "batch036_candidate_v2_preservation.json")
    diagnosis = read_json(BATCH037_DIR / "batch037_provider_execution_substage_diagnosis.json")
    patch_application = read_json(BATCH037_DIR / "batch037_patch_v2_application_result.json")
    scope = read_json(BATCH037_DIR / "batch037_patch_v2_scope_audit.json")
    post_repair = read_json(BATCH037_DIR / "batch037_post_repair_target_replay_v2.json")
    duplicate = read_json(BATCH037_DIR / "batch037_duplicate_clean_replay_v2.json")
    validation = read_json(BATCH037_DIR / "batch037_issue_derived_repair_validation.json")
    feasibility = read_json(BATCH037_DIR / "issue_derived_repair_feasibility_batch037.json")
    claim = read_json(BATCH037_DIR / "claim_boundary_batch037.json")
    ledger = read_json(BATCH037_DIR / "proof_obligations_ledger_batch037.json")
    closure = read_json(BATCH037_DIR / "batch037_controller_audit_closure_check.json")
    psa82 = read_json(BATCH037_DIR / "batch037_psa82_permutation_null_diagnostic.json")
    fragility = read_json(BATCH037_DIR / "batch037_structured_fragility_diagnostic.json")
    language = read_json(BATCH037_DIR / "public_language_audit_batch037.json")
    minimality = read_json(BATCH037_DIR / "artifact_minimality_audit.json")
    budget = read_json(BATCH037_DIR / "artifact_payload_budget.json")

    expected_artifact = {
        "artifact_name": "post_v2_37_hardening_batch036_post_repair_failure_decomposition_artifacts",
        "artifact_id": 8098158675,
        "workflow_run_id": 28762763373,
        "workflow_head_sha": "a0855e65813f9d6e38c39f20636a65069f09a5cb",
        "artifact_sha256": "7f2105ec414b23ea9bc48e5720b15aebda66a57ec161a507cebf6e82b708eeb7",
        "artifact_size_bytes": 161782,
        "zip_entry_count": 169,
        "unsafe_path_count": 0,
        "duplicate_path_count": 0,
        "pycache_pyc_payload_count": 0,
    }
    if ingest.get("status") != "PASS" or verification.get("status") != "PASS":
        errors.append("Batch037 did not record Batch036 artifact custody before Batch037 logic")
    for key, value in expected_artifact.items():
        if verification.get(key) != value:
            errors.append(f"Batch037 Batch036 artifact verification mismatch for {key}")
    if verification.get("artifact_manifest_checked") != 168 or verification.get("batch036_manifest_checked") != 25 or verification.get("post_manifest_checked") != 141:
        errors.append("Batch037 Batch036 manifest counts mismatch")
    if ingest.get("artifact_sha256") != expected_artifact["artifact_sha256"] or ingest.get("artifact_size_bytes") != expected_artifact["artifact_size_bytes"]:
        errors.append("Batch037 Batch036 ingest identity mismatch")

    if batch036_state.get("status") != "PASS_WITH_BATCH036_REPAIR_NOT_VALIDATED":
        errors.append("Batch037 did not start from official Batch036 repair-not-validated state")
    if batch036_state.get("exact_blocker") != "provider_batch036_execution_failed":
        errors.append("Batch037 did not preserve Batch036 provider blocker")
    if preservation.get("status") != "PASS":
        errors.append("Batch037 candidate v2 preservation not PASS")
    if preservation.get("candidate_v2_patch_sha256") != "9c1061f5c60878b7ace6a3c02f41ec2af162fd4de66192a34028ed720e864ec1":
        errors.append("Batch037 candidate v2 patch SHA mismatch")
    if preservation.get("candidate_v2_touched_files") != ["src/darker/git.py"] or preservation.get("source_only") is not True or preservation.get("tests_modified") is not False:
        errors.append("Batch037 candidate v2 preservation scope invalid")

    expected_order = [
        "provider_available",
        "provider_workspace_materialized",
        "selected_source_head_verified",
        "candidate_v2_patch_available",
        "candidate_v2_patch_hash_verified",
        "candidate_v2_patch_apply_check",
        "candidate_v2_patch_apply",
        "post_repair_target_replay_v2",
        "duplicate_clean_replay_v2",
    ]
    if diagnosis.get("status") != "PASS":
        errors.append("Batch037 substage diagnosis not PASS")
    if diagnosis.get("substage_order") != expected_order:
        errors.append("Batch037 substage order mismatch")
    records = diagnosis.get("substage_records", {})
    for name in expected_order:
        record = records.get(name, {})
        if record.get("status") not in {"PASS", "BLOCK", "NOT_RUN"}:
            errors.append(f"Batch037 substage {name} has invalid status")
        if record.get("status") in {"PASS", "BLOCK"}:
            for key in ["returncode", "stdout_sha256", "stderr_sha256", "sanitized_stdout_excerpt", "sanitized_stderr_excerpt"]:
                if key not in record:
                    errors.append(f"Batch037 substage {name} missing {key}")
    apply_check = records.get("candidate_v2_patch_apply_check", {})
    apply_stage = records.get("candidate_v2_patch_apply", {})
    source_stage = records.get("selected_source_head_verified", {})
    hash_stage = records.get("candidate_v2_patch_hash_verified", {})
    if patch_application.get("patch_apply_attempted") is True:
        if source_stage.get("status") != "PASS":
            errors.append("Batch037 patch apply attempted without selected source head verification")
        if hash_stage.get("status") != "PASS":
            errors.append("Batch037 patch apply attempted without candidate v2 patch hash verification")
        if apply_check.get("status") != "PASS" or patch_application.get("patch_apply_check_status") != "PASS":
            errors.append("Batch037 patch apply attempted without successful git apply --check")
    if apply_check.get("status") == "BLOCK" and patch_application.get("patch_apply_attempted") is True:
        errors.append("Batch037 applied patch despite failed apply check")
    if apply_stage.get("status") == "PASS" and patch_application.get("status") != "PASS":
        errors.append("Batch037 substage apply PASS but application record not PASS")

    if patch_application.get("status") == "PASS":
        if patch_application.get("touched_files") != ["src/darker/git.py"]:
            errors.append("Batch037 patch v2 touched unexpected files")
        if patch_application.get("source_only") is not True or patch_application.get("tests_modified") is not False:
            errors.append("Batch037 patch v2 application scope invalid")
        if scope.get("status") != "PASS" or scope.get("source_only") is not True or scope.get("tests_modified") is not False:
            errors.append("Batch037 patch v2 scope audit invalid")
        if post_repair.get("status") not in {"PASS", "BLOCK"}:
            errors.append("Batch037 patch application did not lead to a replay record")
    else:
        if state.get("issue_derived_repair_validated") is True:
            errors.append("Batch037 validated repair without patch application")

    if post_repair.get("classification") == "target_resolution_blocked_by_secondary_linter_precondition":
        if post_repair.get("target_failure_resolved") is not True:
            errors.append("Batch037 secondary-precondition classification lacks target resolution")
        if not post_repair.get("secondary_linter_precondition_terms_observed"):
            errors.append("Batch037 secondary-precondition classification lacks linter terms")
    if post_repair.get("classification") == "repair_v2_target_not_resolved":
        if post_repair.get("target_failure_resolved") is not False:
            errors.append("Batch037 repair-v2-target-not-resolved classification inconsistent")
    if post_repair.get("missing_pylint_treated_as_target_issue") is True or post_repair.get("missing_pylint_treated_as_repair_success") is True:
        errors.append("Batch037 treated missing pylint as target issue or repair success")

    repair_validated = state.get("issue_derived_repair_validated") is True
    if repair_validated:
        if validation.get("status") != "PASS":
            errors.append("Batch037 validated repair without validation PASS")
        if post_repair.get("target_replay_fully_passed") is not True:
            errors.append("Batch037 validated repair without full post-repair target pass")
        if duplicate.get("status") != "PASS" or duplicate.get("duplicate_replay_passed") is not True:
            errors.append("Batch037 validated repair without duplicate clean replay")
    if state.get("issue_derived_repair_episode_count") != 0 or claim.get("issue_derived_repair_episodes") != 0:
        errors.append("Batch037 incremented issue-derived repair episode count")
    if validation.get("issue_derived_repair_episode_count_increment_candidate") is not False or feasibility.get("issue_derived_repair_episode_count_increment_candidate") is not False:
        errors.append("Batch037 marked issue-derived count increment candidate")

    if claim.get("patch_generated") is not True or claim.get("patch_authorized") is not True:
        errors.append("Batch037 lost candidate generated/authorized claim")
    if claim.get("native_external_repair_episodes") != 4 or state.get("native_repair_episode_count") != 4:
        errors.append("Batch037 native repair episode count changed")
    if claim.get("matched_null_ran") is not False or state.get("matched_null_diagnostic_run_count") != 0:
        errors.append("Batch037 matched-null ran unexpectedly")
    if claim.get("psa82_permutation_null_ran") is not False or claim.get("structured_fragility_diagnostic_ran") is not False:
        errors.append("Batch037 diagnostics ran unexpectedly")
    if closure.get("pass_logic_changed") is not False or closure.get("diagnostic_replaced_empirical_gate") is not False:
        errors.append("Batch037 ControllerAudit diagnostic replaced or changed pass logic")
    if psa82.get("diagnostic_replaced_empirical_gate") is not False or fragility.get("diagnostic_replaced_empirical_gate") is not False:
        errors.append("Batch037 diagnostics replaced empirical repair gates")
    if state.get("full_scoring") != "NOT_RUN/disallowed" or state.get("memory_lift") != "not_demonstrated" or state.get("self_maintaining_software") != "false/not_demonstrated":
        errors.append("Batch037 state overclaims")
    if claim.get("full_scoring") != "NOT_RUN/disallowed" or claim.get("memory_lift") != "not_demonstrated" or claim.get("self_maintaining_software") != "false/not_demonstrated":
        errors.append("Batch037 claim boundary overclaims")
    if state.get("current_protocol") != "v2.13" or claim.get("current_protocol") != "v2.13":
        errors.append("Batch037 changed current protocol")
    if ledger.get("status") != "PASS":
        errors.append("Batch037 proof ledger invalid")
    if language.get("status") != "PASS":
        errors.append("Batch037 public language audit failed")
    if minimality.get("status") != "PASS" or minimality.get("recursive_prior_batch_packaging_detected") is not False:
        errors.append("Batch037 artifact minimality failed")
    if budget.get("status") != "PASS":
        errors.append("Batch037 artifact budget failed")
    for path in list(BATCH037_DIR.glob("*.json")) + list(BATCH037_DIR.glob("*.md")) + list(BATCH037_DIR.glob("*.py")) + list(BATCH037_DIR.glob("*.diff")):
        text = path.read_text(encoding="utf-8")
        if any(marker in text for marker in ["1.45", "wiggle_room", "closure_tolerance", "residual_tolerance"]):
            errors.append(f"Batch037 introduced forbidden tolerance marker in {path.name}")
    return errors


def audit_batch038_records() -> list[str]:
    errors: list[str] = []
    for name in BATCH038_REQUIRED:
        if not (BATCH038_DIR / name).is_file():
            errors.append(f"batch038 missing required file {name}")
    if errors:
        return errors
    if verify_manifest(BATCH038_DIR).get("status") != "PASS":
        errors.append("batch038 manifest mismatch")

    state = read_json(BATCH038_DIR / "consolidated_state_clean_replication_batch_038.json")
    ingest = read_json(BATCH038_DIR / "batch037_artifact_ingest_summary.json")
    verification = read_json(BATCH038_DIR / "batch037_artifact_verification.json")
    boundary = read_json(BATCH038_DIR / "batch037_official_boundary_preservation.json")
    governance = read_json(BATCH038_DIR / BATCH038_GOVERNANCE_FILE)
    identity = read_json(BATCH038_DIR / "batch038_stable_identity_map.json")
    blockers = read_json(BATCH038_DIR / "batch038_blocker_lineage_map.json")
    cofactors = read_json(BATCH038_DIR / "batch038_cofactor_materialization_registry.json")
    not_run = read_json(BATCH038_DIR / "batch038_not_run_reason_registry.json")
    failed_branch = read_json(BATCH038_DIR / "batch038_failed_repair_branch_record.json")
    step_ring = read_json(BATCH038_DIR / "batch038_step_activation_ring.json")
    stage_audit = read_json(BATCH038_DIR / "batch038_compartmentalized_repair_stage_audit.json")
    no_floating = read_json(BATCH038_DIR / "batch038_no_floating_update_audit.json")
    telemetry = read_json(BATCH038_DIR / "batch038_command_telemetry_sanitization_audit.json")
    contract = read_json(BATCH038_DIR / "batch038_expected_output_contract.json")
    verifier = read_json(BATCH038_DIR / "batch038_independent_verifier_summary.json")
    psa82 = read_json(BATCH038_DIR / "batch038_psa82_diagnostic_boundary.json")
    boundary_terms = read_json(BATCH038_DIR / BATCH038_BOUNDARY_FILE)
    stale = read_json(BATCH038_DIR / "batch038_stale_blocker_retirement_registry.json")
    analysis = read_json(BATCH038_DIR / "batch038_patch_serialization_failure_analysis.json")
    policy = read_json(BATCH038_DIR / "batch038_corrected_patch_generation_policy.json")
    integrity = read_json(BATCH038_DIR / "batch038_corrected_patch_integrity.json")
    apply_check = read_json(BATCH038_DIR / "batch038_corrected_patch_apply_check.json")
    application = read_json(BATCH038_DIR / "batch038_corrected_patch_application_result.json")
    scope = read_json(BATCH038_DIR / "batch038_corrected_patch_scope_audit.json")
    post_repair = read_json(BATCH038_DIR / "batch038_post_repair_target_replay.json")
    duplicate = read_json(BATCH038_DIR / "batch038_duplicate_clean_replay.json")
    validation = read_json(BATCH038_DIR / "batch038_issue_derived_repair_validation.json")
    feasibility = read_json(BATCH038_DIR / "issue_derived_repair_feasibility_batch038.json")
    claim = read_json(BATCH038_DIR / "claim_boundary_batch038.json")
    ledger = read_json(BATCH038_DIR / "proof_obligations_ledger_batch038.json")
    minimality = read_json(BATCH038_DIR / "artifact_minimality_audit.json")
    budget = read_json(BATCH038_DIR / "artifact_payload_budget.json")
    language = read_json(BATCH038_DIR / "public_language_audit_batch038.json")
    patch_text = (BATCH038_DIR / "batch038_corrected_source_only_patch_candidate.diff").read_text(encoding="utf-8")

    if ingest.get("status") != "PASS" or verification.get("status") != "PASS":
        errors.append("Batch038 did not preserve Batch037 artifact custody")
    expected_artifact = {
        "artifact_name": "post_v2_37_hardening_batch037_provider_execution_substage_recovery_artifacts",
        "artifact_id": 8099848792,
        "workflow_run_id": 28768059294,
        "workflow_head_sha": "5613264ff3cca6efc8e8a13553926a9c0d254379",
        "artifact_sha256": "7646e4c7db29e010da4f03d6f20b9e7c225a0ddfbea027c7423450e91af25fc3",
        "artifact_size_bytes": 159993,
        "zip_entry_count": 164,
    }
    for key, value in expected_artifact.items():
        if verification.get(key) != value or ingest.get(key) != value:
            errors.append(f"Batch038 Batch037 artifact identity mismatch for {key}")
    if verification.get("manifest_failure_count") != 0 or verification.get("unsafe_path_count") != 0 or verification.get("duplicate_path_count") != 0:
        errors.append("Batch038 Batch037 artifact verification facts invalid")
    if boundary.get("batch037_status_preserved") != "PASS_WITH_BATCH037_PROVIDER_SUBSTAGE_BLOCKED":
        errors.append("Batch038 did not preserve Batch037 official status")
    if boundary.get("batch037_exact_blocker_preserved") != "patch_v2_apply_check_failed":
        errors.append("Batch038 did not preserve Batch037 exact blocker")
    if boundary.get("batch037_candidate_v2_patch_sha256") != "9c1061f5c60878b7ace6a3c02f41ec2af162fd4de66192a34028ed720e864ec1":
        errors.append("Batch038 did not preserve original candidate v2 patch SHA")
    if "corrupt patch at line 23" not in str(boundary.get("batch037_patch_apply_check_stderr", "")):
        errors.append("Batch038 did not preserve corrupt-patch stderr")

    for record_name, record in [
        ("governance", governance),
        ("identity", identity),
        ("blockers", blockers),
        ("cofactors", cofactors),
        ("not_run", not_run),
        ("failed_branch", failed_branch),
        ("step_ring", step_ring),
        ("stage_audit", stage_audit),
        ("no_floating", no_floating),
        ("telemetry", telemetry),
        ("contract", contract),
        ("verifier", verifier),
        ("psa82", psa82),
        ("boundary_terms", boundary_terms),
        ("stale", stale),
    ]:
        if record.get("status") != "PASS":
            errors.append(f"Batch038 {record_name} record not PASS")
    if len(identity.get("records", [])) < 5:
        errors.append("Batch038 stable identity map incomplete")
    blocker_ids = {item.get("blocker_id") for item in blockers.get("records", []) if isinstance(item, dict)}
    for expected in {"patch_v2_apply_check_failed", "corrupt_patch_at_line_23", "provider_batch036_execution_failed"}:
        if expected not in blocker_ids:
            errors.append(f"Batch038 blocker lineage missing {expected}")
    cofactor_names = {item.get("cofactor_name") for item in cofactors.get("cofactors", []) if isinstance(item, dict)}
    for expected in {"pylint", "diff serialization / patch hygiene", "corrected candidate patch diff SHA256"}:
        if expected not in cofactor_names:
            errors.append(f"Batch038 cofactor registry missing {expected}")
    not_run_entries = not_run.get("entries", [])
    if not isinstance(not_run_entries, list) or len(not_run_entries) < 10:
        errors.append("Batch038 NOT_RUN reason registry incomplete")
    for item in not_run_entries:
        if item.get("status") == "NOT_RUN" and not item.get("reason"):
            errors.append(f"Batch038 NOT_RUN gate lacks reason: {item.get('gate_name')}")

    if failed_branch.get("failure_classification") != "patch_serialization_failure_before_semantic_repair_validation":
        errors.append("Batch038 failed branch did not classify serialization failure")
    if failed_branch.get("branch_closed_without_count_increment") is not True:
        errors.append("Batch038 failed branch not closed without count increment")
    if analysis.get("invalid_placeholder_token_detected") is not True or analysis.get("invalid_placeholder_token_removed") is not True:
        errors.append("Batch038 did not detect/remove invalid placeholder token")
    if analysis.get("classification") != "patch_serialization_failure_before_semantic_repair_validation":
        errors.append("Batch038 patch failure classification mismatch")
    if policy.get("semantic_candidate_v3_generated") is not False or policy.get("forbidden_inputs_used") != []:
        errors.append("Batch038 corrected patch policy used forbidden or v3 path")
    if "<CTX_BLANK>" in patch_text:
        errors.append("Batch038 corrected patch still contains invalid placeholder token")
    if integrity.get("corrected_patch_sha256") != "1cf85f55ec48cc47199e33b3b04fc74a16bf935814784e9abdc56b574d960396":
        errors.append("Batch038 corrected patch SHA mismatch")
    if integrity.get("original_patch_sha256") != "9c1061f5c60878b7ace6a3c02f41ec2af162fd4de66192a34028ed720e864ec1":
        errors.append("Batch038 original patch SHA mismatch")
    if integrity.get("source_only") is not True or integrity.get("tests_modified") is not False or integrity.get("touched_files") != ["src/darker/git.py"]:
        errors.append("Batch038 corrected patch scope metadata invalid")
    if scope.get("status") == "PASS":
        if scope.get("source_only") is not True or scope.get("tests_modified") is not False or scope.get("touched_files") != ["src/darker/git.py"]:
            errors.append("Batch038 corrected patch scope audit invalid")
    if application.get("patch_apply_attempted") is True and apply_check.get("status") != "PASS":
        errors.append("Batch038 applied corrected patch without successful apply-check")
    if post_repair.get("status") in {"PASS", "BLOCK"} and application.get("status") != "PASS":
        errors.append("Batch038 ran post-repair replay before patch application PASS")
    if duplicate.get("status") != "NOT_RUN" and post_repair.get("target_replay_fully_passed") is not True:
        errors.append("Batch038 ran duplicate replay before target replay fully passed")

    validated = state.get("issue_derived_repair_validated") is True
    if validated:
        if post_repair.get("target_replay_fully_passed") is not True or duplicate.get("duplicate_replay_passed") is not True:
            errors.append("Batch038 validated repair without replay and duplicate replay")
        if state.get("issue_derived_repair_episode_count") != 1:
            errors.append("Batch038 validated repair without issue-derived count increment")
    else:
        if state.get("issue_derived_repair_episode_count") != 0 or claim.get("issue_derived_repair_episodes") != 0:
            errors.append("Batch038 incremented issue-derived count without validation")
        if validation.get("issue_derived_repair_episode_count_increment_candidate") is True or feasibility.get("issue_derived_repair_episode_count_increment_candidate") is True:
            errors.append("Batch038 marked count increment candidate without validation")
    if state.get("native_repair_episode_count") != 4 or claim.get("native_external_repair_episodes") != 4:
        errors.append("Batch038 native repair count changed")
    if state.get("full_scoring") != "NOT_RUN/disallowed" or state.get("memory_lift") != "not_demonstrated" or state.get("self_maintaining_software") != "false/not_demonstrated":
        errors.append("Batch038 state overclaims")
    if claim.get("full_scoring") != "NOT_RUN/disallowed" or claim.get("memory_lift") != "not_demonstrated" or claim.get("self_maintaining_software") != "false/not_demonstrated":
        errors.append("Batch038 claim boundary overclaims")
    if state.get("current_protocol") != "v2.13" or claim.get("current_protocol") != "v2.13":
        errors.append("Batch038 changed current protocol")
    if psa82.get("psa82_used_as_repair_proof") is not False or psa82.get("psa82_replaces_target_replay") is not False or psa82.get("psa82_replaces_duplicate_replay") is not False:
        errors.append("Batch038 PSA-82 boundary overclaimed")
    if boundary_terms.get("design_mapping_language_used_as_repair_proof") is not False or boundary_terms.get("repo_proof_requires_empirical_replay_and_duplicate_replay") is not True:
        errors.append("Batch038 design mapping boundary invalid")
    if no_floating.get("selected_source_commit_pinned") != "a2d13656adfaa010fb6c7339087f3347ad2b815a":
        errors.append("Batch038 selected source commit not pinned")
    if no_floating.get("no_fixed_gold_later_pr_access") is not True:
        errors.append("Batch038 no-floating audit permits forbidden evidence")
    if ledger.get("status") != "PASS" or ledger.get("hash_chain_valid") is not True:
        errors.append("Batch038 proof ledger invalid")
    if minimality.get("status") != "PASS" or minimality.get("recursive_prior_batch_packaging_detected") is not False:
        errors.append("Batch038 artifact minimality failed")
    if budget.get("status") != "PASS":
        errors.append("Batch038 artifact budget failed")
    if language.get("status") != "PASS":
        errors.append("Batch038 public language audit failed")
    for path in list(BATCH038_DIR.glob("*.json")) + list(BATCH038_DIR.glob("*.md")) + list(BATCH038_DIR.glob("*.py")) + list(BATCH038_DIR.glob("*.diff")):
        text = path.read_text(encoding="utf-8")
        if any(marker in text for marker in ["1.45", "wiggle_room", "closure_tolerance", "residual_tolerance"]):
            errors.append(f"Batch038 introduced forbidden tolerance marker in {path.name}")
    return errors


def audit_batch039_records() -> list[str]:
    errors: list[str] = []
    for name in BATCH039_REQUIRED:
        if not (BATCH039_DIR / name).is_file():
            errors.append(f"batch039 missing required file {name}")
    if errors:
        return errors
    if verify_manifest(BATCH039_DIR).get("status") != "PASS":
        errors.append("batch039 manifest mismatch")

    state = read_json(BATCH039_DIR / "consolidated_state_clean_replication_batch_039.json")
    ingest = read_json(BATCH039_DIR / "batch038_artifact_ingest_summary.json")
    verification = read_json(BATCH039_DIR / "batch038_artifact_verification.json")
    preservation = read_json(BATCH039_DIR / "batch038_target_resolution_preservation.json")
    governance_preservation = read_json(BATCH039_DIR / "batch038_governance_artifact_preservation.json")
    continuity = read_json(BATCH039_DIR / BATCH039_GOVERNANCE_CONTINUITY_FILE)
    identity = read_json(BATCH039_DIR / "batch039_stable_identity_map_update.json")
    blocker_lineage = read_json(BATCH039_DIR / "batch039_blocker_lineage_map_update.json")
    model = read_json(BATCH039_DIR / "batch039_secondary_cofactor_governance_model.json")
    general_policy = read_json(BATCH039_DIR / "batch039_general_cofactor_materialization_policy.json")
    not_run = read_json(BATCH039_DIR / "batch039_not_run_reason_registry.json")
    failed_record = read_json(BATCH039_DIR / "batch039_failed_branch_or_precondition_record.json")
    step_ring = read_json(BATCH039_DIR / "batch039_step_activation_ring.json")
    no_floating = read_json(BATCH039_DIR / "batch039_no_floating_update_audit.json")
    telemetry = read_json(BATCH039_DIR / "batch039_command_telemetry_sanitization_audit.json")
    contract = read_json(BATCH039_DIR / "batch039_expected_output_contract.json")
    psa82 = read_json(BATCH039_DIR / "batch039_psa82_diagnostic_boundary.json")
    boundary = read_json(BATCH039_DIR / BATCH039_BOUNDARY_FILE)
    linter = read_json(BATCH039_DIR / "batch039_declared_linter_cofactor_verification.json")
    linter_policy = read_json(BATCH039_DIR / "batch039_declared_linter_materialization_policy.json")
    materialization = read_json(BATCH039_DIR / "batch039_declared_linter_materialization_result.json")
    patch = read_json(BATCH039_DIR / "batch039_corrected_patch_preservation.json")
    replay = read_json(BATCH039_DIR / "batch039_post_repair_target_replay_under_cofactor_governance.json")
    chain = read_json(BATCH039_DIR / "batch039_secondary_cofactor_chain_update.json")
    duplicate = read_json(BATCH039_DIR / "batch039_duplicate_clean_replay_under_cofactor_governance.json")
    validation = read_json(BATCH039_DIR / "batch039_issue_derived_repair_validation.json")
    feasibility = read_json(BATCH039_DIR / "issue_derived_repair_feasibility_batch039.json")
    claim = read_json(BATCH039_DIR / "claim_boundary_batch039.json")
    ledger = read_json(BATCH039_DIR / "proof_obligations_ledger_batch039.json")
    minimality = read_json(BATCH039_DIR / "artifact_minimality_audit.json")
    budget = read_json(BATCH039_DIR / "artifact_payload_budget.json")
    language = read_json(BATCH039_DIR / "public_language_audit_batch039.json")

    if state.get("status") != "PASS_WITH_BATCH039_DECLARED_SECONDARY_COFACTOR_LOCK_REQUIRED":
        errors.append("Batch039 status mismatch")
    if state.get("exact_blocker") != "declared_secondary_cofactor_unpinned_lock_required":
        errors.append("Batch039 exact blocker mismatch")
    expected_artifact = {
        "artifact_name": "post_v2_37_hardening_batch038_reactome_patch_serialization_recovery_artifacts",
        "artifact_id": 8117490206,
        "workflow_run_id": 28812461319,
        "workflow_head_sha": "337f9460d2c83408909b03ae3dfa57a32aedf9dc",
        "artifact_sha256": "64adc2ffa04bc97231c65177eb91bdf70a8fa198f68ff2528c334da7ef551b75",
        "artifact_size_bytes": 179553,
        "zip_entry_count": 184,
    }
    for key, value in expected_artifact.items():
        if ingest.get(key) != value or verification.get(key) != value:
            errors.append(f"Batch039 Batch038 artifact identity mismatch for {key}")
    if ingest.get("raw_zip_bytes_ingested") is not False or ingest.get("zip_or_tar_committed") is not False:
        errors.append("Batch039 ingested raw artifact bytes")
    if verification.get("manifest_failure_count") != 0 or verification.get("unsafe_path_count") != 0 or verification.get("duplicate_path_count") != 0:
        errors.append("Batch039 Batch038 artifact verification facts invalid")
    if preservation.get("batch038_status") != "PASS_WITH_BATCH038_TARGET_RESOLVED_SECONDARY_LINTER_PRECONDITION":
        errors.append("Batch039 did not preserve official Batch038 status")
    if preservation.get("batch038_exact_blocker") != "target_resolution_blocked_by_secondary_linter_precondition":
        errors.append("Batch039 did not preserve official Batch038 blocker")
    if preservation.get("target_failure_resolved") is not True or preservation.get("original_git_target_indicators_absent") is not True:
        errors.append("Batch039 did not preserve target-resolution progress")
    if preservation.get("issue_derived_repair_validated") is not False:
        errors.append("Batch039 overclaimed Batch038 repair validation")
    if governance_preservation.get("status") != "PASS" or governance_preservation.get("batch038_governance_ignored") is not False:
        errors.append("Batch039 did not preserve Batch038 governance artifacts")
    if continuity.get("status") != "PASS" or continuity.get("design_mapping_used_as_repair_proof") is not False:
        errors.append("Batch039 governance continuity invalid")
    if len(identity.get("records", [])) < 6:
        errors.append("Batch039 stable identity lineage incomplete")
    blockers = {item.get("blocker_id"): item for item in blocker_lineage.get("records", []) if isinstance(item, dict)}
    for retired in ["patch_v2_apply_check_failed", "corrupt_patch_at_line_23"]:
        if blockers.get(retired, {}).get("active_or_retired") != "retired" or blockers.get(retired, {}).get("corrected_by_batch") != "clean_replication_batch_038":
            errors.append(f"Batch039 did not retire {retired} through Batch038")
    if blockers.get("target_resolution_blocked_by_secondary_linter_precondition", {}).get("active_or_retired") != "active":
        errors.append("Batch039 did not preserve active secondary precondition")
    if blockers.get("declared_secondary_cofactor_unpinned_lock_required", {}).get("active_or_retired") != "active":
        errors.append("Batch039 blocker lineage missing declared cofactor lock blocker")
    required_states = {
        "observed",
        "declared_by_selected_source",
        "undeclared",
        "declared_but_unpinned",
        "declared_and_locked",
        "provider_materialized",
        "provider_materialization_blocked",
        "materialized_but_new_secondary_blocker_observed",
        "exhausted_requires_seed_or_scope_retirement",
    }
    if not required_states.issubset(set(model.get("states", []))):
        errors.append("Batch039 secondary cofactor state machine incomplete")
    if len(model.get("cofactor_classes", [])) < 6:
        errors.append("Batch039 cofactor model is too pylint-specific")
    policy = model.get("general_policy", {})
    if policy.get("floating_or_unpinned_dependency_may_not_be_silently_installed_as_proof") is not True:
        errors.append("Batch039 model permits floating dependency proof")
    pylint_records = [item for item in model.get("observed_secondary_cofactors", []) if item.get("cofactor_name") == "pylint"]
    if not pylint_records:
        errors.append("Batch039 model missing pylint instance")
    else:
        pylint = pylint_records[0]
        if pylint.get("state") != "declared_but_unpinned" or pylint.get("provider_only_materialization_allowed") is not False:
            errors.append("Batch039 pylint state/materialization gate invalid")
        if pylint.get("may_count_as_target_failure") is not False or pylint.get("may_count_as_repair_success") is not False:
            errors.append("Batch039 treats pylint as target failure or repair success")
    if general_policy.get("install_unpinned_floating_dependency_as_repair_proof") is not False:
        errors.append("Batch039 general materialization policy permits floating proof")
    if linter.get("status") != "PASS":
        errors.append("Batch039 linter verification not PASS")
    if linter.get("setup_cfg", {}).get("declares_pylint_under_options_extras_require_test") is not True:
        errors.append("Batch039 setup.cfg declaration missing")
    if linter.get("pyproject_toml", {}).get("declares_darker_lint_pylint") is not True:
        errors.append("Batch039 pyproject declaration missing")
    if linter.get("pinned") is not False or linter.get("existing_provider_dependency_lock_includes_pylint") is not False:
        errors.append("Batch039 linter pin/lock status mismatch")
    if linter.get("materialization_would_require_dynamic_dependency_resolution") is not True:
        errors.append("Batch039 did not identify dynamic dependency resolution requirement")
    if linter_policy.get("provider_only_materialization_authorized") is not False or linter_policy.get("blocker") != "declared_secondary_cofactor_unpinned_lock_required":
        errors.append("Batch039 linter materialization policy mismatch")
    if materialization.get("materialization_attempted") is not False or materialization.get("status") != "BLOCK":
        errors.append("Batch039 attempted or misclassified linter materialization")
    if materialization.get("source_mutated") is not False or materialization.get("tests_mutated") is not False:
        errors.append("Batch039 cofactor materialization mutated source/tests")
    if patch.get("status") != "PASS" or patch.get("corrected_patch_sha256") != "1cf85f55ec48cc47199e33b3b04fc74a16bf935814784e9abdc56b574d960396":
        errors.append("Batch039 corrected patch preservation invalid")
    if replay.get("status") != "NOT_RUN" or replay.get("blocker") != "declared_secondary_cofactor_unpinned_lock_required":
        errors.append("Batch039 replay did not block on unpinned cofactor lock")
    if replay.get("target_failure_resolved_in_batch038") is not True or replay.get("target_replay_fully_passed") is not False:
        errors.append("Batch039 replay preservation facts invalid")
    if chain.get("one_off_silent_fix_used") is not False or chain.get("active_secondary_cofactor_state") != "declared_but_unpinned":
        errors.append("Batch039 secondary cofactor chain handling invalid")
    if duplicate.get("status") != "NOT_RUN" or duplicate.get("prerequisite_target_replay_fully_passed") is not False:
        errors.append("Batch039 duplicate replay ordering invalid")
    if validation.get("issue_derived_repair_validated") is not False or validation.get("issue_derived_repair_episode_count_increment_candidate") is not False:
        errors.append("Batch039 issue-derived validation overclaim")
    if feasibility.get("issue_derived_repair_feasibility") is not False:
        errors.append("Batch039 issue-derived feasibility overclaim")
    if failed_record.get("original_git_target_resolved") is not True or failed_record.get("branch_closed_without_count_increment") is not True:
        errors.append("Batch039 failed/precondition record invalid")
    if no_floating.get("floating_dependency_install_performed") is not False or no_floating.get("fixed_gold_later_pr_accessed") is not False:
        errors.append("Batch039 no-floating audit invalid")
    if telemetry.get("status") != "PASS" or telemetry.get("token_or_secret_capture_allowed") is not False:
        errors.append("Batch039 telemetry sanitization invalid")
    if contract.get("status") != "PASS" or not set(BATCH039_REQUIRED).issubset(set(contract.get("required_outputs", []))):
        errors.append("Batch039 expected output contract incomplete")
    if psa82.get("psa82_used_as_repair_proof") is not False or psa82.get("psa82_replaces_target_replay") is not False or psa82.get("psa82_replaces_duplicate_replay") is not False:
        errors.append("Batch039 PSA-82 boundary overclaimed")
    if boundary.get("design_mapping_language_used_as_repair_proof") is not False or boundary.get("repo_proof_requires_empirical_replay_and_duplicate_replay") is not True:
        errors.append("Batch039 design mapping boundary invalid")
    if len(not_run.get("entries", [])) < 8:
        errors.append("Batch039 NOT_RUN reason registry incomplete")
    for item in not_run.get("entries", []):
        if item.get("status") in {"NOT_RUN", "BLOCK"} and not item.get("reason"):
            errors.append(f"Batch039 NOT_RUN/BLOCK gate lacks reason: {item.get('gate_name')}")
    if step_ring.get("status") != "PASS" or "floating pylint installation" not in step_ring.get("blocked", []):
        errors.append("Batch039 step activation ring missing floating-install block")
    if claim.get("native_external_repair_episodes") != 4 or claim.get("issue_derived_repair_episodes") != 0:
        errors.append("Batch039 claim boundary changed repair counts")
    if claim.get("full_scoring") != "NOT_RUN/disallowed" or claim.get("memory_lift") != "not_demonstrated" or claim.get("self_maintaining_software") != "false/not_demonstrated":
        errors.append("Batch039 claim boundary overclaims")
    if claim.get("current_protocol") != "v2.13" or state.get("current_protocol") != "v2.13":
        errors.append("Batch039 changed current protocol")
    if ledger.get("status") != "PASS" or ledger.get("hash_chain_valid") is not True:
        errors.append("Batch039 proof ledger invalid")
    if minimality.get("status") != "PASS" or minimality.get("recursive_prior_batch_packaging_detected") is not False:
        errors.append("Batch039 artifact minimality failed")
    if budget.get("status") != "PASS":
        errors.append("Batch039 artifact budget failed")
    if language.get("status") != "PASS":
        errors.append("Batch039 public language audit failed")
    for path in list(BATCH039_DIR.glob("*.json")) + list(BATCH039_DIR.glob("*.md")) + list(BATCH039_DIR.glob("*.py")) + list(BATCH039_DIR.glob("*.diff")):
        text = path.read_text(encoding="utf-8")
        if any(marker in text for marker in ["1.45", "wiggle_room", "closure_tolerance", "residual_tolerance", "25.7"]):
            errors.append(f"Batch039 introduced forbidden tolerance marker in {path.name}")
    return errors


def audit_batch040_records() -> list[str]:
    errors: list[str] = []
    for name in BATCH040_REQUIRED:
        if not (BATCH040_DIR / name).is_file():
            errors.append(f"batch040 missing required file {name}")
    if errors:
        return errors
    manifest_status = verify_manifest(BATCH040_DIR).get("status")
    if manifest_status != "PASS":
        errors.append("batch040 manifest mismatch")

    state = read_json(BATCH040_DIR / "consolidated_state_clean_replication_batch_040.json")
    ingest = read_json(BATCH040_DIR / "batch039_artifact_ingest_summary.json")
    verification = read_json(BATCH040_DIR / "batch039_artifact_verification.json")
    governance_preservation = read_json(BATCH040_DIR / "batch039_secondary_cofactor_governance_preservation.json")
    target_preservation = read_json(BATCH040_DIR / "batch039_target_resolution_preservation.json")
    continuity = read_json(BATCH040_DIR / BATCH040_GOVERNANCE_CONTINUITY_FILE)
    identity = read_json(BATCH040_DIR / "batch040_stable_identity_map_update.json")
    blocker_lineage = read_json(BATCH040_DIR / "batch040_blocker_lineage_map_update.json")
    model = read_json(BATCH040_DIR / "batch040_secondary_cofactor_governance_model_update.json")
    not_run = read_json(BATCH040_DIR / "batch040_not_run_reason_registry.json")
    failed_record = read_json(BATCH040_DIR / "batch040_failed_branch_or_precondition_record.json")
    step_ring = read_json(BATCH040_DIR / "batch040_step_activation_ring.json")
    stage_audit = read_json(BATCH040_DIR / "batch040_compartmentalized_repair_stage_audit.json")
    no_floating = read_json(BATCH040_DIR / "batch040_no_floating_update_audit.json")
    telemetry = read_json(BATCH040_DIR / "batch040_command_telemetry_sanitization_audit.json")
    contract = read_json(BATCH040_DIR / "batch040_expected_output_contract.json")
    psa82 = read_json(BATCH040_DIR / "batch040_psa82_diagnostic_boundary.json")
    boundary = read_json(BATCH040_DIR / BATCH040_BOUNDARY_FILE)
    lock_policy = read_json(BATCH040_DIR / "batch040_reviewed_cofactor_lock_policy.json")
    discovery_policy = read_json(BATCH040_DIR / "batch040_pylint_lock_discovery_policy.json")
    discovery = read_json(BATCH040_DIR / "batch040_pylint_provider_lock_discovery_result.json")
    lock = read_json(BATCH040_DIR / "batch040_pylint_provider_lock.json")
    review = read_json(BATCH040_DIR / "batch040_pylint_lock_review.json")
    materialization_policy = read_json(BATCH040_DIR / "batch040_provider_only_cofactor_materialization_policy.json")
    materialization = read_json(BATCH040_DIR / "batch040_provider_only_cofactor_materialization_result.json")
    pylint_executable = read_json(BATCH040_DIR / "batch040_pylint_executable_verification.json")
    patch = read_json(BATCH040_DIR / "batch040_corrected_patch_preservation.json")
    replay = read_json(BATCH040_DIR / "batch040_post_repair_target_replay_with_reviewed_cofactor_lock.json")
    chain = read_json(BATCH040_DIR / "batch040_secondary_cofactor_chain_update.json")
    duplicate = read_json(BATCH040_DIR / "batch040_duplicate_clean_replay_with_reviewed_cofactor_lock.json")
    validation = read_json(BATCH040_DIR / "batch040_issue_derived_repair_validation.json")
    feasibility = read_json(BATCH040_DIR / "issue_derived_repair_feasibility_batch040.json")
    claim = read_json(BATCH040_DIR / "claim_boundary_batch040.json")
    ledger = read_json(BATCH040_DIR / "proof_obligations_ledger_batch040.json")
    minimality = read_json(BATCH040_DIR / "artifact_minimality_audit.json")
    budget = read_json(BATCH040_DIR / "artifact_payload_budget.json")
    language = read_json(BATCH040_DIR / "public_language_audit_batch040.json")

    allowed_statuses = {
        "PASS_WITH_BATCH040_PINNED_COFACTOR_LOCK_UNAVAILABLE",
        "PASS_WITH_BATCH040_REVIEWED_LOCK_MATERIALIZATION_BLOCKED",
        "PASS_WITH_BATCH040_REVIEWED_LOCK_REPLAY_NOT_VALIDATED",
        "PASS_WITH_BATCH040_DUPLICATE_REPLAY_NOT_VALIDATED",
        "PASS_WITH_BATCH040_ISSUE_DERIVED_REPAIR_VALIDATED",
    }
    if state.get("status") not in allowed_statuses:
        errors.append("Batch040 status is not an allowed reviewed-lock boundary")
    expected_artifact = {
        "artifact_name": "post_v2_37_hardening_batch039_secondary_cofactor_governance_artifacts",
        "artifact_id": 8119514842,
        "workflow_run_id": 28817716254,
        "workflow_head_sha": "23f9acfdd654c3b9cb1b5bf0f6ab3cec145231bd",
        "artifact_sha256": "d86adfc09e55440821b6a690b4a93de24fc5cd078995d4653087697393c02be2",
        "artifact_size_bytes": 172520,
        "zip_entry_count": 181,
    }
    for key, value in expected_artifact.items():
        if ingest.get(key) != value or verification.get(key) != value:
            errors.append(f"Batch040 Batch039 artifact identity mismatch for {key}")
    if ingest.get("raw_zip_bytes_ingested") is not False or ingest.get("zip_or_tar_committed") is not False:
        errors.append("Batch040 ingested raw artifact bytes")
    if verification.get("manifest_failure_count") != 0 or verification.get("unsafe_path_count") != 0 or verification.get("duplicate_path_count") != 0:
        errors.append("Batch040 Batch039 artifact verification facts invalid")
    if verification.get("artifact_manifest_checked") != 180 or verification.get("batch039_manifest_checked") != 36 or verification.get("post_manifest_checked") != 142:
        errors.append("Batch040 Batch039 manifest check counts invalid")
    if governance_preservation.get("batch039_status_preserved") != "PASS_WITH_BATCH039_DECLARED_SECONDARY_COFACTOR_LOCK_REQUIRED":
        errors.append("Batch040 did not preserve Batch039 status")
    if governance_preservation.get("batch039_exact_blocker_preserved") != "declared_secondary_cofactor_unpinned_lock_required":
        errors.append("Batch040 did not preserve Batch039 blocker")
    if governance_preservation.get("pylint_declared_by_selected_source") is not True or governance_preservation.get("pylint_unpinned_preserved") is not True:
        errors.append("Batch040 did not preserve declared-unpinned pylint facts")
    if target_preservation.get("batch038_target_failure_resolved") is not True or target_preservation.get("batch038_original_git_target_indicators_absent") is not True:
        errors.append("Batch040 did not preserve Batch038 target resolution")
    if target_preservation.get("repair_validated_before_batch040") is not False:
        errors.append("Batch040 incorrectly treats prior boundary as repair validated")
    if continuity.get("status") != "PASS" or continuity.get("design_mapping_used_as_repair_proof") is not False:
        errors.append("Batch040 governance continuity overclaimed")
    if len(identity.get("records", [])) < 7:
        errors.append("Batch040 stable identity lineage incomplete")
    if not any(item.get("batch_id") == "clean_replication_batch_040" for item in identity.get("records", [])):
        errors.append("Batch040 stable identity map missing Batch040")
    if not any(item.get("blocker_id") == "declared_secondary_cofactor_unpinned_lock_required" for item in blocker_lineage.get("records", [])):
        errors.append("Batch040 blocker lineage missing Batch039 blocker")
    if model.get("general_policy_not_pylint_only") is not True or len(model.get("future_cofactor_classes_supported", [])) < 6:
        errors.append("Batch040 cofactor model is too pylint-specific")
    if lock_policy.get("applies_to_future_declared_secondary_cofactors") is not True:
        errors.append("Batch040 lock policy is not general")
    for policy_key in [
        "selected_source_declaration_required",
        "python_provider_compatibility_required",
        "transitive_dependency_capture_required",
        "package_version_capture_required",
        "hash_capture_when_available_required",
        "install_command_capture_required",
        "materialization_authorization_requires_reviewed_provider_safe_lock",
        "replay_authorization_requires_materialization_pass",
    ]:
        if lock_policy.get(policy_key) is not True:
            errors.append(f"Batch040 lock policy missing {policy_key}")
    if lock_policy.get("source_mutation_allowed") is not False or lock_policy.get("test_mutation_allowed") is not False:
        errors.append("Batch040 cofactor lock policy allows source/test mutation")
    if lock_policy.get("floating_install_counted_as_repair_proof") is not False or lock_policy.get("fixed_gold_future_later_evidence_allowed") is not False:
        errors.append("Batch040 cofactor lock policy allows forbidden proof")
    if discovery_policy.get("verify_declaration_before_resolution") is not True or discovery_policy.get("confirm_unpinned_before_lock") is not True:
        errors.append("Batch040 discovery policy does not verify declaration/unpinned state")
    if discovery.get("selected_source_declaration_verified") is not True or discovery.get("pylint_unpinned_in_selected_source") is not True:
        errors.append("Batch040 discovery did not preserve selected-source pylint facts")
    if discovery.get("source_mutated") is not False or discovery.get("tests_mutated") is not False or discovery.get("fixed_gold_future_later_evidence_used") is not False:
        errors.append("Batch040 discovery used forbidden mutation/evidence")
    if lock.get("status") != "PASS" or lock.get("cofactor_name") != "pylint":
        errors.append("Batch040 pylint provider lock missing")
    packages = lock.get("packages", [])
    if len(packages) < 8:
        errors.append("Batch040 pylint provider lock missing transitive packages")
    if any(not item.get("name") or not item.get("version") or not item.get("sha256") for item in packages):
        errors.append("Batch040 provider lock package missing exact version/hash")
    if lock.get("provider_only") is not True or lock.get("source_mutation_allowed") is not False or lock.get("test_mutation_allowed") is not False:
        errors.append("Batch040 provider lock allows forbidden mutation")
    if review.get("status") == "PASS":
        if review.get("reviewed") is not True or review.get("provider_safe") is not True or review.get("materialization_authorized") is not True:
            errors.append("Batch040 lock review PASS without reviewed/provider-safe/materialization authorization")
    else:
        if state.get("status") != "PASS_WITH_BATCH040_PINNED_COFACTOR_LOCK_UNAVAILABLE":
            errors.append("Batch040 lock review blocked without lock-unavailable boundary")
    if materialization_policy.get("materialize_only_after_reviewed_lock") is not True or materialization_policy.get("provider_only") is not True:
        errors.append("Batch040 materialization policy invalid")
    if materialization.get("source_mutated") is not False or materialization.get("tests_mutated") is not False:
        errors.append("Batch040 provider-only cofactor materialization mutated source/tests")
    if review.get("status") != "PASS" and materialization.get("status") == "PASS":
        errors.append("Batch040 materialized pylint without reviewed lock")
    if materialization.get("status") == "PASS" and pylint_executable.get("status") != "PASS":
        errors.append("Batch040 materialization passed without pylint executable verification")
    if patch.get("status") != "PASS" or patch.get("corrected_patch_sha256") != "1cf85f55ec48cc47199e33b3b04fc74a16bf935814784e9abdc56b574d960396":
        errors.append("Batch040 corrected patch preservation invalid")
    if patch.get("touched_files") != ["src/darker/git.py"] or patch.get("source_only") is not True or patch.get("tests_modified") is not False:
        errors.append("Batch040 corrected patch scope invalid")
    if replay.get("status") != "NOT_RUN" and materialization.get("status") != "PASS":
        errors.append("Batch040 replay ran before provider materialization PASS")
    if replay.get("target_replay_fully_passed") is True:
        if replay.get("classification") != "post_repair_target_replay_passed_with_reviewed_cofactor_lock":
            errors.append("Batch040 replay full-pass classification mismatch")
    else:
        if validation.get("issue_derived_repair_validated") is True:
            errors.append("Batch040 validated repair without target replay full pass")
    if duplicate.get("status") != "NOT_RUN" and replay.get("target_replay_fully_passed") is not True:
        errors.append("Batch040 duplicate replay ran before target replay full pass")
    if duplicate.get("duplicate_replay_passed") is not True and validation.get("issue_derived_repair_validated") is True:
        errors.append("Batch040 validated repair without duplicate replay pass")
    if validation.get("issue_derived_repair_episode_count_increment_candidate") is True:
        if replay.get("target_replay_fully_passed") is not True or duplicate.get("duplicate_replay_passed") is not True:
            errors.append("Batch040 marked count increment candidate without replay+duplicate pass")
    if state.get("issue_derived_repair_episode_count") != 0 or claim.get("issue_derived_repair_episodes") != 0:
        errors.append("Batch040 incremented official issue-derived repair count in same batch")
    if state.get("native_repair_episode_count") != 4 or claim.get("native_external_repair_episodes") != 4:
        errors.append("Batch040 changed native repair count")
    if feasibility.get("issue_derived_repair_feasibility") is True and validation.get("issue_derived_repair_validated") is not True:
        errors.append("Batch040 feasibility true without validation")
    if claim.get("full_scoring") != "NOT_RUN/disallowed" or state.get("full_scoring") != "NOT_RUN/disallowed":
        errors.append("Batch040 full scoring boundary changed")
    if claim.get("memory_lift") != "not_demonstrated" or state.get("memory_lift") != "not_demonstrated":
        errors.append("Batch040 memory lift overclaimed")
    if claim.get("self_maintaining_software") != "false/not_demonstrated" or state.get("self_maintaining_software") != "false/not_demonstrated":
        errors.append("Batch040 self-maintaining software overclaimed")
    if claim.get("current_protocol") != "v2.13" or state.get("current_protocol") != "v2.13":
        errors.append("Batch040 changed current protocol")
    if chain.get("one_off_silent_fix_used") is not False:
        errors.append("Batch040 silently fixed secondary cofactor")
    if stage_audit.get("duplicate_after_target_replay_only") is not True:
        errors.append("Batch040 duplicate replay order invalid")
    if "floating pylint installation as proof" not in step_ring.get("blocked", []):
        errors.append("Batch040 step activation ring missing floating-install block")
    if no_floating.get("floating_dependency_install_performed") is not False or no_floating.get("floating_dependency_install_counted_as_repair_proof") is not False:
        errors.append("Batch040 no-floating audit invalid")
    if telemetry.get("token_or_secret_capture_allowed") is not False:
        errors.append("Batch040 telemetry audit allows token capture")
    if contract.get("status") != "PASS" or not set(BATCH040_REQUIRED).issubset(set(contract.get("required_outputs", []))):
        errors.append("Batch040 expected output contract incomplete")
    if psa82.get("used_as_repair_proof") is not False or psa82.get("diagnostic_replaces_target_replay") is not False or psa82.get("diagnostic_replaces_duplicate_replay") is not False:
        errors.append("Batch040 diagnostic boundary overclaimed")
    if boundary.get("design_mapping_language_used_as_repair_proof") is not False or boundary.get("repo_proof_requires_empirical_replay_and_duplicate_replay") is not True:
        errors.append("Batch040 design mapping boundary invalid")
    if len(not_run.get("entries", [])) < 3:
        errors.append("Batch040 NOT_RUN reason registry incomplete")
    for item in not_run.get("entries", []):
        if item.get("status") in {"NOT_RUN", "BLOCK"} and not item.get("reason"):
            errors.append(f"Batch040 NOT_RUN/BLOCK gate lacks reason: {item.get('gate_name')}")
    if ledger.get("status") != "PASS" or ledger.get("hash_chain_valid") is not True:
        errors.append("Batch040 proof ledger invalid")
    if not any(item.get("entry_id") == "ROLLBACK_BLOCK" for item in ledger.get("entries", [])):
        errors.append("Batch040 proof ledger missing rollback boundary")
    if minimality.get("status") != "PASS" or minimality.get("recursive_prior_batch_packaging_detected") is not False:
        errors.append("Batch040 artifact minimality failed")
    if budget.get("status") != "PASS":
        errors.append("Batch040 artifact budget failed")
    if language.get("status") != "PASS":
        errors.append("Batch040 public language audit failed")
    forbidden_markers = ["1.45", "25.7", "wiggle_room", "closure_tolerance", "residual_tolerance"]
    for path in list(BATCH040_DIR.glob("*.json")) + list(BATCH040_DIR.glob("*.md")) + list(BATCH040_DIR.glob("*.py")) + list(BATCH040_DIR.glob("*.diff")):
        text = path.read_text(encoding="utf-8")
        if any(marker in text for marker in forbidden_markers):
            errors.append(f"Batch040 introduced forbidden tolerance marker in {path.name}")
    return errors


def audit_batch041_records() -> list[str]:
    errors: list[str] = []
    for name in BATCH041_REQUIRED:
        if not (BATCH041_DIR / name).is_file():
            errors.append(f"batch041 missing required file {name}")
    if errors:
        return errors
    manifest_status = verify_manifest(BATCH041_DIR).get("status")
    if manifest_status != "PASS":
        errors.append("batch041 manifest mismatch")

    state = read_json(BATCH041_DIR / "consolidated_state_clean_replication_batch_041.json")
    ingest = read_json(BATCH041_DIR / "batch040_artifact_ingest_summary.json")
    verification = read_json(BATCH041_DIR / "batch040_artifact_verification.json")
    internal = read_json(BATCH041_DIR / "batch040_artifact_internal_status_preservation.json")
    reconciliation = read_json(BATCH041_DIR / "batch040_local_vs_artifact_blocker_reconciliation.json")
    target_preservation = read_json(BATCH041_DIR / "batch040_target_resolution_preservation.json")
    cofactor_preservation = read_json(BATCH041_DIR / "batch040_secondary_cofactor_governance_preservation.json")
    continuity = read_json(BATCH041_DIR / BATCH041_GOVERNANCE_CONTINUITY_FILE)
    stable = read_json(BATCH041_DIR / "batch041_stable_identity_integrity_audit.json")
    identity_update = read_json(BATCH041_DIR / "batch041_stable_identity_map_update.json")
    proof = read_json(BATCH041_DIR / "batch041_proof_ledger_referrer_audit.json")
    provenance = read_json(BATCH041_DIR / "batch041_cofactor_lock_provenance_audit.json")
    drift = read_json(BATCH041_DIR / "batch041_dependency_drift_audit.json")
    chain_budget = read_json(BATCH041_DIR / "batch041_secondary_cofactor_chain_budget.json")
    replay_matrix = read_json(BATCH041_DIR / "batch041_replay_classification_matrix.json")
    diagnostics = read_json(BATCH041_DIR / "batch041_included_excluded_diagnostics_registry.json")
    validation_activation = read_json(BATCH041_DIR / "batch041_validation_activation_audit.json")
    transport = read_json(BATCH041_DIR / "batch041_transport_export_equivalence_audit.json")
    origin = read_json(BATCH041_DIR / "batch041_evidence_origin_classification.json")
    lock_policy = read_json(BATCH041_DIR / "batch041_lock_completion_policy.json")
    completion = read_json(BATCH041_DIR / "batch041_pylint_lock_completion_result.json")
    lock_v2 = read_json(BATCH041_DIR / "batch041_pylint_provider_lock_v2.json")
    review = read_json(BATCH041_DIR / "batch041_pylint_lock_v2_review.json")
    materialization = read_json(BATCH041_DIR / "batch041_provider_only_cofactor_materialization_result.json")
    pylint_executable = read_json(BATCH041_DIR / "batch041_pylint_executable_verification.json")
    patch = read_json(BATCH041_DIR / "batch041_corrected_patch_preservation.json")
    post_repair = read_json(BATCH041_DIR / "batch041_post_repair_target_replay_with_lock_v2.json")
    duplicate = read_json(BATCH041_DIR / "batch041_duplicate_clean_replay_with_lock_v2.json")
    validation = read_json(BATCH041_DIR / "batch041_issue_derived_repair_validation.json")
    feasibility = read_json(BATCH041_DIR / "issue_derived_repair_feasibility_batch041.json")
    claim = read_json(BATCH041_DIR / "claim_boundary_batch041.json")
    ledger = read_json(BATCH041_DIR / "proof_obligations_ledger_batch041.json")
    not_run = read_json(BATCH041_DIR / "batch041_not_run_reason_registry.json")
    minimality = read_json(BATCH041_DIR / "artifact_minimality_audit.json")
    budget = read_json(BATCH041_DIR / "artifact_payload_budget.json")
    language = read_json(BATCH041_DIR / "public_language_audit_batch041.json")

    allowed_statuses = {
        "PASS_WITH_BATCH041_PINNED_COFACTOR_LOCK_STILL_UNAVAILABLE",
        "PASS_WITH_BATCH041_PROVIDER_MATERIALIZATION_BLOCKED",
        "PASS_WITH_BATCH041_LOCK_V2_REPLAY_NOT_VALIDATED",
        "PASS_WITH_BATCH041_DUPLICATE_REPLAY_NOT_VALIDATED",
        "PASS_WITH_BATCH041_ISSUE_DERIVED_REPAIR_VALIDATED",
    }
    if state.get("status") not in allowed_statuses:
        errors.append("Batch041 status is not an allowed lock-completion boundary")
    expected_artifact = {
        "artifact_name": "post_v2_37_hardening_batch040_reviewed_cofactor_lock_artifacts",
        "artifact_id": 8121640518,
        "workflow_run_id": 28823410425,
        "workflow_head_sha": "4ad4aa0ec129d658a31657f09fb2429ea99bbbd6",
        "artifact_sha256": "57da142928769bf9bd1795a8a83f752dce742df85b329ee4126b5e6a86b86a50",
        "artifact_size_bytes": 176224,
        "zip_entry_count": 185,
    }
    for key, value in expected_artifact.items():
        if ingest.get(key) != value or verification.get(key) != value:
            errors.append(f"Batch041 Batch040 artifact identity mismatch for {key}")
    if ingest.get("raw_zip_bytes_ingested") is not False or ingest.get("zip_or_tar_committed") is not False:
        errors.append("Batch041 ingested raw Batch040 artifact bytes")
    if verification.get("status") != "PASS":
        errors.append("Batch041 Batch040 artifact verification did not pass")
    artifact_manifest = verification.get("artifact_level_manifest", {})
    batch040_manifest = verification.get("batch040_output_manifest", {})
    post_manifest = verification.get("post_output_manifest", {})
    if (
        artifact_manifest.get("failure_count") != 0
        or batch040_manifest.get("failure_count") != 0
        or post_manifest.get("failure_count") != 0
        or verification.get("unsafe_path_count") != 0
        or verification.get("duplicate_path_count") != 0
    ):
        errors.append("Batch041 Batch040 artifact verification facts invalid")
    if artifact_manifest.get("checked") != 184 or batch040_manifest.get("checked") != 40 or post_manifest.get("checked") != 142:
        errors.append("Batch041 Batch040 manifest check counts invalid")
    if internal.get("status") != "PASS" or internal.get("artifact_internal_status") != "PASS_WITH_BATCH040_PINNED_COFACTOR_LOCK_UNAVAILABLE":
        errors.append("Batch041 did not preserve official Batch040 status")
    if internal.get("artifact_internal_exact_blocker") != "pinned_cofactor_lock_unavailable":
        errors.append("Batch041 did not preserve official Batch040 blocker")
    if internal.get("repo_side_pre_ingest_status") != "PASS_WITH_BATCH040_REVIEWED_LOCK_MATERIALIZATION_BLOCKED":
        errors.append("Batch041 did not record repo-side pre-ingest Batch040 status")
    if reconciliation.get("status") != "PASS" or reconciliation.get("post_ingest_active_batch040_blocker") != "pinned_cofactor_lock_unavailable":
        errors.append("Batch041 did not supersede local/provider Batch040 blocker with official blocker")
    if target_preservation.get("status") != "PASS" or target_preservation.get("batch038_original_git_target_failure_preserved_resolved") is not True:
        errors.append("Batch041 did not preserve Batch038 target-resolution boundary")
    if cofactor_preservation.get("status") != "PASS" or cofactor_preservation.get("batch039_secondary_cofactor_governance_preserved") is not True:
        errors.append("Batch041 did not preserve Batch039 cofactor governance")
    if continuity.get("status") != "PASS" or continuity.get("design_mapping_language_is_not_repair_proof") is not True:
        errors.append("Batch041 governance continuity overclaimed")

    if stable.get("status") != "PASS" or not all(
        stable.get(key) is True
        for key in [
            "no_duplicate_repair_attempt_id",
            "no_duplicate_active_blocker_ids",
            "each_active_blocker_has_one_next_allowed_action",
            "each_patch_candidate_has_one_parent_attempt",
            "each_replay_result_points_to_one_patch_sha",
            "each_cofactor_lock_points_to_one_selected_source_commit",
            "retired_blockers_cannot_be_active",
            "current_identity_primary_older_lineage_only",
            "failed_branches_have_rollback_targets",
            "no_active_branch_ambiguous_parentage",
            "no_unmarked_identity_merge",
        ]
    ):
        errors.append("Batch041 stable identity integrity audit failed")
    if identity_update.get("current_identity") != "batch041_lock_v2":
        errors.append("Batch041 stable identity map did not mark lock-v2 as current")
    if proof.get("status") != "PASS" or proof.get("hash_chain_valid") is not True:
        errors.append("Batch041 proof-ledger referrer audit failed")
    if not any(item.get("entry_id") == "ROLLBACK_BLOCK" for item in ledger.get("entries", [])):
        errors.append("Batch041 proof obligations ledger missing rollback boundary")
    if ledger.get("hash_chain_valid") is not True:
        errors.append("Batch041 proof obligations hash chain invalid")

    packages = lock_v2.get("packages", [])
    package_names = {item.get("name") for item in packages}
    if lock_v2.get("status") != "PASS" or lock_v2.get("lock_id") != "batch041_pylint_provider_only_lock_v2":
        errors.append("Batch041 lock-v2 record invalid")
    if "colorama" in package_names:
        errors.append("Batch041 lock-v2 retained provider-excluded colorama")
    if len(packages) != 8:
        errors.append("Batch041 lock-v2 package count invalid")
    if any(not item.get("name") or not item.get("version") or not item.get("sha256") for item in packages):
        errors.append("Batch041 lock-v2 package missing exact version/hash")
    platform_change = lock_v2.get("platform_conditioned_change", {})
    if platform_change.get("colorama_silently_removed") is not False or platform_change.get("colorama_required_on_selected_linux_provider") is not False:
        errors.append("Batch041 colorama platform-conditioned rationale invalid")
    if review.get("status") == "PASS":
        if review.get("reviewed") is not True or review.get("provider_safe") is not True or review.get("materialization_authorized") is not True:
            errors.append("Batch041 lock-v2 PASS without reviewed/provider-safe/materialization authorization")
        if completion.get("missing_expected_files") or completion.get("extra_unreviewed_files") or completion.get("hash_mismatches"):
            errors.append("Batch041 reviewed lock-v2 has missing/extra/hash-mismatch entries")
        if completion.get("resolver_output_reproducible") is not True:
            errors.append("Batch041 reviewed lock-v2 is not reproducible")
        if review.get("all_packages_exact_version_pinned") is not True or review.get("all_packages_have_hashes") is not True:
            errors.append("Batch041 reviewed lock-v2 lacks exact pins or hashes")
    else:
        if state.get("status") != "PASS_WITH_BATCH041_PINNED_COFACTOR_LOCK_STILL_UNAVAILABLE":
            errors.append("Batch041 lock-v2 review blocked without unavailable boundary")
    if provenance.get("lock_mutates_source") is not False or provenance.get("lock_mutates_tests") is not False:
        errors.append("Batch041 cofactor provenance allows source/test mutation")
    if provenance.get("fixed_gold_future_later_evidence_used") is not False:
        errors.append("Batch041 cofactor provenance used forbidden evidence")
    if provenance.get("lock_review_status") != review.get("status"):
        errors.append("Batch041 cofactor provenance review status mismatch")

    if materialization.get("source_mutated") is not False or materialization.get("tests_mutated") is not False:
        errors.append("Batch041 provider materialization mutated source/tests")
    if review.get("status") != "PASS" and materialization.get("status") == "PASS":
        errors.append("Batch041 materialized provider lock before reviewed lock-v2")
    if materialization.get("status") == "PASS" and pylint_executable.get("status") != "PASS":
        errors.append("Batch041 provider materialization passed without pylint executable verification")
    if drift.get("status") == "BLOCK" and post_repair.get("status") != "NOT_RUN":
        errors.append("Batch041 replay ran despite dependency drift block")
    if materialization.get("status") != "PASS" and drift.get("status") != "NOT_RUN":
        errors.append("Batch041 dependency drift ran without materialization")
    if drift.get("core_dependencies_unchanged") is False and drift.get("status") != "BLOCK":
        errors.append("Batch041 dependency drift did not block changed core dependencies")
    if chain_budget.get("status") != "PASS" or chain_budget.get("one_off_silent_fix_used") is not False:
        errors.append("Batch041 secondary cofactor chain budget invalid")
    if int(chain_budget.get("max_new_secondary_cofactors_per_batch", 0)) > 1 or int(chain_budget.get("max_chain_depth", 0)) > 3:
        errors.append("Batch041 cofactor chain budget exceeds conservative defaults")
    if replay_matrix.get("status") != "PASS" or replay_matrix.get("classification") not in {
        "target_defect_regressed",
        "target_defect_resolved_but_secondary_cofactor_missing",
        "target_defect_resolved_but_linter_reports_findings",
        "target_defect_resolved_full_command_failed_other_secondary",
        "target_defect_resolved_full_command_passed",
        "duplicate_replay_passed",
        "duplicate_replay_failed",
        "lock_unavailable_no_replay",
        "dependency_drift_blocks_replay",
        "cofactor_chain_exhausted",
    }:
        errors.append("Batch041 replay classification invalid")
    if diagnostics.get("status") != "PASS" or "full scoring" not in diagnostics.get("excluded", []):
        errors.append("Batch041 diagnostics registry invalid")
    if validation_activation.get("status") != "PASS" or validation_activation.get("validation_present_only_as_prose") is not False:
        errors.append("Batch041 validation activation audit invalid")
    if not validation_activation.get("not_run_validators_have_explicit_blockers", False):
        errors.append("Batch041 NOT_RUN validators lack explicit blockers")
    if transport.get("status") != "PASS":
        errors.append("Batch041 transport/export equivalence did not pass")
    if (
        transport.get("corrected_patch_sha_in_repo") != transport.get("corrected_patch_sha_in_provider_input")
        or transport.get("provider_source_head_matches_selected") is not True
    ):
        errors.append("Batch041 transport equivalence failed patch/source checks")
    allowed_origins = {
        "manual_artifact_ingest",
        "uploaded_artifact_verification",
        "repo_committed_summary",
        "AI_generated_patch_candidate",
        "provider_execution_telemetry",
        "diagnostic_output",
        "audit_result",
        "claim_boundary",
        "proof_ledger_entry",
        "dependency_resolution_output",
        "cofactor_lock_record",
    }
    if origin.get("status") != "PASS" or any(item.get("classification") not in allowed_origins for item in origin.get("items", [])):
        errors.append("Batch041 evidence origin classification invalid")
    if origin.get("diagnostic_outputs_do_not_masquerade_as_repair_proof") is not True:
        errors.append("Batch041 evidence origin permits diagnostic-as-proof")
    if lock_policy.get("status") != "PASS" or lock_policy.get("review_required_before_materialization") is not True:
        errors.append("Batch041 lock completion policy invalid")
    if patch.get("status") != "PASS" or patch.get("corrected_patch_sha256") != "1cf85f55ec48cc47199e33b3b04fc74a16bf935814784e9abdc56b574d960396":
        errors.append("Batch041 corrected patch preservation invalid")
    if patch.get("selected_source_head") != "a2d13656adfaa010fb6c7339087f3347ad2b815a" or patch.get("source_only") is not True or patch.get("tests_modified") is not False:
        errors.append("Batch041 corrected patch boundary invalid")
    if post_repair.get("status") != "NOT_RUN" and not (review.get("status") == "PASS" and materialization.get("status") == "PASS" and drift.get("status") == "PASS" and transport.get("status") == "PASS"):
        errors.append("Batch041 post-repair replay ran before all activation gates passed")
    if duplicate.get("status") != "NOT_RUN" and post_repair.get("target_replay_fully_passed") is not True:
        errors.append("Batch041 duplicate replay ran before post-repair target replay fully passed")
    if validation.get("issue_derived_repair_validated") is True and (post_repair.get("target_replay_fully_passed") is not True or duplicate.get("duplicate_replay_passed") is not True):
        errors.append("Batch041 issue-derived repair validated without target+duplicate replay")
    if feasibility.get("issue_derived_repair_feasibility") is True and validation.get("issue_derived_repair_validated") is not True:
        errors.append("Batch041 feasibility true without validation")
    if state.get("native_repair_episode_count") != 4 or claim.get("native_external_repair_episodes") != 4:
        errors.append("Batch041 changed native repair count")
    if state.get("issue_derived_repair_episode_count") != 0 or claim.get("issue_derived_repair_episodes") != 0:
        errors.append("Batch041 incremented issue-derived repair count without policy activation")
    if state.get("full_scoring") != "NOT_RUN/disallowed" or claim.get("full_scoring") != "NOT_RUN/disallowed":
        errors.append("Batch041 full scoring boundary changed")
    if state.get("memory_lift") != "not_demonstrated" or claim.get("memory_lift") != "not_demonstrated":
        errors.append("Batch041 memory lift overclaimed")
    if state.get("self_maintaining_software") != "false/not_demonstrated" or claim.get("self_maintaining_software") != "false/not_demonstrated":
        errors.append("Batch041 self-maintaining software overclaimed")
    if state.get("current_protocol") != "v2.13" or claim.get("current_protocol") != "v2.13":
        errors.append("Batch041 changed current protocol")
    for item in not_run.get("entries", []):
        if item.get("status") == "NOT_RUN" and not item.get("reason"):
            errors.append(f"Batch041 NOT_RUN gate lacks reason: {item.get('gate_name')}")
    if minimality.get("status") != "PASS" or minimality.get("recursive_prior_batch_packaging_detected") is not False:
        errors.append("Batch041 artifact minimality failed")
    if budget.get("status") != "PASS":
        errors.append("Batch041 artifact budget failed")
    if language.get("status") != "PASS":
        errors.append("Batch041 public language audit failed")
    forbidden_markers = ["1.45", "25.7", "wiggle_room", "closure_tolerance", "residual_tolerance"]
    for path in list(BATCH041_DIR.glob("*.json")) + list(BATCH041_DIR.glob("*.md")) + list(BATCH041_DIR.glob("*.py")) + list(BATCH041_DIR.glob("*.diff")):
        text = path.read_text(encoding="utf-8")
        if any(marker in text for marker in forbidden_markers):
            errors.append(f"Batch041 introduced forbidden tolerance marker in {path.name}")
    return errors


def audit_batch042_records() -> list[str]:
    errors: list[str] = []
    for name in BATCH042_REQUIRED:
        if not (BATCH042_DIR / name).is_file():
            errors.append(f"batch042 missing required file {name}")
    if errors:
        return errors
    if verify_manifest(BATCH042_DIR).get("status") != "PASS":
        errors.append("batch042 manifest mismatch")

    state = read_json(BATCH042_DIR / "consolidated_state_clean_replication_batch_042.json")
    ingest = read_json(BATCH042_DIR / "batch041_artifact_ingest_summary.json")
    verification = read_json(BATCH042_DIR / "batch041_artifact_verification.json")
    repair_preservation = read_json(BATCH042_DIR / "batch041_repair_validation_preservation.json")
    replay_preservation = read_json(BATCH042_DIR / "batch041_replay_and_duplicate_replay_preservation.json")
    count_gate = read_json(BATCH042_DIR / "batch042_issue_derived_episode_count_gate.json")
    continuity = read_json(BATCH042_DIR / BATCH042_GOVERNANCE_CONTINUITY_FILE)
    lineage = read_json(BATCH042_DIR / "batch042_stable_identity_lineage_lock.json")
    proof_lock = read_json(BATCH042_DIR / "batch042_proof_ledger_validation_lock.json")
    replay_classification = read_json(BATCH042_DIR / "batch042_replay_classification_preservation.json")
    diagnostics = read_json(BATCH042_DIR / "batch042_included_excluded_diagnostics_registry.json")
    psa82 = read_json(BATCH042_DIR / "batch042_psa82_diagnostic_boundary.json")
    design_boundary = read_json(BATCH042_DIR / BATCH042_BOUNDARY_FILE)
    stale = read_json(BATCH042_DIR / "batch042_stale_blocker_retirement_registry.json")
    feasibility = read_json(BATCH042_DIR / "issue_derived_repair_feasibility_batch042.json")
    claim = read_json(BATCH042_DIR / "claim_boundary_batch042.json")
    ledger = read_json(BATCH042_DIR / "proof_obligations_ledger_batch042.json")
    minimality = read_json(BATCH042_DIR / "artifact_minimality_audit.json")
    budget = read_json(BATCH042_DIR / "artifact_payload_budget.json")
    language = read_json(BATCH042_DIR / "public_language_audit_batch042.json")

    if state.get("status") != "PASS_WITH_BATCH042_ISSUE_DERIVED_REPAIR_COUNT_LOCKED":
        errors.append("Batch042 did not reach issue-derived count-lock boundary")
    if state.get("exact_blocker") is not None:
        errors.append("Batch042 count-lock boundary has an active blocker")
    expected_artifact = {
        "artifact_name": "post_v2_37_hardening_batch041_lock_completion_identity_integrity_artifacts",
        "artifact_id": 8122860577,
        "workflow_run_id": 28826607981,
        "workflow_head_sha": "f096ec7d1ddd3f6fa0af6c70ee8b52ec1ba42b78",
        "artifact_sha256": "169c7bf1ac94938a2217695927c5d418fd12d220286a2503ae4984fd7f92dcec",
        "artifact_size_bytes": 177818,
        "zip_entry_count": 182,
    }
    for key, value in expected_artifact.items():
        if ingest.get(key) != value or verification.get(key) != value:
            errors.append(f"Batch042 Batch041 artifact identity mismatch for {key}")
    if ingest.get("raw_zip_bytes_ingested") is not False or ingest.get("zip_or_tar_committed") is not False:
        errors.append("Batch042 ingested raw artifact bytes")
    if verification.get("status") != "PASS":
        errors.append("Batch042 Batch041 artifact verification not PASS")
    if verification.get("unsafe_path_count") != 0 or verification.get("duplicate_path_count") != 0 or verification.get("pycache_pyc_payload_count") != 0:
        errors.append("Batch042 Batch041 artifact hygiene facts invalid")
    if verification.get("artifact_manifest_checked") != 181 or verification.get("batch041_manifest_checked") != 37 or verification.get("post_manifest_checked") != 142:
        errors.append("Batch042 Batch041 manifest counts invalid")
    if verification.get("manifest_failure_count") != 0:
        errors.append("Batch042 Batch041 artifact manifest failures recorded")

    if repair_preservation.get("status") != "PASS":
        errors.append("Batch042 did not preserve Batch041 repair validation")
    if repair_preservation.get("batch041_status_preserved") != "PASS_WITH_BATCH041_ISSUE_DERIVED_REPAIR_VALIDATED":
        errors.append("Batch042 did not preserve Batch041 validated status")
    if repair_preservation.get("batch041_exact_blocker_preserved") is not None:
        errors.append("Batch042 did not preserve Batch041 exact blocker None")
    if repair_preservation.get("post_repair_target_replay_status") != "PASS" or repair_preservation.get("duplicate_clean_replay_status") != "PASS":
        errors.append("Batch042 did not preserve replay PASS states")
    if repair_preservation.get("issue_derived_repair_validated") is not True:
        errors.append("Batch042 did not preserve issue-derived validation true")
    if repair_preservation.get("issue_derived_repair_episode_count_increment_candidate") is not True:
        errors.append("Batch042 did not preserve count increment candidate")
    if repair_preservation.get("official_issue_derived_repair_episode_count_incremented_before_batch042") is not False:
        errors.append("Batch042 did not preserve pre-Batch042 count boundary")

    if replay_preservation.get("status") != "PASS":
        errors.append("Batch042 replay/duplicate preservation not PASS")
    for key in ["same_patch_sha", "same_lock_sha", "same_command_manifest", "same_provider_context_class"]:
        if replay_preservation.get(key) is not True:
            errors.append(f"Batch042 replay preservation failed {key}")

    if count_gate.get("status") != "PASS" or count_gate.get("issue_derived_repair_episode_count_increment_authorized") is not True:
        errors.append("Batch042 issue-derived count gate did not authorize increment")
    if count_gate.get("issue_derived_repair_episode_count_before_batch042") != 0 or count_gate.get("issue_derived_repair_episode_count_after_batch042") != 1:
        errors.append("Batch042 issue-derived count before/after invalid")
    if count_gate.get("native_external_repair_episode_count") != 4:
        errors.append("Batch042 native episode count changed")
    if count_gate.get("full_scoring") != "NOT_RUN/disallowed" or count_gate.get("memory_lift") != "not_demonstrated":
        errors.append("Batch042 count gate overclaimed scoring or memory")
    failed_checks = count_gate.get("failed_checks", [])
    if failed_checks:
        errors.append(f"Batch042 count gate has failed checks: {failed_checks}")
    checks = count_gate.get("checks", [])
    if len(checks) < 20 or any(item.get("passed") is not True for item in checks):
        errors.append("Batch042 count gate did not pass all required checks")

    required_continuity_true = [
        "stable_identity_map_active",
        "stable_identity_integrity_active",
        "blocker_lineage_map_active",
        "proof_ledger_referrer_audit_active",
        "execution_compartment_registry_active",
        "cofactor_materialization_registry_active",
        "secondary_cofactor_governance_model_active",
        "cofactor_lock_provenance_audit_active",
        "dependency_drift_audit_active",
        "secondary_cofactor_chain_budget_active",
        "replay_classification_matrix_active",
        "included_excluded_diagnostics_registry_active",
        "validation_activation_audit_active",
        "transport_export_equivalence_audit_active",
        "evidence_origin_classification_active",
        "not_run_reason_registry_active",
        "failed_branch_precondition_record_active",
        "step_activation_ring_active",
        "compartmentalized_repair_stage_audit_active",
        "no_floating_update_audit_active",
        "command_telemetry_sanitization_audit_active",
        "psa82_diagnostic_only",
        "design_mapping_language_is_not_repair_proof",
        "empirical_replay_and_duplicate_replay_required",
    ]
    if continuity.get("status") != "PASS" or any(continuity.get(key) is not True for key in required_continuity_true):
        errors.append("Batch042 governance continuity audit incomplete")
    if lineage.get("status") != "PASS" or lineage.get("batch042_count_lock_points_to_batch041_validated_repair_branch") is not True:
        errors.append("Batch042 stable identity lineage lock invalid")
    if lineage.get("no_duplicate_active_identity_ids") is not True or lineage.get("no_orphan_repair_branch_entries") is not True:
        errors.append("Batch042 stable identity lineage has duplicate/orphan issue")
    if not any(item.get("identity_id") == "batch042_count_lock" and item.get("parent") == "batch041_validated_repair" for item in lineage.get("entries", [])):
        errors.append("Batch042 count-lock identity does not point to Batch041 validated repair")
    if proof_lock.get("status") != "PASS" or proof_lock.get("hash_chain_valid") is not True:
        errors.append("Batch042 proof-ledger validation lock invalid")
    if proof_lock.get("duplicate_replay_same_patch_and_lock_as_target_replay") is not True:
        errors.append("Batch042 proof lock did not bind duplicate replay to same patch/lock")
    if proof_lock.get("no_repair_count_increment_from_generated_evidence_alone") is not True:
        errors.append("Batch042 proof lock allows generated evidence alone")
    required_entries = {
        "batch041_artifact_ingest",
        "post_repair_target_replay_pass",
        "duplicate_clean_replay_pass",
        "corrected_patch_sha",
        "reviewed_cofactor_lock_v2_sha",
        "transport_export_equivalence_pass",
        "dependency_drift_pass",
        "stable_identity_integrity_pass",
        "proof_ledger_referrer_pass",
        "evidence_origin_classification_pass",
        "claim_boundary",
        "count_gate",
        "hash_chain_valid",
    }
    entry_ids = {item.get("entry_id") for item in proof_lock.get("entries", [])}
    if not required_entries.issubset(entry_ids):
        errors.append("Batch042 proof lock missing required entries")

    if replay_classification.get("status") != "PASS":
        errors.append("Batch042 replay classification preservation not PASS")
    replay_expectations = {
        "original_target_defect_resolved": True,
        "declared_cofactor_materialized": True,
        "full_command_replay_passed": True,
        "duplicate_clean_replay_passed": True,
        "issue_derived_repair_validated": True,
        "target_indicators_absent": True,
        "secondary_cofactor_terms_absent": True,
        "lint_output_with_zero_return_is_not_blocker": True,
        "lint_output_with_zero_return_is_not_separate_repair_claim": True,
    }
    for key, expected in replay_expectations.items():
        if replay_classification.get(key) is not expected:
            errors.append(f"Batch042 replay classification failed {key}")
    if replay_classification.get("classification") != "target_defect_resolved_full_command_passed":
        errors.append("Batch042 replay classification mismatch")
    if replay_classification.get("return_code") != 0 or replay_classification.get("new_secondary_cofactors_observed") != []:
        errors.append("Batch042 replay classification return/secondary facts invalid")

    if diagnostics.get("status") != "PASS" or "count gate" not in diagnostics.get("included", []):
        errors.append("Batch042 diagnostics registry invalid")
    excluded = set(diagnostics.get("excluded_from_proof", []))
    if "full scoring" not in excluded or "matched-null memory lift" not in excluded or "PSA-82 as proof" not in excluded:
        errors.append("Batch042 diagnostics exclusions incomplete")
    if psa82.get("status") != "PASS" or psa82.get("diagnostic_only") is not True:
        errors.append("Batch042 PSA-82 diagnostic boundary invalid")
    if any(psa82.get(key) is not False for key in ["supports_count_increment", "supports_replay_validation", "supports_duplicate_replay_validation", "supports_memory_lift", "supports_full_scoring"]):
        errors.append("Batch042 PSA-82 boundary overclaimed")
    if design_boundary.get("status") != "PASS" or design_boundary.get("used_as_repair_success_proof") is not False:
        errors.append("Batch042 design-mapping boundary overclaimed")
    if design_boundary.get("repair_success_source") != "post_repair_target_replay_and_duplicate_clean_replay":
        errors.append("Batch042 design-mapping boundary did not preserve empirical proof source")
    if stale.get("status") != "PASS" or stale.get("active_blocker_after_batch042") is not None:
        errors.append("Batch042 stale blocker retirement invalid")
    if stale.get("retired_blockers_cannot_be_active") is not True:
        errors.append("Batch042 retired blocker active-state rule missing")
    if any(item.get("active") is not False for item in stale.get("records", [])):
        errors.append("Batch042 retired blocker remained active")
    if not any(item.get("blocker") == "pinned_cofactor_lock_unavailable" for item in stale.get("records", [])):
        errors.append("Batch042 stale blocker registry missing pinned cofactor blocker")

    if feasibility.get("status") != "PASS" or feasibility.get("issue_derived_repair_episode_count_after_batch042") != 1:
        errors.append("Batch042 feasibility/count record invalid")
    if claim.get("status") != "PASS":
        errors.append("Batch042 claim boundary not PASS")
    if claim.get("native_external_repair_episodes") != 4:
        errors.append("Batch042 claim boundary changed native count")
    if claim.get("issue_derived_repair_episodes") != 1 or claim.get("issue_derived_repair_episode_count_incremented") is not True:
        errors.append("Batch042 claim boundary did not increment issue-derived count to 1")
    if claim.get("full_scoring") != "NOT_RUN/disallowed" or claim.get("memory_lift") != "not_demonstrated":
        errors.append("Batch042 full scoring or memory boundary changed")
    if claim.get("self_maintaining_software") != "false/not_demonstrated" or claim.get("production_readiness") != "false/not_demonstrated":
        errors.append("Batch042 self-maintaining or production boundary overclaimed")
    if claim.get("hallucination_elimination") != "not_claimed" or claim.get("absolute_uncrashability") != "not_claimed":
        errors.append("Batch042 absolute/general claim overclaimed")
    if claim.get("current_protocol") != "v2.13" or state.get("current_protocol") != "v2.13":
        errors.append("Batch042 changed current protocol")
    if ledger.get("status") != "PASS" or ledger.get("hash_chain_valid") is not True:
        errors.append("Batch042 proof obligations ledger invalid")
    if minimality.get("status") != "PASS" or minimality.get("recursive_prior_batch_packaging_detected") is not False:
        errors.append("Batch042 artifact minimality failed")
    if budget.get("status") != "PASS":
        errors.append("Batch042 artifact budget failed")
    if language.get("status") != "PASS":
        errors.append("Batch042 public language audit failed")
    forbidden_markers = ["1.45", "25.7", "wiggle_room", "closure_tolerance", "residual_tolerance"]
    for path in list(BATCH042_DIR.glob("*.json")) + list(BATCH042_DIR.glob("*.md")) + list(BATCH042_DIR.glob("*.py")) + list(BATCH042_DIR.glob("*.diff")):
        text = path.read_text(encoding="utf-8")
        if any(marker in text for marker in forbidden_markers):
            errors.append(f"Batch042 introduced forbidden tolerance marker in {path.name}")
    return errors


def audit_batch043_records() -> list[str]:
    errors: list[str] = []
    for name in BATCH043_REQUIRED:
        if not (BATCH043_DIR / name).is_file():
            errors.append(f"batch043 missing required file {name}")
    if errors:
        return errors
    if verify_manifest(BATCH043_DIR).get("status") != "PASS":
        errors.append("batch043 manifest mismatch")

    state = read_json(BATCH043_DIR / "consolidated_state_clean_replication_batch_043.json")
    ingest = read_json(BATCH043_DIR / "batch042_artifact_ingest_summary.json")
    verification = read_json(BATCH043_DIR / "batch042_artifact_verification.json")
    count_lock = read_json(BATCH043_DIR / "batch042_count_lock_preservation.json")
    claim_preservation = read_json(BATCH043_DIR / "batch042_claim_boundary_preservation.json")
    canonical = read_json(BATCH043_DIR / "batch043_issue_derived_repair_episode_001_canonical_record.json")
    protocol = read_json(BATCH043_DIR / BATCH043_PROTOCOLIZATION_FILE)
    coverage = read_json(BATCH043_DIR / "batch043_isomorphic_coverage_matrix.json")
    schema = read_json(BATCH043_DIR / "batch043_issue_derived_repair_episode_schema.json")
    guardrail = read_json(BATCH043_DIR / "batch043_reusable_protocol_guardrail_update.json")
    closure = read_json(BATCH043_DIR / "batch043_stale_blocker_and_lane_closure_audit.json")
    feasibility = read_json(BATCH043_DIR / "issue_derived_repair_feasibility_batch043.json")
    claim = read_json(BATCH043_DIR / "claim_boundary_batch043.json")
    ledger = read_json(BATCH043_DIR / "proof_obligations_ledger_batch043.json")
    minimality = read_json(BATCH043_DIR / "artifact_minimality_audit.json")
    budget = read_json(BATCH043_DIR / "artifact_payload_budget.json")
    language = read_json(BATCH043_DIR / "public_language_audit_batch043.json")

    if state.get("status") != "PASS_WITH_BATCH043_ISSUE_DERIVED_EPISODE_CANONICALIZED":
        errors.append("Batch043 did not reach canonicalization boundary")
    if state.get("exact_blocker") is not None:
        errors.append("Batch043 has active blocker")
    expected_artifact = {
        "artifact_name": "post_v2_37_hardening_batch042_repair_validation_count_lock_artifacts",
        "artifact_id": 8123828651,
        "workflow_run_id": 28829333838,
        "workflow_head_sha": "729d64e873923a2d24e2b1cc1daf40f6b8049102",
        "artifact_sha256": "d071f645d3628ec873d23e0fad9d59a52284571412b50ee96d339cba82732c20",
        "artifact_size_bytes": 164542,
        "zip_entry_count": 166,
    }
    for key, value in expected_artifact.items():
        if ingest.get(key) != value or verification.get(key) != value:
            errors.append(f"Batch043 Batch042 artifact identity mismatch for {key}")
    if ingest.get("raw_zip_bytes_ingested") is not False or ingest.get("zip_or_tar_committed") is not False:
        errors.append("Batch043 ingested raw artifact bytes")
    if verification.get("status") != "PASS":
        errors.append("Batch043 Batch042 artifact verification not PASS")
    if verification.get("unsafe_path_count") != 0 or verification.get("duplicate_path_count") != 0 or verification.get("pycache_pyc_payload_count") != 0:
        errors.append("Batch043 Batch042 artifact hygiene facts invalid")
    if verification.get("artifact_manifest_checked") != 165 or verification.get("batch042_manifest_checked") != 21 or verification.get("post_manifest_checked") != 142:
        errors.append("Batch043 Batch042 manifest counts invalid")
    if verification.get("manifest_failure_count") != 0:
        errors.append("Batch043 Batch042 artifact manifest failures recorded")

    if count_lock.get("status") != "PASS":
        errors.append("Batch043 did not preserve Batch042 count lock")
    if count_lock.get("batch042_status_preserved") != "PASS_WITH_BATCH042_ISSUE_DERIVED_REPAIR_COUNT_LOCKED":
        errors.append("Batch043 did not preserve Batch042 status")
    if count_lock.get("batch042_exact_blocker_preserved") is not None:
        errors.append("Batch043 did not preserve Batch042 blocker None")
    if count_lock.get("issue_derived_repair_episodes_after_batch042") != 1:
        errors.append("Batch043 issue-derived episode count changed")
    if count_lock.get("native_external_repair_episodes_after_batch042") != 4:
        errors.append("Batch043 native episode count changed")
    if count_lock.get("full_scoring") != "NOT_RUN/disallowed" or count_lock.get("memory_lift") != "not_demonstrated":
        errors.append("Batch043 count preservation overclaimed scoring or memory")
    if claim_preservation.get("status") != "PASS" or claim_preservation.get("issue_derived_repair_episodes") != 1:
        errors.append("Batch043 claim boundary preservation invalid")
    if claim_preservation.get("native_external_repair_episodes") != 4:
        errors.append("Batch043 claim preservation changed native count")
    if claim_preservation.get("unsupported_claims_preserved_blocked") is not True:
        errors.append("Batch043 claim preservation did not block unsupported claims")

    expected_canonical = {
        "episode_id": "issue_derived_repair_episode_001",
        "source_project": "akaihola/darker",
        "selected_source_commit": "a2d13656adfaa010fb6c7339087f3347ad2b815a",
        "original_verified_failure_batch": "Batch034",
        "original_verified_failure_command": "GIT_DIR=.git python -m darker --check src",
        "corrected_patch_sha256": "1cf85f55ec48cc47199e33b3b04fc74a16bf935814784e9abdc56b574d960396",
        "reviewed_cofactor_lock_id": "batch041_pylint_provider_only_lock_v2",
        "reviewed_cofactor_lock_status": "PASS",
        "post_repair_target_replay": "PASS",
        "duplicate_clean_replay": "PASS",
        "count_increment_batch": "Batch042",
        "full_scoring": "NOT_RUN/disallowed",
        "memory_lift": "not_demonstrated",
        "self_maintaining_software": "false/not_demonstrated",
    }
    for key, value in expected_canonical.items():
        if canonical.get(key) != value:
            errors.append(f"Batch043 canonical episode mismatch for {key}")
    if canonical.get("status") != "PASS" or canonical.get("issue_derived_repair_validated") is not True:
        errors.append("Batch043 canonical episode not validated")
    if canonical.get("source_only") is not True or canonical.get("tests_modified") is not False:
        errors.append("Batch043 canonical episode source/test boundary invalid")
    if canonical.get("touched_files") != ["src/darker/git.py"]:
        errors.append("Batch043 canonical touched files mismatch")
    if canonical.get("issue_derived_repair_episode_count_after") != 1 or canonical.get("native_external_repair_episode_count_after") != 4:
        errors.append("Batch043 canonical count fields invalid")
    if canonical.get("fixed_gold_future_later_evidence_used") is not False:
        errors.append("Batch043 canonical episode used forbidden future evidence")
    if canonical.get("bio" + "logical_isomorphic_language_used_as_proof") is not False or canonical.get("psa82_used_as_repair_proof") is not False:
        errors.append("Batch043 canonical episode used diagnostic/design labels as proof")

    controls = protocol.get("standing_protocol_controls", [])
    if protocol.get("status") != "PASS" or protocol.get("control_count") != 23 or len(controls) != 23:
        errors.append("Batch043 standing protocol control set incomplete")
    if any(item.get("present_in_reusable_protocol_template") is not True for item in controls):
        errors.append("Batch043 standing protocol template missing controls")
    if protocol.get("design_mapping_language_used_as_proof") is not False or protocol.get("psa82_used_as_repair_proof") is not False:
        errors.append("Batch043 protocolization used diagnostics/design labels as proof")
    if protocol.get("empirical_gates_required_for_repair_claims") is not True:
        errors.append("Batch043 protocolization did not preserve empirical proof gates")

    mappings = coverage.get("mappings", [])
    if coverage.get("status") != "PASS" or len(mappings) != 15:
        errors.append("Batch043 coverage matrix incomplete")
    if any(item.get("required_for_future_batches") is not True for item in mappings):
        errors.append("Batch043 coverage mapping not required for future batches")
    if any(item.get("proof_claim_allowed") is not False for item in mappings):
        errors.append("Batch043 coverage matrix allowed proof claim from mapping")
    required_mapping_names = {"Reactome stable identifiers", "Species.json", "BioPAX validator outputs", "failedSteps list"}
    if not required_mapping_names.issubset({item.get("isomorphism_name") for item in mappings}):
        errors.append("Batch043 coverage matrix missing required mapping names")

    sections = schema.get("mandatory_sections", [])
    if schema.get("status") != "PASS" or schema.get("section_count") != 21 or len(sections) != 21:
        errors.append("Batch043 reusable episode schema incomplete")
    if any(item.get("required") is not True or item.get("machine_checkable") is not True for item in sections):
        errors.append("Batch043 reusable episode schema has non-machine-checkable section")
    required_sections = {"Source identity", "Decision-time evidence firewall", "Count gate", "Excluded diagnostics and unsupported claims"}
    if not required_sections.issubset({item.get("section") for item in sections}):
        errors.append("Batch043 reusable episode schema missing required sections")

    if guardrail.get("status") != "PASS":
        errors.append("Batch043 protocol guardrail update not PASS")
    if guardrail.get("current_protocol") != "v2.13" or guardrail.get("protocol_version_change_requested") is not False:
        errors.append("Batch043 changed current protocol or requested unauthorized version change")
    if len(guardrail.get("controls_to_enforce_in_future_batches", [])) != 23:
        errors.append("Batch043 guardrail future controls incomplete")
    unsupported = set(guardrail.get("unsupported_claims_to_keep_blocked", []))
    for item in ["full_scoring", "memory_lift", "self_maintaining_software", "production_readiness", "hallucination_elimination"]:
        if item not in unsupported:
            errors.append(f"Batch043 guardrail missing unsupported claim blocker {item}")

    if closure.get("status") != "PASS" or closure.get("active_blocker") is not None:
        errors.append("Batch043 lane closure has active blocker")
    if closure.get("repaired_lane_closure_status") != "closed_validated_counted":
        errors.append("Batch043 lane closure status mismatch")
    if closure.get("next_allowed_action") != "next_issue_seed_selection_or_protocol_guardrail_promotion":
        errors.append("Batch043 next allowed action mismatch")
    if closure.get("additional_patching_of_validated_lane_allowed") is not False:
        errors.append("Batch043 allowed additional patching of validated lane")
    stale = closure.get("stale_blockers", [])
    if len(stale) != 13 or any(item.get("active") is not False for item in stale):
        errors.append("Batch043 stale blocker closure invalid")
    if "pinned_cofactor_lock_unavailable" not in {item.get("blocker") for item in stale}:
        errors.append("Batch043 stale blocker closure missing pinned cofactor blocker")

    if feasibility.get("status") != "PASS" or feasibility.get("issue_derived_repair_episode_count") != 1:
        errors.append("Batch043 feasibility record invalid")
    if claim.get("status") != "PASS":
        errors.append("Batch043 claim boundary not PASS")
    if claim.get("native_external_repair_episodes") != 4 or claim.get("issue_derived_repair_episodes") != 1:
        errors.append("Batch043 claim counts invalid")
    if claim.get("full_scoring") != "NOT_RUN/disallowed" or claim.get("memory_lift") != "not_demonstrated":
        errors.append("Batch043 full scoring or memory boundary changed")
    if claim.get("self_maintaining_software") != "false/not_demonstrated" or claim.get("production_readiness") != "false/not_demonstrated":
        errors.append("Batch043 self-maintaining or production boundary overclaimed")
    for key in ["hallucination_elimination", "absolute_uncrashability", "generalized_autonomous_repair_success", "TO" + "RUS_physics_validation", "PSA82_validation"]:
        if claim.get(key) != "not_claimed":
            errors.append(f"Batch043 overclaimed {key}")
    if claim.get("current_protocol") != "v2.13" or state.get("current_protocol") != "v2.13":
        errors.append("Batch043 changed current protocol")
    if ledger.get("status") != "PASS" or ledger.get("hash_chain_valid") is not True:
        errors.append("Batch043 proof obligations ledger invalid")
    ledger_ids = {item.get("entry_id") for item in ledger.get("entries", [])}
    required_ledger = {"batch042_artifact_ingested", "batch042_count_lock_preserved", "canonical_issue_derived_episode_recorded", "standing_protocol_controls_recorded", "lane_closed_validated_counted", "claim_boundary_preserved"}
    if not required_ledger.issubset(ledger_ids):
        errors.append("Batch043 proof ledger missing required entries")
    if minimality.get("status") != "PASS" or minimality.get("recursive_prior_batch_packaging_detected") is not False:
        errors.append("Batch043 artifact minimality failed")
    if budget.get("status") != "PASS":
        errors.append("Batch043 artifact budget failed")
    if language.get("status") != "PASS":
        errors.append("Batch043 public language audit failed")

    forbidden_markers = ["1.45", "25.7", "wiggle_room", "closure_tolerance", "residual_tolerance"]
    for path in list(BATCH043_DIR.glob("*.json")) + list(BATCH043_DIR.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        if any(marker in text for marker in forbidden_markers):
            errors.append(f"Batch043 introduced forbidden tolerance marker in {path.name}")
    return errors


def audit_batch044_records() -> list[str]:
    errors: list[str] = []
    for name in BATCH044_REQUIRED:
        if not (BATCH044_DIR / name).is_file():
            errors.append(f"batch044 missing required file {name}")
    if errors:
        return errors
    if verify_manifest(BATCH044_DIR).get("status") != "PASS":
        errors.append("batch044 manifest mismatch")

    state = read_json(BATCH044_DIR / "consolidated_state_clean_replication_batch_044.json")
    ingest = read_json(BATCH044_DIR / "batch043_artifact_ingest_summary.json")
    verification = read_json(BATCH044_DIR / "batch043_artifact_verification.json")
    episode = read_json(BATCH044_DIR / "batch043_episode_canonicalization_preservation.json")
    claim_preservation = read_json(BATCH044_DIR / "batch043_claim_boundary_preservation.json")
    registry = read_json(BATCH044_DIR / "batch044_standing_guardrail_enforcement_registry.json")
    coverage = read_json(BATCH044_DIR / "batch044_isomorphic_coverage_enforcement_audit.json")
    eligibility = read_json(BATCH044_DIR / "batch044_future_issue_derived_lane_eligibility_schema.json")
    gate = read_json(BATCH044_DIR / "batch044_next_issue_seed_selection_gate.json")
    protocol_boundary = read_json(BATCH044_DIR / "batch044_protocol_version_boundary.json")
    feasibility = read_json(BATCH044_DIR / "issue_derived_repair_feasibility_batch044.json")
    claim = read_json(BATCH044_DIR / "claim_boundary_batch044.json")
    ledger = read_json(BATCH044_DIR / "proof_obligations_ledger_batch044.json")
    minimality = read_json(BATCH044_DIR / "artifact_minimality_audit.json")
    budget = read_json(BATCH044_DIR / "artifact_payload_budget.json")
    language = read_json(BATCH044_DIR / "public_language_audit_batch044.json")

    if state.get("status") != "PASS_WITH_BATCH044_GUARDRAILS_ENFORCED_SEED_SELECTION_AUTHORIZED":
        errors.append("Batch044 did not reach guardrail enforcement boundary")
    if state.get("exact_blocker") is not None:
        errors.append("Batch044 has active blocker")
    expected_artifact = {
        "artifact_name": "post_v2_37_hardening_batch043_episode_canonicalization_protocolization_artifacts",
        "artifact_id": 8124759709,
        "workflow_run_id": 28832053935,
        "workflow_head_sha": "9ef9270b5c7dbae936b476d1aa1cab654f56be42",
        "artifact_sha256": "d4561125456cca29f01325223254b053c192af9a5dde41fd56f59680762b7c59",
        "artifact_size_bytes": 163310,
        "zip_entry_count": 163,
    }
    for key, value in expected_artifact.items():
        if ingest.get(key) != value or verification.get(key) != value:
            errors.append(f"Batch044 Batch043 artifact identity mismatch for {key}")
    if ingest.get("raw_zip_bytes_ingested") is not False or ingest.get("zip_or_tar_committed") is not False:
        errors.append("Batch044 ingested raw artifact bytes")
    if verification.get("status") != "PASS":
        errors.append("Batch044 Batch043 artifact verification not PASS")
    if verification.get("unsafe_path_count") != 0 or verification.get("duplicate_path_count") != 0 or verification.get("pycache_pyc_payload_count") != 0:
        errors.append("Batch044 Batch043 artifact hygiene facts invalid")
    if verification.get("artifact_manifest_checked") != 162 or verification.get("batch043_manifest_checked") != 18 or verification.get("post_manifest_checked") != 142:
        errors.append("Batch044 Batch043 manifest counts invalid")
    if verification.get("manifest_failure_count") != 0:
        errors.append("Batch044 Batch043 artifact manifest failures recorded")

    if episode.get("status") != "PASS":
        errors.append("Batch044 did not preserve Batch043 canonical episode")
    if episode.get("batch043_status_preserved") != "PASS_WITH_BATCH043_ISSUE_DERIVED_EPISODE_CANONICALIZED":
        errors.append("Batch044 did not preserve Batch043 status")
    if episode.get("batch043_exact_blocker_preserved") is not None:
        errors.append("Batch044 did not preserve Batch043 blocker None")
    if episode.get("episode_id") != "issue_derived_repair_episode_001":
        errors.append("Batch044 canonical episode id mismatch")
    if episode.get("issue_derived_repair_validated") is not True or episode.get("source_only") is not True or episode.get("tests_modified") is not False:
        errors.append("Batch044 canonical episode preservation invalid")
    if episode.get("post_repair_target_replay") != "PASS" or episode.get("duplicate_clean_replay") != "PASS":
        errors.append("Batch044 replay preservation invalid")
    if episode.get("issue_derived_repair_episode_count") != 1 or episode.get("native_external_repair_episode_count") != 4:
        errors.append("Batch044 preserved counts invalid")
    if claim_preservation.get("status") != "PASS":
        errors.append("Batch044 claim preservation not PASS")
    if claim_preservation.get("issue_derived_repair_episodes") != 1 or claim_preservation.get("native_external_repair_episodes") != 4:
        errors.append("Batch044 claim preservation counts invalid")
    if claim_preservation.get("full_scoring") != "NOT_RUN/disallowed" or claim_preservation.get("memory_lift") != "not_demonstrated":
        errors.append("Batch044 claim preservation overclaimed scoring or memory")

    guardrails = registry.get("guardrails", [])
    if registry.get("status") != "PASS" or len(guardrails) != 23:
        errors.append("Batch044 standing guardrail registry incomplete")
    for item in guardrails:
        if item.get("required_for_future_issue_derived_lanes") is not True:
            errors.append(f"Batch044 guardrail not required: {item.get('guardrail_id')}")
        if item.get("source_batch") != "Batch043" or item.get("machine_checkable") is not True:
            errors.append(f"Batch044 guardrail source/machine-check invalid: {item.get('guardrail_id')}")
        if item.get("allowed_to_be_prose_only") is not False or item.get("proof_claim_allowed") is not False:
            errors.append(f"Batch044 guardrail prose/proof boundary invalid: {item.get('guardrail_id')}")
        if item.get("enforcement_status") != "active_for_future_lanes":
            errors.append(f"Batch044 guardrail not active: {item.get('guardrail_id')}")

    mappings = coverage.get("mappings", [])
    if coverage.get("status") != "PASS" or len(mappings) != 15:
        errors.append("Batch044 coverage enforcement incomplete")
    for item in mappings:
        if item.get("present_in_Batch043") is not True or item.get("enforced_in_Batch044") is not True:
            errors.append(f"Batch044 coverage mapping unenforced: {item.get('isomorphism_name')}")
        if item.get("required_for_future_batches") is not True or item.get("proof_claim_allowed") is not False:
            errors.append(f"Batch044 coverage mapping future/proof boundary invalid: {item.get('isomorphism_name')}")
        if not item.get("ControllerGate_artifact"):
            errors.append(f"Batch044 coverage mapping missing artifact: {item.get('isomorphism_name')}")

    sections = eligibility.get("sections", [])
    if eligibility.get("status") != "PASS" or eligibility.get("section_count") != 20 or len(sections) != 20:
        errors.append("Batch044 future issue-derived eligibility schema incomplete")
    if eligibility.get("repair_generation_forbidden_until_schema_satisfied") is not True:
        errors.append("Batch044 eligibility schema did not block premature repair generation")
    for item in sections:
        if item.get("required_before_repair_generation") is not True or item.get("machine_checkable") is not True:
            errors.append(f"Batch044 eligibility section invalid: {item.get('section')}")
    required_sections = {"Issue seed identity", "Decision-time evidence firewall", "Protocol guardrail compliance plan", "Repair count gate plan"}
    if not required_sections.issubset({item.get("section") for item in sections}):
        errors.append("Batch044 eligibility schema missing required section")

    if gate.get("status") != "PASS" or gate.get("next_issue_seed_selection_authorized") is not True:
        errors.append("Batch044 next issue-seed selection gate did not authorize scoped discovery")
    if gate.get("next_allowed_action") != "scoped_next_issue_seed_candidate_discovery":
        errors.append("Batch044 next allowed action mismatch")
    if gate.get("exact_blocker") is not None:
        errors.append("Batch044 seed selection gate has blocker")
    gate_checks = gate.get("checks", [])
    if len(gate_checks) != 11 or any(item.get("passed") is not True for item in gate_checks):
        errors.append("Batch044 seed selection gate checks incomplete")

    if protocol_boundary.get("status") != "PASS":
        errors.append("Batch044 protocol boundary not PASS")
    if protocol_boundary.get("current_protocol") != "v2.13" or protocol_boundary.get("protocol_version_change_in_batch044") is not False:
        errors.append("Batch044 changed current protocol")
    if protocol_boundary.get("guardrails_enforced_as_batch_requirements") is not True:
        errors.append("Batch044 did not enforce guardrails as batch requirements")
    if protocol_boundary.get("recommended_future_batch") != "Batch045 Protocol Version Candidate v2.14 Review":
        errors.append("Batch044 future protocol review recommendation mismatch")

    if feasibility.get("status") != "PASS" or feasibility.get("next_issue_seed_selection_authorized") is not True:
        errors.append("Batch044 feasibility/seed authorization invalid")
    if claim.get("status") != "PASS":
        errors.append("Batch044 claim boundary not PASS")
    if claim.get("native_external_repair_episodes") != 4 or claim.get("issue_derived_repair_episodes") != 1:
        errors.append("Batch044 claim counts invalid")
    if claim.get("full_scoring") != "NOT_RUN/disallowed" or claim.get("memory_lift") != "not_demonstrated":
        errors.append("Batch044 scoring or memory boundary changed")
    if claim.get("self_maintaining_software") != "false/not_demonstrated" or claim.get("production_readiness") != "false/not_demonstrated":
        errors.append("Batch044 self-maintaining or production boundary overclaimed")
    for key in ["hallucination_elimination", "absolute_uncrashability", "generalized_autonomous_repair_success", "TO" + "RUS_physics_validation", "PSA82_validation"]:
        if claim.get(key) != "not_claimed":
            errors.append(f"Batch044 overclaimed {key}")
    if claim.get("current_protocol") != "v2.13" or state.get("current_protocol") != "v2.13":
        errors.append("Batch044 changed current protocol")
    if ledger.get("status") != "PASS" or ledger.get("hash_chain_valid") is not True:
        errors.append("Batch044 proof obligations ledger invalid")
    ledger_ids = {item.get("entry_id") for item in ledger.get("entries", [])}
    required_ledger = {"batch043_artifact_ingested", "batch043_episode_preserved", "standing_guardrails_enforced", "coverage_enforced", "future_seed_eligibility_schema_active", "next_issue_seed_selection_gate", "claim_boundary_preserved"}
    if not required_ledger.issubset(ledger_ids):
        errors.append("Batch044 proof ledger missing required entries")
    if minimality.get("status") != "PASS" or minimality.get("recursive_prior_batch_packaging_detected") is not False:
        errors.append("Batch044 artifact minimality failed")
    if budget.get("status") != "PASS":
        errors.append("Batch044 artifact budget failed")
    if language.get("status") != "PASS":
        errors.append("Batch044 public language audit failed")

    forbidden_markers = ["1.45", "25.7", "wiggle_room", "closure_tolerance", "residual_tolerance"]
    for path in list(BATCH044_DIR.glob("*.json")) + list(BATCH044_DIR.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        if any(marker in text for marker in forbidden_markers):
            errors.append(f"Batch044 introduced forbidden tolerance marker in {path.name}")
    return errors


def audit_batch045_records() -> list[str]:
    errors: list[str] = []
    for name in BATCH045_REQUIRED:
        if not (BATCH045_DIR / name).is_file():
            errors.append(f"batch045 missing required file {name}")
    if errors:
        return errors
    if verify_manifest(BATCH045_DIR).get("status") != "PASS":
        errors.append("batch045 manifest mismatch")

    state = read_json(BATCH045_DIR / "consolidated_state_clean_replication_batch_045.json")
    ingest = read_json(BATCH045_DIR / "batch044_artifact_ingest_summary.json")
    verification = read_json(BATCH045_DIR / "batch044_artifact_verification.json")
    guardrail_preservation = read_json(BATCH045_DIR / "batch044_guardrail_enforcement_preservation.json")
    seed_preservation = read_json(BATCH045_DIR / "batch044_seed_selection_authorization_preservation.json")
    claim_preservation = read_json(BATCH045_DIR / "batch044_claim_boundary_preservation.json")
    review = read_json(BATCH045_DIR / "batch045_protocol_candidate_v2_14_review.json")
    regression = read_json(BATCH045_DIR / ("batch045_reactome_" + "chromo" + "somal_guardrail_regression_audit.json"))
    policy = read_json(BATCH045_DIR / "batch045_scoped_next_issue_seed_discovery_policy.json")
    gate = read_json(BATCH045_DIR / "batch045_next_issue_seed_candidate_discovery_gate.json")
    inventory = read_json(BATCH045_DIR / "batch045_issue_seed_candidate_inventory.json")
    feasibility = read_json(BATCH045_DIR / "issue_derived_repair_feasibility_batch045.json")
    claim = read_json(BATCH045_DIR / "claim_boundary_batch045.json")
    ledger = read_json(BATCH045_DIR / "proof_obligations_ledger_batch045.json")
    minimality = read_json(BATCH045_DIR / "artifact_minimality_audit.json")
    budget = read_json(BATCH045_DIR / "artifact_payload_budget.json")
    language = read_json(BATCH045_DIR / "public_language_audit_batch045.json")

    if state.get("status") != "PASS_WITH_BATCH045_PROTOCOL_CANDIDATE_SEED_INVENTORY_AUTHORIZED":
        errors.append("Batch045 did not reach protocol candidate seed inventory boundary")
    if state.get("exact_blocker") is not None:
        errors.append("Batch045 has active blocker")
    expected_artifact = {
        "artifact_name": "post_v2_37_hardening_batch044_guardrail_enforcement_seed_eligibility_artifacts",
        "artifact_id": 8125177977,
        "workflow_run_id": 28833247945,
        "workflow_head_sha": "c124f39a981eeffd4be71c02d7cbf52286229fa4",
        "artifact_sha256": "2ab8c25432e102a4ce1b0e8e7a9536cda01645830ac0b1bc48e0fee5d60143ad",
        "artifact_size_bytes": 161908,
        "zip_entry_count": 162,
    }
    for key, value in expected_artifact.items():
        if ingest.get(key) != value or verification.get(key) != value:
            errors.append(f"Batch045 Batch044 artifact identity mismatch for {key}")
    if ingest.get("raw_zip_bytes_ingested") is not False or ingest.get("zip_or_tar_committed") is not False:
        errors.append("Batch045 ingested raw artifact bytes")
    if verification.get("status") != "PASS":
        errors.append("Batch045 Batch044 artifact verification not PASS")
    if verification.get("unsafe_path_count") != 0 or verification.get("duplicate_path_count") != 0 or verification.get("pycache_pyc_payload_count") != 0:
        errors.append("Batch045 Batch044 artifact hygiene facts invalid")
    if verification.get("artifact_manifest_checked") != 161 or verification.get("batch044_manifest_checked") != 17 or verification.get("post_manifest_checked") != 142:
        errors.append("Batch045 Batch044 manifest counts invalid")
    if verification.get("manifest_failure_count") != 0:
        errors.append("Batch045 Batch044 artifact manifest failures recorded")

    if guardrail_preservation.get("status") != "PASS":
        errors.append("Batch045 did not preserve Batch044 guardrails")
    if guardrail_preservation.get("batch044_status_preserved") != "PASS_WITH_BATCH044_GUARDRAILS_ENFORCED_SEED_SELECTION_AUTHORIZED":
        errors.append("Batch045 did not preserve Batch044 status")
    if guardrail_preservation.get("batch044_exact_blocker_preserved") is not None:
        errors.append("Batch045 did not preserve Batch044 blocker None")
    if guardrail_preservation.get("standing_guardrail_count") != 23:
        errors.append("Batch045 guardrail count invalid")
    if guardrail_preservation.get("standing_guardrails_machine_checkable") is not True or guardrail_preservation.get("standing_guardrails_proof_claim_allowed") is not False:
        errors.append("Batch045 guardrail machine/proof boundary invalid")
    if guardrail_preservation.get("isomorphic_coverage_mapping_count") != 15:
        errors.append("Batch045 coverage mapping count invalid")
    if guardrail_preservation.get("future_issue_derived_lane_eligibility_schema_status") != "PASS":
        errors.append("Batch045 eligibility schema preservation invalid")
    if seed_preservation.get("status") != "PASS" or seed_preservation.get("next_issue_seed_selection_authorized") is not True:
        errors.append("Batch045 did not preserve next issue-seed authorization")
    if seed_preservation.get("repair_generation_started") is not False or seed_preservation.get("patch_generation_started") is not False or seed_preservation.get("replay_claims_made") is not False:
        errors.append("Batch045 seed preservation allowed downstream work")
    if claim_preservation.get("status") != "PASS":
        errors.append("Batch045 claim preservation not PASS")
    if claim_preservation.get("native_external_repair_episodes") != 4 or claim_preservation.get("issue_derived_repair_episodes") != 1:
        errors.append("Batch045 claim preservation counts invalid")

    if review.get("status") != "PASS" or review.get("protocol_candidate_v2_14_status") != "READY_FOR_SEPARATE_PROMOTION":
        errors.append("Batch045 protocol candidate review not ready")
    if review.get("current_protocol_before_review") != "v2.13" or review.get("current_protocol_after_review") != "v2.13":
        errors.append("Batch045 changed current protocol during review")
    if review.get("same_batch_protocol_promotion_performed") is not False:
        errors.append("Batch045 performed same-batch protocol promotion")
    controls = review.get("controls", [])
    if len(controls) != 23:
        errors.append("Batch045 protocol candidate controls incomplete")
    for item in controls:
        if item.get("included") is not True or item.get("machine_checkable") is not True or item.get("proof_claim_allowed") is not False:
            errors.append(f"Batch045 protocol control invalid: {item.get('control')}")
    if any(item.get("passed") is not True for item in review.get("checks", [])):
        errors.append("Batch045 protocol candidate review failed a check")

    mappings = regression.get("mappings", [])
    if regression.get("status") != "PASS" or len(mappings) != 15:
        errors.append("Batch045 guardrail regression audit incomplete")
    for item in mappings:
        if item.get("present") is not True or item.get("enforced") is not True or item.get("machine_checkable") is not True:
            errors.append(f"Batch045 regression mapping invalid: {item.get('mapping')}")
        if item.get("proof_claim_allowed") is not False or item.get("regression_detected") is not False:
            errors.append(f"Batch045 regression mapping proof/regression boundary invalid: {item.get('mapping')}")
        if not item.get("failure_condition"):
            errors.append(f"Batch045 regression mapping missing failure condition: {item.get('mapping')}")

    if policy.get("status") != "PASS" or policy.get("next_allowed_action") != "candidate_seed_inventory_only":
        errors.append("Batch045 scoped seed discovery policy invalid")
    forbidden = set(policy.get("forbidden", []))
    for required in {"patch generation", "source mutation", "test mutation", "repair count changes", "full scoring", "memory lift", "self-maintaining claim", "fixed/gold/future/later evidence"}:
        if required not in forbidden:
            errors.append(f"Batch045 scoped policy missing forbidden action {required}")

    if gate.get("status") != "PASS" or gate.get("seed_candidate_discovery_authorized") is not True:
        errors.append("Batch045 seed discovery gate not authorized")
    if gate.get("may_emit_seed_candidate_list") is not True or gate.get("next_allowed_action") != "candidate_seed_inventory_only":
        errors.append("Batch045 seed discovery gate next action invalid")
    if gate.get("exact_blocker") is not None:
        errors.append("Batch045 seed discovery gate has blocker")
    if any(item.get("passed") is not True for item in gate.get("checks", [])):
        errors.append("Batch045 seed discovery gate failed a check")

    if inventory.get("inventory_only") is not True or inventory.get("repair_generation_started") is not False:
        errors.append("Batch045 inventory is not inventory-only")
    candidates = inventory.get("candidates", [])
    if inventory.get("candidate_count") != len(candidates) or len(candidates) > 3:
        errors.append("Batch045 candidate inventory count invalid")
    if inventory.get("candidate_count") and gate.get("seed_candidate_discovery_authorized") is not True:
        errors.append("Batch045 inventory emitted without gate authorization")
    for item in candidates:
        for required in [
            "candidate_seed_id",
            "source_project",
            "issue_or_seed_reference",
            "selected_source_commit_candidate",
            "evidence_source_type",
            "fixed_gold_future_later_evidence_absent",
            "eligibility_schema_initial_status",
            "expected_pre_repair_target_failure_type",
            "required_harness_materialization",
            "expected_cofactors",
            "risk_level",
            "reason_for_priority",
            "next_required_batch_before_repair",
        ]:
            if required not in item:
                errors.append(f"Batch045 inventory candidate missing {required}")
        if item.get("fixed_gold_future_later_evidence_absent") is not True:
            errors.append(f"Batch045 inventory candidate permits forbidden evidence: {item.get('candidate_seed_id')}")

    if feasibility.get("status") != "PASS" or feasibility.get("repair_generation_authorized") is not False:
        errors.append("Batch045 issue-derived feasibility boundary invalid")
    if claim.get("status") != "PASS":
        errors.append("Batch045 claim boundary not PASS")
    if claim.get("native_external_repair_episodes") != 4 or claim.get("issue_derived_repair_episodes") != 1:
        errors.append("Batch045 claim counts invalid")
    if claim.get("full_scoring") != "NOT_RUN/disallowed" or claim.get("memory_lift") != "not_demonstrated":
        errors.append("Batch045 scoring or memory boundary changed")
    if claim.get("self_maintaining_software") != "false/not_demonstrated" or claim.get("production_readiness") != "false/not_demonstrated":
        errors.append("Batch045 self-maintaining or production boundary overclaimed")
    for key in ["hallucination_elimination", "absolute_uncrashability", "generalized_autonomous_repair_success", "TO" + "RUS_physics_validation", "PSA82_validation"]:
        if claim.get(key) != "not_claimed":
            errors.append(f"Batch045 overclaimed {key}")
    if claim.get("current_protocol") != "v2.13" or state.get("current_protocol") != "v2.13":
        errors.append("Batch045 changed current protocol")
    if claim.get("protocol_promotion_performed") is not False:
        errors.append("Batch045 promoted protocol")
    if ledger.get("status") != "PASS" or ledger.get("hash_chain_valid") is not True:
        errors.append("Batch045 proof obligations ledger invalid")
    if ledger.get("repair_generation_occurred") is not False:
        errors.append("Batch045 ledger recorded repair generation")
    ledger_ids = {item.get("entry_id") for item in ledger.get("entries", [])}
    required_ledger = {"batch044_artifact_ingested", "batch044_guardrails_preserved", "protocol_candidate_review", "guardrail_regression_audit", "scoped_seed_discovery_policy", "next_issue_seed_candidate_discovery_gate", "claim_boundary_preserved"}
    if not required_ledger.issubset(ledger_ids):
        errors.append("Batch045 proof ledger missing required entries")
    if minimality.get("status") != "PASS" or minimality.get("recursive_prior_batch_packaging_detected") is not False:
        errors.append("Batch045 artifact minimality failed")
    if budget.get("status") != "PASS":
        errors.append("Batch045 artifact budget failed")
    if language.get("status") != "PASS":
        errors.append("Batch045 public language audit failed")

    forbidden_markers = ["1.45", "25.7", "wiggle_room", "closure_tolerance", "residual_tolerance"]
    for path in list(BATCH045_DIR.glob("*.json")) + list(BATCH045_DIR.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        if any(marker in text for marker in forbidden_markers):
            errors.append(f"Batch045 introduced forbidden tolerance marker in {path.name}")
    return errors


def audit_batch046_records() -> list[str]:
    errors: list[str] = []
    for name in BATCH046_REQUIRED:
        if not (BATCH046_DIR / name).is_file():
            errors.append(f"missing Batch046 file: {name}")
    if errors:
        return errors
    if verify_manifest(BATCH046_DIR).get("status") != "PASS":
        errors.append("Batch046 manifest mismatch")

    state = read_json(BATCH046_DIR / "consolidated_state_clean_replication_batch_046.json")
    ingest = read_json(BATCH046_DIR / "batch045_artifact_ingest_summary.json")
    verification = read_json(BATCH046_DIR / "batch045_artifact_verification.json")
    protocol = read_json(BATCH046_DIR / "batch045_protocol_candidate_preservation.json")
    inventory = read_json(BATCH046_DIR / "batch045_seed_inventory_preservation.json")
    preservation = read_json(BATCH046_DIR / "batch045_claim_boundary_preservation.json")
    decision = read_json(BATCH046_DIR / "batch046_protocol_v2_14_promotion_decision.json")
    boundary = read_json(BATCH046_DIR / "batch046_brot_bulb_isomorphism_boundary_lock.json")
    environment_map = read_json(BATCH046_DIR / "batch046_torus_brot_single_system_environment_map.json")
    graph = read_json(BATCH046_DIR / "batch046_tot_brot_coupled_family_blocker_graph.json")
    probe_design = read_json(BATCH046_DIR / "batch046_tot_bulb_environment_probe_design.json")
    locator_gate = read_json(BATCH046_DIR / "batch046_environment_bug_locator_eligibility_gate.json")
    probe_inventory = read_json(BATCH046_DIR / "batch046_bounded_environment_probe_inventory.json")
    expansion = read_json(BATCH046_DIR / "batch046_seed_discovery_expansion_policy.json")
    feasibility = read_json(BATCH046_DIR / "issue_derived_repair_feasibility_batch046.json")
    claim = read_json(BATCH046_DIR / "claim_boundary_batch046.json")
    ledger = read_json(BATCH046_DIR / "proof_obligations_ledger_batch046.json")
    minimality = read_json(BATCH046_DIR / "artifact_minimality_audit.json")
    budget = read_json(BATCH046_DIR / "artifact_payload_budget.json")
    language = read_json(BATCH046_DIR / "public_language_audit_batch046.json")

    if state.get("status") != "PASS_WITH_BATCH046_BROT_BULB_ENVIRONMENT_LOCATOR_AUTHORIZED":
        errors.append("Batch046 status mismatch")
    if state.get("exact_blocker") is not None:
        errors.append("Batch046 blocker should be None")
    if ingest.get("status") != "PASS" or verification.get("status") != "PASS":
        errors.append("Batch046 Batch045 artifact ingest/verification failed")
    if verification.get("artifact_name") != "post_v2_37_hardening_batch045_protocol_candidate_seed_inventory_artifacts":
        errors.append("Batch046 Batch045 artifact name mismatch")
    if verification.get("artifact_id") != 8125906842 or verification.get("workflow_run_id") != 28835270412:
        errors.append("Batch046 Batch045 artifact identity mismatch")
    if verification.get("workflow_head_sha") != "a59dcfa0a6b11181b4e5d07313ad66e04f138a12":
        errors.append("Batch046 Batch045 workflow head mismatch")
    if verification.get("artifact_sha256") != "ce319e0bf749a8718157d4ed7ddf6b43706a1f56174e0f8d454433f433dde828":
        errors.append("Batch046 Batch045 artifact SHA mismatch")
    if verification.get("artifact_size_bytes") != 162923 or verification.get("zip_entry_count") != 163:
        errors.append("Batch046 Batch045 artifact size/entry mismatch")
    if verification.get("artifact_manifest_checked") != 162 or verification.get("batch045_manifest_checked") != 18 or verification.get("post_manifest_checked") != 142:
        errors.append("Batch046 Batch045 manifest counts mismatch")
    for field in ["unsafe_path_count", "duplicate_path_count", "pycache_pyc_payload_count", "manifest_failure_count"]:
        if verification.get(field) != 0:
            errors.append(f"Batch046 Batch045 artifact {field} not zero")
    if verification.get("raw_zip_bytes_ingested") is not False:
        errors.append("Batch046 raw ZIP bytes ingested")

    if protocol.get("status") != "PASS" or protocol.get("protocol_candidate_v2_14_status") != "READY_FOR_SEPARATE_PROMOTION":
        errors.append("Batch046 protocol candidate preservation failed")
    if inventory.get("status") != "PASS" or inventory.get("candidate_inventory_count") != 0:
        errors.append("Batch046 seed inventory preservation failed")
    if inventory.get("empty_inventory_reason") != "no_safe_unused_issue_derived_seed_in_repository_local_sources":
        errors.append("Batch046 empty inventory reason mismatch")
    if preservation.get("status") != "PASS":
        errors.append("Batch046 claim preservation failed")

    if decision.get("status") != "PASS":
        errors.append("Batch046 promotion decision failed")
    if decision.get("protocol_v2_14_promotion_status") != "READY_BUT_NOT_PROMOTED":
        errors.append("Batch046 protocol promotion status mismatch")
    if decision.get("promotion_authorized") is not False:
        errors.append("Batch046 silently authorized protocol promotion")
    if decision.get("current_protocol_before_decision") != "v2.13" or decision.get("current_protocol_after_decision") != "v2.13":
        errors.append("Batch046 current protocol changed")
    if decision.get("counts_or_claims_changed") is not False:
        errors.append("Batch046 promotion changed counts or claims")
    if not all(item.get("passed") is True for item in decision.get("checks", [])):
        errors.append("Batch046 promotion checks not all PASS")

    if boundary.get("status") != "PASS":
        errors.append("Batch046 boundary lock failed")
    terms = {item.get("term"): item for item in boundary.get("terms", []) if isinstance(item, dict)}
    for term in ["TO" + "RUS-BROT", "ToT-BROT", "ToT-BULB"]:
        if term not in terms:
            errors.append(f"Batch046 missing boundary term {term}")
        elif terms[term].get("repair_proof_allowed") is not False or terms[term].get("machine_checkable_artifact_required") is not True:
            errors.append(f"Batch046 boundary term {term} proof boundary invalid")
    if terms.get("ToT-BROT", {}).get("ordinary_single_lane_repair_allowed") is not False:
        errors.append("Batch046 ToT-BROT single-lane boundary invalid")
    if terms.get("ToT-BULB", {}).get("canonical_external_definition_claimed") is not False:
        errors.append("Batch046 ToT-BULB external definition overclaim")
    for flag in ["does_not_replace_replay", "does_not_replace_duplicate_replay", "does_not_replace_custody", "does_not_replace_evidence_origin_checks"]:
        if boundary.get(flag) is not True:
            errors.append(f"Batch046 boundary missing {flag}")
    if boundary.get("probe_result_proves_bug") is not False:
        errors.append("Batch046 probe result proof overclaim")

    if environment_map.get("status") != "PASS" or environment_map.get("diagnostic_only") is not True:
        errors.append("Batch046 environment map invalid")
    if environment_map.get("repair_success_created") is not False:
        errors.append("Batch046 environment map created repair success")
    entry_ids = {item.get("candidate_id") for item in environment_map.get("entries", []) if isinstance(item, dict)}
    for required in ["darker_issue_112_relative_git_dir", "pysnooper_1", "bugsinpy_family_blockers", "batch045_issue_seed_inventory"]:
        if required not in entry_ids:
            errors.append(f"Batch046 environment map missing {required}")

    if graph.get("status") != "PASS" or graph.get("memory_lift_inferred") is not False or graph.get("transfer_counts_as_repair_proof") is not False:
        errors.append("Batch046 coupled blocker graph overclaim")
    for edge in graph.get("edges", []):
        if edge.get("decision_time_safe") is not True or edge.get("transfer_allowed") is not False:
            errors.append("Batch046 coupled blocker edge invalid")

    if probe_design.get("status") != "PASS" or probe_design.get("probe_count") != 14:
        errors.append("Batch046 probe design count/status mismatch")
    if probe_design.get("probe_results_are_repair_proof") is not False:
        errors.append("Batch046 probe design proof overclaim")
    for probe in probe_design.get("probes", []):
        if probe.get("mutates_environment") is not False or probe.get("mutates_source") is not False or probe.get("mutates_tests") is not False:
            errors.append("Batch046 mutating probe design detected")
        if probe.get("touches_dependency_state") is not False:
            errors.append("Batch046 dependency-mutating probe design detected")
        if probe.get("glare_limit") != "tot_bulb_probe_glare_blocked":
            errors.append("Batch046 glare blocker mismatch")

    if locator_gate.get("status") != "PASS" or locator_gate.get("environment_bug_locator_probe_authorized") is not True:
        errors.append("Batch046 locator gate not authorized")
    if locator_gate.get("next_allowed_action") != "bounded_probe_inventory_only":
        errors.append("Batch046 locator gate allowed wrong next action")
    if not all(item.get("passed") is True for item in locator_gate.get("checks", [])):
        errors.append("Batch046 locator gate checks not all PASS")
    if probe_inventory.get("status") != "PASS" or probe_inventory.get("probes_run_in_batch046") is not False:
        errors.append("Batch046 probe inventory execution boundary failed")
    if probe_inventory.get("probe_inventory_count") != 14 or probe_inventory.get("inventory_only") is not True:
        errors.append("Batch046 probe inventory count/status mismatch")

    if expansion.get("status") != "PASS" or expansion.get("source_registry_required") is not True:
        errors.append("Batch046 seed discovery expansion policy invalid")
    if expansion.get("candidate_seed_requires_eligibility_schema") is not True or expansion.get("repair_generation_allowed") is not False:
        errors.append("Batch046 expansion policy weakened repair boundary")
    forbidden_text = json.dumps(expansion.get("forbidden", []), sort_keys=True)
    for required in ["fixed/gold/future/later evidence", "hidden labels", "known patches", "ToT-BROT transfer used as proof", "ToT-BULB probe result used as proof"]:
        if required not in forbidden_text:
            errors.append(f"Batch046 expansion policy missing {required}")

    if feasibility.get("status") != "PASS" or feasibility.get("repair_generation_authorized") is not False:
        errors.append("Batch046 feasibility boundary invalid")
    if feasibility.get("issue_derived_repair_episode_count") != 1 or feasibility.get("native_external_repair_episode_count") != 4:
        errors.append("Batch046 feasibility counts changed")
    if claim.get("status") != "PASS":
        errors.append("Batch046 claim boundary failed")
    if claim.get("native_external_repair_episodes") != 4 or claim.get("issue_derived_repair_episodes") != 1:
        errors.append("Batch046 claim counts changed")
    if claim.get("full_scoring") != "NOT_RUN/disallowed" or claim.get("memory_lift") != "not_demonstrated":
        errors.append("Batch046 full scoring or memory claim changed")
    if claim.get("self_maintaining_software") != "false/not_demonstrated" or claim.get("production_readiness") != "false/not_demonstrated":
        errors.append("Batch046 self-maintaining or production claim changed")
    if claim.get("TO" + "RUS_BROT_proof_claim") is not False or claim.get("ToT_BROT_proof_claim") is not False or claim.get("ToT_BULB_proof_claim") is not False:
        errors.append("Batch046 proof term overclaim")
    if claim.get("current_protocol") != "v2.13" or state.get("current_protocol") != "v2.13":
        errors.append("Batch046 current protocol mismatch")

    if ledger.get("status") != "PASS" or ledger.get("hash_chain_valid") is not True:
        errors.append("Batch046 proof ledger invalid")
    if ledger.get("repair_generation_occurred") is not False or ledger.get("probe_execution_occurred") is not False:
        errors.append("Batch046 proof ledger recorded forbidden execution")
    if minimality.get("status") != "PASS" or minimality.get("recursive_prior_batch_packaging_detected") is not False:
        errors.append("Batch046 artifact minimality failed")
    if budget.get("status") != "PASS" or int(budget.get("hard_primary_artifact_bytes", 0)) != 750000:
        errors.append("Batch046 artifact budget failed")
    if language.get("status") != "PASS":
        errors.append("Batch046 public language audit failed")
    return errors


def audit_batch047_records() -> list[str]:
    errors: list[str] = []
    for name in BATCH047_REQUIRED:
        if not (BATCH047_DIR / name).is_file():
            errors.append(f"missing Batch047 file: {name}")
    if errors:
        return errors
    if verify_manifest(BATCH047_DIR).get("status") != "PASS":
        errors.append("Batch047 manifest mismatch")

    state = read_json(BATCH047_DIR / "consolidated_state_clean_replication_batch_047.json")
    ingest = read_json(BATCH047_DIR / "batch046_artifact_ingest_summary.json")
    verification = read_json(BATCH047_DIR / "batch046_artifact_verification.json")
    locator_preservation = read_json(BATCH047_DIR / "batch046_brot_bulb_locator_preservation.json")
    claim_preservation = read_json(BATCH047_DIR / "batch046_claim_boundary_preservation.json")
    registry = read_json(BATCH047_DIR / "batch047_source_registry_for_bounded_probe_execution.json")
    policy = read_json(BATCH047_DIR / "batch047_tot_bulb_probe_execution_policy.json")
    results = read_json(BATCH047_DIR / "batch047_tot_bulb_probe_execution_results.json")
    torus_interpretation = read_json(BATCH047_DIR / "batch047_torus_brot_probe_interpretation.json")
    coupled_interpretation = read_json(BATCH047_DIR / "batch047_tot_brot_coupled_probe_interpretation.json")
    inventory = read_json(BATCH047_DIR / "batch047_issue_seed_candidate_inventory.json")
    protocol = read_json(BATCH047_DIR / "batch047_protocol_v2_14_boundary_preservation.json")
    feasibility = read_json(BATCH047_DIR / "issue_derived_repair_feasibility_batch047.json")
    claim = read_json(BATCH047_DIR / "claim_boundary_batch047.json")
    ledger = read_json(BATCH047_DIR / "proof_obligations_ledger_batch047.json")
    minimality = read_json(BATCH047_DIR / "artifact_minimality_audit.json")
    budget = read_json(BATCH047_DIR / "artifact_payload_budget.json")
    language = read_json(BATCH047_DIR / "public_language_audit_batch047.json")

    if state.get("status") != "PASS_WITH_BATCH047_TOT_BULB_PROBE_EXECUTION_RECORDED":
        errors.append("Batch047 status mismatch")
    if state.get("exact_blocker") is not None:
        errors.append("Batch047 blocker should be None")
    if ingest.get("status") != "PASS" or verification.get("status") != "PASS":
        errors.append("Batch047 Batch046 artifact ingest/verification failed")
    if verification.get("artifact_name") != "post_v2_37_hardening_batch046_brot_bulb_environment_locator_artifacts":
        errors.append("Batch047 Batch046 artifact name mismatch")
    if verification.get("artifact_id") != 8126394588 or verification.get("workflow_run_id") != 28836675599:
        errors.append("Batch047 Batch046 artifact identity mismatch")
    if verification.get("workflow_head_sha") != "381e4b34b16fdf2261347fd5c64a506b05d31d8a":
        errors.append("Batch047 Batch046 workflow head mismatch")
    if verification.get("artifact_sha256") != "a5358881998a225eb0575d2a14fa3a35bd8f464c11f3dea75b2d39263d8568a0":
        errors.append("Batch047 Batch046 artifact SHA mismatch")
    if verification.get("artifact_size_bytes") != 166521 or verification.get("zip_entry_count") != 166:
        errors.append("Batch047 Batch046 artifact size/entry mismatch")
    if verification.get("artifact_manifest_checked") != 165 or verification.get("batch046_manifest_checked") != 21 or verification.get("post_manifest_checked") != 142:
        errors.append("Batch047 Batch046 manifest counts mismatch")
    for field in ["unsafe_path_count", "duplicate_path_count", "pycache_pyc_payload_count", "manifest_failure_count"]:
        if verification.get(field) != 0:
            errors.append(f"Batch047 Batch046 artifact {field} not zero")
    if verification.get("raw_zip_bytes_ingested") is not False:
        errors.append("Batch047 raw ZIP bytes ingested")

    if locator_preservation.get("status") != "PASS":
        errors.append("Batch047 locator preservation failed")
    if locator_preservation.get("batch046_status_preserved") != "PASS_WITH_BATCH046_BROT_BULB_ENVIRONMENT_LOCATOR_AUTHORIZED":
        errors.append("Batch047 Batch046 status not preserved")
    if locator_preservation.get("environment_bug_locator_probe_authorized") is not True:
        errors.append("Batch047 lost Batch046 probe authorization")
    if locator_preservation.get("bounded_probe_inventory_count") != 14:
        errors.append("Batch047 lost Batch046 probe inventory count")
    if locator_preservation.get("probe_execution_occurred_in_batch046") is not False or locator_preservation.get("repair_generation_occurred_in_batch046") is not False:
        errors.append("Batch047 Batch046 execution boundary changed")
    if claim_preservation.get("status") != "PASS":
        errors.append("Batch047 claim preservation failed")

    if registry.get("status") != "PASS":
        errors.append("Batch047 source registry not PASS")
    entries = registry.get("entries", [])
    if not isinstance(entries, list) or not entries:
        errors.append("Batch047 source registry missing entries before probes")
        entries = []
    if registry.get("registry_created_before_probe_execution") is not True:
        errors.append("Batch047 registry not created before probes")
    registry_ids = {entry.get("source_registry_id") for entry in entries if isinstance(entry, dict)}
    for entry in entries:
        if entry.get("decision_time_safe") is not True:
            errors.append(f"Batch047 registry entry not decision-time safe: {entry.get('source_registry_id')}")
        if entry.get("evidence_firewall_status") != "PASS":
            errors.append(f"Batch047 registry entry firewall not PASS: {entry.get('source_registry_id')}")
        if not isinstance(entry.get("allowed_probe_classes"), list):
            errors.append(f"Batch047 registry entry lacks allowed probes: {entry.get('source_registry_id')}")
    forbidden_registry = json.dumps(registry.get("forbidden_source_classes", []), sort_keys=True)
    for required in ["fixed/gold/future/later evidence", "known patches", "hidden labels", "ToT-BROT transfer as proof", "ToT-BULB probe result as proof"]:
        if required not in forbidden_registry:
            errors.append(f"Batch047 source registry missing forbidden class {required}")

    if policy.get("status") != "PASS":
        errors.append("Batch047 probe policy not PASS")
    for field in [
        "non_mutating_required",
        "sanitized_telemetry_and_hashes_required",
        "not_run_reason_required_for_skipped_probe",
    ]:
        if policy.get(field) is not True:
            errors.append(f"Batch047 probe policy missing {field}")
    for field in [
        "source_mutation_allowed",
        "test_mutation_allowed",
        "fixture_mutation_allowed",
        "harness_mutation_allowed",
        "dependency_mutation_allowed",
        "cache_mutation_allowed",
        "workspace_mutation_allowed",
        "fixed_gold_future_later_access_allowed",
        "dependency_install_allowed",
        "patch_generation_allowed",
        "repair_execution_allowed",
        "validation_claim_allowed",
        "probe_results_are_repair_proof",
    ]:
        if policy.get(field) is not False:
            errors.append(f"Batch047 probe policy over-allowed {field}")
    if policy.get("probe_glare_blocker") != "tot_bulb_probe_glare_blocked":
        errors.append("Batch047 probe glare blocker mismatch")
    if set(policy.get("probe_classes_authorized", [])) != {
        "source_presence_probe",
        "source_head_probe",
        "command_manifest_probe",
        "target_test_presence_probe",
        "harness_origin_probe",
        "cofactor_declaration_probe",
        "cofactor_lock_probe",
        "workspace_purity_probe",
        "workspace_equivalence_probe",
        "dependency_drift_probe",
        "transport_equivalence_probe",
        "stale_cache_probe",
        "proof_ledger_referrer_probe",
        "evidence_origin_probe",
    }:
        errors.append("Batch047 authorized probe classes mismatch")

    if results.get("status") != "PASS":
        errors.append("Batch047 probe results not PASS")
    result_items = results.get("results", [])
    if not isinstance(result_items, list) or not result_items:
        errors.append("Batch047 probe results missing")
        result_items = []
    if any(item.get("source_registry_id") not in registry_ids for item in result_items):
        errors.append("Batch047 probe result emitted without registry entry")
    for item in result_items:
        if item.get("mutation_detected") is not False:
            errors.append("Batch047 probe mutation violation")
        if item.get("status") == "NOT_RUN" and not item.get("not_run_reason"):
            errors.append("Batch047 skipped probe missing NOT_RUN reason")
        if item.get("status") in {"PASS", "BLOCK"} and item.get("executed") is not True:
            errors.append("Batch047 executed status mismatch")
        if item.get("glare_blocked") is True and item.get("status") != "BLOCK":
            errors.append("Batch047 glare block status mismatch")
    if results.get("mutation_violation") is not False:
        errors.append("Batch047 mutation violation flag set")
    for field in ["fixed_gold_future_later_accessed", "dependency_install_attempted", "patch_generation_attempted", "repair_execution_attempted", "probe_results_treated_as_repair_proof"]:
        if results.get(field) is not False:
            errors.append(f"Batch047 probe result overclaim/forbidden action: {field}")
    if state.get("executed_probe_count") != results.get("executed_probe_count"):
        errors.append("Batch047 executed probe count mismatch")
    if state.get("blocked_probe_count") != results.get("blocked_probe_count"):
        errors.append("Batch047 blocked probe count mismatch")
    if state.get("not_run_probe_count") != results.get("not_run_probe_count"):
        errors.append("Batch047 NOT_RUN probe count mismatch")

    if torus_interpretation.get("status") != "PASS" or torus_interpretation.get("diagnostic_only") is not True:
        errors.append("Batch047 single-system interpretation invalid")
    for item in torus_interpretation.get("interpretations", []):
        if item.get("target_failure_reproducibility_status") != "NOT_RUN":
            errors.append("Batch047 interpretation implied target replay")
        if item.get("seed_repair_eligibility_status") != "NOT_AUTHORIZED_IN_BATCH047":
            errors.append("Batch047 interpretation authorized repair eligibility")
    if coupled_interpretation.get("status") != "PASS":
        errors.append("Batch047 coupled interpretation invalid")
    if coupled_interpretation.get("memory_lift_inferred") is not False or coupled_interpretation.get("repair_generalization_inferred") is not False:
        errors.append("Batch047 coupled interpretation overclaim")
    if coupled_interpretation.get("coupled_pattern_treated_as_proof") is not False:
        errors.append("Batch047 coupled pattern treated as proof")
    for item in coupled_interpretation.get("patterns", []):
        if item.get("transfer_allowed_for_repair") is not False:
            errors.append("Batch047 coupled transfer allowed for repair")

    if inventory.get("status") != "PASS" or inventory.get("candidate_inventory_count") != 0:
        errors.append("Batch047 candidate inventory count/status mismatch")
    if inventory.get("repair_generation_authorized") is not False:
        errors.append("Batch047 candidate inventory authorized repair generation")
    if inventory.get("probe_results_are_discovery_evidence_only") is not True:
        errors.append("Batch047 inventory treated probes as validation evidence")
    if not inventory.get("empty_inventory_reason"):
        errors.append("Batch047 empty inventory reason missing")
    if protocol.get("status") != "PASS":
        errors.append("Batch047 protocol boundary not PASS")
    if protocol.get("current_protocol_before_batch047") != "v2.13" or protocol.get("current_protocol_after_batch047") != "v2.13":
        errors.append("Batch047 current protocol changed")
    if protocol.get("protocol_promotion_performed") is not False or protocol.get("silent_promotion_blocked") is not True:
        errors.append("Batch047 protocol promotion boundary failed")
    if protocol.get("recommended_future_batch") != "Batch048 protocol v2.14 promotion review":
        errors.append("Batch047 future promotion recommendation mismatch")

    if feasibility.get("status") != "PASS" or feasibility.get("repair_generation_authorized") is not False:
        errors.append("Batch047 feasibility boundary invalid")
    if feasibility.get("issue_derived_repair_episode_count") != 1 or feasibility.get("native_external_repair_episode_count") != 4:
        errors.append("Batch047 feasibility counts changed")
    if claim.get("status") != "PASS":
        errors.append("Batch047 claim boundary failed")
    if claim.get("native_external_repair_episodes") != 4 or claim.get("issue_derived_repair_episodes") != 1:
        errors.append("Batch047 claim counts changed")
    if claim.get("full_scoring") != "NOT_RUN/disallowed" or claim.get("memory_lift") != "not_demonstrated":
        errors.append("Batch047 full scoring or memory claim changed")
    if claim.get("self_maintaining_software") != "false/not_demonstrated" or claim.get("production_readiness") != "false/not_demonstrated":
        errors.append("Batch047 self-maintaining or production claim changed")
    for key in ["hallucination_elimination", "absolute_uncrashability", "generalized_autonomous_repair_success", "TO" + "RUS_physics_validation", "PSA82_validation"]:
        if claim.get(key) != "not_claimed":
            errors.append(f"Batch047 overclaimed {key}")
    if claim.get("TO" + "RUS_BROT_proof_claim") is not False or claim.get("ToT_BROT_proof_claim") is not False or claim.get("ToT_BULB_proof_claim") is not False:
        errors.append("Batch047 proof term overclaim")
    if claim.get("current_protocol") != "v2.13" or state.get("current_protocol") != "v2.13":
        errors.append("Batch047 current protocol mismatch")
    if ledger.get("status") != "PASS" or ledger.get("hash_chain_valid") is not True:
        errors.append("Batch047 proof ledger invalid")
    if ledger.get("repair_generation_occurred") is not False or ledger.get("patch_generation_occurred") is not False:
        errors.append("Batch047 proof ledger recorded repair/patch generation")
    if ledger.get("target_replay_occurred") is not False or ledger.get("duplicate_replay_occurred") is not False:
        errors.append("Batch047 proof ledger recorded replay")
    if minimality.get("status") != "PASS" or minimality.get("recursive_prior_batch_packaging_detected") is not False:
        errors.append("Batch047 artifact minimality failed")
    if budget.get("status") != "PASS" or int(budget.get("hard_primary_artifact_bytes", 0)) != 750000:
        errors.append("Batch047 artifact budget failed")
    if language.get("status") != "PASS":
        errors.append("Batch047 public language audit failed")

    forbidden_markers = ["1.45", "25.7", "wiggle_room", "closure_tolerance", "residual_tolerance"]
    for path in list(BATCH047_DIR.glob("*.json")) + list(BATCH047_DIR.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        if any(marker in text for marker in forbidden_markers):
            errors.append(f"Batch047 introduced forbidden tolerance marker in {path.name}")
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
        Path("docs/provider_workspace_bridge.md"),
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
        Path("configs/clean_replication_batch_041.json"),
        Path("configs/clean_replication_batch_042.json"),
        Path("configs/clean_replication_batch_043.json"),
        Path("configs/clean_replication_batch_044.json"),
        Path("configs/clean_replication_batch_045.json"),
        Path("configs/clean_replication_batch_046.json"),
        Path("configs/clean_replication_batch_047.json"),
        Path("configs/clean_replication_batch_014.json"),
        Path("configs/clean_replication_batch_015.json"),
        Path("configs/clean_replication_batch_016.json"),
        Path("configs/clean_replication_batch_017.json"),
        Path("configs/clean_replication_batch_018.json"),
        Path("configs/clean_replication_batch_019.json"),
        Path("configs/clean_replication_batch_020.json"),
        Path("configs/clean_replication_batch_021.json"),
        Path("configs/clean_replication_batch_022.json"),
        Path("configs/clean_replication_batch_023.json"),
        Path("configs/clean_replication_batch_024.json"),
        Path("configs/clean_replication_batch_025.json"),
        Path("configs/clean_replication_batch_026.json"),
        Path("configs/clean_replication_batch_027.json"),
        Path("configs/clean_replication_batch_028.json"),
        Path("configs/clean_replication_batch_029.json"),
        Path("configs/clean_replication_batch_030.json"),
        Path("configs/clean_replication_batch_031.json"),
        Path("configs/clean_replication_batch_033.json"),
        Path("configs/clean_replication_batch_034.json"),
        Path("configs/clean_replication_batch_035.json"),
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
        Path("controllergate/core/batch033_issue_seed_retargeting.py"),
        Path("controllergate/core/batch034_v10_harness_execution.py"),
        Path("controllergate/core/batch035_gated_source_repair.py"),
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
        Path("controllergate/core/batch036_post_repair_failure_decomposition.py"),
        Path("configs/clean_replication_batch_036.json"),
        Path("controllergate/core/batch037_provider_execution_substage_recovery.py"),
        Path("controllergate/core/batch046_brot_bulb_environment_locator.py"),
        Path("controllergate/core/batch047_tot_bulb_probe_execution.py"),
        Path("configs/clean_replication_batch_037.json"),
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
    paths.extend(sorted(BATCH018_DIR.glob("*.json")))
    paths.extend(sorted(BATCH018_DIR.glob("*.md")))
    paths.extend(sorted(BATCH019_DIR.glob("*.json")))
    paths.extend(sorted(BATCH019_DIR.glob("*.md")))
    paths.extend(sorted(BATCH020_DIR.glob("*.json")))
    paths.extend(sorted(BATCH020_DIR.glob("*.md")))
    paths.extend(sorted(BATCH021_DIR.glob("*.json")))
    paths.extend(sorted(BATCH021_DIR.glob("*.md")))
    paths.extend(sorted(BATCH022_DIR.glob("*.json")))
    paths.extend(sorted(BATCH022_DIR.glob("*.md")))
    paths.extend(sorted(BATCH023_DIR.glob("*.json")))
    paths.extend(sorted(BATCH023_DIR.glob("*.md")))
    paths.extend(sorted(BATCH024_DIR.glob("*.json")))
    paths.extend(sorted(BATCH024_DIR.glob("*.md")))
    paths.extend(sorted(BATCH025_DIR.glob("*.json")))
    paths.extend(sorted(BATCH025_DIR.glob("*.md")))
    paths.extend(sorted(BATCH026_DIR.glob("*.json")))
    paths.extend(sorted(BATCH026_DIR.glob("*.md")))
    paths.extend(sorted(BATCH027_DIR.glob("*.json")))
    paths.extend(sorted(BATCH027_DIR.glob("*.md")))
    paths.extend(sorted(BATCH028_DIR.glob("*.json")))
    paths.extend(sorted(BATCH028_DIR.glob("*.md")))
    paths.extend(sorted(BATCH029_DIR.glob("*.json")))
    paths.extend(sorted(BATCH029_DIR.glob("*.md")))
    paths.extend(sorted(BATCH030_DIR.glob("*.json")))
    paths.extend(sorted(BATCH030_DIR.glob("*.md")))
    paths.extend(sorted(BATCH031_DIR.glob("*.json")))
    paths.extend(sorted(BATCH031_DIR.glob("*.md")))
    paths.extend(sorted(BATCH032_DIR.glob("*.json")))
    paths.extend(sorted(BATCH032_DIR.glob("*.md")))
    paths.extend(sorted(BATCH033_DIR.glob("*.json")))
    paths.extend(sorted(BATCH033_DIR.glob("*.md")))
    paths.extend(sorted(BATCH034_DIR.glob("*.json")))
    paths.extend(sorted(BATCH034_DIR.glob("*.md")))
    paths.extend(sorted(BATCH034_DIR.glob("*.py")))
    paths.extend(sorted(BATCH035_DIR.glob("*.json")))
    paths.extend(sorted(BATCH035_DIR.glob("*.md")))
    paths.extend(sorted(BATCH035_DIR.glob("*.py")))
    paths.extend(sorted(BATCH036_DIR.glob("*.json")))
    paths.extend(sorted(BATCH036_DIR.glob("*.md")))
    paths.extend(sorted(BATCH036_DIR.glob("*.py")))
    paths.extend(sorted(BATCH036_DIR.glob("*.diff")))
    paths.extend(sorted(BATCH037_DIR.glob("*.json")))
    paths.extend(sorted(BATCH037_DIR.glob("*.md")))
    paths.extend(sorted(BATCH037_DIR.glob("*.py")))
    paths.extend(sorted(BATCH037_DIR.glob("*.diff")))
    paths.extend(sorted(BATCH041_DIR.glob("*.json")))
    paths.extend(sorted(BATCH041_DIR.glob("*.md")))
    paths.extend(sorted(BATCH042_DIR.glob("*.json")))
    paths.extend(sorted(BATCH042_DIR.glob("*.md")))
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
        + require_files(BATCH024_DIR, BATCH024_REQUIRED)
        + require_files(BATCH028_DIR, BATCH028_REQUIRED)
        + require_files(BATCH029_DIR, BATCH029_REQUIRED)
        + require_files(BATCH030_DIR, BATCH030_REQUIRED)
        + require_files(BATCH031_DIR, BATCH031_REQUIRED)
        + require_files(BATCH032_DIR, BATCH032_REQUIRED)
        + require_files(BATCH033_DIR, BATCH033_REQUIRED)
        + require_files(BATCH034_DIR, BATCH034_REQUIRED)
        + require_files(BATCH035_DIR, BATCH035_REQUIRED)
        + require_files(BATCH036_DIR, BATCH036_REQUIRED)
        + require_files(BATCH037_DIR, BATCH037_REQUIRED)
        + require_files(BATCH041_DIR, BATCH041_REQUIRED)
        + require_files(BATCH042_DIR, BATCH042_REQUIRED)
        + require_files(BATCH043_DIR, BATCH043_REQUIRED)
        + require_files(BATCH044_DIR, BATCH044_REQUIRED)
        + require_files(BATCH045_DIR, BATCH045_REQUIRED)
        + require_files(BATCH046_DIR, BATCH046_REQUIRED)
        + require_files(BATCH047_DIR, BATCH047_REQUIRED)
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
    if verify_manifest(BATCH024_DIR)["status"] != "PASS":
        return fail("batch024 manifest mismatch")
    if verify_manifest(BATCH028_DIR)["status"] != "PASS":
        return fail("batch028 manifest mismatch")
    if verify_manifest(BATCH029_DIR)["status"] != "PASS":
        return fail("batch029 manifest mismatch")
    if verify_manifest(BATCH030_DIR)["status"] != "PASS":
        return fail("batch030 manifest mismatch")
    if verify_manifest(BATCH031_DIR)["status"] != "PASS":
        return fail("batch031 manifest mismatch")
    if verify_manifest(BATCH032_DIR)["status"] != "PASS":
        return fail("batch032 manifest mismatch")
    if verify_manifest(BATCH033_DIR)["status"] != "PASS":
        return fail("batch033 manifest mismatch")
    if verify_manifest(BATCH034_DIR)["status"] != "PASS":
        return fail("batch034 manifest mismatch")
    if verify_manifest(BATCH035_DIR)["status"] != "PASS":
        return fail("batch035 manifest mismatch")
    if verify_manifest(BATCH036_DIR)["status"] != "PASS":
        return fail("batch036 manifest mismatch")
    if verify_manifest(BATCH037_DIR)["status"] != "PASS":
        return fail("batch037 manifest mismatch")
    if verify_manifest(BATCH038_DIR)["status"] != "PASS":
        return fail("batch038 manifest mismatch")
    if verify_manifest(BATCH039_DIR)["status"] != "PASS":
        return fail("batch039 manifest mismatch")
    if verify_manifest(BATCH040_DIR)["status"] != "PASS":
        return fail("batch040 manifest mismatch")
    if verify_manifest(BATCH041_DIR)["status"] != "PASS":
        return fail("batch041 manifest mismatch")
    if verify_manifest(BATCH042_DIR)["status"] != "PASS":
        return fail("batch042 manifest mismatch")
    if verify_manifest(BATCH043_DIR)["status"] != "PASS":
        return fail("batch043 manifest mismatch")
    if verify_manifest(BATCH044_DIR)["status"] != "PASS":
        return fail("batch044 manifest mismatch")
    if verify_manifest(BATCH045_DIR)["status"] != "PASS":
        return fail("batch045 manifest mismatch")
    if verify_manifest(BATCH046_DIR)["status"] != "PASS":
        return fail("batch046 manifest mismatch")
    if verify_manifest(BATCH047_DIR)["status"] != "PASS":
        return fail("batch047 manifest mismatch")
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
    batch024_errors = audit_batch024_records()
    if batch024_errors:
        return fail(f"batch024 audit failed: {batch024_errors}")
    batch025_errors = audit_batch025_records()
    if batch025_errors:
        return fail(f"batch025 audit failed: {batch025_errors}")
    batch026_errors = audit_batch026_records()
    if batch026_errors:
        return fail(f"batch026 audit failed: {batch026_errors}")
    batch027_errors = audit_batch027_records()
    if batch027_errors:
        return fail(f"batch027 audit failed: {batch027_errors}")
    batch028_errors = audit_batch028_records()
    if batch028_errors:
        return fail(f"batch028 audit failed: {batch028_errors}")
    batch029_errors = audit_batch029_records()
    if batch029_errors:
        return fail(f"batch029 audit failed: {batch029_errors}")
    batch030_errors = audit_batch030_records()
    if batch030_errors:
        return fail(f"batch030 audit failed: {batch030_errors}")
    batch031_errors = audit_batch031_records()
    if batch031_errors:
        return fail(f"batch031 audit failed: {batch031_errors}")
    batch032_errors = audit_batch032_records()
    if batch032_errors:
        return fail(f"batch032 audit failed: {batch032_errors}")
    batch033_errors = audit_batch033_records()
    if batch033_errors:
        return fail(f"batch033 audit failed: {batch033_errors}")
    batch034_errors = audit_batch034_records()
    if batch034_errors:
        return fail(f"batch034 audit failed: {batch034_errors}")
    batch035_errors = audit_batch035_records()
    if batch035_errors:
        return fail(f"batch035 audit failed: {batch035_errors}")
    batch036_errors = audit_batch036_records()
    if batch036_errors:
        return fail(f"batch036 audit failed: {batch036_errors}")
    batch037_errors = audit_batch037_records()
    if batch037_errors:
        return fail(f"batch037 audit failed: {batch037_errors}")
    batch038_errors = audit_batch038_records()
    if batch038_errors:
        return fail(f"batch038 audit failed: {batch038_errors}")
    batch039_errors = audit_batch039_records()
    if batch039_errors:
        return fail(f"batch039 audit failed: {batch039_errors}")
    batch040_errors = audit_batch040_records()
    if batch040_errors:
        return fail(f"batch040 audit failed: {batch040_errors}")
    batch041_errors = audit_batch041_records()
    if batch041_errors:
        return fail(f"batch041 audit failed: {batch041_errors}")
    batch042_errors = audit_batch042_records()
    if batch042_errors:
        return fail(f"batch042 audit failed: {batch042_errors}")
    batch043_errors = audit_batch043_records()
    if batch043_errors:
        return fail(f"batch043 audit failed: {batch043_errors}")
    batch044_errors = audit_batch044_records()
    if batch044_errors:
        return fail(f"batch044 audit failed: {batch044_errors}")
    batch045_errors = audit_batch045_records()
    if batch045_errors:
        return fail(f"batch045 audit failed: {batch045_errors}")
    batch046_errors = audit_batch046_records()
    if batch046_errors:
        return fail(f"batch046 audit failed: {batch046_errors}")
    batch047_errors = audit_batch047_records()
    if batch047_errors:
        return fail(f"batch047 audit failed: {batch047_errors}")
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
    if not str(final_report.get("status", "")).startswith("PASS_WITH_BATCH047_"):
        return fail("final report did not advance to Batch047 bounded probe execution boundary")
    allowed_latest_blockers = {
        "docker_runtime_provider_unavailable",
        "python37_docker_provider_unavailable",
        "runtime_provider_python_version_mismatch",
        "manual_lock_environment_materialization_failed",
        "provider_harness_v9_execution_failed",
        "provider_harness_v10_execution_failed",
        "provider_batch035_execution_failed",
        "provider_batch036_execution_failed",
        "provider_batch037_execution_failed",
        "provider_batch038_execution_failed",
        "provider_source_checkout_failed",
        "provider_source_commit_mismatch",
        "provider_workspace_materialization_failed",
        "candidate_v2_patch_unavailable",
        "candidate_v2_patch_hash_mismatch",
        "patch_v2_apply_check_failed",
        "patch_serialization_unrecoverable",
        "corrected_patch_unavailable",
        "corrected_patch_integrity_failed",
        "corrected_patch_apply_check_failed",
        "corrected_patch_application_failed",
        "corrected_patch_scope_invalid",
        "harness_v9_file_missing",
        "harness_v10_file_missing",
        "harness_v9_payload_integrity_failed",
        "batch028_artifact_custody_or_harness_integrity_missing",
        "issue_derived_harness_v9_target_aligned_failure_not_reproduced_under_approved_context",
        "issue_seed_not_reproduced_by_current_harness",
        "issue_seed_not_reproduced_by_v10_harness",
        "safe_directory_normalization_failed",
        "issue_seed_retargeting_requires_separate_gated_v10_execution",
        "issue_derived_seed_retired_no_repair_feasibility",
        "harness_v10_execution_not_run",
        "harness_v10_execution_blocked",
        "pre_patch_target_failure_not_reproduced",
        "patch_application_failed",
        "patch_scope_invalid",
        "patch_v2_application_failed",
        "post_repair_target_not_resolved",
        "repair_v2_target_not_resolved",
        "repair_v2_serialization_corrected_but_target_not_resolved",
        "target_failure_still_present_with_secondary_linter_precondition",
        "target_resolution_blocked_by_secondary_linter_precondition",
        "declared_secondary_cofactor_unpinned_lock_required",
        "pinned_cofactor_lock_unavailable",
        "provider_batch040_execution_failed",
        "provider_batch040_execution_not_run",
        "provider_batch041_execution_failed",
        "provider_batch041_execution_not_run",
        "lock_v2_materialization_not_passed",
        "lock_unavailable_no_replay",
        "dependency_drift_blocks_replay",
        "transport_equivalence_failed",
        "target_defect_regressed",
        "target_defect_resolved_but_secondary_cofactor_missing",
        "target_defect_resolved_but_linter_reports_findings",
        "target_defect_resolved_full_command_failed_other_secondary",
        "duplicate_replay_failed",
        "cofactor_chain_exhausted",
        "batch042_count_gate_failed",
        "batch042_count_lock_preservation_failed",
        "reviewed_cofactor_lock_materialization_failed",
        "pylint_executable_verification_failed",
        "provider_only_materialization_not_passed",
        "post_repair_target_replay_not_fully_passed",
        "target_regressed_after_cofactor_materialization",
        "reviewed_cofactor_materialized_but_secondary_failure_remains",
        "new_secondary_cofactor_observed",
        "target_failure_still_present",
        "target_resolution_status_ambiguous",
        "duplicate_clean_replay_failed",
        "duplicate_patch_application_failed",
        "issue_derived_repair_not_validated",
        "batch034_v10_verification_not_preserved",
        "no_safe_source_only_patch_candidate",
        "no_safe_source_only_refinement_candidate",
        "provider_batch035_execution_not_run",
        "provider_batch036_execution_not_run",
        "provider_batch037_execution_not_run",
        "provider_batch038_execution_not_run",
    }
    if final_report.get("exact_blocker") is not None and final_report.get("exact_blocker") not in allowed_latest_blockers:
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
    if final_report.get("batch024_provider_workspace_bridge_status") not in {"PASS", "BLOCK"}:
        return fail("final report Batch024 provider workspace bridge status missing")
    if final_report.get("batch024_provider_input_bundle_status") != "PASS":
        return fail("final report Batch024 provider input bundle status mismatch")
    if final_report.get("batch024_provider_output_bundle_status") != "PASS":
        return fail("final report Batch024 provider output bundle status mismatch")
    if final_report.get("batch024_provider_workspace_cleanup_status") != "PASS":
        return fail("final report Batch024 provider workspace cleanup status mismatch")
    if final_report.get("batch024_selected_source_commit") != "a2d13656adfaa010fb6c7339087f3347ad2b815a":
        return fail("final report Batch024 selected source commit mismatch")
    if final_report.get("batch024_source_materialization_status") == "PASS" and final_report.get("batch024_provider_source_checkout_status") != "PASS":
        return fail("final report Batch024 materialization before source checkout")
    if final_report.get("batch024_target_intent_alignment_status") == "PASS" and final_report.get("batch024_source_materialization_status") != "PASS":
        return fail("final report Batch024 target-intent before materialization")
    if final_report.get("batch024_harness_v9_generated") is not False:
        return fail("final report Batch024 harness boundary mismatch")
    if final_report.get("batch024_issue_derived_repair_feasibility") is not False:
        return fail("final report Batch024 issue-derived feasibility overclaim")
    if final_report.get("batch024_structured_fragility_diagnostic_status") != "NOT_RUN_NO_PATCH_CANDIDATE":
        return fail("final report Batch024 structured diagnostic status mismatch")
    if final_report.get("batch024_native_repair_episode_count") != 4 or final_report.get("batch024_issue_derived_repair_episode_count") != 0:
        return fail("final report Batch024 repair counts changed")
    if not str(final_report.get("clean_replication_batch_025_status", "")).startswith("PASS_WITH_BATCH025_"):
        return fail("final report Batch025 status missing")
    if final_report.get("clean_replication_batch_025_status") != "PASS_WITH_BATCH025_TARGET_INTENT_ALIGNED":
        return fail("final report Batch025 official aligned status missing")
    if final_report.get("clean_replication_batch_025_exact_blocker") != "issue_derived_harness_v9_generation_pending_after_target_intent_alignment":
        return fail("final report Batch025 official blocker missing")
    if final_report.get("batch025_provider_command_context_status") != "PASS":
        return fail("final report Batch025 provider command context not PASS")
    if final_report.get("batch025_source_materialization_status") != "PASS":
        return fail("final report Batch025 source materialization not PASS")
    if final_report.get("batch025_target_intent_alignment_status") != "PASS":
        return fail("final report Batch025 Target-Intent Alignment not PASS")
    if final_report.get("batch025_target_intent_alignment_status") == "PASS" and final_report.get("batch025_provider_git_context_status") != "PASS":
        return fail("final report Batch025 target-intent lacks Git context")
    if final_report.get("batch025_issue_derived_harness_v9_generated") is not False:
        return fail("final report Batch025 harness generated unexpectedly")
    if final_report.get("batch025_issue_derived_repair_feasibility") is not False:
        return fail("final report Batch025 issue-derived feasibility overclaim")
    if final_report.get("batch025_repair_only_fallback_attempted") is not False:
        return fail("final report Batch025 repair fallback ran unexpectedly")
    if final_report.get("batch025_matched_null_diagnostic_run_count") != 0:
        return fail("final report Batch025 matched-null diagnostic ran unexpectedly")
    if final_report.get("batch025_psa82_permutation_null_status") != "NOT_RUN_NO_PATCH_CANDIDATE":
        return fail("final report Batch025 PSA-82 diagnostic status mismatch")
    if final_report.get("batch025_structured_fragility_diagnostic_status") != "NOT_RUN_NO_PATCH_CANDIDATE":
        return fail("final report Batch025 structured diagnostic status mismatch")
    if final_report.get("batch025_native_repair_episode_count") != 4 or final_report.get("batch025_issue_derived_repair_episode_count") != 0:
        return fail("final report Batch025 repair counts changed")
    if not str(final_report.get("clean_replication_batch_026_status", "")).startswith("PASS_WITH_BATCH026_"):
        return fail("final report Batch026 status missing")
    if final_report.get("batch026_batch025_target_intent_alignment_status") != "PASS":
        return fail("final report Batch026 missing Batch025 target-intent prerequisite")
    if final_report.get("batch026_relative_git_dir_active_command_context_used") is not False:
        return fail("final report Batch026 used relative Git directory active command context")
    if final_report.get("batch026_issue_derived_repair_feasibility") is True and final_report.get("batch026_issue_derived_harness_v9_target_aligned_failure_reproduced") is not True:
        return fail("final report Batch026 feasibility without harness verification")
    if final_report.get("batch026_patch_generated") is not False or final_report.get("batch026_patch_authorized") is not False or final_report.get("batch026_patch_attempted") is not False:
        return fail("final report Batch026 patch boundary changed")
    if final_report.get("batch026_repair_only_fallback_attempted") is not False:
        return fail("final report Batch026 repair fallback ran unexpectedly")
    if final_report.get("batch026_matched_null_diagnostic_run_count") != 0:
        return fail("final report Batch026 matched-null diagnostic ran unexpectedly")
    if final_report.get("batch026_psa82_permutation_null_status") != "NOT_RUN_NO_PATCH_CANDIDATE":
        return fail("final report Batch026 PSA-82 diagnostic status mismatch")
    if final_report.get("batch026_structured_fragility_diagnostic_status") != "NOT_RUN_NO_PATCH_CANDIDATE":
        return fail("final report Batch026 structured diagnostic status mismatch")
    if final_report.get("batch026_native_repair_episode_count") != 4 or final_report.get("batch026_issue_derived_repair_episode_count") != 0:
        return fail("final report Batch026 repair counts changed")
    if not str(final_report.get("clean_replication_batch_027_status", "")).startswith("PASS_WITH_BATCH027_"):
        return fail("final report Batch027 status missing")
    if final_report.get("batch027_batch026_harness_state_reconciliation_status") != "PASS":
        return fail("final report Batch027 harness-state reconciliation not PASS")
    if final_report.get("batch027_batch026_harness_state_classification") not in {"generated_but_unexecuted_harness", "executed_harness_result_recorded"}:
        return fail("final report Batch027 harness-state classification invalid")
    if final_report.get("batch027_relative_git_dir_active_command_context_used") is not False:
        return fail("final report Batch027 used relative Git directory active command context")
    if final_report.get("batch027_issue_derived_repair_feasibility") is True and final_report.get("batch027_harness_v9_verified") is not True:
        return fail("final report Batch027 feasibility without harness verification")
    if final_report.get("batch027_patch_generated") is not False or final_report.get("batch027_patch_authorized") is not False or final_report.get("batch027_patch_attempted") is not False:
        return fail("final report Batch027 patch boundary changed")
    if final_report.get("batch027_repair_only_fallback_attempted") is not False:
        return fail("final report Batch027 repair fallback ran unexpectedly")
    if final_report.get("batch027_matched_null_diagnostic_run_count") != 0:
        return fail("final report Batch027 matched-null diagnostic ran unexpectedly")
    if final_report.get("batch027_psa82_permutation_null_status") != "NOT_RUN_NO_PATCH_CANDIDATE":
        return fail("final report Batch027 PSA-82 diagnostic status mismatch")
    if final_report.get("batch027_structured_fragility_diagnostic_status") != "NOT_RUN_NO_PATCH_CANDIDATE":
        return fail("final report Batch027 structured diagnostic status mismatch")
    if final_report.get("batch027_native_repair_episode_count") != 4 or final_report.get("batch027_issue_derived_repair_episode_count") != 0:
        return fail("final report Batch027 repair counts changed")
    if not str(final_report.get("clean_replication_batch_028_status", "")).startswith("PASS_WITH_BATCH028_"):
        return fail("final report Batch028 status missing")
    if final_report.get("batch028_batch027_status_preserved") != "PASS_WITH_BATCH027_HARNESS_V9_EXECUTION_BLOCKED":
        return fail("final report Batch028 did not preserve Batch027 boundary")
    if final_report.get("batch028_batch027_execution_telemetry_precision_status") != "PASS":
        return fail("final report Batch028 telemetry precision audit not PASS")
    if final_report.get("batch028_harness_payload_status") != "PASS":
        return fail("final report Batch028 harness payload status not PASS")
    if final_report.get("batch028_harness_payload_method") not in {"rehydrated", "regenerated"}:
        return fail("final report Batch028 harness payload method missing")
    if final_report.get("batch028_harness_payload_sha256") != "da098a46ef7efea42f2c9b35451b51f66038d58b6675fe386868338a3b3e0c01":
        return fail("final report Batch028 harness payload SHA mismatch")
    if final_report.get("batch028_relative_git_dir_active_command_context_used") is not False:
        return fail("final report Batch028 used relative Git directory active command context")
    if final_report.get("batch028_issue_derived_repair_feasibility") is True and final_report.get("batch028_harness_v9_verified") is not True:
        return fail("final report Batch028 feasibility without harness verification")
    if final_report.get("clean_replication_batch_028_exact_blocker") == "issue_derived_harness_v9_target_aligned_failure_not_reproduced_under_approved_context" and final_report.get("batch028_harness_v9_executed") is not True:
        return fail("final report Batch028 claimed target failure not reproduced without execution")
    if final_report.get("batch028_patch_generated") is not False or final_report.get("batch028_patch_authorized") is not False or final_report.get("batch028_patch_attempted") is not False:
        return fail("final report Batch028 patch boundary changed")
    if final_report.get("batch028_repair_only_fallback_attempted") is not False:
        return fail("final report Batch028 repair fallback ran unexpectedly")
    if final_report.get("batch028_matched_null_diagnostic_run_count") != 0:
        return fail("final report Batch028 matched-null diagnostic ran unexpectedly")
    if final_report.get("batch028_psa82_permutation_null_status") != "NOT_RUN_NO_PATCH_CANDIDATE":
        return fail("final report Batch028 PSA-82 diagnostic status mismatch")
    if final_report.get("batch028_structured_fragility_diagnostic_status") != "NOT_RUN_NO_PATCH_CANDIDATE":
        return fail("final report Batch028 structured diagnostic status mismatch")
    if final_report.get("batch028_native_repair_episode_count") != 4 or final_report.get("batch028_issue_derived_repair_episode_count") != 0:
        return fail("final report Batch028 repair counts changed")
    if not str(final_report.get("clean_replication_batch_029_status", "")).startswith("PASS_WITH_BATCH029_"):
        return fail("final report Batch029 status missing")
    if final_report.get("batch029_batch028_status_preserved") != "PASS_WITH_BATCH028_HARNESS_V9_EXECUTION_BLOCKED":
        return fail("final report Batch029 did not preserve Batch028 boundary")
    if final_report.get("batch029_batch028_execution_telemetry_precision_status") != "PASS":
        return fail("final report Batch029 telemetry precision audit not PASS")
    if final_report.get("batch029_harness_payload_integrity_status") != "PASS":
        return fail("final report Batch029 harness payload integrity not PASS")
    if final_report.get("batch029_harness_payload_sha256") != "da098a46ef7efea42f2c9b35451b51f66038d58b6675fe386868338a3b3e0c01":
        return fail("final report Batch029 harness payload SHA mismatch")
    if final_report.get("batch029_harness_v9_executed") is True and final_report.get("batch029_provider_source_head_verified") is not True:
        return fail("final report Batch029 executed without source HEAD verification")
    if final_report.get("batch029_relative_git_dir_active_command_context_used") is not False:
        return fail("final report Batch029 used relative Git directory active command context")
    if final_report.get("batch029_issue_derived_repair_feasibility") is True and final_report.get("batch029_harness_v9_verified") is not True:
        return fail("final report Batch029 feasibility without harness verification")
    if final_report.get("clean_replication_batch_029_exact_blocker") == "issue_derived_harness_v9_target_aligned_failure_not_reproduced_under_approved_context" and final_report.get("batch029_harness_v9_executed") is not True:
        return fail("final report Batch029 claimed target failure not reproduced without execution")
    if final_report.get("batch029_patch_generated") is not False or final_report.get("batch029_patch_authorized") is not False or final_report.get("batch029_patch_attempted") is not False:
        return fail("final report Batch029 patch boundary changed")
    if final_report.get("batch029_repair_only_fallback_attempted") is not False:
        return fail("final report Batch029 repair fallback ran unexpectedly")
    if final_report.get("batch029_matched_null_diagnostic_run_count") != 0:
        return fail("final report Batch029 matched-null diagnostic ran unexpectedly")
    if final_report.get("batch029_psa82_permutation_null_status") != "NOT_RUN_NO_PATCH_CANDIDATE":
        return fail("final report Batch029 PSA-82 diagnostic status mismatch")
    if final_report.get("batch029_structured_fragility_diagnostic_status") != "NOT_RUN_NO_PATCH_CANDIDATE":
        return fail("final report Batch029 structured diagnostic status mismatch")
    if final_report.get("batch029_native_repair_episode_count") != 4 or final_report.get("batch029_issue_derived_repair_episode_count") != 0:
        return fail("final report Batch029 repair counts changed")
    if not str(final_report.get("clean_replication_batch_030_status", "")).startswith("PASS_WITH_BATCH030_"):
        return fail("final report Batch030 status missing")
    if final_report.get("batch030_batch029_status_preserved") != "PASS_WITH_BATCH029_HARNESS_V9_EXECUTION_BLOCKED":
        return fail("final report Batch030 did not preserve Batch029 boundary")
    if final_report.get("batch030_batch029_artifact_ingest_status") != "PASS":
        return fail("final report Batch030 Batch029 artifact ingest not PASS")
    if final_report.get("batch030_batch029_blocker_precision_audit_status") != "PASS":
        return fail("final report Batch030 blocker precision audit not PASS")
    if final_report.get("batch030_gate_predicate_correction_status") != "PASS":
        return fail("final report Batch030 gate predicate correction not PASS")
    if final_report.get("clean_replication_batch_030_exact_blocker") == "batch028_artifact_custody_or_harness_integrity_missing":
        return fail("final report Batch030 carried stale custody/integrity blocker")
    if final_report.get("batch030_harness_payload_availability_status") != "PASS":
        return fail("final report Batch030 harness payload availability not PASS")
    if final_report.get("batch030_harness_payload_integrity_status") != "PASS":
        return fail("final report Batch030 harness payload integrity not PASS")
    if final_report.get("batch030_harness_payload_sha256") != "da098a46ef7efea42f2c9b35451b51f66038d58b6675fe386868338a3b3e0c01":
        return fail("final report Batch030 harness payload SHA mismatch")
    if final_report.get("batch030_harness_v9_executed") is True and final_report.get("batch030_provider_source_head_verified") is not True:
        return fail("final report Batch030 executed without source HEAD verification")
    if final_report.get("batch030_relative_git_dir_active_command_context_used") is not False:
        return fail("final report Batch030 used relative Git directory active command context")
    if final_report.get("batch030_issue_derived_repair_feasibility") is True and final_report.get("batch030_harness_v9_verified") is not True:
        return fail("final report Batch030 feasibility without harness verification")
    if final_report.get("clean_replication_batch_030_exact_blocker") == "issue_derived_harness_v9_target_aligned_failure_not_reproduced_under_approved_context" and final_report.get("batch030_harness_v9_executed") is not True:
        return fail("final report Batch030 claimed target failure not reproduced without execution")
    if final_report.get("batch030_patch_generated") is not False or final_report.get("batch030_patch_authorized") is not False or final_report.get("batch030_patch_attempted") is not False:
        return fail("final report Batch030 patch boundary changed")
    if final_report.get("batch030_repair_only_fallback_attempted") is not False:
        return fail("final report Batch030 repair fallback ran unexpectedly")
    if final_report.get("batch030_matched_null_diagnostic_run_count") != 0:
        return fail("final report Batch030 matched-null diagnostic ran unexpectedly")
    if final_report.get("batch030_psa82_permutation_null_status") != "NOT_RUN_NO_PATCH_CANDIDATE":
        return fail("final report Batch030 PSA-82 diagnostic status mismatch")
    if final_report.get("batch030_structured_fragility_diagnostic_status") != "NOT_RUN_NO_PATCH_CANDIDATE":
        return fail("final report Batch030 structured diagnostic status mismatch")
    if final_report.get("batch030_native_repair_episode_count") != 4 or final_report.get("batch030_issue_derived_repair_episode_count") != 0:
        return fail("final report Batch030 repair counts changed")
    if not str(final_report.get("clean_replication_batch_031_status", "")).startswith("PASS_WITH_BATCH031_"):
        return fail("final report Batch031 status missing")
    if final_report.get("batch031_batch030_status_preserved") != "PASS_WITH_BATCH030_HARNESS_V9_EXECUTION_BLOCKED":
        return fail("final report Batch031 did not preserve Batch030 boundary")
    if final_report.get("batch031_batch030_artifact_ingest_status") != "PASS":
        return fail("final report Batch031 Batch030 artifact ingest not PASS")
    if final_report.get("batch031_batch030_blocker_precision_audit_status") != "PASS":
        return fail("final report Batch031 blocker precision audit not PASS")
    if final_report.get("batch031_provider_source_commit_predicate_audit_status") != "PASS":
        return fail("final report Batch031 provider source commit predicate audit not PASS")
    if final_report.get("batch031_expected_source_commit_sha") != "a2d13656adfaa010fb6c7339087f3347ad2b815a":
        return fail("final report Batch031 expected source commit mismatch")
    if final_report.get("batch031_provider_source_head_match") is True and final_report.get("clean_replication_batch_031_exact_blocker") == "provider_source_commit_mismatch":
        return fail("final report Batch031 carried source commit mismatch despite matching HEAD")
    if final_report.get("batch031_harness_payload_availability_status") != "PASS":
        return fail("final report Batch031 harness payload availability not PASS")
    if final_report.get("batch031_harness_payload_integrity_status") != "PASS":
        return fail("final report Batch031 harness payload integrity not PASS")
    if final_report.get("batch031_harness_payload_sha256") != "da098a46ef7efea42f2c9b35451b51f66038d58b6675fe386868338a3b3e0c01":
        return fail("final report Batch031 harness payload SHA mismatch")
    if final_report.get("batch031_harness_v9_executed") is True and final_report.get("batch031_provider_source_head_verified") is not True:
        return fail("final report Batch031 executed without source HEAD verification")
    if final_report.get("batch031_relative_git_dir_active_command_context_used") is not False:
        return fail("final report Batch031 used relative Git directory active command context")
    if final_report.get("batch031_issue_derived_repair_feasibility") is True and final_report.get("batch031_harness_v9_verified") is not True:
        return fail("final report Batch031 feasibility without harness verification")
    if final_report.get("clean_replication_batch_031_exact_blocker") == "issue_derived_harness_v9_target_aligned_failure_not_reproduced_under_approved_context" and final_report.get("batch031_harness_v9_executed") is not True:
        return fail("final report Batch031 claimed target failure not reproduced without execution")
    if final_report.get("batch031_patch_generated") is not False or final_report.get("batch031_patch_authorized") is not False or final_report.get("batch031_patch_attempted") is not False:
        return fail("final report Batch031 patch boundary changed")
    if final_report.get("batch031_repair_only_fallback_attempted") is not False:
        return fail("final report Batch031 repair fallback ran unexpectedly")
    if final_report.get("batch031_matched_null_diagnostic_run_count") != 0:
        return fail("final report Batch031 matched-null diagnostic ran unexpectedly")
    if final_report.get("batch031_psa82_permutation_null_status") != "NOT_RUN_NO_PATCH_CANDIDATE":
        return fail("final report Batch031 PSA-82 diagnostic status mismatch")
    if final_report.get("batch031_structured_fragility_diagnostic_status") != "NOT_RUN_NO_PATCH_CANDIDATE":
        return fail("final report Batch031 structured diagnostic status mismatch")
    if final_report.get("batch031_native_repair_episode_count") != 4 or final_report.get("batch031_issue_derived_repair_episode_count") != 0:
        return fail("final report Batch031 repair counts changed")
    if not str(final_report.get("clean_replication_batch_032_status", "")).startswith("PASS_WITH_BATCH032_"):
        return fail("final report Batch032 status missing")
    if final_report.get("batch032_batch031_status_preserved") != "PASS_WITH_BATCH031_HARNESS_V9_EXECUTION_BLOCKED":
        return fail("final report Batch032 did not preserve Batch031 boundary")
    if final_report.get("batch032_batch031_artifact_ingest_status") != "PASS":
        return fail("final report Batch032 Batch031 artifact ingest not PASS")
    if final_report.get("batch032_execution_result_classification_status") != "PASS":
        return fail("final report Batch032 execution classification not PASS")
    if final_report.get("batch032_safe_directory_precondition_classification_status") != "PASS":
        return fail("final report Batch032 safe-directory classification not PASS")
    if final_report.get("batch032_provider_environment_normalization_status") not in {"PASS", "BLOCK"}:
        return fail("final report Batch032 provider normalization status missing")
    if final_report.get("batch032_safe_directory_normalization_source_mutation") is not False or final_report.get("batch032_safe_directory_normalization_test_mutation") is not False:
        return fail("final report Batch032 normalization mutated source/tests")
    if final_report.get("batch032_provider_environment_normalization_status") == "PASS" and final_report.get("batch032_source_head_unchanged") is not True:
        return fail("final report Batch032 source HEAD changed after normalization")
    if final_report.get("batch032_relative_git_dir_active_command_context_used") is not False:
        return fail("final report Batch032 used relative Git directory active command context")
    if final_report.get("batch032_issue_derived_repair_feasibility") is True and final_report.get("batch032_harness_v9_verified") is not True:
        return fail("final report Batch032 feasibility without harness verification")
    if final_report.get("batch032_patch_generated") is not False or final_report.get("batch032_patch_authorized") is not False or final_report.get("batch032_patch_attempted") is not False:
        return fail("final report Batch032 patch boundary changed")
    if final_report.get("batch032_repair_ran") is not False:
        return fail("final report Batch032 repair ran unexpectedly")
    if final_report.get("batch032_matched_null_diagnostic_run_count") != 0:
        return fail("final report Batch032 matched-null diagnostic ran unexpectedly")
    if final_report.get("batch032_native_repair_episode_count") != 4 or final_report.get("batch032_issue_derived_repair_episode_count") != 0:
        return fail("final report Batch032 repair counts changed")
    if not str(final_report.get("status", "")).startswith("PASS_WITH_BATCH047_"):
        return fail("final report top-level status is not Batch047")
    if not str(final_report.get("clean_replication_batch_033_status", "")).startswith("PASS_WITH_BATCH033_"):
        return fail("final report Batch033 status missing")
    if final_report.get("batch033_batch032_status_preserved") != "PASS_WITH_BATCH032_HARNESS_V9_TARGET_NOT_REPRODUCED":
        return fail("final report Batch033 did not preserve Batch032 boundary")
    if final_report.get("batch033_batch032_artifact_ingest_status") != "PASS":
        return fail("final report Batch033 Batch032 artifact ingest not PASS")
    if final_report.get("batch033_batch032_target_not_reproduced_summary_status") != "PASS":
        return fail("final report Batch033 target-not-reproduced summary not PASS")
    if final_report.get("batch033_issue_seed_retargeting_classification") not in {
        "issue_requires_more_specific_decision_time_fixture",
        "issue_seed_not_reproduced_by_current_harness",
        "issue_derived_seed_retired_no_repair_feasibility",
        "issue_seed_retargeting_possible_from_allowed_evidence",
    }:
        return fail("final report Batch033 retargeting classification invalid")
    if final_report.get("batch033_retargeting_possible_from_allowed_evidence") is True:
        if final_report.get("batch033_issue_seed_retargeting_classification") != "issue_seed_retargeting_possible_from_allowed_evidence":
            return fail("final report Batch033 retargeting possible/classification mismatch")
        if final_report.get("batch033_harness_v10_design_policy_status") != "PASS":
            return fail("final report Batch033 v10 design policy not PASS")
        if final_report.get("batch033_harness_v10_generation_status") != "PASS_DESIGN_ONLY":
            return fail("final report Batch033 v10 generation not design-only")
    if final_report.get("batch033_harness_v10_executable_generated") is not False or final_report.get("batch033_harness_v10_executed") is not False:
        return fail("final report Batch033 generated or executed v10 harness")
    if final_report.get("batch033_issue_derived_repair_feasibility") is not False:
        return fail("final report Batch033 issue-derived feasibility overclaim")
    if final_report.get("batch033_repair_ran") is not False:
        return fail("final report Batch033 repair ran unexpectedly")
    if final_report.get("batch033_patch_generated") is not False or final_report.get("batch033_patch_authorized") is not False or final_report.get("batch033_patch_attempted") is not False:
        return fail("final report Batch033 patch boundary changed")
    if final_report.get("batch033_matched_null_diagnostic_run_count") != 0:
        return fail("final report Batch033 matched-null diagnostic ran unexpectedly")
    if final_report.get("batch033_psa82_permutation_null_status") != "NOT_RUN_NO_PATCH_CANDIDATE":
        return fail("final report Batch033 PSA-82 diagnostic status mismatch")
    if final_report.get("batch033_structured_fragility_diagnostic_status") != "NOT_RUN_NO_PATCH_CANDIDATE":
        return fail("final report Batch033 structured diagnostic status mismatch")
    if final_report.get("batch033_native_repair_episode_count") != 4 or final_report.get("batch033_issue_derived_repair_episode_count") != 0:
        return fail("final report Batch033 repair counts changed")
    if not str(final_report.get("clean_replication_batch_034_status", "")).startswith("PASS_WITH_BATCH034_"):
        return fail("final report Batch034 status missing")
    if final_report.get("batch034_batch033_status_preserved") != "PASS_WITH_BATCH033_RETARGETING_DESIGN_ONLY":
        return fail("final report Batch034 did not preserve Batch033 boundary")
    if final_report.get("batch034_primary_artifact_name") != "post_v2_37_hardening_batch034_v10_harness_execution_artifacts":
        return fail("final report Batch034 artifact name mismatch")
    if final_report.get("batch034_batch033_artifact_ingest_status") != "PASS":
        return fail("final report Batch034 Batch033 artifact ingest not PASS")
    if final_report.get("batch034_batch033_retargeting_design_summary_status") != "PASS":
        return fail("final report Batch034 design summary not PASS")
    if final_report.get("batch034_harness_v10_materialization_status") != "PASS":
        return fail("final report Batch034 harness materialization not PASS")
    harness_path = Path(str(final_report.get("batch034_harness_v10_path", "")))
    if not harness_path.is_file():
        return fail("final report Batch034 harness path missing")
    if final_report.get("batch034_harness_v10_sha256") != sha256_file(harness_path):
        return fail("final report Batch034 harness SHA mismatch")
    if final_report.get("batch034_relative_git_dir_issue_stimulus_policy_status") != "PASS":
        return fail("final report Batch034 relative-GIT_DIR policy not PASS")
    if final_report.get("batch034_relative_git_dir_general_provider_context_used") is not False:
        return fail("final report Batch034 used relative Git directory as general provider context")
    if final_report.get("batch034_harness_v10_executed") is True:
        if final_report.get("batch034_source_head_verified_before_execution") is not True:
            return fail("final report Batch034 executed without source HEAD verification")
        if final_report.get("batch034_provider_command_context_status") != "PASS":
            return fail("final report Batch034 command context not PASS despite execution")
        if final_report.get("batch034_harness_v10_execution_status") != "PASS":
            return fail("final report Batch034 execution status not PASS despite execution")
        if final_report.get("batch034_relative_git_dir_issue_stimulus_used") is not True:
            return fail("final report Batch034 execution missed issue stimulus marker")
    else:
        if final_report.get("batch034_issue_derived_repair_feasibility") is not False:
            return fail("final report Batch034 feasibility true without execution")
    if final_report.get("batch034_harness_v10_verified") is True:
        if final_report.get("batch034_target_intent_matching_result") is not True:
            return fail("final report Batch034 verified without target-intent match")
        if final_report.get("batch034_issue_derived_repair_feasibility") is not True:
            return fail("final report Batch034 verified without feasibility")
    else:
        if final_report.get("clean_replication_batch_034_exact_blocker") not in {
            "docker_runtime_provider_unavailable",
            "provider_source_checkout_failed",
            "provider_harness_v10_execution_failed",
            "manual_lock_environment_materialization_failed",
            "safe_directory_normalization_failed",
            "harness_v10_file_missing",
            "issue_seed_not_reproduced_by_v10_harness",
            "harness_v10_execution_not_run",
            "provider_source_commit_mismatch",
            "harness_v10_execution_blocked",
        }:
            return fail("final report Batch034 blocker invalid")
        if final_report.get("batch034_issue_derived_repair_feasibility") is not False:
            return fail("final report Batch034 feasibility overclaim")
    if final_report.get("batch034_repair_ran") is not False:
        return fail("final report Batch034 repair ran unexpectedly")
    if final_report.get("batch034_patch_generated") is not False or final_report.get("batch034_patch_authorized") is not False or final_report.get("batch034_patch_attempted") is not False:
        return fail("final report Batch034 patch boundary changed")
    if final_report.get("batch034_matched_null_diagnostic_run_count") != 0:
        return fail("final report Batch034 matched-null diagnostic ran unexpectedly")
    if final_report.get("batch034_psa82_permutation_null_status") != "NOT_RUN_NO_PATCH_CANDIDATE":
        return fail("final report Batch034 PSA-82 diagnostic status mismatch")
    if final_report.get("batch034_structured_fragility_diagnostic_status") != "NOT_RUN_NO_PATCH_CANDIDATE":
        return fail("final report Batch034 structured diagnostic status mismatch")
    if final_report.get("batch034_native_repair_episode_count") != 4 or final_report.get("batch034_issue_derived_repair_episode_count") != 0:
        return fail("final report Batch034 repair counts changed")
    if not str(final_report.get("clean_replication_batch_035_status", "")).startswith("PASS_WITH_BATCH035_"):
        return fail("final report Batch035 status missing")
    if final_report.get("batch035_batch034_status_preserved") != "PASS_WITH_BATCH034_HARNESS_V10_VERIFIED_REPAIR_NOT_RUN":
        return fail("final report Batch035 did not preserve verified Batch034 boundary")
    if final_report.get("batch035_primary_artifact_name") != "post_v2_37_hardening_batch035_gated_source_repair_artifacts":
        return fail("final report Batch035 artifact name mismatch")
    if final_report.get("batch035_batch034_artifact_ingest_status") != "PASS":
        return fail("final report Batch035 Batch034 artifact ingest not PASS")
    if final_report.get("batch035_batch034_v10_verification_preservation_status") != "PASS":
        return fail("final report Batch035 did not preserve v10 verification")
    if final_report.get("batch035_repair_authorization_gate_status") != "PASS" or final_report.get("batch035_repair_authorized") is not True:
        return fail("final report Batch035 repair authorization gate not PASS")
    if final_report.get("batch035_candidate_generation_status") != "PASS" or final_report.get("batch035_source_inspection_status") != "PASS":
        return fail("final report Batch035 candidate/source inspection not PASS")
    if final_report.get("batch035_patch_candidate_touched_files") != ["src/darker/git.py"]:
        return fail("final report Batch035 patch candidate scope mismatch")
    if final_report.get("batch035_issue_derived_repair_validated") is True:
        if final_report.get("batch035_patch_application_status") != "PASS" or final_report.get("batch035_patch_scope_status") != "PASS":
            return fail("final report Batch035 validated without patch application/scope PASS")
        if final_report.get("batch035_post_repair_target_failure_resolved") is not True:
            return fail("final report Batch035 validated without post-repair target resolution")
        if final_report.get("batch035_duplicate_clean_replay_passed") is not True:
            return fail("final report Batch035 validated without duplicate clean replay")
        if final_report.get("batch035_issue_derived_repair_episode_count") != 1:
            return fail("final report Batch035 validated repair did not increment issue-derived count")
    else:
        if final_report.get("batch035_issue_derived_repair_episode_count") != 0:
            return fail("final report Batch035 incremented issue-derived count without validation")
        if final_report.get("clean_replication_batch_035_exact_blocker") not in {
            "docker_runtime_provider_unavailable",
            "provider_source_checkout_failed",
            "provider_batch035_execution_failed",
            "manual_lock_environment_materialization_failed",
            "safe_directory_normalization_failed",
            "pre_patch_target_failure_not_reproduced",
            "patch_application_failed",
            "patch_scope_invalid",
            "post_repair_target_not_resolved",
            "duplicate_clean_replay_failed",
            "issue_derived_repair_not_validated",
            "batch034_v10_verification_not_preserved",
            "no_safe_source_only_patch_candidate",
            "provider_batch035_execution_not_run",
        }:
            return fail("final report Batch035 blocker invalid")
    if final_report.get("batch035_matched_null_diagnostic_run_count") != 0:
        return fail("final report Batch035 matched-null diagnostic ran unexpectedly")
    if final_report.get("batch035_psa82_permutation_null_status") not in {"NOT_RUN_NO_PATCH_CANDIDATE", "NOT_RUN_DIAGNOSTIC_OPTIONAL"}:
        return fail("final report Batch035 PSA-82 diagnostic status mismatch")
    if final_report.get("batch035_structured_fragility_diagnostic_status") not in {"NOT_RUN_NO_PATCH_CANDIDATE", "NOT_RUN_DIAGNOSTIC_OPTIONAL"}:
        return fail("final report Batch035 structured diagnostic status mismatch")
    if final_report.get("batch035_native_repair_episode_count") != 4:
        return fail("final report Batch035 native repair count changed")
    if not str(final_report.get("clean_replication_batch_036_status", "")).startswith("PASS_WITH_BATCH036_"):
        return fail("final report Batch036 status missing")
    if final_report.get("batch036_primary_artifact_name") != "post_v2_37_hardening_batch036_post_repair_failure_decomposition_artifacts":
        return fail("final report Batch036 artifact name mismatch")
    if final_report.get("batch036_batch035_status_preserved") != "PASS_WITH_BATCH035_REPAIR_NOT_VALIDATED":
        return fail("final report Batch036 did not preserve Batch035 attempted-repair boundary")
    if final_report.get("batch036_batch035_exact_blocker_preserved") != "post_repair_target_not_resolved":
        return fail("final report Batch036 did not preserve Batch035 blocker")
    if final_report.get("batch036_batch035_artifact_ingest_status") != "PASS":
        return fail("final report Batch036 Batch035 artifact ingest not PASS")
    if final_report.get("batch036_batch035_repair_attempt_preservation_status") != "PASS":
        return fail("final report Batch036 repair attempt preservation not PASS")
    if final_report.get("batch036_post_repair_failure_decomposition_status") != "PASS":
        return fail("final report Batch036 failure decomposition not PASS")
    if final_report.get("batch036_post_repair_failure_classification") != "target_failure_still_present_with_secondary_linter_precondition":
        return fail("final report Batch036 failure classification mismatch")
    if final_report.get("batch036_source_inspection_refinement_status") != "PASS":
        return fail("final report Batch036 source inspection not PASS")
    if final_report.get("batch036_candidate_v2_generation_status") != "PASS" or final_report.get("batch036_candidate_v2_generated") is not True:
        return fail("final report Batch036 candidate v2 generation missing")
    if final_report.get("batch036_patch_candidate_v2_touched_files") != ["src/darker/git.py"]:
        return fail("final report Batch036 candidate v2 scope mismatch")
    if final_report.get("batch036_issue_derived_repair_validated") is True:
        if final_report.get("batch036_patch_v2_application_status") != "PASS":
            return fail("final report Batch036 validated without patch application PASS")
        if final_report.get("batch036_post_repair_target_failure_resolved_v2") is not True:
            return fail("final report Batch036 validated without target resolution")
        if final_report.get("batch036_duplicate_clean_replay_v2_passed") is not True:
            return fail("final report Batch036 validated without duplicate replay")
        if final_report.get("batch036_issue_derived_repair_episode_count") != 1:
            return fail("final report Batch036 validated repair did not increment issue-derived count")
    else:
        if final_report.get("batch036_issue_derived_repair_episode_count") != 0:
            return fail("final report Batch036 incremented issue-derived count without validation")
        if final_report.get("clean_replication_batch_036_exact_blocker") not in {
            "docker_runtime_provider_unavailable",
            "provider_source_checkout_failed",
            "provider_batch036_execution_failed",
            "manual_lock_environment_materialization_failed",
            "safe_directory_normalization_failed",
            "patch_v2_application_failed",
            "target_failure_still_present_with_secondary_linter_precondition",
            "target_resolution_blocked_by_secondary_linter_precondition",
            "target_failure_still_present",
            "target_resolution_status_ambiguous",
            "duplicate_clean_replay_failed",
            "no_safe_source_only_refinement_candidate",
            "provider_batch036_execution_not_run",
        }:
            return fail("final report Batch036 blocker invalid")
    if final_report.get("batch036_matched_null_diagnostic_run_count") != 0:
        return fail("final report Batch036 matched-null diagnostic ran unexpectedly")
    if final_report.get("batch036_psa82_permutation_null_status") not in {"NOT_RUN_NO_PATCH_CANDIDATE", "NOT_RUN_DIAGNOSTIC_OPTIONAL"}:
        return fail("final report Batch036 PSA-82 diagnostic status mismatch")
    if final_report.get("batch036_structured_fragility_diagnostic_status") not in {"NOT_RUN_NO_PATCH_CANDIDATE", "NOT_RUN_DIAGNOSTIC_OPTIONAL"}:
        return fail("final report Batch036 structured diagnostic status mismatch")
    if final_report.get("batch036_controller_audit_closure_check_status") not in {"NOT_RUN_NO_PATCH_CANDIDATE", "NOT_RUN_DIAGNOSTIC_OPTIONAL"}:
        return fail("final report Batch036 ControllerAudit diagnostic status mismatch")
    if final_report.get("batch036_native_repair_episode_count") != 4:
        return fail("final report Batch036 native repair count changed")
    if not str(final_report.get("clean_replication_batch_037_status", "")).startswith("PASS_WITH_BATCH037_"):
        return fail("final report Batch037 status missing")
    if final_report.get("batch037_primary_artifact_name") != "post_v2_37_hardening_batch037_provider_execution_substage_recovery_artifacts":
        return fail("final report Batch037 artifact name mismatch")
    if final_report.get("batch037_batch036_artifact_ingest_status") != "PASS" or final_report.get("batch037_batch036_artifact_verification_status") != "PASS":
        return fail("final report Batch037 Batch036 artifact custody not PASS")
    if final_report.get("batch037_batch036_status_preserved") != "PASS_WITH_BATCH036_REPAIR_NOT_VALIDATED":
        return fail("final report Batch037 did not preserve Batch036 repair-not-validated boundary")
    if final_report.get("batch037_batch036_exact_blocker_preserved") != "provider_batch036_execution_failed":
        return fail("final report Batch037 did not preserve Batch036 provider blocker")
    if final_report.get("batch037_candidate_v2_preservation_status") != "PASS":
        return fail("final report Batch037 candidate v2 preservation not PASS")
    if final_report.get("batch037_candidate_v2_patch_sha256") != "9c1061f5c60878b7ace6a3c02f41ec2af162fd4de66192a34028ed720e864ec1":
        return fail("final report Batch037 patch SHA mismatch")
    if final_report.get("batch037_provider_execution_substage_diagnosis_status") != "PASS":
        return fail("final report Batch037 substage diagnosis not PASS")
    if final_report.get("batch037_patch_v2_application_status") == "PASS":
        if final_report.get("batch037_patch_v2_apply_check_status") != "PASS":
            return fail("final report Batch037 applied patch without apply-check PASS")
        if final_report.get("batch037_patch_v2_scope_audit_status") != "PASS":
            return fail("final report Batch037 patch scope audit not PASS")
    if final_report.get("batch037_issue_derived_repair_validated") is True:
        if final_report.get("batch037_post_repair_target_failure_resolved_v2") is not True:
            return fail("final report Batch037 validated without target resolution")
        if final_report.get("batch037_duplicate_clean_replay_v2_passed") is not True:
            return fail("final report Batch037 validated without duplicate replay")
    if final_report.get("batch037_issue_derived_repair_episode_count") != 0:
        return fail("final report Batch037 incremented issue-derived count")
    if final_report.get("batch037_issue_derived_repair_episode_count_increment_candidate") is not False:
        return fail("final report Batch037 marked issue-derived count increment candidate")
    if final_report.get("batch037_matched_null_diagnostic_run_count") != 0:
        return fail("final report Batch037 matched-null diagnostic ran unexpectedly")
    if final_report.get("batch037_psa82_permutation_null_status") not in {"NOT_RUN_NO_PATCH_CANDIDATE", "NOT_RUN_DIAGNOSTIC_OPTIONAL"}:
        return fail("final report Batch037 PSA-82 diagnostic status mismatch")
    if final_report.get("batch037_structured_fragility_diagnostic_status") not in {"NOT_RUN_NO_PATCH_CANDIDATE", "NOT_RUN_DIAGNOSTIC_OPTIONAL"}:
        return fail("final report Batch037 structured diagnostic status mismatch")
    if final_report.get("batch037_controller_audit_closure_check_status") not in {"NOT_RUN_NO_PATCH_CANDIDATE", "NOT_RUN_DIAGNOSTIC_OPTIONAL"}:
        return fail("final report Batch037 ControllerAudit diagnostic status mismatch")
    if final_report.get("batch037_native_repair_episode_count") != 4:
        return fail("final report Batch037 native repair count changed")
    if not str(final_report.get("clean_replication_batch_038_status", "")).startswith("PASS_WITH_BATCH038_"):
        return fail("final report Batch038 status missing")
    if final_report.get("batch038_primary_artifact_name") != "post_v2_37_hardening_batch038_reactome_patch_serialization_recovery_artifacts":
        return fail("final report Batch038 artifact name mismatch")
    if final_report.get("batch038_batch037_artifact_ingest_status") != "PASS" or final_report.get("batch038_batch037_artifact_verification_status") != "PASS":
        return fail("final report Batch038 Batch037 artifact custody not PASS")
    if final_report.get("batch038_batch037_status_preserved") != "PASS_WITH_BATCH037_PROVIDER_SUBSTAGE_BLOCKED":
        return fail("final report Batch038 did not preserve Batch037 provider substage boundary")
    if final_report.get("batch038_batch037_exact_blocker_preserved") != "patch_v2_apply_check_failed":
        return fail("final report Batch038 did not preserve Batch037 patch blocker")
    if final_report.get("batch038_governance_artifacts_generated") is not True:
        return fail("final report Batch038 governance artifacts missing")
    if final_report.get("batch038_patch_serialization_failure_classification") != "patch_serialization_failure_before_semantic_repair_validation":
        return fail("final report Batch038 patch serialization classification mismatch")
    if final_report.get("batch038_original_patch_sha256") != "9c1061f5c60878b7ace6a3c02f41ec2af162fd4de66192a34028ed720e864ec1":
        return fail("final report Batch038 original patch SHA mismatch")
    if final_report.get("batch038_corrected_patch_sha256") != "1cf85f55ec48cc47199e33b3b04fc74a16bf935814784e9abdc56b574d960396":
        return fail("final report Batch038 corrected patch SHA mismatch")
    if final_report.get("batch038_corrected_patch_application_status") == "PASS":
        if final_report.get("batch038_corrected_patch_apply_check_status") != "PASS":
            return fail("final report Batch038 applied patch without apply-check PASS")
        if final_report.get("batch038_corrected_patch_scope_audit_status") != "PASS":
            return fail("final report Batch038 corrected patch scope audit not PASS")
    if final_report.get("batch038_issue_derived_repair_validated") is True:
        if final_report.get("batch038_post_repair_target_failure_resolved") is not True:
            return fail("final report Batch038 validated without target resolution")
        if final_report.get("batch038_duplicate_clean_replay_passed") is not True:
            return fail("final report Batch038 validated without duplicate replay")
    else:
        if final_report.get("batch038_issue_derived_repair_episode_count") != 0:
            return fail("final report Batch038 incremented issue-derived count without validation")
        if final_report.get("batch038_issue_derived_repair_episode_count_increment_candidate") is not False:
            return fail("final report Batch038 marked issue-derived count increment candidate without validation")
    if final_report.get("batch038_native_repair_episode_count") != 4:
        return fail("final report Batch038 native repair count changed")
    if final_report.get("batch038_matched_null_diagnostic_run_count") != 0:
        return fail("final report Batch038 matched-null diagnostic ran unexpectedly")
    if final_report.get("batch038_psa82_diagnostic_status") not in {"NOT_RUN_NO_PATCH_CANDIDATE", "NOT_RUN_DIAGNOSTIC_OPTIONAL"}:
        return fail("final report Batch038 PSA-82 diagnostic status mismatch")
    if final_report.get("batch038_structured_fragility_diagnostic_status") not in {"NOT_RUN_NO_PATCH_CANDIDATE", "NOT_RUN_DIAGNOSTIC_OPTIONAL"}:
        return fail("final report Batch038 structured diagnostic status mismatch")
    if final_report.get("batch038_controller_audit_closure_check_status") not in {"NOT_RUN_NO_PATCH_CANDIDATE", "NOT_RUN_DIAGNOSTIC_OPTIONAL"}:
        return fail("final report Batch038 ControllerAudit diagnostic status mismatch")
    if final_report.get("clean_replication_batch_039_status") != "PASS_WITH_BATCH039_DECLARED_SECONDARY_COFACTOR_LOCK_REQUIRED":
        return fail("final report Batch039 status mismatch")
    if final_report.get("clean_replication_batch_039_exact_blocker") != "declared_secondary_cofactor_unpinned_lock_required":
        return fail("final report Batch039 blocker mismatch")
    if final_report.get("batch039_primary_artifact_name") != "post_v2_37_hardening_batch039_secondary_cofactor_governance_artifacts":
        return fail("final report Batch039 artifact name mismatch")
    if final_report.get("batch039_batch038_artifact_ingest_status") != "PASS" or final_report.get("batch039_batch038_artifact_verification_status") != "PASS":
        return fail("final report Batch039 Batch038 artifact custody not PASS")
    if final_report.get("batch039_batch038_status_preserved") != "PASS_WITH_BATCH038_TARGET_RESOLVED_SECONDARY_LINTER_PRECONDITION":
        return fail("final report Batch039 did not preserve Batch038 target-resolution boundary")
    if final_report.get("batch039_batch038_exact_blocker_preserved") != "target_resolution_blocked_by_secondary_linter_precondition":
        return fail("final report Batch039 did not preserve Batch038 secondary blocker")
    if final_report.get("batch039_batch038_target_failure_resolved") is not True or final_report.get("batch039_batch038_original_git_target_indicators_absent") is not True:
        return fail("final report Batch039 did not preserve original target resolution")
    if final_report.get("batch039_general_secondary_cofactor_governance_status") != "PASS":
        return fail("final report Batch039 general cofactor governance missing")
    if final_report.get("batch039_declared_linter_verification_status") != "PASS":
        return fail("final report Batch039 declared linter verification missing")
    if final_report.get("batch039_materialization_policy_status") != "BLOCK" or final_report.get("batch039_materialization_result_status") != "BLOCK":
        return fail("final report Batch039 materialization boundary mismatch")
    if final_report.get("batch039_post_repair_target_replay_under_cofactor_governance_status") != "NOT_RUN":
        return fail("final report Batch039 replay ran without materialization authorization")
    if final_report.get("batch039_secondary_cofactor_chain_status") != "PASS":
        return fail("final report Batch039 cofactor chain status mismatch")
    if final_report.get("batch039_duplicate_clean_replay_under_cofactor_governance_status") != "NOT_RUN":
        return fail("final report Batch039 duplicate replay boundary mismatch")
    if final_report.get("batch039_issue_derived_repair_validated") is not False:
        return fail("final report Batch039 issue-derived validation overclaim")
    if final_report.get("batch039_issue_derived_repair_episode_count_increment_candidate") is not False:
        return fail("final report Batch039 count increment candidate overclaim")
    if final_report.get("batch039_native_repair_episode_count") != 4 or final_report.get("batch039_issue_derived_repair_episode_count") != 0:
        return fail("final report Batch039 repair counts changed")
    if not str(final_report.get("clean_replication_batch_040_status", "")).startswith("PASS_WITH_BATCH040_"):
        return fail("final report Batch040 status missing")
    if final_report.get("batch040_primary_artifact_name") != "post_v2_37_hardening_batch040_reviewed_cofactor_lock_artifacts":
        return fail("final report Batch040 artifact name mismatch")
    if final_report.get("batch040_batch039_artifact_ingest_status") != "PASS" or final_report.get("batch040_batch039_artifact_verification_status") != "PASS":
        return fail("final report Batch040 Batch039 artifact custody not PASS")
    if final_report.get("batch040_batch039_status_preserved") != "PASS_WITH_BATCH039_DECLARED_SECONDARY_COFACTOR_LOCK_REQUIRED":
        return fail("final report Batch040 did not preserve Batch039 status")
    if final_report.get("batch040_batch039_exact_blocker_preserved") != "declared_secondary_cofactor_unpinned_lock_required":
        return fail("final report Batch040 did not preserve Batch039 blocker")
    if final_report.get("batch040_batch039_target_resolution_preservation_status") != "PASS":
        return fail("final report Batch040 did not preserve target resolution")
    if final_report.get("batch040_governance_continuity_status") != "PASS":
        return fail("final report Batch040 governance continuity not PASS")
    if final_report.get("batch040_reviewed_cofactor_lock_policy_status") != "PASS":
        return fail("final report Batch040 reviewed cofactor lock policy not PASS")
    if final_report.get("batch040_pylint_lock_discovery_status") not in {"PASS", "BLOCK"}:
        return fail("final report Batch040 pylint lock discovery status invalid")
    if final_report.get("batch040_pylint_lock_review_status") not in {"PASS", "BLOCK"}:
        return fail("final report Batch040 pylint lock review status invalid")
    if final_report.get("batch040_provider_only_materialization_status") == "PASS":
        if final_report.get("batch040_pylint_lock_review_status") != "PASS":
            return fail("final report Batch040 materialization passed without lock review")
        if final_report.get("batch040_pylint_executable_verification_status") != "PASS":
            return fail("final report Batch040 materialization passed without executable verification")
    if final_report.get("batch040_post_repair_target_replay_status") != "NOT_RUN":
        if final_report.get("batch040_provider_only_materialization_status") != "PASS":
            return fail("final report Batch040 replay ran before materialization PASS")
    if final_report.get("batch040_duplicate_clean_replay_status") != "NOT_RUN":
        if final_report.get("batch040_post_repair_target_replay_fully_passed") is not True:
            return fail("final report Batch040 duplicate replay ran before target replay full pass")
    if final_report.get("batch040_issue_derived_repair_validated") is True:
        if final_report.get("batch040_post_repair_target_replay_fully_passed") is not True:
            return fail("final report Batch040 validated without target replay full pass")
        if final_report.get("batch040_duplicate_clean_replay_passed") is not True:
            return fail("final report Batch040 validated without duplicate replay pass")
    else:
        if final_report.get("batch040_issue_derived_repair_episode_count_increment_candidate") is True:
            return fail("final report Batch040 marked count increment candidate without validation")
    if final_report.get("batch040_native_repair_episode_count") != 4 or final_report.get("batch040_issue_derived_repair_episode_count") != 0:
        return fail("final report Batch040 repair counts changed")
    if not str(final_report.get("clean_replication_batch_041_status", "")).startswith("PASS_WITH_BATCH041_"):
        return fail("final report Batch041 status missing")
    if final_report.get("batch041_primary_artifact_name") != "post_v2_37_hardening_batch041_lock_completion_identity_integrity_artifacts":
        return fail("final report Batch041 artifact name mismatch")
    if final_report.get("batch041_batch040_artifact_ingest_status") != "PASS" or final_report.get("batch041_batch040_artifact_verification_status") != "PASS":
        return fail("final report Batch041 Batch040 artifact custody not PASS")
    if final_report.get("batch041_artifact_internal_status") != "PASS_WITH_BATCH040_PINNED_COFACTOR_LOCK_UNAVAILABLE":
        return fail("final report Batch041 did not preserve artifact-internal Batch040 status")
    if final_report.get("batch041_artifact_internal_blocker") != "pinned_cofactor_lock_unavailable":
        return fail("final report Batch041 did not preserve artifact-internal Batch040 blocker")
    if final_report.get("batch041_active_batch040_blocker_after_ingest") != "pinned_cofactor_lock_unavailable":
        return fail("final report Batch041 active Batch040 blocker mismatch")
    for key in [
        "batch041_stable_identity_integrity_status",
        "batch041_proof_ledger_referrer_audit_status",
        "batch041_secondary_cofactor_chain_budget_status",
        "batch041_replay_classification_status",
        "batch041_diagnostics_registry_status",
        "batch041_validation_activation_status",
        "batch041_transport_export_equivalence_status",
        "batch041_evidence_origin_classification_status",
    ]:
        if final_report.get(key) != "PASS":
            return fail(f"final report Batch041 {key} not PASS")
    if final_report.get("batch041_lock_completion_status") not in {"PASS", "BLOCK"}:
        return fail("final report Batch041 lock-completion status invalid")
    if final_report.get("batch041_lock_v2_review_status") not in {"PASS", "BLOCK"}:
        return fail("final report Batch041 lock-v2 review status invalid")
    if final_report.get("batch041_lock_v2_review_status") == "PASS" and final_report.get("batch041_lock_v2_provider_safe") is not True:
        return fail("final report Batch041 reviewed lock-v2 not provider-safe")
    if final_report.get("batch041_cofactor_lock_provenance_status") not in {"PASS", "BLOCK"}:
        return fail("final report Batch041 cofactor provenance status invalid")
    if final_report.get("batch041_dependency_drift_audit_status") not in {"PASS", "NOT_RUN", "BLOCK"}:
        return fail("final report Batch041 dependency drift status invalid")
    if final_report.get("batch041_provider_only_materialization_status") == "PASS":
        if final_report.get("batch041_pylint_executable_verification_status") != "PASS":
            return fail("final report Batch041 materialization passed without executable verification")
    if final_report.get("batch041_post_repair_target_replay_status") != "NOT_RUN":
        if final_report.get("batch041_provider_only_materialization_status") != "PASS":
            return fail("final report Batch041 replay ran before materialization PASS")
        if final_report.get("batch041_dependency_drift_audit_status") != "PASS":
            return fail("final report Batch041 replay ran before dependency drift PASS")
    if final_report.get("batch041_duplicate_clean_replay_status") != "NOT_RUN":
        if final_report.get("batch041_post_repair_target_replay_status") != "PASS":
            return fail("final report Batch041 duplicate replay ran before target replay PASS")
    if final_report.get("batch041_issue_derived_repair_validated") is True and final_report.get("batch041_duplicate_clean_replay_status") != "PASS":
        return fail("final report Batch041 validated repair without duplicate replay PASS")
    if final_report.get("batch041_native_repair_episode_count") != 4 or final_report.get("batch041_issue_derived_repair_episode_count") != 0:
        return fail("final report Batch041 repair counts changed")
    if final_report.get("clean_replication_batch_042_status") != "PASS_WITH_BATCH042_ISSUE_DERIVED_REPAIR_COUNT_LOCKED":
        return fail("final report Batch042 status mismatch")
    if final_report.get("clean_replication_batch_042_exact_blocker") is not None:
        return fail("final report Batch042 blocker should be None")
    if final_report.get("batch042_primary_artifact_name") != "post_v2_37_hardening_batch042_repair_validation_count_lock_artifacts":
        return fail("final report Batch042 artifact name mismatch")
    if final_report.get("batch042_batch041_artifact_ingest_status") != "PASS" or final_report.get("batch042_batch041_artifact_verification_status") != "PASS":
        return fail("final report Batch042 Batch041 artifact custody not PASS")
    if final_report.get("batch042_repair_validation_preservation_status") != "PASS":
        return fail("final report Batch042 repair validation preservation not PASS")
    if final_report.get("batch042_replay_and_duplicate_replay_preservation_status") != "PASS":
        return fail("final report Batch042 replay preservation not PASS")
    if final_report.get("batch042_issue_derived_episode_count_gate_status") != "PASS":
        return fail("final report Batch042 count gate not PASS")
    if final_report.get("batch042_issue_derived_repair_episode_count_before") != 0:
        return fail("final report Batch042 before-count mismatch")
    if final_report.get("batch042_issue_derived_repair_episode_count_after") != 1:
        return fail("final report Batch042 after-count mismatch")
    if final_report.get("batch042_native_external_repair_episode_count") != 4:
        return fail("final report Batch042 native count changed")
    if final_report.get("batch042_stable_identity_lineage_lock_status") != "PASS":
        return fail("final report Batch042 stable identity lineage lock not PASS")
    if final_report.get("batch042_proof_ledger_validation_lock_status") != "PASS":
        return fail("final report Batch042 proof-ledger validation lock not PASS")
    if final_report.get("batch042_replay_classification_preservation_status") != "PASS":
        return fail("final report Batch042 replay classification preservation not PASS")
    if final_report.get("batch042_stale_blocker_retirement_status") != "PASS":
        return fail("final report Batch042 stale blocker retirement not PASS")
    if final_report.get("batch042_full_scoring") != "NOT_RUN/disallowed":
        return fail("final report Batch042 full scoring boundary changed")
    if final_report.get("batch042_memory_lift") != "not_demonstrated":
        return fail("final report Batch042 memory-lift boundary changed")
    if final_report.get("batch042_self_maintaining_software") != "false/not_demonstrated":
        return fail("final report Batch042 self-maintaining boundary changed")
    if final_report.get("clean_replication_batch_043_status") != "PASS_WITH_BATCH043_ISSUE_DERIVED_EPISODE_CANONICALIZED":
        return fail("final report Batch043 status mismatch")
    if final_report.get("clean_replication_batch_043_exact_blocker") is not None:
        return fail("final report Batch043 blocker should be None")
    if final_report.get("batch043_primary_artifact_name") != "post_v2_37_hardening_batch043_episode_canonicalization_protocolization_artifacts":
        return fail("final report Batch043 artifact name mismatch")
    if final_report.get("batch043_batch042_artifact_ingest_status") != "PASS" or final_report.get("batch043_batch042_artifact_verification_status") != "PASS":
        return fail("final report Batch043 Batch042 artifact custody not PASS")
    if final_report.get("batch043_batch042_count_lock_preservation_status") != "PASS":
        return fail("final report Batch043 count lock preservation not PASS")
    if final_report.get("batch043_batch042_claim_boundary_preservation_status") != "PASS":
        return fail("final report Batch043 claim boundary preservation not PASS")
    if final_report.get("batch043_canonical_episode_record_status") != "PASS":
        return fail("final report Batch043 canonical episode record not PASS")
    if final_report.get("batch043_protocolization_audit_status") != "PASS":
        return fail("final report Batch043 protocolization audit not PASS")
    if final_report.get("batch043_isomorphic_coverage_matrix_status") != "PASS":
        return fail("final report Batch043 coverage matrix not PASS")
    if final_report.get("batch043_reusable_episode_schema_status") != "PASS":
        return fail("final report Batch043 reusable episode schema not PASS")
    if final_report.get("batch043_protocol_guardrail_update_status") != "PASS":
        return fail("final report Batch043 protocol guardrail update not PASS")
    if final_report.get("batch043_stale_blocker_lane_closure_status") != "PASS":
        return fail("final report Batch043 lane closure not PASS")
    if final_report.get("batch043_issue_derived_repair_episode_count") != 1:
        return fail("final report Batch043 issue-derived count mismatch")
    if final_report.get("batch043_native_external_repair_episode_count") != 4:
        return fail("final report Batch043 native count changed")
    if final_report.get("batch043_full_scoring") != "NOT_RUN/disallowed":
        return fail("final report Batch043 full scoring boundary changed")
    if final_report.get("batch043_memory_lift") != "not_demonstrated":
        return fail("final report Batch043 memory-lift boundary changed")
    if final_report.get("batch043_self_maintaining_software") != "false/not_demonstrated":
        return fail("final report Batch043 self-maintaining boundary changed")
    if final_report.get("batch043_production_readiness") != "false/not_demonstrated":
        return fail("final report Batch043 production boundary changed")
    if final_report.get("batch043_current_protocol") != "v2.13":
        return fail("final report Batch043 current protocol changed")
    if final_report.get("clean_replication_batch_044_status") != "PASS_WITH_BATCH044_GUARDRAILS_ENFORCED_SEED_SELECTION_AUTHORIZED":
        return fail("final report Batch044 status mismatch")
    if final_report.get("clean_replication_batch_044_exact_blocker") is not None:
        return fail("final report Batch044 blocker should be None")
    if final_report.get("batch044_primary_artifact_name") != "post_v2_37_hardening_batch044_guardrail_enforcement_seed_eligibility_artifacts":
        return fail("final report Batch044 artifact name mismatch")
    if final_report.get("batch044_batch043_artifact_ingest_status") != "PASS" or final_report.get("batch044_batch043_artifact_verification_status") != "PASS":
        return fail("final report Batch044 Batch043 artifact custody not PASS")
    if final_report.get("batch044_episode_canonicalization_preservation_status") != "PASS":
        return fail("final report Batch044 episode preservation not PASS")
    if final_report.get("batch044_standing_guardrail_enforcement_status") != "PASS":
        return fail("final report Batch044 guardrail enforcement not PASS")
    if final_report.get("batch044_isomorphic_coverage_enforcement_status") != "PASS":
        return fail("final report Batch044 coverage enforcement not PASS")
    if final_report.get("batch044_future_issue_derived_lane_eligibility_schema_status") != "PASS":
        return fail("final report Batch044 eligibility schema not PASS")
    if final_report.get("batch044_next_issue_seed_selection_gate_status") != "PASS":
        return fail("final report Batch044 next issue-seed gate not PASS")
    if final_report.get("batch044_next_issue_seed_selection_authorized") is not True:
        return fail("final report Batch044 next issue-seed selection not authorized")
    if final_report.get("batch044_protocol_version_boundary_status") != "PASS":
        return fail("final report Batch044 protocol boundary not PASS")
    if final_report.get("batch044_issue_derived_repair_episode_count") != 1:
        return fail("final report Batch044 issue-derived count mismatch")
    if final_report.get("batch044_native_external_repair_episode_count") != 4:
        return fail("final report Batch044 native count changed")
    if final_report.get("batch044_full_scoring") != "NOT_RUN/disallowed":
        return fail("final report Batch044 full scoring boundary changed")
    if final_report.get("batch044_memory_lift") != "not_demonstrated":
        return fail("final report Batch044 memory-lift boundary changed")
    if final_report.get("batch044_self_maintaining_software") != "false/not_demonstrated":
        return fail("final report Batch044 self-maintaining boundary changed")
    if final_report.get("batch044_production_readiness") != "false/not_demonstrated":
        return fail("final report Batch044 production boundary changed")
    if final_report.get("batch044_current_protocol") != "v2.13":
        return fail("final report Batch044 current protocol changed")
    if final_report.get("clean_replication_batch_045_status") != "PASS_WITH_BATCH045_PROTOCOL_CANDIDATE_SEED_INVENTORY_AUTHORIZED":
        return fail("final report Batch045 status mismatch")
    if final_report.get("clean_replication_batch_045_exact_blocker") is not None:
        return fail("final report Batch045 blocker should be None")
    if final_report.get("batch045_primary_artifact_name") != "post_v2_37_hardening_batch045_protocol_candidate_seed_inventory_artifacts":
        return fail("final report Batch045 artifact name mismatch")
    if final_report.get("batch045_batch044_artifact_ingest_status") != "PASS" or final_report.get("batch045_batch044_artifact_verification_status") != "PASS":
        return fail("final report Batch045 Batch044 artifact custody not PASS")
    if final_report.get("batch045_batch044_guardrail_enforcement_preservation_status") != "PASS":
        return fail("final report Batch045 guardrail preservation not PASS")
    if final_report.get("batch045_batch044_seed_selection_authorization_preservation_status") != "PASS":
        return fail("final report Batch045 seed authorization preservation not PASS")
    if final_report.get("batch045_batch044_claim_boundary_preservation_status") != "PASS":
        return fail("final report Batch045 claim preservation not PASS")
    if final_report.get("batch045_protocol_candidate_v2_14_review_status") != "PASS":
        return fail("final report Batch045 protocol candidate review not PASS")
    if final_report.get("batch045_protocol_candidate_v2_14_status") != "READY_FOR_SEPARATE_PROMOTION":
        return fail("final report Batch045 protocol candidate not ready")
    if final_report.get("batch045_guardrail_regression_audit_status") != "PASS":
        return fail("final report Batch045 guardrail regression audit not PASS")
    if final_report.get("batch045_scoped_next_issue_seed_discovery_policy_status") != "PASS":
        return fail("final report Batch045 scoped discovery policy not PASS")
    if final_report.get("batch045_next_issue_seed_candidate_discovery_gate_status") != "PASS":
        return fail("final report Batch045 seed discovery gate not PASS")
    if final_report.get("batch045_seed_candidate_discovery_authorized") is not True:
        return fail("final report Batch045 seed discovery not authorized")
    if final_report.get("batch045_candidate_inventory_count") != 0:
        return fail("final report Batch045 candidate inventory count mismatch")
    if final_report.get("batch045_issue_derived_repair_episode_count") != 1:
        return fail("final report Batch045 issue-derived count mismatch")
    if final_report.get("batch045_native_external_repair_episode_count") != 4:
        return fail("final report Batch045 native count changed")
    if final_report.get("batch045_full_scoring") != "NOT_RUN/disallowed":
        return fail("final report Batch045 full scoring boundary changed")
    if final_report.get("batch045_memory_lift") != "not_demonstrated":
        return fail("final report Batch045 memory-lift boundary changed")
    if final_report.get("batch045_self_maintaining_software") != "false/not_demonstrated":
        return fail("final report Batch045 self-maintaining boundary changed")
    if final_report.get("batch045_production_readiness") != "false/not_demonstrated":
        return fail("final report Batch045 production boundary changed")
    if final_report.get("batch045_current_protocol") != "v2.13":
        return fail("final report Batch045 current protocol changed")
    if final_report.get("clean_replication_batch_046_status") != "PASS_WITH_BATCH046_BROT_BULB_ENVIRONMENT_LOCATOR_AUTHORIZED":
        return fail("final report Batch046 status mismatch")
    if final_report.get("clean_replication_batch_046_exact_blocker") is not None:
        return fail("final report Batch046 blocker should be None")
    if final_report.get("batch046_primary_artifact_name") != "post_v2_37_hardening_batch046_brot_bulb_environment_locator_artifacts":
        return fail("final report Batch046 artifact name mismatch")
    if final_report.get("batch046_batch045_artifact_ingest_status") != "PASS" or final_report.get("batch046_batch045_artifact_verification_status") != "PASS":
        return fail("final report Batch046 Batch045 artifact custody not PASS")
    if final_report.get("batch046_protocol_candidate_v2_14_preservation_status") != "PASS":
        return fail("final report Batch046 protocol candidate preservation not PASS")
    if final_report.get("batch046_protocol_v2_14_promotion_decision_status") != "PASS":
        return fail("final report Batch046 promotion decision not PASS")
    if final_report.get("batch046_protocol_v2_14_promotion_status") != "READY_BUT_NOT_PROMOTED":
        return fail("final report Batch046 promotion status mismatch")
    for key in [
        "batch046_brot_bulb_boundary_lock_status",
        "batch046_torus_brot_environment_map_status",
        "batch046_tot_brot_coupled_blocker_graph_status",
        "batch046_tot_bulb_probe_design_status",
        "batch046_environment_bug_locator_eligibility_status",
        "batch046_seed_discovery_expansion_policy_status",
    ]:
        if final_report.get(key) != "PASS":
            return fail(f"final report {key} not PASS")
    if final_report.get("batch046_environment_bug_locator_probe_authorized") is not True:
        return fail("final report Batch046 environment locator not authorized")
    if final_report.get("batch046_bounded_probe_inventory_count") != 14:
        return fail("final report Batch046 probe inventory count mismatch")
    if final_report.get("batch046_issue_derived_repair_episode_count") != 1:
        return fail("final report Batch046 issue-derived count mismatch")
    if final_report.get("batch046_native_external_repair_episode_count") != 4:
        return fail("final report Batch046 native count changed")
    if final_report.get("batch046_full_scoring") != "NOT_RUN/disallowed":
        return fail("final report Batch046 full scoring boundary changed")
    if final_report.get("batch046_memory_lift") != "not_demonstrated":
        return fail("final report Batch046 memory-lift boundary changed")
    if final_report.get("batch046_self_maintaining_software") != "false/not_demonstrated":
        return fail("final report Batch046 self-maintaining boundary changed")
    if final_report.get("batch046_production_readiness") != "false/not_demonstrated":
        return fail("final report Batch046 production boundary changed")
    if final_report.get("batch046_current_protocol") != "v2.13":
        return fail("final report Batch046 current protocol changed")
    if final_report.get("clean_replication_batch_047_status") != "PASS_WITH_BATCH047_TOT_BULB_PROBE_EXECUTION_RECORDED":
        return fail("final report Batch047 status mismatch")
    if final_report.get("clean_replication_batch_047_exact_blocker") is not None:
        return fail("final report Batch047 blocker should be None")
    if final_report.get("batch047_primary_artifact_name") != "post_v2_37_hardening_batch047_tot_bulb_probe_execution_artifacts":
        return fail("final report Batch047 artifact name mismatch")
    if final_report.get("batch047_batch046_artifact_ingest_status") != "PASS" or final_report.get("batch047_batch046_artifact_verification_status") != "PASS":
        return fail("final report Batch047 Batch046 artifact custody not PASS")
    if final_report.get("batch047_brot_bulb_locator_preservation_status") != "PASS":
        return fail("final report Batch047 locator preservation not PASS")
    if final_report.get("batch047_source_registry_status") != "PASS":
        return fail("final report Batch047 source registry not PASS")
    if int(final_report.get("batch047_source_registry_entry_count", 0)) < 1:
        return fail("final report Batch047 source registry empty")
    if final_report.get("batch047_probe_execution_policy_status") != "PASS" or final_report.get("batch047_probe_execution_results_status") != "PASS":
        return fail("final report Batch047 probe policy/results not PASS")
    if int(final_report.get("batch047_executed_probe_count", 0)) < 1:
        return fail("final report Batch047 executed no probes")
    if int(final_report.get("batch047_not_run_probe_count", -1)) < 0:
        return fail("final report Batch047 NOT_RUN probe count invalid")
    if final_report.get("batch047_candidate_inventory_count") != 0:
        return fail("final report Batch047 candidate inventory count mismatch")
    if final_report.get("batch047_protocol_v2_14_boundary_status") != "PASS":
        return fail("final report Batch047 protocol boundary not PASS")
    if final_report.get("batch047_issue_derived_repair_episode_count") != 1:
        return fail("final report Batch047 issue-derived count mismatch")
    if final_report.get("batch047_native_external_repair_episode_count") != 4:
        return fail("final report Batch047 native count changed")
    if final_report.get("batch047_full_scoring") != "NOT_RUN/disallowed":
        return fail("final report Batch047 full scoring boundary changed")
    if final_report.get("batch047_memory_lift") != "not_demonstrated":
        return fail("final report Batch047 memory-lift boundary changed")
    if final_report.get("batch047_self_maintaining_software") != "false/not_demonstrated":
        return fail("final report Batch047 self-maintaining boundary changed")
    if final_report.get("batch047_production_readiness") != "false/not_demonstrated":
        return fail("final report Batch047 production boundary changed")
    if final_report.get("batch047_current_protocol") != "v2.13":
        return fail("final report Batch047 current protocol changed")
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
