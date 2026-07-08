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


OUT_DIR = ROOT / "outputs" / "post_v2_37_hardening_batch057c_layered_source_only_patch_recovery_freezegun"
CURRENT_PROTOCOL = "v2.14"
EXPECTED_BATCH057B_SHA256 = "3365b2d2e600e0dd44dcad66af2c4bb5d5c5a6b038dba9193de2ba8e6d3344c5"
EXPECTED_BATCH057B_SIZE = 88926
EXPECTED_BATCH057B_ENTRY_COUNT = 109
EXPECTED_BATCH057B_ARTIFACT_MANIFEST_CHECKED = 108
EXPECTED_BATCH057B_OUTPUT_MANIFEST_CHECKED = 107
EXPECTED_CANDIDATE = "freezegun_547_py313_datetimes_assertion"
EXPECTED_SOURCE_FILE = "freezegun/api.py"
EXPECTED_ARTIFACT = "post_v2_37_hardening_batch057c_layered_source_only_patch_recovery_freezegun_artifacts"

REQUIRED_TOP_LEVEL = [
    "batch057b_artifact_ingestion_summary.json",
    "batch057b_artifact_sha256_verification.json",
    "batch057b_result_preservation.json",
    "batch057b_elbow_gate_preservation.json",
    "batch057b_candidate_classification_preservation.json",
    "batch057b_claim_boundary_preservation.json",
    "batch057b_next_action_boundary.json",
    "freezegun_candidate_setup.json",
    "freezegun_fresh_prerepair_replay_results.json",
    "fresh_prerepair_original_target_log_raw.txt",
    "fresh_prerepair_primary_minimal_log_raw.txt",
    "fresh_prerepair_secondary_minimal_log_raw.txt",
    "decision_time_input_manifest.json",
    "forbidden_evidence_audit.json",
    "issue_body_leakage_boundary.json",
    "label_blindness_check.json",
    "gold_patch_exclusion_check.json",
    "future_evidence_exclusion_check.json",
    "source_discovery_plan.json",
    "source_discovery_result.json",
    "source_file_inventory.json",
    "suspect_source_files.json",
    "bounded_failure_to_source_trace_primary.json",
    "bounded_failure_to_source_trace_secondary.json",
    "decision_time_source_manifest.json",
    "source_surface_localization_check.json",
    "stage1_primary_patch_generation_trace.json",
    "stage1_primary_source_only_patch_candidate.diff",
    "stage1_primary_source_only_patch_candidate.json",
    "stage1_primary_patch_safety_check.json",
    "stage1_primary_patch_application_result.json",
    "stage1_primary_changed_files_manifest.json",
    "stage1_primary_test_mutation_check.json",
    "stage1_primary_source_only_check.json",
    "stage1_primary_post_repair_primary_minimal_log_raw.txt",
    "stage1_primary_post_repair_primary_family_log_raw.txt",
    "stage1_primary_post_repair_secondary_minimal_log_raw.txt",
    "stage1_primary_post_repair_full_target_log_raw.txt",
    "stage1_primary_post_repair_results.json",
    "stage1_primary_outcome_classification.json",
    "stage2_secondary_authorization_check.json",
    "stage2_secondary_not_authorized_reason.json",
    "stage2_secondary_no_patch_reason.json",
    "stage2_secondary_patch_generation_trace.json",
    "stage2_secondary_patch_not_generated.json",
    "stage2_secondary_patch_application_not_run.json",
    "stage2_secondary_patch_safety_check.json",
    "stage2_secondary_changed_files_manifest.json",
    "stage2_secondary_test_mutation_check.json",
    "stage2_secondary_source_only_check.json",
    "stage2_secondary_post_repair_results.json",
    "stage2_secondary_outcome_classification.json",
    "batch057c_final_outcome_classification.json",
    "batch057c_layered_patch_results.json",
    "batch058_duplicate_replay_candidates.json",
    "batch058_count_gate_recommendation.json",
    "batch057d_secondary_layer_recovery_recommendation.json",
    "batch056b_wave2_pre_repair_replay_recommendation.json",
    "batch057c_summary.md",
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
    ".whl",
    ".pyc",
    ".pyo",
    "__pycache__",
    ".pytest_cache",
    "artifact_payload/",
    "ControllerGate_runtime",
    "runtime_workspaces/",
    "venv/",
    ".venv/",
]

