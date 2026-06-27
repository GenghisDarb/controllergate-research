#!/usr/bin/env python3
"""Audit v2.33 candidate #2 seed intake and matched-null experiment evidence."""

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
CAMPAIGN_ID = "v2_33_candidate2_matched_null_memory_repair_lane"
OUTPUT_ROOT = REPO_ROOT / "outputs" / CAMPAIGN_ID
V232_ROOT = REPO_ROOT / "outputs" / "v2_32_second_external_candidate_seed_and_memory_protocol_lane"
SEED_PATH = REPO_ROOT / "inputs" / "external_candidate_seed_draft_v2_33.json"
README_PATH = REPO_ROOT / "README.md"
ROADMAP_PATH = REPO_ROOT / "docs" / "non_ansible_capability_roadmap.md"
CAPABILITY_PLAN_PATH = REPO_ROOT / "docs" / "structural_repair_capability_plan.md"
RESOLUTION_DOC_PATH = REPO_ROOT / "docs" / ("controllergate_" + "t" + "ld" + "_resolution_map.md")
SHAREABLE_PATH = REPO_ROOT / "controllergate_v1_7_beta" / "reports" / "critic_review_package" / "shareable_summary.md"
EXTERNAL_REGISTRY_PATH = REPO_ROOT / "configs" / "external_candidate_registry.json"
EPISODE_REGISTRY_PATH = REPO_ROOT / "configs" / "external_repair_episode_registry.json"

BLOCKER = "blocked_no_second_external_candidate_seed_draft_provided"
FIRST_CANDIDATE = "py_bugger_issue_65"
EXPECTED_V232_SHA = "4fa00924210ffa95b6d3c3104457350502bbda2cf7bd348ea92cc2a3f736609e"
EXPECTED_V232_RUN = 28284054288
EXPECTED_V232_ARTIFACT_ID = 7922901616
EXPECTED_V233_SHA = "7f8cb2fe180c974cf17880d2a010829e39445a6d1de05c272a0a0d7087115c6a"
EXPECTED_V233_SIZE = 78316
EXPECTED_V233_ENTRIES = 43
EXPECTED_V233_MANIFEST_CHECKED = 31
EXPECTED_V233_RUN = 28295104567
EXPECTED_V233_ARTIFACT_ID = 7926245010
EXPECTED_V233_ARTIFACT_NAME = "v2_33_candidate2_matched_null_memory_repair_lane_artifacts"
EXPECTED_V233_HEAD = "aeb627422c12c0b8258b84b1329c20349311d870"

REQUIRED_FILES = [
    "campaign_summary.md",
    "campaign_results.json",
    "v2_33_official_artifact_verification.json",
    "v2_32_artifact_ingest_verification.json",
    "artifact_repo_snapshot_comparison.json",
    "first_scoreable_episode_carry_forward.json",
    "seed_presence_check_v2_33.json",
    "second_seed_schema_validation.json",
    "second_seed_forbidden_source_guard.json",
    "second_seed_registry_merge_report.json",
    "external_candidate_registry_validation_report_after_second_seed.json",
    "external_candidate_registry_status_after_second_seed.json",
    "prospective_matched_null_memory_protocol_carry_forward.json",
    "matched_null_experiment_preregistration_v2_33.json",
    "matched_null_arm_a_memory_enabled_plan.json",
    "matched_null_arm_b_memory_disabled_plan.json",
    "memory_lift_claim_evaluation.json",
    "telomeric_budget_policy.json",
    "micro_reversal_policy.json",
    "public_language_audit.json",
    "proof_obligations_ledger.json",
    "roadmap_carry_forward_check_v2_33.json",
    "resolution_depth_diagnostic_v2_33.json",
    "claim_boundary_v2_33.json",
    "SHA256SUMS.txt",
]

NO_SEED_PACKET_FILES = [
    "candidate2_discovery_packet.md",
    "candidate2_seed_template.json",
    "candidate2_seed_review_checklist.md",
    "candidate2_seed_validation_commands.md",
    "candidate2_disallowed_seed_patterns.md",
    "candidate2_candidate_hunt_queries.txt",
    "candidate2_manual_verification_protocol.md",
    "candidate2_external_helper_prompt.md",
]

