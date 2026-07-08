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


OUT_DIR = ROOT / "outputs" / "post_v2_37_hardening_batch056f_timeout_split_replay_wave_2"
BATCH056E_DIR = ROOT / "outputs" / "post_v2_37_hardening_batch056e_timeout_candidate_decomposition_wave_2_provider_capsules"
CURRENT_PROTOCOL = "v2.14"
EXPECTED_BATCH056E_SHA256 = "767a96b0f01cde03461d2be0614b4866e4544698afe9f25d6565844ad1ab17b0"
EXPECTED_BATCH056E_SIZE = 118483
EXPECTED_BATCH056E_ENTRY_COUNT = 143
EXPECTED_BATCH056E_ARTIFACT_MANIFEST_CHECKED = 142
EXPECTED_BATCH056E_OUTPUT_MANIFEST_CHECKED = 141
EXPECTED_TIMEOUT_CANDIDATES = [
    "codex_wave2_nousresearch_hermes_agent_48986",
    "codex_wave2_nousresearch_hermes_agent_60243",
    "codex_wave2_nousresearch_hermes_agent_57197",
    "codex_wave2_m0smith_genia_2026_518",
]
ALLOWED_PHASE_CLASSIFICATIONS = {
    "phase_pass",
    "phase_fail_target_code_failure",
    "phase_fail_provider_dependency",
    "phase_fail_network_or_model_download",
    "phase_fail_external_service",
    "phase_fail_timeout",
    "phase_fail_test_collection",
    "phase_fail_import_error",
    "phase_blocked_unbounded",
    "phase_blocked_no_declared_evidence",
    "phase_blocked_leakage_risk",
    "phase_not_run_due_prior_blocker",
    "phase_not_safe",
}
REQUIRED_TOP_LEVEL = [
    "batch056e_artifact_ingestion_summary.json",
    "batch056e_artifact_sha256_verification.json",
    "batch056e_result_preservation.json",
    "batch056e_timeout_decomposition_preservation.json",
    "batch056e_provider_capsule_preservation.json",
    "batch056e_amds_timeout_bridge_preservation.json",
    "batch056e_claim_boundary_preservation.json",
    "batch056e_next_action_boundary.json",
    "timeout_split_replay_standard.json",
    "timeout_split_replay_schema.json",
    "timeout_split_replay_decision_rules.json",
    "timeout_split_non_repair_boundary.json",
    "reactome_step_gating_pattern_reference.json",
    "timeout_split_audit_requirements.json",
    "chromosomal_maintenance_stage_map.json",
    "tension_relief_materialization_gate_report.json",
    "activation_license_denial_report.json",
    "cytoskeleton_timeout_boundary_report.json",
    "transcription_factor_dependency_boundary_preservation.json",
    "snapshottest_provider_success_target_nonmaterialization_case_study.json",
    "timeout_split_replay_plan.json",
    "timeout_split_replay_results.json",
    "timeout_split_materialized_failure_registry.json",
    "timeout_split_blocked_candidate_registry.json",
    "timeout_split_candidate_retirement_registry.json",
    "timeout_split_amds_bridge_dashboard.json",
    "timeout_split_future_decomposition_recommendation.json",
    "timeout_split_future_patch_gate_recommendation.json",
    "timeout_split_future_provider_capsule_recommendation.json",
    "timeout_split_future_wave3_recommendation.json",
    "freezegun_provider_portability_fallback_preservation.json",
    "batch056f_summary.md",
    "batch056f_final_decision.json",
    "claim_boundary.json",
    "audit.json",
    "package_verification.json",
    "artifact_sha256_verification.json",
    "SHA256SUMS.txt",
]
REQUIRED_CANDIDATE_FILES = [
    "timeout_split_replay_plan.json",
    "timeout_split_phase_budget.json",
    "timeout_split_allowed_evidence_manifest.json",
    "timeout_split_forbidden_evidence_audit.json",
    "timeout_split_workspace_manifest.json",
    "timeout_split_provider_precondition_check.json",
    "timeout_split_execution_trace.json",
    "amds_timeout_board_state_after_split.json",
    "timeout_cell_registry_after_split.json",
    "timeout_mine_risk_map_after_split.json",
    "timeout_safe_action_frontier_after_split.json",
    "timeout_information_gain_move_ranking_after_split.json",
    "timeout_flagged_unsafe_cells_after_split.json",
    "timeout_probe_to_capsule_transition_gate_after_split.json",
    "timeout_patch_license_from_amds_after_split.json",
    "timeout_candidate_summary_after_split.json",
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


def audit_metadata_only(errors: list[str], rel: str) -> dict[str, Any]:
    record = read_json(OUT_DIR / rel)
    if record.get("metadata_scope") != "explanatory_audit_metadata_only":
        errors.append(f"{rel}: diagnostic labels must be audit metadata only")
    if record.get("proof_rules_changed") is not False:
        errors.append(f"{rel}: proof rules changed")
    if record.get("patch_license_changed") is not False:
        errors.append(f"{rel}: patch license changed")
    if record.get("count_boundary_changed") is not False:
        errors.append(f"{rel}: count boundary changed")
    return record


def main() -> int:
    errors: list[str] = []
    if not OUT_DIR.is_dir():
        print(f"FAIL: missing output directory: {OUT_DIR.relative_to(ROOT)}")
        return 1
    for rel in REQUIRED_TOP_LEVEL:
        if not (OUT_DIR / rel).is_file():
            errors.append(f"missing required Batch056f output: {rel}")
    if not errors:
        manifest = verify_manifest(OUT_DIR)
        if manifest.get("status") != "PASS":
            errors.append(f"Batch056f SHA256SUMS verification failed: {manifest}")
    if errors:
        print("FAIL:")
        for error in errors:
            print(f"- {error}")
        return 1

    artifact = read_json(OUT_DIR / "batch056e_artifact_sha256_verification.json")
    ingest = read_json(OUT_DIR / "batch056e_artifact_ingestion_summary.json")
    preservation = read_json(OUT_DIR / "batch056e_result_preservation.json")
    next_boundary = read_json(OUT_DIR / "batch056e_next_action_boundary.json")
    standard = read_json(OUT_DIR / "timeout_split_replay_standard.json")
    non_repair = read_json(OUT_DIR / "timeout_split_non_repair_boundary.json")
    reactome = read_json(OUT_DIR / "reactome_step_gating_pattern_reference.json")
    plan = read_json(OUT_DIR / "timeout_split_replay_plan.json")
    results = read_json(OUT_DIR / "timeout_split_replay_results.json")
    materialized = read_json(OUT_DIR / "timeout_split_materialized_failure_registry.json")
    amds = read_json(OUT_DIR / "timeout_split_amds_bridge_dashboard.json")
    future_patch = read_json(OUT_DIR / "timeout_split_future_patch_gate_recommendation.json")
    future_wave3 = read_json(OUT_DIR / "timeout_split_future_wave3_recommendation.json")
    final = read_json(OUT_DIR / "batch056f_final_decision.json")
    claim = read_json(OUT_DIR / "claim_boundary.json")
    package = read_json(OUT_DIR / "package_verification.json")

    if artifact.get("status") != "PASS":
        errors.append("Batch056e artifact verification did not pass")
    if artifact.get("zip_sha256") != EXPECTED_BATCH056E_SHA256 or artifact.get("artifact_sha256") != EXPECTED_BATCH056E_SHA256:
        errors.append("Batch056e artifact SHA mismatch")
    if artifact.get("zip_size_bytes") != EXPECTED_BATCH056E_SIZE or artifact.get("zip_entry_count") != EXPECTED_BATCH056E_ENTRY_COUNT:
        errors.append("Batch056e artifact size or entry count mismatch")
    if artifact.get("artifact_manifest", {}).get("checked") != EXPECTED_BATCH056E_ARTIFACT_MANIFEST_CHECKED:
        errors.append("Batch056e artifact manifest checked count mismatch")
    output_manifest = artifact.get("output_manifests", {}).get("post_v2_37_hardening_batch056e_timeout_candidate_decomposition_wave_2_provider_capsules", {})
    if output_manifest.get("checked") != EXPECTED_BATCH056E_OUTPUT_MANIFEST_CHECKED or output_manifest.get("failures") != 0:
        errors.append("Batch056e internal manifest verification mismatch")
    for key in ["unsafe_path_count", "duplicate_path_count", "zip_pycache_entries", "zip_pyc_entries"]:
        if artifact.get(key) != 0:
            errors.append(f"Batch056e artifact has non-zero {key}")
    if ingest.get("status") != "PASS":
        errors.append("Batch056e official ingest did not pass")
    expect_false(errors, artifact, "raw_zip_bytes_ingested", "Batch056e artifact verification")
    expect_false(errors, artifact, "zip_payload_committed", "Batch056e artifact verification")
    if preservation.get("issue_derived_repair_count") != 2 or preservation.get("native_external_repair_count") != 4:
        errors.append("Batch056e repair counts not preserved")
    for key in ["batch056e_patch_generated", "batch056e_patch_applied", "batch056e_duplicate_replay_run", "batch056e_count_gate_run", "repair_count_increment"]:
        expect_false(errors, preservation, key, "Batch056e result preservation")
    if next_boundary.get("matches_expected") is not True:
        errors.append("Batch056e next action did not authorize Batch056f")

    if standard.get("status") != "PASS" or len(standard.get("phases", [])) != 8:
        errors.append("Timeout split replay standard missing phase set")
    for phase in standard.get("phases", []):
        if not phase.get("timeout_budget_seconds"):
            errors.append(f"phase lacks timeout budget: {phase}")
        if phase.get("mutates_source_or_tests") is not False or phase.get("repair_success_claim_allowed") is not False:
            errors.append(f"phase weakens non-repair boundary: {phase}")
    for key in [
        "timeout_split_is_repair_success",
        "provider_capsule_success_is_repair_success",
        "patch_generation_allowed",
        "post_repair_replay_allowed",
        "duplicate_replay_allowed",
        "count_gate_allowed",
        "repair_count_increment_allowed",
    ]:
        expect_false(errors, non_repair, key, "Batch056f non-repair boundary")
    if reactome.get("reactome_used_as") != "infrastructure_step_gating_pattern_only" or reactome.get("reactome_used_as_repair_seed") is not False or reactome.get("reactome_used_as_external_repair_evidence") is not False:
        errors.append("Reactome pattern not quarantined as infrastructure-only")
    if plan.get("candidate_scope") != EXPECTED_TIMEOUT_CANDIDATES:
        errors.append("Batch056f candidate scope mismatch")
    if plan.get("patching_allowed") is not False:
        errors.append("Batch056f plan permits patching")

    for rel in [
        "chromosomal_maintenance_stage_map.json",
        "tension_relief_materialization_gate_report.json",
        "activation_license_denial_report.json",
        "cytoskeleton_timeout_boundary_report.json",
        "transcription_factor_dependency_boundary_preservation.json",
        "snapshottest_provider_success_target_nonmaterialization_case_study.json",
    ]:
        audit_metadata_only(errors, rel)
    stage_map = read_json(OUT_DIR / "chromosomal_maintenance_stage_map.json")
    if stage_map.get("stage") != "Step 3" or stage_map.get("stage_name") != "tension relief / materialization recovery":
        errors.append("diagnostic stage map does not preserve Step 3 materialization recovery")
    activation = read_json(OUT_DIR / "activation_license_denial_report.json")
    if activation.get("activation_license_state") != "closed" or activation.get("patch_license_denied") is not True:
        errors.append("activation license denial report failed to preserve closed patch license")
    snap = read_json(OUT_DIR / "snapshottest_provider_success_target_nonmaterialization_case_study.json")
    if snap.get("provider_dependency_recovery_succeeded") is not True or snap.get("target_bug_reproduced") is not False or snap.get("patch_licensed") is not False:
        errors.append("snapshottest case study does not preserve provider-success/target-nonmaterialization boundary")

    rows = results.get("results", [])
    if [row.get("candidate_id") for row in rows] != EXPECTED_TIMEOUT_CANDIDATES:
        errors.append("Batch056f result candidate set mismatch")
    if materialized.get("count") != 0 or materialized.get("materialized_target_code_failures") != []:
        errors.append("Batch056f unexpectedly materialized target-code failures")
    if future_patch.get("recommended_candidates") != []:
        errors.append("Batch056f opened a future patch gate without materialized target-code failure")
    if future_wave3.get("recommended") is not True:
        errors.append("Batch056f should recommend Wave 3 when no target-code failure materializes")
    if amds.get("patch_execution_authorized_in_batch056f") is not False:
        errors.append("AMDS authorized patch execution in Batch056f")

    for row in rows:
        candidate_id = row.get("candidate_id")
        cdir = OUT_DIR / "candidates" / str(candidate_id)
        for rel in REQUIRED_CANDIDATE_FILES:
            if not (cdir / rel).is_file():
                errors.append(f"missing candidate output for {candidate_id}: {rel}")
        for key in ["patch_generated", "patch_applied", "post_repair_replay_run", "duplicate_replay_run", "count_gate_run", "repair_count_increment"]:
            expect_false(errors, row, key, f"Batch056f result {candidate_id}")
        if row.get("target_code_failure_materialized") is not False:
            errors.append(f"target-code failure unexpectedly materialized for {candidate_id}")
        for phase_index in range(8):
            for suffix in ["result.json", "timeout_status.json", "classification.json"]:
                if not (cdir / f"phase_{phase_index}_{suffix}").is_file():
                    errors.append(f"missing phase artifact for {candidate_id}: phase_{phase_index}_{suffix}")
            result = read_json(cdir / f"phase_{phase_index}_result.json")
            classification = read_json(cdir / f"phase_{phase_index}_classification.json")
            if classification.get("classification") not in ALLOWED_PHASE_CLASSIFICATIONS:
                errors.append(f"invalid phase classification for {candidate_id}: {classification.get('classification')}")
            for key in ["mutated_source", "mutated_tests", "used_fixed_gold_future_evidence", "installed_undeclared_dependencies", "downloaded_unbounded_model_or_data", "counts_as_repair_success"]:
                expect_false(errors, result, key, f"phase result {candidate_id} phase {phase_index}")
            if classification.get("repair_authorized") is not False:
                errors.append(f"phase authorized repair for {candidate_id} phase {phase_index}")
        forbidden = read_json(cdir / "timeout_split_forbidden_evidence_audit.json")
        for key in ["fixed_commit_used", "gold_patch_used", "future_commit_used", "issue_body_fix_or_workaround_text_used", "source_mutated", "tests_mutated", "unbounded_download_performed", "external_credentials_required"]:
            expect_false(errors, forbidden, key, f"forbidden evidence audit {candidate_id}")
        patch_license = read_json(cdir / "timeout_patch_license_from_amds_after_split.json")
        if patch_license.get("patch_execution_authorized_in_batch056f") is not False:
            errors.append(f"patch execution authorized for {candidate_id}")

    for key in ["patch_generated", "patch_applied", "post_repair_replay_run", "duplicate_replay_run", "count_gate_run", "repair_count_increment"]:
        expect_false(errors, final, key, "Batch056f final decision")
    if claim.get("current_protocol") != CURRENT_PROTOCOL:
        errors.append("Current protocol changed from v2.14")
    if claim.get("issue_derived_repair_count") != 2 or claim.get("native_external_repair_count") != 4:
        errors.append("Repair counts changed in Batch056f")
    if claim.get("full_scoring") != "NOT_RUN/disallowed" or claim.get("memory_lift") != "not_demonstrated" or claim.get("self_maintaining_software") != "false/not_demonstrated":
        errors.append("Batch056f claim boundary overclaim")
    for key in ["patch_generated", "patch_applied", "post_repair_replay_run", "duplicate_replay_run", "count_gate_run", "repair_count_increment", "timeout_split_counts_as_repair_success", "provider_success_counts_as_repair_success"]:
        expect_false(errors, claim, key, "Batch056f claim boundary")
    expect_false(errors, package, "raw_zip_payload_committed", "Batch056f package")
    expect_false(errors, package, "runtime_workspaces_committed", "Batch056f package")

    batch056e_final = read_json(BATCH056E_DIR / "batch056e_final_decision.json")
    if batch056e_final.get("next_allowed_action") != "batch056f_timeout_split_replay_wave_2":
        errors.append("Existing Batch056e next action changed")
    audit_git_status(errors)
    if errors:
        print("FAIL:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Batch056f timeout split replay wave 2 audit PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
