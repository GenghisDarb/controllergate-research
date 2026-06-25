#!/usr/bin/env python3
"""Audit v2.22 BugsInPy target-test materialization lane evidence."""

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
OUTPUT_ROOT = REPO_ROOT / "outputs" / "v2_22_bugsinpy_target_test_materialization_lane"
CAMPAIGN_ID = "v2_22_bugsinpy_target_test_materialization_lane"
BUGSINPY_REPO = "https://github.com/soarsmu/BugsInPy.git"
BUGSINPY_COMMIT = "11c5f1eea954a42132cfd06bf257766a7963e0fd"
BUGGY_REVISION = "e21a31162f4c54be693d8ca8260e42393b39abd3"
FIXED_REVISION = "56f22f8ffe1c6b2be4d2cf3ad1987fdb66113da2"
TARGET_TEST = "tests/test_chinese.py"

REQUIRED_FILES = [
    "campaign_summary.md",
    "campaign_results.json",
    "v2_21_artifact_ingest_verification.json",
    "artifact_repo_snapshot_comparison.json",
    "official_bugsinpy_framework_materialization_trace.json",
    "official_bugsinpy_cli_inventory.json",
    "pinned_bugsinpy_framework_checkout_audit.json",
    "framework_command_manifest.json",
    "target_test_materialization_search.json",
    "target_test_source_classification.json",
    "target_test_provenance.json",
    "target_test_materialized_file_audit.json",
    "target_test_absence_proof.json",
    "buggy_source_test_search.json",
    "forbidden_source_guard.json",
    "fixed_commit_access_guard.json",
    "future_commit_access_guard.json",
    "synthetic_test_guard.json",
    "pysnooper1_terminal_provenance_decision.json",
    "candidate_scope_transition_recommendation.json",
    "roadmap_carry_forward_check_v2_22.json",
    "resolution_depth_diagnostic_v2_22.json",
    "proof_obligations_ledger.json",
    "retrocausal_reward_signal.json",
    "test_suite_structural_signature.json",
    "dependency_recovery_audit.json",
    "pre_repair_replay_gate_summary.json",
    "environment_lock_summary.json",
    "bugsinpy_command_map_v2_22.json",
    "workspace_purity_report.json",
    "workspace_equivalence_summary.json",
    "test_workspace_equivalence.json",
    "chaperonin_topology_map.json",
    "replisome_coupling_check.json",
    "nuclear_pore_transport_log.json",
    "harness_origin_pre_post_integrity_check.json",
    "patch_candidate_safety_check.json",
    "patch_size_cap.json",
    "realtime_patch_safety_trace.json",
    "patch_application_step.json",
    "post_validation_workspace_analysis.json",
    "claim_boundary_v2_22.json",
    "SHA256SUMS.txt",
]

