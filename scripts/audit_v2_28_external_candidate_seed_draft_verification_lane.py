#!/usr/bin/env python3
"""Audit v2.28 External Candidate Seed Draft Verification Lane evidence."""

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
CAMPAIGN_ID = "v2_28_external_candidate_seed_draft_verification_lane"
OUTPUT_ROOT = REPO_ROOT / "outputs" / CAMPAIGN_ID
REGISTRY_PATH = REPO_ROOT / "configs" / "external_candidate_registry.json"
SEED_PATH = REPO_ROOT / "inputs" / "external_candidate_seed_draft.json"
NONCANONICAL_SEED_PATH = REPO_ROOT / "configs" / "candidate_seed_draft.json"
V227_ROOT = REPO_ROOT / "outputs" / "v2_27_external_candidate_seed_draft_verification_lane"
V223_ROOT = REPO_ROOT / "outputs" / "v2_23_non_ansible_candidate_transition_lane"
EXPECTED_SEED = {
    "candidate_id": "py_bugger_issue_65",
    "repo_url": "https://github.com/ehmatthes/py-bugger",
    "buggy_commit_sha": "67cf214f2d619848e90280fd4469377123e81b94",
    "test_command": "python -m pytest tests/integration_tests/test_modifications.py::test_indentationerror_multiple_trys -q",
    "target_test_file_paths": ["tests/integration_tests/test_modifications.py"],
    "support_file_paths": ["tests/sample_code/sample_scripts/two_trys.py"],
    "environment_lock_source": "pyproject.toml",
}
ALLOWED_BLOCKERS = {
    None,
    "blocked_external_candidate_seed_draft_invalid",
    "seed_capture_target_test_not_in_buggy_tree",
    "seed_capture_support_file_not_in_buggy_tree",
    "seed_capture_external_network_dependency_blocked",
    "seed_capture_generated_reproducer_forbidden",
    "seed_capture_timeout_policy_missing",
    "seed_capture_pre_repair_environmental_pass",
    "seed_capture_environment_resolution_failed",
    "seed_capture_target_test_not_executed",
    "seed_capture_test_harness_defect",
    "seed_capture_registry_validation_failed",
    "blocked_noncanonical_seed_path_only",
    "blocked_placeholder_seed_value_detected",
    "seed_capture_failure_not_matching_seed_intent",
}
REQUIRED_FILES = [
    "campaign_summary.md",
    "campaign_results.json",
    "v2_27_artifact_ingest_verification.json",
    "artifact_repo_snapshot_comparison.json",
    "seed_draft_presence_check.json",
    "seed_draft_schema_validation.json",
    "seed_draft_path_policy_check.json",
    "seed_draft_forbidden_source_guard.json",
    "seed_candidate_lead_truth_audit.json",
    "seed_candidate_issue_reference_audit.json",
    "seed_candidate_network_dependency_audit.json",
    "seed_candidate_timeout_policy_audit.json",
    "seed_candidate_test_execution_intent_match.json",
    "seed_candidate_source_checkout_audit.json",
    "seed_candidate_buggy_tree_manifest.json",
    "seed_candidate_target_test_file_hashes.json",
    "seed_candidate_support_file_hashes.json",
    "seed_candidate_environment_file_hashes.json",
    "seed_candidate_command_manifest.json",
    "seed_candidate_environment_resolution_preflight.json",
    "seed_candidate_failure_capture_raw.log",
    "seed_candidate_failure_capture_normalized.txt",
    "seed_candidate_failure_capture_hash.json",
    "seed_candidate_failure_signature_manifest.json",
    "seed_candidate_source_test_colocation_proof.json",
    "seed_candidate_support_file_colocation_proof.json",
    "seed_candidate_registry_entry_candidate.json",
    "seed_candidate_registry_merge_report.json",
    "external_candidate_registry_validation_report_after_merge.json",
    "external_candidate_registry_status_after_merge.json",
    "public_language_audit.json",
    "roadmap_carry_forward_check_v2_28.json",
    "resolution_depth_diagnostic_v2_28.json",
    "claim_boundary_v2_28.json",
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
    result = subprocess.run([sys.executable, str(REPO_ROOT / script)], cwd=str(REPO_ROOT), text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if result.returncode != 0:
        tail = "\n".join((result.stdout + "\n" + result.stderr).splitlines()[-20:])
        errors.append(f"regression audit failed: {script}\n{tail}")


def regression_scripts() -> list[str]:
    return [
        "scripts/audit_v2_27_external_candidate_seed_draft_verification_lane.py",
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
    expect(isinstance(entries, list) and len(entries) >= 8, errors, "proof ledger entries missing")
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
    seed = load_json(SEED_PATH, errors)
    ingest = load_json(OUTPUT_ROOT / "v2_27_artifact_ingest_verification.json", errors)
    schema = load_json(OUTPUT_ROOT / "seed_draft_schema_validation.json", errors)
    path_policy = load_json(OUTPUT_ROOT / "seed_draft_path_policy_check.json", errors)
    guard = load_json(OUTPUT_ROOT / "seed_draft_forbidden_source_guard.json", errors)
    lead = load_json(OUTPUT_ROOT / "seed_candidate_lead_truth_audit.json", errors)
    issue_ref = load_json(OUTPUT_ROOT / "seed_candidate_issue_reference_audit.json", errors)
    network = load_json(OUTPUT_ROOT / "seed_candidate_network_dependency_audit.json", errors)
    timeout = load_json(OUTPUT_ROOT / "seed_candidate_timeout_policy_audit.json", errors)
    intent = load_json(OUTPUT_ROOT / "seed_candidate_test_execution_intent_match.json", errors)
    checkout = load_json(OUTPUT_ROOT / "seed_candidate_source_checkout_audit.json", errors)
    target_hashes = load_json(OUTPUT_ROOT / "seed_candidate_target_test_file_hashes.json", errors)
    support_hashes = load_json(OUTPUT_ROOT / "seed_candidate_support_file_hashes.json", errors)
    env_hashes = load_json(OUTPUT_ROOT / "seed_candidate_environment_file_hashes.json", errors)
    env_preflight = load_json(OUTPUT_ROOT / "seed_candidate_environment_resolution_preflight.json", errors)
    failure_hash = load_json(OUTPUT_ROOT / "seed_candidate_failure_capture_hash.json", errors)
    signature = load_json(OUTPUT_ROOT / "seed_candidate_failure_signature_manifest.json", errors)
    colocation = load_json(OUTPUT_ROOT / "seed_candidate_source_test_colocation_proof.json", errors)
    support_colocation = load_json(OUTPUT_ROOT / "seed_candidate_support_file_colocation_proof.json", errors)
    entry = load_json(OUTPUT_ROOT / "seed_candidate_registry_entry_candidate.json", errors)
    merge = load_json(OUTPUT_ROOT / "seed_candidate_registry_merge_report.json", errors)
    validation = load_json(OUTPUT_ROOT / "external_candidate_registry_validation_report_after_merge.json", errors)
    status_after = load_json(OUTPUT_ROOT / "external_candidate_registry_status_after_merge.json", errors)
    public_language = load_json(OUTPUT_ROOT / "public_language_audit.json", errors)
    roadmap = load_json(OUTPUT_ROOT / "roadmap_carry_forward_check_v2_28.json", errors)
    claim = load_json(OUTPUT_ROOT / "claim_boundary_v2_28.json", errors)
    ledger = load_json(OUTPUT_ROOT / "proof_obligations_ledger.json", errors)
    v227_official = load_json(V227_ROOT / "v2_27_official_artifact_verification.json", errors)
    v223_block = load_json(V223_ROOT / "global_bugsinpy_provenance_block.json", errors)

    expect(v227_official.get("status") == "PASS", errors, "v2.27 official verification source not PASS")
    expect(ingest.get("status") == "PASS", errors, "v2.27 artifact ingest not carried forward")
    expect(ingest.get("zip_sha256") == "3a25700c93647b531cbf1c561e6b84925517547b0f745a27f5a3a21f3c046ec3", errors, "v2.27 digest mismatch")
    expect(v223_block.get("status") == "BLOCK", errors, "benchmark framework global block status mismatch")
    expect(v223_block.get("candidate_selection_allowed") is False, errors, "benchmark framework global block not carried forward")
    for key, expected in EXPECTED_SEED.items():
        expect(seed.get(key) == expected, errors, f"seed draft {key} mismatch")
    expect(schema.get("status") == "PASS", errors, "seed schema did not PASS")
    expect(schema.get("brad_supplied_seed_match") is True, errors, "Brad-supplied seed match not recorded")
    expect(path_policy.get("canonical_seed_present") is True, errors, "canonical seed not present")
    expect(path_policy.get("noncanonical_seed_used") is False, errors, "noncanonical seed path used")
    expect(not NONCANONICAL_SEED_PATH.exists(), errors, "deprecated seed path exists")
    expect(guard.get("fixed_commit_read") is False, errors, "fixed commit read")
    expect(guard.get("later_commit_read") is False, errors, "later commit read")
    expect(guard.get("gold_patch_used") is False, errors, "gold patch used")
    expect(guard.get("hidden_label_used") is False, errors, "hidden label used")
    expect(guard.get("benchmark_framework_checkout_used") is False, errors, "benchmark framework checkout used")
    expect(guard.get("generated_or_manual_reproducer_accepted") is False, errors, "generated/manual reproducer accepted")
    expect(network.get("test_command_requires_external_network") is False, errors, "test command requires external network")
    expect(network.get("status") == "PASS", errors, "network guard did not PASS")
    expect(timeout.get("status") in {"PASS", "BLOCK"}, errors, "timeout audit status invalid")
    expect(lead.get("lead_treated_as_registry_truth") is False, errors, "lead treated as registry truth")
    expect(issue_ref.get("lead_content_used_as_repair_evidence") is False, errors, "issue lead used as repair evidence")
    expect(issue_ref.get("pr_patch_content_inspected") is False, errors, "PR patch content inspected")
    expect(checkout.get("fixed_or_later_commit_accessed") is False, errors, "fixed/later commit accessed")
    expect(checkout.get("fixed_commit_checked_out") is False, errors, "fixed commit checked out")

    blocker = results.get("exact_blocker")
    expect(blocker in ALLOWED_BLOCKERS, errors, f"unexpected blocker {blocker}")
    if blocker is None:
        expect(results.get("status") == "verified_external_candidate_seed_added", errors, "success status mismatch")
        expect(checkout.get("exact_buggy_commit_checked_out") is True, errors, "success without exact commit checkout")
        expect(target_hashes.get("target_test_file_hashes_status") == "PASS", errors, "success without target hash")
        expect(support_hashes.get("support_file_hashes_status") == "PASS", errors, "success without support hash")
        expect(env_hashes.get("environment_lock_source_status") == "PASS", errors, "success without environment hash")
        expect(failure_hash.get("failure_capture_status") == "PASS", errors, "success without failure capture")
        expect(signature.get("failure_signature_manifest_status") == "PASS", errors, "success without signature")
        expect(colocation.get("target_test_physically_present_before_any_patch") is True, errors, "success without native target test")
        expect(support_colocation.get("support_files_physically_present_in_buggy_tree") is True, errors, "success without native support file")
        expect(intent.get("target_test_executed") is True, errors, "success without target execution")
        expect(merge.get("registry_updated_with_candidate") is True, errors, "success without registry update")
        expect(entry.get("candidate") is not None, errors, "success without candidate entry")
    else:
        expect(merge.get("registry_updated_with_candidate") is False, errors, "blocked run updated registry")
        if blocker == "seed_capture_environment_resolution_failed":
            expect(
                env_preflight.get("environment_install_status") in {"BLOCK", "venv_creation_failed"},
                errors,
                "environment blocker without install block",
            )
        if blocker == "seed_capture_target_test_not_in_buggy_tree":
            expect(target_hashes.get("target_test_file_hashes_status") == "BLOCK", errors, "target blocker without target block")
        if blocker == "seed_capture_support_file_not_in_buggy_tree":
            expect(support_hashes.get("support_file_hashes_status") == "BLOCK", errors, "support blocker without support block")

    fresh_validation = registry_validator.validate_registry()
    expect(fresh_validation.get("registry_validation_status") == "PASS", errors, "fresh registry validation did not PASS")
    expect(validation.get("registry_validation_status") == fresh_validation.get("registry_validation_status"), errors, "validation status stale")
    expect(validation.get("registry_sha256") == sha256_path(REGISTRY_PATH), errors, "validation registry SHA stale")
    expect(status_after.get("registry_validation_status") == "PASS", errors, "registry validation after merge did not PASS")
    expect(status_after.get("reviewed_valid_candidate_count") == validation.get("valid_reviewed_candidate_count"), errors, "reviewed count mismatch")
    expect(public_language.get("status") == "PASS", errors, "public language audit did not PASS")
    expect(roadmap.get("status") == "PASS", errors, "roadmap carry-forward check did not PASS")
    expect(claim.get("current_protocol_version") == "v2.13", errors, "current protocol changed")
    expect(claim.get("full_scoring") == "NOT_RUN", errors, "full scoring changed")
    expect(claim.get("full_scoring_allowed") is False, errors, "full scoring allowed")
    expect(claim.get("repair_attempted") is False, errors, "repair attempted")
    expect(claim.get("patch_generated") is False, errors, "patch generated")
    expect(claim.get("repair_engine_invoked") is False, errors, "repair engine invoked")
    expect(claim.get("pysnooper1_reopened") is False, errors, "PySnooper:1 reopened")
    expect(claim.get("pysnooper2_pursued") is False, errors, "PySnooper:2 pursued")
    expect(claim.get("pr_patch_content_used_as_repair_evidence") is False, errors, "PR patch used as repair evidence")
    expect(claim.get("fixed_or_later_commit_accessed") is False, errors, "fixed/later commit accessed in claim")
    expect(claim.get("memory_lift_status") == "undemonstrated", errors, "memory lift claimed")
    expect(claim.get("self_maintaining_software_status") == "false/not_demonstrated", errors, "self-maintaining claim changed")
    audit_proof_ledger(ledger, errors)

    print(f"v2.28 manifest entries checked: {checked}")
    for key in [
        "seed_draft_present",
        "seed_draft_validation_status",
        "external_clone_attempted",
        "exact_commit_checkout_status",
        "target_test_colocation_status",
        "support_file_colocation_status",
        "environment_install_status",
        "failure_capture_status",
        "registry_merge_status",
        "registry_validation_status_after_merge",
        "reviewed_valid_candidate_count_after_run",
        "exact_blocker",
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
    current_audit = subprocess.run([sys.executable, "scripts/controllergate_audit.py", "--protocol", "current"], cwd=str(REPO_ROOT), text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if current_audit.returncode != 0:
        errors.append("current protocol audit failed")
    current_dry_run = subprocess.run([sys.executable, "scripts/controllergate_run.py", "--protocol", "current", "--dry-run"], cwd=str(REPO_ROOT), text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if current_dry_run.returncode != 0:
        errors.append("current protocol dry-run failed")
    if errors:
        print("v2.28 audit FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("v2.28 audit PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
