#!/usr/bin/env python3
"""Audit v2.27 External Candidate Seed Draft Verification Lane evidence."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path, PurePosixPath
from typing import Any

import validate_external_candidate_registry as registry_validator


REPO_ROOT = Path(__file__).resolve().parents[1]
CAMPAIGN_ID = "v2_27_external_candidate_seed_draft_verification_lane"
OUTPUT_ROOT = REPO_ROOT / "outputs" / CAMPAIGN_ID
REGISTRY_PATH = REPO_ROOT / "configs" / "external_candidate_registry.json"
CANONICAL_SEED_PATH = REPO_ROOT / "inputs" / "external_candidate_seed_draft.json"
NONCANONICAL_SEED_PATH = REPO_ROOT / "configs" / "candidate_seed_draft.json"
V226_ROOT = REPO_ROOT / "outputs" / "v2_26_external_candidate_seed_capture_lane"
V223_ROOT = REPO_ROOT / "outputs" / "v2_23_non_ansible_candidate_transition_lane"
BLOCKER_NO_SEED_DRAFT = "blocked_no_external_candidate_seed_draft_provided"
EXPECTED_V227_ARTIFACT = {
    "artifact_name": "v2_27_external_candidate_seed_draft_verification_lane_artifacts",
    "workflow_run_id": 28256911882,
    "artifact_id": 7913130871,
    "zip_size": 67983,
    "zip_sha256": "3a25700c93647b531cbf1c561e6b84925517547b0f745a27f5a3a21f3c046ec3",
    "entry_count": 38,
    "internal_manifest_checked": 28,
    "successful_v2_27_head_commit": "c40b49e3ff147c0e245a06d76bcd73cd0e7a39f2",
}

REQUIRED_FILES = [
    "campaign_summary.md",
    "campaign_results.json",
    "v2_26_artifact_ingest_verification.json",
    "v2_27_official_artifact_verification.json",
    "artifact_repo_snapshot_comparison.json",
    "seed_draft_presence_check.json",
    "seed_draft_schema_validation.json",
    "seed_draft_path_policy_check.json",
    "seed_draft_forbidden_source_guard.json",
    "seed_candidate_source_checkout_audit.json",
    "seed_candidate_buggy_tree_manifest.json",
    "seed_candidate_target_test_file_hashes.json",
    "seed_candidate_environment_file_hashes.json",
    "seed_candidate_command_manifest.json",
    "seed_candidate_environment_resolution_preflight.json",
    "seed_candidate_failure_capture_raw.log",
    "seed_candidate_failure_capture_normalized.txt",
    "seed_candidate_failure_capture_hash.json",
    "seed_candidate_failure_signature_manifest.json",
    "seed_candidate_source_test_colocation_proof.json",
    "seed_candidate_registry_entry_candidate.json",
    "seed_candidate_registry_merge_report.json",
    "external_candidate_registry_validation_report_after_merge.json",
    "external_candidate_registry_status_after_merge.json",
    "public_language_audit.json",
    "roadmap_carry_forward_check_v2_27.json",
    "resolution_depth_diagnostic_v2_27.json",
    "claim_boundary_v2_27.json",
    "proof_obligations_ledger.json",
    "SHA256SUMS.txt",
]

FORBIDDEN_OUTPUTS = {
    "memory_enabled_source_only_repair_patch.diff",
    "target_validation_log.txt",
    "duplicate_replay_summary.json",
    "executed_scope_manifest.json",
}


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path, errors: list[str]) -> dict[str, Any]:
    if not path.is_file():
        errors.append(f"missing JSON: {path.relative_to(REPO_ROOT).as_posix()}")
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"invalid JSON {path.relative_to(REPO_ROOT).as_posix()}: {exc}")
        return {}
    if not isinstance(value, dict):
        errors.append(f"expected object: {path.relative_to(REPO_ROOT).as_posix()}")
        return {}
    return value


def expect(condition: bool, errors: list[str], message: str) -> None:
    if not condition:
        errors.append(message)


def verify_manifest(root: Path) -> tuple[list[str], int]:
    errors: list[str] = []
    manifest = root / "SHA256SUMS.txt"
    if not manifest.is_file():
        return [f"missing manifest: {manifest.relative_to(REPO_ROOT).as_posix()}"], 0
    seen: set[str] = set()
    checked = 0
    for line_no, line in enumerate(manifest.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        parts = line.split(maxsplit=1)
        if len(parts) != 2 or not re.fullmatch(r"[0-9a-f]{64}", parts[0]):
            errors.append(f"SHA256SUMS.txt:{line_no}: malformed entry")
            continue
        expected, rel = parts
        pure = PurePosixPath(rel)
        if rel.startswith("/") or any(part in {"", ".", ".."} for part in pure.parts):
            errors.append(f"SHA256SUMS.txt:{line_no}: unsafe path {rel}")
            continue
        path = root.joinpath(*pure.parts)
        seen.add(rel)
        if not path.is_file():
            errors.append(f"SHA256SUMS.txt:{line_no}: missing file {rel}")
            continue
        if sha256_path(path) != expected:
            errors.append(f"SHA256SUMS.txt:{line_no}: hash mismatch {rel}")
        checked += 1
    expected_files = {
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file() and path.name != "SHA256SUMS.txt"
    }
    for rel in sorted(expected_files - seen):
        errors.append(f"manifest missing {rel}")
    for rel in sorted(seen - expected_files):
        errors.append(f"manifest contains extra {rel}")
    return errors, checked


def run_python_script(script: str, errors: list[str]) -> None:
    result = subprocess.run(
        [sys.executable, str(REPO_ROOT / script)],
        cwd=str(REPO_ROOT),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        tail = "\n".join((result.stdout + "\n" + result.stderr).splitlines()[-20:])
        errors.append(f"regression audit failed: {script}\n{tail}")


def regression_scripts() -> list[str]:
    return [
        "scripts/audit_v2_26_external_candidate_seed_capture_lane.py",
        "scripts/audit_v2_25_external_candidate_registry_construction_lane.py",
        "scripts/audit_v2_24_external_safe_source_candidate_acquisition_lane.py",
        "scripts/audit_v2_23_non_ansible_candidate_transition_lane.py",
        "scripts/audit_v2_22_bugsinpy_target_test_materialization_lane.py",
        "scripts/audit_v2_21_harness_origin_verification_lane.py",
        "scripts/audit_v2_20_test_provenance_repair_lane.py",
        "scripts/audit_v2_19_bugsinpy_materialized_test_provenance.py",
        "scripts/audit_v2_18_origin_licensing_source_acquisition.py",
        "scripts/audit_v2_17_pysnooper1_runtime_workspace_materialization.py",
        "scripts/audit_v2_16.py",
        "scripts/audit_v2_15_" + "chromo" + "somal_maintenance_gate_order.py",
        "scripts/audit_v2_14_capability_recovery_lane.py",
        "scripts/audit_v2_13_minimal_forensic_context_lane.py",
        "scripts/audit_v2_12_dependency_cofactor_recovery.py",
    ]


def audit_proof_ledger(ledger: dict[str, Any], errors: list[str]) -> None:
    expect(ledger.get("status") == "PASS", errors, "proof ledger status mismatch")
    entries = ledger.get("entries")
    expect(isinstance(entries, list) and len(entries) >= 6, errors, "proof ledger entries missing")
    if not isinstance(entries, list):
        return
    previous = "0" * 64
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            errors.append(f"proof ledger entry {index} is not an object")
            return
        expect(entry.get("index") == index, errors, f"proof ledger index mismatch at {index}")
        expect(entry.get("previous_entry_hash") == previous, errors, f"proof ledger previous hash mismatch at {index}")
        recorded_hash = entry.get("entry_hash")
        payload = {key: value for key, value in entry.items() if key != "entry_hash"}
        computed_hash = hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()
        expect(recorded_hash == computed_hash, errors, f"proof ledger hash mismatch at {index}")
        previous = str(recorded_hash)
    expect(ledger.get("head_hash") == previous, errors, "proof ledger head hash mismatch")


def audit_outputs(errors: list[str]) -> None:
    for rel in REQUIRED_FILES:
        expect((OUTPUT_ROOT / rel).is_file(), errors, f"missing required output: {rel}")
    for rel in FORBIDDEN_OUTPUTS:
        expect(not (OUTPUT_ROOT / rel).exists(), errors, f"unexpected forbidden output: {rel}")
    manifest_errors, checked = verify_manifest(OUTPUT_ROOT)
    errors.extend(manifest_errors)
    expect(checked == len(REQUIRED_FILES) - 1, errors, "manifest entry count mismatch")

    results = load_json(OUTPUT_ROOT / "campaign_results.json", errors)
    v226_ingest = load_json(OUTPUT_ROOT / "v2_26_artifact_ingest_verification.json", errors)
    v227_official = load_json(OUTPUT_ROOT / "v2_27_official_artifact_verification.json", errors)
    v226_official = load_json(V226_ROOT / "v2_26_official_artifact_verification.json", errors)
    presence = load_json(OUTPUT_ROOT / "seed_draft_presence_check.json", errors)
    path_policy = load_json(OUTPUT_ROOT / "seed_draft_path_policy_check.json", errors)
    schema = load_json(OUTPUT_ROOT / "seed_draft_schema_validation.json", errors)
    guard = load_json(OUTPUT_ROOT / "seed_draft_forbidden_source_guard.json", errors)
    checkout = load_json(OUTPUT_ROOT / "seed_candidate_source_checkout_audit.json", errors)
    tree_manifest = load_json(OUTPUT_ROOT / "seed_candidate_buggy_tree_manifest.json", errors)
    target_hashes = load_json(OUTPUT_ROOT / "seed_candidate_target_test_file_hashes.json", errors)
    env_hashes = load_json(OUTPUT_ROOT / "seed_candidate_environment_file_hashes.json", errors)
    command = load_json(OUTPUT_ROOT / "seed_candidate_command_manifest.json", errors)
    env_preflight = load_json(OUTPUT_ROOT / "seed_candidate_environment_resolution_preflight.json", errors)
    failure_hash = load_json(OUTPUT_ROOT / "seed_candidate_failure_capture_hash.json", errors)
    signature = load_json(OUTPUT_ROOT / "seed_candidate_failure_signature_manifest.json", errors)
    colocation = load_json(OUTPUT_ROOT / "seed_candidate_source_test_colocation_proof.json", errors)
    entry_candidate = load_json(OUTPUT_ROOT / "seed_candidate_registry_entry_candidate.json", errors)
    merge = load_json(OUTPUT_ROOT / "seed_candidate_registry_merge_report.json", errors)
    validation = load_json(OUTPUT_ROOT / "external_candidate_registry_validation_report_after_merge.json", errors)
    status_after = load_json(OUTPUT_ROOT / "external_candidate_registry_status_after_merge.json", errors)
    public_language = load_json(OUTPUT_ROOT / "public_language_audit.json", errors)
    roadmap = load_json(OUTPUT_ROOT / "roadmap_carry_forward_check_v2_27.json", errors)
    claim = load_json(OUTPUT_ROOT / "claim_boundary_v2_27.json", errors)
    ledger = load_json(OUTPUT_ROOT / "proof_obligations_ledger.json", errors)
    v223_block = load_json(V223_ROOT / "global_bugsinpy_provenance_block.json", errors)
    registry = load_json(REGISTRY_PATH, errors)

    expect(v226_official.get("status") == "PASS", errors, "v2.26 official verification source not PASS")
    expect(v226_ingest.get("status") == "PASS", errors, "v2.26 artifact ingest not carried forward")
    expect(v226_ingest.get("zip_sha256") == "4d24593b2c68877e79731975ce824121f17145dcd4318c154a3d6a602aa8d81d", errors, "v2.26 digest mismatch")
    expect(v226_ingest.get("manual_artifact_boundary") == "PASS", errors, "v2.26 manual artifact boundary not carried forward")
    expect(v227_official.get("status") == "PASS", errors, "v2.27 official verification not PASS")
    for key, value in EXPECTED_V227_ARTIFACT.items():
        expect(v227_official.get(key) == value, errors, f"v2.27 official artifact {key} mismatch")
    expect(v227_official.get("safe_path_status") == "PASS", errors, "v2.27 artifact path safety not PASS")
    expect(v227_official.get("duplicate_path_count") == 0, errors, "v2.27 artifact duplicate paths found")
    expect(v227_official.get("internal_manifest_missing_count") == 0, errors, "v2.27 internal manifest missing entries")
    expect(v227_official.get("internal_manifest_malformed_count") == 0, errors, "v2.27 internal manifest malformed entries")
    expect(v227_official.get("internal_manifest_failure_count") == 0, errors, "v2.27 internal manifest hash failures")
    expect(v227_official.get("output_manifest_coverage") == "PASS", errors, "v2.27 output manifest coverage not PASS")
    expect(v227_official.get("manual_artifact_boundary") == "PASS", errors, "v2.27 manual artifact boundary not recorded")
    expect(v227_official.get("downloaded_by_codex") is False, errors, "v2.27 artifact custody claims Codex download")
    expect(v227_official.get("local_artifact_path_outside_git") is True, errors, "v2.27 local artifact path not outside Git")
    expect(v227_official.get("seed_absent_blocker_carry_forward_status") == "PASS", errors, "v2.27 seed blocker carry-forward not PASS")
    expect(v227_official.get("registry_validation_carry_forward_status") == "PASS", errors, "v2.27 registry carry-forward not PASS")
    expect(v227_official.get("byte_custody_fix_record_status") == "PASS", errors, "v2.27 byte-custody fix not recorded")
    expect(v227_official.get("v2_28_seed_draft_verification_recommendation_carry_forward_status") == "PASS", errors, "v2.28 recommendation carry-forward not PASS")
    expect(v223_block.get("status") == "BLOCK", errors, "benchmark framework global block status mismatch")
    expect(v223_block.get("candidate_selection_allowed") is False, errors, "benchmark framework global block not carried forward")

    fresh_validation = registry_validator.validate_registry()
    expect(fresh_validation.get("registry_validation_status") == "PASS", errors, "fresh registry validation did not PASS")
    expect(validation.get("registry_validation_status") == fresh_validation.get("registry_validation_status"), errors, "validation status stale")
    candidates = registry.get("candidates") if isinstance(registry.get("candidates"), list) else []

    seed_present = results.get("seed_draft_present") is True
    noncanonical_present = path_policy.get("deprecated_noncanonical_seed_path_present") is True
    expect(path_policy.get("canonical_seed_present") is seed_present, errors, "path policy canonical seed mismatch")
    expect(path_policy.get("noncanonical_seed_used") is False, errors, "noncanonical seed path was used")
    expect(path_policy.get("canonical_seed_required") is True, errors, "canonical seed path not required")

    if not seed_present:
        expect(results.get("exact_blocker") == BLOCKER_NO_SEED_DRAFT, errors, "absent seed-draft blocker mismatch")
        expect(presence.get("seed_draft_present") is False, errors, "presence check claims seed draft present")
        expect(schema.get("status") == "not_run_seed_draft_absent", errors, "schema validation status mismatch for absent seed")
        expect(checkout.get("external_clone_attempted") is False, errors, "external clone attempted despite absent seed")
        expect(merge.get("registry_updated_with_candidate") is False, errors, "registry updated despite absent seed")
        expect(results.get("registry_merge_status") == "not_run_seed_draft_absent", errors, "absent seed merge status mismatch")

    if seed_present:
        if schema.get("status") == "PASS":
            expect(command.get("external_network_dependency_detected") is False, errors, "seed command requires external network")
            expect(command.get("unsafe_shell_syntax_detected") is False, errors, "seed command contains unsafe syntax")
        if command.get("timeout_expected") is True:
            expect(isinstance(command.get("command_timeout_seconds"), int) and command.get("command_timeout_seconds") > 0, errors, "timeout seed missing timeout seconds")
            expect(isinstance(command.get("expected_timeout_classification"), str) and command.get("expected_timeout_classification"), errors, "timeout seed missing classification")
        if merge.get("registry_updated_with_candidate") is True:
            expect(colocation.get("target_test_physically_present_before_any_patch") is True, errors, "merged seed lacks native target test")
            expect(target_hashes.get("target_test_file_hashes_status") == "PASS", errors, "merged seed target hashes missing")
            expect(env_hashes.get("environment_lock_source_status") == "PASS", errors, "merged seed environment lock missing")
            expect(failure_hash.get("failure_capture_status") == "PASS", errors, "merged seed failure capture missing")
            expect(signature.get("failure_signature_manifest_status") == "PASS", errors, "merged seed signature missing")
            expect(validation.get("registry_validation_status") == "PASS", errors, "merged registry validation not PASS")
            expect(entry_candidate.get("candidate") is not None, errors, "merged seed candidate record missing")

    expect(guard.get("fixed_commit_read") is False, errors, "fixed commit read")
    expect(guard.get("future_commit_read") is False, errors, "future commit read")
    expect(guard.get("gold_patch_used") is False, errors, "gold patch used")
    expect(guard.get("hidden_label_used") is False, errors, "hidden label used")
    expect(guard.get("synthetic_or_generated_test_used") is False, errors, "synthetic/generated test used")
    expect(guard.get("generated_reproducer_accepted") is False, errors, "generated/manual reproducer accepted")
    expect(guard.get("native_buggy_test_required") is True, errors, "native buggy-test rule not enforced")
    expect(guard.get("external_network_dependency_detected") is False, errors, "external network seed dependency accepted")
    expect(checkout.get("fixed_commit_checked_out") is False, errors, "fixed commit checked out")
    expect(checkout.get("fixed_commit_read") is False, errors, "fixed commit read in checkout audit")
    expect(checkout.get("gold_patch_used") is False, errors, "gold patch used in checkout audit")
    expect(checkout.get("benchmark_framework_checkout_used") is False, errors, "benchmark framework checkout used")
    expect(target_hashes.get("generated_or_manual_reproducer_accepted") is False, errors, "generated/manual reproducer accepted as target test")
    expect(colocation.get("generated_or_manual_reproducer_accepted") is False, errors, "generated/manual reproducer accepted in co-location proof")
    expect(env_preflight.get("external_network_dependency_blocked") in {False, True}, errors, "environment preflight missing network block field")

    expect(results.get("live_issue_selected_directly") is False, errors, "live issue selected directly")
    expect(results.get("candidate_fabricated") is False, errors, "candidate fabricated")
    expect(results.get("repair_attempted") is False, errors, "repair attempted")
    expect(results.get("patch_generated") is False, errors, "patch generated")
    expect(claim.get("pysnooper1_reopened") is False, errors, "PySnooper:1 reopened")
    expect(claim.get("pysnooper2_pursued") is False, errors, "PySnooper:2 pursued")
    expect(claim.get("repair_engine_invoked") is False, errors, "repair engine invoked")
    expect(claim.get("post_patch_validation_run") is False, errors, "post-patch validation run")
    expect(claim.get("executed_scope_manifest_run") is False, errors, "executed scope manifest run")
    expect(claim.get("generated_reproducer_accepted_as_target_test") is False, errors, "generated reproducer claim boundary breach")
    expect(claim.get("external_network_seed_accepted") is False, errors, "external network seed accepted")
    expect(claim.get("timeout_seed_without_policy_accepted") is False, errors, "timeout seed without policy accepted")
    expect(claim.get("current_protocol_version") == "v2.13", errors, "current protocol changed")
    expect(claim.get("full_scoring") == "NOT_RUN", errors, "full scoring changed")
    expect(claim.get("full_scoring_allowed") is False, errors, "full scoring allowed")
    expect(claim.get("memory_lift_status") == "undemonstrated", errors, "memory lift claimed")
    expect(claim.get("self_maintaining_software_status") == "false/not_demonstrated", errors, "self-maintaining claim changed")
    expect(claim.get("final_non_ansible_positive_memory_count") == 0, errors, "non-Ansible positive-memory count changed")
    expect(status_after.get("registry_validation_status") == "PASS", errors, "registry validation after merge did not PASS")
    expect(status_after.get("reviewed_valid_candidate_count") == validation.get("valid_reviewed_candidate_count"), errors, "reviewed count mismatch after merge")
    expect(public_language.get("status") == "PASS", errors, "public language audit did not PASS")
    expect(roadmap.get("status") == "PASS", errors, "roadmap carry-forward check did not PASS")
    expect(tree_manifest.get("status") in {"PASS", "not_run_seed_draft_absent", "not_run_schema_or_policy_blocked"}, errors, "tree manifest status unexpected")
    audit_proof_ledger(ledger, errors)

    print(f"v2.27 manifest entries checked: {checked}")
    for key in [
        "seed_draft_present",
        "seed_draft_validation_status",
        "seed_path_policy_status",
        "external_clone_attempted",
        "target_test_colocation_status",
        "failure_capture_status",
        "registry_merge_status",
        "registry_validation_status_after_merge",
        "reviewed_valid_candidate_count_after_run",
        "exact_blocker",
        "full_scoring",
        "memory_lift_status",
        "self_maintaining_software_status",
    ]:
        print(f"{key}={results.get(key)}")


def main() -> int:
    errors: list[str] = []
    if not OUTPUT_ROOT.is_dir():
        errors.append(f"missing output root: {OUTPUT_ROOT.relative_to(REPO_ROOT).as_posix()}")
    else:
        audit_outputs(errors)
    for script in regression_scripts():
        run_python_script(script, errors)
    current_audit = subprocess.run(
        [sys.executable, "scripts/controllergate_audit.py", "--protocol", "current"],
        cwd=str(REPO_ROOT),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if current_audit.returncode != 0:
        errors.append("current protocol audit failed")
    current_dry_run = subprocess.run(
        [sys.executable, "scripts/controllergate_run.py", "--protocol", "current", "--dry-run"],
        cwd=str(REPO_ROOT),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if current_dry_run.returncode != 0:
        errors.append("current protocol dry-run failed")
    if errors:
        print("v2.27 audit FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("v2.27 audit PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
