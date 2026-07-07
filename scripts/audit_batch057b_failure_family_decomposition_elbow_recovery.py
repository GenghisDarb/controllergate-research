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


OUT_DIR = ROOT / "outputs" / "post_v2_37_hardening_batch057b_failure_family_decomposition_elbow_recovery"
EXPECTED_BATCH057_SHA256 = "7d472153a1123f0ed16e23dfa90cca43dc0a7d7059603373ee80e6d1a51542cf"
EXPECTED_BATCH057_SIZE = 108887
EXPECTED_BATCH057_ENTRY_COUNT = 155
EXPECTED_BATCH057_ARTIFACT_MANIFEST_CHECKED = 154
EXPECTED_BATCH057_OUTPUT_MANIFEST_CHECKED = 153
CURRENT_PROTOCOL = "v2.14"
EXPECTED_CANDIDATES = {
    "datasette_2461_async_event_loop_cli_tests",
    "freezegun_547_py313_datetimes_assertion",
    "venusian_91_py313_frameinfo_callinfo",
    "pexpect_699_replwrap_bash_assertions",
}
OPEN_STATES = {
    "elbow_open_single_localized_source_family",
    "elbow_open_primary_family_only_diagnostic_patch_allowed",
}
EXPECTED_STATES = {
    "datasette_2461_async_event_loop_cli_tests": "elbow_closed_multi_family_ambiguous",
    "freezegun_547_py313_datetimes_assertion": "elbow_open_primary_family_only_diagnostic_patch_allowed",
    "venusian_91_py313_frameinfo_callinfo": "elbow_closed_test_expectation_or_interpreter_behavior",
    "pexpect_699_replwrap_bash_assertions": "elbow_closed_environment_provider",
}
REQUIRED_TOP_LEVEL = [
    "batch057_artifact_ingestion_summary.json",
    "batch057_artifact_sha256_verification.json",
    "batch057_result_preservation.json",
    "batch057_candidate_classification_preservation.json",
    "batch057_claim_boundary_preservation.json",
    "batch057_next_action_boundary.json",
    "failure_family_decomposition_wave_1_plan.json",
    "failure_family_decomposition_wave_1_results.json",
    "bug_layer_registry_wave_1.json",
    "primary_failure_family_selection_wave_1.json",
    "secondary_failure_family_registry_wave_1.json",
    "tertiary_failure_family_registry_wave_1.json",
    "minimal_subtarget_replay_plan_wave_1.json",
    "minimal_subtarget_replay_results_wave_1.json",
    "elbow_activation_gate_wave_1.json",
    "layered_repair_claim_boundary.json",
    "elbow_recovery_candidate_ranking.json",
    "batch057c_patch_recovery_recommendation.json",
    "batch056b_wave2_pre_repair_replay_recommendation.json",
    "wave1_candidate_retirement_registry.json",
    "batch057b_summary.md",
    "claim_boundary.json",
    "audit.json",
    "package_verification.json",
    "artifact_sha256_verification.json",
    "SHA256SUMS.txt",
]
REQUIRED_CANDIDATE_FILES = [
    "failure_family_decomposition.json",
    "bug_layer_registry.json",
    "primary_failure_family_selection.json",
    "secondary_failure_family_registry.json",
    "tertiary_failure_family_registry.json",
    "failure_family_traceback_clusters.json",
    "failure_family_test_node_clusters.json",
    "failure_family_exception_type_clusters.json",
    "failure_family_source_surface_map.json",
    "failure_family_environment_marker_map.json",
    "minimal_subtarget_replay_plan.json",
    "minimal_subtarget_replay_result.json",
    "subtarget_vs_original_target_mapping.json",
    "elbow_activation_gate.json",
    "layered_repair_claim_boundary.json",
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
    return [line.rstrip() for line in result.stdout.splitlines() if line.strip()]


def has_forbidden_new_path(path: str) -> bool:
    normalized = path.replace("\\", "/").lower()
    return (
        "incoming_artifacts/" in normalized
        or "artifact_payload/" in normalized
        or "controllergate_runtime/" in normalized
        or "__pycache__/" in normalized
        or ".pytest_cache/" in normalized
        or ".venv/" in normalized
        or normalized.endswith((".zip", ".tar", ".tgz", ".tar.gz", ".7z", ".whl", ".pyc", ".pyo"))
    )


def expect_false(errors: list[str], record: dict[str, Any], field: str, label: str) -> None:
    if record.get(field) is not False:
        errors.append(f"{label} expected false: {field}")


def main() -> int:
    errors: list[str] = []
    if not OUT_DIR.is_dir():
        print("FAIL: missing Batch057b output directory")
        return 1
    for rel in REQUIRED_TOP_LEVEL:
        if not (OUT_DIR / rel).is_file():
            errors.append(f"missing required Batch057b output: {rel}")
    manifest = verify_manifest(OUT_DIR)
    if manifest.get("status") != "PASS":
        errors.append(f"Batch057b SHA256SUMS mismatch: {manifest}")
    if errors:
        print("FAIL:", errors)
        return 1

    ingest = read_json(OUT_DIR / "batch057_artifact_ingestion_summary.json")
    verification = read_json(OUT_DIR / "batch057_artifact_sha256_verification.json")
    preservation = read_json(OUT_DIR / "batch057_result_preservation.json")
    classification_preservation = read_json(OUT_DIR / "batch057_candidate_classification_preservation.json")
    claim_preservation = read_json(OUT_DIR / "batch057_claim_boundary_preservation.json")
    next_boundary = read_json(OUT_DIR / "batch057_next_action_boundary.json")
    plan = read_json(OUT_DIR / "failure_family_decomposition_wave_1_plan.json")
    results = read_json(OUT_DIR / "failure_family_decomposition_wave_1_results.json")
    layers = read_json(OUT_DIR / "bug_layer_registry_wave_1.json")
    minimal = read_json(OUT_DIR / "minimal_subtarget_replay_results_wave_1.json")
    elbow = read_json(OUT_DIR / "elbow_activation_gate_wave_1.json")
    claim = read_json(OUT_DIR / "claim_boundary.json")
    layered_claim = read_json(OUT_DIR / "layered_repair_claim_boundary.json")
    batch057c = read_json(OUT_DIR / "batch057c_patch_recovery_recommendation.json")
    wave2 = read_json(OUT_DIR / "batch056b_wave2_pre_repair_replay_recommendation.json")
    retired = read_json(OUT_DIR / "wave1_candidate_retirement_registry.json")
    audit = read_json(OUT_DIR / "audit.json")
    package = read_json(OUT_DIR / "package_verification.json")
    artifact_sha = read_json(OUT_DIR / "artifact_sha256_verification.json")

    if ingest.get("status") != "PASS" or verification.get("status") != "PASS":
        errors.append("Batch057 artifact ingest/verification did not PASS")
    if verification.get("zip_sha256") != EXPECTED_BATCH057_SHA256:
        errors.append("Batch057 artifact SHA256 mismatch")
    if verification.get("zip_size_bytes") != EXPECTED_BATCH057_SIZE:
        errors.append("Batch057 artifact byte size mismatch")
    if verification.get("zip_entry_count") != EXPECTED_BATCH057_ENTRY_COUNT:
        errors.append("Batch057 artifact entry count mismatch")
    if verification.get("unsafe_path_count") != 0 or verification.get("duplicate_path_count") != 0:
        errors.append("Batch057 artifact path safety failed")
    if verification.get("zip_pycache_entries") != 0 or verification.get("zip_pyc_entries") != 0:
        errors.append("Batch057 artifact contains pycache/pyc payload")
    if verification.get("artifact_manifest", {}).get("checked") != EXPECTED_BATCH057_ARTIFACT_MANIFEST_CHECKED:
        errors.append("Batch057 artifact manifest coverage mismatch")
    output_manifest = verification.get("output_manifests", {}).get("post_v2_37_hardening_batch057_source_only_patch_gate_wave_1", {})
    if output_manifest.get("checked") != EXPECTED_BATCH057_OUTPUT_MANIFEST_CHECKED:
        errors.append("Batch057 internal output manifest coverage mismatch")
    if verification.get("raw_zip_bytes_ingested") is not False or verification.get("zip_payload_committed") is not False:
        errors.append("Batch057 raw artifact boundary failed")

    if preservation.get("fresh_pre_repair_reproduction_count") != 4:
        errors.append("Batch057 fresh reproduction count not preserved at 4")
    if preservation.get("source_only_patches_generated") != 0:
        errors.append("Batch057 patch-generated count not preserved at 0")
    if preservation.get("patch_target_pass_count") != 0:
        errors.append("Batch057 target-pass count not preserved at 0")
    if preservation.get("batch058_duplicate_replay_candidates") != 0:
        errors.append("Batch058 duplicate replay candidate count not preserved at 0")
    if preservation.get("next_allowed_action") != "batch057b_source_discovery_recovery_or_batch056b_wave2_pre_repair_replay":
        errors.append("Batch057 next action boundary mismatch")
    if classification_preservation.get("candidate_classifications", {}) != {
        "datasette_2461_async_event_loop_cli_tests": "blocked_ambiguous_multi_failure_source_surface",
        "freezegun_547_py313_datetimes_assertion": "blocked_ambiguous_multi_failure_source_surface",
        "pexpect_699_replwrap_bash_assertions": "blocked_environment_specific_failure",
        "venusian_91_py313_frameinfo_callinfo": "blocked_no_safe_source_patch",
    }:
        errors.append("Batch057 candidate classification preservation mismatch")
    if claim_preservation.get("issue_derived_repair_count") != 2:
        errors.append("Issue-derived repair count not preserved at 2")
    if claim_preservation.get("native_external_repair_count") != 4:
        errors.append("Native external repair count not preserved at 4")
    if claim_preservation.get("full_scoring") != "NOT_RUN/disallowed":
        errors.append("Full scoring boundary changed")
    if claim_preservation.get("memory_lift") != "not_demonstrated":
        errors.append("Memory lift boundary changed")
    if claim_preservation.get("self_maintaining_software") != "false/not_demonstrated":
        errors.append("Self-maintaining boundary changed")
    for field in ["batch057b_patch_generated", "batch057b_duplicate_replay_run", "batch057b_count_gate_run", "batch057b_repair_count_increment"]:
        expect_false(errors, claim_preservation, field, "Batch057b claim preservation")
    if next_boundary.get("patching_allowed") is not False or next_boundary.get("duplicate_replay_allowed") is not False or next_boundary.get("count_gate_allowed") is not False:
        errors.append("Batch057b next action boundary allows forbidden action")

    if plan.get("candidate_count") != 4 or set(plan.get("candidate_ids", [])) != EXPECTED_CANDIDATES:
        errors.append("Batch057b plan candidate set mismatch")
    result_rows = results.get("results", [])
    if len(result_rows) != 4 or {row.get("lead_id") for row in result_rows} != EXPECTED_CANDIDATES:
        errors.append("Batch057b results candidate set mismatch")
    if layers.get("status") != "PASS" or len(layers.get("candidates", [])) != 4:
        errors.append("Batch057b bug-layer registry incomplete")
    if minimal.get("minimal_subtarget_replay_count") != 5:
        errors.append("Batch057b minimal subtarget replay count mismatch")
    if elbow.get("open_candidate_count") != 1 or elbow.get("closed_candidate_count") != 3:
        errors.append("Batch057b elbow open/closed counts mismatch")
    if elbow.get("states") != EXPECTED_STATES:
        errors.append("Batch057b elbow states mismatch")
    if batch057c.get("recommended_candidates") != ["freezegun_547_py313_datetimes_assertion"]:
        errors.append("Batch057c recommendation must include only Freezegun")
    if batch057c.get("patching_performed_in_batch057b") is not False or batch057c.get("counting_allowed") is not False:
        errors.append("Batch057c recommendation overclaims Batch057b work")
    if wave2.get("wave2_replay_run_in_batch057b") is not False:
        errors.append("Wave 2 replay ran in Batch057b")
    if retired.get("retired_count") != 1:
        errors.append("Batch057b retired candidate count mismatch")

    for field in [
        "batch057b_patch_generated",
        "batch057b_patch_applied",
        "batch057b_post_repair_target_replay_run",
        "batch057b_duplicate_replay_run",
        "batch057b_count_gate_run",
        "batch057b_repair_count_increment",
    ]:
        expect_false(errors, claim, field, "Batch057b claim boundary")
    if claim.get("current_protocol") != CURRENT_PROTOCOL:
        errors.append("Current protocol not preserved at v2.14")
    if claim.get("issue_derived_repair_count") != 2 or claim.get("native_external_repair_count") != 4:
        errors.append("Repair counts changed in Batch057b claim boundary")
    if claim.get("full_scoring") != "NOT_RUN/disallowed" or claim.get("memory_lift") != "not_demonstrated" or claim.get("self_maintaining_software") != "false/not_demonstrated":
        errors.append("Batch057b public claim boundary overclaim")
    if claim.get("next_allowed_action") != "batch057c_source_only_patch_recovery_wave_1":
        errors.append("Batch057b next allowed action mismatch")
    if claim.get("subtarget_results_are_not_counted_repairs") is not True:
        errors.append("Batch057b did not mark subtargets diagnostic-only")
    if layered_claim.get("batch057b_generated_source_patches") != 0 or layered_claim.get("batch057b_applied_patches") != 0:
        errors.append("Batch057b generated or applied a patch")
    for field in ["post_repair_target_replay_run", "duplicate_replay_run", "count_gate_run", "repair_count_increment"]:
        expect_false(errors, layered_claim, field, "Layered repair claim boundary")
    if audit.get("status") != "PASS":
        errors.append("Batch057b embedded audit status is not PASS")
    if package.get("artifact_name") != "post_v2_37_hardening_batch057b_failure_family_decomposition_elbow_recovery_artifacts":
        errors.append("Batch057b package artifact name mismatch")
    if package.get("raw_zip_payload_committed") is not False:
        errors.append("Batch057b package verification permits raw ZIP payload")
    if artifact_sha.get("status") != "PENDING_WORKFLOW_ARTIFACT" or artifact_sha.get("batch057_local_zip_sha256") != EXPECTED_BATCH057_SHA256:
        errors.append("Batch057b artifact SHA boundary mismatch")

    for row in result_rows:
        lead_id = row.get("lead_id")
        candidate_dir = OUT_DIR / "candidates" / str(lead_id)
        for rel in REQUIRED_CANDIDATE_FILES:
            if not (candidate_dir / rel).is_file():
                errors.append(f"missing candidate output for {lead_id}: {rel}")
        if errors:
            continue
        decomposition = read_json(candidate_dir / "failure_family_decomposition.json")
        registry = read_json(candidate_dir / "bug_layer_registry.json")
        subtarget = read_json(candidate_dir / "minimal_subtarget_replay_result.json")
        elbow_record = read_json(candidate_dir / "elbow_activation_gate.json")
        layered = read_json(candidate_dir / "layered_repair_claim_boundary.json")
        mapping = read_json(candidate_dir / "subtarget_vs_original_target_mapping.json")
        if decomposition.get("failure_family_count", 0) < 1:
            errors.append(f"no failure families recorded for {lead_id}")
        if registry.get("status") != "PASS" or not registry.get("layers"):
            errors.append(f"bug-layer registry incomplete for {lead_id}")
        if subtarget.get("status") != "PASS":
            blocker = candidate_dir / "minimal_subtarget_replay_blocker.json"
            if not blocker.is_file():
                errors.append(f"minimal subtarget replay missing and no blocker for {lead_id}")
        if subtarget.get("counting_allowed") is not False or subtarget.get("patch_success_claim_allowed") is not False:
            errors.append(f"subtarget replay overclaims count/patch success for {lead_id}")
        if elbow_record.get("elbow_activation_state") != EXPECTED_STATES[lead_id]:
            errors.append(f"unexpected elbow state for {lead_id}")
        if (elbow_record.get("elbow_activation_state") in OPEN_STATES) != bool(elbow_record.get("elbow_open")):
            errors.append(f"elbow open flag mismatch for {lead_id}")
        if elbow_record.get("batch057b_patch_generated") is not False or elbow_record.get("batch057b_patch_applied") is not False or elbow_record.get("batch057b_post_repair_replay_run") is not False:
            errors.append(f"candidate elbow gate records forbidden Batch057b repair action for {lead_id}")
        for field in ["patch_generated", "patch_applied", "post_repair_target_replay_run", "duplicate_replay_run", "count_gate_run", "repair_count_increment", "fixed_gold_future_evidence_used", "issue_body_fix_text_used", "tests_modified"]:
            expect_false(errors, layered, field, f"candidate layered boundary {lead_id}")
        if mapping.get("subtarget_success_cannot_count_as_original_target_success") is not True:
            errors.append(f"subtarget/original target mapping missing count boundary for {lead_id}")

    staged_or_changed = git_lines("status", "--short")
    for line in staged_or_changed:
        path = line[3:] if len(line) > 3 else line
        if line.startswith("?? incoming_artifacts/"):
            continue
        if has_forbidden_new_path(path):
            errors.append(f"forbidden path appears in worktree status: {line}")

    if errors:
        print("FAIL:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Batch057b failure-family decomposition elbow recovery audit PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
