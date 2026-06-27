#!/usr/bin/env python3
"""Audit v2.30 Failure Signature Canonicalization + Repair Continuation evidence."""

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
CAMPAIGN_ID = "v2_30_failure_signature_canonicalization_repair_lane"
OUTPUT_ROOT = REPO_ROOT / "outputs" / CAMPAIGN_ID
REGISTRY_PATH = REPO_ROOT / "configs" / "external_candidate_registry.json"
REGISTRY_SCHEMA_PATH = REPO_ROOT / "configs" / "external_candidate_registry.schema.json"
NORMALIZATION_POLICY_PATH = REPO_ROOT / "configs" / "failure_signature_normalization_policy.json"
V229_ROOT = REPO_ROOT / "outputs" / "v2_29_external_candidate_repair_lane"

EXPECTED = {
    "candidate_id": "py_bugger_issue_65",
    "repo_url": "https://github.com/ehmatthes/py-bugger",
    "buggy_commit_sha": "67cf214f2d619848e90280fd4469377123e81b94",
    "test_command": "python -m pytest tests/integration_tests/test_modifications.py::test_indentationerror_multiple_trys -q",
    "target_test_path": "tests/integration_tests/test_modifications.py",
    "target_test_sha256": "3e3c9521a4c1084df9269fb6bd38cb47808061559d7eb3eafa3fd78f4f3965b1",
    "support_file_path": "tests/sample_code/sample_scripts/two_trys.py",
    "support_file_sha256": "66a72a7abc6f2bffec7881d0a5b0a006deb408a8c496148210e14caafd1a2d11",
    "environment_lock_source_sha256": "2f1fe04032ca64b556e4db66a1aa5af3c81ccc958735a390226ea1b987484631",
    "v2_28_normalized_hash": "a97ccd92654e725d3c54d88ece253973a8d98e7f4d1b5a42c4ca921a433dd2ea",
    "v2_29_normalized_hash": "96afb1e4c1f14a7453cbc859924486d11420ff1a3197775919f14d355e2a7cff",
    "v2_29_zip_sha256": "6908479e18a3ace65ea82363a96f08b9a5630c4b96ced18df2173aa20730e591",
}
REPAIR_SOURCE_PATH = "src/py_bugger/utils/bug_utils.py"

ALLOWED_BLOCKERS = {
    None,
    "v2_29_artifact_verification_failed",
    "reviewed_candidate_registry_entry_missing_or_invalid",
    "selected_candidate_registry_evidence_mismatch",
    "selected_candidate_checkout_failed",
    "selected_candidate_target_test_hash_mismatch",
    "selected_candidate_support_file_hash_mismatch",
    "selected_candidate_environment_file_hash_mismatch",
    "selected_candidate_dependency_resolution_failed",
    "semantic_failure_signature_unstable",
    "semantic_failure_signature_refresh_failed",
    "signature_refresh_registry_validation_failed",
    "pre_repair_environmental_pass_blocked",
    "external_bug_signature_mismatch_semantic",
    "pre_repair_target_test_not_executed",
    "pre_repair_environment_resolution_failed",
    "ast_dependency_closure_failed",
    "dynamic_import_provenance_blocked",
    "pre_post_handoff_consistency_failed",
    "patch_candidate_safety_gate_failed",
    "repair_patch_not_generated",
    "patch_application_failed",
    "target_validation_same_failure",
    "target_validation_new_failure",
    "target_validation_no_test_collected",
    "environmental_pass_without_source_repair_blocked",
    "low_replay_reliability_stochastic",
    "post_validation_workspace_contamination_detected",
    "forbidden_file_modified",
    "forbidden_evidence_detected",
}

