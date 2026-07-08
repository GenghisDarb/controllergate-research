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


OUT_DIR = ROOT / "outputs" / "post_v2_37_hardening_batch060c_cloudpickle_provider_runtime_recovery"
BATCH060B_DIR = ROOT / "outputs" / "post_v2_37_hardening_batch060b_cloudpickle_decomposition_audioread_provider_preservation"
CURRENT_PROTOCOL = "v2.14"

EXPECTED_BATCH060B_SHA256 = "6bf0358df31888197d0de3f0a04c79afef1f15d81f712e262509061df66e9539"
EXPECTED_BATCH060B_SIZE = 42053
EXPECTED_BATCH060B_ENTRY_COUNT = 53
EXPECTED_BATCH060B_ARTIFACT_MANIFEST_CHECKED = 52
EXPECTED_BATCH060B_OUTPUT_MANIFEST_CHECKED = 51

REQUIRED_FILES = [
    "batch060b_artifact_ingestion_summary.json",
    "batch060b_artifact_sha256_verification.json",
    "batch060b_result_preservation.json",
    "batch060b_cloudpickle_decomposition_preservation.json",
    "batch060b_audioread_provider_branch_preservation.json",
    "batch060b_claim_boundary_preservation.json",
    "batch060b_next_action_boundary.json",
    "cloudpickle_provider_runtime_evidence_manifest.json",
    "cloudpickle_provider_runtime_forbidden_evidence_audit.json",
    "cloudpickle_issue_body_leakage_boundary.json",
    "cloudpickle_label_blindness_check.json",
    "cloudpickle_gold_patch_exclusion_check.json",
    "cloudpickle_future_evidence_exclusion_check.json",
    "cloudpickle_provider_runtime_capsule_plan.json",
    "cloudpickle_declared_dependency_map.json",
    "cloudpickle_declared_runtime_map.json",
    "cloudpickle_declared_test_command_map.json",
    "cloudpickle_distutils_availability_probe_plan.json",
    "cloudpickle_runtime_recovery_safety_check.json",
    "cloudpickle_provider_runtime_non_repair_boundary.json",
    "cloudpickle_provider_probe_results.json",
    "cloudpickle_distutils_probe_result.json",
    "cloudpickle_setuptools_probe_result.json",
    "cloudpickle_provider_install_attempt.json",
    "cloudpickle_provider_install_log_raw.txt",
    "cloudpickle_provider_runtime_recovery_result.json",
    "cloudpickle_post_recovery_replay_plan.json",
    "cloudpickle_post_recovery_replay_results.json",
    "cloudpickle_post_recovery_distutils_family_log_raw.txt",
    "cloudpickle_post_recovery_class_dict_family_log_raw.txt",
    "cloudpickle_post_recovery_full_target_log_raw.txt",
    "cloudpickle_post_recovery_failure_signature_extract.json",
    "cloudpickle_post_recovery_family_status.json",
    "cloudpickle_provider_runtime_amds_board_after_recovery.json",
    "cloudpickle_failure_cell_registry_after_recovery.json",
    "cloudpickle_failure_mine_risk_map_after_recovery.json",
    "cloudpickle_safe_action_frontier_after_recovery.json",
    "cloudpickle_information_gain_ranking_after_recovery.json",
    "cloudpickle_ast_loop_extrusion_bridge_after_recovery.json",
    "cloudpickle_source_contact_graph_after_recovery.json",
    "cloudpickle_probe_to_patch_transition_gate_after_recovery.json",
    "cloudpickle_patch_license_from_amds_after_recovery.json",
    "audioread_provider_backend_branch_preservation.json",
    "audioread_no_action_in_batch060c.json",
    "batch060c_whole_problem_map.json",
    "tld_structural_boundary_report_batch060c.json",
    "reactome_provider_capsule_carryforward_batch060c.json",
    "metaphor_to_artifact_boundary_batch060c.json",
    "provider_runtime_pattern_library.json",
    "autonomic_bottleneck_routing_rules.json",
    "provider_runtime_recovery_rule_registry.json",
    "known_provider_blocker_taxonomy.json",
    "candidate_pre_patch_provider_screen.json",
    "provider_runtime_learning_update.json",
    "future_candidate_auto_route_policy.json",
    "amds_to_provider_capsule_bridge_update.json",
    "tld_failure_boundary_pattern_update.json",
    "reactome_provider_capsule_generalization_update.json",
    "self_maintenance_capability_gap_report.json",
    "recurring_issue_registry.json",
    "patch_debt_ledger.json",
    "codex_friction_log.json",
    "repeat_failure_pattern_index.json",
    "temporary_vs_permanent_fix_audit.json",
    "permanent_fix_recommendation_queue.json",
    "repo_topology_audit.json",
    "duplicate_function_audit.json",
    "duplicate_module_audit.json",
    "utility_overlap_audit.json",
    "stale_script_and_workflow_audit.json",
    "repo_structure_recommendations.md",
    "controllergate_maintenance_memory_update.json",
    "batch060c_final_decision.json",
    "batch060d_cloudpickle_class_dict_patch_gate_recommendation.json",
    "batch060e_cloudpickle_decomposition_followup_recommendation.json",
    "batch060f_audioread_provider_backend_capsule_replay_recommendation.json",
    "batch058b_seed_discovery_wave_3_expansion_recommendation.json",
    "batch061_duplicate_replay_recommendation.json",
    "batch060c_summary.md",
    "claim_boundary.json",
    "audit.json",
    "package_verification.json",
    "artifact_sha256_verification.json",
    "SHA256SUMS.txt",
]

