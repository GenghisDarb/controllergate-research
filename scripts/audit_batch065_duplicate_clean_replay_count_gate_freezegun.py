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


OUT_DIR = ROOT / "outputs" / "post_v2_37_hardening_batch065_duplicate_clean_replay_count_gate_freezegun"
BATCH064_DIR = ROOT / "outputs" / "post_v2_37_hardening_batch064_freezegun_source_only_patch_gate"
CURRENT_PROTOCOL = "v2.14"
FREEZEGUN_ID = "freezegun_547_py313_datetimes_assertion"
PYTEST_ID = "pytest_13895_pytest9_skiptest_behavior"
PATCH_SHA256 = "8daf31c4d59ead1832aa3bdc6260bae3c92a1052f140c9f0442a550c4ebf3247"

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
    ".venv",
    "/venv/",
    "\\venv\\",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
]

REQUIRED_FILES = [
    "batch064_artifact_ingestion_summary.json",
    "batch064_artifact_sha256_verification.json",
    "batch064_result_preservation.json",
    "batch064_freezegun_patch_preservation.json",
    "batch064_freezegun_target_pass_preservation.json",
    "batch064_pytest_blocker_preservation.json",
    "batch064_claim_boundary_preservation.json",
    "batch064_next_action_boundary.json",
    "batch065_candidate_scope.json",
    "batch065_candidate_scope_audit.json",
    "batch065_excluded_candidate_registry.json",
    "pytest_blocked_command_boundary_preservation_batch065.json",
    "batch065_decision_time_input_manifest.json",
    "batch065_forbidden_evidence_audit.json",
    "batch065_issue_body_leakage_boundary.json",
    "batch065_label_blindness_check.json",
    "batch065_gold_patch_exclusion_check.json",
    "batch065_future_evidence_exclusion_check.json",
    "duplicate_workspace_manifest.json",
    "duplicate_commit_verification.json",
    "duplicate_workspace_custody_check.json",
    "duplicate_candidate_source_baseline_hashes.json",
    "duplicate_provider_runtime_plan.json",
    "duplicate_provider_install_attempt.json",
    "duplicate_provider_install_log_raw.txt",
    "duplicate_provider_runtime_result.json",
    "duplicate_prerepair_focused_nodes_command.txt",
    "duplicate_prerepair_focused_nodes_log_raw.txt",
    "duplicate_prerepair_focused_nodes_result.json",
    "duplicate_prerepair_full_target_command.txt",
    "duplicate_prerepair_full_target_log_raw.txt",
    "duplicate_prerepair_full_target_result.json",
    "duplicate_prerepair_failure_signature_extract.json",
    "duplicate_prerepair_failure_family_match.json",
    "duplicate_patch_identity_check.json",
    "duplicate_patch_application_result.json",
    "duplicate_changed_files_manifest.json",
    "duplicate_source_only_check.json",
    "duplicate_test_mutation_check.json",
    "duplicate_fixture_mutation_check.json",
    "duplicate_dependency_file_mutation_check.json",
    "duplicate_patch_post_apply_source_hashes.json",
    "duplicate_postpatch_focused_nodes_command.txt",
    "duplicate_postpatch_focused_nodes_log_raw.txt",
    "duplicate_postpatch_focused_nodes_result.json",
    "duplicate_postpatch_full_target_command.txt",
    "duplicate_postpatch_full_target_log_raw.txt",
    "duplicate_postpatch_full_target_result.json",
    "duplicate_postpatch_failure_signature_extract.json",
    "duplicate_replay_outcome_classification.json",
    "issue_repair_count_gate_plan.json",
    "issue_repair_count_gate_results.json",
    "issue_repair_count_gate_criteria_matrix.json",
    "issue_repair_count_gate_pass_record.json",
    "issue_derived_repair_count_update.json",
    "native_external_repair_count_preservation.json",
    "duplicate_or_already_counted_check.json",
    "canonical_issue_repair_record_freezegun.json",
    "proof_ledger_freezegun_entry.json",
    "proof_ledger_update_summary.json",
    "freezegun_count_gate_pattern_update.json",
    "staged_source_family_to_count_gate_pattern.json",
    "platform_api_absence_count_gate_pattern_update.json",
    "duplicate_replay_count_gate_pattern_library_update.json",
    "issue_derived_repair_increment_pattern_update.json",
    "salvage_candidate_to_counted_repair_route_update.json",
    "pytest_command_boundary_preservation_update.json",
    "project_health_review_batch065.json",
    "capability_maturity_scorecard_batch065.json",
    "version_progress_grade_batch065.json",
    "self_maintenance_readiness_review_batch065.json",
    "recurring_bottleneck_trend_report_batch065.json",
    "next_highest_impact_action_report_batch065.json",
    "public_language_neutrality_check_batch065.json",
    "public_summary_claim_safety_check_batch065.json",
    "internal_vs_public_language_boundary_batch065.json",
    "post_count_acceleration_trigger_batch065.json",
    "post_count_state_capture_batch065.json",
    "post_count_claim_boundary_batch065.json",
    "next_count_opportunity_queue_batch065.json",
    "next_count_candidate_strategy_batch065.json",
    "proof_distance_to_issue_repair_count_5.json",
    "candidate_path_comparison_after_batch065.json",
    "next_best_proof_path_after_batch065.json",
    "public_readiness_audit_batch065.json",
    "repo_topology_public_readiness_review_batch065.json",
    "duplicate_function_review_batch065.json",
    "duplicate_script_review_batch065.json",
    "workflow_duplication_review_batch065.json",
    "audit_boilerplate_duplication_review_batch065.json",
    "artifact_schema_duplication_review_batch065.json",
    "public_docs_staleness_review_batch065.json",
    "readme_public_alignment_review_batch065.json",
    "license_and_attribution_review_batch065.json",
    "release_packaging_readiness_review_batch065.json",
    "permanent_fix_queue_after_batch065.json",
    "repo_hygiene_backlog_after_batch065.json",
    "public_ready_cleanup_backlog_after_batch065.json",
    "self_maintenance_infrastructure_backlog_after_batch065.json",
    "reactome_tld_isomorphic_engineering_map_batch065.json",
    "reactome_provider_capsule_full_utilization_review_batch065.json",
    "tld_governance_full_utilization_review_batch065.json",
    "isomorphic_logic_gap_audit_batch065.json",
    "isomorphic_logic_to_repo_function_matrix_batch065.json",
    "self_maintaining_wrapper_capability_upgrade_review_batch065.json",
    "autonomic_runtime_wrapper_gap_report_batch065.json",
    "next_autonomic_layer_recommendation_batch065.json",
    "batch065_final_decision.json",
    "batch066_next_action_recommendation.json",
    "batch063b_pytest_provider_runtime_recovery_recommendation.json",
    "batch058d_seed_discovery_expansion_recommendation.json",
    "batch062b_repo_hygiene_utility_consolidation_planning_recommendation.json",
    "memory_lift_future_plan_recommendation.json",
    "batch065_summary.md",
    "claim_boundary.json",
    "audit.json",
    "package_verification.json",
    "artifact_sha256_verification.json",
    "SHA256SUMS.txt",
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


def public_batch065_block(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    marker = "Batch065 is the latest duplicate clean replay and issue-derived repair count-gate boundary."
    start = text.find(marker)
    if start == -1:
        return ""
    next_marker = text.find("Batch064 is the latest Freezegun source-only patch-gate boundary.", start)
    if next_marker == -1:
        next_marker = min(len(text), start + 5000)
    return text[start:next_marker]


def audit_public_summary(errors: list[str]) -> None:
    for rel in [
        "README.md",
        "docs/current_status.md",
        "controllergate_v1_7_beta/reports/critic_review_package/shareable_summary.md",
    ]:
        block = public_batch065_block(ROOT / rel)
        expect(errors, bool(block), f"missing Batch065 public summary block in {rel}")
        for phrase in [
            "Workflow success is not equivalent to repair success.",
            "Provider/runtime setup is not repair success.",
            "A repair is counted only after duplicate clean replay and count gate pass.",
            "The public-readiness and repo-topology reviews are advisory and do not constitute repair proof.",
            "No repo refactor was performed in this proof-gate batch.",
            "The project health grade is advisory and does not constitute proof.",
            "Self-maintaining software remains false/not_demonstrated.",
        ]:
            expect(errors, phrase in block, f"Batch065 public summary missing {phrase!r} in {rel}")
        lowered = block.lower()
        for term in PUBLIC_FORBIDDEN_TERMS:
            expect(errors, term.lower() not in lowered, f"Batch065 public summary contains internal term {term!r} in {rel}")


def main() -> int:
    errors: list[str] = []
    if not OUT_DIR.is_dir():
        print(f"FAIL: missing output directory: {OUT_DIR.relative_to(ROOT)}")
        return 1
    for rel in REQUIRED_FILES:
        expect(errors, (OUT_DIR / rel).is_file(), f"missing required Batch065 output: {rel}")
    if errors:
        print("FAIL:")
        for error in errors:
            print(f"- {error}")
        return 1

    manifest = verify_manifest(OUT_DIR)
    expect(errors, manifest.get("status") == "PASS", f"Batch065 SHA256SUMS verification failed: {manifest}")

    artifact = read_json(OUT_DIR / "batch064_artifact_sha256_verification.json")
    preservation = read_json(OUT_DIR / "batch064_result_preservation.json")
    patch_preserve = read_json(OUT_DIR / "batch064_freezegun_patch_preservation.json")
    scope = read_json(OUT_DIR / "batch065_candidate_scope_audit.json")
    forbidden = read_json(OUT_DIR / "batch065_forbidden_evidence_audit.json")
    commit = read_json(OUT_DIR / "duplicate_commit_verification.json")
    workspace = read_json(OUT_DIR / "duplicate_workspace_custody_check.json")
    provider = read_json(OUT_DIR / "duplicate_provider_runtime_result.json")
    prerepair = read_json(OUT_DIR / "duplicate_prerepair_failure_family_match.json")
    identity = read_json(OUT_DIR / "duplicate_patch_identity_check.json")
    patch_app = read_json(OUT_DIR / "duplicate_patch_application_result.json")
    source_only = read_json(OUT_DIR / "duplicate_source_only_check.json")
    tests = read_json(OUT_DIR / "duplicate_test_mutation_check.json")
    fixtures = read_json(OUT_DIR / "duplicate_fixture_mutation_check.json")
    deps = read_json(OUT_DIR / "duplicate_dependency_file_mutation_check.json")
    replay = read_json(OUT_DIR / "duplicate_replay_outcome_classification.json")
    count = read_json(OUT_DIR / "issue_repair_count_gate_results.json")
    matrix = read_json(OUT_DIR / "issue_repair_count_gate_criteria_matrix.json")
    update = read_json(OUT_DIR / "issue_derived_repair_count_update.json")
    native = read_json(OUT_DIR / "native_external_repair_count_preservation.json")
    duplicate = read_json(OUT_DIR / "duplicate_or_already_counted_check.json")
    canonical = read_json(OUT_DIR / "canonical_issue_repair_record_freezegun.json")
    final = read_json(OUT_DIR / "batch065_final_decision.json")
    claim = read_json(OUT_DIR / "claim_boundary.json")
    package = read_json(OUT_DIR / "package_verification.json")
    public_language = read_json(OUT_DIR / "public_language_neutrality_check_batch065.json")
    summary_safety = read_json(OUT_DIR / "public_summary_claim_safety_check_batch065.json")
    post_count = read_json(OUT_DIR / "post_count_state_capture_batch065.json")
    topology = read_json(OUT_DIR / "repo_topology_public_readiness_review_batch065.json")
    duplicate_functions = read_json(OUT_DIR / "duplicate_function_review_batch065.json")
    permanent = read_json(OUT_DIR / "permanent_fix_queue_after_batch065.json")
    reactome_map = read_json(OUT_DIR / "reactome_tld_isomorphic_engineering_map_batch065.json")
    wrapper = read_json(OUT_DIR / "self_maintaining_wrapper_capability_upgrade_review_batch065.json")

    expect(errors, artifact.get("status") == "PASS", "Batch064 artifact verification did not pass")
    expect(errors, artifact.get("zip_sha256") == "b798b25fae2ee63dec57cdf8a2e227c197fb186539bbcdbbda2b5d126c9f5580", "Batch064 artifact SHA mismatch")
    expect(errors, artifact.get("zip_size_bytes") == 67818, "Batch064 artifact size mismatch")
    expect(errors, artifact.get("zip_entry_count") == 128, "Batch064 artifact entry count mismatch")
    expect(errors, artifact.get("artifact_manifest", {}).get("status") == "PASS", "Batch064 artifact manifest failed")
    expect(errors, artifact.get("output_manifest", {}).get("status") == "PASS", "Batch064 output manifest failed")
    expect(errors, preservation.get("issue_derived_repair_count_before_batch065") == 3, "Issue-derived repair count before Batch065 should be 3")
    expect(errors, preservation.get("native_external_repair_count") == 4, "Native external repair count changed")
    expect(errors, preservation.get("full_scoring") == "NOT_RUN/disallowed", "Full scoring changed")
    expect(errors, preservation.get("memory_lift") == "not_demonstrated", "Memory lift changed")
    expect(errors, preservation.get("self_maintaining_software") == "false/not_demonstrated", "Self-maintaining status changed")
    expect(errors, patch_preserve.get("patch_sha256") == PATCH_SHA256, "Batch064 patch SHA not preserved")
    expect(errors, patch_preserve.get("changed_files") == ["freezegun/api.py"], "Batch064 changed files not preserved")
    expect(errors, scope.get("operated_only_on_freezegun") is True, "Batch065 did not scope to Freezegun")
    expect(errors, scope.get("new_patch_generated") is False, "Batch065 must not generate a new patch")
    expect(errors, scope.get("pytest_patched") is False, "Batch065 must not patch Pytest")
    for key in ["fixed_commit_used", "future_commit_used", "pr_patch_used", "gold_patch_used", "issue_body_fix_or_workaround_text_used", "modern_fixed_source_used", "test_modified", "fixture_modified", "synthetic_test_used", "new_patch_generation"]:
        expect(errors, forbidden.get(key) is False, f"Forbidden evidence expected {key}=false")

    expect(errors, commit.get("status") == "PASS" and commit.get("resolved_head") == "df263dcec48f43154a5873eb0dff2d4ba94374da", "Duplicate commit verification failed")
    expect(errors, workspace.get("status") == "PASS" and workspace.get("native_test_path_exists") is True and workspace.get("source_path_exists") is True, "Duplicate workspace custody failed")
    expect(errors, provider.get("classification") == "provider_runtime_recovered_from_declared_metadata", "Provider/runtime setup not recovered from declared metadata")
    expect(errors, provider.get("provider_setup_is_repair_success") is False, "Provider setup must not be counted as repair")
    expect(errors, prerepair.get("status") == "PASS", "Pre-repair duplicate failure did not reproduce")
    expect(errors, prerepair.get("pre_repair_focused_failures_reproduced") is True, "Focused pre-repair failures did not reproduce")
    expect(errors, prerepair.get("pre_repair_full_target_failed") is True, "Full target did not fail pre-repair")
    expect(errors, prerepair.get("no_source_or_test_mutation_before_replay") is True, "Source/test mutation occurred before pre-repair replay")
    expect(errors, identity.get("patch_sha256") == PATCH_SHA256 and identity.get("patch_matches_batch064") is True, "Patch identity does not match Batch064")
    expect(errors, patch_app.get("status") == "PASS" and patch_app.get("changed_files") == ["freezegun/api.py"], "Patch did not apply cleanly to expected source file")
    expect(errors, source_only.get("source_only") is True, "Patch is not source-only")
    expect(errors, tests.get("test_files_modified") == [], "Tests were modified")
    expect(errors, fixtures.get("fixture_files_modified") == [], "Fixtures were modified")
    expect(errors, deps.get("dependency_or_build_files_modified") == [], "Dependency/build files were modified")
    expect(errors, replay.get("classification") == "duplicate_clean_replay_pass", "Duplicate replay did not pass")
    expect(errors, replay.get("full_target_returncode") == 0, "Duplicate full target did not pass")
    expect(errors, count.get("count_gate_passed") is True, "Count gate did not pass")
    expect(errors, update.get("before") == 3 and update.get("after") == 4, "Issue-derived repair count did not move 3 -> 4")
    expect(errors, update.get("incremented_by_count_gate_only") is True, "Repair count was not incremented by count gate only")
    expect(errors, native.get("native_external_repair_count") == 4 and native.get("unchanged") is True, "Native external repair count not preserved")
    expect(errors, duplicate.get("already_counted_before_batch065") is False and duplicate.get("duplicate_of_existing_repair") is False, "Candidate duplicate/already-counted check failed")
    expect(errors, canonical.get("counted_issue_derived_repair") is True, "Canonical Freezegun repair record was not counted")
    expect(errors, all(row.get("passed") is True for row in matrix.get("criteria", [])), "Count gate criteria matrix has failures")
    expect(errors, final.get("status") == "PASS", "Final decision did not pass")
    expect(errors, final.get("current_protocol") == CURRENT_PROTOCOL, "Current protocol changed")
    expect(errors, final.get("issue_derived_repair_count_before_batch065") == 3 and final.get("issue_derived_repair_count_after_batch065") == 4, "Final count boundary wrong")
    expect(errors, final.get("native_external_repair_count") == 4, "Final native count changed")
    expect(errors, final.get("full_scoring") == "NOT_RUN/disallowed", "Final full scoring changed")
    expect(errors, final.get("memory_lift") == "not_demonstrated", "Final memory lift changed")
    expect(errors, final.get("self_maintaining_software") == "false/not_demonstrated", "Final self-maintaining changed")
    expect(errors, final.get("new_patch_generated") is False, "Final decision says new patch generated")
    expect(errors, final.get("next_allowed_action") in {"batch066_next_issue_repair_candidate_selection_or_pytest_recovery", "batch063b_pytest_provider_runtime_recovery", "batch058d_seed_discovery_expansion", "batch062b_repo_hygiene_utility_consolidation_planning"}, "Invalid next allowed action after count pass")
    expect(errors, claim.get("full_scoring_run") is False, "Claim boundary says full scoring ran")
    for key in ["raw_zip_payload_committed", "runtime_workspaces_committed", "source_checkouts_committed", "venvs_committed", "caches_committed"]:
        expect(errors, package.get(key) is False, f"Package verification expected {key}=false")
    expect(errors, public_language.get("status") == "PASS", "Public language neutrality failed")
    expect(errors, summary_safety.get("repair_count_increments_only_through_duplicate_replay_and_count_gate") is True, "Public summary safety missing count boundary")
    expect(errors, post_count.get("does_not_modify_proof_gate") is True, "Post-count acceleration modified proof gate")
    expect(errors, topology.get("no_repo_refactor_performed") is True, "Repo topology review implies a refactor was performed")
    expect(errors, duplicate_functions.get("no_repo_refactor_performed") is True, "Duplicate-function review implies a refactor was performed")
    expect(errors, permanent.get("advisory_only") is True, "Permanent fix queue is not advisory-only")
    expect(errors, reactome_map.get("not_repair_evidence") is True, "Infrastructure/governance map must not be repair evidence")
    expect(errors, wrapper.get("self_maintaining_software_demonstrated") is False, "Wrapper review overclaimed self-maintaining software")

    audit_public_summary(errors)
    audit_git_status(errors)
    run_python_script("scripts/audit_batch064_freezegun_source_only_patch_gate.py", errors)
    proc = subprocess.run([sys.executable, "scripts/controllergate_audit.py", "--protocol", "current"], cwd=ROOT, text=True, capture_output=True, check=False)
    expect(errors, proc.returncode == 0, f"current protocol audit failed: {proc.stdout[-1000:]} {proc.stderr[-1000:]}")
    proc = subprocess.run([sys.executable, "scripts/controllergate_run.py", "--protocol", "current", "--dry-run"], cwd=ROOT, text=True, capture_output=True, check=False)
    expect(errors, proc.returncode == 0, f"current protocol dry-run failed: {proc.stdout[-1000:]} {proc.stderr[-1000:]}")

    if errors:
        print("FAIL:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Batch065 duplicate clean replay count gate Freezegun audit PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
