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


OUT_DIR = ROOT / "outputs" / "post_v2_37_hardening_batch060f_audioread_provider_backend_capsule_replay"
CURRENT_PROTOCOL = "v2.14"
EXPECTED_BATCH058B_SHA256 = "d01af2290a1389f47ad1537952002188e2cff162872f9f42d6ed5ddaaa207194"
EXPECTED_BATCH058B_SIZE = 73442
EXPECTED_BATCH058B_ENTRY_COUNT = 94
EXPECTED_BATCH058B_ARTIFACT_MANIFEST_CHECKED = 93
EXPECTED_BATCH058B_OUTPUT_MANIFEST_CHECKED = 85
EXPECTED_PATCH_SHA256 = "c010f384c7d4f6e77d3b861a6533675fb0f9e589cfedc3705a7847659e7428cd"

REQUIRED_FILES = [
    "batch058b_artifact_ingestion_summary.json",
    "batch058b_artifact_sha256_verification.json",
    "artifact_sha256_verification.json",
    "batch058b_result_preservation.json",
    "batch058b_seed_expansion_preservation.json",
    "batch058b_candidate_selection_preservation.json",
    "batch058b_claim_boundary_preservation.json",
    "batch058b_next_action_boundary.json",
    "audioread_prior_branch_inventory.json",
    "audioread_batch060_patch_preservation.json",
    "audioread_batch060_partial_improvement_preservation.json",
    "audioread_batch060b_provider_classification_preservation.json",
    "audioread_failed_repair_branch_record_batch060f.json",
    "audioread_decision_time_input_manifest.json",
    "audioread_forbidden_evidence_audit.json",
    "audioread_issue_body_leakage_boundary.json",
    "audioread_label_blindness_check.json",
    "audioread_gold_patch_exclusion_check.json",
    "audioread_future_evidence_exclusion_check.json",
    "audioread_workspace_manifest.json",
    "audioread_commit_verification.json",
    "audioread_workspace_custody_check.json",
    "audioread_baseline_source_hashes.json",
    "audioread_command_context.json",
    "audioread_command_normalization.json",
    "audioread_prerepair_replay_command.txt",
    "audioread_prerepair_replay_log_raw.txt",
    "audioread_prerepair_replay_result.json",
    "audioread_prerepair_failure_signature_extract.json",
    "audioread_provider_backend_capsule_plan.json",
    "audioread_declared_dependency_map.json",
    "audioread_declared_runtime_map.json",
    "audioread_declared_test_command_map.json",
    "audioread_declared_optional_backend_map.json",
    "audioread_audio_backend_probe_plan.json",
    "audioread_provider_backend_safety_check.json",
    "audioread_provider_backend_non_repair_boundary.json",
    "audioread_provider_probe_log_raw.txt",
    "audioread_provider_probe_results.json",
    "audioread_backend_tool_probe_results.json",
    "audioread_python_backend_probe_results.json",
    "audioread_provider_install_attempt.json",
    "audioread_provider_install_not_run_reason.txt",
    "audioread_provider_backend_recovery_result.json",
    "audioread_exact_prior_patch_identity_check.json",
    "audioread_exact_prior_patch_application_result.json",
    "audioread_exact_prior_patch_changed_files_manifest.json",
    "audioread_exact_prior_patch_source_only_check.json",
    "audioread_exact_prior_patch_test_mutation_check.json",
    "audioread_exact_prior_patch_fixture_mutation_check.json",
    "audioread_exact_prior_patch_dependency_file_mutation_check.json",
    "audioread_available_backends_probe_result.json",
    "audioread_replay_matrix_plan.json",
    "audioread_original_target_replay_after_prior_patch_command.txt",
    "audioread_original_target_replay_after_prior_patch_log_raw.txt",
    "audioread_split_node_replay_results.json",
    "audioread_failure_signature_comparison.json",
    "audioread_replay_matrix_results.json",
    "audioread_amds_full_bug_tree_state_batch060f.json",
    "audioread_bug_tree_node_registry_batch060f.json",
    "audioread_bug_tree_edge_registry_batch060f.json",
    "audioread_secondary_bug_registry_batch060f.json",
    "audioread_provider_dependency_branch_registry_batch060f.json",
    "audioread_interpreter_behavior_branch_registry_batch060f.json",
    "audioread_unrecoverable_branch_registry_batch060f.json",
    "audioread_repairable_branch_registry_batch060f.json",
    "audioread_next_action_frontier_batch060f.json",
    "optional_backend_missing_pattern_update.json",
    "provider_backend_capsule_pattern_library_update.json",
    "removed_stdlib_exposes_backend_layer_pattern.json",
    "partial_improvement_to_provider_capsule_route.json",
    "provider_dependency_terminal_state_update.json",
    "recurring_bottleneck_trend_report_batch060f.json",
    "self_maintenance_runtime_progress_review_batch060f.json",
    "audioread_provider_backend_outcome_classification.json",
    "audioread_repair_count_eligibility_assessment.json",
    "project_health_review_batch060f.json",
    "capability_maturity_scorecard_batch060f.json",
    "version_progress_grade_batch060f.json",
    "strategic_direction_check_batch060f.json",
    "proof_milestone_distance_report_batch060f.json",
    "regression_and_drift_watch_batch060f.json",
    "self_maintenance_readiness_review_batch060f.json",
    "next_highest_impact_action_report_batch060f.json",
    "tld_governance_boundary_batch060f.json",
    "reactome_provider_capsule_boundary_batch060f.json",
    "internal_theory_to_engineering_translation_batch060f.json",
    "public_language_neutrality_check_batch060f.json",
    "public_summary_claim_safety_check_batch060f.json",
    "batch060f_final_decision.json",
    "batch060f_summary.md",
    "claim_boundary.json",
    "audit.json",
    "package_verification.json",
    "SHA256SUMS.txt",
]

