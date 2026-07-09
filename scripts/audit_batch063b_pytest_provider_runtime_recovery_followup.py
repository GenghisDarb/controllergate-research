from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from controllergate.core.manifests import verify_manifest


OUT_DIR = ROOT / "outputs" / "post_v2_37_hardening_batch063b_pytest_provider_runtime_recovery_followup"
CURRENT_PROTOCOL = "v2.14"

PUBLIC_FORBIDDEN_TERMS = [
    "TLD",
    "TORUS",
    "chromosomal",
    "biological",
    "ToT-BULB",
    "metrological immune system",
    "replisome",
    "nuclear pore",
    "MCM",
    "6-set",
    "14-set",
    "196-set",
    "apoptosis",
    "SafeDeath",
    "sister chromatid",
    "cohesin",
]

FORBIDDEN_STATUS_FRAGMENTS = [
    ".zip",
    ".tar",
    ".tgz",
    ".7z",
    ".pyc",
    "__pycache__",
    "ControllerGate_runtime",
    ".venv",
    "/venv/",
    "\\venv\\",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
]

REQUIRED_FILES = [
    "batch066_artifact_ingestion_summary.json",
    "batch066_artifact_sha256_verification.json",
    "batch066_result_preservation.json",
    "batch066_pytest_command_boundary_preservation.json",
    "batch066_provider_runtime_preservation.json",
    "batch066_permanent_fix_queue_preservation.json",
    "batch066_reactome_tld_utilization_preservation.json",
    "batch066_claim_boundary_preservation.json",
    "batch066_next_action_boundary.json",
    "batch063b_candidate_scope.json",
    "batch063b_candidate_scope_audit.json",
    "batch063b_excluded_candidate_registry.json",
    "batch063b_decision_time_input_manifest.json",
    "batch063b_forbidden_evidence_audit.json",
    "batch063b_issue_body_leakage_boundary.json",
    "batch063b_label_blindness_check.json",
    "batch063b_gold_patch_exclusion_check.json",
    "batch063b_future_evidence_exclusion_check.json",
    "pytest_workspace_manifest_batch063b.json",
    "pytest_commit_verification_batch063b.json",
    "pytest_workspace_custody_check_batch063b.json",
    "pytest_workspace_purity_manifest_batch063b.json",
    "pytest_stale_cache_contamination_check_batch063b.json",
    "pytest_baseline_source_hashes_batch063b.json",
    "pytest_project_config_map_batch063b.json",
    "pytest_declared_dependency_map_batch063b.json",
    "pytest_declared_runtime_map_batch063b.json",
    "pytest_declared_test_command_map_batch063b.json",
    "baseline_registry_snapshot_before_pytest_recovery_batch063b.json",
    "pytest_version_origin_bootstrap_plan.json",
    "pytest_version_origin_probe_results.json",
    "pytest_scm_metadata_probe_results.json",
    "pytest_git_tag_reachability_audit.json",
    "pytest_version_origin_classification.json",
    "pytest_version_origin_recovery_result.json",
    "pytest_runner_target_split_plan.json",
    "pytest_runner_target_import_origin_audit.json",
    "pytest_runner_target_collision_check.json",
    "pytest_self_test_harness_origin_bootstrap.json",
    "pytest_command_translation_layer_batch063b.json",
    "pytest_provider_runtime_capsule_plan_batch063b.json",
    "pytest_provider_install_attempt_batch063b.json",
    "pytest_provider_install_log_raw_batch063b.txt",
    "pytest_provider_runtime_setup_result_batch063b.json",
    "pytest_provider_recovery_non_repair_boundary_batch063b.json",
    "pytest_command_boundary_probe_plan_batch063b.json",
    "pytest_command_boundary_probe_results_batch063b.json",
    "pytest_command_boundary_log_raw_batch063b.txt",
    "pytest_collect_only_result_batch063b.json",
    "pytest_command_config_error_extract_batch063b.json",
    "pytest_command_boundary_classification_batch063b.json",
    "pytest_normalized_replay_authorization_batch063b.json",
    "pytest_prerepair_not_run_reason_batch063b.json",
    "pytest_prerepair_replay_plan_batch063b.json",
    "pytest_prerepair_replay_command_batch063b.txt",
    "pytest_prerepair_replay_log_raw_batch063b.txt",
    "pytest_prerepair_replay_result_batch063b.json",
    "pytest_prerepair_failure_signature_extract_batch063b.json",
    "pytest_prerepair_outcome_classification_batch063b.json",
    "pytest_diagnostic_not_run_reason_batch063b.json",
    "pytest_diagnostic_minimal_replay_plan_batch063b.json",
    "pytest_diagnostic_minimal_replay_results_batch063b.json",
    "pytest_diagnostic_failed_node_registry_batch063b.json",
    "pytest_diagnostic_traceback_roots_batch063b.json",
    "pytest_diagnostic_failure_signature_extract_batch063b.json",
    "pytest_amds_full_bug_tree_state_batch063b.json",
    "pytest_amds_node_registry_batch063b.json",
    "pytest_amds_next_action_frontier_batch063b.json",
    "pytest_patch_license_from_amds_batch063b.json",
    "pytest_source_contact_prior_or_replay_map_batch063b.json",
    "pytest_provider_dependency_replay_map_batch063b.json",
    "pytest_interpreter_behavior_replay_map_batch063b.json",
    "pytest_test_expectation_replay_map_batch063b.json",
    "workspace_purity_filter_pattern_update_batch063b.json",
    "command_translation_layer_pattern_update_batch063b.json",
    "candidate_isolated_venv_pattern_update_batch063b.json",
    "baseline_registry_snapshot_pattern_update_batch063b.json",
    "proof_ledger_forkpoint_pattern_update_batch063b.json",
    "confidence_abstention_audit_batch063b.json",
    "self_test_harness_origin_bootstrap_pattern_update_batch063b.json",
    "ast_topology_extrusion_future_requirement_batch063b.json",
    "cross_family_homology_ledger_future_requirement_batch063b.json",
    "apoptosis_safe_abstention_policy_update_batch063b.json",
    "non_circular_harness_origin_policy_update_batch063b.json",
    "batch063b_reactome_provider_capsule_utilization_update.json",
    "batch063b_tld_governance_utilization_update.json",
    "batch063b_isomorphic_logic_to_engineering_gap_closure_update.json",
    "batch063b_public_safe_engineering_translation_update.json",
    "batch063b_repo_hygiene_pressure_reassessment.json",
    "batch063b_duplicate_function_risk_reassessment.json",
    "batch063b_shared_utility_extraction_recommendation.json",
    "batch063b_public_readiness_recommendation.json",
    "project_health_review_batch063b.json",
    "capability_maturity_scorecard_batch063b.json",
    "version_progress_grade_batch063b.json",
    "strategic_direction_check_batch063b.json",
    "proof_milestone_distance_report_batch063b.json",
    "regression_and_drift_watch_batch063b.json",
    "self_maintenance_readiness_review_batch063b.json",
    "next_highest_impact_action_report_batch063b.json",
    "public_language_neutrality_check_batch063b.json",
    "public_summary_claim_safety_check_batch063b.json",
    "internal_vs_public_language_boundary_batch063b.json",
    "universal_wrapper_law_manifest_batch063b.json",
    "self_maintaining_wrapper_nonclaim_boundary_batch063b.json",
    "situational_fix_escape_hatch_blocker_policy_batch063b.json",
    "controllergate_state_transition_contract_batch063b.json",
    "reactome_style_step_contract_model_batch063b.json",
    "provider_capsule_step_contract_schema_batch063b.json",
    "candidate_execution_step_registry_batch063b.json",
    "step_to_output_contract_registry_batch063b.json",
    "deprecated_or_unbounded_step_exclusion_registry_batch063b.json",
    "provider_output_verifier_contract_batch063b.json",
    "reactome_to_controllergate_mapping_matrix_batch063b.json",
    "tld_governance_enforcement_matrix_batch063b.json",
    "tld_to_controllergate_rule_mapping_batch063b.json",
    "frozen_gate_and_lock_registry_batch063b.json",
    "bundle_bound_evidence_policy_batch063b.json",
    "outcome_blind_materialization_policy_batch063b.json",
    "full_failure_preservation_policy_batch063b.json",
    "contamination_prevention_policy_batch063b.json",
    "workspace_purity_policy_batch063b.json",
    "candidate_isolated_runtime_policy_batch063b.json",
    "stale_artifact_resistance_policy_batch063b.json",
    "candidate_workspace_purity_schema_batch063b.json",
    "candidate_isolated_venv_schema_batch063b.json",
    "global_environment_drift_prevention_policy_batch063b.json",
    "command_translation_layer_policy_batch063b.json",
    "candidate_command_manifest_schema_batch063b.json",
    "pytest_command_translation_case_study_batch063b.json",
    "command_boundary_terminal_state_registry_batch063b.json",
    "command_manifest_origin_audit_batch063b.json",
    "non_circular_harness_origin_policy_batch063b.json",
    "harness_origin_bootstrap_schema_batch063b.json",
    "harness_origin_root_of_trust_registry_batch063b.json",
    "harness_origin_self_reference_blocker_policy_batch063b.json",
    "harness_origin_pre_post_integrity_policy_batch063b.json",
    "ast_topology_extrusion_policy_batch063b.json",
    "ast_topology_extrusion_schema_batch063b.json",
    "source_syntax_resilience_policy_batch063b.json",
    "patch_gate_ast_integrity_requirement_batch063b.json",
    "pytest_readonly_ast_topology_probe_batch063b.json",
    "pytest_readonly_source_inventory_batch063b.json",
    "pytest_readonly_ast_parse_status_batch063b.json",
    "pytest_source_contact_topology_prior_batch063b.json",
    "cross_family_homology_ledger_batch063b.json",
    "repair_pattern_homology_schema_batch063b.json",
    "counted_repair_shape_library_batch063b.json",
    "homologous_failure_pattern_index_batch063b.json",
    "confidence_abstention_policy_batch063b.json",
    "safe_abstention_watchdog_schema_batch063b.json",
    "unrecoverable_branch_explanation_policy_batch063b.json",
    "loop_prevention_policy_batch063b.json",
    "universal_bug_terminal_state_registry_batch063b.json",
    "bug_terminal_state_contract_batch063b.json",
    "candidate_reopen_condition_registry_batch063b.json",
    "unrecoverable_under_current_policy_registry_batch063b.json",
    "baseline_registry_snapshot_policy_batch063b.json",
    "proof_ledger_forkpoint_policy_batch063b.json",
    "failed_attempt_branch_record_schema_batch063b.json",
    "rollback_marker_policy_batch063b.json",
    "ghost_state_prevention_policy_batch063b.json",
    "public_ready_repo_architecture_gap_batch063b.json",
    "duplicate_function_and_utility_review_batch063b.json",
    "shared_core_module_extraction_plan_batch063b.json",
    "public_docs_update_priority_batch063b.json",
    "repo_public_release_readiness_scorecard_batch063b.json",
    "batch063b_final_decision.json",
    "batch067_pytest_source_only_patch_gate_recommendation.json",
    "batch067_pytest_failure_family_decomposition_recommendation.json",
    "batch063c_pytest_command_boundary_manual_review_recommendation.json",
    "batch058d_seed_discovery_expansion_recommendation.json",
    "batch062b_repo_hygiene_utility_consolidation_planning_recommendation.json",
    "memory_lift_future_plan_recommendation.json",
    "batch063b_summary.md",
    "claim_boundary.json",
    "audit.json",
    "package_verification.json",
    "artifact_sha256_verification.json",
    "SHA256SUMS.txt",
]

