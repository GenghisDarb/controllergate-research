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


OUT_DIR = ROOT / "outputs" / "post_v2_37_hardening_batch056b_wave2_pre_repair_replay_plus_amds_bridge"
CURRENT_PROTOCOL = "v2.14"
EXPECTED_BATCH057C_SHA256 = "86184c8517bc091bf5d43cc257216cafa22e247973d496310251c70983ca9889"
EXPECTED_BATCH057C_SIZE = 42862
EXPECTED_BATCH057C_ENTRY_COUNT = 65
EXPECTED_BATCH057C_ARTIFACT_MANIFEST_CHECKED = 64
EXPECTED_BATCH057C_OUTPUT_MANIFEST_CHECKED = 63
EXPECTED_ARTIFACT = "post_v2_37_hardening_batch056b_wave2_pre_repair_replay_plus_amds_bridge_artifacts"
EXPECTED_WAVE2_IDS = [
    "pairtools_250_py313_pipes_removed",
    "pytest_13480_wdefault_unraisable_threadexception",
    "snapshottest_177_py312_imp_removed",
    "codex_wave2_nousresearch_hermes_agent_48986",
    "codex_wave2_nousresearch_hermes_agent_60243",
    "codex_wave2_nousresearch_hermes_agent_57197",
    "codex_wave2_m0smith_genia_2026_518",
]
REQUIRED_TOP_LEVEL = [
    "batch057c_artifact_ingestion_summary.json",
    "batch057c_artifact_sha256_verification.json",
    "batch057c_result_preservation.json",
    "batch057c_freezegun_partial_improvement_preservation.json",
    "batch057c_stage2_provider_blocker_preservation.json",
    "batch057c_claim_boundary_preservation.json",
    "batch057c_next_action_boundary.json",
    "freezegun_provider_portability_secondary_family_plan.json",
    "amds_existing_capability_inventory.json",
    "minimal_probe_lineage_trace.json",
    "amds_non_duplication_check.json",
    "amds_to_repair_gap_report.json",
    "amds_bridge_scope_lock.json",
    "failure_stack_constraint_graph_schema.json",
    "ast_loop_extrusion_bridge_schema.json",
    "probe_to_patch_transition_gate_schema.json",
    "safe_action_frontier_schema.json",
    "patch_license_from_amds_schema.json",
    "wave2_candidate_plan_preservation.json",
    "wave2_candidate_plan_diff_from_prompt.json",
    "wave2_pre_repair_replay_plan.json",
    "wave2_pre_repair_replay_results.json",
    "wave2_materialized_failure_registry.json",
    "wave2_blocked_candidate_registry.json",
    "wave2_amds_bridge_dashboard.json",
    "wave2_candidate_ranking_for_next_patch_gate.json",
    "wave2_candidate_ranking_for_decomposition.json",
    "wave2_candidate_retirement_registry.json",
    "wave2_exact_blockers.json",
    "batch056b_final_decision.json",
    "batch056b_summary.md",
    "claim_boundary.json",
    "audit.json",
    "package_verification.json",
    "artifact_sha256_verification.json",
    "SHA256SUMS.txt",
]
REQUIRED_CANDIDATE_FILES = [
    "candidate_replay_plan.json",
    "candidate_commit_verification.json",
    "candidate_workspace_manifest.json",
    "candidate_dependency_plan.json",
    "candidate_command_context.json",
    "candidate_command_normalization.json",
    "decision_time_input_manifest.json",
    "issue_body_leakage_boundary.json",
    "label_blindness_check.json",
    "gold_patch_exclusion_check.json",
    "future_evidence_exclusion_check.json",
    "workspace_custody_check.json",
    "provider_precondition_check.json",
    "pre_repair_replay_command.txt",
    "pre_repair_replay_result.json",
    "classification.json",
    "amds_failure_board_state.json",
    "failure_cell_registry.json",
    "failure_mine_risk_map.json",
    "safe_action_frontier.json",
    "information_gain_move_ranking.json",
    "flagged_unsafe_cells.json",
    "minimal_probe_lineage_candidate.json",
    "failure_stack_constraint_graph.json",
    "ast_loop_extrusion_bridge.json",
    "source_contact_graph_extrusion_result.json",
    "probe_to_patch_transition_gate.json",
    "patch_license_from_amds.json",
    "amds_candidate_summary.json",
]
ALLOWED_REPLAY_CLASSIFICATIONS = {
    "pre_repair_failure_materialized",
    "failure_not_reproduced",
    "blocked_dependency_install_failure",
    "blocked_python_version_unavailable",
    "blocked_tox_env_unavailable",
    "blocked_native_test_missing",
    "blocked_repo_checkout_failure",
    "blocked_commit_unresolved",
    "blocked_command_ambiguous",
    "blocked_environment_unclear",
    "blocked_timeout",
    "blocked_network_required",
    "blocked_compiled_dependency",
    "blocked_provider_precondition",
    "blocked_decision_time_leakage_risk",
    "blocked_issue_mismatch",
    "blocked_probe_only_source",
    "probe_only_needs_manual_review",
}
PATCH_OPEN_STATES = {
    "amds_bridge_patch_license_future_open_single_source_family",
    "amds_bridge_patch_license_future_open_primary_family_diagnostic_only",
}
ALLOWED_BRIDGE_CLASSIFICATIONS = PATCH_OPEN_STATES | {
    "amds_bridge_decomposition_needed",
    "amds_bridge_provider_precondition_needed",
    "amds_bridge_dependency_materialization_needed",
    "amds_bridge_interpreter_behavior_track_needed",
    "amds_bridge_manual_review_needed",
    "amds_bridge_candidate_retired",
    "amds_bridge_probe_only_quarantine",
    "amds_bridge_blocked_no_materialized_failure",
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


def expect_true(errors: list[str], obj: dict[str, Any], key: str, context: str) -> None:
    if obj.get(key) is not True:
        errors.append(f"{context}: expected {key}=true")


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
            errors.append(f"missing required Batch056b output: {rel}")

    if not errors:
        manifest = verify_manifest(OUT_DIR)
        if manifest.get("status") != "PASS":
            errors.append(f"Batch056b SHA256SUMS verification failed: {manifest}")

    if errors:
        print("FAIL:")
        for error in errors:
            print(f"- {error}")
        return 1

    artifact = read_json(OUT_DIR / "batch057c_artifact_sha256_verification.json")
    partial = read_json(OUT_DIR / "batch057c_freezegun_partial_improvement_preservation.json")
    blocker = read_json(OUT_DIR / "batch057c_stage2_provider_blocker_preservation.json")
    claim057c = read_json(OUT_DIR / "batch057c_claim_boundary_preservation.json")
    next057c = read_json(OUT_DIR / "batch057c_next_action_boundary.json")
    freezegun_plan = read_json(OUT_DIR / "freezegun_provider_portability_secondary_family_plan.json")
    inventory = read_json(OUT_DIR / "amds_existing_capability_inventory.json")
    lineage = read_json(OUT_DIR / "minimal_probe_lineage_trace.json")
    nondup = read_json(OUT_DIR / "amds_non_duplication_check.json")
    scope = read_json(OUT_DIR / "amds_bridge_scope_lock.json")
    plan = read_json(OUT_DIR / "wave2_candidate_plan_preservation.json")
    diff = read_json(OUT_DIR / "wave2_candidate_plan_diff_from_prompt.json")
    results = read_json(OUT_DIR / "wave2_pre_repair_replay_results.json")
    materialized = read_json(OUT_DIR / "wave2_materialized_failure_registry.json")
    blocked = read_json(OUT_DIR / "wave2_blocked_candidate_registry.json")
    dashboard = read_json(OUT_DIR / "wave2_amds_bridge_dashboard.json")
    patch_gate = read_json(OUT_DIR / "wave2_candidate_ranking_for_next_patch_gate.json")
    decomposition = read_json(OUT_DIR / "wave2_candidate_ranking_for_decomposition.json")
    final = read_json(OUT_DIR / "batch056b_final_decision.json")
    claim = read_json(OUT_DIR / "claim_boundary.json")
    embedded_audit = read_json(OUT_DIR / "audit.json")
    package = read_json(OUT_DIR / "package_verification.json")
    artifact_sha = read_json(OUT_DIR / "artifact_sha256_verification.json")

    if artifact.get("status") != "PASS":
        errors.append("Batch057c artifact verification did not pass")
    if artifact.get("zip_sha256") != EXPECTED_BATCH057C_SHA256 or artifact.get("artifact_sha256") != EXPECTED_BATCH057C_SHA256:
        errors.append("Batch057c artifact SHA256 mismatch")
    if artifact.get("zip_size_bytes") != EXPECTED_BATCH057C_SIZE or artifact.get("artifact_size_bytes") != EXPECTED_BATCH057C_SIZE:
        errors.append("Batch057c artifact size mismatch")
    if artifact.get("zip_entry_count") != EXPECTED_BATCH057C_ENTRY_COUNT:
        errors.append("Batch057c ZIP entry count mismatch")
    if artifact.get("artifact_manifest", {}).get("checked") != EXPECTED_BATCH057C_ARTIFACT_MANIFEST_CHECKED:
        errors.append("Batch057c artifact manifest checked count mismatch")
    output_manifest = artifact.get("output_manifests", {}).get("post_v2_37_hardening_batch057c_layered_source_only_patch_recovery_freezegun", {})
    if output_manifest.get("checked") != EXPECTED_BATCH057C_OUTPUT_MANIFEST_CHECKED or output_manifest.get("failures") != 0:
        errors.append("Batch057c internal manifest verification mismatch")
    for key in ["unsafe_path_count", "duplicate_path_count", "zip_pycache_entries", "zip_pyc_entries"]:
        if artifact.get(key) != 0:
            errors.append(f"Batch057c artifact has non-zero {key}")
    expect_false(errors, artifact, "raw_zip_bytes_ingested", "Batch057c artifact verification")
    expect_false(errors, artifact, "zip_payload_committed", "Batch057c artifact verification")

    expect_true(errors, partial, "stage1_primary_patch_partial_improvement", "Freezegun partial preservation")
    expect_true(errors, partial, "stage1_primary_family_passed", "Freezegun partial preservation")
    expect_true(errors, partial, "partial_improvement_not_counted", "Freezegun partial preservation")
    expect_false(errors, partial, "freezegun_patched_in_batch056b", "Freezegun partial preservation")
    if blocker.get("status") != "PASS" or blocker.get("stage2_authorization") != "BLOCK":
        errors.append("Freezegun Stage 2 provider blocker not preserved")
    if blocker.get("exact_blocker") != "secondary_family_provider_tzset_unavailable":
        errors.append("Freezegun Stage 2 exact blocker mismatch")
    if claim057c.get("issue_derived_repair_count") != 2 or claim057c.get("native_external_repair_count") != 4:
        errors.append("Batch057c repair counts not preserved")
    if claim057c.get("full_scoring") != "NOT_RUN/disallowed" or claim057c.get("memory_lift") != "not_demonstrated" or claim057c.get("self_maintaining_software") != "false/not_demonstrated":
        errors.append("Batch057c claim boundary changed")
    if next057c.get("batch056b_is_that_next_allowed_action") is not True:
        errors.append("Batch057c next action boundary does not point to Batch056b")
    if freezegun_plan.get("batch056b_executes_provider_recovery") is not False:
        errors.append("Batch056b executed forbidden Freezegun provider recovery")

    expect_true(errors, inventory, "amds_already_exists", "AMDS inventory")
    expect_true(errors, inventory, "minimal_probe_already_exists", "AMDS inventory")
    expect_false(errors, inventory, "batch056b_adds_new_solver", "AMDS inventory")
    expect_true(errors, lineage, "minimal_probe_outputs_are_hypotheses_only", "MinimalProbe lineage")
    expect_false(errors, lineage, "repair_proof_claimed", "MinimalProbe lineage")
    expect_true(errors, nondup, "existing_amds_capability", "AMDS non-duplication")
    expect_true(errors, nondup, "existing_minimal_probe_capability", "AMDS non-duplication")
    expect_false(errors, nondup, "new_solver_added", "AMDS non-duplication")
    expect_false(errors, nondup, "probe_outputs_treated_as_repair_evidence", "AMDS non-duplication")
    expect_true(errors, scope, "bridge_instrumentation_added", "AMDS bridge scope")
    expect_false(errors, scope, "patching_authorized_in_batch056b", "AMDS bridge scope")
    expect_true(errors, scope, "probe_outputs_treated_as_hypotheses_only", "AMDS bridge scope")
    expect_true(errors, scope, "seed_promotion_requires_gate", "AMDS bridge scope")

    for rel in [
        "failure_stack_constraint_graph_schema.json",
        "ast_loop_extrusion_bridge_schema.json",
        "probe_to_patch_transition_gate_schema.json",
        "safe_action_frontier_schema.json",
        "patch_license_from_amds_schema.json",
    ]:
        if read_json(OUT_DIR / rel).get("status") != "PASS":
            errors.append(f"schema artifact does not pass: {rel}")

    if plan.get("candidate_count") != 7 or plan.get("candidate_ids") != EXPECTED_WAVE2_IDS:
        errors.append("Wave 2 candidate plan was not preserved exactly")
    if diff.get("status") != "PASS" or diff.get("differences") != []:
        errors.append("Wave 2 prompt/artifact candidate-plan diff not clean")
    result_rows = results.get("results", [])
    if results.get("candidate_count") != 7 or {row.get("lead_id") for row in result_rows} != set(EXPECTED_WAVE2_IDS):
        errors.append("Wave 2 replay results candidate set mismatch")
    if materialized.get("count") != 0:
        errors.append("Batch056b should not record target-code materialized failures after boundary classification")
    if blocked.get("count") != 7:
        errors.append("Batch056b blocked/not-materialized count mismatch")
    if dashboard.get("patching_authorized_in_batch056b") is not False:
        errors.append("AMDS dashboard authorized patching")
    if patch_gate.get("candidate_count") != 0 or patch_gate.get("recommended_candidates") != []:
        errors.append("Batch056b recommended a future patch gate despite only boundary failures")
    if set(decomposition.get("recommended_candidates", [])) != {
        "codex_wave2_nousresearch_hermes_agent_48986",
        "codex_wave2_nousresearch_hermes_agent_60243",
        "codex_wave2_nousresearch_hermes_agent_57197",
        "codex_wave2_m0smith_genia_2026_518",
    }:
        errors.append("Wave 2 decomposition recommendation set mismatch")
    if final.get("next_allowed_action") != "batch056d_wave2_provider_dependency_recovery":
        errors.append("Batch056b final next action mismatch")
    for key in ["patch_generated", "patch_applied", "duplicate_replay_run", "count_gate_run"]:
        expect_false(errors, final, key, "Batch056b final decision")

    if claim.get("current_protocol") != CURRENT_PROTOCOL:
        errors.append("Current protocol not preserved at v2.14")
    if claim.get("issue_derived_repair_count") != 2 or claim.get("native_external_repair_count") != 4:
        errors.append("Repair counts changed in Batch056b claim boundary")
    if claim.get("full_scoring") != "NOT_RUN/disallowed" or claim.get("memory_lift") != "not_demonstrated" or claim.get("self_maintaining_software") != "false/not_demonstrated":
        errors.append("Batch056b public claim boundary overclaim")
    for key in [
        "batch056b_patch_generated",
        "batch056b_patch_applied",
        "batch056b_post_repair_replay_run",
        "batch056b_duplicate_replay_run",
        "batch056b_count_gate_run",
        "batch056b_repair_count_increment",
        "freezegun_patched_in_batch056b",
        "wave2_patched_in_batch056b",
    ]:
        expect_false(errors, claim, key, "Batch056b claim boundary")
    if embedded_audit.get("status") != "PASS":
        errors.append("Embedded Batch056b audit marker is not PASS")
    if package.get("artifact_name") != EXPECTED_ARTIFACT:
        errors.append("Batch056b package artifact name mismatch")
    expect_false(errors, package, "raw_zip_payload_committed", "Batch056b package verification")
    if artifact_sha.get("status") != "PENDING_WORKFLOW_ARTIFACT" or artifact_sha.get("artifact_name") != EXPECTED_ARTIFACT:
        errors.append("Batch056b workflow artifact SHA boundary mismatch")
    if artifact_sha.get("batch057c_local_zip_sha256") != EXPECTED_BATCH057C_SHA256:
        errors.append("Batch056b artifact SHA record lost Batch057c custody hash")

    for row in result_rows:
        lead_id = row.get("lead_id")
        candidate_dir = OUT_DIR / "candidates" / str(lead_id)
        for rel in REQUIRED_CANDIDATE_FILES:
            if not (candidate_dir / rel).is_file():
                errors.append(f"missing candidate artifact for {lead_id}: {rel}")
        if not ((candidate_dir / "pre_repair_replay_log_raw.txt").is_file() or (candidate_dir / "pre_repair_replay_not_run_reason.txt").is_file()):
            errors.append(f"missing replay log or not-run reason for {lead_id}")
        if not ((candidate_dir / "failure_signature_extract.txt").is_file() or (candidate_dir / "failure_signature_not_available.json").is_file()):
            errors.append(f"missing failure signature artifact for {lead_id}")
        if errors:
            continue
        replay = read_json(candidate_dir / "pre_repair_replay_result.json")
        classification = read_json(candidate_dir / "classification.json")
        decision_inputs = read_json(candidate_dir / "decision_time_input_manifest.json")
        leakage = read_json(candidate_dir / "issue_body_leakage_boundary.json")
        label = read_json(candidate_dir / "label_blindness_check.json")
        gold = read_json(candidate_dir / "gold_patch_exclusion_check.json")
        future = read_json(candidate_dir / "future_evidence_exclusion_check.json")
        workspace = read_json(candidate_dir / "workspace_custody_check.json")
        patch_license = read_json(candidate_dir / "patch_license_from_amds.json")
        gate = read_json(candidate_dir / "probe_to_patch_transition_gate.json")
        board = read_json(candidate_dir / "amds_failure_board_state.json")
        if replay.get("classification") not in ALLOWED_REPLAY_CLASSIFICATIONS:
            errors.append(f"unexpected replay classification for {lead_id}: {replay.get('classification')}")
        if classification.get("patch_generated") is not False or classification.get("patch_applied") is not False or classification.get("post_repair_replay_run") is not False:
            errors.append(f"candidate mutated or ran post-repair replay: {lead_id}")
        for key in ["fixed_commit_read", "future_commit_read", "gold_patch_read", "pr_patch_read", "patch_generated"]:
            expect_false(errors, decision_inputs, key, f"decision-time inputs {lead_id}")
        if leakage.get("issue_body_used_as_repair_evidence") is not False or leakage.get("fix_or_workaround_text_persisted") is not False:
            errors.append(f"issue-body repair leakage for {lead_id}")
        if label.get("hidden_labels_used") is not False:
            errors.append(f"hidden label usage for {lead_id}")
        if gold.get("gold_patch_used") is not False:
            errors.append(f"gold patch usage for {lead_id}")
        if future.get("future_evidence_used") is not False:
            errors.append(f"future evidence usage for {lead_id}")
        if workspace.get("raw_workspace_committed") is not False or workspace.get("patch_generated") is not False or workspace.get("patch_applied") is not False:
            errors.append(f"workspace custody violation for {lead_id}")
        bridge_state = patch_license.get("patch_license_state")
        if bridge_state not in ALLOWED_BRIDGE_CLASSIFICATIONS:
            errors.append(f"unexpected AMDS bridge classification for {lead_id}: {bridge_state}")
        if patch_license.get("patch_execution_authorized_in_batch056b") is not False:
            errors.append(f"patch execution authorized for {lead_id}")
        if gate.get("future_patch_gate_candidate") is True and (
            replay.get("classification") != "pre_repair_failure_materialized" or bridge_state not in PATCH_OPEN_STATES
        ):
            errors.append(f"candidate incorrectly recommended for future patch gate: {lead_id}")
        if not board.get("cells"):
            errors.append(f"AMDS failure board has no cells for {lead_id}")

    audit_git_status(errors)

    if errors:
        print("FAIL:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Batch056b Wave 2 pre-repair replay plus AMDS bridge audit PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