ALLOWED_PROVIDER_STATUSES = {
    "provider_backend_capsule_recovered",
    "provider_backend_capsule_unavailable",
    "provider_backend_capsule_manual_review_needed",
}

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


def public_batch060f_block(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    marker = "Batch060f is the latest Audioread branch-replay boundary."
    start = text.find(marker)
    if start == -1:
        return ""
    next_marker = text.find("Batch058b is the latest seed-discovery boundary.", start)
    if next_marker == -1:
        next_marker = min(len(text), start + 3000)
    return text[start:next_marker]


def audit_public_summary(errors: list[str]) -> None:
    for rel in [
        "README.md",
        "docs/current_status.md",
        "controllergate_v1_7_beta/reports/critic_review_package/shareable_summary.md",
    ]:
        block = public_batch060f_block(ROOT / rel)
        expect(errors, bool(block), f"missing Batch060f public summary block in {rel}")
        for phrase in [
            "Provider/backend setup is not repair success.",
            "Applying an exact prior patch for branch replay is not a new repair.",
            "Repair count increments require duplicate clean replay and count gate.",
            "Self-maintaining software remains false/not_demonstrated.",
        ]:
            expect(errors, phrase in block, f"Batch060f public summary missing {phrase!r} in {rel}")
        lowered = block.lower()
        for term in PUBLIC_FORBIDDEN_TERMS:
            expect(errors, term.lower() not in lowered, f"Batch060f public summary contains internal term {term!r} in {rel}")


def main() -> int:
    errors: list[str] = []
    if not OUT_DIR.is_dir():
        print(f"FAIL: missing output directory: {OUT_DIR.relative_to(ROOT)}")
        return 1
    for rel in REQUIRED_FILES:
        if not (OUT_DIR / rel).is_file():
            errors.append(f"missing required Batch060f output: {rel}")
    if not errors:
        manifest = verify_manifest(OUT_DIR)
        if manifest.get("status") != "PASS":
            errors.append(f"Batch060f SHA256SUMS verification failed: {manifest}")
    if errors:
        print("FAIL:")
        for error in errors:
            print(f"- {error}")
        return 1

    artifact = read_json(OUT_DIR / "batch058b_artifact_sha256_verification.json")
    ingest = read_json(OUT_DIR / "batch058b_artifact_ingestion_summary.json")
    preserved = read_json(OUT_DIR / "batch058b_result_preservation.json")
    next_boundary = read_json(OUT_DIR / "batch058b_next_action_boundary.json")
    prior = read_json(OUT_DIR / "audioread_prior_branch_inventory.json")
    patch_preservation = read_json(OUT_DIR / "audioread_batch060_patch_preservation.json")
    evidence = read_json(OUT_DIR / "audioread_decision_time_input_manifest.json")
    forbidden = read_json(OUT_DIR / "audioread_forbidden_evidence_audit.json")
    issue_leakage = read_json(OUT_DIR / "audioread_issue_body_leakage_boundary.json")
    gold = read_json(OUT_DIR / "audioread_gold_patch_exclusion_check.json")
    future = read_json(OUT_DIR / "audioread_future_evidence_exclusion_check.json")
    label = read_json(OUT_DIR / "audioread_label_blindness_check.json")
    workspace = read_json(OUT_DIR / "audioread_workspace_manifest.json")
    commit = read_json(OUT_DIR / "audioread_commit_verification.json")
    prerepair = read_json(OUT_DIR / "audioread_prerepair_replay_result.json")
    signature = read_json(OUT_DIR / "audioread_prerepair_failure_signature_extract.json")
    provider_plan = read_json(OUT_DIR / "audioread_provider_backend_capsule_plan.json")
    provider_safety = read_json(OUT_DIR / "audioread_provider_backend_safety_check.json")
    provider_recovery = read_json(OUT_DIR / "audioread_provider_backend_recovery_result.json")
    provider_install = read_json(OUT_DIR / "audioread_provider_install_attempt.json")
    patch_identity = read_json(OUT_DIR / "audioread_exact_prior_patch_identity_check.json")
    patch_apply = read_json(OUT_DIR / "audioread_exact_prior_patch_application_result.json")
    changed = read_json(OUT_DIR / "audioread_exact_prior_patch_changed_files_manifest.json")
    source_only = read_json(OUT_DIR / "audioread_exact_prior_patch_source_only_check.json")
    test_mutation = read_json(OUT_DIR / "audioread_exact_prior_patch_test_mutation_check.json")
    fixture_mutation = read_json(OUT_DIR / "audioread_exact_prior_patch_fixture_mutation_check.json")
    dependency_mutation = read_json(OUT_DIR / "audioread_exact_prior_patch_dependency_file_mutation_check.json")
    replay = read_json(OUT_DIR / "audioread_replay_matrix_results.json")
    comparison = read_json(OUT_DIR / "audioread_failure_signature_comparison.json")
    outcome = read_json(OUT_DIR / "audioread_provider_backend_outcome_classification.json")
    count_gate = read_json(OUT_DIR / "audioread_repair_count_eligibility_assessment.json")
    amds = read_json(OUT_DIR / "audioread_amds_full_bug_tree_state_batch060f.json")
    tld_boundary = read_json(OUT_DIR / "tld_governance_boundary_batch060f.json")
    reactome_boundary = read_json(OUT_DIR / "reactome_provider_capsule_boundary_batch060f.json")
    translation = read_json(OUT_DIR / "internal_theory_to_engineering_translation_batch060f.json")
    public_language = read_json(OUT_DIR / "public_language_neutrality_check_batch060f.json")
    public_claim = read_json(OUT_DIR / "public_summary_claim_safety_check_batch060f.json")
    final = read_json(OUT_DIR / "batch060f_final_decision.json")
    claim = read_json(OUT_DIR / "claim_boundary.json")
    package = read_json(OUT_DIR / "package_verification.json")

    expect(errors, artifact.get("status") == "PASS", "Batch058b artifact verification did not pass")
    expect(errors, artifact.get("zip_sha256") == EXPECTED_BATCH058B_SHA256, "Batch058b artifact SHA mismatch")
    expect(errors, artifact.get("artifact_sha256") == EXPECTED_BATCH058B_SHA256, "Batch058b artifact digest mismatch")
    expect(errors, artifact.get("zip_size_bytes") == EXPECTED_BATCH058B_SIZE, "Batch058b artifact size mismatch")
    expect(errors, artifact.get("zip_entry_count") == EXPECTED_BATCH058B_ENTRY_COUNT, "Batch058b artifact entry count mismatch")
    expect(errors, artifact.get("artifact_manifest", {}).get("checked") == EXPECTED_BATCH058B_ARTIFACT_MANIFEST_CHECKED, "Batch058b artifact manifest checked count mismatch")
    expect(errors, artifact.get("output_manifest", {}).get("checked") == EXPECTED_BATCH058B_OUTPUT_MANIFEST_CHECKED, "Batch058b output manifest checked count mismatch")
    expect(errors, artifact.get("artifact_manifest", {}).get("status") == "PASS", "Batch058b artifact manifest failed")
    expect(errors, artifact.get("output_manifest", {}).get("status") == "PASS", "Batch058b output manifest failed")
    for key in ["unsafe_path_count", "duplicate_path_count", "zip_pycache_entries", "zip_pyc_entries"]:
        expect(errors, artifact.get(key) == 0, f"Batch058b artifact has non-zero {key}")
    expect_false(errors, artifact, "raw_zip_bytes_ingested", "Batch058b artifact verification")
    expect_false(errors, artifact, "zip_payload_committed", "Batch058b artifact verification")
    expect(errors, ingest.get("status") == "PASS" and ingest.get("official_output_ingest", {}).get("status") == "PASS", "Batch058b ingest did not pass")
    expect(errors, preserved.get("batch058b_final_decision_status") == "PASS", "Batch058b final decision not preserved")
    expect(errors, next_boundary.get("status") == "PASS", "Batch058b next action boundary not preserved")

    expect(errors, prior.get("candidate_id") == "audioread_144_py313_aifc_removed", "wrong Audioread candidate id")
    expect(errors, prior.get("candidate_sha") == "577f8e2cbe99f33dd7d236deb1626e372f4762e9", "wrong Audioread candidate SHA")
    expect(errors, prior.get("prior_patch_sha256") == EXPECTED_PATCH_SHA256, "prior patch SHA not preserved")
    expect(errors, patch_preservation.get("patch_identity_verified") is True, "prior patch identity not verified")
    expect(errors, patch_preservation.get("batch060_patch_altered", False) is False, "Batch060 patch was altered")
    expect(errors, "fixed commits" in evidence.get("forbidden_evidence", []), "forbidden evidence list missing fixed commits")
    for label_name, obj in [
        ("forbidden", forbidden),
        ("issue_body", issue_leakage),
        ("gold", gold),
        ("future", future),
        ("label", label),
    ]:
        expect(errors, obj.get("status") == "PASS", f"{label_name} evidence audit did not pass")
        for key in [
            "fixed_commit_used",
            "future_commit_used",
            "pr_patch_used",
            "gold_patch_used",
            "issue_body_fix_or_workaround_text_persisted",
            "labels_or_hidden_state_used",
        ]:
            if key in obj:
                expect_false(errors, obj, key, label_name)

    expect(errors, workspace.get("status") == "PASS", "Audioread workspace manifest did not pass")
    expect(errors, workspace.get("workspace_outside_repo") is True, "Audioread workspace was not recorded outside repo")
    expect(errors, commit.get("status") == "PASS", "Audioread commit verification did not pass")
    expect(errors, prerepair.get("failure_reproduced") is True, "pre-repair aifc failure was not reproduced")
    expect(errors, prerepair.get("status") == "pre_repair_failure_reproduced_module_aifc_missing", "pre-repair failure status mismatch")
    expect(errors, signature.get("exception_type") == "ModuleNotFoundError", "pre-repair exception type mismatch")
    expect(errors, signature.get("normalized_failure") == "No module named 'aifc'", "pre-repair normalized failure mismatch")

    expect(errors, provider_plan.get("status") == "PASS", "provider/backend capsule plan did not pass")
    expect(errors, provider_safety.get("status") == "PASS", "provider/backend safety check did not pass")
    expect(errors, provider_safety.get("undeclared_backend_install_forbidden") is True, "undeclared backend install was not forbidden")
    expect(errors, provider_recovery.get("status") in ALLOWED_PROVIDER_STATUSES, "provider/backend recovery status is not allowed")
    expect(errors, provider_recovery.get("provider_setup_counted_as_repair") is False, "provider setup counted as repair")
    expect(errors, provider_install.get("status") in {"NOT_RUN", "PASS"}, "provider install status is unexpected")
    if provider_install.get("status") == "PASS":
        expect(errors, provider_plan.get("declared_external_backend_found") is True, "provider install ran without declared backend")

    expect(errors, patch_identity.get("status") == "PASS", "exact prior patch identity did not pass")
    expect(errors, patch_identity.get("patch_sha256") == EXPECTED_PATCH_SHA256, "exact prior patch SHA mismatch")
    expect(errors, patch_identity.get("patch_regenerated") is False, "prior patch was regenerated")
    expect(errors, patch_identity.get("patch_modified") is False, "prior patch was modified")
    expect(errors, patch_apply.get("status") == "PASS", "exact prior patch application failed")
    expect(errors, changed.get("changed_files") == ["audioread/rawread.py"], f"unexpected changed files: {changed.get('changed_files')!r}")
    expect(errors, source_only.get("status") == "PASS", "source-only check did not pass")
    expect_false(errors, test_mutation, "tests_modified", "exact prior patch")
    expect_false(errors, fixture_mutation, "fixtures_modified", "exact prior patch")
    expect_false(errors, dependency_mutation, "dependency_files_modified", "exact prior patch")

    expect(errors, replay.get("status") == "PASS", "replay matrix did not pass")
    expect(errors, replay.get("baseline_no_patch_no_provider") == "pre_repair_failure_reproduced_module_aifc_missing", "baseline replay matrix state mismatch")
    expect(errors, replay.get("duplicate_replay_run") is False, "duplicate replay should not run in Batch060f")
    expect(errors, replay.get("count_gate_run") is False, "count gate should not run in Batch060f")
    expect(errors, comparison.get("primary_import_crash_removed_by_prior_patch") is True, "prior patch did not remove primary import crash in branch replay")
    expect(errors, outcome.get("status") == "PASS", "Audioread outcome classification did not pass")
    expect(errors, count_gate.get("eligible_for_repair_count_increment_now") is False, "repair count became eligible inside Batch060f")
    expect(errors, amds.get("status") == "PASS", "Audioread bug-tree state did not pass")
    expect(errors, amds.get("next_allowed_action") == final.get("next_allowed_action"), "next action mismatch between bug tree and final decision")

    expect(errors, tld_boundary.get("internal_metadata_only") is True, "TLD boundary was not internal metadata only")
    expect(errors, reactome_boundary.get("not_repair_evidence") is True, "provider capsule boundary was treated as repair evidence")
    expect(errors, translation.get("internal_labels_do_not_change_proof_rules") is True, "internal labels changed proof rules")
    expect(errors, public_language.get("status") == "PASS", "public language neutrality check failed")
    expect(errors, public_claim.get("status") == "PASS", "public claim safety check failed")

    expect(errors, final.get("status") == "PASS", "Batch060f final status not PASS")
    expect(errors, final.get("batch058b_ingest_status") == "PASS", "Batch058b ingest not reflected in final decision")
    expect(errors, final.get("current_protocol") == CURRENT_PROTOCOL, "current protocol changed")
    expect(errors, final.get("issue_derived_repair_count") == 3, "issue-derived repair count changed")
    expect(errors, final.get("native_external_repair_count") == 4, "native external repair count changed")
    expect(errors, final.get("full_scoring") == "NOT_RUN/disallowed", "full scoring changed")
    expect(errors, final.get("memory_lift") == "not_demonstrated", "memory lift changed")
    expect(errors, final.get("self_maintaining_software") == "false/not_demonstrated", "self-maintaining software claim changed")
    expect(errors, final.get("patch_generated") is False, "Batch060f generated a new patch")
    expect(errors, final.get("new_source_patch_generated") is False, "Batch060f generated a new source patch")
    expect(errors, final.get("batch060_patch_altered") is False, "Batch060 patch altered")
    expect(errors, final.get("exact_prior_patch_applied_for_branch_replay") is True, "exact prior patch branch replay not recorded")
    expect(errors, final.get("duplicate_replay_run") is False, "duplicate replay ran")
    expect(errors, final.get("count_gate_run") is False, "count gate ran")
    expect(errors, final.get("repair_count_increment") is False, "repair count incremented")
    expect(errors, final.get("next_allowed_action") in {
        "batch060g_audioread_duplicate_clean_replay_and_issue_repair_count_gate",
        "batch058c_seed_discovery_expansion_or_salvage_reassessment",
        "batch060g_audioread_secondary_source_decomposition",
    }, "unexpected Batch060f next allowed action")

    for key in [
        "new_source_patch_generated",
        "batch060_patch_altered",
        "tests_mutated",
        "fixtures_mutated",
        "dependency_build_files_modified_as_source_repair",
        "duplicate_replay_run",
        "count_gate_run",
        "repair_count_increment",
        "provider_backend_setup_counted_as_repair",
        "partial_improvement_counted_as_repair",
        "repo_refactor_performed",
        "workflow_deleted",
        "source_behavior_changed_outside_branch_replay_workspace",
    ]:
        expect_false(errors, claim, key, "claim boundary")
    expect(errors, claim.get("current_protocol") == CURRENT_PROTOCOL, "claim boundary current protocol changed")
    expect(errors, package.get("status") == "PASS", "package verification did not pass")
    for key in ["raw_zip_payload_committed", "runtime_workspaces_committed", "source_checkouts_committed", "venvs_committed", "caches_committed"]:
        expect_false(errors, package, key, "package verification")

    audit_public_summary(errors)
    audit_git_status(errors)

    if errors:
        print("FAIL:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Batch060f Audioread provider/backend capsule replay audit PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
