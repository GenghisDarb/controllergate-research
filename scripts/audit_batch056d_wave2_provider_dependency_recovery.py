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


OUT_DIR = ROOT / "outputs" / "post_v2_37_hardening_batch056d_wave2_provider_dependency_recovery"
BATCH056B_DIR = ROOT / "outputs" / "post_v2_37_hardening_batch056b_wave2_pre_repair_replay_plus_amds_bridge"
CURRENT_PROTOCOL = "v2.14"
EXPECTED_BATCH056B_SHA256 = "0da4a224d91a7cb5025e4343879788de0cd45fe1b427c975d573f6b71ecc5157"
EXPECTED_BATCH056B_SIZE = 182455
EXPECTED_BATCH056B_ENTRY_COUNT = 254
EXPECTED_BATCH056B_ARTIFACT_MANIFEST_CHECKED = 253
EXPECTED_BATCH056B_OUTPUT_MANIFEST_CHECKED = 252
EXPECTED_RECOVERY_CANDIDATES = [
    "pairtools_250_py313_pipes_removed",
    "pytest_13480_wdefault_unraisable_threadexception",
    "snapshottest_177_py312_imp_removed",
]
EXPECTED_DEFERRED_TIMEOUT_CANDIDATES = [
    "codex_wave2_nousresearch_hermes_agent_48986",
    "codex_wave2_nousresearch_hermes_agent_60243",
    "codex_wave2_nousresearch_hermes_agent_57197",
    "codex_wave2_m0smith_genia_2026_518",
]
REQUIRED_TOP_LEVEL = [
    "batch056b_artifact_ingestion_summary.json",
    "batch056b_artifact_sha256_verification.json",
    "batch056b_result_preservation.json",
    "batch056b_wave2_replay_preservation.json",
    "batch056b_amds_bridge_preservation.json",
    "batch056b_claim_boundary_preservation.json",
    "batch056b_next_action_boundary.json",
    "batch_lineage_map.json",
    "batch_numbering_sanity_check.json",
    "branch_relative_batch_index.json",
    "chronological_execution_index.json",
    "next_allowed_action_validation.json",
    "provider_dependency_recovery_plan.json",
    "provider_dependency_recovery_results.json",
    "provider_dependency_recovery_summary.md",
    "provider_dependency_recovery_dashboard.json",
    "post_recovery_prerepair_replay_results.json",
    "materialized_failure_candidates_after_recovery.json",
    "still_blocked_provider_dependency_candidates.json",
    "timeout_decomposition_deferred_registry.json",
    "future_failure_decomposition_recommendation.json",
    "future_patch_gate_recommendation.json",
    "freezegun_provider_portability_plan_preservation.json",
    "amds_bridge_after_recovery_dashboard.json",
    "batch056d_final_decision.json",
    "claim_boundary.json",
    "audit.json",
    "package_verification.json",
    "artifact_sha256_verification.json",
    "SHA256SUMS.txt",
]
REQUIRED_CANDIDATE_FILES = [
    "dependency_recovery_plan.json",
    "declared_dependency_evidence.json",
    "declared_dependency_lineage.json",
    "provider_recovery_plan.json",
    "provider_recovery_safety_check.json",
    "dependency_install_attempts.json",
    "dependency_recovery_result.json",
    "post_recovery_prerepair_replay_plan.json",
    "post_recovery_prerepair_replay_result.json",
    "post_recovery_prerepair_replay_command.txt",
    "post_recovery_prerepair_replay_log_raw.txt",
    "post_recovery_failure_signature_extract.txt",
    "command_change_justification.json",
    "recovery_not_target_repair_boundary.json",
    "amds_bridge_update_after_recovery.json",
    "classification_after_recovery.json",
    "amds_failure_board_state_after_recovery.json",
    "failure_cell_registry_after_recovery.json",
    "failure_mine_risk_map_after_recovery.json",
    "safe_action_frontier_after_recovery.json",
    "information_gain_move_ranking_after_recovery.json",
    "flagged_unsafe_cells_after_recovery.json",
    "failure_stack_constraint_graph_after_recovery.json",
    "ast_loop_extrusion_bridge_after_recovery.json",
    "source_contact_graph_extrusion_result_after_recovery.json",
    "probe_to_patch_transition_gate_after_recovery.json",
    "patch_license_from_amds_after_recovery.json",
    "amds_candidate_summary_after_recovery.json",
]
ALLOWED_RECOVERY_CLASSIFICATIONS = {
    "provider_dependency_recovery_succeeded_failure_materialized",
    "provider_dependency_recovery_succeeded_failure_not_reproduced",
    "provider_dependency_recovery_succeeded_new_blocker",
    "provider_dependency_recovery_partial",
    "blocked_no_declared_dependency_evidence",
    "blocked_dependency_install_failure",
    "blocked_provider_precondition",
    "blocked_python_version_unavailable",
    "blocked_tox_env_unavailable",
    "blocked_compiled_dependency",
    "blocked_network_required",
    "blocked_timeout",
    "blocked_command_ambiguous",
    "blocked_recovery_would_use_forbidden_evidence",
    "blocked_recovery_would_mutate_target_source",
    "probe_only_needs_manual_review",
}
FUTURE_PATCH_STATES = {
    "future_patch_license_open_single_source_family",
    "future_patch_license_open_primary_family_diagnostic_only",
    "future_decomposition_needed_before_patch",
    "future_provider_dependency_recovery_needed",
    "future_candidate_retired",
    "future_manual_review_needed",
}
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
            errors.append(f"missing required Batch056d output: {rel}")

    if not errors:
        manifest = verify_manifest(OUT_DIR)
        if manifest.get("status") != "PASS":
            errors.append(f"Batch056d SHA256SUMS verification failed: {manifest}")

    if errors:
        print("FAIL:")
        for error in errors:
            print(f"- {error}")
        return 1

    artifact = read_json(OUT_DIR / "batch056b_artifact_sha256_verification.json")
    result_preservation = read_json(OUT_DIR / "batch056b_result_preservation.json")
    replay_preservation = read_json(OUT_DIR / "batch056b_wave2_replay_preservation.json")
    amds_preservation = read_json(OUT_DIR / "batch056b_amds_bridge_preservation.json")
    claim_preservation = read_json(OUT_DIR / "batch056b_claim_boundary_preservation.json")
    next_boundary = read_json(OUT_DIR / "batch056b_next_action_boundary.json")
    lineage = read_json(OUT_DIR / "batch_lineage_map.json")
    numbering = read_json(OUT_DIR / "batch_numbering_sanity_check.json")
    next_validation = read_json(OUT_DIR / "next_allowed_action_validation.json")
    plan = read_json(OUT_DIR / "provider_dependency_recovery_plan.json")
    results = read_json(OUT_DIR / "provider_dependency_recovery_results.json")
    dashboard = read_json(OUT_DIR / "provider_dependency_recovery_dashboard.json")
    replay_results = read_json(OUT_DIR / "post_recovery_prerepair_replay_results.json")
    materialized = read_json(OUT_DIR / "materialized_failure_candidates_after_recovery.json")
    still_blocked = read_json(OUT_DIR / "still_blocked_provider_dependency_candidates.json")
    deferred = read_json(OUT_DIR / "timeout_decomposition_deferred_registry.json")
    future_decomp = read_json(OUT_DIR / "future_failure_decomposition_recommendation.json")
    future_patch = read_json(OUT_DIR / "future_patch_gate_recommendation.json")
    freezegun = read_json(OUT_DIR / "freezegun_provider_portability_plan_preservation.json")
    amds_after = read_json(OUT_DIR / "amds_bridge_after_recovery_dashboard.json")
    final = read_json(OUT_DIR / "batch056d_final_decision.json")
    claim = read_json(OUT_DIR / "claim_boundary.json")
    audit = read_json(OUT_DIR / "audit.json")
    package = read_json(OUT_DIR / "package_verification.json")
    artifact_boundary = read_json(OUT_DIR / "artifact_sha256_verification.json")

    if artifact.get("status") != "PASS":
        errors.append("Batch056b official artifact verification did not pass")
    if artifact.get("zip_sha256") != EXPECTED_BATCH056B_SHA256 or artifact.get("artifact_sha256") != EXPECTED_BATCH056B_SHA256:
        errors.append("Batch056b artifact SHA256 mismatch")
    if artifact.get("zip_size_bytes") != EXPECTED_BATCH056B_SIZE or artifact.get("zip_entry_count") != EXPECTED_BATCH056B_ENTRY_COUNT:
        errors.append("Batch056b artifact size or entry count mismatch")
    if artifact.get("artifact_manifest", {}).get("checked") != EXPECTED_BATCH056B_ARTIFACT_MANIFEST_CHECKED:
        errors.append("Batch056b artifact manifest checked count mismatch")
    output_manifest = artifact.get("output_manifests", {}).get("post_v2_37_hardening_batch056b_wave2_pre_repair_replay_plus_amds_bridge", {})
    if output_manifest.get("checked") != EXPECTED_BATCH056B_OUTPUT_MANIFEST_CHECKED or output_manifest.get("failures") != 0:
        errors.append("Batch056b internal manifest verification mismatch")
    for key in ["unsafe_path_count", "duplicate_path_count", "zip_pycache_entries", "zip_pyc_entries"]:
        if artifact.get(key) != 0:
            errors.append(f"Batch056b artifact has non-zero {key}")
    expect_false(errors, artifact, "raw_zip_bytes_ingested", "Batch056b artifact verification")
    expect_false(errors, artifact, "zip_payload_committed", "Batch056b artifact verification")

    if result_preservation.get("issue_derived_repair_count") != 2 or result_preservation.get("native_external_repair_count") != 4:
        errors.append("Batch056b repair counts not preserved")
    for key in ["batch056b_patch_generated", "batch056b_patch_applied", "batch056b_duplicate_replay_run", "batch056b_count_gate_run"]:
        expect_false(errors, result_preservation, key, "Batch056b result preservation")
    if replay_preservation.get("wave2_candidates_replayed") != 7 or replay_preservation.get("wave2_materialized_target_code_failures") != 0 or replay_preservation.get("wave2_blocked_candidates") != 7:
        errors.append("Batch056b Wave 2 replay preservation mismatch")
    if amds_preservation.get("duplicate_solver_added") is not False:
        errors.append("Batch056b AMDS bridge duplicate solver boundary not preserved")
    if claim_preservation.get("full_scoring") != "NOT_RUN/disallowed" or claim_preservation.get("memory_lift") != "not_demonstrated" or claim_preservation.get("self_maintaining_software") != "false/not_demonstrated":
        errors.append("Batch056b claim boundary overclaim")
    if next_boundary.get("matches_expected") is not True:
        errors.append("Batch056b next action boundary did not permit Batch056d")

    if lineage.get("batch056d_after_batch057c_valid") is not True:
        errors.append("Batch-lineage map did not validate Batch056d after Batch057c")
    if numbering.get("batch056d_is_branch_relative") is not True or numbering.get("chronological_rollback_occurred") is not False:
        errors.append("Batch numbering sanity check failed")
    if numbering.get("batch058_candidate_exists") is not False:
        errors.append("Batch058 candidate incorrectly exists")
    if next_validation.get("batch056d_allowed") is not True or next_validation.get("batch058_allowed") is not False:
        errors.append("Next-action validation allowed the wrong boundary")

    if plan.get("attempted_candidates") != EXPECTED_RECOVERY_CANDIDATES:
        errors.append("Batch056d attempted candidate scope mismatch")
    if plan.get("deferred_timeout_candidates") != EXPECTED_DEFERRED_TIMEOUT_CANDIDATES:
        errors.append("Batch056d deferred timeout candidate set mismatch")
    expect_false(errors, plan, "patch_generation_allowed", "Batch056d provider recovery plan")
    result_rows = results.get("results", [])
    if [row.get("candidate_id") for row in result_rows] != EXPECTED_RECOVERY_CANDIDATES:
        errors.append("Provider/dependency recovery result scope mismatch")
    if set(dashboard.get("classifications", {})) != set(EXPECTED_RECOVERY_CANDIDATES):
        errors.append("Provider/dependency recovery dashboard scope mismatch")
    if len(replay_results.get("results", [])) != 3:
        errors.append("Post-recovery replay results count mismatch")
    if materialized.get("count") != sum(1 for row in result_rows if row.get("materialized_target_code_failure") is True):
        errors.append("Materialized failure count inconsistent")
    if still_blocked.get("count") != sum(1 for row in result_rows if row.get("materialized_target_code_failure") is not True):
        errors.append("Still-blocked count inconsistent")
    if deferred.get("decomposition_run_in_batch056d") is not False or deferred.get("candidates") != EXPECTED_DEFERRED_TIMEOUT_CANDIDATES:
        errors.append("Timeout decomposition deferral violated")
    if not isinstance(future_decomp.get("recommended_candidates"), list):
        errors.append("Future decomposition recommendation missing list")
    if not isinstance(future_patch.get("recommended_candidates"), list):
        errors.append("Future patch-gate recommendation missing list")
    if freezegun.get("freezegun_patched_in_batch056d") is not False:
        errors.append("Freezegun was patched in Batch056d")
    if amds_after.get("patching_authorized_in_batch056d") is not False:
        errors.append("AMDS after-recovery dashboard authorized patching")

    for row in result_rows:
        candidate_id = row.get("candidate_id")
        candidate_dir = OUT_DIR / "candidates" / str(candidate_id)
        for rel in REQUIRED_CANDIDATE_FILES:
            if not (candidate_dir / rel).is_file():
                errors.append(f"missing candidate output for {candidate_id}: {rel}")
        if row.get("classification") not in ALLOWED_RECOVERY_CLASSIFICATIONS:
            errors.append(f"unexpected recovery classification for {candidate_id}: {row.get('classification')}")
        if row.get("future_patch_license_state") not in FUTURE_PATCH_STATES:
            errors.append(f"unexpected future patch-license state for {candidate_id}: {row.get('future_patch_license_state')}")
        for key in ["patch_generated", "patch_applied", "duplicate_replay_run", "count_gate_run"]:
            expect_false(errors, row, key, f"recovery result {candidate_id}")
        if errors:
            continue
        safety = read_json(candidate_dir / "provider_recovery_safety_check.json")
        boundary = read_json(candidate_dir / "recovery_not_target_repair_boundary.json")
        classification = read_json(candidate_dir / "classification_after_recovery.json")
        patch_license = read_json(candidate_dir / "patch_license_from_amds_after_recovery.json")
        gate = read_json(candidate_dir / "probe_to_patch_transition_gate_after_recovery.json")
        evidence = read_json(candidate_dir / "declared_dependency_evidence.json")
        for key in ["fixed_commit_used", "future_commit_used", "gold_patch_used", "pr_patch_used", "source_modified", "tests_modified", "synthetic_tests_added"]:
            expect_false(errors, safety, key, f"safety check {candidate_id}")
        if boundary.get("provider_dependency_recovery_is_not_target_repair") is not True or boundary.get("repair_count_increment_allowed") is not False:
            errors.append(f"provider/dependency recovery counted as repair for {candidate_id}")
        if classification.get("classification") != row.get("classification"):
            errors.append(f"classification file mismatch for {candidate_id}")
        if patch_license.get("patch_execution_authorized_in_batch056d") is not False:
            errors.append(f"patch execution authorized for {candidate_id}")
        if gate.get("transition_gate") != "CLOSED_IN_BATCH056D":
            errors.append(f"patch transition gate open for {candidate_id}")
        if evidence.get("forbidden_evidence_used") is not False:
            errors.append(f"forbidden dependency evidence used for {candidate_id}")

    for key in ["patch_generated", "patch_applied", "post_repair_replay_run", "duplicate_replay_run", "count_gate_run", "repair_count_increment"]:
        expect_false(errors, final, key, "Batch056d final decision")
    if claim.get("current_protocol") != CURRENT_PROTOCOL:
        errors.append("Current protocol changed from v2.14")
    if claim.get("issue_derived_repair_count") != 2 or claim.get("native_external_repair_count") != 4:
        errors.append("Repair counts changed in Batch056d claim boundary")
    if claim.get("full_scoring") != "NOT_RUN/disallowed" or claim.get("memory_lift") != "not_demonstrated" or claim.get("self_maintaining_software") != "false/not_demonstrated":
        errors.append("Batch056d claim boundary overclaim")
    for key in [
        "batch056d_patch_generated",
        "batch056d_patch_applied",
        "batch056d_post_repair_replay_run",
        "batch056d_duplicate_replay_run",
        "batch056d_count_gate_run",
        "batch056d_repair_count_increment",
        "freezegun_patched_in_batch056d",
        "wave2_patched_in_batch056d",
    ]:
        expect_false(errors, claim, key, "Batch056d claim boundary")
    if audit.get("status") != "PASS":
        errors.append("Embedded Batch056d audit marker is not PASS")
    expect_false(errors, package, "raw_zip_payload_committed", "Batch056d package verification")
    expect_false(errors, package, "runtime_workspaces_committed", "Batch056d package verification")
    if artifact_boundary.get("status") != "PENDING_WORKFLOW_ARTIFACT":
        errors.append("Batch056d artifact boundary should remain pending workflow upload")

    batch056b_final = read_json(BATCH056B_DIR / "batch056b_final_decision.json")
    if batch056b_final.get("next_allowed_action") != "batch056d_wave2_provider_dependency_recovery":
        errors.append("Existing Batch056b next action changed")

    audit_git_status(errors)

    if errors:
        print("FAIL:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Batch056d Wave 2 provider/dependency recovery audit PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
