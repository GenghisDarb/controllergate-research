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


OUT_DIR = ROOT / "outputs" / "post_v2_37_hardening_batch060d_cloudpickle_class_dict_patch_gate_with_amds_health_review"
CURRENT_PROTOCOL = "v2.14"
EXPECTED_BATCH060C_SHA256 = "f2cbb7ed34e72a798e2887f3bb462082fefe7ff3f582dfaf2b92beb6be16e219"
EXPECTED_BATCH060C_SIZE = 69497
EXPECTED_BATCH060C_ENTRY_COUNT = 85
EXPECTED_BATCH060C_ARTIFACT_MANIFEST_CHECKED = 84
EXPECTED_BATCH060C_OUTPUT_MANIFEST_CHECKED = 83

REQUIRED_FILES = [
    "batch060c_artifact_ingestion_summary.json",
    "batch060c_artifact_sha256_verification.json",
    "batch060c_result_preservation.json",
    "batch060c_cloudpickle_provider_runtime_preservation.json",
    "batch060c_pattern_library_preservation.json",
    "batch060c_patch_debt_repo_topology_preservation.json",
    "batch060c_audioread_branch_preservation.json",
    "batch060c_claim_boundary_preservation.json",
    "batch060c_next_action_boundary.json",
    "cloudpickle_decision_time_input_manifest.json",
    "cloudpickle_forbidden_evidence_audit.json",
    "cloudpickle_issue_body_leakage_boundary.json",
    "cloudpickle_label_blindness_check.json",
    "cloudpickle_gold_patch_exclusion_check.json",
    "cloudpickle_future_evidence_exclusion_check.json",
    "cloudpickle_candidate_patch_gate_plan.json",
    "cloudpickle_commit_verification.json",
    "cloudpickle_workspace_manifest.json",
    "cloudpickle_provider_runtime_preservation.json",
    "cloudpickle_dependency_plan.json",
    "cloudpickle_command_context.json",
    "cloudpickle_command_normalization.json",
    "cloudpickle_provider_precondition_check.json",
    "cloudpickle_workspace_custody_check.json",
    "cloudpickle_class_dict_source_discovery_plan.json",
    "cloudpickle_class_dict_source_discovery_result.json",
    "cloudpickle_source_file_inventory.json",
    "cloudpickle_suspect_source_files.json",
    "cloudpickle_class_dict_failure_to_source_trace.json",
    "cloudpickle_decision_time_source_manifest.json",
    "cloudpickle_source_surface_localization_check.json",
    "cloudpickle_ast_loop_extrusion_bridge.json",
    "cloudpickle_source_contact_graph_extrusion_result.json",
    "cloudpickle_probe_to_patch_transition_gate.json",
    "cloudpickle_patch_license_from_amds.json",
    "cloudpickle_class_dict_source_only_patch_candidate.diff",
    "cloudpickle_class_dict_source_only_patch_candidate.json",
    "cloudpickle_class_dict_patch_generation_trace.json",
    "cloudpickle_class_dict_patch_safety_check.json",
    "cloudpickle_class_dict_patch_application_result.json",
    "cloudpickle_class_dict_changed_files_manifest.json",
    "cloudpickle_class_dict_test_mutation_check.json",
    "cloudpickle_class_dict_source_only_check.json",
    "cloudpickle_pre_repair_distutils_family_log_raw.txt",
    "cloudpickle_pre_repair_distutils_family_protocol2_log_raw.txt",
    "cloudpickle_pre_repair_class_dict_log_raw.txt",
    "cloudpickle_pre_repair_full_target_log_raw.txt",
    "cloudpickle_post_repair_class_dict_log_raw.txt",
    "cloudpickle_post_repair_distutils_family_log_raw.txt",
    "cloudpickle_post_repair_distutils_family_protocol2_log_raw.txt",
    "cloudpickle_post_repair_full_target_log_raw.txt",
    "cloudpickle_post_repair_results.json",
    "cloudpickle_post_repair_failure_signature_extract.json",
    "cloudpickle_repair_outcome_classification.json",
    "amds_full_bug_tree_closure_plan.json",
    "amds_full_bug_tree_state.json",
    "amds_bug_tree_node_registry.json",
    "amds_bug_tree_edge_registry.json",
    "amds_recursive_probe_trace.json",
    "amds_layer_expansion_log.json",
    "amds_secondary_bug_registry.json",
    "amds_tertiary_bug_registry.json",
    "amds_quaternary_and_deeper_bug_registry.json",
    "amds_provider_dependency_branch_registry.json",
    "amds_interpreter_behavior_branch_registry.json",
    "amds_test_expectation_branch_registry.json",
    "amds_unrecoverable_branch_registry.json",
    "amds_repairable_branch_registry.json",
    "amds_next_action_frontier.json",
    "amds_recursive_probe_budget.json",
    "amds_full_bug_tree_closure_summary.md",
    "project_health_review_batch060d.json",
    "project_health_review_batch060d.md",
    "project_health_review_batch060c.json",
    "project_health_review_batch060c.md",
    "capability_maturity_scorecard.json",
    "capability_maturity_scorecard.md",
    "version_progress_grade.json",
    "strategic_direction_check.json",
    "proof_milestone_distance_report.json",
    "regression_and_drift_watch.json",
    "recurring_bottleneck_trend_report.json",
    "self_maintenance_readiness_review.json",
    "next_highest_impact_action_report.json",
    "batch060d_whole_problem_map.json",
    "tld_structural_boundary_report_batch060d.json",
    "reactome_provider_capsule_carryforward_batch060d.json",
    "isomorphic_logic_correctness_check_batch060d.json",
    "metaphor_to_artifact_boundary_batch060d.json",
    "batch061_duplicate_replay_candidates.json",
    "batch061_count_gate_recommendation.json",
    "batch060e_followup_recommendation.json",
    "batch060f_audioread_provider_backend_capsule_replay_recommendation.json",
    "batch058b_seed_discovery_wave_3_expansion_recommendation.json",
    "batch060d_summary.md",
    "batch060d_final_decision.json",
    "claim_boundary.json",
    "audit.json",
    "package_verification.json",
    "artifact_sha256_verification.json",
    "SHA256SUMS.txt",
]

