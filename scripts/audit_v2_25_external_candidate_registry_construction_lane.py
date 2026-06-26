#!/usr/bin/env python3
"""Audit v2.25 External Candidate Registry Construction Lane evidence."""

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
CAMPAIGN_ID = "v2_25_external_candidate_registry_construction_lane"
OUTPUT_ROOT = REPO_ROOT / "outputs" / CAMPAIGN_ID
REGISTRY_PATH = REPO_ROOT / "configs" / "external_candidate_registry.json"
SCHEMA_PATH = REPO_ROOT / "configs" / "external_candidate_registry.schema.json"
VALIDATOR_PATH = REPO_ROOT / "scripts" / "validate_external_candidate_registry.py"
SEED_PATH = REPO_ROOT / "inputs" / "external_candidate_registry_seed.json"
V224_ROOT = REPO_ROOT / "outputs" / "v2_24_external_safe_source_candidate_acquisition_lane"
V223_ROOT = REPO_ROOT / "outputs" / "v2_23_non_ansible_candidate_transition_lane"
BLOCKER_NO_SEED = "blocked_no_reviewed_external_candidate_seed_provided"
REQUIRED_FILES = [
    "campaign_summary.md",
    "campaign_results.json",
    "v2_24_artifact_ingest_verification.json",
    "artifact_repo_snapshot_comparison.json",
    "external_candidate_registry_schema.json",
    "external_candidate_registry_validation_report.json",
    "external_candidate_registry_seed_ingest_report.json",
    "external_candidate_registry_candidate_review_report.json",
    "external_candidate_registry_failure_signature_policy.json",
    "external_candidate_registry_normalization_policy.json",
    "external_candidate_registry_status.json",
    "external_candidate_registry_next_step.json",
    "public_language_audit.json",
    "roadmap_carry_forward_check_v2_25.json",
    "resolution_depth_diagnostic_v2_25.json",
    "claim_boundary_v2_25.json",
    "proof_obligations_ledger.json",
    "SHA256SUMS.txt",
]
FORBIDDEN_OUTPUTS = {
    "memory_enabled_source_only_repair_patch.diff",
    "target_validation_log.txt",
    "duplicate_replay_summary.json",
    "seed_candidate_source_checkout_audit.json",
    "seed_candidate_buggy_tree_manifest.json",
    "seed_candidate_target_test_file_hashes.json",
    "seed_candidate_environment_file_hashes.json",
    "seed_candidate_failure_capture_log.txt",
    "seed_candidate_failure_capture_normalized.txt",
    "seed_candidate_failure_capture_hash.json",
    "seed_candidate_failure_signature_comparison.json",
    "seed_candidate_registry_entry_written.json",
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
        expect(not (OUTPUT_ROOT / rel).exists(), errors, f"unexpected seed execution or repair output: {rel}")
    manifest_errors, checked = verify_manifest(OUTPUT_ROOT)
    errors.extend(manifest_errors)
    expect(checked == len(REQUIRED_FILES) - 1, errors, "manifest entry count mismatch")

    registry = load_json(REGISTRY_PATH, errors)
    schema = load_json(SCHEMA_PATH, errors)
    results = load_json(OUTPUT_ROOT / "campaign_results.json", errors)
    v224 = load_json(OUTPUT_ROOT / "v2_24_artifact_ingest_verification.json", errors)
    validation_report = load_json(OUTPUT_ROOT / "external_candidate_registry_validation_report.json", errors)
    seed_report = load_json(OUTPUT_ROOT / "external_candidate_registry_seed_ingest_report.json", errors)
    review_report = load_json(OUTPUT_ROOT / "external_candidate_registry_candidate_review_report.json", errors)
    status = load_json(OUTPUT_ROOT / "external_candidate_registry_status.json", errors)
    next_step = load_json(OUTPUT_ROOT / "external_candidate_registry_next_step.json", errors)
    public_language = load_json(OUTPUT_ROOT / "public_language_audit.json", errors)
    roadmap = load_json(OUTPUT_ROOT / "roadmap_carry_forward_check_v2_25.json", errors)
    claim = load_json(OUTPUT_ROOT / "claim_boundary_v2_25.json", errors)
    ledger = load_json(OUTPUT_ROOT / "proof_obligations_ledger.json", errors)
    v223_block = load_json(V223_ROOT / "global_bugsinpy_provenance_block.json", errors)
    v224_official = load_json(V224_ROOT / "v2_24_official_artifact_verification.json", errors)

    expect(SCHEMA_PATH.is_file(), errors, "registry schema file missing")
    expect(VALIDATOR_PATH.is_file(), errors, "validator script missing")
    expect(REGISTRY_PATH.is_file(), errors, "registry file missing")
    expect(registry.get("schema_version") == "v2.25", errors, "registry schema version mismatch")
    expect(registry.get("review_policy") == registry_validator.REQUIRED_REVIEW_POLICY, errors, "registry review policy mismatch")
    expect(isinstance(registry.get("candidates"), list), errors, "registry candidates must be a list")
    expect(schema.get("title") == "ControllerGate External Candidate Registry", errors, "schema title mismatch")

    fresh_validation = registry_validator.validate_registry()
    expect(fresh_validation.get("registry_validation_status") == "PASS", errors, "fresh registry validation did not PASS")
    expect(validation_report.get("registry_validation_status") == fresh_validation.get("registry_validation_status"), errors, "validation report status stale")
    expect(validation_report.get("registry_sha256") == sha256_path(REGISTRY_PATH), errors, "validation report registry SHA stale")
    expect(validation_report.get("schema_sha256") == sha256_path(SCHEMA_PATH), errors, "validation report schema SHA stale")

    seed_present = SEED_PATH.is_file()
    candidates = registry.get("candidates") if isinstance(registry.get("candidates"), list) else []
    if not seed_present:
        expect(candidates == [], errors, "candidate entry fabricated despite absent seed")
        expect(seed_report.get("exact_blocker") == BLOCKER_NO_SEED, errors, "absent-seed blocker mismatch")
        expect(seed_report.get("external_clone_attempted") is False, errors, "external clone attempted despite absent seed")
        expect(seed_report.get("registry_updated_with_candidate") is False, errors, "registry updated despite absent seed")
    expect(results.get("registry_candidate_count") == len(candidates), errors, "results candidate count mismatch")
    expect(results.get("reviewed_valid_candidate_count") == validation_report.get("valid_reviewed_candidate_count"), errors, "reviewed count mismatch")

    expect(v224.get("status") == "PASS", errors, "v2.24 ingest verification not carried forward")
    expect(v224.get("zip_sha256") == "1801c197bb032c415dea4a33a9208042b0377d069e95fc4cde1ab4e0f2e7db8d", errors, "v2.24 digest mismatch")
    expect(v224_official.get("status") == "PASS", errors, "v2.24 official verification source not PASS")
    expect(v223_block.get("status") == "BLOCK", errors, "benchmark framework global block source status mismatch")
    expect(v223_block.get("candidate_selection_allowed") is False, errors, "benchmark framework global block not carried forward")

    for container_name, container in {
        "results": results,
        "status": status,
        "review_report": review_report,
        "claim": claim,
    }.items():
        expect(container.get("external_clone_attempted") is False, errors, f"{container_name}: external clone attempted")
        expect(container.get("patch_generated") in {False, None}, errors, f"{container_name}: patch generated")
        expect(container.get("patch_attempted") in {False, None}, errors, f"{container_name}: patch attempted")
    expect(review_report.get("live_issue_selected_directly") is False, errors, "live issue selected directly")
    expect(claim.get("pysnooper1_reopened") is False, errors, "PySnooper:1 reopened")
    expect(claim.get("pysnooper2_pursued") is False, errors, "PySnooper:2 pursued")
    expect(claim.get("repair_engine_invoked") is False, errors, "repair engine invoked")
    expect(claim.get("repair_attempted") is False, errors, "repair attempted")
    expect(claim.get("current_protocol_version") == "v2.13", errors, "current protocol changed")
    expect(claim.get("full_scoring") == "NOT_RUN", errors, "full scoring changed")
    expect(claim.get("full_scoring_allowed") is False, errors, "full scoring allowed")
    expect(claim.get("memory_lift_status") == "undemonstrated", errors, "memory lift claimed")
    expect(claim.get("self_maintaining_software_status") == "false/not_demonstrated", errors, "self-maintaining claim changed")
    expect(claim.get("final_non_ansible_positive_memory_count") == 0, errors, "non-Ansible positive-memory count changed")

    expect(public_language.get("status") == "PASS", errors, "public language audit did not PASS")
    expect(roadmap.get("status") == "PASS", errors, "roadmap carry-forward check did not PASS")
    expect(next_step.get("do_not_begin_next_version_in_this_lane") is True, errors, "next-version stop boundary missing")
    audit_proof_ledger(ledger, errors)

    print(f"v2.25 manifest entries checked: {checked}")
    for key in [
        "registry_validation_status",
        "registry_candidate_count",
        "reviewed_valid_candidate_count",
        "seed_file_present",
        "external_clone_attempted",
        "failure_capture_status",
        "registry_updated_with_candidate",
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
        print("v2.25 audit FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("v2.25 audit PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
