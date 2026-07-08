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


BATCH060B_DIR = ROOT / "outputs" / "post_v2_37_hardening_batch060b_cloudpickle_decomposition_audioread_provider_preservation"
BATCH060_DIR = ROOT / "outputs" / "post_v2_37_hardening_batch060_source_only_patch_gate_wave_3"
CURRENT_PROTOCOL = "v2.14"

EXPECTED_BATCH060_SHA256 = "faff6d674d923740d2c937db6ff7132836290b448750470ef648c49de19d9022"
EXPECTED_BATCH060_SIZE = 98801
EXPECTED_BATCH060_ENTRY_COUNT = 130
EXPECTED_BATCH060_ARTIFACT_MANIFEST_CHECKED = 129
EXPECTED_BATCH060_OUTPUT_MANIFEST_CHECKED = 128

REQUIRED_FILES = [
    "batch060_artifact_ingestion_summary.json",
    "batch060_artifact_sha256_verification.json",
    "batch060_result_preservation.json",
    "batch060_audioread_partial_improvement_preservation.json",
    "batch060_cloudpickle_blocker_preservation.json",
    "batch060_claim_boundary_preservation.json",
    "batch060_next_action_boundary.json",
    "audioread_failed_repair_branch_record.json",
    "audioread_partial_improvement_forensics.json",
    "audioread_post_patch_failure_family_decomposition.json",
    "audioread_backend_provider_capsule_plan.json",
    "audioread_future_recovery_recommendation.json",
    "cloudpickle_failure_family_decomposition.json",
    "cloudpickle_bug_layer_registry.json",
    "cloudpickle_primary_failure_family_selection.json",
    "cloudpickle_secondary_failure_family_registry.json",
    "cloudpickle_tertiary_failure_family_registry.json",
    "cloudpickle_traceback_cluster_map.json",
    "cloudpickle_test_node_cluster_map.json",
    "cloudpickle_exception_type_cluster_map.json",
    "cloudpickle_source_surface_map.json",
    "cloudpickle_interpreter_behavior_map.json",
    "cloudpickle_provider_dependency_map.json",
    "cloudpickle_minimal_subtarget_plan.json",
    "cloudpickle_elbow_activation_gate.json",
    "cloudpickle_layered_repair_claim_boundary.json",
    "cloudpickle_diagnostic_replay_plan.json",
    "cloudpickle_diagnostic_replay_results.json",
    "cloudpickle_diagnostic_traceback_roots.json",
    "cloudpickle_diagnostic_failure_signature_extract.json",
    "cloudpickle_subtarget_to_original_target_mapping.json",
    "cloudpickle_ast_loop_extrusion_bridge.json",
    "cloudpickle_source_contact_graph.json",
    "cloudpickle_failure_to_source_contact_map.json",
    "cloudpickle_safe_action_frontier.json",
    "cloudpickle_patch_license_from_amds.json",
    "cloudpickle_next_patch_gate_recommendation.json",
    "wave3_structural_state_map_after_batch060.json",
    "tld_failure_boundary_interpretation_batch060b.json",
    "reactome_provider_capsule_lesson_carryforward_batch060b.json",
    "controllergate_whole_problem_status_batch060b.json",
    "batch060b_final_decision.json",
    "batch060c_cloudpickle_patch_gate_recommendation.json",
    "batch060d_audioread_provider_backend_recovery_recommendation.json",
    "batch058b_seed_discovery_wave_3_expansion_recommendation.json",
    "batch061_duplicate_replay_recommendation.json",
    "batch060b_summary.md",
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


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def git_lines(*args: str) -> list[str]:
    proc = subprocess.run(["git", *args], cwd=ROOT, text=True, capture_output=True, check=False)
    return proc.stdout.splitlines()


def expect_false(errors: list[str], obj: dict[str, Any], key: str, label: str) -> None:
    if obj.get(key) is not False:
        errors.append(f"{label} expected {key}=false, observed {obj.get(key)!r}")


def audit_git_status(errors: list[str]) -> None:
    for line in git_lines("status", "--short"):
        normalized = line[3:].replace("\\", "/") if len(line) > 3 else line.replace("\\", "/")
        if line.startswith("?? incoming_artifacts/"):
            continue
        for fragment in FORBIDDEN_STATUS_FRAGMENTS:
            if fragment in normalized:
                errors.append(f"forbidden path appears in git status: {line}")
                break


def audit_public_text(errors: list[str]) -> None:
    text = "\n".join(path.read_text(encoding="utf-8", errors="replace") for path in BATCH060B_DIR.rglob("*") if path.is_file())
    forbidden_claims = [
        "proof of TORUS physics",
        "self-maintaining software is demonstrated",
        "full scoring enabled",
        "memory lift demonstrated",
        "patch generated in Batch060b",
    ]
    for phrase in forbidden_claims:
        if phrase.lower() in text.lower():
            errors.append(f"forbidden overclaim text present: {phrase}")


def main() -> int:
    errors: list[str] = []
    if not BATCH060B_DIR.is_dir():
        print(f"FAIL: missing Batch060b output directory: {BATCH060B_DIR.relative_to(ROOT)}")
        return 1
    for rel in REQUIRED_FILES:
        if not (BATCH060B_DIR / rel).is_file():
            errors.append(f"missing required Batch060b output: {rel}")
    if not errors:
        manifest = verify_manifest(BATCH060B_DIR)
        if manifest.get("status") != "PASS":
            errors.append(f"Batch060b SHA256SUMS verification failed: {manifest}")
    if errors:
        print("FAIL:")
        for error in errors:
            print(f"- {error}")
        return 1

    artifact = read_json(BATCH060B_DIR / "batch060_artifact_sha256_verification.json")
    ingest = read_json(BATCH060B_DIR / "batch060_artifact_ingestion_summary.json")
    preservation = read_json(BATCH060B_DIR / "batch060_result_preservation.json")
    partial = read_json(BATCH060B_DIR / "audioread_failed_repair_branch_record.json")
    audioread_decomp = read_json(BATCH060B_DIR / "audioread_post_patch_failure_family_decomposition.json")
    audioread_future = read_json(BATCH060B_DIR / "audioread_future_recovery_recommendation.json")
    cloudpickle_decomp = read_json(BATCH060B_DIR / "cloudpickle_failure_family_decomposition.json")
    cloudpickle_license = read_json(BATCH060B_DIR / "cloudpickle_patch_license_from_amds.json")
    cloudpickle_next = read_json(BATCH060B_DIR / "cloudpickle_next_patch_gate_recommendation.json")
    diag_plan = read_json(BATCH060B_DIR / "cloudpickle_diagnostic_replay_plan.json")
    reactome = read_json(BATCH060B_DIR / "reactome_provider_capsule_lesson_carryforward_batch060b.json")
    tld = read_json(BATCH060B_DIR / "tld_failure_boundary_interpretation_batch060b.json")
    final = read_json(BATCH060B_DIR / "batch060b_final_decision.json")
    claim = read_json(BATCH060B_DIR / "claim_boundary.json")
    package = read_json(BATCH060B_DIR / "package_verification.json")
    batch061 = read_json(BATCH060B_DIR / "batch061_duplicate_replay_recommendation.json")
    batch060_final = read_json(BATCH060_DIR / "batch060_final_decision.json")

    if artifact.get("status") != "PASS":
        errors.append("Batch060 artifact verification did not pass")
    if artifact.get("zip_sha256") != EXPECTED_BATCH060_SHA256 or artifact.get("artifact_sha256") != EXPECTED_BATCH060_SHA256:
        errors.append("Batch060 artifact SHA mismatch")
    if artifact.get("zip_size_bytes") != EXPECTED_BATCH060_SIZE or artifact.get("zip_entry_count") != EXPECTED_BATCH060_ENTRY_COUNT:
        errors.append("Batch060 artifact size or entry count mismatch")
    if artifact.get("artifact_manifest", {}).get("checked") != EXPECTED_BATCH060_ARTIFACT_MANIFEST_CHECKED:
        errors.append("Batch060 artifact manifest checked count mismatch")
    output_manifest = artifact.get("output_manifests", {}).get(
        "post_v2_37_hardening_batch060_source_only_patch_gate_wave_3", {}
    )
    if output_manifest.get("checked") != EXPECTED_BATCH060_OUTPUT_MANIFEST_CHECKED or output_manifest.get("failures") != 0:
        errors.append("Batch060 internal manifest verification mismatch")
    for key in ["unsafe_path_count", "duplicate_path_count", "zip_pycache_entries", "zip_pyc_entries"]:
        if artifact.get(key) != 0:
            errors.append(f"Batch060 artifact has non-zero {key}")
    if ingest.get("status") != "PASS" or ingest.get("verification", {}).get("status") != "PASS":
        errors.append("Batch060 official ingest did not pass")
    expect_false(errors, artifact, "raw_zip_bytes_ingested", "Batch060 artifact verification")
    expect_false(errors, artifact, "zip_payload_committed", "Batch060 artifact verification")

    if batch060_final.get("next_allowed_action") != "batch060b_failure_family_decomposition_cloudpickle":
        errors.append("Committed Batch060 next action no longer routes to Batch060b")
    if preservation.get("issue_derived_repair_count") != 2 or preservation.get("native_external_repair_count") != 4:
        errors.append("Batch060 preserved repair counts changed")
    if preservation.get("source_only_target_pass_count") != 0 or preservation.get("partial_improvement_count") != 1:
        errors.append("Batch060 result preservation lost target-pass/partial-improvement counts")

    if partial.get("batch060_classification") != "source_only_patch_partial_improvement":
        errors.append("Audioread partial improvement branch record missing")
    if partial.get("post_patch_failure") != "NoBackendError" or partial.get("repair_count_increment_allowed") is not False:
        errors.append("Audioread post-patch NoBackendError boundary not preserved")
    if audioread_decomp.get("selected_classification") != "audioread_optional_backend_capsule_needed":
        errors.append("Audioread provider/backend layer classification mismatch")
    if audioread_future.get("recommendation") != "future_audioread_provider_backend_capsule_replay":
        errors.append("Audioread future provider/backend recommendation mismatch")

    if cloudpickle_decomp.get("family_count") != 2:
        errors.append("Cloudpickle family count mismatch")
    answers = cloudpickle_decomp.get("answers", {})
    if answers.get("module_importability_failures_one_family") is not True:
        errors.append("Cloudpickle distutils nodes were not clustered as one family")
    if answers.get("class_dict_family_separate_interpreter_behavior_family") is not True:
        errors.append("Cloudpickle class-dict family separation missing")
    if answers.get("one_safe_primary_source_patch_available_now") is not False:
        errors.append("Cloudpickle patch was improperly licensed in Batch060b")
    if cloudpickle_license.get("patch_license_state") != "cloudpickle_patch_license_closed_provider_dependency_first":
        errors.append("Cloudpickle future patch-license state mismatch")
    if cloudpickle_next.get("recommendation") != "batch060c_cloudpickle_provider_runtime_recovery":
        errors.append("Cloudpickle next recommendation mismatch")
    if diag_plan.get("rerun_required") is not False and not diag_plan.get("not_run_reason"):
        errors.append("Cloudpickle diagnostic replay artifacts lack rerun or not-run reason")

    for key in [
        "batch060b_patch_generated",
        "batch060b_patch_applied",
        "post_repair_replay_run",
        "duplicate_replay_run",
        "count_gate_run",
        "repair_count_increment",
    ]:
        expect_false(errors, final, key, "Batch060b final decision")
    for key in [
        "batch060b_generates_patch",
        "batch060b_applies_patch",
        "source_mutation",
        "test_mutation",
        "fixture_mutation",
        "post_repair_replay_run",
        "duplicate_replay_run",
        "count_gate_run",
        "repair_count_increment",
    ]:
        expect_false(errors, claim, key, "Batch060b claim boundary")
    if final.get("next_allowed_action") != "batch060c_cloudpickle_provider_runtime_recovery":
        errors.append("Batch060b next action mismatch")
    if final.get("current_protocol") != CURRENT_PROTOCOL:
        errors.append("Current protocol changed from v2.14")
    if final.get("issue_derived_repair_count") != 2 or final.get("native_external_repair_count") != 4:
        errors.append("Batch060b repair counts changed")
    if final.get("full_scoring") != "NOT_RUN/disallowed" or final.get("memory_lift") != "not_demonstrated" or final.get("self_maintaining_software") != "false/not_demonstrated":
        errors.append("Batch060b overclaim")
    if batch061.get("recommended") is not False or batch061.get("candidate_ids") != []:
        errors.append("Batch061 recommendation is not empty despite zero target-pass candidates")
    if reactome.get("not_repair_evidence") is not True:
        errors.append("Reactome carry-forward is not limited to provider-capsule pattern")
    if tld.get("interpretation_scope") != "audit_metadata_and_architecture_guidance_only" or tld.get("not_proof_of_physics") is not True:
        errors.append("TLD interpretation scope is not bounded as audit metadata")
    for key in ["raw_zip_payload_committed", "runtime_workspaces_committed", "source_checkouts_committed", "venvs_committed", "caches_committed"]:
        expect_false(errors, package, key, "Batch060b package verification")

    if list(BATCH060B_DIR.rglob("*.diff")):
        errors.append("Batch060b output contains a patch diff despite no-patch boundary")
    audit_public_text(errors)
    audit_git_status(errors)

    if errors:
        print("FAIL:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Batch060b cloudpickle decomposition and audioread provider preservation audit PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
