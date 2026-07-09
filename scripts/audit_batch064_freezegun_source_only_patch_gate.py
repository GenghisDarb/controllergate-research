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


OUT_DIR = ROOT / "outputs" / "post_v2_37_hardening_batch064_freezegun_source_only_patch_gate"
CURRENT_PROTOCOL = "v2.14"
FREEZEGUN_ID = "freezegun_547_py313_datetimes_assertion"
PYTEST_ID = "pytest_13895_pytest9_skiptest_behavior"

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

REQUIRED_FILES = [
    "batch063_artifact_ingestion_summary.json",
    "batch063_artifact_sha256_verification.json",
    "batch063_result_preservation.json",
    "batch063_freezegun_materialization_preservation.json",
    "batch063_pytest_blocker_preservation.json",
    "batch063_amds_bug_tree_preservation.json",
    "batch063_claim_boundary_preservation.json",
    "batch063_next_action_boundary.json",
    "batch064_candidate_scope.json",
    "batch064_candidate_scope_audit.json",
    "batch064_excluded_candidate_registry.json",
    "pytest_blocked_command_boundary_preservation.json",
    "batch064_decision_time_input_manifest.json",
    "batch064_forbidden_evidence_audit.json",
    "batch064_issue_body_leakage_boundary.json",
    "batch064_label_blindness_check.json",
    "batch064_gold_patch_exclusion_check.json",
    "batch064_future_evidence_exclusion_check.json",
    "freezegun_workspace_manifest.json",
    "freezegun_commit_verification.json",
    "freezegun_workspace_custody_check.json",
    "freezegun_baseline_source_hashes.json",
    "freezegun_command_context.json",
    "freezegun_command_normalization.json",
    "freezegun_declared_dependency_map.json",
    "freezegun_declared_runtime_map.json",
    "freezegun_declared_test_command_map.json",
    "freezegun_provider_runtime_capsule_plan.json",
    "freezegun_provider_install_attempt.json",
    "freezegun_provider_install_log_raw.txt",
    "freezegun_provider_runtime_setup_result.json",
    "freezegun_prerepair_replay_command.txt",
    "freezegun_prerepair_replay_log_raw.txt",
    "freezegun_prerepair_replay_result.json",
    "freezegun_prerepair_failure_signature_extract.json",
    "freezegun_prerepair_outcome_classification.json",
    "freezegun_diagnostic_minimal_replay_plan.json",
    "freezegun_diagnostic_minimal_replay_results.json",
    "freezegun_diagnostic_failed_node_registry.json",
    "freezegun_diagnostic_traceback_roots.json",
    "freezegun_diagnostic_failure_signature_extract.json",
    "freezegun_diagnostic_probe_budget.json",
    "freezegun_failure_split_check.json",
    "freezegun_source_file_inventory.json",
    "freezegun_source_discovery_plan.json",
    "freezegun_source_discovery_result.json",
    "freezegun_suspect_source_files.json",
    "freezegun_failure_to_source_trace.json",
    "freezegun_decision_time_source_manifest.json",
    "freezegun_source_surface_localization_check.json",
    "freezegun_ast_loop_extrusion_bridge.json",
    "freezegun_source_contact_graph_extrusion_result.json",
    "freezegun_probe_to_patch_transition_gate.json",
    "freezegun_patch_license_from_amds_batch064.json",
    "freezegun_source_only_patch_candidate.diff",
    "freezegun_source_only_patch_candidate.json",
    "freezegun_patch_generation_trace.json",
    "freezegun_patch_safety_check.json",
    "freezegun_patch_application_result.json",
    "freezegun_changed_files_manifest.json",
    "freezegun_test_mutation_check.json",
    "freezegun_fixture_mutation_check.json",
    "freezegun_dependency_file_mutation_check.json",
    "freezegun_source_only_check.json",
    "freezegun_post_repair_focused_nodes_command.txt",
    "freezegun_post_repair_focused_nodes_log_raw.txt",
    "freezegun_post_repair_focused_nodes_result.json",
    "freezegun_post_repair_full_target_command.txt",
    "freezegun_post_repair_full_target_log_raw.txt",
    "freezegun_post_repair_full_target_result.json",
    "freezegun_post_repair_failure_signature_extract.json",
    "freezegun_repair_outcome_classification.json",
    "pytest_blocked_target_command_boundary_batch064.json",
    "pytest_future_provider_runtime_recovery_preservation.json",
    "freezegun_amds_full_bug_tree_state_batch064.json",
    "freezegun_bug_tree_node_registry_batch064.json",
    "freezegun_bug_tree_edge_registry_batch064.json",
    "freezegun_secondary_bug_registry_batch064.json",
    "freezegun_provider_dependency_branch_registry_batch064.json",
    "freezegun_interpreter_behavior_branch_registry_batch064.json",
    "freezegun_unrecoverable_branch_registry_batch064.json",
    "freezegun_repairable_branch_registry_batch064.json",
    "freezegun_next_action_frontier_batch064.json",
    "datetime_interpreter_compatibility_pattern_update.json",
    "platform_api_absence_pattern_update.json",
    "source_contact_from_test_only_antipattern_update.json",
    "patch_license_revalidation_pattern_update.json",
    "single_family_patch_gate_with_split_check_pattern.json",
    "freezegun_salvage_pattern_update_batch064.json",
    "pytest_command_boundary_pattern_update_batch064.json",
    "recurring_bottleneck_trend_report_batch064.json",
    "self_maintenance_runtime_progress_review_batch064.json",
    "project_health_review_batch064.json",
    "capability_maturity_scorecard_batch064.json",
    "version_progress_grade_batch064.json",
    "strategic_direction_check_batch064.json",
    "proof_milestone_distance_report_batch064.json",
    "regression_and_drift_watch_batch064.json",
    "self_maintenance_readiness_review_batch064.json",
    "next_highest_impact_action_report_batch064.json",
    "tld_governance_boundary_batch064.json",
    "reactome_provider_capsule_boundary_batch064.json",
    "internal_theory_to_engineering_translation_batch064.json",
    "public_language_neutrality_check_batch064.json",
    "public_summary_claim_safety_check_batch064.json",
    "batch064_final_decision.json",
    "batch065_duplicate_replay_candidates.json",
    "batch065_count_gate_recommendation.json",
    "batch064b_freezegun_decomposition_recommendation.json",
    "batch063b_pytest_provider_runtime_recovery_recommendation.json",
    "batch058d_seed_discovery_expansion_recommendation.json",
    "batch064_summary.md",
    "claim_boundary.json",
    "audit.json",
    "package_verification.json",
    "artifact_sha256_verification.json",
    "SHA256SUMS.txt",
]

