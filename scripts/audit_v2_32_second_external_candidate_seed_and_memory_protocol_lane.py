#!/usr/bin/env python3
"""Audit v2.32 second-seed intake and prospective matched-null protocol evidence."""

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
CAMPAIGN_ID = "v2_32_second_external_candidate_seed_and_memory_protocol_lane"
OUTPUT_ROOT = REPO_ROOT / "outputs" / CAMPAIGN_ID
V231_ROOT = REPO_ROOT / "outputs" / "v2_31_scoreable_repair_episode_consolidation_lane"
SEED_PATH = REPO_ROOT / "inputs" / "external_candidate_seed_draft_v2_32.json"
README_PATH = REPO_ROOT / "README.md"
ROADMAP_PATH = REPO_ROOT / "docs" / "non_ansible_capability_roadmap.md"
CAPABILITY_PLAN_PATH = REPO_ROOT / "docs" / "structural_repair_capability_plan.md"
RESOLUTION_DOC_PATH = REPO_ROOT / "docs" / ("controllergate_" + "t" + "ld" + "_resolution_map.md")
SHAREABLE_PATH = REPO_ROOT / "controllergate_v1_7_beta" / "reports" / "critic_review_package" / "shareable_summary.md"
EXTERNAL_REGISTRY_PATH = REPO_ROOT / "configs" / "external_candidate_registry.json"
EPISODE_REGISTRY_PATH = REPO_ROOT / "configs" / "external_repair_episode_registry.json"

EXPECTED = {
    "first_candidate_id": "py_bugger_issue_65",
    "first_patch_sha256": "02ada076e824bb703bc02d1c33f75f51eb4db4539a5aac8e4f5fa3fedd4972ee",
    "v2_31_artifact_sha256": "dcc798015f920e737b893121175e97c1ba04d1c26ef78bf7b691794817277766",
    "v2_31_workflow_run_id": 28277667635,
    "v2_31_artifact_id": 7920785556,
    "v2_32_artifact_sha256": "4fa00924210ffa95b6d3c3104457350502bbda2cf7bd348ea92cc2a3f736609e",
    "v2_32_artifact_size_bytes": 74561,
    "v2_32_artifact_entry_count": 39,
    "v2_32_internal_manifest_checked": 27,
    "v2_32_workflow_run_id": 28284054288,
    "v2_32_artifact_id": 7922901616,
    "v2_32_artifact_name": "v2_32_second_external_candidate_seed_and_memory_protocol_lane_artifacts",
    "v2_32_head_sha": "62d7b076399b344d6eccb1ef582d8b396f80e94f",
    "no_seed_blocker": "blocked_no_second_external_candidate_seed_draft_provided",
}

