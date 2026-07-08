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


OUT_DIR = ROOT / "outputs" / "post_v2_37_hardening_batch059_pre_repair_replay_wave_3_limited"
BATCH058_DIR = ROOT / "outputs" / "post_v2_37_hardening_batch058_seed_discovery_wave_3_provider_prescreen"
CURRENT_PROTOCOL = "v2.14"
EXPECTED_CANDIDATES = {
    "audioread_144_py313_aifc_removed",
    "cloudpickle_507_py313_typevar_distutils",
}
EXPECTED_BATCH058_SHA256 = "899dc0fbdc039efd04727ce8b1065fd673afe013ec60251d0dc735c17a31ad1d"
EXPECTED_BATCH058_SIZE = 375462
EXPECTED_BATCH058_ENTRY_COUNT = 447
EXPECTED_BATCH058_ARTIFACT_MANIFEST_CHECKED = 446
EXPECTED_BATCH058_OUTPUT_MANIFEST_CHECKED = 445

REQUIRED_TOP_LEVEL = [
    "batch058_artifact_ingestion_summary.json",
    "batch058_artifact_sha256_verification.json",
    "batch058_result_preservation.json",
    "batch058_wave3_provider_prescreen_preservation.json",
    "batch058_candidate_plan_preservation.json",
    "batch058_claim_boundary_preservation.json",
    "batch058_next_action_boundary.json",
    "batch059_pre_repair_replay_plan.json",
    "batch059_pre_repair_replay_results.json",
    "batch059_materialized_failure_registry.json",
    "batch059_blocked_candidate_registry.json",
    "batch059_failure_not_reproduced_registry.json",
    "batch059_amds_bridge_dashboard.json",
    "batch059_future_decomposition_recommendation.json",
    "batch059_future_patch_gate_recommendation.json",
    "batch059_future_provider_recovery_recommendation.json",
    "batch059_summary.md",
    "batch059_final_decision.json",
    "claim_boundary.json",
    "audit.json",
    "package_verification.json",
    "artifact_sha256_verification.json",
    "SHA256SUMS.txt",
]

