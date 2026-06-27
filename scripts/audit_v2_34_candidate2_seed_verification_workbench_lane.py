#!/usr/bin/env python3
"""Audit v2.34 candidate #2 seed verification workbench evidence."""

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
CAMPAIGN_ID = "v2_34_candidate2_seed_verification_workbench_lane"
OUTPUT_ROOT = REPO_ROOT / "outputs" / CAMPAIGN_ID
SEED_PATH = REPO_ROOT / "inputs" / "external_candidate_seed_draft_v2_34.json"
REGISTRY_PATH = REPO_ROOT / "configs" / "external_candidate_registry.json"
README_PATH = REPO_ROOT / "README.md"
ROADMAP_PATH = REPO_ROOT / "docs" / "non_ansible_capability_roadmap.md"
CAPABILITY_PLAN_PATH = REPO_ROOT / "docs" / "structural_repair_capability_plan.md"
RESOLUTION_DOC_PATH = REPO_ROOT / "docs" / ("controllergate_" + "t" + "ld" + "_resolution_map.md")
SHAREABLE_PATH = REPO_ROOT / "controllergate_v1_7_beta" / "reports" / "critic_review_package" / "shareable_summary.md"

BLOCKER = "blocked_no_valid_second_external_candidate_seed_provided"
FIRST_CANDIDATE = "py_bugger_issue_65"
EXPECTED_V234_SHA = "bd8feb5daf31412e72caf09b3a51237dc9a2317a401a9c24ee48604930eac192"
EXPECTED_V234_SIZE = 73749
EXPECTED_V234_ENTRIES = 38
EXPECTED_V234_MANIFEST_CHECKED = 24
EXPECTED_V234_RUN = 28302637324
EXPECTED_V234_ARTIFACT_ID = 7928414578
EXPECTED_V234_ARTIFACT_NAME = "v2_34_candidate2_seed_verification_workbench_lane_artifacts"
EXPECTED_V234_HEAD = "09b8f58f5c0a0c322cfc87616d483ac4dae16bff"
REJECTED_LEADS = {
    "darker_issue_112",
    "commit_check_issue_15",
    "pytest_fail_slow_issue_8",
    "reader_issue_355",
    "pytest_rerunfailures_issue_88",
    "autobahn_issue_1123",
}

REQUIRED_FILES = [
    "campaign_summary.md",
    "campaign_results.json",
    "v2_34_official_artifact_verification.json",
    "v2_33_artifact_ingest_verification.json",
    "artifact_repo_snapshot_comparison.json",
    "byte_custody_tooling_status_v2_34.json",
    "byte_custody_preflight_report_v2_34.json",
    "byte_custody_manifest_fix_report_v2_34.json",
    "byte_custody_workflow_integration_report_v2_34.json",
    "seed_workbench_status_v2_34.json",
    "seed_workbench_schema_policy_v2_34.json",
    "seed_workbench_usage.md",
    "seed_workbench_rejected_prior_leads.json",
    "seed_workbench_candidate2_requirements.md",
    "seed_workbench_external_helper_prompt.md",
    "seed_presence_check_v2_34.json",
    "second_seed_registry_merge_report.json",
    "external_candidate_registry_validation_report_after_second_seed.json",
    "external_candidate_registry_status_after_second_seed.json",
    "matched_null_experiment_status_v2_34.json",
    "public_language_audit.json",
    "proof_obligations_ledger.json",
    "roadmap_carry_forward_check_v2_34.json",
    "resolution_depth_diagnostic_v2_34.json",
    "claim_boundary_v2_34.json",
    "SHA256SUMS.txt",
]

SEED_PRESENT_ONLY_FILES = [
    "second_seed_schema_validation.json",
    "second_seed_forbidden_source_guard.json",
    "second_seed_source_checkout_audit.json",
    "second_seed_buggy_tree_manifest.json",
    "second_seed_target_test_file_hashes.json",
    "second_seed_support_file_hashes.json",
    "second_seed_environment_file_hashes.json",
    "second_seed_command_manifest.json",
    "second_seed_environment_resolution_preflight.json",
    "second_seed_failure_capture_raw.log",
    "second_seed_failure_capture_normalized.txt",
    "second_seed_failure_capture_hash.json",
    "second_seed_semantic_failure_signature_manifest.json",
    "second_seed_registry_entry_candidate.json",
]


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


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
        errors.append(f"expected JSON object: {path.relative_to(REPO_ROOT).as_posix()}")
        return {}
    return value