REQUIRED_FILES = [
    "campaign_summary.md",
    "campaign_results.json",
    "v2_32_official_artifact_verification.json",
    "v2_31_artifact_ingest_verification.json",
    "artifact_repo_snapshot_comparison.json",
    "first_scoreable_episode_carry_forward.json",
    "external_repair_episode_registry_carry_forward.json",
    "failure_memory_weight_ledger_carry_forward.json",
    "second_seed_presence_check.json",
    "second_seed_schema_validation.json",
    "second_seed_path_policy_check.json",
    "second_seed_forbidden_source_guard.json",
    "second_seed_registry_merge_report.json",
    "external_candidate_registry_validation_report_after_second_seed.json",
    "external_candidate_registry_status_after_second_seed.json",
    "prospective_matched_null_memory_protocol_v2_32.json",
    "matched_null_baseline_policy_v2_32.json",
    "memory_enabled_arm_policy_v2_32.json",
    "memory_disabled_arm_policy_v2_32.json",
    "matched_null_separation_score_definition_v2_32.json",
    "seed_constraint_revalidation_policy_v2_32.json",
    "no_overreach_regression_policy_v2_32.json",
    "candidate_2_repair_readiness_status.json",
    "roadmap_carry_forward_check_v2_32.json",
    "resolution_depth_diagnostic_v2_32.json",
    "public_language_audit.json",
    "proof_obligations_ledger.json",
    "claim_boundary_v2_32.json",
    "SHA256SUMS.txt",
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


def verify_manifest(errors: list[str]) -> int:
    manifest = OUTPUT_ROOT / "SHA256SUMS.txt"
    if not manifest.is_file():
        errors.append("missing v2.32 SHA256SUMS.txt")
        return 0
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
    return checked


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


def audit_registry_and_episode_counts(errors: list[str]) -> None:
    registry_validation = registry_validator.validate_registry()
    expect(registry_validation.get("registry_validation_status") == "PASS", errors, "fresh external registry validation failed")
    expect(registry_validation.get("valid_reviewed_candidate_count") == 1, errors, "reviewed valid candidate count must remain 1")
    registry = load_json(EXTERNAL_REGISTRY_PATH, errors)
    candidates = registry.get("candidates")
    expect(isinstance(candidates, list), errors, "external registry candidates missing")
    if isinstance(candidates, list):
        candidate_ids = [item.get("candidate_id") for item in candidates if isinstance(item, dict)]
        expect(candidate_ids.count(EXPECTED["first_candidate_id"]) == 1, errors, "first candidate missing or duplicated")
        expect(len(candidate_ids) == 1, errors, "v2.32 no-seed run must not add candidate #2")
    episode_registry = load_json(EPISODE_REGISTRY_PATH, errors)
    episodes = episode_registry.get("episodes")
    expect(isinstance(episodes, list), errors, "episode registry episodes missing")
    if isinstance(episodes, list):
        scoreable = [item for item in episodes if isinstance(item, dict) and item.get("scoreable") is True]
        expect(len(scoreable) == 1, errors, "scoreable external repair episode count must remain 1")
        if scoreable:
            expect(scoreable[0].get("candidate_id") == EXPECTED["first_candidate_id"], errors, "scoreable episode candidate mismatch")


def audit_outputs(errors: list[str]) -> None:
    for rel in REQUIRED_FILES:
        expect((OUTPUT_ROOT / rel).is_file(), errors, f"missing required output {rel}")
    seed_present = SEED_PATH.is_file()
    if not seed_present:
        for rel in SEED_PRESENT_ONLY_FILES:
            expect(not (OUTPUT_ROOT / rel).exists(), errors, f"seed-present-only output must not exist when seed absent: {rel}")

    official = load_json(OUTPUT_ROOT / "v2_32_official_artifact_verification.json", errors)
    v231 = load_json(OUTPUT_ROOT / "v2_31_artifact_ingest_verification.json", errors)
    results = load_json(OUTPUT_ROOT / "campaign_results.json", errors)
    first_episode = load_json(OUTPUT_ROOT / "first_scoreable_episode_carry_forward.json", errors)
    episode_carry = load_json(OUTPUT_ROOT / "external_repair_episode_registry_carry_forward.json", errors)
    ledger_carry = load_json(OUTPUT_ROOT / "failure_memory_weight_ledger_carry_forward.json", errors)
    presence = load_json(OUTPUT_ROOT / "second_seed_presence_check.json", errors)
    schema = load_json(OUTPUT_ROOT / "second_seed_schema_validation.json", errors)
    path_policy = load_json(OUTPUT_ROOT / "second_seed_path_policy_check.json", errors)
    forbidden = load_json(OUTPUT_ROOT / "second_seed_forbidden_source_guard.json", errors)
    merge = load_json(OUTPUT_ROOT / "second_seed_registry_merge_report.json", errors)
    registry_report = load_json(OUTPUT_ROOT / "external_candidate_registry_validation_report_after_second_seed.json", errors)
    registry_status = load_json(OUTPUT_ROOT / "external_candidate_registry_status_after_second_seed.json", errors)
    protocol = load_json(OUTPUT_ROOT / "prospective_matched_null_memory_protocol_v2_32.json", errors)
    baseline = load_json(OUTPUT_ROOT / "matched_null_baseline_policy_v2_32.json", errors)
    memory_enabled = load_json(OUTPUT_ROOT / "memory_enabled_arm_policy_v2_32.json", errors)
    memory_disabled = load_json(OUTPUT_ROOT / "memory_disabled_arm_policy_v2_32.json", errors)
    score_def = load_json(OUTPUT_ROOT / "matched_null_separation_score_definition_v2_32.json", errors)
    seed_revalidation = load_json(OUTPUT_ROOT / "seed_constraint_revalidation_policy_v2_32.json", errors)
    no_overreach = load_json(OUTPUT_ROOT / "no_overreach_regression_policy_v2_32.json", errors)
    readiness = load_json(OUTPUT_ROOT / "candidate_2_repair_readiness_status.json", errors)
    roadmap = load_json(OUTPUT_ROOT / "roadmap_carry_forward_check_v2_32.json", errors)
    resolution = load_json(OUTPUT_ROOT / "resolution_depth_diagnostic_v2_32.json", errors)
    public_language = load_json(OUTPUT_ROOT / "public_language_audit.json", errors)
    ledger = load_json(OUTPUT_ROOT / "proof_obligations_ledger.json", errors)
    claim = load_json(OUTPUT_ROOT / "claim_boundary_v2_32.json", errors)

    expect(official.get("status") == "PASS", errors, "v2.32 official artifact verification not PASS")
    expect(official.get("manual_artifact_boundary") == "PASS", errors, "v2.32 manual artifact boundary not PASS")
    expect(official.get("downloaded_by_codex") is False, errors, "v2.32 artifact must be manually provided")
    expect(official.get("local_artifact_path_outside_git") is True, errors, "v2.32 artifact path must be outside Git worktree")
    expect(official.get("artifact_name") == EXPECTED["v2_32_artifact_name"], errors, "v2.32 artifact name mismatch")
    expect(official.get("workflow_run_id") == EXPECTED["v2_32_workflow_run_id"], errors, "v2.32 workflow run mismatch")
    expect(official.get("artifact_id") == EXPECTED["v2_32_artifact_id"], errors, "v2.32 artifact ID mismatch")
    expect(official.get("head_sha") == EXPECTED["v2_32_head_sha"], errors, "v2.32 artifact head SHA mismatch")
    expect(official.get("zip_size_bytes") == EXPECTED["v2_32_artifact_size_bytes"], errors, "v2.32 artifact size mismatch")
    expect(official.get("zip_sha256") == EXPECTED["v2_32_artifact_sha256"], errors, "v2.32 artifact SHA mismatch")
    expect(official.get("entry_count") == EXPECTED["v2_32_artifact_entry_count"], errors, "v2.32 artifact entry count mismatch")
    expect(official.get("safe_path_status") == "PASS", errors, "v2.32 artifact safe path status mismatch")
    expect(official.get("unsafe_path_count") == 0, errors, "v2.32 artifact unsafe path count mismatch")
    expect(official.get("duplicate_path_count") == 0, errors, "v2.32 artifact duplicate path count mismatch")
    expect(official.get("internal_manifest_checked") == EXPECTED["v2_32_internal_manifest_checked"], errors, "v2.32 internal manifest count mismatch")
    expect(official.get("internal_manifest_missing") == 0, errors, "v2.32 internal manifest missing entries")
    expect(official.get("internal_manifest_malformed") == 0, errors, "v2.32 internal manifest malformed entries")
    expect(official.get("internal_manifest_failures") == 0, errors, "v2.32 internal manifest hash failures")
    expect(official.get("internal_manifest_status") == "PASS", errors, "v2.32 internal manifest status mismatch")
    expect(official.get("output_manifest_coverage") == "PASS", errors, "v2.32 output manifest coverage mismatch")
    expect(official.get("non_archive_outputs_ingested_count") == EXPECTED["v2_32_internal_manifest_checked"], errors, "v2.32 ingested output count mismatch")
    official_cf = official.get("carry_forward") if isinstance(official.get("carry_forward"), dict) else {}
    expect(official_cf.get("v2_32_audit_status") == "PASS", errors, "v2.32 official audit carry-forward not PASS")
    expect(official_cf.get("regression_audit_status") == "PASS", errors, "v2.32 official regression carry-forward not PASS")
    expect(official_cf.get("public_language_audit_status") == "PASS", errors, "v2.32 official public language carry-forward not PASS")
    expect(official_cf.get("first_scoreable_episode_carry_forward_status") == "PASS", errors, "v2.32 official first episode carry-forward not PASS")
    expect(official_cf.get("scoreable_external_repair_episode_count") == 1, errors, "v2.32 official scoreable count mismatch")
    expect(official_cf.get("selected_candidate_id") == EXPECTED["first_candidate_id"], errors, "v2.32 official selected candidate mismatch")
    expect(official_cf.get("reviewed_valid_candidate_count_after_run") == 1, errors, "v2.32 official reviewed count mismatch")
    expect(official_cf.get("second_seed_present") is False, errors, "v2.32 official second seed presence mismatch")
    expect(official_cf.get("second_seed_verification_status") == "not_run_seed_absent", errors, "v2.32 official second seed verification mismatch")
    expect(official_cf.get("second_seed_registry_merge_status") == "not_run_seed_absent", errors, "v2.32 official second seed merge mismatch")
    expect(official_cf.get("prospective_matched_null_memory_protocol_status") == "PASS", errors, "v2.32 official matched-null protocol not PASS")
    expect(official_cf.get("matched_null_baseline_policy_status") == "PASS", errors, "v2.32 official baseline policy not PASS")
    expect(official_cf.get("memory_enabled_arm_policy_status") == "PASS", errors, "v2.32 official memory-enabled policy not PASS")
    expect(official_cf.get("memory_disabled_arm_policy_status") == "PASS", errors, "v2.32 official memory-disabled policy not PASS")
    expect(official_cf.get("matched_null_separation_score_definition_status") == "PASS", errors, "v2.32 official score definition not PASS")
    expect(official_cf.get("seed_constraint_revalidation_policy_status") == "PASS", errors, "v2.32 official seed revalidation policy not PASS")
    expect(official_cf.get("no_overreach_regression_policy_status") == "PASS", errors, "v2.32 official no-overreach policy not PASS")
    expect(official_cf.get("candidate_2_repair_attempted") is False, errors, "v2.32 official candidate #2 repair mismatch")
    expect(official_cf.get("patch_generated") is False, errors, "v2.32 official patch flag mismatch")
    expect(official_cf.get("full_scoring") == "NOT_RUN/disallowed", errors, "v2.32 official full scoring mismatch")
    expect(official_cf.get("memory_lift_status") == "undemonstrated", errors, "v2.32 official memory-lift mismatch")
    expect(official_cf.get("self_maintaining_software_status") == "false/not_demonstrated", errors, "v2.32 official self-maintaining mismatch")
    expect(official_cf.get("exact_blocker") == EXPECTED["no_seed_blocker"], errors, "v2.32 official blocker mismatch")
    expect(official_cf.get("v2_33_candidate2_memory_experiment_recommendation_carry_forward_status") == "PASS", errors, "v2.33 recommendation carry-forward not PASS")

    expect(v231.get("status") == "PASS", errors, "v2.31 artifact ingest verification not PASS")
    expect(v231.get("zip_sha256") == EXPECTED["v2_31_artifact_sha256"], errors, "v2.31 artifact SHA mismatch")
    expect(v231.get("workflow_run_id") == EXPECTED["v2_31_workflow_run_id"], errors, "v2.31 workflow run mismatch")
    expect(v231.get("artifact_id") == EXPECTED["v2_31_artifact_id"], errors, "v2.31 artifact ID mismatch")

    expect(results.get("status") == "blocked", errors, "v2.32 no-seed status must be blocked")
    expect(results.get("second_seed_present") is False, errors, "second seed must be absent for this run")
    expect(results.get("exact_blocker") == EXPECTED["no_seed_blocker"], errors, "v2.32 exact blocker mismatch")
    expect(results.get("first_scoreable_episode_carry_forward_status") == "PASS", errors, "first scoreable carry-forward failed")
    expect(results.get("reviewed_valid_candidate_count_after_run") == 1, errors, "reviewed count after run must remain 1")
    expect(results.get("candidate_2_repair_attempted") is False, errors, "candidate #2 repair must not be attempted")
    expect(results.get("patch_generated") is False, errors, "patch must not be generated")
    expect(results.get("target_validation_after_patch_run") is False, errors, "target validation after patch must not run")
    expect(results.get("external_clone_attempted") is False, errors, "external clone must not be attempted")
    expect(results.get("s_engine_invoked") is False, errors, "repair engine must not be invoked")
    expect(results.get("current_protocol_version") == "v2.13", errors, "current protocol must remain v2.13")
    expect(results.get("full_scoring") == "NOT_RUN/disallowed", errors, "full scoring boundary mismatch")
    expect(results.get("memory_lift_status") == "undemonstrated", errors, "memory lift must remain undemonstrated")
    expect(results.get("self_maintaining_software_status") == "false/not_demonstrated", errors, "self-maintaining claim boundary mismatch")

    expect(first_episode.get("status") == "PASS", errors, "first episode carry-forward status mismatch")
    expect(first_episode.get("candidate_id") == EXPECTED["first_candidate_id"], errors, "first episode candidate mismatch")
    expect(first_episode.get("scoreable_external_repair_episode_count") == 1, errors, "first episode count mismatch")
    expect(first_episode.get("selected_candidate_scoreable") is True, errors, "first episode scoreable flag mismatch")
    expect(first_episode.get("selected_candidate_positive_memory_only") is False, errors, "first episode memory-only flag mismatch")
    expect(first_episode.get("patch_sha256") == EXPECTED["first_patch_sha256"], errors, "first episode patch SHA mismatch")
    expect(first_episode.get("target_validation_carry_forward_status") == "PASS", errors, "target validation carry-forward mismatch")
    expect(first_episode.get("duplicate_replay_carry_forward_status") == "PASS", errors, "duplicate replay carry-forward mismatch")
    expect(first_episode.get("observed_reliability") == 1.0, errors, "replay reliability mismatch")

    expect(episode_carry.get("status") == "PASS", errors, "episode registry carry-forward status mismatch")
    expect(episode_carry.get("scoreable_external_repair_episode_count") == 1, errors, "episode registry count mismatch")
    expect(episode_carry.get("first_candidate_id") == EXPECTED["first_candidate_id"], errors, "episode registry first candidate mismatch")
    expect(ledger_carry.get("status") == "PASS", errors, "failure ledger carry-forward status mismatch")
    expect(ledger_carry.get("diagnostic_only") is True, errors, "failure ledger must remain diagnostic-only")
    expect(ledger_carry.get("memory_lift_claimed") is False, errors, "failure ledger must not claim memory lift")

    expect(presence.get("status") == "BLOCK", errors, "no-seed presence check must block")
    expect(presence.get("seed_present") is False, errors, "presence check seed flag mismatch")
    expect(presence.get("external_clone_attempted") is False, errors, "presence check external clone mismatch")
    expect(presence.get("live_issue_search_attempted") is False, errors, "live issue search must not run")
    expect(presence.get("candidate_selected") is False, errors, "candidate must not be selected")
    expect(schema.get("status") == "not_run_seed_absent", errors, "schema validation must not run when seed absent")
    expect(path_policy.get("status") == "PASS", errors, "path policy status mismatch")
    expect(path_policy.get("generated_reproducer_forbidden") is True, errors, "generated reproducer guard missing")
    expect(path_policy.get("external_network_dependency_allowed") is False, errors, "external network guard mismatch")
    expect(forbidden.get("status") == "PASS", errors, "forbidden source guard status mismatch")
    for key in [
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

    expect(merge.get("status") == "not_run_seed_absent", errors, "registry merge must not run when seed absent")
    expect(merge.get("registry_updated") is False, errors, "registry must not be updated by no-seed run")
    expect(merge.get("reviewed_valid_candidate_count_after_run") == 1, errors, "registry merge reviewed count mismatch")
    expect(registry_report.get("registry_validation_status") == "PASS", errors, "embedded registry validation failed")
    expect(registry_report.get("valid_reviewed_candidate_count") == 1, errors, "embedded reviewed count mismatch")
    expect(registry_status.get("status") == "PASS", errors, "registry status after second seed mismatch")
    expect(registry_status.get("registry_candidate_count_after_run") == 1, errors, "registry candidate count after run mismatch")
    expect(registry_status.get("reviewed_valid_candidate_count_after_run") == 1, errors, "registry reviewed count after run mismatch")
    expect(registry_status.get("second_seed_merged") is False, errors, "second seed must not merge")

    expect(protocol.get("status") == "PASS", errors, "matched-null protocol status mismatch")
    expect(protocol.get("future_candidate_requirement"), errors, "future candidate requirement missing")
    expect(protocol.get("claim_boundary", {}).get("memory_lift") == "undemonstrated", errors, "protocol memory-lift boundary mismatch")
    expect(baseline.get("status") == "PASS", errors, "matched-null baseline policy mismatch")
    expect(baseline.get("may_read_failure_memory_weight_ledger") is False, errors, "baseline must not read failure memory ledger")
    expect(baseline.get("may_read_successful_patch_bytes_from_any_candidate") is False, errors, "baseline must not read successful patch bytes")
    expect(memory_enabled.get("status") == "PASS", errors, "memory-enabled policy mismatch")
    expect(memory_enabled.get("may_read_failure_memory_weight_ledger") is True, errors, "memory-enabled arm ledger rule mismatch")
    expect(memory_enabled.get("may_access_candidate_2_fixed_future_gold_data") is False, errors, "memory-enabled forbidden evidence rule mismatch")
    expect(memory_enabled.get("may_access_candidate_2_successful_patch_bytes") is False, errors, "memory-enabled candidate #2 patch byte rule mismatch")
    expect(memory_disabled.get("status") == "PASS", errors, "memory-disabled policy mismatch")
    expect(memory_disabled.get("may_read_failure_memory_weight_ledger") is False, errors, "memory-disabled ledger rule mismatch")
    expect(memory_disabled.get("may_read_successful_patch_bytes") is False, errors, "memory-disabled patch byte rule mismatch")
    expect(score_def.get("status") == "PASS", errors, "score definition status mismatch")
    expect(score_def.get("range") == [0.0, 1.0], errors, "score range mismatch")
    expect(score_def.get("threshold_for_future_claim") == 0.95, errors, "score threshold mismatch")
    expect(score_def.get("threshold_met_in_v2_32") is False, errors, "v2.32 must not meet future threshold")
    expect(score_def.get("future_only") is True, errors, "score definition must be future-only")
    expect(seed_revalidation.get("status") == "PASS", errors, "seed revalidation policy status mismatch")
    expect("semantic_failure_signature" in (seed_revalidation.get("must_match_before_future_patch_generation") or []), errors, "seed revalidation semantic signature guard missing")
    expect(no_overreach.get("status") == "PASS", errors, "no-overreach policy status mismatch")
    expect(readiness.get("status") == "BLOCK", errors, "candidate #2 readiness must be blocked without seed")
    expect(readiness.get("candidate_2_selected") is False, errors, "candidate #2 must not be selected")
    expect(readiness.get("candidate_2_repair_attempted") is False, errors, "candidate #2 repair readiness mismatch")
    expect(readiness.get("patch_generated") is False, errors, "candidate #2 patch flag mismatch")
    expect(readiness.get("exact_blocker") == EXPECTED["no_seed_blocker"], errors, "candidate #2 blocker mismatch")
    expect(roadmap.get("status") == "PASS", errors, "roadmap carry-forward status mismatch")
    expect(resolution.get("status") == "PASS", errors, "resolution diagnostic status mismatch")
    expect(resolution.get("scoreable_external_repair_episode_count") == 1, errors, "resolution scoreable count mismatch")
    expect(resolution.get("reviewed_valid_candidate_count_after_run") == 1, errors, "resolution reviewed count mismatch")
    expect(public_language.get("status") == "PASS", errors, "public language audit failed")
    expect(public_language.get("exact_match_count") == 0, errors, "public language exact-match count mismatch")
    audit_proof_ledger(ledger, errors)

    expect(claim.get("status") == "PASS", errors, "claim boundary status mismatch")
    expect(claim.get("current_protocol_version") == "v2.13", errors, "claim current protocol mismatch")
    expect(claim.get("v2_31_promoted_to_current") is False, errors, "v2.31 must not promote to current")
    expect(claim.get("v2_32_promoted_to_current") is False, errors, "v2.32 must not promote to current")
    expect(claim.get("scoreable_external_repair_episode_count") == 1, errors, "claim scoreable count mismatch")
    expect(claim.get("reviewed_valid_candidate_count_after_run") == 1, errors, "claim reviewed count mismatch")
    expect(claim.get("full_scoring") == "NOT_RUN", errors, "claim full scoring status mismatch")
    expect(claim.get("full_scoring_allowed") is False, errors, "claim full scoring allowed mismatch")
    expect(claim.get("memory_lift_status") == "undemonstrated", errors, "claim memory-lift status mismatch")
    expect(claim.get("self_maintaining_software_status") == "false/not_demonstrated", errors, "claim self-maintaining status mismatch")
    for key in [
        "candidate_2_repair_attempted",
        "patch_generated",
        "target_validation_after_patch_run",
        "positive_memory_only_claimed",
        "pysnooper1_reopened",
        "pysnooper2_pursued",
        "ansible_candidate_selected",
        "bugsinpy_active_candidate_acquisition_used",
        "external_clone_attempted",
        "s_engine_invoked",
    ]:
        expect(claim.get(key) is False, errors, f"claim boundary failed for {key}")


def audit_public_docs(errors: list[str]) -> None:
    sections = [
        (README_PATH, "v2.32 second external candidate seed and matched-null protocol lock", "README v2.32 section missing"),
        (ROADMAP_PATH, "v2.32 Second External Candidate Seed and Matched-Null Protocol Lock", "roadmap v2.32 section missing"),
        (CAPABILITY_PLAN_PATH, "v2.32 protocol lock status", "capability plan v2.32 section missing"),
        (RESOLUTION_DOC_PATH, "v2.32 protocol lock status", "resolution doc v2.32 section missing"),
        (SHAREABLE_PATH, "v2.32 Second External Candidate Seed and Matched-Null Protocol Lock", "shareable v2.32 section missing"),
    ]
    for path, heading, message in sections:
        expect(section_present(path, heading), errors, message)
        text = section_text(path, heading)
        hits = [term for term in hidden_public_terms() if term in text]
        expect(not hits, errors, f"blocked public-facing term in {path.relative_to(REPO_ROOT).as_posix()}: {hits}")


def main() -> int:
    errors: list[str] = []
    checked = verify_manifest(errors)
    audit_outputs(errors)
    audit_registry_and_episode_counts(errors)
    audit_public_docs(errors)

    run_python(["scripts/validate_external_candidate_registry.py", "--no-write"], errors, "registry validation")
    run_python(["scripts/audit_v2_31_scoreable_repair_episode_consolidation_lane.py"], errors, "v2.31 nested regression audit")
    run_python(["scripts/controllergate_audit.py", "--protocol", "current"], errors, "current protocol audit")
    run_python(["scripts/controllergate_run.py", "--protocol", "current", "--dry-run"], errors, "current protocol dry run")

    if errors:
        print("v2.32 audit FAIL")
        for error in errors:
            print(f"- {error}")
        return 1

    results = load_json(OUTPUT_ROOT / "campaign_results.json", [])
    print("v2.32 audit PASS")
    print(f"v2.32 manifest entries checked: {checked}")
    print("v2.31 nested regression audit status=PASS")
    for key in [
        "first_scoreable_episode_carry_forward_status",
        "second_seed_present",
        "second_seed_verification_status",
        "second_seed_registry_merge_status",
        "reviewed_valid_candidate_count_after_run",
        "prospective_matched_null_memory_protocol_status",
        "candidate_2_repair_attempted",
        "patch_generated",
        "full_scoring",
        "memory_lift_status",
        "self_maintaining_software_status",
        "exact_blocker",
    ]:
        print(f"{key}={results.get(key)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
