#!/usr/bin/env python3
"""Audit v2.36 resolved-commit replay and candidate admission evidence."""

from __future__ import annotations

import csv
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path, PurePosixPath
from typing import Any

import validate_external_candidate_registry as registry_validator


REPO_ROOT = Path(__file__).resolve().parents[1]
CAMPAIGN_ID = "v2_36_resolved_commit_replay_seed_promotion"
OUTPUT_ROOT = REPO_ROOT / "outputs" / CAMPAIGN_ID
V35_ROOT = REPO_ROOT / "outputs" / "v2_35_automated_candidate2_acquisition_lane"
REGISTRY_PATH = REPO_ROOT / "configs" / "external_candidate_registry.json"
README_PATH = REPO_ROOT / "README.md"
ROADMAP_PATH = REPO_ROOT / "docs" / "non_ansible_capability_roadmap.md"
CAPABILITY_PLAN_PATH = REPO_ROOT / "docs" / "structural_repair_capability_plan.md"
SHAREABLE_PATH = REPO_ROOT / "controllergate_v1_7_beta" / "reports" / "critic_review_package" / "shareable_summary.md"

FINAL_BLOCKER = "blocked_no_native_or_issue_derived_candidate2_seed_acquired"
FIRST_CANDIDATE = "py_bugger_issue_65"
V35_ARTIFACT_SHA256 = "f0fc373f727f2e142255a1392d107a00e997961889dc4d113141bceb298f6f7b"

REQUIRED_FILES = [
    "campaign_summary.md",
    "campaign_results.json",
    "v2_35_artifact_ingest_verification.json",
    "artifact_repo_snapshot_comparison.json",
    "byte_custody_preflight_report_v2_36.json",
    "resolved_commit_replay_queue_v2_36.json",
    "resolved_commit_replay_policy_v2_36.json",
    "resolved_commit_replay_attempt_log.json",
    "resolved_commit_replay_rejection_ledger.json",
    "resolved_commit_environment_strategy.json",
    "candidate2_registry_merge_report.json",
    "external_candidate_registry_validation_report_after_candidate2.json",
    "external_candidate_registry_status_after_candidate2.json",
    "matched_null_experiment_status_v2_36.json",
    "public_language_audit.json",
    "proof_obligations_ledger.json",
    "roadmap_carry_forward_check_v2_36.json",
    "resolution_depth_diagnostic_v2_36.json",
    "claim_boundary_v2_36.json",
    "issue_derived_acquisition_status_v2_36.json",
    "acquisition_risk_calibration_policy_v2_36.json",
    "acquisition_risk_calibration_log_v2_36.json",
    "issue_text_timestamp_guard_v2_36.json",
    "issue_derived_harness_generation_policy_v2_36.json",
    "issue_derived_harness_firewall_v2_36.json",
    "issue_derived_harness_candidate_log_v2_36.json",
    "issue_derived_matched_null_experiment_status.json",
    "issue_derived_memory_lift_claim_evaluation.json",
    "structural_navigation_map_v2_36.json",
    "repairability_basin_scores_v2_36.csv",
    "escape_boundary_rejection_ledger_v2_36.json",
    "candidate_admission_decision_map_v2_36.json",
    "active_probe_router_policy_v2_36.json",
    "active_probe_routing_log_v2_36.json",
    "minimal_verification_probe_trace_v2_36.json",
    "active_probe_budget_trace_v2_36.json",
    "coupled_dependency_projection_map_v2_36.json",
    "interlock_invariant_map_v2_36.json",
    "context_boundary_map_v2_36.json",
    "proof_coordinate_ledger_v2_36.json",
    "SHA256SUMS.txt",
]

