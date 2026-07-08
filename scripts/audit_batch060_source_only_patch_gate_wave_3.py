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


OUT_DIR = ROOT / "outputs" / "post_v2_37_hardening_batch060_source_only_patch_gate_wave_3"
BATCH059_DIR = ROOT / "outputs" / "post_v2_37_hardening_batch059_pre_repair_replay_wave_3_limited"
CURRENT_PROTOCOL = "v2.14"
EXPECTED_CANDIDATES = {
    "audioread_144_py313_aifc_removed",
    "cloudpickle_507_py313_typevar_distutils",
}
EXPECTED_BATCH059_SHA256 = "ee567374154ec750c967fbcc8462d675619c6fedbf7a847ec8b2c5bcbd688ba7"
EXPECTED_BATCH059_SIZE = 79596
EXPECTED_BATCH059_ENTRY_COUNT = 96
EXPECTED_BATCH059_ARTIFACT_MANIFEST_CHECKED = 95
EXPECTED_BATCH059_OUTPUT_MANIFEST_CHECKED = 94

REQUIRED_TOP_LEVEL = [
    "batch059_artifact_ingestion_summary.json",
    "batch059_artifact_sha256_verification.json",
    "batch059_result_preservation.json",
    "batch059_materialized_failure_preservation.json",
    "batch059_amds_bridge_preservation.json",
    "batch059_claim_boundary_preservation.json",
    "batch059_next_action_boundary.json",
    "source_only_patch_gate_wave_3_plan.json",
    "source_only_patch_gate_wave_3_results.json",
    "source_only_patch_gate_wave_3_summary.md",
    "source_only_patch_gate_wave_3_dashboard.json",
    "batch061_duplicate_replay_candidates.json",
    "batch061_count_gate_recommendation.json",
    "batch060b_failure_family_decomposition_recommendation.json",
    "batch059b_provider_runtime_recovery_recommendation.json",
    "batch058b_seed_discovery_wave_3_expansion_recommendation.json",
    "batch060_final_decision.json",
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
    "candidate_patch_gate_plan.json",
    "candidate_commit_verification.json",
    "candidate_workspace_manifest.json",
    "candidate_provider_capsule_preservation.json",
    "candidate_dependency_plan.json",
    "candidate_command_context.json",
    "candidate_command_normalization.json",
    "candidate_provider_precondition_check.json",
    "workspace_custody_check.json",
    "provider_capsule_setup_result.json",
    "provider_capsule_setup_trace.json",
    "provider_capsule_install_log_raw.txt",
    "fresh_pre_repair_replay_command.txt",
    "fresh_pre_repair_replay_log_raw.txt",
    "fresh_pre_repair_replay_result.json",
    "diagnostic_minimal_replay_plan.json",
    "diagnostic_minimal_replay_results.json",
    "diagnostic_failure_signature_extract.json",
    "diagnostic_traceback_roots.json",
    "diagnostic_subtarget_to_original_target_mapping.json",
    "source_discovery_plan.json",
    "source_discovery_result.json",
    "source_file_inventory.json",
    "suspect_source_files.json",
    "bounded_failure_to_source_trace.json",
    "decision_time_source_manifest.json",
    "source_surface_localization_check.json",
    "ast_loop_extrusion_bridge.json",
    "source_contact_graph_extrusion_result.json",
    "probe_to_patch_transition_gate.json",
    "patch_license_from_amds.json",
    "source_only_patch_candidate.json",
    "patch_generation_trace.json",
    "patch_safety_check.json",
    "patch_application_result.json",
    "changed_files_manifest.json",
    "test_mutation_check.json",
    "source_only_check.json",
    "post_repair_replay_command.txt",
    "post_repair_replay_result.json",
    "post_repair_failure_signature_extract.txt",
    "minimal_post_repair_subtarget_results.json",
    "repair_outcome_classification.json",
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
            errors.append(f"missing required Batch060 output: {rel}")
    if not errors:
        manifest = verify_manifest(OUT_DIR)
        if manifest.get("status") != "PASS":
            errors.append(f"Batch060 SHA256SUMS verification failed: {manifest}")
    if errors:
        print("FAIL:")
        for error in errors:
            print(f"- {error}")
        return 1

    artifact = read_json(OUT_DIR / "batch059_artifact_sha256_verification.json")
    ingest = read_json(OUT_DIR / "batch059_artifact_ingestion_summary.json")
    preservation = read_json(OUT_DIR / "batch059_result_preservation.json")
    next_boundary = read_json(OUT_DIR / "batch059_next_action_boundary.json")
    plan = read_json(OUT_DIR / "source_only_patch_gate_wave_3_plan.json")
    results = read_json(OUT_DIR / "source_only_patch_gate_wave_3_results.json")
    final = read_json(OUT_DIR / "batch060_final_decision.json")
    claim = read_json(OUT_DIR / "claim_boundary.json")
    package = read_json(OUT_DIR / "package_verification.json")
    batch061 = read_json(OUT_DIR / "batch061_duplicate_replay_candidates.json")
    batch061_count = read_json(OUT_DIR / "batch061_count_gate_recommendation.json")
    decomp = read_json(OUT_DIR / "batch060b_failure_family_decomposition_recommendation.json")

    if artifact.get("status") != "PASS":
        errors.append("Batch059 artifact verification did not pass")
    if artifact.get("zip_sha256") != EXPECTED_BATCH059_SHA256 or artifact.get("artifact_sha256") != EXPECTED_BATCH059_SHA256:
        errors.append("Batch059 artifact SHA mismatch")
    if artifact.get("zip_size_bytes") != EXPECTED_BATCH059_SIZE or artifact.get("zip_entry_count") != EXPECTED_BATCH059_ENTRY_COUNT:
        errors.append("Batch059 artifact size or entry count mismatch")
    if artifact.get("artifact_manifest", {}).get("checked") != EXPECTED_BATCH059_ARTIFACT_MANIFEST_CHECKED:
        errors.append("Batch059 artifact manifest checked count mismatch")
    output_manifest = artifact.get("output_manifests", {}).get("post_v2_37_hardening_batch059_pre_repair_replay_wave_3_limited", {})
    if output_manifest.get("checked") != EXPECTED_BATCH059_OUTPUT_MANIFEST_CHECKED or output_manifest.get("failures") != 0:
        errors.append("Batch059 internal manifest verification mismatch")
    for key in ["unsafe_path_count", "duplicate_path_count", "zip_pycache_entries", "zip_pyc_entries"]:
        if artifact.get(key) != 0:
            errors.append(f"Batch059 artifact has non-zero {key}")
    if ingest.get("status") != "PASS" or ingest.get("artifact_verification", {}).get("status") != "PASS":
        errors.append("Batch059 official ingest did not pass")
    expect_false(errors, artifact, "raw_zip_bytes_ingested", "Batch059 artifact verification")
    expect_false(errors, artifact, "zip_payload_committed", "Batch059 artifact verification")

    if preservation.get("issue_derived_repair_count") != 2 or preservation.get("native_external_repair_count") != 4:
        errors.append("Batch059 repair counts not preserved")
    if preservation.get("target_code_failure_materialization_count") != 2 or preservation.get("blocked_candidate_count") != 0:
        errors.append("Batch059 materialized failure count not preserved")
    for key in ["batch059_patch_generated", "batch059_patch_applied", "batch059_duplicate_replay_run", "batch059_count_gate_run"]:
        expect_false(errors, preservation, key, "Batch059 result preservation")
    if next_boundary.get("status") != "PASS" or next_boundary.get("observed_next_allowed_action") != "batch060_source_only_patch_gate_wave_3":
        errors.append("Batch059 next-action boundary does not authorize Batch060")

    planned_ids = set(plan.get("candidate_ids", []))
    if planned_ids != EXPECTED_CANDIDATES:
        errors.append(f"Batch060 operated on unexpected candidate scope: {sorted(planned_ids)}")
    expect_false(errors, plan, "duplicate_replay_allowed", "Batch060 plan")
    expect_false(errors, plan, "count_gate_allowed", "Batch060 plan")
    expect_false(errors, plan, "repair_count_increment_allowed", "Batch060 plan")

    candidate_results = results.get("candidate_results", [])
    if {row.get("candidate_id") for row in candidate_results} != EXPECTED_CANDIDATES:
        errors.append("Batch060 result candidate scope mismatch")
    if {row.get("candidate_id") for row in final.get("candidate_results", [])} != EXPECTED_CANDIDATES:
        errors.append("Batch060 final candidate scope mismatch")

    for row in final.get("candidate_results", []):
        cid = row.get("candidate_id")
        cdir = OUT_DIR / "candidates" / cid
        if not cdir.is_dir():
            errors.append(f"missing candidate directory: {cid}")
            continue
        required = list(PER_CANDIDATE_FILES)
        if row.get("patch_generated"):
            required.append("source_only_patch_candidate.diff")
        else:
            required += ["source_only_patch_not_generated.json", "no_safe_patch_reason.json"]
        for rel in required:
            if not (cdir / rel).is_file():
                errors.append(f"missing candidate file for {cid}: {rel}")
        commit = read_json(cdir / "candidate_commit_verification.json")
        if commit.get("status") != "PASS" or commit.get("commit_resolved") is not True:
            errors.append(f"commit verification failed for {cid}")
        fresh = read_json(cdir / "fresh_pre_repair_replay_result.json")
        if fresh.get("original_target_reproduced") is not True:
            errors.append(f"fresh original target was not reproduced for {cid}")
        diag = read_json(cdir / "diagnostic_minimal_replay_results.json")
        if diag.get("status") != "PASS":
            errors.append(f"diagnostic minimal replay missing or failed for {cid}")
        forbidden = read_json(cdir / "forbidden_evidence_audit.json")
        for key, value in forbidden.items():
            if key.endswith("_used") and value is not False:
                errors.append(f"forbidden evidence used for {cid}: {key}")
        leakage = read_json(cdir / "issue_body_leakage_boundary.json")
        if leakage.get("issue_body_text_persisted") is not False or leakage.get("issue_body_fix_or_workaround_text_used") is not False:
            errors.append(f"issue body leakage boundary failed for {cid}")
        patch_license = read_json(cdir / "patch_license_from_amds.json")
        if row.get("patch_generated") and not patch_license.get("license_open"):
            errors.append(f"patch generated without open license for {cid}")
        patch = read_json(cdir / "source_only_patch_candidate.json")
        if row.get("patch_generated") and (patch.get("patch_non_empty") is not True):
            errors.append(f"generated patch is empty for {cid}")
        safety = read_json(cdir / "patch_safety_check.json")
        if row.get("patch_generated"):
            if safety.get("status") != "PASS" or safety.get("source_only") is not True:
                errors.append(f"patch safety failed for {cid}")
            if safety.get("tests_modified") is not False or safety.get("fixtures_modified") is not False or safety.get("dependency_or_build_files_modified") is not False:
                errors.append(f"patch touched forbidden files for {cid}")
        test_mutation = read_json(cdir / "test_mutation_check.json")
        if test_mutation.get("tests_modified") is not False or test_mutation.get("fixtures_modified") is not False:
            errors.append(f"tests/fixtures modified for {cid}")
        post = read_json(cdir / "post_repair_replay_result.json")
        if row.get("patch_applied") and not post.get("classification"):
            errors.append(f"missing post-repair original target replay for {cid}")
        if post.get("classification") in {"source_only_patch_partial_improvement", "source_only_patch_primary_only_improvement"} and row.get("source_only_target_pass"):
            errors.append(f"partial improvement counted as target pass for {cid}")
        outcome = read_json(cdir / "repair_outcome_classification.json")
        if outcome.get("source_only_target_pass") is True and outcome.get("classification") != "source_only_patch_target_pass":
            errors.append(f"invalid target-pass classification for {cid}")
        workspace = read_json(cdir / "workspace_custody_check.json")
        if workspace.get("workspace_outside_repo") is not True or workspace.get("tests_mutated") is not False:
            errors.append(f"workspace custody failed for {cid}")

    if final.get("patch_generated_count") != sum(1 for row in final.get("candidate_results", []) if row.get("patch_generated")):
        errors.append("patch generated count mismatch")
    if final.get("patch_applied_count") != sum(1 for row in final.get("candidate_results", []) if row.get("patch_applied")):
        errors.append("patch applied count mismatch")
    if final.get("source_only_target_pass_count") != len(batch061.get("candidate_ids", [])):
        errors.append("Batch061 candidate count does not match target-pass count")
    if batch061_count.get("recommended") is not bool(batch061.get("candidate_ids")):
        errors.append("Batch061 count-gate recommendation mismatch")
    if final.get("source_only_target_pass_count", 0) == 0 and final.get("next_allowed_action") == "batch061_duplicate_clean_replay_and_issue_repair_count_gate_wave_3":
        errors.append("Batch061 selected without a source-only target pass")
    if "cloudpickle_507_py313_typevar_distutils" not in decomp.get("candidate_ids", []):
        errors.append("Cloudpickle decomposition recommendation missing")

    for key in ["duplicate_replay_run", "count_gate_run", "repair_count_increment"]:
        expect_false(errors, final, key, "Batch060 final decision")
    if final.get("issue_derived_repair_count") != 2 or final.get("native_external_repair_count") != 4:
        errors.append("repair counts changed in Batch060")
    if final.get("full_scoring") != "NOT_RUN/disallowed" or final.get("memory_lift") != "not_demonstrated" or final.get("self_maintaining_software") != "false/not_demonstrated":
        errors.append("Batch060 overclaim")
    if final.get("current_protocol") != CURRENT_PROTOCOL:
        errors.append("Current protocol changed from v2.14")
    for key in ["duplicate_replay_run", "count_gate_run", "repair_count_increment"]:
        expect_false(errors, claim, key, "Batch060 claim boundary")
    if claim.get("partial_improvement_counts_as_repair") is not False or claim.get("minimal_subtarget_pass_counts_as_repair") is not False:
        errors.append("partial/minimal result overclaimed as repair")
    for key in ["raw_zip_payload_committed", "runtime_workspaces_committed", "source_checkouts_committed", "venvs_committed", "caches_committed"]:
        expect_false(errors, package, key, "Batch060 package verification")

    batch059_final = read_json(BATCH059_DIR / "batch059_final_decision.json")
    if batch059_final.get("next_allowed_action") != "batch060_source_only_patch_gate_wave_3":
        errors.append("Existing Batch059 next action changed")
    audit_git_status(errors)
    if errors:
        print("FAIL:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Batch060 source-only patch gate wave 3 audit PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