SEED_PRESENT_ONLY_FILES = [
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
    "second_seed_source_test_colocation_proof.json",
    "second_seed_support_file_colocation_proof.json",
    "second_seed_registry_entry_candidate.json",
    "matched_null_arm_a_results.json",
    "matched_null_arm_b_results.json",
    "matched_null_separation_score_result.json",
    "telomeric_budget_trace_arm_a.json",
    "telomeric_budget_trace_arm_b.json",
    "micro_reversal_trace_arm_a.json",
    "micro_reversal_trace_arm_b.json",
    "context_boundary_map_arm_a.json",
    "context_boundary_map_arm_b.json",
    "seed_constraint_revalidation_arm_a.json",
    "seed_constraint_revalidation_arm_b.json",
    "no_overreach_regression_arm_a.json",
    "no_overreach_regression_arm_b.json",
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
        errors.append("missing v2.33 SHA256SUMS.txt")
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
        if rel.startswith("/") or any(part in {"", ".", ".."} for part in pure.parts):
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


def hidden_public_terms() -> list[str]:
    return [
        "chromo" + "somal",
        "bio" + "logical",
        "iso" + "morphic",
        "TO" + "RUS",
        "T" + "LD",
        "A" + "GI",
        "observer" + "-state",
        "recursion" + "-constant",
        "meta" + "phorical",
    ]


def section_present(path: Path, heading: str) -> bool:
    if not path.is_file():
        return False
    return f"## {heading}" in path.read_text(encoding="utf-8")


def section_text(path: Path, heading: str) -> str:
    if not path.is_file():
        return ""
    text = path.read_text(encoding="utf-8")
    match = re.search(rf"\n## {re.escape(heading)}\n(.*?)(?=\n## |\Z)", text, re.S)
    return match.group(0) if match else ""


def run_python(args: list[str], errors: list[str], label: str) -> None:
    result = subprocess.run(
        [sys.executable, *args],
        cwd=str(REPO_ROOT),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        tail = "\n".join((result.stdout + "\n" + result.stderr).splitlines()[-30:])
        errors.append(f"{label} failed\n{tail}")


def audit_proof_ledger(ledger: dict[str, Any], errors: list[str]) -> None:
    expect(ledger.get("status") == "PASS", errors, "proof ledger status mismatch")
    entries = ledger.get("entries")
    expect(isinstance(entries, list) and len(entries) >= 9, errors, "proof ledger entries missing")
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


def audit_discovery_packet(errors: list[str], manifest_entries: set[str]) -> None:
    for rel in NO_SEED_PACKET_FILES:
        path = OUTPUT_ROOT / rel
        expect(path.is_file(), errors, f"missing Candidate #2 discovery packet file {rel}")
        expect(rel in manifest_entries, errors, f"discovery packet file missing from SHA256SUMS: {rel}")
    template = load_json(OUTPUT_ROOT / "candidate2_seed_template.json", errors)
    expect(
        list(template.keys())
        == [
            "candidate_id",
            "source_type",
            "repo_url",
            "buggy_commit_sha",
            "test_command",
            "target_test_file_paths",
            "support_file_paths",
            "environment_lock_source",
            "decision_time_safe_basis",
            "registry_author",
            "registry_review_status",
            "created_utc",
            "notes",
        ],
        errors,
        "candidate2 seed template fields/order mismatch",
    )
    expect(template.get("source_type") == "public_github_repo", errors, "seed template source_type mismatch")
    expect(template.get("decision_time_safe_basis") == "offline_manual_verification", errors, "seed template basis mismatch")
    expect(template.get("registry_author") == "manual_seed_draft", errors, "seed template author mismatch")
    expect(template.get("registry_review_status") == "seed_draft", errors, "seed template review status mismatch")
    packet = (OUTPUT_ROOT / "candidate2_discovery_packet.md").read_text(encoding="utf-8") if (OUTPUT_ROOT / "candidate2_discovery_packet.md").is_file() else ""
    for phrase in [
        "v2.33 stopped",
        "native target test",
        "lead evidence only",
        "40-character",
        "Short SHAs",
        "No fixed commit contents",
        "generated tests",
        "public internet access",
    ]:
        expect(phrase in packet, errors, f"discovery packet missing phrase: {phrase}")
    checklist = (OUTPUT_ROOT / "candidate2_seed_review_checklist.md").read_text(encoding="utf-8") if (OUTPUT_ROOT / "candidate2_seed_review_checklist.md").is_file() else ""
    for phrase in [
        "repo is public GitHub or public HTTPS Git",
        "candidate is not BugsInPy",
        "candidate is not Ansible",
        "buggy_commit_sha is exactly 40 hex characters",
        "target test file exists in that exact buggy commit tree",
        "exact test command fails before patch",
        "no fixed commit content inspected",
    ]:
        expect(phrase in checklist, errors, f"seed review checklist missing phrase: {phrase}")
    helper = (OUTPUT_ROOT / "candidate2_external_helper_prompt.md").read_text(encoding="utf-8") if (OUTPUT_ROOT / "candidate2_external_helper_prompt.md").is_file() else ""
    expect("Find one real external Python seed candidate" in helper, errors, "external helper prompt missing opening instruction")
    expect("Do not provide placeholders" in helper, errors, "external helper prompt missing no-placeholder instruction")


def audit_registry_and_episode_counts(errors: list[str]) -> None:
    registry_validation = registry_validator.validate_registry()
    expect(registry_validation.get("registry_validation_status") == "PASS", errors, "fresh external registry validation failed")
    expect(registry_validation.get("valid_reviewed_candidate_count") == 1, errors, "reviewed valid candidate count must remain 1")
    registry = load_json(EXTERNAL_REGISTRY_PATH, errors)
    candidates = registry.get("candidates")
    expect(isinstance(candidates, list), errors, "external registry candidates missing")
    if isinstance(candidates, list):
        ids = [item.get("candidate_id") for item in candidates if isinstance(item, dict)]
        expect(ids.count(FIRST_CANDIDATE) == 1, errors, "first candidate missing or duplicated")
        expect(len(ids) == 1, errors, "v2.33 no-seed run must not add candidate #2")
    episode_registry = load_json(EPISODE_REGISTRY_PATH, errors)
    episodes = episode_registry.get("episodes")
    expect(isinstance(episodes, list), errors, "episode registry episodes missing")
    if isinstance(episodes, list):
        scoreable = [item for item in episodes if isinstance(item, dict) and item.get("scoreable") is True]
        expect(len(scoreable) == 1, errors, "scoreable external repair episode count must remain 1")


def audit_outputs(errors: list[str], manifest_entries: set[str]) -> None:
    for rel in REQUIRED_FILES:
        expect((OUTPUT_ROOT / rel).is_file(), errors, f"missing required output {rel}")
    seed_present = SEED_PATH.is_file()
    expect(seed_present is False, errors, "this v2.33 official run expects no seed file")
    if not seed_present:
        audit_discovery_packet(errors, manifest_entries)
        for rel in SEED_PRESENT_ONLY_FILES:
            expect(not (OUTPUT_ROOT / rel).exists(), errors, f"seed/arm output must not exist when seed absent: {rel}")

    official = load_json(OUTPUT_ROOT / "v2_33_official_artifact_verification.json", errors)
    v232 = load_json(OUTPUT_ROOT / "v2_32_artifact_ingest_verification.json", errors)
    results = load_json(OUTPUT_ROOT / "campaign_results.json", errors)
    first = load_json(OUTPUT_ROOT / "first_scoreable_episode_carry_forward.json", errors)
    presence = load_json(OUTPUT_ROOT / "seed_presence_check_v2_33.json", errors)
    schema = load_json(OUTPUT_ROOT / "second_seed_schema_validation.json", errors)
    forbidden = load_json(OUTPUT_ROOT / "second_seed_forbidden_source_guard.json", errors)
    merge = load_json(OUTPUT_ROOT / "second_seed_registry_merge_report.json", errors)
    registry_report = load_json(OUTPUT_ROOT / "external_candidate_registry_validation_report_after_second_seed.json", errors)
    registry_status = load_json(OUTPUT_ROOT / "external_candidate_registry_status_after_second_seed.json", errors)
    protocol = load_json(OUTPUT_ROOT / "prospective_matched_null_memory_protocol_carry_forward.json", errors)
    prereg = load_json(OUTPUT_ROOT / "matched_null_experiment_preregistration_v2_33.json", errors)
    arm_a = load_json(OUTPUT_ROOT / "matched_null_arm_a_memory_enabled_plan.json", errors)
    arm_b = load_json(OUTPUT_ROOT / "matched_null_arm_b_memory_disabled_plan.json", errors)
    memory_eval = load_json(OUTPUT_ROOT / "memory_lift_claim_evaluation.json", errors)
    budget = load_json(OUTPUT_ROOT / "telomeric_budget_policy.json", errors)
    reversal = load_json(OUTPUT_ROOT / "micro_reversal_policy.json", errors)
    roadmap = load_json(OUTPUT_ROOT / "roadmap_carry_forward_check_v2_33.json", errors)
    resolution = load_json(OUTPUT_ROOT / "resolution_depth_diagnostic_v2_33.json", errors)
    public_language = load_json(OUTPUT_ROOT / "public_language_audit.json", errors)
    ledger = load_json(OUTPUT_ROOT / "proof_obligations_ledger.json", errors)
    claim = load_json(OUTPUT_ROOT / "claim_boundary_v2_33.json", errors)

    expect(official.get("status") == "PASS", errors, "v2.33 official artifact verification not PASS")
    expect(official.get("manual_artifact_boundary") == "PASS", errors, "v2.33 manual artifact boundary not PASS")
    expect(official.get("downloaded_by_codex") is False, errors, "v2.33 artifact must be manually provided")
    expect(official.get("local_artifact_path_outside_git") is True, errors, "v2.33 artifact path must be outside Git worktree")
    expect(official.get("artifact_name") == EXPECTED_V233_ARTIFACT_NAME, errors, "v2.33 artifact name mismatch")
    expect(official.get("workflow_run_id") == EXPECTED_V233_RUN, errors, "v2.33 workflow run mismatch")
    expect(official.get("artifact_id") == EXPECTED_V233_ARTIFACT_ID, errors, "v2.33 artifact ID mismatch")
    expect(official.get("head_sha") == EXPECTED_V233_HEAD, errors, "v2.33 artifact head SHA mismatch")
    expect(official.get("zip_size_bytes") == EXPECTED_V233_SIZE, errors, "v2.33 artifact size mismatch")
    expect(official.get("zip_sha256") == EXPECTED_V233_SHA, errors, "v2.33 artifact SHA mismatch")
    expect(official.get("entry_count") == EXPECTED_V233_ENTRIES, errors, "v2.33 artifact entry count mismatch")
    expect(official.get("safe_path_status") == "PASS", errors, "v2.33 artifact safe path status mismatch")
    expect(official.get("unsafe_path_count") == 0, errors, "v2.33 artifact unsafe path count mismatch")
    expect(official.get("duplicate_path_count") == 0, errors, "v2.33 artifact duplicate path count mismatch")
    expect(official.get("internal_manifest_checked") == EXPECTED_V233_MANIFEST_CHECKED, errors, "v2.33 internal manifest count mismatch")
    expect(official.get("internal_manifest_missing") == 0, errors, "v2.33 internal manifest missing entries")
    expect(official.get("internal_manifest_malformed") == 0, errors, "v2.33 internal manifest malformed entries")
    expect(official.get("internal_manifest_failures") == 0, errors, "v2.33 internal manifest hash failures")
    expect(official.get("internal_manifest_status") == "PASS", errors, "v2.33 internal manifest status mismatch")
    expect(official.get("output_manifest_coverage") == "PASS", errors, "v2.33 output manifest coverage mismatch")
    expect(official.get("non_archive_outputs_ingested_count") == EXPECTED_V233_MANIFEST_CHECKED, errors, "v2.33 ingested output count mismatch")
    official_cf = official.get("carry_forward") if isinstance(official.get("carry_forward"), dict) else {}
    expect(official_cf.get("v2_33_audit_status") == "PASS", errors, "v2.33 official audit carry-forward not PASS")
    expect(official_cf.get("regression_audit_status") == "PASS", errors, "v2.33 official regression carry-forward not PASS")
    expect(official_cf.get("public_language_audit_status") == "PASS", errors, "v2.33 official public language carry-forward not PASS")
    expect(official_cf.get("first_scoreable_episode_carry_forward_status") == "PASS", errors, "v2.33 official first episode carry-forward not PASS")
    expect(official_cf.get("scoreable_external_repair_episode_count") == 1, errors, "v2.33 official scoreable count mismatch")
    expect(official_cf.get("selected_candidate_id") == FIRST_CANDIDATE, errors, "v2.33 official selected candidate mismatch")
    expect(official_cf.get("reviewed_valid_candidate_count_after_run") == 1, errors, "v2.33 official reviewed count mismatch")
    expect(official_cf.get("second_seed_present") is False, errors, "v2.33 official second seed presence mismatch")
    expect(official_cf.get("second_seed_verification_status") == "not_run_seed_absent", errors, "v2.33 official seed verification mismatch")
    expect(official_cf.get("second_seed_registry_merge_status") == "not_run_seed_absent", errors, "v2.33 official seed merge mismatch")
    expect(official_cf.get("candidate2_discovery_packet_status") == "PASS", errors, "v2.33 official discovery packet not PASS")
    expect(official_cf.get("candidate2_seed_template_status") == "PASS", errors, "v2.33 official seed template not PASS")
    expect(official_cf.get("candidate2_external_helper_prompt_status") == "PASS", errors, "v2.33 official external helper prompt not PASS")
    expect(official_cf.get("matched_null_experiment_attempted") is False, errors, "v2.33 official matched-null attempted mismatch")
    expect(official_cf.get("arm_a_memory_enabled_status") == "planned_not_run_no_seed", errors, "v2.33 official Arm A status mismatch")
    expect(official_cf.get("arm_b_memory_disabled_status") == "planned_not_run_no_seed", errors, "v2.33 official Arm B status mismatch")
    expect(official_cf.get("arm_a_patch_generated") is False, errors, "v2.33 official Arm A patch flag mismatch")
    expect(official_cf.get("arm_b_patch_generated") is False, errors, "v2.33 official Arm B patch flag mismatch")
    expect(official_cf.get("arm_a_target_validation_status") == "not_run_no_seed", errors, "v2.33 official Arm A target status mismatch")
    expect(official_cf.get("arm_b_target_validation_status") == "not_run_no_seed", errors, "v2.33 official Arm B target status mismatch")
    expect(official_cf.get("arm_a_duplicate_replay_status") == "not_run_no_seed", errors, "v2.33 official Arm A replay status mismatch")
    expect(official_cf.get("arm_b_duplicate_replay_status") == "not_run_no_seed", errors, "v2.33 official Arm B replay status mismatch")
    expect(official_cf.get("matched_null_separation_score") is None, errors, "v2.33 official separation score should be absent")
    expect(official_cf.get("preliminary_single_candidate_memory_lift_evidence") is False, errors, "v2.33 official preliminary memory evidence mismatch")
    expect(official_cf.get("full_scoring") == "NOT_RUN/disallowed", errors, "v2.33 official full scoring mismatch")
    expect(official_cf.get("memory_lift_status") == "undemonstrated", errors, "v2.33 official memory-lift mismatch")
    expect(official_cf.get("self_maintaining_software_status") == "false/not_demonstrated", errors, "v2.33 official self-maintaining mismatch")
    expect(official_cf.get("exact_blocker") == BLOCKER, errors, "v2.33 official blocker mismatch")
    expect(official_cf.get("v2_34_seed_verification_workbench_recommendation_carry_forward_status") == "PASS", errors, "v2.34 recommendation carry-forward not PASS")

    expect(v232.get("status") == "PASS", errors, "v2.32 official ingest verification not PASS")
    expect(v232.get("zip_sha256") == EXPECTED_V232_SHA, errors, "v2.32 artifact SHA mismatch")
    expect(v232.get("workflow_run_id") == EXPECTED_V232_RUN, errors, "v2.32 workflow run mismatch")
    expect(v232.get("artifact_id") == EXPECTED_V232_ARTIFACT_ID, errors, "v2.32 artifact ID mismatch")
    expect(v232.get("manual_artifact_boundary") == "PASS", errors, "v2.32 manual artifact boundary not PASS")
    expect(v232.get("downloaded_by_codex") is False, errors, "v2.32 artifact must be manually provided")
    v232_cf = v232.get("carry_forward") if isinstance(v232.get("carry_forward"), dict) else {}
    expect(v232_cf.get("v2_32_audit_status") == "PASS", errors, "v2.32 audit carry-forward not PASS")
    expect(v232_cf.get("regression_audit_status") == "PASS", errors, "v2.32 regression carry-forward not PASS")
    expect(v232_cf.get("prospective_matched_null_memory_protocol_status") == "PASS", errors, "v2.32 matched-null protocol carry-forward not PASS")

    expect(results.get("status") == "blocked", errors, "v2.33 no-seed status must be blocked")
    expect(results.get("second_seed_present") is False, errors, "second seed must be absent")
    expect(results.get("second_seed_verification_status") == "not_run_seed_absent", errors, "second seed verification status mismatch")
    expect(results.get("second_seed_registry_merge_status") == "not_run_seed_absent", errors, "second seed merge status mismatch")
    expect(results.get("candidate2_discovery_packet_status") == "PASS", errors, "discovery packet status mismatch")
    expect(results.get("candidate2_seed_template_status") == "PASS", errors, "seed template status mismatch")
    expect(results.get("candidate2_external_helper_prompt_status") == "PASS", errors, "external helper prompt status mismatch")
    expect(results.get("matched_null_experiment_attempted") is False, errors, "matched-null experiment must not be attempted")
    expect(results.get("arm_a_memory_enabled_status") == "planned_not_run_no_seed", errors, "Arm A status mismatch")
    expect(results.get("arm_b_memory_disabled_status") == "planned_not_run_no_seed", errors, "Arm B status mismatch")
    expect(results.get("arm_a_patch_generated") is False, errors, "Arm A patch flag mismatch")
    expect(results.get("arm_b_patch_generated") is False, errors, "Arm B patch flag mismatch")
    expect(results.get("preliminary_single_candidate_memory_lift_evidence") is False, errors, "preliminary memory evidence must be false")
    expect(results.get("full_scoring") == "NOT_RUN/disallowed", errors, "full scoring status mismatch")
    expect(results.get("memory_lift_status") == "undemonstrated", errors, "memory lift status mismatch")
    expect(results.get("self_maintaining_software_status") == "false/not_demonstrated", errors, "self-maintaining status mismatch")
    expect(results.get("exact_blocker") == BLOCKER, errors, "v2.33 blocker mismatch")

    expect(first.get("status") == "PASS", errors, "first scoreable carry-forward status mismatch")
    expect(first.get("candidate_id") == FIRST_CANDIDATE, errors, "first scoreable candidate mismatch")
    expect(first.get("scoreable_external_repair_episode_count") == 1, errors, "first scoreable count mismatch")
    expect(first.get("selected_candidate_positive_memory_only") is False, errors, "first scoreable memory-only flag mismatch")
    expect(presence.get("status") == "BLOCK", errors, "presence check must block")
    expect(presence.get("external_clone_attempted") is False, errors, "external clone must not be attempted")
    expect(presence.get("live_issue_search_attempted") is False, errors, "live issue search must not be attempted")
    expect(presence.get("candidate2_selected") is False, errors, "candidate #2 must not be selected")
    expect(schema.get("status") == "not_run_seed_absent", errors, "schema validation must not run when seed absent")
    expect(forbidden.get("status") == "PASS", errors, "forbidden source guard status mismatch")
    for key in [
        "live_issue_search_used_to_create_candidate",
        "candidate_fabricated",
        "fixed_commit_contents_read",
        "later_commit_contents_read",
        "fixed_diff_computed",
        "pr_patch_content_used",
        "gold_patch_used",
        "hidden_label_used",
        "benchmark_future_test_used",
        "synthetic_or_generated_test_used",
        "bugsinpy_active_candidate_acquisition_used",
    ]:
        expect(forbidden.get(key) is False, errors, f"forbidden source guard failed for {key}")
    expect(merge.get("status") == "not_run_seed_absent", errors, "registry merge must not run")
    expect(merge.get("registry_updated") is False, errors, "registry must not be updated")
    expect(registry_report.get("registry_validation_status") == "PASS", errors, "embedded registry validation failed")
    expect(registry_status.get("status") == "PASS", errors, "registry status mismatch")
    expect(registry_status.get("registry_candidate_count_after_run") == 1, errors, "registry candidate count mismatch")
    expect(registry_status.get("reviewed_valid_candidate_count_after_run") == 1, errors, "reviewed candidate count mismatch")
    expect(registry_status.get("second_seed_merged") is False, errors, "second seed must not merge")

    expect(protocol.get("status") == "PASS", errors, "protocol carry-forward status mismatch")
    expect(protocol.get("experiment_allowed_only_after_seed_verifies") is True, errors, "protocol seed precondition missing")
    expect(prereg.get("status") == "PASS", errors, "experiment preregistration status mismatch")
    expect(prereg.get("experiment_attempted") is False, errors, "experiment attempted flag mismatch")
    expect(prereg.get("candidate2_seed_required_before_repair") is True, errors, "candidate2 seed requirement missing")
    expect(arm_a.get("status") == "planned_not_run_no_seed", errors, "Arm A plan status mismatch")
    expect(arm_a.get("may_read_failure_memory_weight_ledger") is True, errors, "Arm A memory policy mismatch")
    expect(arm_a.get("candidate2_successful_patch_bytes_forbidden") is True, errors, "Arm A candidate2 patch byte rule mismatch")
    expect(arm_b.get("status") == "planned_not_run_no_seed", errors, "Arm B plan status mismatch")
    expect(arm_b.get("may_read_failure_memory_weight_ledger") is False, errors, "Arm B ledger rule mismatch")
    expect(arm_b.get("may_read_successful_patch_bytes_from_any_candidate") is False, errors, "Arm B successful patch byte rule mismatch")
    expect(memory_eval.get("preliminary_single_candidate_memory_lift_evidence") is False, errors, "memory lift evidence must be false")
    expect(memory_eval.get("memory_lift_status") == "undemonstrated", errors, "memory eval status mismatch")
    expect(memory_eval.get("matched_null_separation_score_computed") is False, errors, "score must not be computed")
    expect(budget.get("status") == "PASS", errors, "budget policy status mismatch")
    expect(budget.get("default_total_budget_per_arm") == 12, errors, "budget total mismatch")
    expect(budget.get("silent_budget_reset_allowed") is False, errors, "budget reset rule mismatch")
    expect(budget.get("budget_exhaustion_blocker") == "telomeric_budget_exhausted", errors, "budget blocker mismatch")
    expect(reversal.get("status") == "PASS", errors, "micro-reversal policy status mismatch")
    expect(reversal.get("max_micro_reversals_per_arm") == 1, errors, "micro-reversal cap mismatch")
    expect(reversal.get("same_allowance_for_both_arms") is True, errors, "micro-reversal arm equality mismatch")
    expect(roadmap.get("status") == "PASS", errors, "roadmap carry-forward status mismatch")
    expect(resolution.get("status") == "PASS", errors, "resolution diagnostic status mismatch")
    expect(resolution.get("discovery_packet_status") == "PASS", errors, "resolution discovery status mismatch")
    expect(public_language.get("status") == "PASS", errors, "public language audit failed")
    expect(public_language.get("exact_match_count") == 0, errors, "public language exact-match count mismatch")
    audit_proof_ledger(ledger, errors)

    expect(claim.get("status") == "PASS", errors, "claim boundary status mismatch")
    expect(claim.get("current_protocol_version") == "v2.13", errors, "current protocol mismatch")
    expect(claim.get("v2_32_promoted_to_current") is False, errors, "v2.32 must not promote")
    expect(claim.get("v2_33_promoted_to_current") is False, errors, "v2.33 must not promote")
    expect(claim.get("v2_34_started") is False, errors, "v2.34 must not start")
    for key in [
        "second_seed_present",
        "matched_null_experiment_attempted",
        "candidate2_repair_attempted",
        "patch_generated",
        "s_engine_invoked",
        "external_clone_attempted",
        "live_issue_search_used_to_create_candidate",
        "candidate_fabricated",
        "full_scoring_allowed",
        "preliminary_single_candidate_memory_lift_evidence",
        "pysnooper1_reopened",
        "pysnooper2_pursued",
        "ansible_candidate_selected",
        "bugsinpy_active_candidate_acquisition_used",
    ]:
        expect(claim.get(key) is False, errors, f"claim boundary failed for {key}")
    expect(claim.get("exact_blocker") == BLOCKER, errors, "claim blocker mismatch")


def audit_public_docs(errors: list[str]) -> None:
    sections = [
        (README_PATH, "v2.33 candidate #2 seed intake and matched-null experiment status", "README v2.33 section missing"),
        (ROADMAP_PATH, "v2.33 Candidate #2 Seed Intake and Matched-Null Experiment Status", "roadmap v2.33 section missing"),
        (CAPABILITY_PLAN_PATH, "v2.33 candidate #2 status", "capability plan v2.33 section missing"),
        (RESOLUTION_DOC_PATH, "v2.33 candidate #2 status", "resolution doc v2.33 section missing"),
        (SHAREABLE_PATH, "v2.33 Candidate #2 Seed Intake and Matched-Null Experiment Status", "shareable v2.33 section missing"),
    ]
    for path, heading, message in sections:
        expect(section_present(path, heading), errors, message)
        text = section_text(path, heading)
        hits = [term for term in hidden_public_terms() if term in text]
        expect(not hits, errors, f"blocked public-facing term in {path.relative_to(REPO_ROOT).as_posix()}: {hits}")


def main() -> int:
    errors: list[str] = []
    checked, manifest_entries = verify_manifest(errors)
    audit_outputs(errors, manifest_entries)
    audit_registry_and_episode_counts(errors)
    audit_public_docs(errors)

    run_python(["scripts/validate_external_candidate_registry.py", "--no-write"], errors, "registry validation")
    run_python(["scripts/audit_v2_32_second_external_candidate_seed_and_memory_protocol_lane.py"], errors, "v2.32 nested regression audit")
    run_python(["scripts/controllergate_audit.py", "--protocol", "current"], errors, "current protocol audit")
    run_python(["scripts/controllergate_run.py", "--protocol", "current", "--dry-run"], errors, "current protocol dry run")

    if errors:
        print("v2.33 audit FAIL")
        for error in errors:
            print(f"- {error}")
        return 1

    results = load_json(OUTPUT_ROOT / "campaign_results.json", [])
    print("v2.33 audit PASS")
    print(f"v2.33 manifest entries checked: {checked}")
    print("v2.32 nested regression audit status=PASS")
    for key in [
        "first_scoreable_episode_carry_forward_status",
        "second_seed_present",
        "second_seed_verification_status",
        "candidate2_discovery_packet_status",
        "candidate2_seed_template_status",
        "candidate2_external_helper_prompt_status",
        "matched_null_experiment_attempted",
        "arm_a_memory_enabled_status",
        "arm_b_memory_disabled_status",
        "preliminary_single_candidate_memory_lift_evidence",
        "full_scoring",
        "memory_lift_status",
        "self_maintaining_software_status",
        "exact_blocker",
    ]:
        print(f"{key}={results.get(key)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
