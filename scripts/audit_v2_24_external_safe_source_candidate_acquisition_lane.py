#!/usr/bin/env python3
"""Audit v2.24 external safe-source candidate registry precheck evidence."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path, PurePosixPath
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_ROOT = REPO_ROOT / "outputs" / "v2_24_external_safe_source_candidate_acquisition_lane"
V223_ROOT = REPO_ROOT / "outputs" / "v2_23_non_ansible_candidate_transition_lane"
REGISTRY_PATH = REPO_ROOT / "configs" / "external_candidate_registry.json"
CAMPAIGN_ID = "v2_24_external_safe_source_candidate_acquisition_lane"
BLOCKER = "blocked_external_candidate_registry_missing_or_invalid"
NEXT_STEP = "create_reviewed_external_candidate_registry_entry"
NEXT_LANE = "v2.25 External Candidate Registry Construction Lane"
NORMALIZATION_POLICY = "strip_timestamps_absolute_paths_and_ansi"
OFFICIAL_VERIFICATION_FILE = "v2_24_official_artifact_verification.json"

REQUIRED_FILES = [
    "campaign_summary.md",
    "campaign_results.json",
    "v2_23_official_ingest_reference.json",
    "external_candidate_registry_precheck.json",
    "external_candidate_registry_schema_audit.json",
    "selected_external_candidate_bug_signature_manifest.json",
    "selected_external_candidate_failure_capture_log.txt",
    "selected_external_candidate_failure_capture_hash.json",
    "selected_external_candidate_failure_signature_comparison.json",
    "v2_25_external_candidate_registry_construction_recommendation.json",
    "claim_boundary_v2_24.json",
    "public_language_audit.json",
    OFFICIAL_VERIFICATION_FILE,
    "SHA256SUMS.txt",
]

FORBIDDEN_OUTPUTS = {
    "selected_external_candidate_executed_scope_manifest.json",
    "selected_external_candidate_executed_scope_trace.log",
    "selected_external_candidate_executed_file_hashes.csv",
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
        errors.append(f"missing JSON: {path}")
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"invalid JSON {path}: {exc}")
        return {}
    if not isinstance(value, dict):
        errors.append(f"expected object: {path}")
        return {}
    return value


def expect(condition: bool, errors: list[str], message: str) -> None:
    if not condition:
        errors.append(message)


def verify_manifest(root: Path) -> tuple[list[str], int]:
    errors: list[str] = []
    manifest = root / "SHA256SUMS.txt"
    if not manifest.is_file():
        return [f"missing manifest: {manifest}"], 0
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


def audit_v223_boundary(errors: list[str]) -> None:
    verification = load_json(V223_ROOT / "v2_23_official_artifact_verification.json", errors)
    expect(verification.get("status") == "PASS", errors, "v2.23 official artifact verification is not PASS")
    expect(
        verification.get("zip_sha256") == "fbbed9f699822b16733a77a8c4b32c960a5ef3fed527059737b645802b0116ca",
        errors,
        "v2.23 official artifact digest mismatch",
    )
    audit = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "audit_v2_23_non_ansible_candidate_transition_lane.py")],
        cwd=str(REPO_ROOT),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if audit.returncode != 0:
        errors.append("v2.23 audit did not pass from v2.24 audit")


def audit_official_verification(verification: dict[str, Any], errors: list[str]) -> None:
    expect(verification.get("status") == "PASS", errors, "v2.24 official artifact verification is not PASS")
    expect(
        verification.get("artifact_name") == "v2_24_external_safe_source_candidate_acquisition_lane_artifacts",
        errors,
        "v2.24 official artifact name mismatch",
    )
    expect(verification.get("workflow_run_id") == 28212746325, errors, "v2.24 workflow run ID mismatch")
    expect(verification.get("artifact_id") == 7895535773, errors, "v2.24 artifact ID mismatch")
    expect(verification.get("zip_size") == 51049, errors, "v2.24 artifact size mismatch")
    expect(
        verification.get("zip_sha256") == "1801c197bb032c415dea4a33a9208042b0377d069e95fc4cde1ab4e0f2e7db8d",
        errors,
        "v2.24 artifact digest mismatch",
    )
    expect(verification.get("entry_count") == 20, errors, "v2.24 ZIP entry count mismatch")
    expect(verification.get("safe_paths") is True, errors, "v2.24 ZIP safe-path check did not pass")
    expect(verification.get("unsafe_path_count") == 0, errors, "v2.24 ZIP unsafe paths present")
    expect(verification.get("duplicate_path_count") == 0, errors, "v2.24 ZIP duplicate paths present")
    expect(verification.get("internal_manifest_checked_count") == 12, errors, "v2.24 internal manifest count mismatch")
    expect(verification.get("internal_manifest_missing_count") == 0, errors, "v2.24 internal manifest missing entries")
    expect(verification.get("internal_manifest_malformed_count") == 0, errors, "v2.24 internal manifest malformed entries")
    expect(verification.get("internal_manifest_failure_count") == 0, errors, "v2.24 internal manifest failures")
    coverage = verification.get("output_manifest_coverage") or {}
    expect(coverage.get("status") == "PASS", errors, "v2.24 output manifest coverage did not PASS")
    expect(verification.get("local_artifact_path_outside_git") is True, errors, "v2.24 local artifact path is not outside git")
    expect(verification.get("non_tar_non_zip_ingested_file_count") == 13, errors, "v2.24 ingested file count mismatch")
    expect(verification.get("registry_blocker_carry_forward_status") == "PASS", errors, "v2.24 registry blocker carry-forward mismatch")
    expect(verification.get("v2_25_recommendation_carry_forward_status") == "PASS", errors, "v2.25 recommendation carry-forward mismatch")


def audit_outputs(root: Path, errors: list[str]) -> None:
    for rel in REQUIRED_FILES:
        expect((root / rel).is_file(), errors, f"missing required output: {rel}")
    for rel in FORBIDDEN_OUTPUTS:
        expect(not (root / rel).exists(), errors, f"unexpected repair/trace output: {rel}")
    manifest_errors, checked = verify_manifest(root)
    errors.extend(manifest_errors)
    expect(checked >= len(REQUIRED_FILES) - 1, errors, "manifest checked fewer files than required")

    registry = load_json(REGISTRY_PATH, errors)
    results = load_json(root / "campaign_results.json", errors)
    v223_ref = load_json(root / "v2_23_official_ingest_reference.json", errors)
    precheck = load_json(root / "external_candidate_registry_precheck.json", errors)
    schema = load_json(root / "external_candidate_registry_schema_audit.json", errors)
    manifest = load_json(root / "selected_external_candidate_bug_signature_manifest.json", errors)
    capture_hash = load_json(root / "selected_external_candidate_failure_capture_hash.json", errors)
    comparison = load_json(root / "selected_external_candidate_failure_signature_comparison.json", errors)
    recommendation = load_json(root / "v2_25_external_candidate_registry_construction_recommendation.json", errors)
    claim = load_json(root / "claim_boundary_v2_24.json", errors)
    public_language = load_json(root / "public_language_audit.json", errors)
    official = load_json(root / OFFICIAL_VERIFICATION_FILE, errors)

    expect(REGISTRY_PATH.is_file(), errors, "external candidate registry config missing")
    registry_schema_version = registry.get("schema_version")
    expect(registry_schema_version in {"v2.24", "v2.25"}, errors, "registry schema version mismatch")
    if registry_schema_version == "v2.24":
        expect(registry.get("document_type") == "external_candidate_registry", errors, "registry document type mismatch")
        expect(registry.get("current_protocol_version") == "v2.13", errors, "registry current protocol mismatch")
        expect(isinstance(registry.get("entries"), list), errors, "registry entries is not a list")
        entries = registry.get("entries") if isinstance(registry.get("entries"), list) else []
    else:
        expect(isinstance(registry.get("review_policy"), dict), errors, "v2.25 registry review policy missing")
        expect(isinstance(registry.get("candidates"), list), errors, "v2.25 registry candidates is not a list")
        entries = []
    valid_count = schema.get("valid_entry_count")
    expect(results.get("campaign_id") == CAMPAIGN_ID, errors, "campaign ID mismatch")
    expect(results.get("status") == "PASS_WITH_EXTERNAL_CANDIDATE_REGISTRY_BLOCK", errors, "campaign status mismatch")
    expect(results.get("v2_23_official_ingest_verified") is True, errors, "v2.23 official ingest not verified")
    expect(v223_ref.get("status") == "PASS", errors, "v2.23 ingest reference did not PASS")
    expect(precheck.get("status") == "BLOCK", errors, "registry precheck did not BLOCK")
    expect(precheck.get("blocker") == BLOCKER, errors, "registry precheck blocker mismatch")
    expect(precheck.get("candidate_pool_built_from_valid_registry_entries_only") is True, errors, "candidate pool source rule missing")
    expect(precheck.get("candidate_pool_size") == 0, errors, "candidate pool unexpectedly non-empty")
    expect(precheck.get("clone_attempted") is False, errors, "external clone attempted despite registry block")
    expect(precheck.get("live_issue_selected_directly") is False, errors, "candidate selected directly from live issue")
    expect(precheck.get("s_engine_invoked") is False, errors, "S-Engine invoked before registry precheck passed")
    expect(precheck.get("patch_generation_attempted") is False, errors, "patch generation attempted before registry precheck passed")
    expect(precheck.get("recommendation") == NEXT_STEP, errors, "registry precheck next step mismatch")
    expect(schema.get("registry_exists") is True, errors, "schema audit says registry missing")
    if registry_schema_version == "v2.24":
        expect(schema.get("registry_sha256") == sha256_path(REGISTRY_PATH), errors, "registry SHA mismatch")
    expect(schema.get("entry_count") == len(entries), errors, "registry entry count mismatch")
    expect(valid_count == 0, errors, "v2.24 expected zero valid registry entries")
    expect(schema.get("status") == "PASS", errors, "schema audit should PASS for well-formed empty registry")

    expect(manifest.get("status") == "not_applicable_registry_blocked", errors, "bug signature manifest status mismatch")
    expect(manifest.get("selected_candidate") is None, errors, "selected candidate present despite registry block")
    expect(manifest.get("selected_candidate_has_reviewed_registry_entry") is False, errors, "selected candidate claims reviewed entry")
    expect(manifest.get("expected_failure_signature_log_hash") is None, errors, "unexpected expected failure hash")
    expect(manifest.get("target_test_files_verified_in_buggy_tree") is False, errors, "target test verification ran despite registry block")
    expect((root / "selected_external_candidate_failure_capture_log.txt").is_file(), errors, "failure capture log missing")
    expect(capture_hash.get("status") == "not_run_registry_blocked", errors, "failure capture hash status mismatch")
    expect(capture_hash.get("raw_stdout_stderr_captured") is False, errors, "stdout/stderr captured despite registry block")
    expect(capture_hash.get("normalized_log_sha256") is None, errors, "normalized failure hash unexpectedly present")
    expect(capture_hash.get("normalization_policy") == "strip_timestamps_absolute_paths_and_ansi", errors, "normalization policy mismatch")
    expect(capture_hash.get("meaningful_failure_content_removed_by_normalization") is False, errors, "normalization removed meaningful content")
    expect(comparison.get("status") == "not_run_registry_blocked", errors, "failure signature comparison status mismatch")
    expect(comparison.get("signature_match") is False, errors, "signature match claimed despite no capture")
    expect(comparison.get("pre_repair_environmental_pass_detected") is False, errors, "pre-repair environmental pass detected")
    expect(comparison.get("patch_generation_authorized") is False, errors, "patch generation authorized without signature verification")

    expect(recommendation.get("recommended_next_lane") == NEXT_LANE, errors, "next lane recommendation mismatch")
    expect(recommendation.get("smallest_next_step") == NEXT_STEP, errors, "smallest next step mismatch")
    expect(recommendation.get("do_not_begin_v2_25_in_this_lane") is True, errors, "v2.25 boundary missing")

    for key in [
        "external_clone_attempted",
        "s_engine_invoked",
        "executed_scope_manifest_run",
        "patch_generated",
        "patch_authorized",
        "patch_attempted",
    ]:
        expect(claim.get(key) is False, errors, f"forbidden action/claim true: {key}")
    expect(claim.get("current_protocol_version") == "v2.13", errors, "current protocol changed")
    expect(claim.get("v2_24_promoted_to_current") is False, errors, "v2.24 promoted to current")
    expect(claim.get("full_scoring") == "NOT_RUN", errors, "full scoring changed")
    expect(claim.get("full_scoring_allowed") is False, errors, "full scoring allowed")
    expect(claim.get("memory_lift_status") == "undemonstrated", errors, "memory lift claimed")
    expect(claim.get("self_maintaining_software_status") == "false/not_demonstrated", errors, "self-maintaining claim changed")
    expect(claim.get("final_non_ansible_positive_memory_count") == 0, errors, "non-Ansible positive-memory count changed")
    expect(public_language.get("status") == "PASS", errors, "public language audit did not PASS")

    expect(results.get("external_candidate_registry_valid_entry_count") == 0, errors, "results valid-entry count mismatch")
    expect(results.get("exact_blocker") == BLOCKER, errors, "exact blocker mismatch")
    expect(results.get("recommendation") == NEXT_STEP, errors, "recommendation mismatch")
    expect(results.get("recommended_next_lane") == NEXT_LANE, errors, "recommended next lane mismatch")
    expect(results.get("candidate_selection_status") == "not_run_no_valid_registry_entries", errors, "candidate selection status mismatch")
    expect(results.get("selected_candidate") is None, errors, "candidate selected despite registry block")
    expect(results.get("live_issue_selected_directly") is False, errors, "live issue selected directly")
    expect(results.get("external_clone_attempted") is False, errors, "external clone attempted")
    expect(results.get("failure_capture_status") == "not_run_registry_blocked", errors, "failure capture status mismatch")
    expect(results.get("failure_signature_comparison_status") == "not_run_registry_blocked", errors, "failure signature comparison status mismatch")
    expect(results.get("s_engine_invoked") is False, errors, "S-Engine invoked")
    expect(results.get("dependency_recovery_run") is False, errors, "dependency recovery ran")
    expect(results.get("executed_scope_manifest_status") == "not_run_registry_blocked", errors, "executed scope manifest ran before signature verification")
    expect(results.get("patch_generated") is False, errors, "patch generated")
    expect(results.get("patch_authorized") is False, errors, "patch authorized")
    expect(results.get("patch_attempted") is False, errors, "patch attempted")
    expect(results.get("full_scoring") == "NOT_RUN", errors, "results full scoring changed")
    expect(results.get("full_scoring_allowed") is False, errors, "results full scoring allowed")
    expect(results.get("memory_lift_status") == "undemonstrated", errors, "results memory lift claimed")
    expect(results.get("self_maintaining_software_status") == "false/not_demonstrated", errors, "results self-maintaining claim changed")
    expect(results.get("current_protocol_version") == "v2.13", errors, "results current protocol changed")

    audit_v223_boundary(errors)
    audit_official_verification(official, errors)

    print(f"v2.24 manifest entries checked: {checked}")
    for key in [
        "external_candidate_registry_precheck_status",
        "external_candidate_registry_valid_entry_count",
        "candidate_selection_status",
        "failure_capture_status",
        "patch_generated",
        "full_scoring",
        "memory_lift_status",
        "self_maintaining_software_status",
        "current_protocol_version",
        "exact_blocker",
        "recommendation",
        "recommended_next_lane",
    ]:
        print(f"{key}={results.get(key)}")


def main() -> int:
    errors: list[str] = []
    if not OUTPUT_ROOT.is_dir():
        errors.append(f"missing output root: {OUTPUT_ROOT}")
    else:
        audit_outputs(OUTPUT_ROOT, errors)
    if errors:
        print("v2.24 audit FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("v2.24 audit PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