REQUIRED_DOCS_CONFIGS = [
    "configs/provider_runtime_pattern_registry.json",
    "configs/autonomic_bottleneck_routing_rules.json",
    "docs/controllergate_provider_runtime_recovery_patterns.md",
    "docs/controllergate_self_maintenance_runtime_wrapper_roadmap.md",
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


def git_lines(*args: str) -> list[str]:
    proc = subprocess.run(["git", *args], cwd=ROOT, text=True, capture_output=True, check=False)
    return proc.stdout.splitlines()


def expect_false(errors: list[str], obj: dict[str, Any], key: str, label: str) -> None:
    if obj.get(key) is not False:
        errors.append(f"{label} expected {key}=false, observed {obj.get(key)!r}")


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
            errors.append(f"missing required Batch060c output: {rel}")
    for rel in REQUIRED_DOCS_CONFIGS:
        if not (ROOT / rel).is_file():
            errors.append(f"missing required docs/config file: {rel}")
    if not errors:
        manifest = verify_manifest(OUT_DIR)
        if manifest.get("status") != "PASS":
            errors.append(f"Batch060c SHA256SUMS verification failed: {manifest}")
    if errors:
        print("FAIL:")
        for error in errors:
            print(f"- {error}")
        return 1

    artifact = read_json(OUT_DIR / "batch060b_artifact_sha256_verification.json")
    ingest = read_json(OUT_DIR / "batch060b_artifact_ingestion_summary.json")
    preserved = read_json(OUT_DIR / "batch060b_result_preservation.json")
    forbidden = read_json(OUT_DIR / "cloudpickle_provider_runtime_forbidden_evidence_audit.json")
    capsule = read_json(OUT_DIR / "cloudpickle_provider_runtime_capsule_plan.json")
    probe = read_json(OUT_DIR / "cloudpickle_provider_probe_results.json")
    install = read_json(OUT_DIR / "cloudpickle_provider_install_attempt.json")
    recovery = read_json(OUT_DIR / "cloudpickle_provider_runtime_recovery_result.json")
    replay = read_json(OUT_DIR / "cloudpickle_post_recovery_replay_results.json")
    family = read_json(OUT_DIR / "cloudpickle_post_recovery_family_status.json")
    license_after = read_json(OUT_DIR / "cloudpickle_patch_license_from_amds_after_recovery.json")
    audioread = read_json(OUT_DIR / "audioread_provider_backend_branch_preservation.json")
    tld = read_json(OUT_DIR / "tld_structural_boundary_report_batch060c.json")
    reactome = read_json(OUT_DIR / "reactome_provider_capsule_carryforward_batch060c.json")
    patterns = read_json(OUT_DIR / "provider_runtime_pattern_library.json")
    rules = read_json(OUT_DIR / "autonomic_bottleneck_routing_rules.json")
    screen = read_json(OUT_DIR / "candidate_pre_patch_provider_screen.json")
    recurring = read_json(OUT_DIR / "recurring_issue_registry.json")
    topology = read_json(OUT_DIR / "repo_topology_audit.json")
    duplicates = read_json(OUT_DIR / "duplicate_function_audit.json")
    overlap = read_json(OUT_DIR / "utility_overlap_audit.json")
    stale = read_json(OUT_DIR / "stale_script_and_workflow_audit.json")
    maintenance = read_json(OUT_DIR / "controllergate_maintenance_memory_update.json")
    final = read_json(OUT_DIR / "batch060c_final_decision.json")
    claim = read_json(OUT_DIR / "claim_boundary.json")
    package = read_json(OUT_DIR / "package_verification.json")
    batch061 = read_json(OUT_DIR / "batch061_duplicate_replay_recommendation.json")
    batch060b_final = read_json(BATCH060B_DIR / "batch060b_final_decision.json")

    if artifact.get("status") != "PASS":
        errors.append("Batch060b artifact verification did not pass")
    if artifact.get("zip_sha256") != EXPECTED_BATCH060B_SHA256 or artifact.get("artifact_sha256") != EXPECTED_BATCH060B_SHA256:
        errors.append("Batch060b artifact SHA mismatch")
    if artifact.get("zip_size_bytes") != EXPECTED_BATCH060B_SIZE or artifact.get("zip_entry_count") != EXPECTED_BATCH060B_ENTRY_COUNT:
        errors.append("Batch060b artifact size or entry count mismatch")
    if artifact.get("artifact_manifest", {}).get("checked") != EXPECTED_BATCH060B_ARTIFACT_MANIFEST_CHECKED:
        errors.append("Batch060b artifact manifest checked count mismatch")
    output_manifest = artifact.get("output_manifests", {}).get(
        "post_v2_37_hardening_batch060b_cloudpickle_decomposition_audioread_provider_preservation", {}
    )
    if output_manifest.get("checked") != EXPECTED_BATCH060B_OUTPUT_MANIFEST_CHECKED or output_manifest.get("failures") != 0:
        errors.append("Batch060b internal manifest verification mismatch")
    for key in ["unsafe_path_count", "duplicate_path_count", "zip_pycache_entries", "zip_pyc_entries"]:
        if artifact.get(key) != 0:
            errors.append(f"Batch060b artifact has non-zero {key}")
    if ingest.get("status") != "PASS" or ingest.get("verification", {}).get("status") != "PASS":
        errors.append("Batch060b official ingest did not pass")
    expect_false(errors, artifact, "raw_zip_bytes_ingested", "Batch060b artifact verification")
    expect_false(errors, artifact, "zip_payload_committed", "Batch060b artifact verification")
    if batch060b_final.get("next_allowed_action") != "batch060c_cloudpickle_provider_runtime_recovery":
        errors.append("Committed Batch060b no longer routes to Batch060c")
    if preserved.get("issue_derived_repair_count") != 2 or preserved.get("native_external_repair_count") != 4:
        errors.append("Batch060b preserved repair counts changed")

    for key in [
        "fixed_commit_used",
        "future_commit_used",
        "pr_patch_used",
        "gold_patch_used",
        "issue_body_fix_text_used",
        "synthetic_tests_added",
        "test_mutation",
    ]:
        expect_false(errors, forbidden, key, "Cloudpickle forbidden evidence audit")
    if capsule.get("answers", {}).get("installing_setuptools_decision_time_safe") is not True:
        errors.append("Setuptools provider materialization is not recorded as decision-time safe")
    if install.get("undeclared_dependency_install") is not False:
        errors.append("Provider install attempt authorized an undeclared dependency")
    if probe.get("after_setuptools_distutils") != "available":
        errors.append("Distutils did not become available after provider materialization")
    if recovery.get("classification") != "provider_runtime_recovery_succeeded_target_failure_materialized":
        errors.append("Provider/runtime recovery classification mismatch")
    if recovery.get("repair_success") is not False:
        errors.append("Provider recovery was overclaimed as repair success")
    if family.get("distutils_family_status") != "distutils_family_resolved_by_provider":
        errors.append("Distutils family was not resolved by provider")
    if family.get("class_dict_family_status") != "class_dict_family_still_fails_interpreter_behavior":
        errors.append("Class-dict family status mismatch")
    if family.get("full_target_status") != "full_target_failure_reduced_to_class_dict_only":
        errors.append("Full target was not reduced to class-dict family")
    if replay.get("full_target", {}).get("return_code") != 1:
        errors.append("Full target replay did not preserve remaining failure")
    if license_after.get("license_is_future_only") is not True or license_after.get("batch060c_patch_allowed") is not False:
        errors.append("Cloudpickle patch license after recovery is not future-only")
    if license_after.get("patch_license_state") != "cloudpickle_patch_license_future_open_class_dict_single_family":
        errors.append("Cloudpickle future patch license state mismatch")

    if audioread.get("patched_in_batch060c") is not False or audioread.get("counted_in_batch060c") is not False:
        errors.append("Audioread branch was modified or counted in Batch060c")
    if tld.get("not_proof_of_physics") is not True:
        errors.append("TLD boundary is not limited to metadata/guidance")
    if reactome.get("not_repair_evidence") is not True:
        errors.append("Reactome boundary is not limited to provider-capsule pattern")

    pattern_ids = {pattern.get("pattern_id") for pattern in patterns.get("patterns", [])}
    expected_patterns = {
        "removed_stdlib_module",
        "optional_backend_missing",
        "test_runner_provider_mismatch",
        "python_runtime_behavior_change",
        "compiled_dependency_boundary",
        "network_model_external_service_boundary",
        "source_provider_mixed_surface",
    }
    if not expected_patterns.issubset(pattern_ids):
        errors.append("Provider/runtime pattern library is missing expected patterns")
    if rules.get("no_rule_authorizes_batch060c_patching") is not True:
        errors.append("A routing rule authorizes Batch060c patching")
    if rules.get("no_rule_allows_undeclared_dependency_install") is not True:
        errors.append("A routing rule allows undeclared dependency install")
    if rules.get("no_rule_allows_test_mutation") is not True:
        errors.append("A routing rule allows test mutation")
    if screen.get("provider_runtime_patterns_detected") != [
        "removed_stdlib_module",
        "source_provider_mixed_surface",
        "python_runtime_behavior_change",
    ]:
        errors.append("Candidate pre-patch provider screen does not record Cloudpickle split")
    if screen.get("provider_screen_status") != "provider_recovery_required":
        errors.append("Provider screen status mismatch")
    if screen.get("patch_license_precondition") != "closed_provider_first":
        errors.append("Provider screen patch precondition mismatch")

    if recurring.get("issue_count", 0) < 18:
        errors.append("Recurring issue registry does not include enough repeated issue classes")
    if topology.get("status") != "PASS" or "workflow_files_map" not in topology:
        errors.append("Repo topology audit missing workflow map")
    if duplicates.get("status") != "PASS":
        errors.append("Duplicate function audit missing")
    if overlap.get("status") != "PASS":
        errors.append("Utility overlap audit missing")
    if stale.get("no_workflow_deleted") is not True:
        errors.append("Stale workflow audit does not preserve workflows")
    if maintenance.get("status") != "PASS" or maintenance.get("next_best_repo_hygiene_batch") != "batch06x_audit_boilerplate_deduplication":
        errors.append("Maintenance memory update missing expected future-only recommendation")

    for key in [
        "batch060c_patch_generated",
        "batch060c_patch_applied",
        "source_mutation",
        "test_mutation",
        "post_repair_replay_run",
        "duplicate_replay_run",
        "count_gate_run",
        "repair_count_increment",
    ]:
        expect_false(errors, final, key, "Batch060c final decision")
    for key in [
        "batch060c_generates_patch",
        "batch060c_applies_patch",
        "source_mutation",
        "test_mutation",
        "synthetic_tests_added",
        "post_repair_replay_run",
        "duplicate_replay_run",
        "count_gate_run",
        "repair_count_increment",
        "provider_runtime_recovery_counts_as_repair",
    ]:
        expect_false(errors, claim, key, "Batch060c claim boundary")
    if claim.get("no_production_refactor_performed") is not True or claim.get("all_maintenance_recommendations_future_only") is not True:
        errors.append("Maintenance-memory claim boundary missing")
    if final.get("next_allowed_action") != "batch060d_cloudpickle_class_dict_source_only_patch_gate":
        errors.append("Batch060c next action mismatch")
    if final.get("current_protocol") != CURRENT_PROTOCOL:
        errors.append("Current protocol changed from v2.14")
    if final.get("issue_derived_repair_count") != 2 or final.get("native_external_repair_count") != 4:
        errors.append("Repair counts changed")
    if final.get("full_scoring") != "NOT_RUN/disallowed" or final.get("memory_lift") != "not_demonstrated" or final.get("self_maintaining_software") != "false/not_demonstrated":
        errors.append("Batch060c overclaim")
    if batch061.get("recommended") is not False or batch061.get("candidate_ids") != []:
        errors.append("Batch061 recommendation is not empty")
    for key in ["raw_zip_payload_committed", "runtime_workspaces_committed", "source_checkouts_committed", "venvs_committed", "caches_committed"]:
        expect_false(errors, package, key, "Batch060c package verification")

    if list(OUT_DIR.rglob("*.diff")):
        errors.append("Batch060c output contains patch diff despite no-patch boundary")
    audit_git_status(errors)

    if errors:
        print("FAIL:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Batch060c cloudpickle provider runtime recovery audit PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