PRIOR_AUDITS = [
    "scripts/audit_batch063_wave3_or_salvage_pre_repair_replay_limited.py",
    "scripts/audit_batch058c_seed_discovery_expansion_or_salvage_reassessment.py",
    "scripts/audit_batch060f_audioread_provider_backend_capsule_replay.py",
    "scripts/audit_batch058b_seed_discovery_wave_3_expansion.py",
    "scripts/audit_batch062_next_issue_repair_candidate_selection_or_wave3_expansion.py",
    "scripts/audit_batch061_duplicate_clean_replay_count_gate_cloudpickle_wave_3.py",
    "scripts/audit_batch060d_cloudpickle_class_dict_patch_gate_with_amds_health_review.py",
    "scripts/audit_batch060c_cloudpickle_provider_runtime_recovery.py",
    "scripts/audit_batch060b_cloudpickle_decomposition_audioread_provider_preservation.py",
    "scripts/audit_batch060_source_only_patch_gate_wave_3.py",
    "scripts/audit_batch059_pre_repair_replay_wave_3_limited.py",
    "scripts/audit_batch058_seed_discovery_wave_3_provider_prescreen.py",
    "scripts/audit_batch056f_timeout_split_replay_wave_2.py",
    "scripts/audit_batch056e_timeout_candidate_decomposition_wave_2_provider_capsules.py",
    "scripts/audit_batch056d_wave2_provider_dependency_recovery.py",
    "scripts/audit_batch056b_wave2_pre_repair_replay_plus_amds_bridge.py",
    "scripts/audit_batch057c_layered_source_only_patch_recovery_freezegun.py",
    "scripts/audit_batch057b_failure_family_decomposition_elbow_recovery.py",
    "scripts/audit_batch057_source_only_patch_gate_wave_1.py",
    "scripts/audit_batch056_pre_repair_replay_wave_1_plus_wave_2_intake.py",
    "scripts/audit_batch055_seed_discovery_wave_1.py",
    "scripts/audit_post_v2_37_hardening_and_batch002.py",
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


def public_batch064_block(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    marker = "Batch064 is the latest Freezegun source-only patch-gate boundary."
    start = text.find(marker)
    if start == -1:
        return ""
    next_marker = text.find("Batch063 is the latest limited pre-repair replay boundary.", start)
    if next_marker == -1:
        next_marker = min(len(text), start + 5000)
    return text[start:next_marker]


def audit_public_summary(errors: list[str]) -> None:
    for rel in [
        "README.md",
        "docs/current_status.md",
        "controllergate_v1_7_beta/reports/critic_review_package/shareable_summary.md",
    ]:
        block = public_batch064_block(ROOT / rel)
        expect(errors, bool(block), f"missing Batch064 public summary block in {rel}")
        for phrase in [
            "Workflow success is not equivalent to repair success.",
            "Pre-repair replay is not repair success.",
            "Future patch license is not repair success.",
            "Partial improvement is not repair success.",
            "Repair count increments require duplicate clean replay and count gate.",
            "Self-maintaining software remains false/not_demonstrated.",
        ]:
            expect(errors, phrase in block, f"Batch064 public summary missing {phrase!r} in {rel}")
        lowered = block.lower()
        for term in PUBLIC_FORBIDDEN_TERMS:
            expect(errors, term.lower() not in lowered, f"Batch064 public summary contains internal term {term!r} in {rel}")


def main() -> int:
    errors: list[str] = []
    if not OUT_DIR.is_dir():
        print(f"FAIL: missing output directory: {OUT_DIR.relative_to(ROOT)}")
        return 1
    for rel in REQUIRED_FILES:
        expect(errors, (OUT_DIR / rel).is_file(), f"missing required Batch064 output: {rel}")
    if errors:
        print("FAIL:")
        for error in errors:
            print(f"- {error}")
        return 1

    manifest = verify_manifest(OUT_DIR)
    expect(errors, manifest.get("status") == "PASS", f"Batch064 SHA256SUMS verification failed: {manifest}")

    artifact = read_json(OUT_DIR / "batch063_artifact_sha256_verification.json")
    ingest = read_json(OUT_DIR / "batch063_artifact_ingestion_summary.json")
    preservation = read_json(OUT_DIR / "batch063_result_preservation.json")
    materialization = read_json(OUT_DIR / "batch063_freezegun_materialization_preservation.json")
    pytest_preserve = read_json(OUT_DIR / "batch063_pytest_blocker_preservation.json")
    scope = read_json(OUT_DIR / "batch064_candidate_scope_audit.json")
    forbidden = read_json(OUT_DIR / "batch064_forbidden_evidence_audit.json")
    commit = read_json(OUT_DIR / "freezegun_commit_verification.json")
    workspace = read_json(OUT_DIR / "freezegun_workspace_custody_check.json")
    provider = read_json(OUT_DIR / "freezegun_provider_runtime_setup_result.json")
    prerepair = read_json(OUT_DIR / "freezegun_prerepair_outcome_classification.json")
    split = read_json(OUT_DIR / "freezegun_failure_split_check.json")
    source = read_json(OUT_DIR / "freezegun_source_discovery_result.json")
    suspects = read_json(OUT_DIR / "freezegun_suspect_source_files.json")
    transition = read_json(OUT_DIR / "freezegun_probe_to_patch_transition_gate.json")
    license_ = read_json(OUT_DIR / "freezegun_patch_license_from_amds_batch064.json")
    patch = read_json(OUT_DIR / "freezegun_source_only_patch_candidate.json")
    safety = read_json(OUT_DIR / "freezegun_patch_safety_check.json")
    app = read_json(OUT_DIR / "freezegun_patch_application_result.json")
    tests = read_json(OUT_DIR / "freezegun_test_mutation_check.json")
    fixtures = read_json(OUT_DIR / "freezegun_fixture_mutation_check.json")
    deps = read_json(OUT_DIR / "freezegun_dependency_file_mutation_check.json")
    source_only = read_json(OUT_DIR / "freezegun_source_only_check.json")
    post_full = read_json(OUT_DIR / "freezegun_post_repair_full_target_result.json")
    outcome = read_json(OUT_DIR / "freezegun_repair_outcome_classification.json")
    final = read_json(OUT_DIR / "batch064_final_decision.json")
    batch065 = read_json(OUT_DIR / "batch065_duplicate_replay_candidates.json")
    claim = read_json(OUT_DIR / "claim_boundary.json")
    package = read_json(OUT_DIR / "package_verification.json")
    public_language = read_json(OUT_DIR / "public_language_neutrality_check_batch064.json")
    tld = read_json(OUT_DIR / "tld_governance_boundary_batch064.json")
    reactome = read_json(OUT_DIR / "reactome_provider_capsule_boundary_batch064.json")

    expect(errors, artifact.get("status") == "PASS", "Batch063 artifact verification did not pass")
    expect(errors, artifact.get("zip_sha256") == "28b80af6ef3787d53a0e0371a9c2fbac2077e7533ce35503b1183ee2f62bedf8", "Batch063 artifact SHA mismatch")
    expect(errors, artifact.get("zip_size_bytes") == 79829, "Batch063 artifact size mismatch")
    expect(errors, artifact.get("zip_entry_count") == 134, "Batch063 artifact entry count mismatch")
    expect(errors, artifact.get("artifact_manifest", {}).get("status") == "PASS", "Batch063 artifact manifest failed")
    expect(errors, artifact.get("output_manifest", {}).get("status") == "PASS", "Batch063 output manifest failed")
    expect(errors, ingest.get("status") == "PASS", "Batch063 artifact ingest did not pass")
    expect(errors, preservation.get("issue_derived_repair_count") == 3, "Issue-derived repair count not preserved")
    expect(errors, preservation.get("native_external_repair_count") == 4, "Native external repair count not preserved")
    expect(errors, preservation.get("full_scoring") == "NOT_RUN/disallowed", "Full scoring changed")
    expect(errors, preservation.get("memory_lift") == "not_demonstrated", "Memory lift changed")
    expect(errors, preservation.get("self_maintaining_software") == "false/not_demonstrated", "Self-maintaining changed")
    expect(errors, materialization.get("freezegun_materialized_failure") == "pre_repair_failure_materialized", "Freezegun materialization not preserved")
    expect(errors, materialization.get("freezegun_patch_license_from_batch063") == "patch_license_future_open_single_source_family", "Batch063 Freezegun license not preserved")
    expect(errors, pytest_preserve.get("pytest_status") == "blocked_target_command_invalid", "Pytest blocker not preserved")
    expect(errors, scope.get("operated_only_on_freezegun_for_patching") is True, "Batch064 did not scope to Freezegun")
    expect(errors, scope.get("pytest_patched") is False, "Pytest must not be patched")
    for key in ["fixed_commit_used", "future_commit_used", "pr_patch_used", "gold_patch_used", "issue_body_fix_or_workaround_text_used", "modern_fixed_source_used", "test_modified", "fixture_modified", "synthetic_test_used"]:
        expect(errors, forbidden.get(key) is False, f"Forbidden evidence expected {key}=false")

    expect(errors, commit.get("status") == "PASS" and commit.get("resolved_head") == "df263dcec48f43154a5873eb0dff2d4ba94374da", "Freezegun commit verification failed")
    expect(errors, workspace.get("status") == "PASS" and workspace.get("native_test_path_exists") is True and workspace.get("source_package_exists") is True, "Workspace custody failed")
    expect(errors, provider.get("classification") == "provider_runtime_recovered_from_declared_metadata", "Provider/runtime setup not recovered from declared metadata")
    expect(errors, prerepair.get("classification") == "pre_repair_failure_materialized", "Fresh pre-repair failure did not materialize before patch")
    expect(errors, split.get("failure_split_classification") in {"freezegun_single_source_family", "freezegun_two_source_families", "freezegun_source_plus_provider_interpreter_family"}, "Failure split classification invalid")
    expect(errors, split.get("one_narrow_source_only_patch_can_address_full_target") is True, "Split check did not license a full-target source patch")
    expect(errors, source.get("status") == "PASS", "Source discovery did not pass")
    expect(errors, suspects.get("tests_only_source_contact") is False, "Source-contact map is tests-only")
    expect(errors, "freezegun/api.py" in suspects.get("suspect_source_files", []), "freezegun/api.py not in suspect source files")
    expect(errors, transition.get("patch_generation_allowed") is True, "Probe-to-patch transition gate not open")
    expect(errors, license_.get("patch_license_state") in {"freezegun_patch_license_open_single_source_family", "freezegun_patch_license_open_staged_source_family"}, "Batch064 patch license not open")
    expect(errors, patch.get("status") == "PASS" and patch.get("patch_sha256"), "Patch candidate missing or empty")
    expect(errors, patch.get("changed_files") == ["freezegun/api.py"], "Patch must touch only freezegun/api.py")
    expect(errors, safety.get("source_only") is True, "Patch safety source-only check failed")
    expect(errors, app.get("patch_applied") is True, "Patch was not applied")
    expect(errors, tests.get("test_files_modified") == [], "Tests were modified")
    expect(errors, fixtures.get("fixture_files_modified") == [], "Fixtures were modified")
    expect(errors, deps.get("dependency_or_build_files_modified") == [], "Dependency/build files were modified")
    expect(errors, source_only.get("source_only") is True, "Source-only check failed")
    expect(errors, post_full.get("returncode") == 0, "Post-repair original full target did not pass")
    expect(errors, outcome.get("classification") == "source_only_patch_target_pass", "Repair outcome is not source-only target pass")
    expect(errors, final.get("status") == "PASS", "Final decision not PASS")
    expect(errors, final.get("current_protocol") == CURRENT_PROTOCOL, "Current protocol changed")
    expect(errors, final.get("issue_derived_repair_count") == 3, "Final issue-derived count changed")
    expect(errors, final.get("native_external_repair_count") == 4, "Final native external count changed")
    expect(errors, final.get("source_only_target_pass_count") == 1, "Source-only target pass count should be 1")
    expect(errors, final.get("batch065_duplicate_replay_candidate_count") == 1, "Batch065 candidate count should be 1")
    expect(errors, final.get("duplicate_replay_run") is False, "Batch064 must not run duplicate replay")
    expect(errors, final.get("count_gate_run") is False, "Batch064 must not run count gate")
    expect(errors, final.get("repair_count_increment") is False, "Batch064 must not increment repair count")
    expect(errors, final.get("full_scoring") == "NOT_RUN/disallowed", "Full scoring changed in final")
    expect(errors, final.get("memory_lift") == "not_demonstrated", "Memory lift changed in final")
    expect(errors, final.get("self_maintaining_software") == "false/not_demonstrated", "Self-maintaining changed in final")
    expect(errors, batch065.get("candidate_count") == 1 and batch065.get("duplicate_replay_run_in_batch064") is False, "Batch065 recommendation invalid")
    expect(errors, claim.get("duplicate_replay_run") is False and claim.get("count_gate_run") is False and claim.get("repair_count_increment") is False, "Claim boundary overreached")
    for key in ["raw_zip_payload_committed", "runtime_workspaces_committed", "source_checkouts_committed", "venvs_committed", "caches_committed"]:
        expect(errors, package.get(key) is False, f"Package verification expected {key}=false")
    expect(errors, public_language.get("status") == "PASS", "Public language neutrality failed")
    expect(errors, tld.get("internal_governance_audit_logic_only") is True, "TLD boundary not internal-only")
    expect(errors, reactome.get("provider_capsule_step_gating_pattern_only") is True, "Reactome boundary not provider-capsule-only")

    audit_public_summary(errors)
    audit_git_status(errors)
    for rel in PRIOR_AUDITS:
        run_python_script(rel, errors)
    proc = subprocess.run([sys.executable, "scripts/controllergate_audit.py", "--protocol", "current"], cwd=ROOT, text=True, capture_output=True, check=False)
    expect(errors, proc.returncode == 0, f"current protocol audit failed: {proc.stdout[-1000:]} {proc.stderr[-1000:]}")
    proc = subprocess.run([sys.executable, "scripts/controllergate_run.py", "--protocol", "current", "--dry-run"], cwd=ROOT, text=True, capture_output=True, check=False)
    expect(errors, proc.returncode == 0, f"current protocol dry-run failed: {proc.stdout[-1000:]} {proc.stderr[-1000:]}")

    if errors:
        print("FAIL:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Batch064 Freezegun source-only patch gate audit PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