FORBIDDEN_PATCH_OUTPUTS = {
    "memory_enabled_source_only_repair_patch.diff",
    "no_memory_source_only_repair_patch.diff",
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


def is_outside_repo(path_text: str | None) -> bool:
    if not path_text:
        return False
    path = Path(path_text)
    try:
        resolved = path.resolve()
    except OSError:
        resolved = path.absolute()
    repo = REPO_ROOT.resolve()
    return resolved != repo and repo not in resolved.parents


def audit_transport(root: Path, transport: dict[str, Any], errors: list[str]) -> None:
    expect(transport.get("status") == "PASS", errors, "transport status did not PASS")
    expect(transport.get("transport_integrity_status") == "PASS", errors, "transport integrity did not PASS")
    entries = transport.get("entries")
    expect(isinstance(entries, list), errors, "transport entries missing")
    if not isinstance(entries, list):
        return
    covered = set()
    for entry in entries:
        rel = entry.get("workspace_relative_path")
        repo_rel = entry.get("repo_output_path")
        if not rel or not repo_rel:
            errors.append("transport entry missing path")
            continue
        covered.add(str(rel))
        path = REPO_ROOT / str(repo_rel)
        expect(path.is_file(), errors, f"transport target missing: {repo_rel}")
        if path.is_file():
            digest = sha256_path(path)
            expect(entry.get("workspace_sha256") == digest, errors, f"transport workspace hash mismatch: {repo_rel}")
            expect(entry.get("repo_ingested_sha256") == digest, errors, f"transport repo hash mismatch: {repo_rel}")
        expect(entry.get("transport_integrity") == "PASS", errors, f"transport entry failed: {repo_rel}")
    required = {
        path.relative_to(root).as_posix()
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
    expect(ledger.get("status") == "PASS", errors, "ledger status did not PASS")
    expect(ledger.get("ghost_state_count") == 0, errors, "ledger reports ghost states")
    entries = ledger.get("ledger_entries")
    expect(isinstance(entries, list) and bool(entries), errors, "ledger entries missing")
    if not isinstance(entries, list):
        return
    previous = None
    block_seen = False
    cleanup_seen = False
    for index, entry in enumerate(entries):
        expect(entry.get("index") == index, errors, f"ledger index mismatch at {index}")
        expect(entry.get("previous_entry_hash") == previous, errors, f"ledger previous hash mismatch at {index}")
        material = {key: value for key, value in entry.items() if key != "entry_hash"}
        expect(canonical_sha(material) == entry.get("entry_hash"), errors, f"ledger hash mismatch at {index}")
        rel = entry.get("path")
        if rel:
            target = root / str(rel)
            expect(target.is_file(), errors, f"ledger target missing: {rel}")
            if target.is_file():
                expect(sha256_path(target) == entry.get("sha256"), errors, f"ledger target hash mismatch: {rel}")
        if entry.get("result") == "block":
            block_seen = True
        if entry.get("action") == "rollback_workspace_and_stop":
            cleanup_seen = entry.get("workspace_cleanup_confirmed") is True
        previous = entry.get("entry_hash")
    expect(ledger.get("ledger_tip") == previous, errors, "ledger tip mismatch")
    expect(block_seen, errors, "ledger lacks block state")
    expect(cleanup_seen, errors, "ledger lacks cleanup state")


def audit_v221_boundary(errors: list[str]) -> None:
    verification = load_json(REPO_ROOT / "outputs" / "v2_21_harness_origin_verification_lane" / "v2_21_official_artifact_verification.json", errors)
    expect(verification.get("status") == "PASS", errors, "v2.21 official verification is not PASS")
    expect(
        verification.get("zip_sha256") == "35b22fd48d93ae5c5163ad9ab5d27ac99cfc351bfd2e08b869f38479aebade08",
        errors,
        "v2.21 official artifact digest mismatch",
    )
    audit = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "audit_v2_21_harness_origin_verification_lane.py")],
        cwd=str(REPO_ROOT),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if audit.returncode != 0:
        errors.append("v2.21 audit did not pass from v2.22 audit")