SEED_ONLY_FILES = [
    "candidate2_verified_seed_record.json",
    "candidate2_verified_seed_draft_v2_36.json",
    "candidate2_source_checkout_audit.json",
    "candidate2_buggy_tree_manifest.json",
    "candidate2_target_test_file_hashes.json",
    "candidate2_support_file_hashes.json",
    "candidate2_environment_file_hashes.json",
    "candidate2_command_manifest.json",
    "candidate2_environment_resolution_preflight.json",
    "candidate2_semantic_failure_signature_manifest.json",
    "candidate2_registry_entry_candidate.json",
]

ISSUE_VERIFIED_ONLY_FILES = [
    "issue_derived_ephemeral_harness.py",
    "issue_derived_harness_sha256.txt",
    "issue_derived_issue_text_hash.json",
    "issue_derived_harness_verification_result.json",
    "issue_derived_harness_failure_capture_raw.log",
    "issue_derived_harness_failure_capture_normalized.txt",
    "issue_derived_harness_semantic_failure_signature.json",
    "issue_derived_candidate_registry_entry_candidate.json",
    "issue_derived_candidate_registry_merge_report.json",
]

MATCHED_NULL_ONLY_FILES = [
    "matched_null_arm_a_memory_enabled_plan.json",
    "matched_null_arm_b_memory_disabled_plan.json",
    "matched_null_arm_a_results.json",
    "matched_null_arm_b_results.json",
    "matched_null_separation_score_result.json",
    "memory_lift_claim_evaluation.json",
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
        errors.append("missing v2.36 SHA256SUMS.txt")
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
    expect(isinstance(entries, list) and len(entries) >= 5, errors, "proof ledger entries missing")
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

    results = load_json(OUTPUT_ROOT / "campaign_results.json", errors)
    v35 = load_json(OUTPUT_ROOT / "v2_35_artifact_ingest_verification.json", errors)
    queue = load_json(OUTPUT_ROOT / "resolved_commit_replay_queue_v2_36.json", errors)
    policy = load_json(OUTPUT_ROOT / "resolved_commit_replay_policy_v2_36.json", errors)
    attempts = load_json(OUTPUT_ROOT / "resolved_commit_replay_attempt_log.json", errors)
    rejections = load_json(OUTPUT_ROOT / "resolved_commit_replay_rejection_ledger.json", errors)
    merge = load_json(OUTPUT_ROOT / "candidate2_registry_merge_report.json", errors)
    registry_report = load_json(OUTPUT_ROOT / "external_candidate_registry_validation_report_after_candidate2.json", errors)
    registry_status = load_json(OUTPUT_ROOT / "external_candidate_registry_status_after_candidate2.json", errors)
    experiment = load_json(OUTPUT_ROOT / "matched_null_experiment_status_v2_36.json", errors)
    issue_status = load_json(OUTPUT_ROOT / "issue_derived_acquisition_status_v2_36.json", errors)
    issue_guard = load_json(OUTPUT_ROOT / "issue_text_timestamp_guard_v2_36.json", errors)
    issue_firewall = load_json(OUTPUT_ROOT / "issue_derived_harness_firewall_v2_36.json", errors)
    public_language = load_json(OUTPUT_ROOT / "public_language_audit.json", errors)
    ledger = load_json(OUTPUT_ROOT / "proof_obligations_ledger.json", errors)
    roadmap = load_json(OUTPUT_ROOT / "roadmap_carry_forward_check_v2_36.json", errors)
    claim = load_json(OUTPUT_ROOT / "claim_boundary_v2_36.json", errors)
    structural = load_json(OUTPUT_ROOT / "structural_navigation_map_v2_36.json", errors)
    admission = load_json(OUTPUT_ROOT / "candidate_admission_decision_map_v2_36.json", errors)
    probe_policy = load_json(OUTPUT_ROOT / "active_probe_router_policy_v2_36.json", errors)
    probe_log = load_json(OUTPUT_ROOT / "active_probe_routing_log_v2_36.json", errors)
    probe_budget = load_json(OUTPUT_ROOT / "active_probe_budget_trace_v2_36.json", errors)
    projection = load_json(OUTPUT_ROOT / "coupled_dependency_projection_map_v2_36.json", errors)
    interlock = load_json(OUTPUT_ROOT / "interlock_invariant_map_v2_36.json", errors)
    context = load_json(OUTPUT_ROOT / "context_boundary_map_v2_36.json", errors)
    coordinates = load_json(OUTPUT_ROOT / "proof_coordinate_ledger_v2_36.json", errors)

    expect(v35.get("status") == "PASS", errors, "v2.35 official ingest not PASS")
    expect(v35.get("zip_sha256") == V35_ARTIFACT_SHA256, errors, "v2.35 official artifact SHA mismatch")
    expect(results.get("v2_35_official_ingest_status") == "PASS", errors, "campaign v2.35 ingest status mismatch")
    expect(results.get("current_protocol_version") == "v2.13", errors, "current protocol changed")
    expect(results.get("full_scoring") == "NOT_RUN/disallowed", errors, "full scoring must remain disabled")
    expect(results.get("memory_lift_status") == "undemonstrated", errors, "memory lift overclaimed")
    expect(results.get("self_maintaining_software_status") == "false/not_demonstrated", errors, "self-maintaining overclaimed")
    expect(results.get("patch_generated") is False, errors, "patch must not be generated without candidate #2 verification")

    queue_items = queue.get("queue")
    expect(isinstance(queue_items, list) and len(queue_items) == 5, errors, "replay queue count mismatch")
    if isinstance(queue_items, list):
        for item in queue_items:
            if isinstance(item, dict):
                expect(re.fullmatch(r"[0-9a-f]{40}", str(item.get("commit_sha", ""))) is not None, errors, "noncanonical commit in replay queue")
                expect(item.get("v2_35_reason") == "metadata_only_no_native_failure_replay_verified", errors, "queue not derived from v2.35 replay gap")
                expect(item.get("candidate_id") != FIRST_CANDIDATE, errors, "first candidate reused as candidate #2")

    expect(policy.get("native_replay_before_issue_fallback") is True, errors, "native replay order policy missing")
    expect(policy.get("fixed_later_gold_pr_patch_content_forbidden") is True, errors, "forbidden evidence policy missing")

    attempt_list = attempts.get("attempts")
    expect(isinstance(attempt_list, list), errors, "attempt log missing")
    if isinstance(attempt_list, list):
        expect(len(attempt_list) == results.get("commits_replay_attempted"), errors, "attempt count mismatch")
        expect(len(attempt_list) > 0, errors, "no resolved commits replay-attempted")
        for item in attempt_list:
            if not isinstance(item, dict):
                errors.append("invalid attempt record")
                continue
            expect(re.fullmatch(r"[0-9a-f]{40}", str(item.get("commit_sha", ""))) is not None, errors, "noncanonical attempt commit")
            resolution = item.get("commit_resolution") or {}
            expect(resolution.get("rev_parse_status") == "PASS", errors, f"rev-parse not PASS for {item.get('candidate_id')}")
            expect(resolution.get("cat_file_type") == "commit", errors, f"cat-file not commit for {item.get('candidate_id')}")
            expect(item.get("workspace_committed") is False, errors, "external workspace committed")
            expect(item.get("fixed_later_gold_pr_patch_accessed") is False, errors, "forbidden evidence accessed")
            expect(item.get("fixed_diff_computed") is False, errors, "fixed diff computed")
            expect(item.get("pr_patch_content_used") is False, errors, "PR patch content used")

    probe_records = probe_log.get("probes")
    expect(isinstance(probe_records, list) and len(probe_records) > 0, errors, "probe log missing")
    if isinstance(probe_records, list):
        expect(len(probe_records) <= 80, errors, "active probe budget exceeded")
        seen_by_candidate: dict[str, int] = {}
        for probe in probe_records:
            if not isinstance(probe, dict):
                errors.append("invalid probe record")
                continue
            expect(probe.get("probe_id"), errors, "probe id missing")
            expect(probe.get("candidate_id"), errors, "probe candidate missing")
            expect(probe.get("input_evidence_hash"), errors, "probe input hash missing")
            expect(probe.get("output_hash"), errors, "probe output hash missing")
            expect(probe.get("information_gained"), errors, "probe information field missing")
            cid = str(probe.get("candidate_id"))
            seen_by_candidate[cid] = seen_by_candidate.get(cid, 0) + 1
        for cid, count in seen_by_candidate.items():
            expect(count <= 8, errors, f"probe budget exceeded for {cid}")

    expect(probe_policy.get("status") == "PASS", errors, "active probe policy not PASS")
    expect(probe_budget.get("status") == "PASS", errors, "active probe budget trace not PASS")
    expect(structural.get("status") == "PASS", errors, "structural navigation map missing or failed")
    expect((OUTPUT_ROOT / "repairability_basin_scores_v2_36.csv").is_file(), errors, "repairability score CSV missing")
    with (OUTPUT_ROOT / "repairability_basin_scores_v2_36.csv").open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    expect(len(rows) == results.get("commits_replay_attempted"), errors, "repairability score row count mismatch")
    expect(admission.get("status") == "PASS", errors, "admission map not PASS")
    decisions = admission.get("decisions")
    expect(isinstance(decisions, list), errors, "admission decisions missing")
    admitted = [item for item in decisions or [] if isinstance(item, dict) and item.get("admitted")]
    if admitted:
        for item in admitted:
            expect(item.get("admission_decision") in {"admitted_native_replay_candidate", "admitted_issue_derived_reproduction_candidate"}, errors, "invalid admitted decision")
            expect(item.get("repairability_score") is not None and int(item.get("repairability_score")) <= 4, errors, "admitted candidate score too high")
    else:
        expect(results.get("native_candidate2_seed_acquired") is False, errors, "native seed flag inconsistent")
        expect(results.get("issue_derived_candidate2_seed_acquired") is False, errors, "issue-derived seed flag inconsistent")
        expect(results.get("exact_blocker") == FINAL_BLOCKER, errors, "no-seed blocker mismatch")
        for rel in SEED_ONLY_FILES + ISSUE_VERIFIED_ONLY_FILES + MATCHED_NULL_ONLY_FILES:
            expect(not (OUTPUT_ROOT / rel).exists(), errors, f"conditional output must not exist without verified candidate: {rel}")

    expect(projection.get("status") == "PASS", errors, "projection map not PASS")
    expect(interlock.get("status") == "PASS", errors, "interlock map not PASS")
    expect(context.get("status") == "PASS", errors, "context boundary map not PASS")
    expect(coordinates.get("status") == "PASS", errors, "proof coordinate ledger not PASS")
    for item in admitted:
        cid = item.get("candidate_id")
        has_interlock = any((entry.get("candidate_id") == cid and entry.get("status") == "PASS") for entry in interlock.get("maps", []))
        expect(has_interlock, errors, f"admitted candidate lacks source interlock: {cid}")

    expect(issue_status.get("fallback_attempted") is True or results.get("native_candidate2_seed_acquired") is True, errors, "issue-derived fallback did not run after native replay failed")
    expect(issue_status.get("native_replay_failed_first") is True or results.get("native_candidate2_seed_acquired") is True, errors, "issue fallback order invalid")
    expect(issue_guard.get("comments_or_patch_discussion_used") is False, errors, "issue comments or patch discussion used")
    expect(issue_firewall.get("fixed_later_gold_pr_patch_content_used") is False, errors, "issue fallback firewall violated")
    expect(issue_firewall.get("committed_to_external_project_tree") is False, errors, "issue harness committed to external tree")

    expect(rejections.get("status") == "PASS", errors, "rejection ledger not PASS")
    expect(merge.get("registry_updated") is False, errors, "registry updated unexpectedly")
    expect(registry_report.get("registry_validation_status") == "PASS", errors, "registry validation after candidate2 not PASS")
    expect(registry_status.get("reviewed_valid_candidate_count_after_run") == 1, errors, "native reviewed count changed")
    expect(registry_status.get("reviewed_issue_derived_candidate_count") == 0, errors, "issue-derived count changed unexpectedly")
    expect(experiment.get("matched_null_experiment_attempted") is False, errors, "matched-null experiment must not run without verified candidate")
    expect(public_language.get("status") == "PASS", errors, "public language audit not PASS")
    expect(public_language.get("exact_match_count") == 0, errors, "public language hits present")
    audit_proof_ledger(ledger, errors)
    expect(roadmap.get("status") == "PASS", errors, "roadmap carry-forward not PASS")
    expect(claim.get("current_protocol_version") == "v2.13", errors, "claim current protocol changed")
    expect(claim.get("v2_36_promoted_to_current") is False, errors, "v2.36 promoted unexpectedly")
    expect(claim.get("matched_null_experiment_attempted") is False, errors, "claim matched-null mismatch")
    expect(claim.get("patch_generated") is False, errors, "claim patch mismatch")
    expect(claim.get("full_scoring") == "NOT_RUN/disallowed", errors, "claim full scoring mismatch")


def audit_public_updates(errors: list[str]) -> None:
    expect(section_present(README_PATH, "v2.36 resolved-commit replay and candidate admission status"), errors, "README v2.36 section missing")
    expect(section_present(ROADMAP_PATH, "v2.36 resolved-commit replay and candidate admission"), errors, "roadmap v2.36 section missing")
    expect(section_present(CAPABILITY_PLAN_PATH, "v2.36 structural acquisition and admission status"), errors, "capability plan v2.36 section missing")
    expect(section_present(SHAREABLE_PATH, "v2.36 Resolved-Commit Replay and Candidate Admission Status"), errors, "shareable v2.36 section missing")


def audit_registry(errors: list[str]) -> None:
    report = registry_validator.validate_registry()
    expect(report.get("registry_validation_status") == "PASS", errors, "fresh registry validation failed")
    expect(report.get("candidate_count") == 1, errors, "v2.36 no-seed run must not add native candidate #2")
    expect(report.get("valid_reviewed_candidate_count") == 1, errors, "reviewed valid count must remain 1")
    registry = load_json(REGISTRY_PATH, errors)
    candidates = registry.get("candidates")
    if isinstance(candidates, list):
        ids = [item.get("candidate_id") for item in candidates if isinstance(item, dict)]
        expect(ids == [FIRST_CANDIDATE], errors, "registry must still contain only the first reviewed candidate")


def main() -> int:
    errors: list[str] = []
    for rel in REQUIRED_FILES:
        if not (OUTPUT_ROOT / rel).exists():
            errors.append(f"missing required file {rel}")
    checked, entries = verify_manifest(errors)
    audit_outputs(errors, entries)
    audit_public_updates(errors)
    audit_registry(errors)
    run_python(["scripts/byte_custody_preflight.py"], errors, "byte-custody preflight", timeout=1200)
    if errors:
        print("v2.36 audit FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    results = load_json(OUTPUT_ROOT / "campaign_results.json", errors)
    print("v2.36 audit PASS")
    print(f"checked_manifest_entries={checked}")
    print("current_protocol_version=v2.13")
    print(f"replay_queue_count={results.get('replay_queue_count')}")
    print(f"commits_replay_attempted={results.get('commits_replay_attempted')}")
    print(f"native_candidate2_seed_acquired={results.get('native_candidate2_seed_acquired')}")
    print(f"issue_derived_candidate2_seed_acquired={results.get('issue_derived_candidate2_seed_acquired')}")
    print(f"exact_blocker={results.get('exact_blocker')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
