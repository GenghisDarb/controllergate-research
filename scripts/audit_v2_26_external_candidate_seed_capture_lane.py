#!/usr/bin/env python3
"""Audit v2.26 External Candidate Seed Capture Lane evidence."""

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
CAMPAIGN_ID = "v2_26_external_candidate_seed_capture_lane"
OUTPUT_ROOT = REPO_ROOT / "outputs" / CAMPAIGN_ID
REGISTRY_PATH = REPO_ROOT / "configs" / "external_candidate_registry.json"
SEED_DRAFT_PATH = REPO_ROOT / "inputs" / "external_candidate_seed_draft.json"
SEED_EXAMPLE_PATH = REPO_ROOT / "inputs" / "external_candidate_seed_draft.example.json"
V225_ROOT = REPO_ROOT / "outputs" / "v2_25_external_candidate_registry_construction_lane"
V223_ROOT = REPO_ROOT / "outputs" / "v2_23_non_ansible_candidate_transition_lane"
BLOCKER_NO_SEED_DRAFT = "blocked_no_external_candidate_seed_draft_provided"
EXPECTED_V226_ARTIFACT = {
    "artifact_name": "v2_26_external_candidate_seed_capture_lane_artifacts",
    "workflow_run_id": 28253314598,
    "artifact_id": 7911677755,
    "zip_size": 67443,
    "zip_sha256": "4d24593b2c68877e79731975ce824121f17145dcd4318c154a3d6a602aa8d81d",
    "entry_count": 38,
    "internal_manifest_checked": 27,
}

