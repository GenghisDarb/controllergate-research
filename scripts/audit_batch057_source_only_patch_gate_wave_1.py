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


OUT_DIR = ROOT / "outputs" / "post_v2_37_hardening_batch057_source_only_patch_gate_wave_1"
CURRENT_PROTOCOL = "v2.14"
EXPECTED_BATCH056_SHA256 = "7b77a473383ac5063121a047b8b855140fbbd27475637383499e10c40cf5e1df"
EXPECTED_BATCH056_SIZE = 108999
EXPECTED_BATCH056_ENTRY_COUNT = 120
EXPECTED_BATCH056_ARTIFACT_MANIFEST_CHECKED = 119
EXPECTED_BATCH056_OUTPUT_MANIFEST_CHECKED = 118
EXPECTED_BATCH057_ARTIFACT = "post_v2_37_hardening_batch057_source_only_patch_gate_wave_1_artifacts"
EXPECTED_CANDIDATES = {
    "datasette_2461_async_event_loop_cli_tests",
    "freezegun_547_py313_datetimes_assertion",
    "venusian_91_py313_frameinfo_callinfo",
    "pexpect_699_replwrap_bash_assertions",
}
ALLOWED_BLOCKERS = {
    "blocked_ambiguous_multi_failure_source_surface",
    "blocked_no_safe_source_patch",
    "blocked_environment_specific_failure",
    "blocked_batch057_prerepair_replay_not_reproduced",
    "blocked_native_test_missing",
    "blocked_commit_unresolved",
    "blocked_dependency_install_failure",
}
REQUIRED_TOP_LEVEL = [
    "batch056_artifact_ingestion_summary.json",
    "batch056_artifact_sha256_verification.json",
    "batch056_result_preservation.json",
    "batch056_wave_1_replay_preservation.json",
    "batch056_wave_2_future_plan_preservation.json",
    "batch056_claim_boundary_preservation.json",
    "batch056_next_action_boundary.json",
    "source_only_patch_gate_wave_1_plan.json",
    "source_only_patch_gate_wave_1_results.json",
    "source_only_patch_gate_wave_1_summary.md",
    "source_only_patch_gate_wave_1_dashboard.json",
    "batch058_duplicate_replay_candidates.json",
    "batch058_count_gate_recommendation.json",
    "wave_1_patch_blocked_candidate_registry.json",
    "wave_1_patch_failure_registry.json",
    "wave_1_successful_target_pass_registry.json",
    "wave_2_future_plan_preservation.json",
    "claim_boundary.json",
    "audit.json",
    "package_verification.json",
    "artifact_sha256_verification.json",
    "SHA256SUMS.txt",
]
REQUIRED_CANDIDATE_FILES = [
    "candidate_patch_gate_plan.json",
    "candidate_commit_verification.json",
    "candidate_workspace_manifest.json",
    "candidate_dependency_plan.json",
    "candidate_command_context.json",
    "fresh_pre_repair_replay_command.txt",
    "fresh_pre_repair_replay_log_raw.txt",
    "fresh_pre_repair_replay_result.json",
    "fresh_pre_repair_failure_signature_extract.txt",
    "decision_time_input_manifest.json",
    "issue_body_leakage_boundary.json",
    "label_blindness_check.json",
    "gold_patch_exclusion_check.json",
    "future_evidence_exclusion_check.json",
    "provider_precondition_check.json",
    "source_discovery_plan.json",
    "source_discovery_result.json",
    "source_file_inventory.json",
    "suspect_source_files.json",
    "bounded_failure_to_source_trace.json",
    "decision_time_source_manifest.json",
    "forbidden_evidence_audit.json",
    "patch_generation_trace.json",
    "patch_safety_check.json",
    "patch_application_result.json",
    "changed_files_manifest.json",
    "test_mutation_check.json",
    "source_only_check.json",
    "post_repair_replay_command.txt",
    "post_repair_replay_log_raw.txt",
    "post_repair_replay_result.json",
    "post_repair_failure_signature_extract.txt",
    "repair_outcome_classification.json",
]


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def git_lines(*args: str) -> list[str]:
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def has_forbidden_path(path: str) -> bool:
    normalized = path.replace("\\", "/").lower()
    forbidden_parts = [
        "incoming_artifacts/",
        "artifact_payload/",
        "controllergate_runtime/",
        "__pycache__/",
        ".pytest_cache/",
        ".mypy_cache/",
        ".ruff_cache/",
        ".venv/",
        "/venv/",
        "/env/",
        "/.env/",
    ]
    forbidden_suffixes = (
        ".zip",
        ".tar",
        ".tgz",
        ".tar.gz",
        ".7z",
        ".whl",
        ".pyc",
        ".pyo",
    )
    return any(part in normalized for part in forbidden_parts) or normalized.endswith(forbidden_suffixes)


