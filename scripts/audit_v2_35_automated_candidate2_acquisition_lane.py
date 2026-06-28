#!/usr/bin/env python3
"""Audit v2.35 automated candidate #2 acquisition lane evidence."""

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
CAMPAIGN_ID = "v2_35_automated_candidate2_acquisition_lane"
OUTPUT_ROOT = REPO_ROOT / "outputs" / CAMPAIGN_ID
REGISTRY_PATH = REPO_ROOT / "configs" / "external_candidate_registry.json"
LEAD_POOL_PATH = REPO_ROOT / "inputs" / "candidate2_acquisition_lead_pool_v2_35.json"
README_PATH = REPO_ROOT / "README.md"
ROADMAP_PATH = REPO_ROOT / "docs" / "non_ansible_capability_roadmap.md"
CAPABILITY_PLAN_PATH = REPO_ROOT / "docs" / "structural_repair_capability_plan.md"
RESOLUTION_DOC_PATH = REPO_ROOT / "docs" / ("controllergate_" + "t" + "ld" + "_resolution_map.md")
SHAREABLE_PATH = REPO_ROOT / "controllergate_v1_7_beta" / "reports" / "critic_review_package" / "shareable_summary.md"
ACQUISITION_DOC_PATH = REPO_ROOT / "docs" / "candidate2_acquisition_workbench.md"

BLOCKER = "blocked_no_verified_candidate2_seed_acquired"
FIRST_CANDIDATE = "py_bugger_issue_65"
OFFICIAL_ARTIFACT_SHA256 = "f0fc373f727f2e142255a1392d107a00e997961889dc4d113141bceb298f6f7b"
OFFICIAL_ARTIFACT_SIZE = 88330
OFFICIAL_ARTIFACT_ENTRY_COUNT = 41
OFFICIAL_ARTIFACT_ID = 7930137915
OFFICIAL_WORKFLOW_RUN_ID = 28308169464

REQUIRED_FILES = [
    "campaign_summary.md",
    "campaign_results.json",
    "v2_35_official_artifact_verification.json",
    "v2_34_artifact_ingest_verification.json",
    "artifact_repo_snapshot_comparison.json",
    "byte_custody_preflight_report_v2_35.json",
    "acquisition_risk_temperature_policy_v2_35.json",
    "structural_complexity_filter_v2_35.json",
    "candidate2_acquisition_lead_pool_v2_35.json",
    "candidate2_acquisition_policy_v2_35.json",
    "candidate2_acquisition_budget_v2_35.json",
    "candidate2_metadata_probe_log.json",
    "candidate2_github_api_status.json",
    "candidate2_acquisition_attempt_log.json",
    "candidate2_lead_attempts.json",
    "candidate2_resolved_commit_attempts.json",
    "candidate2_rejection_ledger.json",
    "candidate2_registry_merge_report.json",
    "external_candidate_registry_validation_report_after_candidate2.json",
    "external_candidate_registry_status_after_candidate2.json",
    "matched_null_experiment_status_v2_35.json",
    "public_language_audit.json",
    "proof_obligations_ledger.json",
    "roadmap_carry_forward_check_v2_35.json",
    "resolution_depth_diagnostic_v2_35.json",
    "claim_boundary_v2_35.json",
    "SHA256SUMS.txt",
]

SEED_ONLY_FILES = [
    "candidate2_verified_seed_record.json",
    "candidate2_verified_seed_draft_v2_35.json",
    "candidate2_source_checkout_audit.json",
    "candidate2_buggy_tree_manifest.json",
    "candidate2_target_test_file_hashes.json",
    "candidate2_support_file_hashes.json",
    "candidate2_environment_file_hashes.json",
    "candidate2_command_manifest.json",
    "candidate2_environment_resolution_preflight.json",
    "candidate2_failure_capture_raw.log",
    "candidate2_failure_capture_normalized.txt",
    "candidate2_failure_capture_hash.json",
    "candidate2_semantic_failure_signature_manifest.json",
    "candidate2_registry_entry_candidate.json",
]