PER_CANDIDATE_FILES = [
    "decision_time_input_manifest.json",
    "forbidden_evidence_audit.json",
    "issue_body_leakage_boundary.json",
    "label_blindness_check.json",
    "gold_patch_exclusion_check.json",
    "future_evidence_exclusion_check.json",
    "candidate_replay_plan.json",
    "candidate_commit_verification.json",
    "candidate_workspace_manifest.json",
    "candidate_provider_capsule_preservation.json",
    "candidate_dependency_plan.json",
    "candidate_command_context.json",
    "candidate_command_normalization.json",
    "candidate_provider_precondition_check.json",
    "workspace_custody_check.json",
    "provider_capsule_replay_plan.json",
    "provider_capsule_setup_trace.json",
    "provider_capsule_setup_result.json",
    "provider_capsule_not_repair_boundary.json",
    "provider_capsule_install_log_raw.txt",
    "pre_repair_replay_command.txt",
    "pre_repair_replay_result.json",
    "pre_repair_replay_classification.json",
    "amds_replay_board_state.json",
    "failure_cell_registry.json",
    "failure_mine_risk_map.json",
    "safe_action_frontier.json",
    "information_gain_move_ranking.json",
    "flagged_unsafe_cells.json",
    "failure_stack_constraint_graph.json",
    "ast_loop_extrusion_bridge.json",
    "probe_to_patch_transition_gate.json",
    "patch_license_from_amds.json",
    "amds_candidate_summary.json",
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


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def git_lines(*args: str) -> list[str]:
    completed = subprocess.run(["git", *args], cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    return [line.rstrip("\n") for line in completed.stdout.splitlines()]


def expect_false(errors: list[str], obj: dict[str, Any], key: str, context: str) -> None:
    if obj.get(key) is not False:
        errors.append(f"{context}: expected {key}=false")


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
    for rel in REQUIRED_TOP_LEVEL:
        if not (OUT_DIR / rel).is_file():
            errors.append(f"missing required Batch059 output: {rel}")
    if not errors:
        manifest = verify_manifest(OUT_DIR)
        if manifest.get("status") != "PASS":
            errors.append(f"Batch059 SHA256SUMS verification failed: {manifest}")
    if errors:
        print("FAIL:")
        for error in errors:
            print(f"- {error}")
        return 1

    artifact = read_json(OUT_DIR / "batch058_artifact_sha256_verification.json")
    ingest = read_json(OUT_DIR / "batch058_artifact_ingestion_summary.json")
    preservation = read_json(OUT_DIR / "batch058_result_preservation.json")
    next_boundary = read_json(OUT_DIR / "batch058_next_action_boundary.json")
    plan = read_json(OUT_DIR / "batch059_pre_repair_replay_plan.json")
    results = read_json(OUT_DIR / "batch059_pre_repair_replay_results.json")
    materialized = read_json(OUT_DIR / "batch059_materialized_failure_registry.json")
    blocked = read_json(OUT_DIR / "batch059_blocked_candidate_registry.json")
    not_reproduced = read_json(OUT_DIR / "batch059_failure_not_reproduced_registry.json")
    decomposition = read_json(OUT_DIR / "batch059_future_decomposition_recommendation.json")
    patch_gate = read_json(OUT_DIR / "batch059_future_patch_gate_recommendation.json")
    provider_recovery = read_json(OUT_DIR / "batch059_future_provider_recovery_recommendation.json")
    final = read_json(OUT_DIR / "batch059_final_decision.json")
    claim = read_json(OUT_DIR / "claim_boundary.json")
    package = read_json(OUT_DIR / "package_verification.json")

    if artifact.get("status") != "PASS":
        errors.append("Batch058 artifact verification did not pass")
    if artifact.get("zip_sha256") != EXPECTED_BATCH058_SHA256 or artifact.get("artifact_sha256") != EXPECTED_BATCH058_SHA256:
        errors.append("Batch058 artifact SHA mismatch")
    if artifact.get("zip_size_bytes") != EXPECTED_BATCH058_SIZE or artifact.get("zip_entry_count") != EXPECTED_BATCH058_ENTRY_COUNT:
        errors.append("Batch058 artifact size or entry count mismatch")
    if artifact.get("artifact_manifest", {}).get("checked") != EXPECTED_BATCH058_ARTIFACT_MANIFEST_CHECKED:
        errors.append("Batch058 artifact manifest checked count mismatch")
    output_manifest = artifact.get("output_manifests", {}).get("post_v2_37_hardening_batch058_seed_discovery_wave_3_provider_prescreen", {})
    if output_manifest.get("checked") != EXPECTED_BATCH058_OUTPUT_MANIFEST_CHECKED or output_manifest.get("failures") != 0:
        errors.append("Batch058 internal manifest verification mismatch")
    for key in ["unsafe_path_count", "duplicate_path_count", "zip_pycache_entries", "zip_pyc_entries"]:
        if artifact.get(key) != 0:
            errors.append(f"Batch058 artifact has non-zero {key}")
    if ingest.get("status") != "PASS" or ingest.get("artifact_verification", {}).get("status") != "PASS":
        errors.append("Batch058 official ingest did not pass")
    expect_false(errors, artifact, "raw_zip_bytes_ingested", "Batch058 artifact verification")
    expect_false(errors, artifact, "zip_payload_committed", "Batch058 artifact verification")

    if preservation.get("issue_derived_repair_count") != 2 or preservation.get("native_external_repair_count") != 4:
        errors.append("Batch058 repair counts not preserved")
    if preservation.get("full_scoring") != "NOT_RUN/disallowed":
        errors.append("Full scoring boundary changed")
    if preservation.get("memory_lift") != "not_demonstrated" or preservation.get("self_maintaining_software") != "false/not_demonstrated":
        errors.append("Batch058 claim boundaries changed")
    for key in ["batch058_pre_repair_replay_run", "batch058_patch_generated", "batch058_patch_applied", "batch058_duplicate_replay_run", "batch058_count_gate_run"]:
        expect_false(errors, preservation, key, "Batch058 result preservation")
    if next_boundary.get("status") != "PASS" or next_boundary.get("observed_next_allowed_action") != "batch059_pre_repair_replay_wave_3_limited":
        errors.append("Batch058 next-action boundary does not authorize Batch059")

    planned_ids = set(plan.get("candidate_ids", []))
    if planned_ids != EXPECTED_CANDIDATES:
        errors.append(f"Batch059 operated on unexpected candidate scope: {sorted(planned_ids)}")
    for key in ["patch_generation_allowed", "post_repair_replay_allowed", "duplicate_replay_allowed", "count_gate_allowed"]:
        expect_false(errors, plan, key, "Batch059 plan")

    candidate_results = results.get("candidate_results", [])
    result_ids = {row.get("candidate_id") for row in candidate_results}
    if result_ids != EXPECTED_CANDIDATES:
        errors.append(f"Batch059 results have unexpected candidate scope: {sorted(result_ids)}")
    final_results = final.get("candidate_results", [])
    if {row.get("candidate_id") for row in final_results} != EXPECTED_CANDIDATES:
        errors.append("Final decision candidate scope mismatch")

    for row in final_results:
        cid = row.get("candidate_id")
        cdir = OUT_DIR / "candidates" / cid
        if not cdir.is_dir():
            errors.append(f"missing candidate directory: {cid}")
            continue
        for rel in PER_CANDIDATE_FILES:
            if not (cdir / rel).is_file():
                errors.append(f"missing candidate file for {cid}: {rel}")
        if not ((cdir / "pre_repair_replay_log_raw.txt").is_file() or (cdir / "pre_repair_replay_not_run_reason.txt").is_file()):
            errors.append(f"missing pre-repair replay log or exact blocker for {cid}")
        if not ((cdir / "failure_signature_extract.txt").is_file() or (cdir / "failure_signature_not_available.json").is_file()):
            errors.append(f"missing failure signature output for {cid}")
        commit = read_json(cdir / "candidate_commit_verification.json")
        if commit.get("status") != "PASS" or commit.get("commit_resolved") is not True:
            errors.append(f"commit verification failed for {cid}")
        capsule = read_json(cdir / "candidate_provider_capsule_preservation.json")
        if capsule.get("batch058_approval_status") != "approved_for_provider_prescreen":
            errors.append(f"Batch058 provider capsule not preserved for {cid}")
        setup = read_json(cdir / "provider_capsule_setup_result.json")
        if setup.get("provider_setup_is_repair_success") is not False:
            errors.append(f"provider setup counted as repair success for {cid}")
        replay = read_json(cdir / "pre_repair_replay_result.json")
        for key in ["patch_generated", "patch_applied", "post_repair_replay_run", "duplicate_replay_run", "count_gate_run"]:
            expect_false(errors, replay, key, f"pre-repair replay result for {cid}")
        if replay.get("repair_success_claim_allowed") is not False:
            errors.append(f"materialized failure counted as repair success for {cid}")
        forbidden = read_json(cdir / "forbidden_evidence_audit.json")
        if forbidden.get("status") != "PASS":
            errors.append(f"forbidden evidence audit failed for {cid}")
        for key, value in forbidden.items():
            if key.endswith("_used") and value is not False:
                errors.append(f"forbidden evidence used for {cid}: {key}")
        leakage = read_json(cdir / "issue_body_leakage_boundary.json")
        if leakage.get("issue_body_text_persisted") is not False or leakage.get("issue_body_fix_or_workaround_text_used") is not False:
            errors.append(f"issue body leakage boundary failed for {cid}")
        workspace = read_json(cdir / "workspace_custody_check.json")
        if workspace.get("workspace_outside_repo") is not True or workspace.get("source_mutated") is not False or workspace.get("tests_mutated") is not False:
            errors.append(f"workspace custody failed for {cid}")
        amds = read_json(cdir / "amds_candidate_summary.json")
        if amds.get("repair_success_claim_allowed") is not False or amds.get("patch_execution_allowed_in_batch059") is not False:
            errors.append(f"AMDS boundary overclaim for {cid}")
        license_record = read_json(cdir / "patch_license_from_amds.json")
        if license_record.get("license_executed") is not False or license_record.get("license_future_only") is not True:
            errors.append(f"patch license executed in Batch059 for {cid}")

    if final.get("target_code_failure_materialization_count") != len(materialized.get("records", [])):
        errors.append("materialized failure count mismatch")
    if final.get("blocked_candidate_count") != len(blocked.get("records", [])):
        errors.append("blocked candidate count mismatch")
    if final.get("failure_not_reproduced_count") != len(not_reproduced.get("records", [])):
        errors.append("failure-not-reproduced count mismatch")
    if final.get("future_decomposition_candidates") != decomposition.get("candidate_ids"):
        errors.append("future decomposition recommendation mismatch")
    if final.get("future_patch_gate_candidates") != patch_gate.get("candidate_ids"):
        errors.append("future patch-gate recommendation mismatch")
    if final.get("future_provider_recovery_candidates") != provider_recovery.get("candidate_ids"):
        errors.append("future provider recovery recommendation mismatch")

    for key in ["patch_generated", "patch_applied", "source_mutated", "tests_mutated", "post_repair_replay_run", "duplicate_replay_run", "count_gate_run", "repair_count_increment"]:
        expect_false(errors, final, key, "Batch059 final decision")
    if final.get("issue_derived_repair_count") != 2 or final.get("native_external_repair_count") != 4:
        errors.append("repair counts changed in Batch059")
    if final.get("full_scoring") != "NOT_RUN/disallowed" or final.get("memory_lift") != "not_demonstrated" or final.get("self_maintaining_software") != "false/not_demonstrated":
        errors.append("Batch059 overclaim")
    if final.get("current_protocol") != CURRENT_PROTOCOL:
        errors.append("Current protocol changed from v2.14")
    if final.get("next_allowed_action") not in {
        "batch060_failure_family_decomposition_wave_3",
        "batch060_source_only_patch_gate_wave_3",
        "batch059b_provider_runtime_recovery_wave_3",
        "batch058b_seed_discovery_wave_3_expansion",
    }:
        errors.append("Batch059 next_allowed_action is not an allowed future route")
    for key in ["patch_generated", "patch_applied", "source_mutated", "tests_mutated", "post_repair_replay_run", "duplicate_replay_run", "count_gate_run", "repair_count_increment"]:
        expect_false(errors, claim, key, "Batch059 claim boundary")
    if claim.get("materialized_failure_is_repair_success") is not False or claim.get("provider_setup_is_repair_success") is not False:
        errors.append("provider setup or materialized failure overclaimed as repair success")
    for key in ["raw_zip_payload_committed", "runtime_workspaces_committed", "source_checkouts_committed", "venvs_committed", "caches_committed", "repair_count_increment"]:
        expect_false(errors, package, key, "Batch059 package verification")

    batch058_final = read_json(BATCH058_DIR / "batch058_final_decision.json")
    if batch058_final.get("next_allowed_action") != "batch059_pre_repair_replay_wave_3_limited":
        errors.append("Existing Batch058 next action changed")
    audit_git_status(errors)
    if errors:
        print("FAIL:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Batch059 pre-repair replay wave 3 limited audit PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