def expect(condition: bool, errors: list[str], message: str) -> None:
    if not condition:
        errors.append(message)


def verify_manifest(errors: list[str]) -> tuple[int, set[str]]:
    manifest = OUTPUT_ROOT / "SHA256SUMS.txt"
    if not manifest.is_file():
        errors.append("missing v2.34 SHA256SUMS.txt")
        return 0, set()
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
        if rel.startswith("/") or "\\" in rel or any(part in {"", ".", ".."} for part in pure.parts):
            errors.append(f"SHA256SUMS.txt:{line_no}: unsafe path {rel}")
            continue
        path = OUTPUT_ROOT.joinpath(*pure.parts)
        seen.add(rel)
        if not path.is_file():
            errors.append(f"SHA256SUMS.txt:{line_no}: missing file {rel}")
            continue
        if sha256_path(path) != expected:
            errors.append(f"SHA256SUMS.txt:{line_no}: hash mismatch {rel}")
        checked += 1
    expected_files = {
        path.relative_to(OUTPUT_ROOT).as_posix()
        for path in OUTPUT_ROOT.rglob("*")
        if path.is_file() and path.name != "SHA256SUMS.txt"
    }
    for rel in sorted(expected_files - seen):
        errors.append(f"manifest missing {rel}")
    for rel in sorted(seen - expected_files):
        errors.append(f"manifest contains extra {rel}")
    return checked, seen


def run_python(args: list[str], errors: list[str], label: str, timeout: int = 900) -> None:
    result = subprocess.run(
        [sys.executable, *args],
        cwd=str(REPO_ROOT),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        check=False,
    )
    if result.returncode != 0:
        tail = "\n".join((result.stdout + "\n" + result.stderr).splitlines()[-40:])
        errors.append(f"{label} failed\n{tail}")


def section_present(path: Path, heading: str) -> bool:
    return path.is_file() and f"## {heading}" in path.read_text(encoding="utf-8")


def audit_gitattributes(errors: list[str]) -> None:
    path = REPO_ROOT / ".gitattributes"
    expect(path.is_file(), errors, ".gitattributes missing")
    text = path.read_text(encoding="utf-8") if path.is_file() else ""
    for rule in [
        "*.py text eol=lf",
        "*.json text eol=lf",
        "*.md text eol=lf",
        "*.yml text eol=lf",
        "*.yaml text eol=lf",
        "*.txt text eol=lf",
        "*.zip binary",
        "*.tar binary",
        "outputs/v2_34_candidate2_seed_verification_workbench_lane/** text eol=lf",
    ]:
        expect(rule in text, errors, f".gitattributes missing rule {rule}")


def audit_proof_ledger(ledger: dict[str, Any], errors: list[str]) -> None:
    expect(ledger.get("status") == "PASS", errors, "proof ledger status mismatch")
    entries = ledger.get("entries")
    expect(isinstance(entries, list) and len(entries) >= 8, errors, "proof ledger entries missing")
    if not isinstance(entries, list):
        return
    previous = "0" * 64
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            errors.append(f"proof ledger entry {index} invalid")
            return
        expect(entry.get("index") == index, errors, f"proof ledger index mismatch at {index}")
        expect(entry.get("previous_entry_hash") == previous, errors, f"proof ledger previous hash mismatch at {index}")
        recorded = entry.get("entry_hash")
        payload = {key: value for key, value in entry.items() if key != "entry_hash"}
        computed = sha256_text(json.dumps(payload, sort_keys=True))
        expect(recorded == computed, errors, f"proof ledger hash mismatch at {index}")
        previous = str(recorded)
    expect(ledger.get("head_hash") == previous, errors, "proof ledger head hash mismatch")