MATCHED_NULL_ONLY_FILES = [
    "matched_null_arm_a_memory_enabled_plan.json",
    "matched_null_arm_b_memory_disabled_plan.json",
    "matched_null_arm_a_results.json",
    "matched_null_arm_b_results.json",
    "matched_null_separation_score_result.json",
    "memory_lift_claim_evaluation.json",
    "telomeric_budget_policy.json",
    "telomeric_budget_trace_arm_a.json",
    "telomeric_budget_trace_arm_b.json",
    "micro_reversal_policy.json",
    "micro_reversal_trace_arm_a.json",
    "micro_reversal_trace_arm_b.json",
    "context_boundary_map_arm_a.json",
    "context_boundary_map_arm_b.json",
    "seed_constraint_revalidation_arm_a.json",
    "seed_constraint_revalidation_arm_b.json",
    "arm_a_patch.diff",
    "arm_a_patch_sha256.txt",
    "arm_b_patch.diff",
    "arm_b_patch_sha256.txt",
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
        errors.append("missing v2.35 SHA256SUMS.txt")
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


def run_python(args: list[str], errors: list[str], label: str, timeout: int = 1200) -> None:
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
    for rel in SEED_ONLY_FILES + MATCHED_NULL_ONLY_FILES:
        expect(not (OUTPUT_ROOT / rel).exists(), errors, f"conditional output must not exist without verified seed: {rel}")

    results = load_json(OUTPUT_ROOT / "campaign_results.json", errors)
    official = load_json(OUTPUT_ROOT / "v2_35_official_artifact_verification.json", errors)
    v234 = load_json(OUTPUT_ROOT / "v2_34_artifact_ingest_verification.json", errors)
    preflight = load_json(OUTPUT_ROOT / "byte_custody_preflight_report_v2_35.json", errors)
    risk = load_json(OUTPUT_ROOT / "acquisition_risk_temperature_policy_v2_35.json", errors)
    structural = load_json(OUTPUT_ROOT / "structural_complexity_filter_v2_35.json", errors)
    lead_pool = load_json(OUTPUT_ROOT / "candidate2_acquisition_lead_pool_v2_35.json", errors)
    policy = load_json(OUTPUT_ROOT / "candidate2_acquisition_policy_v2_35.json", errors)
    budget = load_json(OUTPUT_ROOT / "candidate2_acquisition_budget_v2_35.json", errors)
    metadata = load_json(OUTPUT_ROOT / "candidate2_metadata_probe_log.json", errors)
    github = load_json(OUTPUT_ROOT / "candidate2_github_api_status.json", errors)
    attempts = load_json(OUTPUT_ROOT / "candidate2_acquisition_attempt_log.json", errors)
    lead_attempts = load_json(OUTPUT_ROOT / "candidate2_lead_attempts.json", errors)
    resolved = load_json(OUTPUT_ROOT / "candidate2_resolved_commit_attempts.json", errors)
    rejection = load_json(OUTPUT_ROOT / "candidate2_rejection_ledger.json", errors)
    merge = load_json(OUTPUT_ROOT / "candidate2_registry_merge_report.json", errors)
    registry_report = load_json(OUTPUT_ROOT / "external_candidate_registry_validation_report_after_candidate2.json", errors)
    registry_status = load_json(OUTPUT_ROOT / "external_candidate_registry_status_after_candidate2.json", errors)
    experiment = load_json(OUTPUT_ROOT / "matched_null_experiment_status_v2_35.json", errors)
    public_language = load_json(OUTPUT_ROOT / "public_language_audit.json", errors)
    ledger = load_json(OUTPUT_ROOT / "proof_obligations_ledger.json", errors)
    roadmap = load_json(OUTPUT_ROOT / "roadmap_carry_forward_check_v2_35.json", errors)
    resolution = load_json(OUTPUT_ROOT / "resolution_depth_diagnostic_v2_35.json", errors)
    claim = load_json(OUTPUT_ROOT / "claim_boundary_v2_35.json", errors)

    expect(official.get("status") == "PASS", errors, "v2.35 official artifact verification not PASS")
    expect(official.get("artifact_name") == "v2_35_automated_candidate2_acquisition_lane_artifacts", errors, "v2.35 official artifact name mismatch")
    expect(official.get("workflow_run_id") == OFFICIAL_WORKFLOW_RUN_ID, errors, "v2.35 official workflow run mismatch")
    expect(official.get("artifact_id") == OFFICIAL_ARTIFACT_ID, errors, "v2.35 official artifact id mismatch")
    expect(official.get("zip_size") == OFFICIAL_ARTIFACT_SIZE, errors, "v2.35 official artifact size mismatch")
    expect(official.get("zip_sha256") == OFFICIAL_ARTIFACT_SHA256, errors, "v2.35 official artifact SHA mismatch")
    expect(official.get("entry_count") == OFFICIAL_ARTIFACT_ENTRY_COUNT, errors, "v2.35 official artifact entry count mismatch")
    expect(official.get("safe_path_status") == "PASS", errors, "v2.35 official safe-path status mismatch")
    expect(official.get("duplicate_path_count") == 0, errors, "v2.35 official duplicate path count mismatch")
    expect(official.get("internal_manifest_entries_checked") == 25, errors, "v2.35 official internal manifest checked count mismatch")
    expect(official.get("internal_manifest_missing_count") == 0, errors, "v2.35 official internal manifest missing count mismatch")
    expect(official.get("internal_manifest_malformed_count") == 0, errors, "v2.35 official internal manifest malformed count mismatch")
    expect(official.get("internal_manifest_failure_count") == 0, errors, "v2.35 official internal manifest failure count mismatch")
    expect(official.get("output_manifest_coverage") == "PASS", errors, "v2.35 official output manifest coverage mismatch")
    expect(official.get("manual_artifact_boundary") == "PASS", errors, "v2.35 manual artifact boundary mismatch")
    expect(official.get("downloaded_by_codex") is False, errors, "v2.35 artifact must be manually supplied")
    local_artifact_path = str(official.get("local_artifact_path_outside_git", ""))
    expect(local_artifact_path and not local_artifact_path.startswith(str(REPO_ROOT)), errors, "v2.35 local artifact path must be outside repo")
    expect(official.get("resolved_commit_carry_forward_status") == "PASS", errors, "v2.35 resolved commit carry-forward missing")
    expect(official.get("metadata_only_replay_gap_carry_forward_status") == "PASS", errors, "v2.35 metadata-only replay gap carry-forward missing")
    expect(official.get("v2_36_replay_queue_carry_forward_status") == "PASS", errors, "v2.36 replay queue carry-forward missing")
    expect(official.get("expected_v2_36_replay_queue_count") == 5, errors, "v2.36 replay queue count carry-forward mismatch")
    comparisons = official.get("repo_snapshot_update_file_comparison")
    expect(isinstance(comparisons, list) and len(comparisons) >= 10, errors, "v2.35 repo snapshot comparison missing")
    if isinstance(comparisons, list):
        allowed_status = {"match", "differs_ingested_from_artifact", "artifact_missing_not_updated"}
        for item in comparisons:
            if isinstance(item, dict):
                expect(item.get("status") in allowed_status, errors, "v2.35 repo snapshot comparison status invalid")

    expect(v234.get("status") == "PASS", errors, "v2.34 official ingest not PASS")
    expect(v234.get("zip_sha256") == "bd8feb5daf31412e72caf09b3a51237dc9a2317a401a9c24ee48604930eac192", errors, "v2.34 artifact SHA mismatch")
    expect(preflight.get("status") == "PASS", errors, "byte-custody preflight not PASS")
    expect(preflight.get("mismatch_count") == 0, errors, "byte-custody preflight mismatch present")
    expect(risk.get("status") == "PASS", errors, "risk policy not PASS")
    expect(risk.get("reject_threshold") == 5, errors, "risk reject threshold mismatch")
    expect(structural.get("status") == "PASS", errors, "structural filter not PASS")
    expect(structural.get("full_repository_tokenization_allowed") is False, errors, "full repo tokenization must be forbidden")
    expect(policy.get("external_metadata_is_lead_only") is True, errors, "metadata lead-only policy missing")
    expect(policy.get("candidate_requires_direct_controllergate_verification") is True, errors, "direct verification policy missing")
    expect(FIRST_CANDIDATE in policy.get("candidate2_forbidden_candidate_ids", []), errors, "first candidate must be forbidden as candidate #2")
    expect(budget.get("max_repos_attempted") == 10, errors, "max repo budget mismatch")
    expect(budget.get("max_candidate_commits_attempted") == 20, errors, "max commit budget mismatch")
    expect(LEAD_POOL_PATH.is_file(), errors, "lead pool input file missing")
    expect(len(lead_pool.get("known_rejected_leads", [])) == 6, errors, "known rejected lead count mismatch")
    expect(len(lead_pool.get("bounded_probe_repositories", [])) >= 10, errors, "bounded probe repo count too small")
    expect(metadata.get("external_metadata_is_proof") is False, errors, "metadata must not be proof")
    expect(metadata.get("full_repository_tokenization_used") is False, errors, "full repo tokenization used")
    expect(github.get("used_for_candidate_proof") is False, errors, "GitHub API must not be candidate proof")

    lead_attempt_list = lead_attempts.get("lead_attempts")
    expect(isinstance(lead_attempt_list, list), errors, "lead attempts missing")
    if isinstance(lead_attempt_list, list):
        expect(len(lead_attempt_list) == results.get("repos_attempted"), errors, "repo attempt count mismatch")
        for item in lead_attempt_list:
            if isinstance(item, dict):
                expect(item.get("workspace_committed") is False, errors, "workspace must not be committed")
                expect(item.get("fixed_later_gold_pr_patch_accessed") is False, errors, "forbidden evidence accessed in lead attempt")
                expect(item.get("candidate_selected") is False, errors, "candidate selected despite no verified seed")

    resolved_commits = resolved.get("resolved_commits")
    expect(isinstance(resolved_commits, list), errors, "resolved commits missing")
    if isinstance(resolved_commits, list):
        expect(len(resolved_commits) == results.get("candidate_commits_attempted"), errors, "commit attempt count mismatch")
        for item in resolved_commits:
            if not isinstance(item, dict):
                errors.append("resolved commit entry invalid")
                continue
            expect(re.fullmatch(r"[0-9a-f]{40}", str(item.get("commit_sha", ""))) is not None, errors, "noncanonical commit accepted into resolved attempts")
            expect(item.get("rev_parse_status") == "PASS", errors, "resolved commit missing rev-parse PASS")
            expect(item.get("cat_file_type") == "commit", errors, "resolved commit not verified as commit object")
            expect(item.get("accepted_as_seed") is False, errors, "seed accepted without full verification")
            expect(item.get("commit_sha") != FIRST_CANDIDATE, errors, "first candidate reused as commit identity")

    expect(rejection.get("status") == "PASS", errors, "rejection ledger not PASS")
    expect(merge.get("status") == "not_run_no_verified_seed", errors, "registry merge should not run")
    expect(merge.get("registry_updated") is False, errors, "registry updated without verified seed")
    expect(registry_report.get("registry_validation_status") == "PASS", errors, "registry validation after candidate2 not PASS")
    expect(registry_status.get("reviewed_valid_candidate_count_after_run") == 1, errors, "reviewed candidate count should remain 1")
    expect(registry_status.get("candidate2_merged") is False, errors, "candidate2 must not merge")
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
    expect(claim.get("v2_35_promoted_to_current") is False, errors, "v2.35 must not be promoted")
    expect(claim.get("verified_seed_acquired") is False, errors, "verified seed flag mismatch")
    expect(claim.get("matched_null_experiment_attempted") is False, errors, "claim boundary experiment flag mismatch")
    expect(claim.get("patch_generated") is False, errors, "claim boundary patch flag mismatch")
    expect(claim.get("full_scoring") == "NOT_RUN/disallowed", errors, "full scoring mismatch")
    expect(claim.get("memory_lift_status") == "undemonstrated", errors, "memory-lift mismatch")
    expect(claim.get("self_maintaining_software_status") == "false/not_demonstrated", errors, "self-maintaining mismatch")
    expect(claim.get("exact_blocker") == BLOCKER, errors, "claim blocker mismatch")

    expect(results.get("status") == "blocked", errors, "campaign status mismatch")
    expect(results.get("v2_34_official_ingest_status") == "PASS", errors, "campaign v2.34 ingest status mismatch")
    expect(results.get("byte_custody_preflight_status") == "PASS", errors, "campaign byte-custody status mismatch")
    expect(results.get("acquisition_lead_count", 0) >= 17, errors, "campaign acquisition lead count too small")
    expect(results.get("repos_attempted", 0) <= 10, errors, "repo budget exceeded")
    expect(results.get("candidate_commits_attempted", 0) <= 20, errors, "commit budget exceeded")
    expect(results.get("verified_seed_acquired") is False, errors, "verified seed acquired unexpectedly")
    expect(results.get("seed_registry_merge_status") == "not_run_no_verified_seed", errors, "seed registry merge status mismatch")
    expect(results.get("reviewed_valid_candidate_count_after_run") == 1, errors, "reviewed candidate count mismatch")
    expect(results.get("matched_null_experiment_attempted") is False, errors, "campaign matched-null attempted mismatch")
    expect(results.get("preliminary_single_candidate_memory_lift_evidence") is False, errors, "preliminary memory evidence must be false")
    expect(results.get("patch_generated") is False, errors, "campaign patch generated mismatch")
    expect(results.get("full_scoring") == "NOT_RUN/disallowed", errors, "campaign full scoring mismatch")
    expect(results.get("memory_lift_status") == "undemonstrated", errors, "campaign memory lift mismatch")
    expect(results.get("self_maintaining_software_status") == "false/not_demonstrated", errors, "campaign self-maintaining mismatch")
    expect(results.get("current_protocol_version") == "v2.13", errors, "campaign current protocol mismatch")
    expect(results.get("exact_blocker") == BLOCKER, errors, "campaign blocker mismatch")


def audit_public_updates(errors: list[str]) -> None:
    expect(section_present(README_PATH, "v2.35 automated candidate #2 acquisition status"), errors, "README v2.35 section missing")
    expect(section_present(ROADMAP_PATH, "v2.35 Automated Candidate #2 Acquisition"), errors, "roadmap v2.35 section missing")
    expect(section_present(CAPABILITY_PLAN_PATH, "v2.35 automated acquisition status"), errors, "capability plan v2.35 section missing")
    expect(section_present(RESOLUTION_DOC_PATH, "v2.35 automated acquisition status"), errors, "resolution doc v2.35 section missing")
    expect(section_present(SHAREABLE_PATH, "v2.35 Automated Candidate #2 Acquisition Status"), errors, "shareable v2.35 section missing")
    expect(section_present(ACQUISITION_DOC_PATH, "Candidate #2 acquisition workbench"), errors, "acquisition workbench doc missing")


def audit_registry(errors: list[str]) -> None:
    report = registry_validator.validate_registry()
    expect(report.get("registry_validation_status") == "PASS", errors, "fresh registry validation failed")
    expect(report.get("candidate_count") == 1, errors, "v2.35 blocked run must not add candidate #2")
    expect(report.get("valid_reviewed_candidate_count") == 1, errors, "reviewed valid count must remain 1")
    registry = load_json(REGISTRY_PATH, errors)
    candidates = registry.get("candidates")
    if isinstance(candidates, list):
        ids = [item.get("candidate_id") for item in candidates if isinstance(item, dict)]
        expect(ids == [FIRST_CANDIDATE], errors, "registry must still contain only first reviewed candidate")


def main() -> int:
    errors: list[str] = []
    for rel in REQUIRED_FILES:
        if not (OUTPUT_ROOT / rel).exists():
            errors.append(f"missing required file {rel}")
    checked, entries = verify_manifest(errors)
    audit_outputs(errors, entries)
    audit_public_updates(errors)
    audit_registry(errors)
    run_python(["scripts/byte_custody_preflight.py"], errors, "byte-custody preflight")
    run_python(["scripts/audit_v2_34_candidate2_seed_verification_workbench_lane.py"], errors, "v2.34 nested regression audit")
    if errors:
        print("v2.35 audit FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("v2.35 audit PASS")
    print(f"checked_manifest_entries={checked}")
    print("current_protocol_version=v2.13")
    print(f"exact_blocker={BLOCKER}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