REQUIRED_FILES = [
    "campaign_summary.md",
    "campaign_results.json",
    "v2_25_artifact_ingest_verification.json",
    "v2_26_official_artifact_verification.json",
    "artifact_repo_snapshot_comparison.json",
    "seed_draft_presence_check.json",
    "seed_draft_schema_validation.json",
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
    "roadmap_carry_forward_check_v2_26.json",
    "resolution_depth_diagnostic_v2_26.json",
    "claim_boundary_v2_26.json",
    "proof_obligations_ledger.json",
    "SHA256SUMS.txt",
]
FORBIDDEN_OUTPUTS = {
    "memory_enabled_source_only_repair_patch.diff",
    "target_validation_log.txt",
    "duplicate_replay_summary.json",
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
    expect(isinstance(entries, list) and len(entries) >= 5, errors, "proof ledger entries missing")
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
        expect(not (OUTPUT_ROOT / rel).exists(), errors, f"unexpected repair output: {rel}")
    manifest_errors, checked = verify_manifest(OUTPUT_ROOT)
    errors.extend(manifest_errors)
    expect(checked == len(REQUIRED_FILES) - 1, errors, "manifest entry count mismatch")

    results = load_json(OUTPUT_ROOT / "campaign_results.json", errors)
    v225 = load_json(OUTPUT_ROOT / "v2_25_artifact_ingest_verification.json", errors)
    v226_official = load_json(OUTPUT_ROOT / "v2_26_official_artifact_verification.json", errors)
    presence = load_json(OUTPUT_ROOT / "seed_draft_presence_check.json", errors)
    schema = load_json(OUTPUT_ROOT / "seed_draft_schema_validation.json", errors)
    guard = load_json(OUTPUT_ROOT / "seed_draft_forbidden_source_guard.json", errors)
    checkout = load_json(OUTPUT_ROOT / "seed_candidate_source_checkout_audit.json", errors)
    tree_manifest = load_json(OUTPUT_ROOT / "seed_candidate_buggy_tree_manifest.json", errors)
    target_hashes = load_json(OUTPUT_ROOT / "seed_candidate_target_test_file_hashes.json", errors)
    env_hashes = load_json(OUTPUT_ROOT / "seed_candidate_environment_file_hashes.json", errors)
    failure_hash = load_json(OUTPUT_ROOT / "seed_candidate_failure_capture_hash.json", errors)
    signature = load_json(OUTPUT_ROOT / "seed_candidate_failure_signature_manifest.json", errors)
    colocation = load_json(OUTPUT_ROOT / "seed_candidate_source_test_colocation_proof.json", errors)
    merge = load_json(OUTPUT_ROOT / "seed_candidate_registry_merge_report.json", errors)
    validation = load_json(OUTPUT_ROOT / "external_candidate_registry_validation_report_after_merge.json", errors)
    status_after = load_json(OUTPUT_ROOT / "external_candidate_registry_status_after_merge.json", errors)
    public_language = load_json(OUTPUT_ROOT / "public_language_audit.json", errors)
    roadmap = load_json(OUTPUT_ROOT / "roadmap_carry_forward_check_v2_26.json", errors)
    claim = load_json(OUTPUT_ROOT / "claim_boundary_v2_26.json", errors)
    ledger = load_json(OUTPUT_ROOT / "proof_obligations_ledger.json", errors)
    v225_official = load_json(V225_ROOT / "v2_25_official_artifact_verification.json", errors)
    v223_block = load_json(V223_ROOT / "global_bugsinpy_provenance_block.json", errors)
    registry = load_json(REGISTRY_PATH, errors)

    expect(SEED_EXAMPLE_PATH.is_file(), errors, "seed draft example missing")
    expect(v225.get("status") == "PASS", errors, "v2.25 artifact ingest verification not carried forward")
    expect(v225.get("zip_sha256") == "41ac43048ca834c203542b2e0b9c9045c2ceb1be43a963cf2d4c66ca250864b2", errors, "v2.25 digest mismatch")
    expect(v226_official.get("status") == "PASS", errors, "v2.26 official verification not PASS")
    for key, value in EXPECTED_V226_ARTIFACT.items():
        expect(v226_official.get(key) == value, errors, f"v2.26 official artifact {key} mismatch")
    expect(v226_official.get("safe_path_status") == "PASS", errors, "v2.26 artifact path safety not PASS")
    expect(v226_official.get("duplicate_path_count") == 0, errors, "v2.26 artifact duplicate paths found")
    expect(v226_official.get("internal_manifest_missing_count") == 0, errors, "v2.26 internal manifest missing entries")
    expect(v226_official.get("internal_manifest_malformed_count") == 0, errors, "v2.26 internal manifest malformed entries")
    expect(v226_official.get("internal_manifest_failure_count") == 0, errors, "v2.26 internal manifest hash failures")
    expect(v226_official.get("output_manifest_coverage") == "PASS", errors, "v2.26 output manifest coverage not PASS")
    expect(v226_official.get("manual_artifact_boundary") == "PASS", errors, "v2.26 manual artifact boundary not recorded")
    expect(v226_official.get("downloaded_by_codex") is False, errors, "v2.26 artifact custody claims Codex download")
    expect(v226_official.get("local_artifact_path_outside_git") is True, errors, "v2.26 local artifact path not outside Git")
    expect(v226_official.get("seed_absent_blocker_carry_forward_status") == "PASS", errors, "v2.26 seed blocker carry-forward not PASS")
    expect(v226_official.get("registry_validation_carry_forward_status") == "PASS", errors, "v2.26 registry carry-forward not PASS")
    expect(v226_official.get("v2_27_seed_draft_verification_recommendation_carry_forward_status") == "PASS", errors, "v2.27 recommendation carry-forward not PASS")
    expect(v225_official.get("status") == "PASS", errors, "v2.25 official verification source not PASS")
    expect(v223_block.get("status") == "BLOCK", errors, "benchmark framework global block status mismatch")
    expect(v223_block.get("candidate_selection_allowed") is False, errors, "benchmark framework global block not carried forward")

    fresh_validation = registry_validator.validate_registry()
    expect(fresh_validation.get("registry_validation_status") == "PASS", errors, "fresh registry validation did not PASS")
    expect(validation.get("registry_validation_status") == fresh_validation.get("registry_validation_status"), errors, "validation status stale")
    expect(validation.get("registry_sha256") == sha256_path(REGISTRY_PATH), errors, "validation registry SHA stale")
    candidates = registry.get("candidates") if isinstance(registry.get("candidates"), list) else []
    seed_present = SEED_DRAFT_PATH.is_file()
    if not seed_present:
        expect(results.get("exact_blocker") == BLOCKER_NO_SEED_DRAFT, errors, "absent seed-draft blocker mismatch")
        expect(presence.get("seed_draft_present") is False, errors, "presence check claims seed draft present")
        expect(schema.get("status") == "not_run_seed_draft_absent", errors, "schema validation status mismatch for absent seed")
        expect(checkout.get("external_clone_attempted") is False, errors, "external clone attempted despite absent seed")
        expect(merge.get("registry_updated_with_candidate") is False, errors, "registry updated despite absent seed")
        expect(candidates == [], errors, "candidate entry fabricated despite absent seed")

    for container_name, container in {
        "results": results,
        "checkout": checkout,
        "claim": claim,
    }.items():
        expect(container.get("external_clone_attempted") is False, errors, f"{container_name}: external clone attempted")
    expect(guard.get("benchmark_framework_checkout_used") is False, errors, "benchmark framework checkout used")
    expect(guard.get("fixed_commit_read") is False, errors, "fixed commit read")
    expect(guard.get("future_commit_read") is False, errors, "future commit read")
    expect(guard.get("gold_patch_used") is False, errors, "gold patch used")
    expect(guard.get("hidden_label_used") is False, errors, "hidden label used")
    expect(tree_manifest.get("status") in {"not_run_seed_draft_absent", "not_run_schema_blocked"}, errors, "tree manifest unexpected status")
    expect(target_hashes.get("target_test_file_hashes_status") in {"not_run_seed_draft_absent", "not_run_schema_blocked"}, errors, "target hash status mismatch")
    expect(env_hashes.get("environment_lock_source_status") in {"not_run_seed_draft_absent", "not_run_schema_blocked"}, errors, "environment lock status mismatch")
    expect(failure_hash.get("failure_capture_status") in {"not_run_seed_draft_absent", "not_run_schema_blocked"}, errors, "failure capture status mismatch")
    expect(signature.get("failure_signature_manifest_status") in {"not_run_seed_draft_absent", "not_run_schema_blocked"}, errors, "signature status mismatch")
    expect(colocation.get("source_test_colocation_status") in {"not_run_seed_draft_absent", "not_run_schema_blocked"}, errors, "co-location status mismatch")
    expect(status_after.get("registry_validation_status") == "PASS", errors, "registry validation after merge did not PASS")
    expect(status_after.get("reviewed_valid_candidate_count") == validation.get("valid_reviewed_candidate_count"), errors, "reviewed count mismatch after merge")

    expect(results.get("live_issue_selected_directly") is False, errors, "live issue selected directly")
    expect(results.get("candidate_fabricated") is False, errors, "candidate fabricated")
    expect(results.get("repair_attempted") is False, errors, "repair attempted")
    expect(results.get("patch_generated") is False, errors, "patch generated")
    expect(claim.get("pysnooper1_reopened") is False, errors, "PySnooper:1 reopened")
    expect(claim.get("pysnooper2_pursued") is False, errors, "PySnooper:2 pursued")
    expect(claim.get("repair_engine_invoked") is False, errors, "repair engine invoked")
    expect(claim.get("current_protocol_version") == "v2.13", errors, "current protocol changed")
    expect(claim.get("full_scoring") == "NOT_RUN", errors, "full scoring changed")
    expect(claim.get("full_scoring_allowed") is False, errors, "full scoring allowed")
    expect(claim.get("memory_lift_status") == "undemonstrated", errors, "memory lift claimed")
    expect(claim.get("self_maintaining_software_status") == "false/not_demonstrated", errors, "self-maintaining claim changed")
    expect(claim.get("final_non_ansible_positive_memory_count") == 0, errors, "non-Ansible positive-memory count changed")
    expect(public_language.get("status") == "PASS", errors, "public language audit did not PASS")
    expect(roadmap.get("status") == "PASS", errors, "roadmap carry-forward check did not PASS")
    audit_proof_ledger(ledger, errors)

    print(f"v2.26 manifest entries checked: {checked}")
    for key in [
        "seed_draft_present",
        "seed_draft_validation_status",
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
        print("v2.26 audit FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("v2.26 audit PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
