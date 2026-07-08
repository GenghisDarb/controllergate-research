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


OUT_DIR = ROOT / "outputs" / "post_v2_37_hardening_batch061_duplicate_clean_replay_count_gate_cloudpickle_wave_3"
CURRENT_PROTOCOL = "v2.14"
CANDIDATE_ID = "cloudpickle_507_py313_typevar_distutils"
CLOUDPICKLE_SHA = "a76f0812ccdbbd1397f36d536dc4d57b6d0557d6"
PATCH_SHA = "a06b5343f41a49daaa9d6902513966c6796e44124640ba29fcf80ede99d06e63"
BATCH060D_SHA = "d3b2cb2b7f64dc4d2fe68b4bc11da5ca5200dea8c8b2586087c9699e6ec1e5da"
BATCH060D_SIZE = 73095
BATCH060D_ENTRY_COUNT = 102
BATCH060D_ARTIFACT_MANIFEST_CHECKED = 101
BATCH060D_OUTPUT_MANIFEST_CHECKED = 100

REQUIRED_FILES = [
    "batch060d_artifact_ingestion_summary.json",
    "batch060d_artifact_sha256_verification.json",
    "batch060d_result_preservation.json",
    "batch060d_cloudpickle_patch_preservation.json",
    "batch060d_amds_bug_tree_preservation.json",
    "batch060d_project_health_preservation.json",
    "batch060d_claim_boundary_preservation.json",
    "batch060d_next_action_boundary.json",
    "batch061_decision_time_input_manifest.json",
    "batch061_forbidden_evidence_audit.json",
    "batch061_issue_body_leakage_boundary.json",
    "batch061_label_blindness_check.json",
    "batch061_gold_patch_exclusion_check.json",
    "batch061_future_evidence_exclusion_check.json",
    "duplicate_workspace_manifest.json",
    "duplicate_commit_verification.json",
    "duplicate_workspace_custody_check.json",
    "duplicate_candidate_source_baseline_hashes.json",
    "duplicate_provider_runtime_plan.json",
    "duplicate_provider_runtime_result.json",
    "duplicate_prerepair_class_dict_command.txt",
    "duplicate_prerepair_class_dict_log_raw.txt",
    "duplicate_prerepair_class_dict_result.json",
    "duplicate_prerepair_full_target_command.txt",
    "duplicate_prerepair_full_target_log_raw.txt",
    "duplicate_prerepair_full_target_result.json",
    "duplicate_prerepair_failure_signature_extract.json",
    "duplicate_patch_identity_check.json",
    "duplicate_patch_application_result.json",
    "duplicate_changed_files_manifest.json",
    "duplicate_source_only_check.json",
    "duplicate_test_mutation_check.json",
    "duplicate_fixture_mutation_check.json",
    "duplicate_dependency_file_mutation_check.json",
    "duplicate_patch_post_apply_source_hashes.json",
    "duplicate_postpatch_class_dict_command.txt",
    "duplicate_postpatch_class_dict_log_raw.txt",
    "duplicate_postpatch_class_dict_result.json",
    "duplicate_postpatch_distutils_family_command.txt",
    "duplicate_postpatch_distutils_family_log_raw.txt",
    "duplicate_postpatch_distutils_family_result.json",
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
    "canonical_issue_repair_record_cloudpickle.json",
    "proof_ledger_cloudpickle_entry.json",
    "proof_ledger_update_summary.json",
    "duplicate_replay_count_gate_pattern_library.json",
    "source_only_success_to_count_gate_route.json",
    "proof_milestone_pattern_update.json",
    "project_health_review_batch061.json",
    "capability_maturity_scorecard_batch061.json",
    "version_progress_grade_batch061.json",
    "self_maintenance_readiness_review_batch061.json",
    "recurring_bottleneck_trend_report_batch061.json",
    "next_highest_impact_action_report_batch061.json",
    "public_language_neutrality_check.json",
    "public_summary_claim_safety_check.json",
    "internal_vs_public_language_boundary.json",
    "batch061_final_decision.json",
    "batch062_next_action_recommendation.json",
    "batch058b_seed_discovery_wave_3_expansion_recommendation.json",
    "batch060f_audioread_provider_backend_capsule_replay_recommendation.json",
    "memory_lift_future_plan_recommendation.json",
    "batch061_summary.md",
    "claim_boundary.json",
    "audit.json",
    "package_verification.json",
    "artifact_sha256_verification.json",
    "SHA256SUMS.txt",
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

PUBLIC_FORBIDDEN_TERMS = [
    "TLD",
    "TORUS",
    "chromosomal",
    "biological",
    "ToT-BULB",
    "metrological immune system",
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


def audit_public_docs(errors: list[str]) -> None:
    required = [
        "Batch061",
        "duplicate clean replay",
        "issue-derived repair count",
        "Workflow success is not equivalent to repair success.",
        "Provider/runtime recovery is not repair success.",
        "Self-maintaining software remains false/not_demonstrated.",
    ]
    paths = [
        ROOT / "README.md",
        ROOT / "docs" / "current_status.md",
        ROOT / "controllergate_v1_7_beta" / "reports" / "critic_review_package" / "shareable_summary.md",
    ]
    for path in paths:
        text = path.read_text(encoding="utf-8")
        for phrase in required:
            expect(errors, phrase in text, f"public summary missing {phrase!r} in {path.relative_to(ROOT)}")
        for term in PUBLIC_FORBIDDEN_TERMS:
            expect(errors, term.lower() not in text.lower(), f"public summary contains internal term {term!r} in {path.relative_to(ROOT)}")


def main() -> int:
    errors: list[str] = []
    if not OUT_DIR.is_dir():
        print(f"FAIL: missing output directory: {OUT_DIR.relative_to(ROOT)}")
        return 1
    for rel in REQUIRED_FILES:
        if not (OUT_DIR / rel).is_file():
            errors.append(f"missing required Batch061 output: {rel}")
    if not errors:
        manifest = verify_manifest(OUT_DIR)
        if manifest.get("status") != "PASS":
            errors.append(f"Batch061 SHA256SUMS verification failed: {manifest}")
    if errors:
        print("FAIL:")
        for error in errors:
            print(f"- {error}")
        return 1

    artifact = read_json(OUT_DIR / "batch060d_artifact_sha256_verification.json")
    ingest = read_json(OUT_DIR / "batch060d_artifact_ingestion_summary.json")
    preserved = read_json(OUT_DIR / "batch060d_result_preservation.json")
    patch_preserved = read_json(OUT_DIR / "batch060d_cloudpickle_patch_preservation.json")
    next_boundary = read_json(OUT_DIR / "batch060d_next_action_boundary.json")
    decision_inputs = read_json(OUT_DIR / "batch061_decision_time_input_manifest.json")
    forbidden = read_json(OUT_DIR / "batch061_forbidden_evidence_audit.json")
    leakage = read_json(OUT_DIR / "batch061_issue_body_leakage_boundary.json")
    gold = read_json(OUT_DIR / "batch061_gold_patch_exclusion_check.json")
    future = read_json(OUT_DIR / "batch061_future_evidence_exclusion_check.json")
    workspace = read_json(OUT_DIR / "duplicate_workspace_manifest.json")
    commit = read_json(OUT_DIR / "duplicate_commit_verification.json")
    custody = read_json(OUT_DIR / "duplicate_workspace_custody_check.json")
    provider = read_json(OUT_DIR / "duplicate_provider_runtime_result.json")
    pre_class = read_json(OUT_DIR / "duplicate_prerepair_class_dict_result.json")
    pre_full = read_json(OUT_DIR / "duplicate_prerepair_full_target_result.json")
    pre_sig = read_json(OUT_DIR / "duplicate_prerepair_failure_signature_extract.json")
    patch_identity = read_json(OUT_DIR / "duplicate_patch_identity_check.json")
    patch_apply = read_json(OUT_DIR / "duplicate_patch_application_result.json")
    changed = read_json(OUT_DIR / "duplicate_changed_files_manifest.json")
    source_only = read_json(OUT_DIR / "duplicate_source_only_check.json")
    test_mutation = read_json(OUT_DIR / "duplicate_test_mutation_check.json")
    fixture_mutation = read_json(OUT_DIR / "duplicate_fixture_mutation_check.json")
    dependency_mutation = read_json(OUT_DIR / "duplicate_dependency_file_mutation_check.json")
    post_class = read_json(OUT_DIR / "duplicate_postpatch_class_dict_result.json")
    post_dist = read_json(OUT_DIR / "duplicate_postpatch_distutils_family_result.json")
    post_full = read_json(OUT_DIR / "duplicate_postpatch_full_target_result.json")
    outcome = read_json(OUT_DIR / "duplicate_replay_outcome_classification.json")
    gate_plan = read_json(OUT_DIR / "issue_repair_count_gate_plan.json")
    gate_results = read_json(OUT_DIR / "issue_repair_count_gate_results.json")
    criteria = read_json(OUT_DIR / "issue_repair_count_gate_criteria_matrix.json")
    count_update = read_json(OUT_DIR / "issue_derived_repair_count_update.json")
    native_count = read_json(OUT_DIR / "native_external_repair_count_preservation.json")
    duplicate_check = read_json(OUT_DIR / "duplicate_or_already_counted_check.json")
    canonical = read_json(OUT_DIR / "canonical_issue_repair_record_cloudpickle.json")
    ledger = read_json(OUT_DIR / "proof_ledger_cloudpickle_entry.json")
    pattern = read_json(OUT_DIR / "duplicate_replay_count_gate_pattern_library.json")
    health = read_json(OUT_DIR / "project_health_review_batch061.json")
    scorecard = read_json(OUT_DIR / "capability_maturity_scorecard_batch061.json")
    readiness = read_json(OUT_DIR / "self_maintenance_readiness_review_batch061.json")
    public_language = read_json(OUT_DIR / "public_language_neutrality_check.json")
    public_claims = read_json(OUT_DIR / "public_summary_claim_safety_check.json")
    internal_public = read_json(OUT_DIR / "internal_vs_public_language_boundary.json")
    final = read_json(OUT_DIR / "batch061_final_decision.json")
    claim = read_json(OUT_DIR / "claim_boundary.json")
    package = read_json(OUT_DIR / "package_verification.json")

    expect(errors, artifact.get("status") == "PASS", "Batch060d artifact verification did not pass")
    expect(errors, artifact.get("zip_sha256") == BATCH060D_SHA, "Batch060d artifact SHA mismatch")
    expect(errors, artifact.get("zip_size_bytes") == BATCH060D_SIZE, "Batch060d artifact size mismatch")
    expect(errors, artifact.get("zip_entry_count") == BATCH060D_ENTRY_COUNT, "Batch060d artifact entry count mismatch")
    expect(errors, artifact.get("artifact_manifest", {}).get("checked") == BATCH060D_ARTIFACT_MANIFEST_CHECKED, "Batch060d artifact manifest count mismatch")
    output_manifest = artifact.get("output_manifests", {}).get("post_v2_37_hardening_batch060d_cloudpickle_class_dict_patch_gate_with_amds_health_review", {})
    expect(errors, output_manifest.get("checked") == BATCH060D_OUTPUT_MANIFEST_CHECKED, "Batch060d output manifest count mismatch")
    expect(errors, output_manifest.get("status") == "PASS", "Batch060d output manifest did not PASS")
    for key in ["unsafe_path_count", "duplicate_path_count", "zip_pycache_entries", "zip_pyc_entries"]:
        expect(errors, artifact.get(key) == 0, f"Batch060d artifact has non-zero {key}")
    expect(errors, ingest.get("status") == "PASS" and ingest.get("official_output_ingest", {}).get("status") == "PASS", "Batch060d official ingest did not pass")

    expect(errors, preserved.get("issue_derived_repair_count_before_batch061") == 2, "Issue-derived count before Batch061 was not 2")
    expect(errors, preserved.get("native_external_repair_count") == 4, "Native external count changed")
    expect(errors, preserved.get("full_scoring") == "NOT_RUN/disallowed", "Full scoring status changed")
    expect(errors, preserved.get("memory_lift") == "not_demonstrated", "Memory lift status changed")
    expect(errors, preserved.get("self_maintaining_software") == "false/not_demonstrated", "Self-maintaining status changed")
    expect(errors, preserved.get("batch060d_duplicate_replay_run") is False, "Batch060d duplicate replay boundary changed")
    expect(errors, preserved.get("batch060d_count_gate_run") is False, "Batch060d count gate boundary changed")
    expect(errors, preserved.get("batch060d_batch061_candidate_count") == 1, "Batch060d Batch061 candidate count mismatch")
    expect(errors, patch_preserved.get("patch_sha256") == PATCH_SHA, "Batch060d patch SHA not preserved")
    expect(errors, patch_preserved.get("new_patch_generated_in_batch061") is False, "Batch061 generated a new patch")
    expect(errors, next_boundary.get("observed_next_allowed_action") == "batch061_duplicate_clean_replay_and_issue_repair_count_gate_wave_3", "Batch060d next action boundary mismatch")
    expect(errors, decision_inputs.get("candidate_id") == CANDIDATE_ID, "Decision-time manifest candidate mismatch")

    for obj, label in [(forbidden, "forbidden evidence"), (leakage, "issue leakage"), (gold, "gold exclusion"), (future, "future exclusion")]:
        for key in [
            "fixed_commit_used",
            "future_commit_used",
            "pr_patch_used",
            "gold_patch_used",
            "issue_body_fix_text_used",
            "helper_provided_fix_used",
            "external_repair_summary_used",
            "modern_fixed_cloudpickle_source_used",
            "tests_modified",
            "fixtures_modified",
            "synthetic_tests_added",
        ]:
            if key in obj:
                expect_false(errors, obj, key, label)

    expect(errors, workspace.get("workspace_outside_live_repo") is True, "Duplicate workspace is not outside live repo")
    expect(errors, workspace.get("workspace_outside_onedrive") is True, "Duplicate workspace uses OneDrive")
    expect(errors, commit.get("status") == "PASS" and commit.get("workspace_head_sha") == CLOUDPICKLE_SHA, "Candidate commit verification failed")
    expect(errors, commit.get("cat_file_type") == "commit", "Candidate SHA did not resolve to commit")
    expect(errors, custody.get("patch_not_pre_applied_before_prerepair_replay") is True, "Patch appears pre-applied before replay")
    expect(errors, provider.get("status") == "PASS" and provider.get("provider_runtime_recovery_counted_as_repair") is False, "Provider/runtime result boundary invalid")

    expect(errors, pre_class.get("return_code") != 0 and pre_class.get("failure_reproduced") is True, "Pre-repair class-dict failure did not reproduce")
    expect(errors, pre_full.get("return_code") != 0 and pre_full.get("failure_reproduced") is True, "Pre-repair full target did not fail")
    expect(errors, pre_sig.get("same_family_or_preserved_equivalent") is True, "Pre-repair failure family was not preserved")
    expect(errors, patch_identity.get("status") == "PASS" and patch_identity.get("patch_sha256") == PATCH_SHA, "Exact patch identity check failed")
    expect(errors, patch_identity.get("new_patch_generated") is False and patch_identity.get("patch_modified_in_batch061") is False, "Patch generation/modification boundary failed")
    expect(errors, patch_apply.get("status") == "PASS" and patch_apply.get("patch_applies_cleanly") is True, "Patch did not apply cleanly")
    expect(errors, changed.get("changed_files") == ["cloudpickle/cloudpickle.py"], "Changed files are not limited to cloudpickle.py")
    expect(errors, source_only.get("source_only") is True, "Source-only check failed")
    expect(errors, source_only.get("tests_modified") is False, "Source-only check reports tests modified")
    expect(errors, source_only.get("fixtures_modified") is False, "Source-only check reports fixtures modified")
    expect(errors, source_only.get("dependency_build_files_modified") is False, "Source-only check reports dependency/build files modified")
    expect(errors, test_mutation.get("tests_modified") is False, "Tests were modified")
    expect(errors, fixture_mutation.get("fixtures_modified") is False, "Fixtures were modified")
    expect(errors, dependency_mutation.get("dependency_build_files_modified") is False, "Dependency/build files were modified")

    expect(errors, post_class.get("return_code") == 0 and post_class.get("target_passed") is True, "Post-patch class-dict target failed")
    expect(errors, post_dist.get("return_code") == 0 and post_dist.get("family_regression_passed") is True, "Post-patch distutils-family checks failed")
    expect(errors, post_full.get("return_code") == 0 and post_full.get("target_passed") is True, "Post-patch full target failed")
    expect(errors, outcome.get("classification") == "duplicate_clean_replay_pass", "Duplicate replay did not pass")
    expect(errors, outcome.get("pre_repair_failure_reproduced") is True, "Outcome lacks pre-repair reproduction")
    expect(errors, outcome.get("exact_patch_applied") is True, "Outcome lacks exact patch application")
    expect(errors, outcome.get("post_patch_duplicate_target_passed") is True, "Outcome lacks post-patch pass")

    expect(errors, gate_plan.get("gate_runs_only_after_duplicate_clean_replay_pass") is True, "Count gate plan order invalid")
    expect(errors, gate_results.get("count_gate_passed") is True, "Count gate did not pass")
    expect(errors, all(item.get("passed") is True for item in criteria.get("criteria", [])), "Not all count-gate criteria passed")
    expect(errors, count_update.get("issue_derived_repair_count_before_batch061") == 2, "Count update before mismatch")
    expect(errors, count_update.get("issue_derived_repair_count_after_batch061") == 3, "Issue-derived repair count did not increment to 3")
    expect(errors, count_update.get("increment") == 1, "Issue-derived increment is not one")
    expect(errors, native_count.get("native_external_repair_count_after_batch061") == 4, "Native external repair count changed")
    expect(errors, duplicate_check.get("already_counted_before_batch061") is False, "Candidate was already counted")
    expect(errors, canonical.get("counted_as_issue_derived") is True and canonical.get("counted_as_native_external") is False, "Canonical issue repair record has wrong count class")
    expect(errors, canonical.get("provider_runtime_recovery_counted_as_repair") is False, "Provider/runtime recovery counted as repair")
    expect(errors, ledger.get("status") == "PASS" and ledger.get("transition") == "issue_derived_repair_count_increment", "Proof ledger entry invalid")

    expect(errors, pattern.get("broader_automation_status") == "scaffolded_not_general", "Pattern library overclaims automation")
    expect(errors, health.get("advisory_diagnostic_only") is True and health.get("does_not_override_audits") is True, "Project health review is not advisory")
    expect(errors, scorecard.get("dimensions", {}).get("memory_lift") == "not_demonstrated", "Scorecard overclaims memory lift")
    expect(errors, readiness.get("self_maintaining_software_demonstrated") is False, "Self-maintaining software was overclaimed")
    expect(errors, readiness.get("claim_ready_used") is False, "Readiness used claim-ready overclaim")
    expect(errors, public_language.get("status") == "PASS", "Public language neutrality check failed")
    expect(errors, public_claims.get("self_maintaining_software_claimed") is False, "Public claim check overclaims self-maintenance")
    expect(errors, public_claims.get("full_scoring_claimed") is False and public_claims.get("memory_lift_claimed") is False, "Public claim check overclaims scoring/memory")
    expect(errors, internal_public.get("machine_checked_outputs_are_authoritative") is True, "Internal/public boundary does not preserve operational outputs")

    expect(errors, final.get("status") == "PASS", "Batch061 final status not PASS")
    expect(errors, final.get("current_protocol") == CURRENT_PROTOCOL, "Current protocol changed")
    expect(errors, final.get("candidate_id") == CANDIDATE_ID, "Final candidate mismatch")
    expect(errors, final.get("pre_repair_duplicate_reproduction_status") == "PASS", "Final pre-repair reproduction not PASS")
    expect(errors, final.get("exact_patch_identity_status") == "PASS", "Final patch identity not PASS")
    expect(errors, final.get("duplicate_replay_outcome") == "duplicate_clean_replay_pass", "Final duplicate outcome mismatch")
    expect(errors, final.get("count_gate_status") == "PASS", "Final count gate status mismatch")
    expect(errors, final.get("issue_derived_repair_count_before_batch061") == 2, "Final issue-derived before count mismatch")
    expect(errors, final.get("issue_derived_repair_count_after_batch061") == 3, "Final issue-derived after count mismatch")
    expect(errors, final.get("native_external_repair_count") == 4, "Final native external count mismatch")
    expect(errors, final.get("full_scoring") == "NOT_RUN/disallowed", "Final full scoring changed")
    expect(errors, final.get("memory_lift") == "not_demonstrated", "Final memory lift changed")
    expect(errors, final.get("self_maintaining_software") == "false/not_demonstrated", "Final self-maintaining status changed")
    expect(errors, final.get("next_allowed_action") == "batch062_next_issue_repair_candidate_selection_or_wave3_expansion", "Final next action mismatch")
    expect(errors, final.get("exact_blocker") is None, "Final blocker should be None")

    expect(errors, claim.get("new_patch_generated_in_batch061") is False, "Claim boundary says new patch generated")
    expect(errors, claim.get("batch060d_exact_patch_used") is True, "Claim boundary does not record exact Batch060d patch")
    for key in ["tests_mutated", "fixtures_mutated", "dependency_build_files_mutated", "provider_runtime_recovery_counted_as_repair"]:
        expect_false(errors, claim, key, "Batch061 claim boundary")
    expect(errors, claim.get("issue_derived_repair_count_after_batch061") == 3, "Claim boundary count mismatch")
    expect(errors, claim.get("native_external_repair_count") == 4, "Claim boundary native count mismatch")
    expect(errors, claim.get("full_scoring") == "NOT_RUN/disallowed", "Claim boundary full scoring changed")
    expect(errors, claim.get("memory_lift") == "not_demonstrated", "Claim boundary memory lift changed")
    expect(errors, claim.get("self_maintaining_software") == "false/not_demonstrated", "Claim boundary self-maintaining changed")
    for key in ["raw_zip_payload_committed", "runtime_workspaces_committed", "source_checkouts_committed", "venvs_committed", "caches_committed", "new_patch_generated_or_committed"]:
        expect_false(errors, package, key, "Batch061 package verification")

    current_cfg = (ROOT / "configs" / "controllergate_current.yaml").read_text(encoding="utf-8")
    expect(errors, "protocol_version: v2.14" in current_cfg, "Current protocol is not v2.14")
    audit_public_docs(errors)
    audit_git_status(errors)

    if errors:
        print("FAIL:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Batch061 duplicate clean replay count gate Cloudpickle wave 3 audit PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