FORBIDDEN_PUBLIC_TERMS = [
    "TORUS",
    "TLD",
    "AGI",
    "observer-state",
    "recursion-constant",
    "Klein twist",
    "RNA primase",
    "OSQN",
    "cymatics",
    "resonance",
    "chromatin",
    "epigenetic",
]


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def git_lines(*args: str) -> list[str]:
    completed = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return [line.rstrip("\n") for line in completed.stdout.splitlines()]


def expect_false(errors: list[str], obj: dict[str, Any], key: str, context: str) -> None:
    if obj.get(key) is not False:
        errors.append(f"{context}: expected {key}=false")


def expect_true(errors: list[str], obj: dict[str, Any], key: str, context: str) -> None:
    if obj.get(key) is not True:
        errors.append(f"{context}: expected {key}=true")


def expect_status(errors: list[str], obj: dict[str, Any], expected: str, context: str) -> None:
    if obj.get("status") != expected:
        errors.append(f"{context}: expected status {expected}, observed {obj.get('status')!r}")


def audit_public_language(errors: list[str]) -> None:
    for rel in ["batch057c_summary.md"]:
        text = (OUT_DIR / rel).read_text(encoding="utf-8")
        for term in FORBIDDEN_PUBLIC_TERMS:
            if term in text:
                errors.append(f"forbidden public-language term in {rel}: {term}")