def ensure_bool_false(errors: list[str], record: dict[str, Any], field: str, label: str) -> None:
    if record.get(field) is not False:
        errors.append(f"{label} expected false: {field}")


def main() -> int:
    errors: list[str] = []

    if not OUT_DIR.is_dir():
        print("FAIL: missing Batch057 output directory")
        return 1
    for rel in REQUIRED_TOP_LEVEL:
        if not (OUT_DIR / rel).is_file():
            errors.append(f"missing required Batch057 output: {rel}")

    manifest = verify_manifest(OUT_DIR)
    if manifest.get("status") != "PASS":
        errors.append(f"Batch057 SHA256SUMS mismatch: {manifest}")

    if errors:
        print("FAIL:", errors)
        return 1

    ingest = read_json(OUT_DIR / "batch056_artifact_ingestion_summary.json")
    verification = read_json(OUT_DIR / "batch056_artifact_sha256_verification.json")
    result_preservation = read_json(OUT_DIR / "batch056_result_preservation.json")
    wave1_preservation = read_json(OUT_DIR / "batch056_wave_1_replay_preservation.json")
    wave2_preservation = read_json(OUT_DIR / "batch056_wave_2_future_plan_preservation.json")
    claim_preservation = read_json(OUT_DIR / "batch056_claim_boundary_preservation.json")
    next_boundary = read_json(OUT_DIR / "batch056_next_action_boundary.json")
    plan = read_json(OUT_DIR / "source_only_patch_gate_wave_1_plan.json")
    results_record = read_json(OUT_DIR / "source_only_patch_gate_wave_1_results.json")
    dashboard = read_json(OUT_DIR / "source_only_patch_gate_wave_1_dashboard.json")
    duplicate_candidates = read_json(OUT_DIR / "batch058_duplicate_replay_candidates.json")
    count_gate = read_json(OUT_DIR / "batch058_count_gate_recommendation.json")
    blocked_registry = read_json(OUT_DIR / "wave_1_patch_blocked_candidate_registry.json")
    failure_registry = read_json(OUT_DIR / "wave_1_patch_failure_registry.json")
    success_registry = read_json(OUT_DIR / "wave_1_successful_target_pass_registry.json")
    claim = read_json(OUT_DIR / "claim_boundary.json")
    audit = read_json(OUT_DIR / "audit.json")
    package = read_json(OUT_DIR / "package_verification.json")
    artifact_sha = read_json(OUT_DIR / "artifact_sha256_verification.json")

    if ingest.get("status") != "PASS" or verification.get("status") != "PASS":
        errors.append("Batch056 artifact ingest/verification did not PASS")
    if verification.get("zip_sha256") != EXPECTED_BATCH056_SHA256:
        errors.append("Batch056 ZIP SHA256 mismatch")
    if verification.get("zip_size_bytes") != EXPECTED_BATCH056_SIZE:
        errors.append("Batch056 ZIP byte size mismatch")
    if verification.get("zip_entry_count") != EXPECTED_BATCH056_ENTRY_COUNT:
        errors.append("Batch056 ZIP entry count mismatch")
    if verification.get("unsafe_path_count") != 0 or verification.get("duplicate_path_count") != 0:
        errors.append("Batch056 ZIP path safety failed")
    if verification.get("zip_pycache_entries") != 0 or verification.get("zip_pyc_entries") != 0:
        errors.append("Batch056 ZIP contains cache/pyc payload")
    if verification.get("artifact_manifest", {}).get("checked") != EXPECTED_BATCH056_ARTIFACT_MANIFEST_CHECKED:
        errors.append("Batch056 artifact manifest coverage mismatch")
    output_manifest = verification.get("output_manifests", {}).get(
        "post_v2_37_hardening_batch056_pre_repair_replay_wave_1_plus_wave_2_intake", {}
    )
    if output_manifest.get("checked") != EXPECTED_BATCH056_OUTPUT_MANIFEST_CHECKED:
        errors.append("Batch056 internal SHA256SUMS coverage mismatch")
    if verification.get("raw_zip_bytes_ingested") is not False or verification.get("zip_payload_committed") is not False:
        errors.append("Batch056 raw ZIP payload boundary failed")

    if result_preservation.get("issue_derived_repair_count") != 2:
        errors.append("Issue-derived repair count not preserved at 2")
    if result_preservation.get("native_external_repair_count") != 4:
        errors.append("Native external repair count not preserved at 4")
    if result_preservation.get("full_scoring") != "NOT_RUN/disallowed":
        errors.append("Full scoring boundary not preserved")
    if result_preservation.get("memory_lift") != "not_demonstrated":
        errors.append("Memory lift boundary not preserved")
    if result_preservation.get("self_maintaining_software") != "false/not_demonstrated":
        errors.append("Self-maintaining boundary not preserved")
    if result_preservation.get("next_allowed_action") != "batch057_source_only_patch_gate_wave_1":
        errors.append("Batch056 next action was not Batch057 patch gate")
    if wave1_preservation.get("wave_1_candidate_count") != 5:
        errors.append("Batch056 Wave 1 candidate count not preserved at 5")
    if wave1_preservation.get("wave_1_materialized_failure_count") != 4:
        errors.append("Batch056 Wave 1 materialized count not preserved at 4")
    if wave1_preservation.get("wave_1_blocked_count") != 1:
        errors.append("Batch056 Wave 1 blocked count not preserved at 1")
    if set(wave1_preservation.get("batch057_recommended_candidates", [])) != EXPECTED_CANDIDATES:
        errors.append("Batch057 candidate set is not the exact materialized Wave 1 set")
    if wave2_preservation.get("wave_2_approved_for_future_replay_count") != 7:
        errors.append("Batch056 Wave 2 future replay count not preserved at 7")
    for field in ["wave_2_replayed_in_batch057", "wave_2_patched_in_batch057", "wave_2_count_gate_run_in_batch057"]:
        ensure_bool_false(errors, wave2_preservation, field, "Wave 2 preservation")
    if claim_preservation.get("status") != "PASS":
        errors.append("Batch056 claim preservation failed")
    for field in ["batch057_duplicate_replay_run", "batch057_count_gate_run", "batch057_repair_count_increment"]:
        ensure_bool_false(errors, claim_preservation, field, "Batch056 claim preservation")
    if next_boundary.get("preserved_next_allowed_action") != "batch057_source_only_patch_gate_wave_1":
        errors.append("Batch056 next-action boundary was not preserved")

    result_rows = results_record.get("results", [])
    if results_record.get("status") != "PASS" or len(result_rows) != 4:
        errors.append("Batch057 results do not contain exactly four PASS rows")
    if {row.get("lead_id") for row in result_rows} != EXPECTED_CANDIDATES:
        errors.append("Batch057 results candidate set mismatch")
    plan_ids = {item.get("lead_id") for item in plan.get("candidates", [])}
    if plan.get("candidate_count") != 4 or plan_ids != EXPECTED_CANDIDATES:
        errors.append("Batch057 plan candidate set/count mismatch")
    if dashboard.get("fresh_prerepair_reproduction_count") != 4:
        errors.append("Batch057 fresh pre-repair reproduction count is not 4")
    if dashboard.get("patch_generated_count") != 0:
        errors.append("Batch057 unexpectedly generated patches")
    if dashboard.get("patch_target_pass_count") != 0 or dashboard.get("patch_target_fail_count") != 0:
        errors.append("Batch057 unexpectedly ran post-repair target validation")
    if dashboard.get("blocked_no_safe_patch_count") != 4:
        errors.append("Batch057 blocked/no-safe-patch count is not 4")
    if dashboard.get("next_allowed_action") != "batch057b_source_discovery_recovery_or_batch056b_wave2_pre_repair_replay":
        errors.append("Batch057 next allowed action mismatch")
    if duplicate_candidates.get("candidate_count") != 0 or duplicate_candidates.get("candidates") != []:
        errors.append("Batch058 duplicate replay candidates should be empty")
    if duplicate_candidates.get("counted_repairs_in_batch057") != 0:
        errors.append("Batch057 attempted to count repairs before duplicate replay")
    if count_gate.get("count_gate_run_in_batch057") is not False:
        errors.append("Batch057 count gate should not run")
    if count_gate.get("next_allowed_action") != dashboard.get("next_allowed_action"):
        errors.append("Batch058 count recommendation next action mismatch")
    if success_registry.get("count") != 0 or failure_registry.get("count") != 0:
        errors.append("Batch057 success/failure patch registries should both be empty without generated patches")
    if blocked_registry.get("count") != 4:
        errors.append("Batch057 blocked candidate registry count mismatch")

    for field in [
        "batch057_duplicate_replay_run",
        "batch057_count_gate_run",
        "batch057_repair_count_increment",
        "batch057_wave_2_patch_or_replay",
    ]:
        ensure_bool_false(errors, claim, field, "Batch057 claim boundary")
    if claim.get("current_protocol") != CURRENT_PROTOCOL:
        errors.append("Current protocol is not preserved at v2.14")
    if claim.get("issue_derived_repair_count") != 2 or claim.get("native_external_repair_count") != 4:
        errors.append("Repair counts changed in Batch057 claim boundary")
    if claim.get("full_scoring") != "NOT_RUN/disallowed":
        errors.append("Batch057 full scoring overclaim")
    if claim.get("memory_lift") != "not_demonstrated":
        errors.append("Batch057 memory lift overclaim")
    if claim.get("self_maintaining_software") != "false/not_demonstrated":
        errors.append("Batch057 self-maintaining overclaim")
    if audit.get("status") != "PASS":
        errors.append("Batch057 embedded audit status is not PASS")
    if package.get("artifact_name") != EXPECTED_BATCH057_ARTIFACT or package.get("raw_zip_payload_committed") is not False:
        errors.append("Batch057 package verification boundary failed")
    if artifact_sha.get("status") != "PENDING_WORKFLOW_ARTIFACT" or artifact_sha.get("batch056_local_zip_sha256") != EXPECTED_BATCH056_SHA256:
        errors.append("Batch057 artifact SHA verification record failed")

    for row in result_rows:
        lead_id = row.get("lead_id")
        candidate_dir = OUT_DIR / "patch_candidates" / str(lead_id)
        for rel in REQUIRED_CANDIDATE_FILES:
            if not (candidate_dir / rel).is_file():
                errors.append(f"missing Batch057 candidate output for {lead_id}: {rel}")
        if errors:
            continue
        prerepair = read_json(candidate_dir / "fresh_pre_repair_replay_result.json")
        discovery = read_json(candidate_dir / "source_discovery_result.json")
        patch_trace = read_json(candidate_dir / "patch_generation_trace.json")
        patch_safety = read_json(candidate_dir / "patch_safety_check.json")
        patch_application = read_json(candidate_dir / "patch_application_result.json")
        changed_files = read_json(candidate_dir / "changed_files_manifest.json")
        test_mutation = read_json(candidate_dir / "test_mutation_check.json")
        source_only = read_json(candidate_dir / "source_only_check.json")
        post_repair = read_json(candidate_dir / "post_repair_replay_result.json")
        outcome = read_json(candidate_dir / "repair_outcome_classification.json")
        decision_inputs = read_json(candidate_dir / "decision_time_input_manifest.json")
        leakage = read_json(candidate_dir / "issue_body_leakage_boundary.json")
        label = read_json(candidate_dir / "label_blindness_check.json")
        gold = read_json(candidate_dir / "gold_patch_exclusion_check.json")
        future = read_json(candidate_dir / "future_evidence_exclusion_check.json")
        forbidden = read_json(candidate_dir / "forbidden_evidence_audit.json")
        commit = read_json(candidate_dir / "candidate_commit_verification.json")

        if prerepair.get("fresh_batch057_pre_repair_replay_reproduced") is not True:
            errors.append(f"fresh pre-repair replay not reproduced for {lead_id}")
        if prerepair.get("patch_generated_before_replay") is not False:
            errors.append(f"patch was generated before replay for {lead_id}")
        if row.get("fresh_prerepair_reproduced") is not True:
            errors.append(f"Batch057 row does not mark fresh reproduction for {lead_id}")
        if row.get("patch_generation_classification") not in ALLOWED_BLOCKERS:
            errors.append(f"unexpected Batch057 blocker for {lead_id}: {row.get('patch_generation_classification')}")
        if discovery.get("status") not in {"PASS", "BLOCK"}:
            errors.append(f"source discovery status invalid for {lead_id}")
        if patch_trace.get("patch_generated") is not False:
            errors.append(f"unexpected source patch generated for {lead_id}")
        if patch_trace.get("source_patch_generation_forbidden") is not True:
            errors.append(f"patch generation should be forbidden for {lead_id}")
        if patch_safety.get("patch_generated") is not False:
            errors.append(f"unexpected patch safety generated state for {lead_id}")
        if patch_application.get("patch_applied") not in (False, None):
            errors.append(f"unexpected patch application for {lead_id}")
        if changed_files.get("changed_files") != []:
            errors.append(f"changed files detected for unpatched candidate {lead_id}")
        if test_mutation.get("tests_modified") is not False:
            errors.append(f"test mutation detected for {lead_id}")
        if source_only.get("patch_generated") is not False:
            errors.append(f"source-only record unexpectedly observed generated patch for {lead_id}")
        if post_repair.get("status") != "NOT_RUN":
            errors.append(f"post-repair replay should be NOT_RUN for {lead_id}")
        if outcome.get("batch058_duplicate_replay_candidate") is not False:
            errors.append(f"candidate incorrectly forwarded to Batch058: {lead_id}")
        if row.get("target_pass") is not False:
            errors.append(f"Batch057 row target_pass should be false for {lead_id}")
        if decision_inputs.get("fixed_gold_future_evidence_used") is not False:
            errors.append(f"fixed commit evidence used for {lead_id}")
        if leakage.get("patch_or_workaround_text_used") is not False or leakage.get("issue_body_persisted_as_repair_evidence") is not False:
            errors.append(f"issue body repair leakage for {lead_id}")
        if label.get("hidden_labels_used") is not False:
            errors.append(f"hidden label usage detected for {lead_id}")
        if gold.get("gold_patch_used") is not False:
            errors.append(f"gold patch usage detected for {lead_id}")
        if future.get("future_evidence_used") is not False:
            errors.append(f"future evidence usage detected for {lead_id}")
        for key, value in forbidden.items():
            if key.endswith("_used") and value is not False:
                errors.append(f"forbidden evidence audit failed for {lead_id}: {key}")
        if commit.get("git_cat_file_e_commit_verified") is not True:
            errors.append(f"candidate source commit was not verified for {lead_id}")

    staged_or_changed = git_lines("status", "--short")
    for line in staged_or_changed:
        path = line[3:] if len(line) > 3 else line
        if line.startswith("?? incoming_artifacts/"):
            continue
        if "outputs/post_v2_37_hardening_batch057_source_only_patch_gate_wave_1/" not in path.replace("\\", "/") and not line.startswith(("A ", "M ", "?? ")):
            continue
        if has_forbidden_path(path):
            errors.append(f"forbidden path appears in worktree status: {line}")

    if errors:
        print("FAIL:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Batch057 source-only patch gate wave 1 audit PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