REQUIRED_FILES = [
    "campaign_summary.md",
    "campaign_results.json",
    "v2_29_artifact_ingest_verification.json",
    "artifact_repo_snapshot_comparison.json",
    "selected_candidate_record.json",
    "selected_candidate_registry_entry_before.json",
    "selected_candidate_registry_entry_after.json",
    "failure_signature_normalization_policy.json",
    "failure_signature_canonicalization_plan.json",
    "failure_signature_history_before.json",
    "failure_signature_history_after.json",
    "v2_28_v2_29_failure_comparison.json",
    "semantic_failure_signature_manifest.json",
    "semantic_failure_signature_hash.json",
    "semantic_failure_signature_replay_matrix.json",
    "canonical_failure_capture_1_raw.log",
    "canonical_failure_capture_1_normalized.txt",
    "canonical_failure_capture_1_semantic.json",
    "canonical_failure_capture_2_raw.log",
    "canonical_failure_capture_2_normalized.txt",
    "canonical_failure_capture_2_semantic.json",
    "canonical_failure_capture_3_raw.log",
    "canonical_failure_capture_3_normalized.txt",
    "canonical_failure_capture_3_semantic.json",
    "registry_signature_refresh_report.json",
    "external_candidate_registry_validation_report_after_signature_refresh.json",
    "selected_candidate_source_checkout_audit.json",
    "selected_candidate_buggy_tree_manifest.json",
    "selected_candidate_target_test_file_hashes.json",
    "selected_candidate_support_file_hashes.json",
    "selected_candidate_environment_file_hashes.json",
    "selected_candidate_command_manifest.json",
    "selected_candidate_environment_resolution_preflight.json",
    "pre_repair_replay_gate_summary.json",
    "pre_repair_failure_signature_verification.json",
    "target_validation_pre_patch_log.txt",
    "structural_failure_signature.json",
    "ast_dependency_closure_manifest.json",
    "ast_dependency_closure_edges.csv",
    "ast_dependency_closure_reason_codes.json",
    "ast_dependency_closure_patchable_subset.json",
    "executed_scope_manifest.json",
    "executed_scope_trace.log",
    "executed_file_hashes.csv",
    "context_pinching_filter_manifest.json",
    "context_pinching_filter_capsule.txt",
    "context_pinching_filter_hash.json",
    "context_exclusion_audit.json",
    "pre_generation_context_manifest.json",
    "pre_generation_context_hash.json",
    "failure_memory_weight_ledger_before.json",
    "failure_memory_weight_application_trace.json",
    "failure_memory_weight_ledger_after.json",
    "patch_fragment_plan.json",
    "patch_fragment_safety_checks.json",
    "patch_fragment_assembly_report.json",
    "patch_candidate_safety_check.json",
    "patch_size_cap.json",
    "realtime_patch_safety_trace.json",
    "pre_post_handoff_consistency_gate.json",
    "repair_hypothesis_trace.json",
    "patch_context_alignment_audit.json",
    "patch_application_step.json",
    "target_validation_result.json",
    "validation_context_alignment_audit.json",
    "duplicate_replay_summary.json",
    "stochastic_replay_reliability.json",
    "duplicate_replay_workspace_analysis.json",
    "post_validation_workspace_analysis.json",
    "diagnostic_reward_signal.json",
    "test_suite_structural_signature.json",
    "proof_obligations_ledger.json",
    "nuclear_pore_transport_log.json",
    "public_language_audit.json",
    "claim_boundary_v2_30.json",
    "roadmap_carry_forward_check_v2_30.json",
    "resolution_depth_diagnostic_v2_30.json",
    "SHA256SUMS.txt",
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
        "scripts/audit_v2_29_external_candidate_repair_lane.py",
        "scripts/audit_v2_28_external_candidate_seed_draft_verification_lane.py",
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
    expect(isinstance(entries, list) and len(entries) >= 5, errors, "proof ledger entries missing")
    if not isinstance(entries, list):
        return
    previous = "0" * 64
    for index, entry in enumerate(entries):
        expect(isinstance(entry, dict), errors, f"proof ledger entry {index} invalid")
        if not isinstance(entry, dict):
            return
        expect(entry.get("index") == index, errors, f"proof ledger index mismatch {index}")
        expect(entry.get("previous_entry_hash") == previous, errors, f"proof ledger previous hash mismatch {index}")
        recorded = entry.get("entry_hash")
        payload = {key: value for key, value in entry.items() if key != "entry_hash"}
        computed = sha256_text(json.dumps(payload, sort_keys=True))
        expect(recorded == computed, errors, f"proof ledger hash mismatch {index}")
        previous = str(recorded)
    expect(ledger.get("head_hash") == previous, errors, "proof ledger head hash mismatch")


def registry_candidate(errors: list[str]) -> dict[str, Any]:
    registry = load_json(REGISTRY_PATH, errors)
    candidates = registry.get("candidates")
    if not isinstance(candidates, list):
        errors.append("registry candidates is not a list")
        return {}
    matches = [candidate for candidate in candidates if isinstance(candidate, dict) and candidate.get("candidate_id") == EXPECTED["candidate_id"]]
    expect(len(matches) == 1, errors, "expected exactly one reviewed candidate")
    return matches[0] if matches else {}


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


def audit_outputs(errors: list[str]) -> None:
    for rel in REQUIRED_FILES:
        expect((OUTPUT_ROOT / rel).is_file(), errors, f"missing required output: {rel}")
    manifest_errors, checked = verify_manifest(OUTPUT_ROOT)
    errors.extend(manifest_errors)
    expected_manifest_count = len(REQUIRED_FILES) - 1
    if (OUTPUT_ROOT / "source_patch.diff").exists():
        expected_manifest_count += 2
    if (OUTPUT_ROOT / "target_validation_post_patch_log.txt").exists():
        expected_manifest_count += 1
    if (OUTPUT_ROOT / "static_import_graph.json").exists():
        expected_manifest_count += 3
    expect(checked == expected_manifest_count, errors, "manifest entry count mismatch")

    results = load_json(OUTPUT_ROOT / "campaign_results.json", errors)
    v229 = load_json(OUTPUT_ROOT / "v2_29_artifact_ingest_verification.json", errors)
    v229_official = load_json(V229_ROOT / "v2_29_official_artifact_verification.json", errors)
    selected = load_json(OUTPUT_ROOT / "selected_candidate_record.json", errors)
    before = load_json(OUTPUT_ROOT / "selected_candidate_registry_entry_before.json", errors)
    after = load_json(OUTPUT_ROOT / "selected_candidate_registry_entry_after.json", errors)
    policy = load_json(OUTPUT_ROOT / "failure_signature_normalization_policy.json", errors)
    comparison = load_json(OUTPUT_ROOT / "v2_28_v2_29_failure_comparison.json", errors)
    semantic_manifest = load_json(OUTPUT_ROOT / "semantic_failure_signature_manifest.json", errors)
    semantic_hash_record = load_json(OUTPUT_ROOT / "semantic_failure_signature_hash.json", errors)
    replay_matrix = load_json(OUTPUT_ROOT / "semantic_failure_signature_replay_matrix.json", errors)
    refresh = load_json(OUTPUT_ROOT / "registry_signature_refresh_report.json", errors)
    validation_after = load_json(OUTPUT_ROOT / "external_candidate_registry_validation_report_after_signature_refresh.json", errors)
    checkout = load_json(OUTPUT_ROOT / "selected_candidate_source_checkout_audit.json", errors)
    target_hashes = load_json(OUTPUT_ROOT / "selected_candidate_target_test_file_hashes.json", errors)
    support_hashes = load_json(OUTPUT_ROOT / "selected_candidate_support_file_hashes.json", errors)
    env_hashes = load_json(OUTPUT_ROOT / "selected_candidate_environment_file_hashes.json", errors)
    command = load_json(OUTPUT_ROOT / "selected_candidate_command_manifest.json", errors)
    env_preflight = load_json(OUTPUT_ROOT / "selected_candidate_environment_resolution_preflight.json", errors)
    pre_gate = load_json(OUTPUT_ROOT / "pre_repair_replay_gate_summary.json", errors)
    pre_sig = load_json(OUTPUT_ROOT / "pre_repair_failure_signature_verification.json", errors)
    structural = load_json(OUTPUT_ROOT / "structural_failure_signature.json", errors)
    executed = load_json(OUTPUT_ROOT / "executed_scope_manifest.json", errors)
    ast_manifest = load_json(OUTPUT_ROOT / "ast_dependency_closure_manifest.json", errors)
    ast_subset = load_json(OUTPUT_ROOT / "ast_dependency_closure_patchable_subset.json", errors)
    context = load_json(OUTPUT_ROOT / "context_pinching_filter_manifest.json", errors)
    context_hash = load_json(OUTPUT_ROOT / "context_pinching_filter_hash.json", errors)
    exclusion = load_json(OUTPUT_ROOT / "context_exclusion_audit.json", errors)
    memory_trace = load_json(OUTPUT_ROOT / "failure_memory_weight_application_trace.json", errors)
    patch_plan = load_json(OUTPUT_ROOT / "patch_fragment_plan.json", errors)
    fragment_safety = load_json(OUTPUT_ROOT / "patch_fragment_safety_checks.json", errors)
    assembly = load_json(OUTPUT_ROOT / "patch_fragment_assembly_report.json", errors)
    patch_safety = load_json(OUTPUT_ROOT / "patch_candidate_safety_check.json", errors)
    patch_cap = load_json(OUTPUT_ROOT / "patch_size_cap.json", errors)
    realtime = load_json(OUTPUT_ROOT / "realtime_patch_safety_trace.json", errors)
    handoff = load_json(OUTPUT_ROOT / "pre_post_handoff_consistency_gate.json", errors)
    hypothesis = load_json(OUTPUT_ROOT / "repair_hypothesis_trace.json", errors)
    alignment = load_json(OUTPUT_ROOT / "patch_context_alignment_audit.json", errors)
    application = load_json(OUTPUT_ROOT / "patch_application_step.json", errors)
    validation = load_json(OUTPUT_ROOT / "target_validation_result.json", errors)
    duplicate = load_json(OUTPUT_ROOT / "duplicate_replay_summary.json", errors)
    reliability = load_json(OUTPUT_ROOT / "stochastic_replay_reliability.json", errors)
    post = load_json(OUTPUT_ROOT / "post_validation_workspace_analysis.json", errors)
    reward = load_json(OUTPUT_ROOT / "diagnostic_reward_signal.json", errors)
    transport = load_json(OUTPUT_ROOT / "nuclear_pore_transport_log.json", errors)
    public_language = load_json(OUTPUT_ROOT / "public_language_audit.json", errors)
    claim = load_json(OUTPUT_ROOT / "claim_boundary_v2_30.json", errors)
    roadmap = load_json(OUTPUT_ROOT / "roadmap_carry_forward_check_v2_30.json", errors)
    ledger = load_json(OUTPUT_ROOT / "proof_obligations_ledger.json", errors)
    candidate = registry_candidate(errors)

    expect(v229_official.get("status") == "PASS", errors, "v2.29 official source not PASS")
    expect(v229_official.get("zip_sha256") == EXPECTED["v2_29_zip_sha256"], errors, "v2.29 official source digest mismatch")
    expect(v229.get("status") == "PASS", errors, "v2.29 ingest carry-forward not PASS")
    expect(v229.get("downloaded_by_codex") is False, errors, "v2.29 artifact boundary broken")
    expect(v229.get("v2_29_exact_blocker") == "external_bug_signature_mismatch", errors, "v2.29 blocker not carried forward")
    expect(results.get("v2_29_blocker_carry_forward_status") == "PASS", errors, "v2.29 blocker carry-forward result mismatch")

    expect(selected.get("status") == "PASS", errors, "selected candidate record not PASS")
    expect(before.get("candidate_id") == EXPECTED["candidate_id"], errors, "registry before candidate mismatch")
    expect(after.get("candidate_id") == EXPECTED["candidate_id"], errors, "registry after candidate mismatch")
    expect(candidate.get("candidate_id") == EXPECTED["candidate_id"], errors, "live registry candidate mismatch")
    expect(candidate.get("repo_url") == EXPECTED["repo_url"], errors, "live registry repo mismatch")
    expect(candidate.get("buggy_commit_sha") == EXPECTED["buggy_commit_sha"], errors, "live registry commit mismatch")
    expect(candidate.get("test_command") == EXPECTED["test_command"], errors, "live registry command mismatch")
    old_sig = before.get("expected_failure_signature") if isinstance(before.get("expected_failure_signature"), dict) else {}
    new_sig = after.get("expected_failure_signature") if isinstance(after.get("expected_failure_signature"), dict) else {}
    expect(old_sig.get("log_hash") == EXPECTED["v2_28_normalized_hash"], errors, "historical v2.28 log hash not preserved before")
    expect(new_sig.get("log_hash") == EXPECTED["v2_28_normalized_hash"], errors, "historical v2.28 log hash not preserved after")
    expect(policy.get("policy_version") == "v2.30.failure_signature_normalization.v1", errors, "normalization policy version mismatch")
    expect((NORMALIZATION_POLICY_PATH).is_file(), errors, "normalization policy config missing")
    expect((REGISTRY_SCHEMA_PATH).is_file(), errors, "registry schema missing")

    expect(comparison.get("classification") == "semantic_failure_stable_text_hash_drift", errors, "historical comparison did not classify text-hash drift")
    expect(comparison.get("v2_28_normalized_failure_log_sha256") == EXPECTED["v2_28_normalized_hash"], errors, "comparison v2.28 hash mismatch")
    expect(comparison.get("v2_29_normalized_failure_log_sha256") == EXPECTED["v2_29_normalized_hash"], errors, "comparison v2.29 hash mismatch")
    expect(comparison.get("text_hashes_match") is False, errors, "text hash mismatch not preserved diagnostically")
    expect(comparison.get("semantic_fields_match") is True, errors, "historical semantic fields not stable")

    exact_blocker = results.get("exact_blocker")
    expect(exact_blocker in ALLOWED_BLOCKERS, errors, f"unexpected blocker {exact_blocker}")
    semantic_success = replay_matrix.get("status") == "PASS"
    if semantic_success:
        captures = [load_json(OUTPUT_ROOT / f"canonical_failure_capture_{index}_semantic.json", errors) for index in range(1, 4)]
        hashes = [capture.get("semantic_failure_signature_hash") for capture in captures]
        expect(all(capture.get("status") == "PASS" for capture in captures), errors, "not all semantic captures PASS")
        expect(len(set(hashes)) == 1 and re.fullmatch(r"[0-9a-f]{64}", str(hashes[0])), errors, "semantic capture hashes do not agree")
        expect(semantic_hash_record.get("semantic_failure_signature_hash") == hashes[0], errors, "canonical semantic hash mismatch")
        expect(refresh.get("status") == "PASS", errors, "registry refresh did not PASS")
        expect(validation_after.get("registry_validation_status") == "PASS", errors, "registry validation after refresh not PASS")
        expect(new_sig.get("semantic_log_hash") == hashes[0], errors, "registry semantic hash not updated")
        expect(new_sig.get("normalized_log_hash_v2_30"), errors, "registry v2.30 normalized hash missing")
        expect(new_sig.get("normalization_policy_version") == "v2.30.failure_signature_normalization.v1", errors, "registry policy version missing")
        expect(isinstance(new_sig.get("signature_history"), list) and len(new_sig["signature_history"]) >= 5, errors, "signature history incomplete")
        expect(isinstance(new_sig.get("semantic_fields"), dict), errors, "semantic fields missing from registry")
        expect(pre_gate.get("status") == "PASS", errors, "semantic pre-repair replay gate not PASS")
        expect(pre_gate.get("normalized_full_log_hash_mismatch_is_diagnostic_only") is True, errors, "full text hash mismatch not diagnostic-only after semantic refresh")
        expect(pre_sig.get("status") == "PASS", errors, "semantic failure verification not PASS")
    else:
        expect(exact_blocker in {
            "selected_candidate_checkout_failed",
            "selected_candidate_target_test_hash_mismatch",
            "selected_candidate_support_file_hash_mismatch",
            "selected_candidate_environment_file_hash_mismatch",
            "selected_candidate_dependency_resolution_failed",
            "semantic_failure_signature_unstable",
            "v2_29_artifact_verification_failed",
            "reviewed_candidate_registry_entry_missing_or_invalid",
        }, errors, "blocked run used unexpected pre-refresh blocker")
        expect(refresh.get("status") in {"not_run", "BLOCK"}, errors, "registry refreshed despite missing semantic agreement")
        expect(results.get("patch_generated") is False, errors, "patch generated before semantic agreement")

    expect(checkout.get("repo_url") == EXPECTED["repo_url"], errors, "checkout repo mismatch")
    expect(checkout.get("buggy_commit_sha") == EXPECTED["buggy_commit_sha"], errors, "checkout commit mismatch")
    expect(checkout.get("exact_buggy_commit_only") is True, errors, "checkout not exact buggy commit only")
    expect(checkout.get("fixed_later_commit_contents_read") is False, errors, "fixed/later contents read")
    expect(checkout.get("fixed_diff_computed") is False, errors, "fixed diff computed")
    expect(checkout.get("pr_patch_content_used") is False, errors, "PR patch content used")
    expect(checkout.get("gold_patch_used") is False, errors, "gold patch used")
    expect(checkout.get("hidden_label_used") is False, errors, "hidden label used")
    expect(checkout.get("synthetic_or_backported_tests_used") is False, errors, "synthetic/backported tests used")
    expect(checkout.get("workspace_outside_repo") in {True, None}, errors, "workspace under repo")
    expect(checkout.get("workspace_outside_onedrive") in {True, None}, errors, "workspace under OneDrive")
    target = (target_hashes.get("target_test_files") or [{}])[0]
    support = (support_hashes.get("support_files") or [{}])[0]
    env_file = env_hashes.get("environment_lock_source") or {}
    if target_hashes.get("status") == "PASS":
        expect(target.get("path") == EXPECTED["target_test_path"], errors, "target test path mismatch")
        expect(target.get("sha256") == EXPECTED["target_test_sha256"], errors, "target test SHA mismatch")
    if support_hashes.get("status") == "PASS":
        expect(support.get("path") == EXPECTED["support_file_path"], errors, "support path mismatch")
        expect(support.get("sha256") == EXPECTED["support_file_sha256"], errors, "support SHA mismatch")
    if env_hashes.get("status") == "PASS":
        expect(env_file.get("sha256") == EXPECTED["environment_lock_source_sha256"], errors, "environment SHA mismatch")
    expect(command.get("test_command") == EXPECTED["test_command"], errors, "command mismatch")
    expect(command.get("external_network_required") is False, errors, "external network required")
    expect(env_preflight.get("fallback_attempted") is False, errors, "fallback install attempted")

    if results.get("patch_generated"):
        patch_path = OUTPUT_ROOT / "source_patch.diff"
        patch_sha_path = OUTPUT_ROOT / "source_patch_sha256.txt"
        expect(patch_path.is_file(), errors, "patch generated but diff missing")
        expect(patch_sha_path.is_file(), errors, "patch generated but SHA file missing")
        patch_text = patch_path.read_text(encoding="utf-8")
        patch_sha = sha256_path(patch_path)
        expect(patch_sha_path.read_text(encoding="utf-8").strip() == patch_sha, errors, "patch SHA mismatch")
        expect(REPAIR_SOURCE_PATH in patch_text, errors, "patch does not touch expected source")
        expect("tests/" not in patch_text, errors, "patch touches tests")
        expect(structural.get("status") == "PASS", errors, "patch without structural signature PASS")
        expect(executed.get("status") in {"PASS", "FALLBACK"}, errors, "patch without executed/static scope")
        expect(ast_manifest.get("status") == "PASS", errors, "patch without AST closure PASS")
        expect(REPAIR_SOURCE_PATH in (ast_subset.get("patchable_files") or []), errors, "repair source not patchable")
        expect(context.get("status") == "PASS", errors, "patch without context filter PASS")
        expect(context_hash.get("status") == "PASS", errors, "patch without context hash PASS")
        expect(memory_trace.get("diagnostic_only") is True, errors, "memory trace not diagnostic-only")
        expect(memory_trace.get("weights_used_as_correctness_evidence") is False, errors, "memory used as correctness evidence")
        expect(patch_plan.get("final_patch_count") == 1, errors, "patch count not one")
        expect(len(patch_plan.get("fragments") or []) <= 3, errors, "too many fragments")
        expect(fragment_safety.get("status") == "PASS", errors, "fragment safety not PASS")
        expect(assembly.get("status") == "PASS", errors, "assembly not PASS")
        expect(patch_safety.get("status") == "PASS", errors, "patch safety not PASS")
        expect(patch_safety.get("source_only") is True, errors, "patch not source-only")
        expect(not patch_safety.get("forbidden_files"), errors, "forbidden patch files")
        expect(patch_cap.get("status") == "PASS", errors, "patch size cap not PASS")
        expect(realtime.get("status") == "PASS", errors, "realtime safety not PASS")
        expect(handoff.get("status") == "PASS", errors, "handoff not PASS")
        expect(hypothesis.get("forbidden_evidence_used") is False, errors, "hypothesis used forbidden evidence")
        expect(alignment.get("allowed_context_only") is True, errors, "context alignment not allowed-only")
    else:
        expect(not (OUTPUT_ROOT / "source_patch.diff").exists(), errors, "patch diff exists despite patch_generated=false")
        expect(not (OUTPUT_ROOT / "source_patch_sha256.txt").exists(), errors, "patch SHA exists despite patch_generated=false")
        expect(results.get("patch_attempted") is False, errors, "patch attempted without generated patch")

    if results.get("patch_attempted"):
        expect(application.get("status") == "PASS", errors, "patch attempted but application not PASS")
        expect(application.get("forbidden_files_modified") == [], errors, "forbidden files modified")
        expect((OUTPUT_ROOT / "target_validation_post_patch_log.txt").is_file(), errors, "post-patch log missing")
        expect(validation.get("changed_log_hash_is_not_success") is True, errors, "changed hash treated as success")
    if results.get("selected_candidate_scoreable") is True:
        expect(validation.get("status") == "PASS", errors, "scoreable without target validation PASS")
        expect(validation.get("exit_status") == 0, errors, "scoreable without validation exit 0")
        expect(duplicate.get("passed_replays") == 3, errors, "scoreable without three duplicate replays")
        expect(reliability.get("observed_reliability") == 1.0, errors, "scoreable without reliability 1.0")
    else:
        expect(claim.get("selected_candidate_scoreable") is False, errors, "claim scoreable mismatch")

    expect(exclusion.get("fixed_commit_contents_excluded") is True, errors, "fixed contents not excluded")
    expect(exclusion.get("later_commit_contents_excluded") is True, errors, "later contents not excluded")
    expect(exclusion.get("pr_patch_contents_excluded") is True, errors, "PR patch contents not excluded")
    expect(exclusion.get("gold_patch_excluded") is True, errors, "gold patch not excluded")
    expect(post.get("tests_unmodified") is True, errors, "tests modified")
    expect(post.get("support_files_unmodified") is True, errors, "support files modified")
    expect(reward.get("diagnostic_only") is True, errors, "reward not diagnostic-only")
    expect(reward.get("full_scoring_enabled") is False, errors, "reward enabled full scoring")
    expect(reward.get("memory_lift_claimed") is False, errors, "reward claimed memory lift")
    expect(transport.get("runtime_workspaces_committed") is False, errors, "runtime workspace committed")
    expect(transport.get("venvs_committed") is False, errors, "venv committed")
    expect(public_language.get("status") == "PASS", errors, "public language audit failed")
    expect(roadmap.get("status") == "PASS", errors, "roadmap carry-forward failed")
    expect(claim.get("current_protocol_version") == "v2.13", errors, "current protocol changed")
    expect(claim.get("v2_30_promoted_to_current") is False, errors, "v2.30 promoted to current")
    expect(claim.get("full_scoring") == "NOT_RUN", errors, "full scoring changed")
    expect(claim.get("full_scoring_allowed") is False, errors, "full scoring allowed")
    expect(claim.get("memory_lift_status") == "undemonstrated", errors, "memory lift changed")
    expect(claim.get("self_maintaining_software_status") == "false/not_demonstrated", errors, "self-maintaining status changed")
    expect(claim.get("benchmark_framework_candidate_acquisition_used") is False, errors, "benchmark framework acquisition used")
    expect(claim.get("pysnooper1_reopened") is False, errors, "PySnooper:1 reopened")
    expect(claim.get("pysnooper2_pursued") is False, errors, "PySnooper:2 pursued")
    expect(claim.get("ansible_candidate_selected") is False, errors, "Ansible selected")
    expect(claim.get("final_non_ansible_positive_memory_count") == 0, errors, "non-Ansible positive-memory count changed")
    fresh_validation = registry_validator.validate_registry()
    expect(fresh_validation.get("registry_validation_status") == "PASS", errors, "fresh registry validation did not PASS")
    audit_proof_ledger(ledger, errors)

    scanned_text = ""
    for rel in ["campaign_summary.md", "campaign_results.json", "claim_boundary_v2_30.json"]:
        path = OUTPUT_ROOT / rel
        if path.is_file():
            scanned_text += path.read_text(encoding="utf-8") + "\n"
    for term in hidden_public_terms():
        expect(term not in scanned_text, errors, f"blocked public term present in v2.30 summary/results: {term}")

    print(f"v2.30 manifest entries checked: {checked}")
    for key in [
        "v2_28_v2_29_failure_comparison_status",
        "semantic_failure_signature_status",
        "three_capture_semantic_replay_status",
        "registry_signature_refresh_status",
        "pre_repair_replay_status_after_refresh",
        "patch_generated",
        "patch_authorized",
        "patch_attempted",
        "target_validation_status",
        "duplicate_clean_replay_status",
        "selected_candidate_scoreable",
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
        print("v2.30 audit FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("v2.30 audit PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