def audit_git_status(errors: list[str]) -> None:
    for line in git_lines("status", "--short"):
        path = line[3:] if len(line) > 3 else line
        normalized = path.replace("\\", "/")
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

    for rel in REQUIRED_TOP_LEVEL:
        if not (OUT_DIR / rel).is_file():
            errors.append(f"missing required Batch057c output: {rel}")

    if not errors:
        manifest = verify_manifest(OUT_DIR)
        if manifest.get("status") != "PASS":
            errors.append(f"Batch057c SHA256SUMS verification failed: {manifest}")

    if errors:
        print("FAIL:")
        for error in errors:
            print(f"- {error}")
        return 1

    artifact = read_json(OUT_DIR / "batch057b_artifact_sha256_verification.json")
    result_preservation = read_json(OUT_DIR / "batch057b_result_preservation.json")
    elbow = read_json(OUT_DIR / "batch057b_elbow_gate_preservation.json")
    classifications = read_json(OUT_DIR / "batch057b_candidate_classification_preservation.json")
    claim = read_json(OUT_DIR / "claim_boundary.json")
    setup = read_json(OUT_DIR / "freezegun_candidate_setup.json")
    prerepair = read_json(OUT_DIR / "freezegun_fresh_prerepair_replay_results.json")
    decision_inputs = read_json(OUT_DIR / "decision_time_input_manifest.json")
    forbidden = read_json(OUT_DIR / "forbidden_evidence_audit.json")
    issue_boundary = read_json(OUT_DIR / "issue_body_leakage_boundary.json")
    label = read_json(OUT_DIR / "label_blindness_check.json")
    gold = read_json(OUT_DIR / "gold_patch_exclusion_check.json")
    future = read_json(OUT_DIR / "future_evidence_exclusion_check.json")
    source_result = read_json(OUT_DIR / "source_discovery_result.json")
    source_manifest = read_json(OUT_DIR / "decision_time_source_manifest.json")
    stage1_trace = read_json(OUT_DIR / "stage1_primary_patch_generation_trace.json")
    stage1_candidate = read_json(OUT_DIR / "stage1_primary_source_only_patch_candidate.json")
    stage1_safety = read_json(OUT_DIR / "stage1_primary_patch_safety_check.json")
    stage1_application = read_json(OUT_DIR / "stage1_primary_patch_application_result.json")
    stage1_changed = read_json(OUT_DIR / "stage1_primary_changed_files_manifest.json")
    stage1_test_mutation = read_json(OUT_DIR / "stage1_primary_test_mutation_check.json")
    stage1_source_only = read_json(OUT_DIR / "stage1_primary_source_only_check.json")
    stage1_results = read_json(OUT_DIR / "stage1_primary_post_repair_results.json")
    stage1_outcome = read_json(OUT_DIR / "stage1_primary_outcome_classification.json")
    stage2_auth = read_json(OUT_DIR / "stage2_secondary_authorization_check.json")
    stage2_trace = read_json(OUT_DIR / "stage2_secondary_patch_generation_trace.json")
    stage2_not_generated = read_json(OUT_DIR / "stage2_secondary_patch_not_generated.json")
    stage2_application = read_json(OUT_DIR / "stage2_secondary_patch_application_not_run.json")
    stage2_safety = read_json(OUT_DIR / "stage2_secondary_patch_safety_check.json")
    stage2_changed = read_json(OUT_DIR / "stage2_secondary_changed_files_manifest.json")
    stage2_test_mutation = read_json(OUT_DIR / "stage2_secondary_test_mutation_check.json")
    stage2_source_only = read_json(OUT_DIR / "stage2_secondary_source_only_check.json")
    stage2_results = read_json(OUT_DIR / "stage2_secondary_post_repair_results.json")
    stage2_outcome = read_json(OUT_DIR / "stage2_secondary_outcome_classification.json")
    final = read_json(OUT_DIR / "batch057c_final_outcome_classification.json")
    layered = read_json(OUT_DIR / "batch057c_layered_patch_results.json")
    duplicate = read_json(OUT_DIR / "batch058_duplicate_replay_candidates.json")
    count_gate = read_json(OUT_DIR / "batch058_count_gate_recommendation.json")
    batch057d = read_json(OUT_DIR / "batch057d_secondary_layer_recovery_recommendation.json")
    wave2 = read_json(OUT_DIR / "batch056b_wave2_pre_repair_replay_recommendation.json")
    embedded_audit = read_json(OUT_DIR / "audit.json")
    package = read_json(OUT_DIR / "package_verification.json")
    artifact_sha = read_json(OUT_DIR / "artifact_sha256_verification.json")

    expect_status(errors, artifact, "PASS", "Batch057b artifact verification")
    if artifact.get("zip_sha256") != EXPECTED_BATCH057B_SHA256 or artifact.get("artifact_sha256") != EXPECTED_BATCH057B_SHA256:
        errors.append("Batch057b artifact SHA256 mismatch")
    if artifact.get("zip_size_bytes") != EXPECTED_BATCH057B_SIZE or artifact.get("artifact_size_bytes") != EXPECTED_BATCH057B_SIZE:
        errors.append("Batch057b artifact size mismatch")
    if artifact.get("zip_entry_count") != EXPECTED_BATCH057B_ENTRY_COUNT:
        errors.append("Batch057b artifact ZIP entry count mismatch")
    if artifact.get("artifact_manifest", {}).get("checked") != EXPECTED_BATCH057B_ARTIFACT_MANIFEST_CHECKED:
        errors.append("Batch057b artifact-level SHA256SUMS checked count mismatch")
    output_manifest = artifact.get("output_manifests", {}).get("post_v2_37_hardening_batch057b_failure_family_decomposition_elbow_recovery", {})
    if output_manifest.get("checked") != EXPECTED_BATCH057B_OUTPUT_MANIFEST_CHECKED or output_manifest.get("failures") != 0:
        errors.append("Batch057b internal output SHA256SUMS verification mismatch")
    for key in ["unsafe_path_count", "duplicate_path_count", "zip_pyc_entries", "zip_pycache_entries"]:
        if artifact.get(key) != 0:
            errors.append(f"Batch057b artifact has non-zero {key}")
    expect_false(errors, artifact, "raw_zip_bytes_ingested", "Batch057b artifact verification")
    expect_false(errors, artifact, "zip_payload_committed", "Batch057b artifact verification")

    if result_preservation.get("elbow_open_candidate_count") != 1 or result_preservation.get("elbow_closed_candidate_count") != 3:
        errors.append("Batch057b elbow open/closed counts not preserved")
    if result_preservation.get("candidate_retirement_count") != 1 or result_preservation.get("minimal_subtarget_replay_count") != 5:
        errors.append("Batch057b decomposition counts not preserved")
    if elbow.get("elbow_gate", {}).get("states", {}).get(EXPECTED_CANDIDATE) != "elbow_open_primary_family_only_diagnostic_patch_allowed":
        errors.append("Freezegun elbow-open state not preserved")
    if set(classifications.get("candidate_decomposition_classifications", {}).keys()) != {
        "datasette_2461_async_event_loop_cli_tests",
        EXPECTED_CANDIDATE,
        "pexpect_699_replwrap_bash_assertions",
        "venusian_91_py313_frameinfo_callinfo",
    }:
        errors.append("Batch057b candidate classification set changed")

    if claim.get("current_protocol") != CURRENT_PROTOCOL:
        errors.append("Current protocol is not preserved at v2.14")
    if claim.get("issue_derived_repair_count") != 2:
        errors.append("Issue-derived repair count changed")
    if claim.get("native_external_repair_count") != 4:
        errors.append("Native external repair count changed")
    if claim.get("full_scoring") != "NOT_RUN/disallowed":
        errors.append("Full scoring boundary changed")
    if claim.get("memory_lift") != "not_demonstrated":
        errors.append("Memory lift boundary changed")
    if claim.get("self_maintaining_software") != "false/not_demonstrated":
        errors.append("Self-maintaining boundary changed")
    for key in ["batch057c_duplicate_replay_run", "batch057c_count_gate_run", "batch057c_repair_count_increment"]:
        expect_false(errors, claim, key, "Batch057c claim boundary")
    expect_true(errors, claim, "partial_improvement_not_counted", "Batch057c claim boundary")

    expect_status(errors, setup, "PASS", "Freezegun candidate setup")
    if setup.get("lead_id") != EXPECTED_CANDIDATE:
        errors.append("Batch057c operated on the wrong candidate")
    if setup.get("suspect_source_file", {}).get("path") != EXPECTED_SOURCE_FILE:
        errors.append("Freezegun suspected source file mismatch")

    for name in ["original_target", "primary_minimal", "secondary_minimal"]:
        row = prerepair.get("results", {}).get(name, {})
        if row.get("classification") != "pre_repair_failure_reproduced" or row.get("passed") is not False:
            errors.append(f"fresh pre-repair replay not reproduced for {name}")
    if prerepair.get("patching_authorized_after_replay") is not True:
        errors.append("Batch057c patching was not gated on reproduced pre-repair replay")

    for key in ["fixed_commit_read", "future_commit_read", "gold_patch_read", "pr_patch_read", "issue_body_fix_text_used"]:
        expect_false(errors, decision_inputs, key, "Decision-time input manifest")
    for key, value in forbidden.items():
        if key.endswith("_used") and value is not False:
            errors.append(f"forbidden evidence used: {key}")
    if issue_boundary.get("issue_body_fix_or_workaround_text_persisted") is not False:
        errors.append("issue-body patch/workaround text leaked into repair evidence")
    if label.get("hidden_labels_used") is not False:
        errors.append("hidden labels used")
    if gold.get("gold_patch_used") is not False:
        errors.append("gold patch used")
    if future.get("future_evidence_used") is not False:
        errors.append("future evidence used")

    expect_status(errors, source_result, "PASS", "Source discovery result")
    source_files = [row.get("path") for row in source_manifest.get("source_manifest", {}).get("source_files", [])]
    if EXPECTED_SOURCE_FILE not in source_files:
        errors.append("Freezegun source manifest does not include freezegun/api.py")

    expect_status(errors, stage1_trace, "PASS", "Stage 1 patch generation trace")
    expect_true(errors, stage1_trace, "patch_generated", "Stage 1 patch generation trace")
    expect_status(errors, stage1_candidate, "PASS", "Stage 1 patch candidate")
    if stage1_candidate.get("touches") != [EXPECTED_SOURCE_FILE]:
        errors.append("Stage 1 patch candidate is not limited to freezegun/api.py")
    if not stage1_candidate.get("patch_sha256"):
        errors.append("Stage 1 patch candidate missing patch SHA256")
    if not (OUT_DIR / "stage1_primary_source_only_patch_candidate.diff").read_text(encoding="utf-8").strip():
        errors.append("Stage 1 diff is empty")
    expect_status(errors, stage1_safety, "PASS", "Stage 1 patch safety")
    expect_true(errors, stage1_safety, "patch_non_empty", "Stage 1 patch safety")
    expect_true(errors, stage1_safety, "source_only", "Stage 1 patch safety")
    expect_false(errors, stage1_safety, "tests_modified", "Stage 1 patch safety")
    expect_false(errors, stage1_safety, "fixtures_modified", "Stage 1 patch safety")
    expect_false(errors, stage1_safety, "build_or_dependency_files_modified", "Stage 1 patch safety")
    expect_false(errors, stage1_safety, "forbidden_evidence_used", "Stage 1 patch safety")
    expect_status(errors, stage1_application, "PASS", "Stage 1 patch application")
    expect_true(errors, stage1_application, "patch_applied", "Stage 1 patch application")
    if stage1_changed.get("changed_files") != [EXPECTED_SOURCE_FILE]:
        errors.append("Stage 1 changed files are not limited to freezegun/api.py")
    expect_false(errors, stage1_test_mutation, "tests_modified", "Stage 1 test mutation check")
    expect_true(errors, stage1_source_only, "source_only", "Stage 1 source-only check")
    stage1_rows = stage1_results.get("results", {})
    if stage1_rows.get("primary_minimal", {}).get("passed") is not True:
        errors.append("Stage 1 primary minimal did not pass")
    if stage1_rows.get("primary_family", {}).get("passed") is not True:
        errors.append("Stage 1 primary family did not pass")
    if stage1_rows.get("secondary_minimal", {}).get("passed") is not False:
        errors.append("Stage 1 secondary minimal should remain failing")
    if stage1_rows.get("full_target", {}).get("passed") is not False:
        errors.append("Stage 1 full original target should remain failing")
    if stage1_outcome.get("classification") != "stage1_primary_patch_partial_improvement_secondary_still_fails":
        errors.append("Stage 1 outcome classification mismatch")

    if stage2_auth.get("status") != "BLOCK" or stage2_auth.get("authorized") is not False:
        errors.append("Stage 2 authorization should be blocked")
    if stage2_auth.get("exact_blocker") != "secondary_family_provider_tzset_unavailable":
        errors.append("Stage 2 exact blocker mismatch")
    if stage2_trace.get("patch_generated") is not False or stage2_not_generated.get("patch_generated") is not False:
        errors.append("Stage 2 generated a patch despite authorization block")
    if stage2_application.get("patch_applied") is not False:
        errors.append("Stage 2 applied a patch despite authorization block")
    if stage2_safety.get("status") != "NOT_RUN" or stage2_safety.get("patch_non_empty") is not False:
        errors.append("Stage 2 patch safety should be NOT_RUN with empty patch state")
    if stage2_changed.get("changed_files") != []:
        errors.append("Stage 2 changed files should be empty")
    expect_false(errors, stage2_test_mutation, "tests_modified", "Stage 2 test mutation check")
    if stage2_source_only.get("status") != "NOT_RUN" or stage2_source_only.get("source_only") is not False:
        errors.append("Stage 2 source-only check should be NOT_RUN")
    if stage2_results.get("status") != "NOT_RUN":
        errors.append("Stage 2 post-repair results should be NOT_RUN")
    if stage2_outcome.get("classification") != "stage2_not_authorized":
        errors.append("Stage 2 outcome classification mismatch")

    if final.get("classification") != "source_only_patch_primary_only_improvement":
        errors.append("Final Batch057c classification mismatch")
    if final.get("full_original_target_post_repair_status") != "FAIL":
        errors.append("Full original target post-repair status must remain FAIL")
    if final.get("batch058_duplicate_replay_candidate") is not False:
        errors.append("Batch057c incorrectly created a Batch058 candidate")
    if final.get("exact_blocker") != "secondary_family_provider_tzset_unavailable":
        errors.append("Final exact blocker mismatch")
    if final.get("next_allowed_action") != "batch056b_wave2_pre_repair_replay":
        errors.append("Final next allowed action mismatch")
    if layered.get("stage1", {}).get("primary_family_passed") is not True:
        errors.append("Layered results do not preserve Stage 1 generated/applied state")
    if layered.get("stage2", {}).get("classification") != "stage2_not_authorized":
        errors.append("Layered results do not preserve Stage 2 blocked state")
    if duplicate.get("candidate_count") != 0 or duplicate.get("candidates") != []:
        errors.append("Batch058 duplicate replay candidates must be empty")
    if duplicate.get("counted_repairs_in_batch057c") != 0:
        errors.append("Batch057c counted a repair")
    if count_gate.get("count_gate_run_in_batch057c") is not False or count_gate.get("recommendation_count") != 0:
        errors.append("Batch057c ran or recommended the count gate")
    if batch057d.get("recommended") is not False:
        errors.append("Batch057d should not be recommended for provider-bound secondary residual")
    if wave2.get("recommended") is not True:
        errors.append("Wave 2 replay should be the next recommended path")

    if embedded_audit.get("status") != "PASS":
        errors.append("Embedded Batch057c audit marker is not PASS")
    if package.get("artifact_name") != EXPECTED_ARTIFACT:
        errors.append("Batch057c package artifact name mismatch")
    expect_false(errors, package, "raw_zip_payload_committed", "Batch057c package verification")
    if artifact_sha.get("status") != "PENDING_WORKFLOW_ARTIFACT" or artifact_sha.get("artifact_name") != EXPECTED_ARTIFACT:
        errors.append("Batch057c workflow artifact SHA boundary mismatch")
    if artifact_sha.get("batch057b_local_zip_sha256") != EXPECTED_BATCH057B_SHA256:
        errors.append("Batch057c artifact SHA record lost Batch057b custody hash")

    audit_public_language(errors)
    audit_git_status(errors)

    if errors:
        print("FAIL:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Batch057c layered source-only patch recovery Freezegun audit PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