def audit_outputs(errors: list[str], manifest_entries: set[str]) -> None:
    for rel in REQUIRED_FILES:
        expect((OUTPUT_ROOT / rel).is_file(), errors, f"missing required output {rel}")
        if rel != "SHA256SUMS.txt":
            expect(rel in manifest_entries, errors, f"required output missing from manifest {rel}")

    seed_present = SEED_PATH.is_file()
    if not seed_present:
        for rel in SEED_PRESENT_ONLY_FILES:
            expect(not (OUTPUT_ROOT / rel).exists(), errors, f"seed-present-only output exists while seed absent: {rel}")

    results = load_json(OUTPUT_ROOT / "campaign_results.json", errors)
    official = load_json(OUTPUT_ROOT / "v2_34_official_artifact_verification.json", errors)
    v233 = load_json(OUTPUT_ROOT / "v2_33_artifact_ingest_verification.json", errors)
    tooling = load_json(OUTPUT_ROOT / "byte_custody_tooling_status_v2_34.json", errors)
    preflight = load_json(OUTPUT_ROOT / "byte_custody_preflight_report_v2_34.json", errors)
    fix_report = load_json(OUTPUT_ROOT / "byte_custody_manifest_fix_report_v2_34.json", errors)
    workflow = load_json(OUTPUT_ROOT / "byte_custody_workflow_integration_report_v2_34.json", errors)
    workbench = load_json(OUTPUT_ROOT / "seed_workbench_status_v2_34.json", errors)
    schema = load_json(OUTPUT_ROOT / "seed_workbench_schema_policy_v2_34.json", errors)
    rejected = load_json(OUTPUT_ROOT / "seed_workbench_rejected_prior_leads.json", errors)
    presence = load_json(OUTPUT_ROOT / "seed_presence_check_v2_34.json", errors)
    merge = load_json(OUTPUT_ROOT / "second_seed_registry_merge_report.json", errors)
    registry_report = load_json(OUTPUT_ROOT / "external_candidate_registry_validation_report_after_second_seed.json", errors)
    registry_status = load_json(OUTPUT_ROOT / "external_candidate_registry_status_after_second_seed.json", errors)
    experiment = load_json(OUTPUT_ROOT / "matched_null_experiment_status_v2_34.json", errors)
    public_language = load_json(OUTPUT_ROOT / "public_language_audit.json", errors)
    ledger = load_json(OUTPUT_ROOT / "proof_obligations_ledger.json", errors)
    roadmap = load_json(OUTPUT_ROOT / "roadmap_carry_forward_check_v2_34.json", errors)
    resolution = load_json(OUTPUT_ROOT / "resolution_depth_diagnostic_v2_34.json", errors)
    claim = load_json(OUTPUT_ROOT / "claim_boundary_v2_34.json", errors)

    expect(official.get("status") == "PASS", errors, "v2.34 official artifact verification not PASS")
    expect(official.get("manual_artifact_boundary") == "PASS", errors, "v2.34 manual artifact boundary not PASS")
    expect(official.get("downloaded_by_codex") is False, errors, "v2.34 artifact must be manually provided")
    expect(official.get("local_artifact_path_outside_git") is True, errors, "v2.34 artifact path must be outside Git worktree")
    expect(official.get("artifact_name") == EXPECTED_V234_ARTIFACT_NAME, errors, "v2.34 artifact name mismatch")
    expect(official.get("workflow_run_id") == EXPECTED_V234_RUN, errors, "v2.34 workflow run mismatch")
    expect(official.get("artifact_id") == EXPECTED_V234_ARTIFACT_ID, errors, "v2.34 artifact ID mismatch")
    expect(official.get("head_sha") == EXPECTED_V234_HEAD, errors, "v2.34 artifact head SHA mismatch")
    expect(official.get("zip_size_bytes") == EXPECTED_V234_SIZE, errors, "v2.34 artifact size mismatch")
    expect(official.get("zip_sha256") == EXPECTED_V234_SHA, errors, "v2.34 artifact SHA mismatch")
    expect(official.get("entry_count") == EXPECTED_V234_ENTRIES, errors, "v2.34 artifact entry count mismatch")
    expect(official.get("safe_path_status") == "PASS", errors, "v2.34 artifact safe path status mismatch")
    expect(official.get("unsafe_path_count") == 0, errors, "v2.34 artifact unsafe path count mismatch")
    expect(official.get("duplicate_path_count") == 0, errors, "v2.34 artifact duplicate path count mismatch")
    expect(official.get("internal_manifest_checked") == EXPECTED_V234_MANIFEST_CHECKED, errors, "v2.34 internal manifest count mismatch")
    expect(official.get("internal_manifest_missing") == 0, errors, "v2.34 internal manifest missing entries")
    expect(official.get("internal_manifest_malformed") == 0, errors, "v2.34 internal manifest malformed entries")
    expect(official.get("internal_manifest_failures") == 0, errors, "v2.34 internal manifest hash failures")
    expect(official.get("internal_manifest_status") == "PASS", errors, "v2.34 internal manifest status mismatch")
    expect(official.get("output_manifest_coverage") == "PASS", errors, "v2.34 output manifest coverage mismatch")
    expect(official.get("non_archive_outputs_ingested_count") == EXPECTED_V234_MANIFEST_CHECKED, errors, "v2.34 ingested output count mismatch")
    official_cf = official.get("carry_forward") if isinstance(official.get("carry_forward"), dict) else {}
    expect(official_cf.get("v2_34_audit_status") == "PASS", errors, "v2.34 official audit carry-forward not PASS")
    expect(official_cf.get("regression_audit_status") == "PASS", errors, "v2.34 official regression carry-forward not PASS")
    expect(official_cf.get("public_language_audit_status") == "PASS", errors, "v2.34 official public language carry-forward not PASS")
    expect(official_cf.get("byte_custody_tooling_status") == "PASS", errors, "v2.34 official byte-custody tooling not PASS")
    expect(official_cf.get("byte_custody_preflight_status") == "PASS", errors, "v2.34 official byte-custody preflight not PASS")
    expect(official_cf.get("seed_workbench_status") == "PASS", errors, "v2.34 official seed workbench not PASS")
    expect(official_cf.get("invalid_lead_rejection_carry_forward_status") == "PASS", errors, "v2.34 official lead rejection not PASS")
    expect(official_cf.get("rejected_prior_lead_count") == 6, errors, "v2.34 official rejected lead count mismatch")
    expect(official_cf.get("valid_seed_present") is False, errors, "v2.34 official valid seed presence mismatch")
    expect(official_cf.get("valid_seed_verification_status") == BLOCKER, errors, "v2.34 official seed verification blocker mismatch")
    expect(official_cf.get("seed_registry_merge_status") == "not_run_no_valid_seed", errors, "v2.34 official seed merge mismatch")
    expect(official_cf.get("reviewed_valid_candidate_count_after_run") == 1, errors, "v2.34 official reviewed count mismatch")
    expect(official_cf.get("matched_null_experiment_attempted") is False, errors, "v2.34 official matched-null attempted mismatch")
    expect(official_cf.get("patch_generated") is False, errors, "v2.34 official patch flag mismatch")
    expect(official_cf.get("full_scoring") == "NOT_RUN/disallowed", errors, "v2.34 official full scoring mismatch")
    expect(official_cf.get("memory_lift_status") == "undemonstrated", errors, "v2.34 official memory-lift mismatch")
    expect(official_cf.get("self_maintaining_software_status") == "false/not_demonstrated", errors, "v2.34 official self-maintaining mismatch")
    expect(official_cf.get("v2_35_automated_acquisition_recommendation_carry_forward_status") == "PASS", errors, "v2.35 recommendation carry-forward not PASS")

    expect(v233.get("status") == "PASS", errors, "v2.33 official ingest carry-forward not PASS")
    expect(v233.get("manual_artifact_boundary") == "PASS", errors, "v2.33 manual artifact boundary not PASS")
    expect(v233.get("downloaded_by_codex") is False, errors, "v2.33 artifact must remain manually provided")
    expect(tooling.get("status") == "PASS", errors, "byte-custody tooling not PASS")
    expect(tooling.get("claim_boundary") == "tooling_only_no_scientific_result_change", errors, "byte-custody claim boundary mismatch")
    expect(preflight.get("status") == "PASS", errors, "byte-custody preflight report not PASS")
    expect(preflight.get("mismatch_count") == 0, errors, "byte-custody preflight mismatches present")
    expect(fix_report.get("status") == "PASS", errors, "byte-custody manifest fix report not PASS")
    expect(fix_report.get("semantic_or_scientific_record_changed") is False, errors, "byte-custody report changed scientific record")
    expect(workflow.get("pre_audit_command") == "python scripts/byte_custody_preflight.py", errors, "workflow preflight command mismatch")
    expect(workflow.get("blocker_on_failure") == "byte_custody_preflight_failed", errors, "workflow preflight blocker mismatch")

    expect(workbench.get("status") == "PASS", errors, "seed workbench status not PASS")
    expect(workbench.get("rejected_prior_lead_count") == 6, errors, "rejected prior lead count mismatch")
    expect(workbench.get("live_issue_search_attempted") is False, errors, "live issue search must not be attempted")
    expect(workbench.get("candidate2_selected") is False, errors, "candidate #2 must not be selected without valid seed")
    expect(workbench.get("exact_blocker") == BLOCKER, errors, "workbench blocker mismatch")
    expect(schema.get("commit_sha_rule") == "exactly_40_lowercase_hex_characters", errors, "seed schema commit rule mismatch")
    expect(FIRST_CANDIDATE in schema.get("forbidden_candidate_ids", []), errors, "first candidate must be forbidden as candidate #2")

    rejected_ids = {
        item.get("lead_id")
        for item in rejected.get("rejected_leads", [])
        if isinstance(item, dict)
    }
    expect(rejected.get("lead_count") == 6, errors, "rejected lead count mismatch")
    expect(rejected_ids == REJECTED_LEADS, errors, "rejected lead identities mismatch")
    expect(rejected.get("leads_are_candidates") is False, errors, "rejected leads must not be candidates")
    for item in rejected.get("rejected_leads", []):
        if isinstance(item, dict):
            expect(item.get("registry_merged") is False, errors, f"rejected lead merged: {item.get('lead_id')}")
            expect(item.get("candidate_selected") is False, errors, f"rejected lead selected: {item.get('lead_id')}")

    expect(presence.get("seed_present") is False, errors, "official v2.34 run expects no valid seed")
    expect(presence.get("external_clone_attempted") is False, errors, "external clone must not run with absent seed")
    expect(presence.get("live_issue_search_attempted") is False, errors, "live issue search must not run")
    expect(merge.get("status") == "not_run_no_valid_seed", errors, "seed registry merge status mismatch")
    expect(merge.get("registry_updated") is False, errors, "registry must not update without valid seed")
    expect(registry_report.get("registry_validation_status") == "PASS", errors, "embedded registry validation not PASS")
    expect(registry_status.get("registry_candidate_count_after_run") == 1, errors, "registry candidate count must remain 1")
    expect(registry_status.get("reviewed_valid_candidate_count_after_run") == 1, errors, "reviewed candidate count must remain 1")
    expect(registry_status.get("second_seed_merged") is False, errors, "second seed must not merge")

    expect(experiment.get("matched_null_experiment_attempted") is False, errors, "matched-null experiment must not run")
    expect(experiment.get("repair_attempted") is False, errors, "repair must not run")
    expect(experiment.get("patch_generated") is False, errors, "patch must not be generated")
    expect(experiment.get("s_engine_invoked") is False, errors, "S-Engine must not be invoked")
    expect(public_language.get("status") == "PASS", errors, "public language audit not PASS")
    expect(public_language.get("exact_match_count") == 0, errors, "public language exact-match count mismatch")
    audit_proof_ledger(ledger, errors)
    expect(roadmap.get("status") == "PASS", errors, "roadmap carry-forward not PASS")
    expect(resolution.get("status") == "PASS", errors, "resolution diagnostic not PASS")
    expect(claim.get("current_protocol_version") == "v2.13", errors, "current protocol changed")
    expect(claim.get("v2_34_promoted_to_current") is False, errors, "v2.34 must not be promoted")
    expect(claim.get("full_scoring") == "NOT_RUN/disallowed", errors, "full scoring mismatch")
    expect(claim.get("memory_lift_status") == "undemonstrated", errors, "memory-lift claim mismatch")
    expect(claim.get("self_maintaining_software_status") == "false/not_demonstrated", errors, "self-maintaining claim mismatch")
    expect(claim.get("repair_attempted") is False, errors, "claim boundary repair flag mismatch")
    expect(claim.get("patch_generated") is False, errors, "claim boundary patch flag mismatch")
    expect(claim.get("matched_null_experiment_attempted") is False, errors, "claim boundary experiment flag mismatch")
    expect(claim.get("exact_blocker") == BLOCKER, errors, "claim boundary blocker mismatch")

    expect(results.get("status") == "blocked", errors, "campaign must be blocked without valid seed")
    expect(results.get("v2_33_official_ingest_status") == "PASS", errors, "campaign v2.33 ingest status mismatch")
    expect(results.get("byte_custody_tooling_status") == "PASS", errors, "campaign byte-custody tooling mismatch")
    expect(results.get("byte_custody_preflight_status") == "PASS", errors, "campaign preflight status mismatch")
    expect(results.get("valid_seed_present") is False, errors, "campaign valid seed presence mismatch")
    expect(results.get("valid_seed_verification_status") == BLOCKER, errors, "campaign seed verification blocker mismatch")
    expect(results.get("seed_registry_merge_status") == "not_run_no_valid_seed", errors, "campaign seed merge mismatch")
    expect(results.get("reviewed_valid_candidate_count_after_run") == 1, errors, "campaign reviewed count mismatch")
    expect(results.get("matched_null_experiment_attempted") is False, errors, "campaign matched-null attempted mismatch")
    expect(results.get("patch_generated") is False, errors, "campaign patch flag mismatch")
    expect(results.get("full_scoring") == "NOT_RUN/disallowed", errors, "campaign full scoring mismatch")
    expect(results.get("memory_lift_status") == "undemonstrated", errors, "campaign memory lift mismatch")
    expect(results.get("self_maintaining_software_status") == "false/not_demonstrated", errors, "campaign self-maintaining mismatch")
    expect(results.get("current_protocol_version") == "v2.13", errors, "campaign current protocol mismatch")
    expect(results.get("exact_blocker") == BLOCKER, errors, "campaign blocker mismatch")