REQUIRED_DOCS_CONFIGS = [
    "configs/amds_full_bug_tree_closure_policy.json",
    "docs/controllergate_amds_full_bug_tree_closure.md",
]

FORBIDDEN_STATUS_FRAGMENTS = [
    ".zip",
    ".tar",
    ".tgz",
    ".7z",
    ".pyc",
    "__pycache__",
    "ControllerGate_runtime",
    "artifact_payload",
    ".venv",
    "/venv/",
    "\\venv\\",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
]


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def expect(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def expect_false(errors: list[str], obj: dict[str, Any], key: str, label: str) -> None:
    if obj.get(key) is not False:
        errors.append(f"{label} expected {key}=false, observed {obj.get(key)!r}")


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


def main() -> int:
    errors: list[str] = []
    if not OUT_DIR.is_dir():
        print(f"FAIL: missing output directory: {OUT_DIR.relative_to(ROOT)}")
        return 1
    for rel in REQUIRED_FILES:
        if not (OUT_DIR / rel).is_file():
            errors.append(f"missing required Batch060d output: {rel}")
    for rel in REQUIRED_DOCS_CONFIGS:
        if not (ROOT / rel).is_file():
            errors.append(f"missing required docs/config: {rel}")
    if not errors:
        manifest = verify_manifest(OUT_DIR)
        if manifest.get("status") != "PASS":
            errors.append(f"Batch060d SHA256SUMS verification failed: {manifest}")
    if errors:
        print("FAIL:")
        for error in errors:
            print(f"- {error}")
        return 1

    artifact = read_json(OUT_DIR / "batch060c_artifact_sha256_verification.json")
    ingest = read_json(OUT_DIR / "batch060c_artifact_ingestion_summary.json")
    preserved = read_json(OUT_DIR / "batch060c_result_preservation.json")
    claim060c = read_json(OUT_DIR / "batch060c_claim_boundary_preservation.json")
    next060c = read_json(OUT_DIR / "batch060c_next_action_boundary.json")
    forbidden = read_json(OUT_DIR / "cloudpickle_forbidden_evidence_audit.json")
    precondition = read_json(OUT_DIR / "cloudpickle_provider_precondition_check.json")
    source_discovery = read_json(OUT_DIR / "cloudpickle_class_dict_source_discovery_result.json")
    license_record = read_json(OUT_DIR / "cloudpickle_patch_license_from_amds.json")
    patch = read_json(OUT_DIR / "cloudpickle_class_dict_source_only_patch_candidate.json")
    patch_safety = read_json(OUT_DIR / "cloudpickle_class_dict_patch_safety_check.json")
    patch_apply = read_json(OUT_DIR / "cloudpickle_class_dict_patch_application_result.json")
    changed = read_json(OUT_DIR / "cloudpickle_class_dict_changed_files_manifest.json")
    test_mutation = read_json(OUT_DIR / "cloudpickle_class_dict_test_mutation_check.json")
    source_only = read_json(OUT_DIR / "cloudpickle_class_dict_source_only_check.json")
    post = read_json(OUT_DIR / "cloudpickle_post_repair_results.json")
    outcome = read_json(OUT_DIR / "cloudpickle_repair_outcome_classification.json")
    amds_state = read_json(OUT_DIR / "amds_full_bug_tree_state.json")
    amds_nodes = read_json(OUT_DIR / "amds_bug_tree_node_registry.json")
    amds_budget = read_json(OUT_DIR / "amds_recursive_probe_budget.json")
    health = read_json(OUT_DIR / "project_health_review_batch060d.json")
    scorecard = read_json(OUT_DIR / "capability_maturity_scorecard.json")
    version_grade = read_json(OUT_DIR / "version_progress_grade.json")
    readiness = read_json(OUT_DIR / "self_maintenance_readiness_review.json")
    next_action = read_json(OUT_DIR / "next_highest_impact_action_report.json")
    tld = read_json(OUT_DIR / "tld_structural_boundary_report_batch060d.json")
    reactome = read_json(OUT_DIR / "reactome_provider_capsule_carryforward_batch060d.json")
    metaphor = read_json(OUT_DIR / "metaphor_to_artifact_boundary_batch060d.json")
    batch061 = read_json(OUT_DIR / "batch061_duplicate_replay_candidates.json")
    count_reco = read_json(OUT_DIR / "batch061_count_gate_recommendation.json")
    final = read_json(OUT_DIR / "batch060d_final_decision.json")
    claim = read_json(OUT_DIR / "claim_boundary.json")
    package = read_json(OUT_DIR / "package_verification.json")

    expect(errors, artifact.get("status") == "PASS", "Batch060c artifact verification did not pass")
    expect(errors, artifact.get("zip_sha256") == EXPECTED_BATCH060C_SHA256, "Batch060c artifact SHA mismatch")
    expect(errors, artifact.get("zip_size_bytes") == EXPECTED_BATCH060C_SIZE, "Batch060c artifact size mismatch")
    expect(errors, artifact.get("zip_entry_count") == EXPECTED_BATCH060C_ENTRY_COUNT, "Batch060c artifact entry count mismatch")
    expect(errors, artifact.get("artifact_manifest", {}).get("checked") == EXPECTED_BATCH060C_ARTIFACT_MANIFEST_CHECKED, "Batch060c artifact manifest count mismatch")
    output_manifest = artifact.get("output_manifests", {}).get("post_v2_37_hardening_batch060c_cloudpickle_provider_runtime_recovery", {})
    expect(errors, output_manifest.get("checked") == EXPECTED_BATCH060C_OUTPUT_MANIFEST_CHECKED, "Batch060c output manifest count mismatch")
    expect(errors, output_manifest.get("failures") == 0 and output_manifest.get("missing") == [], "Batch060c output manifest failed")
    for key in ["unsafe_path_count", "duplicate_path_count", "zip_pycache_entries", "zip_pyc_entries"]:
        expect(errors, artifact.get(key) == 0, f"Batch060c artifact has non-zero {key}")
    expect(errors, ingest.get("status") == "PASS" and ingest.get("official_output_ingest", {}).get("status") == "PASS", "Batch060c official ingest did not pass")
    expect(errors, preserved.get("issue_derived_repair_count") == 2, "Issue-derived repair count changed")
    expect(errors, preserved.get("native_external_repair_count") == 4, "Native external repair count changed")
    expect(errors, preserved.get("full_scoring") == "NOT_RUN/disallowed", "Full scoring status changed")
    expect(errors, preserved.get("memory_lift") == "not_demonstrated", "Memory lift status changed")
    expect(errors, preserved.get("self_maintaining_software") == "false/not_demonstrated", "Self-maintaining status changed")
    expect(errors, claim060c.get("status") == "PASS", "Batch060c no-patch/no-count boundary not preserved")
    expect(errors, next060c.get("observed_next_allowed_action") == "batch060d_cloudpickle_class_dict_source_only_patch_gate", "Batch060c next action not preserved")

    for key in [
        "fixed_commit_used",
        "future_commit_used",
        "pr_patch_used",
        "gold_patch_used",
        "issue_body_fix_text_used",
        "external_repair_summary_used",
        "modern_fixed_cloudpickle_source_used",
        "test_mutation",
        "synthetic_tests_added",
    ]:
        expect_false(errors, forbidden, key, "Cloudpickle forbidden evidence audit")
    expect(errors, precondition.get("distutils_nodes_passed_before_patch") is True, "Distutils provider preservation did not pass before patch")
    expect(errors, precondition.get("class_dict_failure_reproduced_before_patch") is True, "Class-dict failure did not reproduce before patch")
    expect(errors, precondition.get("original_target_failed_before_patch") is True, "Original target did not fail before patch")
    expect(errors, precondition.get("patch_authorized") is True, "Patch was not authorized by preconditions")
    expect(errors, source_discovery.get("source_owner") == "cloudpickle/cloudpickle.py::_extract_class_dict", "Source owner mismatch")
    expect(errors, license_record.get("patch_license_state") == "cloudpickle_patch_license_open_single_source_family", "Patch license not open for single source family")
    expect(errors, patch.get("patch_generated") is True, "Patch was not generated")
    expect(errors, patch_safety.get("patch_non_empty") is True, "Patch is empty")
    expect(errors, patch_safety.get("source_only") is True, "Patch is not source-only")
    expect(errors, patch_safety.get("tests_modified") is False, "Patch modified tests")
    expect(errors, patch_safety.get("fixtures_modified") is False, "Patch modified fixtures")
    expect(errors, patch_safety.get("dependency_build_files_modified") is False, "Patch modified dependency/build files")
    expect(errors, patch_apply.get("applied_in_isolated_workspace_only") is True, "Patch was not limited to isolated workspace")
    expect(errors, changed.get("changed_files") == ["cloudpickle/cloudpickle.py"], "Changed files are not limited to cloudpickle.py")
    expect(errors, test_mutation.get("tests_modified") is False and test_mutation.get("fixtures_modified") is False, "Test/fixture mutation detected")
    expect(errors, source_only.get("source_only") is True, "Source-only check failed")
    diff_text = (OUT_DIR / "cloudpickle_class_dict_source_only_patch_candidate.diff").read_text(encoding="utf-8")
    expect(errors, "tests/" not in diff_text.replace("\\", "/"), "Patch diff touches tests")
    expect(errors, "cloudpickle/cloudpickle.py" in diff_text.replace("\\", "/"), "Patch diff does not touch cloudpickle.py")

    expect(errors, post.get("class_dict_minimal_target", {}).get("return_code") == 0, "Post-repair class-dict target failed")
    expect(errors, all(node.get("return_code") == 0 for node in post.get("distutils_regression_nodes", [])), "Post-repair distutils regression check failed")
    expect(errors, post.get("original_full_target", {}).get("return_code") == 0, "Post-repair original full target failed")
    expect(errors, outcome.get("classification") == "source_only_patch_target_pass", "Repair outcome classification mismatch")
    expect(errors, outcome.get("duplicate_replay_run") is False and outcome.get("count_gate_run") is False, "Duplicate/count gate ran in Batch060d")
    expect(errors, outcome.get("repair_count_increment") is False, "Repair count incremented in Batch060d")

    expect(errors, amds_state.get("status") == "PASS" and amds_state.get("maximum_bug_tree_depth") >= 2, "AMDS full bug-tree state invalid")
    node_statuses = [node.get("current_status") for node in amds_nodes.get("nodes", [])]
    expect(errors, "resolved_by_provider_only" in node_statuses, "AMDS missing provider-resolved branch")
    expect(errors, "resolved_by_source_patch_pending_duplicate_replay" in node_statuses, "AMDS missing source patch pending duplicate branch")
    for node in amds_nodes.get("nodes", []):
        expect(errors, node.get("current_status") or node.get("next_allowed_action"), f"AMDS node lacks status/action: {node.get('node_id')}")
    expect(errors, amds_budget.get("exceeded") is False, "AMDS probe budget exceeded")

    expect(errors, health.get("advisory_diagnostic_only") is True and health.get("does_not_override_audits") is True, "Project health review is not advisory-only")
    expect(errors, "dimensions" in scorecard and "overall_project_direction" in scorecard["dimensions"], "Capability scorecard incomplete")
    expect(errors, version_grade.get("overall_grade") in {"A", "B", "C", "D", "F"}, "Version grade invalid")
    expect(errors, version_grade.get("traffic_light_status") in {"green", "yellow", "orange", "red"}, "Traffic-light status invalid")
    expect(errors, readiness.get("self_maintaining_software_demonstrated") is False, "Self-maintaining software was overclaimed")
    expect(errors, readiness.get("claim_ready_used") is False, "Readiness review used claim_ready")
    expect(errors, next_action.get("exactly_one_recommended_next_action") is True, "Next action report does not identify exactly one recommendation")
    expect(errors, tld.get("not_proof_of_physics") is True, "TLD report is not metadata-only")
    expect(errors, reactome.get("not_repair_evidence") is True, "Reactome report is not metadata-only")
    expect(errors, metaphor.get("biological_metaphors_do_not_replace_operational_classifications") is True, "Metaphor boundary invalid")

    expect(errors, batch061.get("candidate_count") == 1, "Batch061 duplicate replay candidate count mismatch")
    expect(errors, count_reco.get("recommended") is True, "Batch061 count-gate recommendation missing")
    expect(errors, final.get("cloudpickle_patch_generated") is True and final.get("cloudpickle_patch_applied") is True, "Final patch generated/applied status mismatch")
    expect(errors, final.get("cloudpickle_repair_outcome_classification") == "source_only_patch_target_pass", "Final repair outcome mismatch")
    expect(errors, final.get("source_only_target_pass_count") == 1, "Final source-only target-pass count mismatch")
    expect(errors, final.get("batch061_duplicate_replay_candidate_count") == 1, "Final Batch061 candidate count mismatch")
    expect(errors, final.get("next_allowed_action") == "batch061_duplicate_clean_replay_and_issue_repair_count_gate_wave_3", "Final next action mismatch")
    expect(errors, final.get("current_protocol") == CURRENT_PROTOCOL, "Current protocol changed")
    expect(errors, final.get("issue_derived_repair_count") == 2 and final.get("native_external_repair_count") == 4, "Repair counts changed")
    expect(errors, final.get("full_scoring") == "NOT_RUN/disallowed", "Full scoring changed")
    expect(errors, final.get("memory_lift") == "not_demonstrated", "Memory lift changed")
    expect(errors, final.get("self_maintaining_software") == "false/not_demonstrated", "Self-maintaining status changed")
    expect(errors, final.get("duplicate_replay_run") is False and final.get("count_gate_run") is False, "Duplicate/count gate ran")
    expect(errors, final.get("repair_count_increment") is False, "Repair count incremented")
    for key in [
        "controllergate_repo_source_mutated_by_candidate_patch",
        "tests_mutated",
        "fixtures_mutated",
        "duplicate_replay_run",
        "count_gate_run",
        "repair_count_increment",
    ]:
        expect_false(errors, claim, key, "Batch060d claim boundary")
    expect(errors, claim.get("project_health_review_advisory_only") is True, "Health review can override proof gates")
    for key in ["raw_zip_payload_committed", "runtime_workspaces_committed", "source_checkouts_committed", "venvs_committed", "caches_committed"]:
        expect_false(errors, package, key, "Batch060d package verification")

    for public_path in [
        ROOT / "README.md",
        ROOT / "docs" / "current_status.md",
        ROOT / "controllergate_v1_7_beta" / "reports" / "critic_review_package" / "shareable_summary.md",
    ]:
        text = public_path.read_text(encoding="utf-8")
        for phrase in [
            "The project health grade is advisory and does not constitute proof.",
            "Workflow success is not equivalent to repair success.",
            "Provider recovery is not repair success.",
            "Partial improvement is not repair success.",
            "Self-maintaining software remains false/not_demonstrated.",
            "Batch060d",
        ]:
            expect(errors, phrase in text, f"public summary missing phrase {phrase!r} in {public_path.relative_to(ROOT)}")

    audit_git_status(errors)

    if errors:
        print("FAIL:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Batch060d cloudpickle class-dict patch gate with AMDS health review audit PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