def audit_outputs(root: Path, errors: list[str]) -> None:
    for rel in REQUIRED_FILES:
        expect((root / rel).is_file(), errors, f"missing required output: {rel}")
    for rel in FORBIDDEN_PATCH_OUTPUTS:
        expect(not (root / rel).exists(), errors, f"unexpected patch output: {rel}")
    manifest_errors, checked = verify_manifest(root)
    errors.extend(manifest_errors)
    expect(checked >= len(REQUIRED_FILES) - 1, errors, "manifest checked fewer files than required")

    results = load_json(root / "campaign_results.json", errors)
    v221 = load_json(root / "v2_21_artifact_ingest_verification.json", errors)
    framework = load_json(root / "pinned_bugsinpy_framework_checkout_audit.json", errors)
    cli = load_json(root / "official_bugsinpy_cli_inventory.json", errors)
    command_manifest = load_json(root / "framework_command_manifest.json", errors)
    materialization = load_json(root / "official_bugsinpy_framework_materialization_trace.json", errors)
    search = load_json(root / "target_test_materialization_search.json", errors)
    source = load_json(root / "target_test_source_classification.json", errors)
    provenance = load_json(root / "target_test_provenance.json", errors)
    materialized_file = load_json(root / "target_test_materialized_file_audit.json", errors)
    absence = load_json(root / "target_test_absence_proof.json", errors)
    buggy_search = load_json(root / "buggy_source_test_search.json", errors)
    fixed_guard = load_json(root / "fixed_commit_access_guard.json", errors)
    future_guard = load_json(root / "future_commit_access_guard.json", errors)
    synthetic_guard = load_json(root / "synthetic_test_guard.json", errors)
    forbidden = load_json(root / "forbidden_source_guard.json", errors)
    terminal = load_json(root / "pysnooper1_terminal_provenance_decision.json", errors)
    recommendation = load_json(root / "candidate_scope_transition_recommendation.json", errors)
    roadmap = load_json(root / "roadmap_carry_forward_check_v2_22.json", errors)
    resolution = load_json(root / "resolution_depth_diagnostic_v2_22.json", errors)
    dependency = load_json(root / "dependency_recovery_audit.json", errors)
    replay = load_json(root / "pre_repair_replay_gate_summary.json", errors)
    reward = load_json(root / "retrocausal_reward_signal.json", errors)
    patch_safety = load_json(root / "patch_candidate_safety_check.json", errors)
    claim = load_json(root / "claim_boundary_v2_22.json", errors)
    workspace = load_json(root / "workspace_purity_report.json", errors)
    coupling = load_json(root / "replisome_coupling_check.json", errors)
    topology = load_json(root / "chaperonin_topology_map.json", errors)
    transport = load_json(root / "nuclear_pore_transport_log.json", errors)
    ledger = load_json(root / "proof_obligations_ledger.json", errors)

    expect(results.get("campaign_id") == CAMPAIGN_ID, errors, "campaign ID mismatch")
    expect(results.get("based_on") == "v2.21", errors, "v2.22 does not build on v2.21")
    expect(results.get("status") == "PASS_WITH_TERMINAL_PYSNOOPER1_PROVENANCE_BLOCK", errors, "v2.22 status mismatch")
    expect(results.get("v2_21_official_ingest_verified") is True, errors, "v2.21 ingest not verified")
    expect(v221.get("status") == "PASS", errors, "embedded v2.21 verification not PASS")
    expect(framework.get("status") == "PASS", errors, "pinned framework checkout did not PASS")
    expect(framework.get("source_repo") == BUGSINPY_REPO, errors, "framework repo mismatch")
    expect(framework.get("observed_commit") == BUGSINPY_COMMIT, errors, "framework commit mismatch")
    expect(framework.get("sparse_checkout_used") is True, errors, "framework checkout did not record sparse checkout")
    expect(framework.get("framework_checkout_outside_repo") is True, errors, "framework checkout not outside repo")
    expect(cli.get("status") == "PASS", errors, "CLI inventory did not PASS")
    for command in ["bugsinpy-checkout", "bugsinpy-compile", "bugsinpy-test"]:
        expect(command in (cli.get("commands_available") or []), errors, f"missing CLI command: {command}")
    expect(command_manifest.get("status") == "PASS", errors, "command manifest did not PASS")
    expect(command_manifest.get("framework_checkout_is_not_materialized_project_source") is True, errors, "framework/materialized distinction missing")
    expect(command_manifest.get("project_key_selected") == "PySnooper", errors, "project key mismatch")
    bug_info = command_manifest.get("bug_info") or {}
    expect(bug_info.get("buggy_commit_id") == BUGGY_REVISION, errors, "buggy commit metadata mismatch")
    expect(bug_info.get("fixed_commit_id") == FIXED_REVISION, errors, "fixed commit metadata mismatch")
    expect(bug_info.get("test_file") == TARGET_TEST, errors, "target test metadata mismatch")
    expect(materialization.get("status") == "PASS", errors, "official materialization did not PASS")
    expect(materialization.get("official_checkout_attempted") is True, errors, "official checkout was not attempted")
    expect(materialization.get("framework_checkout_is_metadata_not_materialized_source") is True, errors, "materialization trace lacks framework distinction")
    expect(materialization.get("checkout_disqualifying_stderr") is False, errors, "checkout had disqualifying stderr")
    expect(materialization.get("materialized_workspace_outside_repo") is True, errors, "materialized workspace not outside repo")
    expect(materialization.get("materialized_workspace_under_onedrive") is False, errors, "materialized workspace under OneDrive")
    expect(search.get("official_checkout_attempted_before_terminal_decision") is True, errors, "search did not follow official checkout")
    expect(search.get("framework_repo_absence_considered_terminal") is False, errors, "framework repo absence was considered terminal")
    expect(search.get("target_test_found") is True, errors, "target test was not found after materialization")
    target_record = search.get("target_test_record") or {}
    expect(target_record.get("relative_path") == "PySnooper/tests/test_chinese.py", errors, "materialized target path mismatch")
    expect(re.fullmatch(r"[0-9a-f]{64}", str(target_record.get("sha256", ""))) is not None, errors, "target test SHA invalid")
    expect(source.get("status") == "BLOCK", errors, "source classification did not BLOCK")
    expect(source.get("source_classification") == "fixed_commit_derived_by_pinned_framework_checkout", errors, "source classification mismatch")
    expect(source.get("checkout_script_uses_fixed_commit_for_target_test_materialization") is True, errors, "fixed-copy script behavior not recorded")
    expect(provenance.get("status") == "BLOCK", errors, "target-test provenance did not BLOCK")
    expect(provenance.get("fixed_revision_contents_used_for_decision_time_test_content") is True, errors, "fixed-source provenance not recorded")
    expect(provenance.get("future_outcome_evidence_used") is False, errors, "future evidence used")
    expect(provenance.get("gold_patch_used") is False, errors, "gold patch used")
    expect(provenance.get("synthetic_or_generated_test_used") is False, errors, "synthetic test used")
    expect(materialized_file.get("status") == "PASS", errors, "materialized file audit did not PASS")
    expect(materialized_file.get("source_guard_status") == "BLOCK", errors, "materialized file source guard did not BLOCK")
    expect(absence.get("framework_repo_absence_alone_used_as_terminal_blocker") is False, errors, "false terminal framework-absence block detected")
    expect(absence.get("official_bugsinpy_checkout_attempted") is True, errors, "absence proof lacks official checkout attempt")
    expect(buggy_search.get("search_completed") is True, errors, "buggy source search not completed")
    expect(fixed_guard.get("status") == "BLOCK", errors, "fixed guard did not BLOCK")
    expect(fixed_guard.get("fixed_commit_contents_used_for_decision_time_test_content") is True, errors, "fixed guard did not record fixed content")
    expect(future_guard.get("status") == "PASS", errors, "future guard did not PASS")
    expect(synthetic_guard.get("status") == "PASS", errors, "synthetic guard did not PASS")
    expect(forbidden.get("status") == "BLOCK", errors, "forbidden source guard did not BLOCK")
    expect(forbidden.get("fixed_source_guard_status") == "BLOCK", errors, "fixed source guard status mismatch")
    expect(terminal.get("decision") == "terminal_blocked", errors, "terminal decision mismatch")
    expect(terminal.get("terminal_under_current_safety_rules") is True, errors, "terminal safety decision not true")
    expect(terminal.get("blocker") == "blocked_target_test_requires_fixed_or_future_source", errors, "terminal blocker mismatch")
    expect(recommendation.get("recommendation") == "select_different_non_ansible_candidate_next", errors, "candidate transition recommendation mismatch")
    expect(roadmap.get("status") == "PASS", errors, "roadmap check did not PASS")
    expect(roadmap.get("roadmap_updated_for_v2_22") is True, errors, "roadmap not updated for v2.22")
    expect(roadmap.get("backlog_updated_for_v2_22") is True, errors, "backlog not updated for v2.22")
    expect(roadmap.get("tld_resolution_map_updated_for_v2_22") is True, errors, "TLD map not updated for v2.22")
    expect(roadmap.get("resolution_depth_map_updated_for_v2_22") is True, errors, "resolution depth map not updated for v2.22")
    expect(resolution.get("status") == "PASS", errors, "resolution diagnostic did not PASS")
    expect(resolution.get("official_materialization_N7p5_status") == "executed", errors, "official materialization resolution status mismatch")
    expect(resolution.get("fixed_future_source_guard_status") == "BLOCK", errors, "resolution source guard mismatch")
    expect(dependency.get("dependency_recovery_status") == "not_executed_target_test_provenance_blocked", errors, "dependency recovery status mismatch")
    expect(dependency.get("install_attempted") is False, errors, "dependency recovery attempted")
    expect(replay.get("pre_repair_replay_attempted") is False, errors, "pre-repair replay attempted")
    expect(replay.get("replay_before_patch_authorization") is True, errors, "replay-before-patch invariant missing")
    expect(reward.get("status") == "PASS", errors, "reward signal did not PASS")
    expect(reward.get("graded_signal") == 0.0, errors, "reward signal is not zero")
    expect(reward.get("failure_type") == "fixed_or_future_test_source_precondition", errors, "reward failure type mismatch")
    expect(patch_safety.get("patch_generated") is False, errors, "patch generated unexpectedly")
    expect(patch_safety.get("patch_authorized") is False, errors, "patch authorized unexpectedly")
    expect(patch_safety.get("patch_attempted") is False, errors, "patch attempted unexpectedly")
    expect(patch_safety.get("tests_modified") is False, errors, "tests modified")
    expect(patch_safety.get("harness_modified") is False, errors, "harness modified")
    expect(claim.get("status") == "PASS", errors, "claim boundary did not PASS")
    expect(claim.get("candidate_scope") == ["PySnooper:1"], errors, "candidate scope mismatch")
    expect(claim.get("pysnooper2_pursued") is False, errors, "PySnooper:2 was pursued")
    expect(claim.get("current_protocol_version") == "v2.13", errors, "current protocol changed")
    expect(claim.get("v2_22_promoted_to_current") is False, errors, "v2.22 promoted to current")
    expect(claim.get("full_scoring") == "NOT_RUN", errors, "full scoring changed")
    expect(claim.get("full_scoring_allowed") is False, errors, "full scoring allowed")
    expect(workspace.get("workspace_outside_repo") is True, errors, "runtime workspace not outside repo")
    expect(workspace.get("workspace_under_onedrive") is False, errors, "runtime workspace under OneDrive")
    expect(coupling.get("coupling_status") == "BLOCK", errors, "replisome coupling did not BLOCK")
    expect(topology.get("topology_status") == "BLOCK", errors, "chaperonin topology did not BLOCK")
    expect(results.get("final_scoreable_count") == 5, errors, "scoreable count changed")
    expect(results.get("final_positive_memory_count") == 2, errors, "positive-memory count changed")
    expect(results.get("final_non_ansible_positive_memory_count") == 0, errors, "non-Ansible positive-memory count changed")
    expect(results.get("full_scoring") == "NOT_RUN", errors, "results full scoring changed")
    expect(results.get("memory_lift_status") == "undemonstrated", errors, "memory lift changed")
    expect(results.get("self_maintaining_software_status") == "false/not_demonstrated", errors, "self-maintaining status changed")

    if terminal.get("blocker") == "blocked_target_test_not_materializable_from_decision_time_safe_sources":
        expect(absence.get("official_bugsinpy_checkout_attempted") is True, errors, "terminal absence without official checkout")
        expect(absence.get("materialized_workspace_search_completed") is True, errors, "terminal absence without materialized search")
        expect(absence.get("buggy_source_tree_search_completed") is True, errors, "terminal absence without buggy-source search")
        expect(absence.get("framework_repo_absence_alone_used_as_terminal_blocker") is False, errors, "terminal absence used framework repo only")

    audit_transport(root, transport, errors)
    audit_ledger(root, ledger, errors)
    audit_v221_boundary(errors)

    print(f"v2.22 manifest entries checked: {checked}")
    for key in [
        "pinned_bugsinpy_framework_verification_status",
        "official_framework_materialization_status",
        "target_test_search_result",
        "target_test_provenance_status",
        "fixed_future_gold_synthetic_source_guard_status",
        "pysnooper1_terminal_provenance_decision",
        "dependency_recovery_status",
        "pre_repair_replay_status",
        "reward_signal_status",
        "reward_graded_signal",
        "reward_failure_type",
        "patch_generated",
        "patch_authorized",
        "patch_attempted",
        "pysnooper1_scoreable",
        "pysnooper1_positive_memory_only",
        "final_non_ansible_positive_memory_count",
        "full_scoring",
        "memory_lift_status",
        "self_maintaining_software_status",
        "current_protocol_version",
        "current_resolution_band_reached",
        "exact_blocker",
    ]:
        print(f"{key}={results.get(key)}")


def main() -> int:
    errors: list[str] = []
    if not OUTPUT_ROOT.is_dir():
        errors.append(f"missing output root: {OUTPUT_ROOT}")
    else:
        audit_outputs(OUTPUT_ROOT, errors)
    if errors:
        print("v2.22 audit FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("v2.22 audit PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
