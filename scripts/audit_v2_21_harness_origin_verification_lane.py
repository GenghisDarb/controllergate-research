#!/usr/bin/env python3
"""Audit v2.21 harness-origin verification lane evidence."""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path, PurePosixPath
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_ROOT = REPO_ROOT / "outputs" / "v2_21_harness_origin_verification_lane"
PIN_CONFIG_PATH = REPO_ROOT / "configs" / "bugsinpy_harness_origin_pins.json"
CAMPAIGN_ID = "v2_21_harness_origin_verification_lane"
PIN_COMMIT = "11c5f1eea954a42132cfd06bf257766a7963e0fd"
BUGGY_REVISION = "e21a31162f4c54be693d8ca8260e42393b39abd3"
PIN_SOURCE_REPO = "https://github.com/soarsmu/BugsInPy.git"
PYSNOOPER_SOURCE_REPO = "https://github.com/cool-RR/PySnooper"
TARGET_TEST = "tests/test_chinese.py"
EXPECTED_HARNESS_MANIFEST_SHA256 = "3706244b4618612fad4681578dd740d1e54dbe9069303072ab7802f656f0e608"
EXPECTED_TOPOLOGY_HASHES = {
    "projects/PySnooper/bugs/1/bug.info": "199b770bd6551117a00f9c7ce2c674d7ddb818e3bb5dc344371340e75e52296e",
    "projects/PySnooper/bugs/1/run_test.sh": "6d24d2d88478e17cefec81f33a1ef5c44cea64321ff46762384c68e219064d0b",
    "projects/PySnooper/bugs/1/setup.sh": "653b7a51d65d7409e319e29d51d5ee2af65d621ad9ef62148e7eacf99e289879",
}

REQUIRED_FILES = [
    "campaign_summary.md",
    "campaign_results.json",
    "harness_origin_pin.json",
    "harness_origin_pin_audit.json",
    "harness_origin_source_inventory.json",
    "harness_origin_pin_promotion_review.json",
    "harness_origin_pre_post_integrity_check.json",
    "proposed_harness_origin_candidate_v2_21.json",
    "test_acquisition_audit.json",
    "test_provenance.json",
    "materialized_test_equivalence_summary.json",
    "test_workspace_equivalence.json",
    "test_purity_report.json",
    "workspace_purity_report.json",
    "workspace_equivalence_summary.json",
    "replisome_coupling_check.json",
    "chaperonin_topology_map.json",
    "recursive_provenance_chain_audit.json",
    "nuclear_pore_transport_log.json",
    "redundancy_cache_lookup.json",
    "environment_lock_summary.json",
    "bugsinpy_command_map_v1.json",
    "baseline_registry_snapshot_v2_21.json",
    "dependency_recovery_audit.json",
    "pre_repair_replay_gate_summary.json",
    "isolated_execution_log.txt",
    "s_engine_cognitive_state_snapshot.json",
    "retrocausal_reward_signal.json",
    "test_suite_structural_signature.json",
    "patch_size_cap.json",
    "realtime_patch_safety_trace.json",
    "patch_application_step.json",
    "telomere_workspace_protection_status.json",
    "post_validation_workspace_analysis.json",
    "patch_candidate_safety_check.json",
    "proof_obligations_ledger.json",
    "claim_boundary_v2_21.json",
    "roadmap_carry_forward_check_v2_21.json",
    "resolution_depth_diagnostic_v2_21.json",
    "SHA256SUMS.txt",
]

