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


OUT_DIR = ROOT / "outputs" / "post_v2_37_hardening_batch056e_timeout_candidate_decomposition_wave_2_provider_capsules"
BATCH056D_DIR = ROOT / "outputs" / "post_v2_37_hardening_batch056d_wave2_provider_dependency_recovery"
CURRENT_PROTOCOL = "v2.14"
EXPECTED_BATCH056D_SHA256 = "c1275feb267fe56cf9ae2cccf8083067c6b0ee788c27a5346aa2f320e454090e"
EXPECTED_BATCH056D_SIZE = 87453
EXPECTED_BATCH056D_ENTRY_COUNT = 115
EXPECTED_BATCH056D_ARTIFACT_MANIFEST_CHECKED = 114
EXPECTED_BATCH056D_OUTPUT_MANIFEST_CHECKED = 113
EXPECTED_TIMEOUT_CANDIDATES = [
    "codex_wave2_nousresearch_hermes_agent_48986",
    "codex_wave2_nousresearch_hermes_agent_60243",
    "codex_wave2_nousresearch_hermes_agent_57197",
    "codex_wave2_m0smith_genia_2026_518",
]
FORBIDDEN_RECOVERY_CANDIDATES = {
    "pairtools_250_py313_pipes_removed",
    "pytest_13480_wdefault_unraisable_threadexception",
    "snapshottest_177_py312_imp_removed",
}
REQUIRED_TOP_LEVEL = [
    "batch056d_artifact_ingestion_summary.json",
    "batch056d_artifact_sha256_verification.json",
    "batch056d_result_preservation.json",
    "batch056d_provider_dependency_preservation.json",
    "batch056d_amds_bridge_preservation.json",
    "batch056d_claim_boundary_preservation.json",
    "batch056d_next_action_boundary.json",
    "provider_materialization_capsule_standard.json",
    "provider_materialization_capsule_schema.json",
    "provider_capsule_decision_rules.json",
    "provider_capsule_non_repair_boundary.json",
    "provider_capsule_reactome_pattern_reference.json",
    "provider_capsule_audit_requirements.json",
    "timeout_decomposition_wave_2_plan.json",
    "timeout_decomposition_wave_2_results.json",
    "timeout_decomposition_wave_2_summary.md",
    "timeout_candidate_dashboard.json",
    "amds_timeout_bridge_dashboard.json",
    "provider_capsule_dashboard.json",
    "future_timeout_split_replay_plan.json",
    "future_provider_capsule_replay_plan.json",
    "future_timeout_candidate_decomposition_recommendation.json",
    "future_provider_capsule_recovery_recommendation.json",
    "future_wave3_seed_discovery_recommendation.json",
    "batch056e_final_decision.json",
    "claim_boundary.json",
    "audit.json",
    "package_verification.json",
    "artifact_sha256_verification.json",
    "SHA256SUMS.txt",
]
REQUIRED_CANDIDATE_FILES = [
    "timeout_decomposition_plan.json",
    "timeout_trace_summary.json",
    "timeout_phase_timeline.json",
    "timeout_last_observed_output.txt",
    "timeout_suspected_phase.json",
    "timeout_resource_risk_assessment.json",
    "timeout_command_split_plan.json",
    "timeout_minimal_probe_plan.json",
    "timeout_provider_capsule.json",
    "timeout_decomposition_result.json",
    "classification.json",
    "amds_timeout_board_state.json",
    "timeout_cell_registry.json",
    "timeout_mine_risk_map.json",
    "timeout_safe_action_frontier.json",
    "timeout_information_gain_move_ranking.json",
    "timeout_flagged_unsafe_cells.json",
    "timeout_probe_to_capsule_transition_gate.json",
    "timeout_patch_license_from_amds.json",
    "provider_materialization_capsule.json",
    "provider_capsule_evidence_manifest.json",
    "provider_capsule_leakage_check.json",
    "provider_capsule_declared_install_map.json",
    "provider_capsule_declared_test_map.json",
    "provider_capsule_declared_runtime_map.json",
    "provider_capsule_declared_timeout_map.json",
    "provider_capsule_unknowns.json",
    "provider_capsule_status.json",
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
            errors.append(f"missing required Batch056e output: {rel}")
    if not errors:
        manifest = verify_manifest(OUT_DIR)
        if manifest.get("status") != "PASS":
            errors.append(f"Batch056e SHA256SUMS verification failed: {manifest}")
    if errors:
        print("FAIL:")
        for error in errors:
            print(f"- {error}")
        return 1

    artifact = read_json(OUT_DIR / "batch056d_artifact_sha256_verification.json")
    preservation = read_json(OUT_DIR / "batch056d_result_preservation.json")
    claim_preservation = read_json(OUT_DIR / "batch056d_claim_boundary_preservation.json")
    next_boundary = read_json(OUT_DIR / "batch056d_next_action_boundary.json")
    standard = read_json(OUT_DIR / "provider_materialization_capsule_standard.json")
    non_repair = read_json(OUT_DIR / "provider_capsule_non_repair_boundary.json")
    pattern = read_json(OUT_DIR / "provider_capsule_reactome_pattern_reference.json")
    plan = read_json(OUT_DIR / "timeout_decomposition_wave_2_plan.json")
    results = read_json(OUT_DIR / "timeout_decomposition_wave_2_results.json")
    amds = read_json(OUT_DIR / "amds_timeout_bridge_dashboard.json")
    capsule_dash = read_json(OUT_DIR / "provider_capsule_dashboard.json")
    future_timeout = read_json(OUT_DIR / "future_timeout_split_replay_plan.json")
    future_provider = read_json(OUT_DIR / "future_provider_capsule_replay_plan.json")
    final = read_json(OUT_DIR / "batch056e_final_decision.json")
    claim = read_json(OUT_DIR / "claim_boundary.json")
    package = read_json(OUT_DIR / "package_verification.json")

    if artifact.get("status") != "PASS":
        errors.append("Batch056d artifact verification did not pass")
    if artifact.get("zip_sha256") != EXPECTED_BATCH056D_SHA256 or artifact.get("artifact_sha256") != EXPECTED_BATCH056D_SHA256:
        errors.append("Batch056d artifact SHA mismatch")
    if artifact.get("zip_size_bytes") != EXPECTED_BATCH056D_SIZE or artifact.get("zip_entry_count") != EXPECTED_BATCH056D_ENTRY_COUNT:
        errors.append("Batch056d artifact size or entry count mismatch")
    if artifact.get("artifact_manifest", {}).get("checked") != EXPECTED_BATCH056D_ARTIFACT_MANIFEST_CHECKED:
        errors.append("Batch056d artifact manifest checked count mismatch")
    output_manifest = artifact.get("output_manifests", {}).get("post_v2_37_hardening_batch056d_wave2_provider_dependency_recovery", {})
    if output_manifest.get("checked") != EXPECTED_BATCH056D_OUTPUT_MANIFEST_CHECKED or output_manifest.get("failures") != 0:
        errors.append("Batch056d internal manifest verification mismatch")
    for key in ["unsafe_path_count", "duplicate_path_count", "zip_pycache_entries", "zip_pyc_entries"]:
        if artifact.get(key) != 0:
            errors.append(f"Batch056d artifact has non-zero {key}")
    expect_false(errors, artifact, "raw_zip_bytes_ingested", "Batch056d artifact verification")
    expect_false(errors, artifact, "zip_payload_committed", "Batch056d artifact verification")
    if preservation.get("issue_derived_repair_count") != 2 or preservation.get("native_external_repair_count") != 4:
        errors.append("Batch056d repair counts not preserved")
    if preservation.get("post_recovery_materialized_target_code_failure_count") != 0:
        errors.append("Batch056d materialized failure count not preserved")
    for key in ["batch056d_patch_generated", "batch056d_patch_applied", "batch056d_duplicate_replay_run", "batch056d_count_gate_run"]:
        expect_false(errors, preservation, key, "Batch056d result preservation")
    if claim_preservation.get("full_scoring") != "NOT_RUN/disallowed" or claim_preservation.get("memory_lift") != "not_demonstrated" or claim_preservation.get("self_maintaining_software") != "false/not_demonstrated":
        errors.append("Batch056d claim boundary changed")
    if next_boundary.get("matches_expected") is not True:
        errors.append("Batch056d next-action boundary did not permit Batch056e")

    if standard.get("status") != "PASS" or "candidate_id" not in standard.get("fields", []):
        errors.append("Provider Materialization Capsule standard missing")
    for key in ["provider_capsule_is_patch", "provider_capsule_is_repair_success", "provider_capsule_can_increment_counts", "provider_capsule_overrides_custody"]:
        expect_false(errors, non_repair, key, "Provider capsule non-repair boundary")
    if pattern.get("reactome_used_as") != "infrastructure_pattern_only" or pattern.get("reactome_used_as_repair_seed") is not False or pattern.get("reactome_used_as_external_repair_evidence") is not False:
        errors.append("Reactome pattern was not quarantined as infrastructure-only")
    if plan.get("candidate_scope") != EXPECTED_TIMEOUT_CANDIDATES:
        errors.append("Timeout candidate scope mismatch")
    if set(plan.get("forbidden_candidates", [])) & FORBIDDEN_RECOVERY_CANDIDATES != FORBIDDEN_RECOVERY_CANDIDATES:
        errors.append("Provider/dependency recovery candidates not explicitly forbidden for Batch056e")
    expect_false(errors, plan, "patching_allowed", "Batch056e plan")
    rows = results.get("results", [])
    if [row.get("candidate_id") for row in rows] != EXPECTED_TIMEOUT_CANDIDATES:
        errors.append("Timeout decomposition result candidate set mismatch")
    if set(amds.get("classifications", {})) != set(EXPECTED_TIMEOUT_CANDIDATES):
        errors.append("AMDS timeout dashboard scope mismatch")
    if amds.get("patching_authorized_in_batch056e") is not False:
        errors.append("AMDS timeout dashboard authorized patching")
    if set(capsule_dash.get("provider_capsule_status_by_candidate", {})) != set(EXPECTED_TIMEOUT_CANDIDATES):
        errors.append("Provider capsule dashboard scope mismatch")
    if not isinstance(future_timeout.get("candidates"), list) or not isinstance(future_provider.get("candidates"), list):
        errors.append("Future replay plan candidates missing")

    for row in rows:
        candidate_id = row.get("candidate_id")
        cdir = OUT_DIR / "candidates" / str(candidate_id)
        for rel in REQUIRED_CANDIDATE_FILES:
            if not (cdir / rel).is_file():
                errors.append(f"missing candidate output for {candidate_id}: {rel}")
        for key in ["patch_generated", "patch_applied", "duplicate_replay_run", "count_gate_run"]:
            expect_false(errors, row, key, f"timeout result {candidate_id}")
        if row.get("amds_timeout_bridge_classification") != "patch_license_closed_timeout_decomposition_only":
            errors.append(f"patch license not closed for {candidate_id}")
        if errors:
            continue
        classification = read_json(cdir / "classification.json")
        patch_license = read_json(cdir / "timeout_patch_license_from_amds.json")
        leakage = read_json(cdir / "provider_capsule_leakage_check.json")
        capsule = read_json(cdir / "provider_materialization_capsule.json")
        evidence = read_json(cdir / "provider_capsule_evidence_manifest.json")
        for key in ["patch_generated", "patch_applied", "post_repair_replay_run", "duplicate_replay_run", "count_gate_run"]:
            expect_false(errors, classification, key, f"classification {candidate_id}")
        if patch_license.get("patch_execution_authorized_in_batch056e") is not False:
            errors.append(f"patch execution authorized for {candidate_id}")
        for key in ["fixed_commit_used", "future_commit_used", "gold_patch_used", "issue_fix_workaround_text_persisted"]:
            expect_false(errors, leakage, key, f"leakage {candidate_id}")
        if capsule.get("capsule_status") not in capsule_dash.get("provider_capsule_status_by_candidate", {}).values():
            errors.append(f"unexpected capsule status for {candidate_id}")
        if evidence.get("forbidden_evidence_used") is not False:
            errors.append(f"forbidden evidence used for {candidate_id}")

    for key in ["patch_generated", "patch_applied", "post_repair_replay_run", "duplicate_replay_run", "count_gate_run", "repair_count_increment"]:
        expect_false(errors, final, key, "Batch056e final decision")
    if claim.get("current_protocol") != CURRENT_PROTOCOL:
        errors.append("Current protocol changed from v2.14")
    if claim.get("issue_derived_repair_count") != 2 or claim.get("native_external_repair_count") != 4:
        errors.append("Repair counts changed in Batch056e")
    if claim.get("full_scoring") != "NOT_RUN/disallowed" or claim.get("memory_lift") != "not_demonstrated" or claim.get("self_maintaining_software") != "false/not_demonstrated":
        errors.append("Batch056e claim boundary overclaim")
    for key in ["batch056e_patch_generated", "batch056e_patch_applied", "batch056e_post_repair_replay_run", "batch056e_duplicate_replay_run", "batch056e_count_gate_run", "batch056e_repair_count_increment"]:
        expect_false(errors, claim, key, "Batch056e claim boundary")
    expect_false(errors, package, "raw_zip_payload_committed", "Batch056e package")
    expect_false(errors, package, "runtime_workspaces_committed", "Batch056e package")

    batch056d_final = read_json(BATCH056D_DIR / "batch056d_final_decision.json")
    if batch056d_final.get("next_allowed_action") != "batch056e_timeout_candidate_decomposition_wave_2":
        errors.append("Existing Batch056d next action changed")
    audit_git_status(errors)
    if errors:
        print("FAIL:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Batch056e timeout decomposition and provider capsules audit PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