def audit_public_updates(errors: list[str]) -> None:
    expect(section_present(README_PATH, "v2.34 candidate #2 seed workbench and byte-custody status"), errors, "README v2.34 section missing")
    expect(section_present(ROADMAP_PATH, "v2.34 Candidate #2 Seed Verification Workbench"), errors, "roadmap v2.34 section missing")
    expect(section_present(CAPABILITY_PLAN_PATH, "v2.34 candidate #2 workbench status"), errors, "capability plan v2.34 section missing")
    expect(section_present(RESOLUTION_DOC_PATH, "v2.34 candidate #2 workbench status"), errors, "resolution doc v2.34 section missing")
    expect(section_present(SHAREABLE_PATH, "v2.34 Candidate #2 Workbench and Byte-Custody Status"), errors, "shareable v2.34 section missing")
    expect((REPO_ROOT / "docs" / "byte_custody_preflight.md").is_file(), errors, "byte-custody preflight doc missing")


def audit_registry(errors: list[str]) -> None:
    report = registry_validator.validate_registry()
    expect(report.get("registry_validation_status") == "PASS", errors, "fresh registry validation failed")
    expect(report.get("candidate_count") == 1, errors, "v2.34 no-seed run must not add candidate #2")
    expect(report.get("valid_reviewed_candidate_count") == 1, errors, "reviewed candidate count must remain 1")
    registry = load_json(REGISTRY_PATH, errors)
    candidates = registry.get("candidates")
    if isinstance(candidates, list):
        ids = [item.get("candidate_id") for item in candidates if isinstance(item, dict)]
        expect(ids == [FIRST_CANDIDATE], errors, "registry must contain only the first reviewed candidate")


def main() -> int:
    errors: list[str] = []
    for rel in REQUIRED_FILES:
        if not (OUTPUT_ROOT / rel).exists():
            errors.append(f"missing required file {rel}")
    checked, entries = verify_manifest(errors)
    audit_gitattributes(errors)
    audit_outputs(errors, entries)
    audit_public_updates(errors)
    audit_registry(errors)
    expect((REPO_ROOT / "scripts" / "byte_custody_preflight.py").is_file(), errors, "byte_custody_preflight.py missing")
    expect((REPO_ROOT / "scripts" / "write_sha256_manifest.py").is_file(), errors, "write_sha256_manifest.py missing")
    expect((REPO_ROOT / "scripts" / "verify_external_candidate_seed.py").is_file(), errors, "verify_external_candidate_seed.py missing")
    run_python(["scripts/byte_custody_preflight.py"], errors, "byte-custody preflight")
    run_python(["scripts/audit_v2_33_candidate2_matched_null_memory_repair_lane.py"], errors, "v2.33 nested regression audit", timeout=1200)

    if errors:
        print("v2.34 audit FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("v2.34 audit PASS")
    print(f"checked_manifest_entries={checked}")
    print("current_protocol_version=v2.13")
    print(f"exact_blocker={BLOCKER}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