REQUIRED_REPO_FILES = [
    "configs/workspace_purity_policy.json",
    "configs/candidate_isolated_runtime_policy.json",
    "configs/controllergate_self_maintenance_runtime_wrapper_backlog.json",
    "configs/controllergate_permanent_fix_queue.json",
    "configs/controllergate_historical_requirements_recovery_lock.json",
    "configs/controllergate_required_wrapper_law_registry.json",
    "docs/controllergate_self_maintenance_runtime_wrapper_roadmap.md",
    "docs/controllergate_public_readiness_plan.md",
    "docs/controllergate_historical_requirements_recovery_lock.md",
]

HR_REQUIRED_FILES = [
    "historical_requirement_recovery_registry_batch063b.json",
    "historical_requirement_gap_matrix_batch063b.json",
    "historical_requirement_status_dashboard_batch063b.json",
    "forgotten_requirement_prevention_policy_batch063b.json",
    "false_win_prevention_policy_batch063b.json",
    "builder_output_provisional_policy_batch063b.json",
    "critic_verification_gate_schema_batch063b.json",
    "decision_report_rerun_sha_agreement_policy_batch063b.json",
    "historical_false_win_ledger_update_batch063b.json",
    "deterministic_replay_readiness_policy_batch063b.json",
    "real_repo_evidence_strengthening_gate_batch063b.json",
    "memory_baseline_availability_gate_batch063b.json",
    "full_scoring_precondition_policy_batch063b.json",
    "real_repo_review_required_terminal_policy_batch063b.json",
    "external_episode_evidence_bundle_policy_batch063b.json",
    "external_episode_pending_bundle_schema_batch063b.json",
    "no_premature_normalization_policy_batch063b.json",
    "decision_time_outcome_evidence_separation_policy_batch063b.json",
    "null_wrapper_policy_batch063b.json",
    "matched_baseline_control_schema_batch063b.json",
    "null_separation_score_policy_batch063b.json",
    "memory_lift_prerequisite_policy_batch063b.json",
    "stateless_baseline_runner_contract_batch063b.json",
    "strict_label_blindness_policy_batch063b.json",
    "ground_truth_peeking_blocker_policy_batch063b.json",
    "fault_class_leakage_audit_schema_batch063b.json",
    "triad_interlock_operational_boundary_batch063b.json",
    "controllergate_5_14_6_196_errata_lock_batch063b.json",
    "corrected_operational_stack_policy_batch063b.json",
    "activation_after_topology_policy_batch063b.json",
    "repair_activation_not_preflight_only_policy_batch063b.json",
    "isomorphic_stack_public_boundary_batch063b.json",
    "secondary_cofactor_lock_policy_batch063b.json",
    "reviewed_provider_lock_schema_batch063b.json",
    "dependency_drift_audit_policy_batch063b.json",
    "declared_unpinned_cofactor_blocker_policy_batch063b.json",
    "cofactor_materialization_nonrepair_boundary_batch063b.json",
    "workflow_snapshot_identity_policy_batch063b.json",
    "runner_revision_guard_policy_batch063b.json",
    "stale_workflow_rerun_blocker_policy_batch063b.json",
    "workflow_head_sha_verification_schema_batch063b.json",
    "command_normalization_guard_policy_batch063b.json",
    "harness_sanity_policy_batch063b.json",
    "command_normalization_policy_global_batch063b.json",
    "project_root_execution_policy_batch063b.json",
    "runner_dependency_preflight_policy_batch063b.json",
    "returncode_127_harness_failure_policy_batch063b.json",
    "historical_harness_origin_blocker_recovery_batch063b.json",
    "target_test_provenance_policy_batch063b.json",
    "self_referential_harness_hash_blocker_batch063b.json",
    "brot_bulb_environment_locator_policy_batch063b.json",
    "environment_topology_locator_schema_batch063b.json",
    "provider_surface_vs_source_surface_classifier_batch063b.json",
    "single_system_vs_coupled_system_boundary_batch063b.json",
    "tot_brot_coupled_candidate_policy_batch063b.json",
    "historical_ast_loop_extrusion_requirement_batch063b.json",
    "ast_topology_patch_gate_precondition_batch063b.json",
    "source_contact_not_tests_only_policy_batch063b.json",
    "native_contact_topology_schema_batch063b.json",
    "branch_closure_without_count_increment_policy_batch063b.json",
    "safe_abstention_policy_historical_lock_batch063b.json",
    "flatline_rejection_policy_batch063b.json",
    "minimum_deltas_constraint_policy_batch063b.json",
    "historical_requirement_recovery_final_status_batch063b.json",
    "batch063b_pytest_next_action_and_wrapper_law_decision.json",
]


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def expect(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def run_python_script(rel: str, errors: list[str]) -> None:
    proc = subprocess.run([sys.executable, rel], cwd=ROOT, text=True, capture_output=True, check=False)
    if proc.returncode != 0:
        errors.append(f"{rel} failed: {proc.stdout[-1000:]} {proc.stderr[-1000:]}")


def git_lines(*args: str) -> list[str]:
    proc = subprocess.run(["git", *args], cwd=ROOT, text=True, capture_output=True, check=False)
    return proc.stdout.splitlines()


def audit_git_status(errors: list[str]) -> None:
    for line in git_lines("status", "--short"):
        normalized = line[3:].replace("\\", "/") if len(line) > 3 else line.replace("\\", "/")
        if line.startswith("?? incoming_artifacts/"):
            continue
        for fragment in FORBIDDEN_STATUS_FRAGMENTS:
            if fragment in normalized:
                errors.append(f"forbidden path appears in git status: {line}")
                break


def public_batch063b_block(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    marker = "Batch063b is the latest Pytest command-boundary and wrapper-hardening boundary."
    start = text.find(marker)
    if start == -1:
        return ""
    next_marker = text.find("\n## ", start)
    if next_marker == -1:
        next_marker = min(len(text), start + 6000)
    return text[start:next_marker]


def audit_public_summary(errors: list[str]) -> None:
    for rel in [
        "README.md",
        "docs/current_status.md",
        "controllergate_v1_7_beta/reports/critic_review_package/shareable_summary.md",
    ]:
        block = public_batch063b_block(ROOT / rel)
        expect(errors, bool(block), f"missing Batch063b public summary block in {rel}")
        for phrase in [
            "Workflow success is not equivalent to repair success.",
            "Version-origin recovery is not repair success.",
            "Command-boundary normalization is not repair success.",
            "Provider/runtime setup is not repair success.",
            "Pre-repair replay is not repair success.",
            "ControllerGate is being hardened as a high-integrity maintenance wrapper, but self-maintaining software remains false/not_demonstrated.",
            "These wrapper-hardening artifacts are engineering controls, not repair proof.",
            "No source repair is counted without source-only target pass, duplicate clean replay, and count gate.",
            "A repair is counted only after source-only target pass, duplicate clean replay, and count gate.",
            "The project health grade is advisory and does not constitute proof.",
            "Self-maintaining software remains false/not_demonstrated.",
            "Historical requirements recovery status:",
            "False-win verification gate status:",
            "Deterministic replay readiness gate status:",
            "Matched baseline/null-wrapper status:",
            "Provider/cofactor lock status:",
            "Command normalization / workflow snapshot guard status:",
            "Terminal-state/reopen-condition policy status:",
        ]:
            expect(errors, phrase in block, f"Batch063b public summary missing {phrase!r} in {rel}")
        lowered = block.lower()
        for term in PUBLIC_FORBIDDEN_TERMS:
            expect(errors, term.lower() not in lowered, f"Batch063b public summary contains internal term {term!r} in {rel}")


def main() -> int:
    errors: list[str] = []
    if not OUT_DIR.is_dir():
        print(f"FAIL: missing output directory: {OUT_DIR.relative_to(ROOT)}")
        return 1
    for rel in REQUIRED_FILES:
        expect(errors, (OUT_DIR / rel).is_file(), f"missing required Batch063b output: {rel}")
    for rel in HR_REQUIRED_FILES:
        expect(errors, (OUT_DIR / rel).is_file(), f"missing required Batch063b historical-recovery output: {rel}")
    for rel in REQUIRED_REPO_FILES:
        expect(errors, (ROOT / rel).is_file(), f"missing required Batch063b repo file: {rel}")
    if errors:
        print("FAIL:")
        for error in errors:
            print(f"- {error}")
        return 1

    manifest = verify_manifest(OUT_DIR)
    expect(errors, manifest.get("status") == "PASS", f"Batch063b SHA256SUMS verification failed: {manifest}")

    artifact = read_json(OUT_DIR / "batch066_artifact_sha256_verification.json")
    preservation = read_json(OUT_DIR / "batch066_result_preservation.json")
    scope = read_json(OUT_DIR / "batch063b_candidate_scope.json")
    forbidden = read_json(OUT_DIR / "batch063b_forbidden_evidence_audit.json")
    workspace = read_json(OUT_DIR / "pytest_workspace_custody_check_batch063b.json")
    purity = read_json(OUT_DIR / "pytest_workspace_purity_manifest_batch063b.json")
    commit = read_json(OUT_DIR / "pytest_commit_verification_batch063b.json")
    version = read_json(OUT_DIR / "pytest_version_origin_classification.json")
    runner = read_json(OUT_DIR / "pytest_runner_target_import_origin_audit.json")
    provider = read_json(OUT_DIR / "pytest_provider_runtime_setup_result_batch063b.json")
    command = read_json(OUT_DIR / "pytest_command_boundary_classification_batch063b.json")
    auth = read_json(OUT_DIR / "pytest_normalized_replay_authorization_batch063b.json")
    prerepair = read_json(OUT_DIR / "pytest_prerepair_outcome_classification_batch063b.json")
    diagnostic = read_json(OUT_DIR / "pytest_diagnostic_not_run_reason_batch063b.json")
    license_ = read_json(OUT_DIR / "pytest_patch_license_from_amds_batch063b.json")
    wrapper = read_json(OUT_DIR / "universal_wrapper_law_manifest_batch063b.json")
    homology = read_json(OUT_DIR / "cross_family_homology_ledger_batch063b.json")
    ast_policy = read_json(OUT_DIR / "ast_topology_extrusion_policy_batch063b.json")
    abstention = read_json(OUT_DIR / "confidence_abstention_policy_batch063b.json")
    repo_gap = read_json(OUT_DIR / "public_ready_repo_architecture_gap_batch063b.json")
    hr_registry = read_json(OUT_DIR / "historical_requirement_recovery_registry_batch063b.json")
    hr_dashboard = read_json(OUT_DIR / "historical_requirement_status_dashboard_batch063b.json")
    hr_final = read_json(OUT_DIR / "historical_requirement_recovery_final_status_batch063b.json")
    hr_decision = read_json(OUT_DIR / "batch063b_pytest_next_action_and_wrapper_law_decision.json")
    false_win = read_json(OUT_DIR / "false_win_prevention_policy_batch063b.json")
    deterministic = read_json(OUT_DIR / "deterministic_replay_readiness_policy_batch063b.json")
    null_wrapper = read_json(OUT_DIR / "null_wrapper_policy_batch063b.json")
    cofactor = read_json(OUT_DIR / "secondary_cofactor_lock_policy_batch063b.json")
    workflow_guard = read_json(OUT_DIR / "workflow_snapshot_identity_policy_batch063b.json")
    harness_sanity = read_json(OUT_DIR / "harness_sanity_policy_batch063b.json")
    env_locator = read_json(OUT_DIR / "brot_bulb_environment_locator_policy_batch063b.json")
    historical_ast = read_json(OUT_DIR / "ast_topology_patch_gate_precondition_batch063b.json")
    safe_abstention_lock = read_json(OUT_DIR / "safe_abstention_policy_historical_lock_batch063b.json")
    final = read_json(OUT_DIR / "batch063b_final_decision.json")
    claim = read_json(OUT_DIR / "claim_boundary.json")
    package = read_json(OUT_DIR / "package_verification.json")

    expect(errors, artifact.get("status") == "PASS", "Batch066 artifact verification did not pass")
    expect(errors, artifact.get("zip_sha256") == "e0352bd1487e200fae0afa5278a4e1fd31ff8bf6aea0b0988f6bb020a5d4debe", "Batch066 artifact SHA mismatch")
    expect(errors, artifact.get("zip_size_bytes") == 55101, "Batch066 artifact size mismatch")
    expect(errors, artifact.get("zip_entry_count") == 91, "Batch066 artifact entry count mismatch")
    expect(errors, artifact.get("artifact_manifest", {}).get("status") == "PASS", "Batch066 artifact manifest failed")
    expect(errors, artifact.get("output_manifest", {}).get("status") == "PASS", "Batch066 output manifest failed")
    expect(errors, preservation.get("issue_derived_repair_count") == 4, "Issue-derived repair count 4 not preserved")
    expect(errors, preservation.get("native_external_repair_count") == 4, "Native external repair count changed")
    expect(errors, preservation.get("full_scoring") == "NOT_RUN/disallowed", "Full scoring changed")
    expect(errors, preservation.get("memory_lift") == "not_demonstrated", "Memory lift changed")
    expect(errors, preservation.get("self_maintaining_software") == "false/not_demonstrated", "Self-maintaining status changed")
    expect(errors, scope.get("only_candidate") == "pytest_13895_pytest9_skiptest_behavior", "Batch063b did not scope to Pytest only")
    for key in ["fixed_commit_used", "future_commit_used", "pr_patch_used", "gold_patch_used", "issue_body_fix_text_used", "hidden_labels_used", "synthetic_tests_used"]:
        expect(errors, forbidden.get(key) is False, f"Forbidden evidence expected {key}=false")
    expect(errors, workspace.get("status") == "PASS" and workspace.get("testing_exists") is True and workspace.get("pyproject_exists") is True, "Pytest workspace custody failed")
    expect(errors, purity.get("status") == "PASS" and purity.get("stale_cache_contamination_count") == 0, "Workspace purity failed before replay")
    expect(errors, commit.get("status") == "PASS" and commit.get("resolved_head") == "041aacad506b6c6891f2898f2bd378e0896e8b86", "Pytest commit verification failed")
    expect(errors, version.get("classification") in {"pytest_version_origin_ok", "pytest_version_origin_missing_tags", "pytest_version_origin_shallow_clone_underresolved", "pytest_version_origin_editable_install_underresolved", "pytest_version_origin_import_shadowing", "pytest_version_origin_runner_target_collision", "pytest_version_origin_unrecoverable_without_forbidden_evidence", "pytest_version_origin_manual_review_needed"}, "Invalid version-origin classification")
    expect(errors, runner.get("external_runner_used") is False or runner.get("target_import_origin_proven_for_external_runner") is True, "External runner trusted without target import proof")
    expect(errors, provider.get("declared_metadata_only") is True, "Provider setup was not declared-metadata only")
    expect(errors, provider.get("provider_runtime_setup_is_repair_success") is False, "Provider setup overclaimed repair success")
    expect(errors, command.get("classification") in {"pytest_command_boundary_normalized", "pytest_command_boundary_partially_normalized", "pytest_command_boundary_invalid_preserved_command", "pytest_command_boundary_requires_declared_tox_nox", "pytest_command_boundary_blocked_unavailable_runner", "pytest_command_boundary_blocked_config_minversion", "pytest_command_boundary_blocked_version_origin", "pytest_command_boundary_blocked_runner_target_collision", "pytest_command_boundary_unbounded", "pytest_command_boundary_manual_review_needed"}, "Invalid command-boundary classification")
    if command.get("classification") not in {"pytest_command_boundary_normalized", "pytest_command_boundary_partially_normalized"}:
        expect(errors, auth.get("pre_repair_replay_authorized") is False, "Pre-repair replay authorized despite blocked command boundary")
        expect(errors, prerepair.get("status") == "NOT_RUN", "Pre-repair replay should not run while boundary blocked")
        expect(errors, diagnostic.get("status") == "NOT_RUN", "Diagnostics should not run without pre-repair materialization")
        expect(errors, license_.get("patch_generation_allowed_in_batch063b") is False, "Patch generation allowed in Batch063b")
    expect(errors, wrapper.get("self_maintaining_software") == "false/not_demonstrated", "Wrapper law overclaimed self-maintenance")
    expect(errors, homology.get("routing_memory_only") is True and homology.get("not_proof") is True, "Homology ledger overclaimed proof")
    expect(errors, ast_policy.get("future_patch_gate_law") is True and ast_policy.get("current_pytest_patch_permission") is False, "AST topology policy gave current patch permission")
    expect(errors, abstention.get("status") == "PASS", "Safe-abstention policy missing")
    expect(errors, repo_gap.get("no_refactor_performed") is True, "Repo hygiene review refactored code")
    allowed_hr_statuses = set(hr_registry.get("allowed_statuses", []))
    requirements = hr_registry.get("requirements", [])
    expect(errors, hr_registry.get("status") == "PASS", "Historical requirement registry did not pass")
    expect(errors, hr_registry.get("no_narrative_only_requirements") is True, "Historical requirements may be narrative-only")
    expect(errors, len(requirements) >= 15, "Historical requirement registry is missing recovered requirements")
    for record in requirements:
        req_id = record.get("requirement_id", "<missing>")
        status = record.get("status")
        expect(errors, bool(status) and status in allowed_hr_statuses, f"{req_id} missing valid status")
        expect(errors, bool(record.get("owner_files_or_modules")), f"{req_id} missing owner files/modules")
        expect(errors, bool(record.get("required_artifacts")), f"{req_id} missing owner artifacts")
        expect(errors, bool(record.get("required_audit_assertions")), f"{req_id} missing audit assertions")
        expect(errors, bool(record.get("next_allowed_action_if_blocking")), f"{req_id} missing next action")
        expect(errors, record.get("proof_lane_effect") in {"none", "governance_only", "provider_boundary", "patch_gate_precondition", "count_gate_precondition", "scoring_precondition", "memory_lift_precondition"}, f"{req_id} has invalid proof lane effect")
        if status in {"scaffolded_with_config_and_audit", "requires_dedicated_future_batch_with_named_batch"}:
            expect(errors, bool(record.get("named_future_batch")), f"{req_id} deferred without named future batch")
            expect(errors, bool(record.get("why_not_now")), f"{req_id} deferred without why_not_now")
            expect(errors, bool(record.get("blocker_if_ignored")), f"{req_id} deferred without blocker_if_ignored")
            expect(errors, bool(record.get("minimum_audit_required_in_current_batch")), f"{req_id} deferred without minimum audit")
    expect(errors, hr_dashboard.get("requirement_count") == len(requirements), "Historical requirement dashboard count mismatch")
    expect(errors, hr_final.get("historical_requirement_recovery_status") == "PASS", "Historical recovery final status did not pass")
    expect(errors, hr_decision.get("selected_next_allowed_action") == "batch067_universal_wrapper_hardening_implementation", "Historical wrapper-law decision did not select wrapper hardening")
    expect(errors, false_win.get("builder_output_is_provisional") is True, "False-win policy missing provisional builder rule")
    expect(errors, bool(deterministic.get("minimum_record_fields")), "Deterministic replay readiness schema missing")
    expect(errors, null_wrapper.get("null_wrapper_status") == "null_wrapper_scaffolded", "Null wrapper scaffold status missing")
    expect(errors, "declared_unpinned_provider_blocked" in cofactor.get("statuses", []), "Provider/cofactor lock statuses missing")
    expect(errors, bool(workflow_guard.get("future_checks")), "Workflow snapshot guard missing future checks")
    expect(errors, harness_sanity.get("returncode_127_is_harness_failure_until_normalized") is True, "Harness sanity returncode 127 rule missing")
    expect(errors, env_locator.get("internal_engineering_language_only") is True, "Environment locator must be internal engineering language only")
    expect(errors, historical_ast.get("blocker") == "patch_license_closed_source_topology_incomplete", "AST topology precondition blocker missing")
    expect(errors, bool(safe_abstention_lock.get("triggers")), "Historical safe-abstention triggers missing")
    expect(errors, final.get("status") == "PASS", "Final decision did not pass")
    expect(errors, final.get("current_protocol") == CURRENT_PROTOCOL, "Current protocol changed")
    expect(errors, final.get("issue_derived_repair_count") == 4, "Final issue-derived repair count not preserved at 4")
    expect(errors, final.get("native_external_repair_count") == 4, "Final native external repair count changed")
    for key in ["patch_generated", "patch_applied", "source_mutated", "tests_mutated", "fixtures_mutated", "dependency_or_build_files_mutated_as_repair", "duplicate_replay_run", "count_gate_run", "repair_count_increment", "full_scoring_run", "memory_lift_analysis_run"]:
        expect(errors, final.get(key) is False, f"Batch063b boundary expected {key}=false")
    expect(errors, final.get("full_scoring") == "NOT_RUN/disallowed", "Full scoring changed")
    expect(errors, final.get("memory_lift") == "not_demonstrated", "Memory lift changed")
    expect(errors, final.get("self_maintaining_software") == "false/not_demonstrated", "Self-maintaining status changed")
    expect(errors, final.get("next_allowed_action") in {"batch067_pytest_source_only_patch_gate", "batch067_pytest_failure_family_decomposition", "batch063c_pytest_command_boundary_followup", "batch062b_repo_hygiene_utility_consolidation_planning", "batch058d_seed_discovery_expansion", "batch067_universal_wrapper_hardening_implementation"}, "Invalid next allowed action")
    expect(errors, final.get("next_allowed_action") == "batch067_universal_wrapper_hardening_implementation", "Batch063b should route to universal wrapper hardening after historical recovery")
    expect(errors, final.get("historical_requirement_recovery_status") == "PASS", "Final decision missing historical recovery status")
    expect(errors, final.get("recovered_requirement_count") == len(requirements), "Final decision historical requirement count mismatch")
    expect(errors, claim.get("repair_count_increment") is False and claim.get("full_scoring") == "NOT_RUN/disallowed", "Claim boundary overreached")
    for key in ["raw_zip_payload_committed", "runtime_workspaces_committed", "source_checkouts_committed", "venvs_committed", "caches_committed"]:
        expect(errors, package.get(key) is False, f"Package verification expected {key}=false")

    audit_public_summary(errors)
    audit_git_status(errors)
    run_python_script("scripts/audit_batch066_next_issue_repair_candidate_selection_or_pytest_recovery.py", errors)
    proc = subprocess.run([sys.executable, "scripts/controllergate_audit.py", "--protocol", "current"], cwd=ROOT, text=True, capture_output=True, check=False)
    expect(errors, proc.returncode == 0, f"current protocol audit failed: {proc.stdout[-1000:]} {proc.stderr[-1000:]}")
    proc = subprocess.run([sys.executable, "scripts/controllergate_run.py", "--protocol", "current", "--dry-run"], cwd=ROOT, text=True, capture_output=True, check=False)
    expect(errors, proc.returncode == 0, f"current protocol dry-run failed: {proc.stdout[-1000:]} {proc.stderr[-1000:]}")

    if errors:
        print("FAIL:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Batch063b Pytest provider runtime recovery followup audit PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