FORBIDDEN_PATCH_OUTPUTS = {
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


def canonical_sha(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()


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


def git_head_has_matching_pin_config() -> bool:
    rel = PIN_CONFIG_PATH.relative_to(REPO_ROOT).as_posix()
    exists = subprocess.run(
        ["git", "cat-file", "-e", f"HEAD:{rel}"],
        cwd=str(REPO_ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if exists.returncode != 0:
        return False
    blob = subprocess.check_output(["git", "cat-file", "blob", f"HEAD:{rel}"], cwd=str(REPO_ROOT))
    return hashlib.sha256(blob).hexdigest() == sha256_path(PIN_CONFIG_PATH)


def is_outside_repo(path_text: str | None) -> bool:
    if not path_text:
        return False
    try:
        path = Path(path_text).resolve()
    except OSError:
        path = Path(path_text).absolute()
    repo = REPO_ROOT.resolve()
    return path != repo and repo not in path.parents


def audit_config_pin(config: dict[str, Any], errors: list[str]) -> None:
    pins = config.get("pins")
    expect(isinstance(pins, list), errors, "pin config missing pins list")
    pin = next((item for item in pins or [] if isinstance(item, dict) and item.get("candidate_id") == "PySnooper:1"), None)
    expect(isinstance(pin, dict), errors, "pin config missing PySnooper:1 pin")
    if not isinstance(pin, dict):
        return
    expect(pin.get("harness_source_type") == "immutable_public_repo_commit", errors, "pin source type is not immutable")
    expect(pin.get("source_url_or_repo") == PIN_SOURCE_REPO, errors, "pin source repo mismatch")
    expect(pin.get("source_commit_sha_or_bundle_identity") == PIN_COMMIT, errors, "pin commit mismatch")
    expect(pin.get("expected_harness_manifest_sha256") == EXPECTED_HARNESS_MANIFEST_SHA256, errors, "pin manifest hash mismatch")
    expect(pin.get("expected_target_test_path") == TARGET_TEST, errors, "pin target test path mismatch")
    expect(pin.get("expected_target_test_sha256") is None, errors, "pin unexpectedly claims target-test SHA256")
    expect(pin.get("pin_authoritative_for_workflow") is True, errors, "pin is not marked authoritative for workflow")
    expect(pin.get("review_status") == "promoted_from_immutable_public_source", errors, "pin review status mismatch")
    manifest_text = str(pin.get("expected_harness_manifest_sha256", "")).lower()
    expect(
        "placeholder" not in manifest_text and "example" not in manifest_text and len(manifest_text) == 64,
        errors,
        "pin expected_harness_manifest_sha256 is placeholder-like",
    )
    commit_text = str(pin.get("source_commit_sha_or_bundle_identity", "")).lower()
    expect(
        "placeholder" not in commit_text
        and "example" not in commit_text
        and re.fullmatch(r"[0-9a-f]{40}", commit_text) is not None,
        errors,
        "pin source_commit_sha_or_bundle_identity is not a concrete Git commit",
    )
    topology = {str(item.get("path")): item for item in pin.get("expected_harness_topology_files") or [] if isinstance(item, dict)}
    expect(set(topology) == set(EXPECTED_TOPOLOGY_HASHES), errors, "pin topology file set mismatch")
    for path, expected_hash in EXPECTED_TOPOLOGY_HASHES.items():
        expect(topology.get(path, {}).get("sha256") == expected_hash, errors, f"pin topology hash mismatch: {path}")
    forbidden = pin.get("forbidden_inputs_checked") or {}
    for key in ["fixed_revision", "gold_patch", "future_outcomes", "hidden_labels", "synthetic_tests", "copied_known_fixes"]:
        expect(forbidden.get(key) is True, errors, f"pin forbidden input check missing: {key}")


def audit_transport(root: Path, transport: dict[str, Any], errors: list[str]) -> None:
    expect(transport.get("status") == "PASS", errors, "transport status did not PASS")
    expect(transport.get("transport_integrity_status") == "PASS", errors, "transport integrity did not PASS")
    entries = transport.get("entries")
    expect(isinstance(entries, list), errors, "transport entries missing")
    if not isinstance(entries, list):
        return
    covered = set()
    for entry in entries:
        rel = entry.get("repo_output_path")
        if not rel:
            errors.append("transport entry missing repo_output_path")
            continue
        rel_path = str(rel).replace("\\", "/")
        covered.add(Path(rel_path).name)
        path = REPO_ROOT / rel_path
        if not path.is_file():
            errors.append(f"transport target missing: {rel}")
            continue
        actual = sha256_path(path)
        expect(entry.get("workspace_sha256") == actual, errors, f"transport workspace hash mismatch: {rel}")
        expect(entry.get("repo_ingested_sha256") == actual, errors, f"transport repo hash mismatch: {rel}")
        expect(entry.get("transport_integrity") == "PASS", errors, f"transport entry failed: {rel}")
    required = {
        path.name
        for path in root.rglob("*")
        if path.is_file()
        and path.name
        not in {
            "SHA256SUMS.txt",
            "nuclear_pore_transport_log.json",
            "proof_obligations_ledger.json",
        }
    }
    missing = required - covered
    expect(not missing, errors, f"transport coverage missing: {sorted(missing)}")


def audit_ledger(root: Path, ledger: dict[str, Any], errors: list[str]) -> None:
    expect(ledger.get("status") == "PASS", errors, "proof ledger status did not PASS")
    expect(ledger.get("ghost_state_count") == 0, errors, "proof ledger reports ghost states")
    entries = ledger.get("ledger_entries")
    expect(isinstance(entries, list) and bool(entries), errors, "proof ledger entries missing")
    if not isinstance(entries, list):
        return
    previous = None
    block_seen = False
    rollback_seen = False
    for index, entry in enumerate(entries):
        expect(entry.get("index") == index, errors, f"ledger index mismatch at {index}")
        expect(entry.get("previous_entry_hash") == previous, errors, f"ledger previous hash mismatch at {index}")
        material = {key: value for key, value in entry.items() if key != "entry_hash"}
        expect(canonical_sha(material) == entry.get("entry_hash"), errors, f"ledger entry hash mismatch at {index}")
        rel = entry.get("path")
        if rel:
            path = root / str(rel)
            expect(path.is_file(), errors, f"ledger target missing: {rel}")
            if path.is_file():
                expect(sha256_path(path) == entry.get("sha256"), errors, f"ledger target hash mismatch: {rel}")
        if entry.get("result") == "block":
            block_seen = True
        if entry.get("action") == "rollback_workspace_and_stop":
            rollback_seen = entry.get("workspace_cleanup_confirmed") is True
        previous = entry.get("entry_hash")
    expect(ledger.get("ledger_tip") == previous, errors, "ledger tip mismatch")
    expect(block_seen, errors, "proof ledger lacks the target-test block state")
    expect(rollback_seen, errors, "proof ledger lacks rollback/cleanup state")


def audit_prior_boundary(errors: list[str]) -> None:
    verification = load_json(
        REPO_ROOT / "outputs" / "v2_20_test_provenance_repair_lane" / "v2_20_official_artifact_verification.json",
        errors,
    )
    expect(verification.get("status") == "PASS", errors, "v2.20 official artifact verification is not PASS")
    expect(
        verification.get("zip_sha256") == "3b6090f33ab4e5bb04ca4f922e51d4688b8d1ef5bc343ab6b26efc40b9e7ca25",
        errors,
        "v2.20 official artifact digest mismatch",
    )
    audit = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "audit_v2_20_test_provenance_repair_lane.py")],
        cwd=str(REPO_ROOT),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if audit.returncode != 0:
        errors.append("v2.20 audit did not pass from v2.21 audit")


def audit_outputs(root: Path, errors: list[str]) -> None:
    for rel in REQUIRED_FILES:
        expect((root / rel).is_file(), errors, f"missing required output: {rel}")
    for rel in FORBIDDEN_PATCH_OUTPUTS:
        expect(not (root / rel).exists(), errors, f"unexpected patch output exists: {rel}")

    manifest_errors, checked = verify_manifest(root)
    errors.extend(manifest_errors)
    expect(checked >= len(REQUIRED_FILES) - 1, errors, "manifest checked fewer files than required")

    config = load_json(PIN_CONFIG_PATH, errors)
    audit_config_pin(config, errors)
    pin_committed = git_head_has_matching_pin_config()
    in_actions = os.environ.get("GITHUB_ACTIONS") == "true"

    results = load_json(root / "campaign_results.json", errors)
    pin = load_json(root / "harness_origin_pin.json", errors)
    pin_audit = load_json(root / "harness_origin_pin_audit.json", errors)
    inventory = load_json(root / "harness_origin_source_inventory.json", errors)
    test_provenance = load_json(root / "test_provenance.json", errors)
    acquisition = load_json(root / "test_acquisition_audit.json", errors)
    workspace_purity = load_json(root / "workspace_purity_report.json", errors)
    workspace_equivalence = load_json(root / "workspace_equivalence_summary.json", errors)
    environment_lock = load_json(root / "environment_lock_summary.json", errors)
    command_map = load_json(root / "bugsinpy_command_map_v1.json", errors)
    baseline = load_json(root / "baseline_registry_snapshot_v2_21.json", errors)
    dependency = load_json(root / "dependency_recovery_audit.json", errors)
    replay = load_json(root / "pre_repair_replay_gate_summary.json", errors)
    reward = load_json(root / "retrocausal_reward_signal.json", errors)
    patch_safety = load_json(root / "patch_candidate_safety_check.json", errors)
    claim = load_json(root / "claim_boundary_v2_21.json", errors)
    roadmap = load_json(root / "roadmap_carry_forward_check_v2_21.json", errors)
    resolution = load_json(root / "resolution_depth_diagnostic_v2_21.json", errors)
    transport = load_json(root / "nuclear_pore_transport_log.json", errors)
    ledger = load_json(root / "proof_obligations_ledger.json", errors)

    expect(results.get("campaign_id") == CAMPAIGN_ID, errors, "campaign_results campaign mismatch")
    expect(results.get("status") == "PASS_WITH_TARGET_TEST_PROVENANCE_BLOCKED", errors, "v2.21 status mismatch")
    expect(results.get("based_on") == "v2.20", errors, "v2.21 did not declare v2.20 boundary")
    expect(results.get("v2_20_official_ingest_verified") is True, errors, "v2.20 official ingest not verified")
    expect(results.get("harness_origin_pin_status") == "PASS", errors, "harness-origin pin did not PASS")
    expect(results.get("harness_origin_authority_type") == "immutable_public_repo_commit", errors, "harness authority type mismatch")
    expect(results.get("harness_origin_source_url_or_repo") == PIN_SOURCE_REPO, errors, "harness source repo mismatch")
    expect(results.get("harness_origin_commit_or_bundle_identity") == PIN_COMMIT, errors, "harness commit mismatch")
    expect(results.get("observed_harness_sha256") == EXPECTED_HARNESS_MANIFEST_SHA256, errors, "observed harness SHA mismatch")
    expect(results.get("pin_promotion_status") == "promoted_from_immutable_public_source", errors, "pin promotion status mismatch")
    expect(results.get("workflow_runtime_generated_authority") is False, errors, "workflow runtime generated authority")
    expect(results.get("target_test_provenance_status") == "BLOCK", errors, "target-test provenance did not BLOCK")
    expect(results.get("target_test_source_origin") is None, errors, "target-test origin unexpectedly present")
    expect(results.get("target_test_sha256") is None, errors, "target-test SHA unexpectedly present")
    expect(results.get("recursive_provenance_chain_status") == "PASS", errors, "recursive provenance did not PASS")
    expect(results.get("replisome_coupling_status") == "BLOCK", errors, "replisome coupling did not BLOCK")
    expect(results.get("chaperonin_topology_status") == "BLOCK", errors, "chaperonin topology did not BLOCK")
    expect(results.get("redundancy_cache_lookup_result") == "not_found", errors, "redundancy cache result mismatch")
    expect(results.get("nuclear_pore_transport_status") == "PASS", errors, "transport did not PASS")
    expect(results.get("harness_pre_post_integrity_status") == "PASS", errors, "harness pre/post integrity did not PASS")
    expect(results.get("workspace_purity_status") == "PASS", errors, "workspace purity did not PASS")
    expect(results.get("workspace_equivalence_status") == "BLOCK", errors, "workspace equivalence did not BLOCK")
    expect(results.get("environment_lock_status") == "PASS", errors, "environment lock did not PASS")
    expect(results.get("command_manifest_status") == "PASS", errors, "command manifest did not PASS")
    expect(results.get("baseline_registry_precheck_status") == "PASS", errors, "baseline precheck did not PASS")
    expect(results.get("dependency_recovery_status") == "not_executed_target_test_provenance_blocked", errors, "dependency recovery was not blocked correctly")
    expect(results.get("pre_repair_replay_status") == "not_run_target_test_provenance_blocked", errors, "pre-repair replay was not blocked correctly")
    expect(results.get("reward_signal_status") == "PASS", errors, "reward signal did not PASS")
    expect(results.get("reward_graded_signal") == 0.0, errors, "reward graded signal is not zero")
    expect(results.get("reward_failure_type") == "test_missing_precondition", errors, "reward failure type mismatch")
    expect(results.get("patch_generated") is False, errors, "patch generated unexpectedly")
    expect(results.get("patch_authorized") is False, errors, "patch authorized unexpectedly")
    expect(results.get("patch_attempted") is False, errors, "patch attempted unexpectedly")
    expect(results.get("target_validation_status") == "not_applicable_no_patch", errors, "target validation status mismatch")
    expect(results.get("duplicate_replay_status") == "not_applicable_no_patch", errors, "duplicate replay status mismatch")
    expect(results.get("pysnooper1_scoreable") is False, errors, "PySnooper:1 unexpectedly scoreable")
    expect(results.get("pysnooper1_positive_memory_only") is False, errors, "PySnooper:1 unexpectedly positive-memory")
    expect(results.get("final_scoreable_count") == 5, errors, "scoreable count changed")
    expect(results.get("final_positive_memory_count") == 2, errors, "positive-memory count changed")
    expect(results.get("final_non_ansible_positive_memory_count") == 0, errors, "non-Ansible positive-memory count changed")
    expect(results.get("full_scoring") == "NOT_RUN", errors, "full scoring status changed")
    expect(results.get("full_scoring_allowed") is False, errors, "full scoring allowed unexpectedly")
    expect(results.get("memory_lift_status") == "undemonstrated", errors, "memory lift status changed")
    expect(results.get("self_maintaining_software_status") == "false/not_demonstrated", errors, "self-maintaining status changed")
    expect(results.get("current_protocol_version") == "v2.13", errors, "current protocol changed")

    expect(pin.get("pin_status") == "PASS", errors, "pin output did not PASS")
    expect(pin.get("workflow_runtime_generated_authority") is False, errors, "pin output reports workflow-generated authority")
    expect(pin.get("observed_harness_manifest_sha256") == EXPECTED_HARNESS_MANIFEST_SHA256, errors, "pin observed manifest mismatch")
    expect(pin.get("pin_config_sha256") == sha256_path(PIN_CONFIG_PATH), errors, "pin config hash mismatch")
    if in_actions:
        expect(pin_committed, errors, "pin config is not committed in GitHub Actions checkout")
        expect(pin.get("pin_existed_in_committed_config_before_runtime") is True, errors, "workflow pin did not exist before runtime")
        expect(pin_audit.get("expected_sha256_source") == "committed_config", errors, "workflow did not use committed config authority")
        expect(results.get("authoritative_sha256_source") == "committed_config", errors, "workflow authoritative SHA source mismatch")
    else:
        expect(pin.get("pin_existed_in_committed_config_before_runtime") in {True, False}, errors, "local pin committed flag invalid")
        expect(
            pin_audit.get("expected_sha256_source") in {"committed_config", "local_precommit_config_pending_commit"},
            errors,
            "local pin authority source invalid",
        )
    expect(pin_audit.get("status") == "PASS", errors, "pin audit did not PASS")
    expect(pin_audit.get("expected_manifest_match") is True, errors, "pin audit manifest mismatch")
    expect(pin_audit.get("expected_file_hashes_match") is True, errors, "pin audit file hash mismatch")
    expect(pin_audit.get("candidate_mapping_includes_pysnooper1") is True, errors, "pin audit missing PySnooper:1 mapping")
    expect(pin_audit.get("proposal_only_pin_used_as_authority") is False, errors, "proposal-only pin used as authority")
    expect(pin_audit.get("self_referential_hash_detected") is False, errors, "self-referential pin hash detected")
    expect(pin_audit.get("workflow_runtime_generated_authority") is False, errors, "pin audit reports workflow-generated authority")
    expect(pin_audit.get("fixed_gold_future_hidden_label_evidence_used") is False, errors, "forbidden evidence used in pin audit")

    records = inventory.get("records")
    expect(isinstance(records, list), errors, "harness inventory records missing")
    record_by_path = {record.get("path"): record for record in records or [] if isinstance(record, dict)}
    for path, expected_hash in EXPECTED_TOPOLOGY_HASHES.items():
        record = record_by_path.get(path, {})
        expect(record.get("present") is True, errors, f"harness file missing: {path}")
        expect(record.get("sha256") == expected_hash, errors, f"harness file SHA mismatch: {path}")
        expect(record.get("sha256_match") is True, errors, f"harness file SHA match false: {path}")
    missing_target = record_by_path.get("projects/PySnooper/bugs/1/tests/test_chinese.py", {})
    expect(missing_target.get("present") is False, errors, "target test unexpectedly present in pinned harness source")
    expect(missing_target.get("http_status") == 404, errors, "target test missing status is not 404")
    expect(inventory.get("forbidden_inputs_accessed") is False, errors, "inventory accessed forbidden inputs")

    for key in [
        "fixed_revision_contents_used",
        "gold_patch_used",
        "future_outcome_evidence_used",
        "hidden_label_evidence_used",
        "synthetic_or_generated_test_used",
        "hallucinated_content_used",
        "repair_mutation",
        "benchmark_harness_materialization",
    ]:
        expect(test_provenance.get(key) is False, errors, f"test provenance reports forbidden condition: {key}")
    expect(test_provenance.get("status") == "BLOCK", errors, "test provenance did not BLOCK")
    expect(test_provenance.get("target_test_sha256") is None, errors, "test provenance target SHA unexpectedly present")
    expect(test_provenance.get("source_harness_pin_sha256") == EXPECTED_HARNESS_MANIFEST_SHA256, errors, "test provenance harness pin SHA mismatch")

    expect(acquisition.get("source_repo_url") == PYSNOOPER_SOURCE_REPO, errors, "source acquisition repo mismatch")
    expect(acquisition.get("buggy_commit_id") == BUGGY_REVISION, errors, "source acquisition buggy revision mismatch")
    expect(acquisition.get("acquired_head_sha") == BUGGY_REVISION, errors, "source acquisition head mismatch")
    expect(acquisition.get("status") == "PASS", errors, "source acquisition did not PASS")
    expect(workspace_purity.get("status") == "PASS", errors, "workspace purity did not PASS")
    expect(workspace_purity.get("workspace_outside_repo") is True, errors, "workspace was not outside repo")
    expect(is_outside_repo(workspace_purity.get("workspace_path")), errors, "workspace path is inside repo")
    expect(workspace_purity.get("workspace_path_under_onedrive") is False, errors, "workspace path under OneDrive")
    expect(workspace_equivalence.get("status") == "BLOCK", errors, "workspace equivalence did not BLOCK")
    expect(environment_lock.get("status") == "PASS", errors, "environment lock did not PASS")
    expect(environment_lock.get("python_toolbox_declared") is True, errors, "python-toolbox declaration missing")
    expect(environment_lock.get("no_undeclared_dependency_install") is True, errors, "undeclared dependency install reported")
    expect(environment_lock.get("no_global_environment_mutation") is True, errors, "global environment mutation reported")
    expect(command_map.get("status") == "PASS", errors, "command map did not PASS")
    expect(command_map.get("target_command") == "python -m pytest -q -s tests/test_chinese.py::test_chinese", errors, "target command mismatch")
    expect(command_map.get("target_test_paths") == [TARGET_TEST], errors, "target test paths mismatch")
    expect(baseline.get("status") == "PASS", errors, "baseline registry did not PASS")
    expect(baseline.get("expected_scoreable_count") == 5, errors, "baseline scoreable count changed")
    expect(baseline.get("expected_positive_memory_count") == 2, errors, "baseline positive-memory count changed")
    expect(baseline.get("expected_non_ansible_positive_memory_count") == 0, errors, "baseline non-Ansible positive-memory count changed")
    expect(dependency.get("dependency_recovery_status") == "not_executed_target_test_provenance_blocked", errors, "dependency recovery status mismatch")
    expect(dependency.get("install_attempted") is False, errors, "dependency install attempted")
    expect(replay.get("pre_repair_replay_attempted") is False, errors, "pre-repair replay attempted")
    expect(replay.get("replay_before_patch_authorization") is True, errors, "replay-before-patch invariant missing")
    expect(reward.get("status") == "PASS", errors, "reward file did not PASS")
    expect(reward.get("graded_signal") == 0.0, errors, "reward file graded signal mismatch")
    expect(reward.get("failure_type") == "test_missing_precondition", errors, "reward file failure type mismatch")
    expect(patch_safety.get("patch_attempt_count") == 0, errors, "patch attempt count changed")
    expect(patch_safety.get("patch_generated") is False, errors, "patch safety reports patch generated")
    expect(patch_safety.get("patch_authorized") is False, errors, "patch safety reports patch authorized")
    expect(patch_safety.get("patch_attempted") is False, errors, "patch safety reports patch attempted")
    expect(patch_safety.get("tests_modified") is False, errors, "patch safety reports tests modified")
    expect(patch_safety.get("fixtures_modified") is False, errors, "patch safety reports fixtures modified")
    expect(patch_safety.get("benchmark_metadata_modified") is False, errors, "patch safety reports benchmark metadata modified")
    expect(patch_safety.get("harness_modified") is False, errors, "patch safety reports harness modified")
    expect(claim.get("status") == "PASS", errors, "claim boundary did not PASS")
    expect(claim.get("candidate_scope") == ["PySnooper:1"], errors, "claim boundary candidate scope mismatch")
    expect(claim.get("pysnooper2_pursued") is False, errors, "PySnooper:2 was pursued")
    expect(claim.get("v2_21_promoted_to_current") is False, errors, "v2.21 promoted to current")
    expect(claim.get("full_scoring") == "NOT_RUN", errors, "claim boundary full scoring changed")
    expect(claim.get("full_scoring_allowed") is False, errors, "claim boundary full scoring allowed")
    expect(claim.get("current_protocol_version") == "v2.13", errors, "claim boundary current protocol changed")
    expect(roadmap.get("status") == "PASS", errors, "roadmap carry-forward check did not PASS")
    expect(roadmap.get("roadmap_updated_for_v2_21") is True, errors, "roadmap not updated for v2.21")
    expect(roadmap.get("backlog_updated_for_v2_21") is True, errors, "backlog not updated for v2.21")
    expect(resolution.get("status") == "PASS", errors, "resolution diagnostic did not PASS")
    expect(resolution.get("harness_origin_N7p13_blocked_or_passed") == "passed", errors, "harness N7p13 did not pass")
    expect(resolution.get("test_provenance_N7_blocked_or_passed") == "blocked", errors, "test provenance N7 did not block")
    expect(resolution.get("repair_generation_N9_not_reached_or_reached") == "not_reached", errors, "repair generation was reached unexpectedly")

    audit_transport(root, transport, errors)
    audit_ledger(root, ledger, errors)
    audit_prior_boundary(errors)

    print(f"v2.21 manifest entries checked: {checked}")
    for key in [
        "harness_origin_pin_status",
        "target_test_provenance_status",
        "replisome_coupling_status",
        "chaperonin_topology_status",
        "dependency_recovery_status",
        "pre_repair_replay_status",
        "patch_generated",
        "patch_authorized",
        "patch_attempted",
        "pysnooper1_scoreable",
        "pysnooper1_positive_memory_only",
        "final_scoreable_count",
        "final_positive_memory_count",
        "final_non_ansible_positive_memory_count",
        "full_scoring",
        "memory_lift_status",
        "self_maintaining_software_status",
        "current_protocol_version",
    ]:
        print(f"{key}={results.get(key)}")
    print(f"workflow_runtime_pin_committed={pin_committed}")


def main() -> int:
    errors: list[str] = []
    if not OUTPUT_ROOT.is_dir():
        errors.append(f"missing output root: {OUTPUT_ROOT}")
    else:
        audit_outputs(OUTPUT_ROOT, errors)
    if errors:
        print("v2.21 audit FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("v2.21 audit PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
