#!/usr/bin/env python3
"""Audit v2.29 External Candidate Repair Lane evidence."""

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
CAMPAIGN_ID = "v2_29_external_candidate_repair_lane"
OUTPUT_ROOT = REPO_ROOT / "outputs" / CAMPAIGN_ID
REGISTRY_PATH = REPO_ROOT / "configs" / "external_candidate_registry.json"
CAPABILITY_PLAN_PATH = REPO_ROOT / "docs" / "structural_repair_capability_plan.md"
CAPABILITY_MATRIX_PATH = REPO_ROOT / "configs" / "structural_repair_capability_matrix.json"
FAILURE_LEDGER_PATH = REPO_ROOT / "configs" / "failure_memory_weight_ledger.json"
V228_ROOT = REPO_ROOT / "outputs" / "v2_28_external_candidate_seed_draft_verification_lane"
V223_ROOT = REPO_ROOT / "outputs" / "v2_23_non_ansible_candidate_transition_lane"

EXPECTED = {
    "candidate_id": "py_bugger_issue_65",
    "repo_url": "https://github.com/ehmatthes/py-bugger",
    "buggy_commit_sha": "67cf214f2d619848e90280fd4469377123e81b94",
    "test_command": "python -m pytest tests/integration_tests/test_modifications.py::test_indentationerror_multiple_trys -q",
    "target_test_path": "tests/integration_tests/test_modifications.py",
    "target_test_sha256": "3e3c9521a4c1084df9269fb6bd38cb47808061559d7eb3eafa3fd78f4f3965b1",
    "support_file_path": "tests/sample_code/sample_scripts/two_trys.py",
    "support_file_sha256": "66a72a7abc6f2bffec7881d0a5b0a006deb408a8c496148210e14caafd1a2d11",
    "environment_lock_source": "pyproject.toml",
    "environment_lock_source_sha256": "2f1fe04032ca64b556e4db66a1aa5af3c81ccc958735a390226ea1b987484631",
    "expected_normalized_log_hash": "a97ccd92654e725d3c54d88ece253973a8d98e7f4d1b5a42c4ca921a433dd2ea",
    "expected_raw_log_sha256": "f2a152ff6a8f3d6e4b70d817123917b992bd1b4d381e2d492f48838250fd6cdb",
    "expected_failure_type": "IndentationError",
    "expected_failing_file": "developer_resources/sample_attribute_node.py",
    "expected_failure_excerpt_hash": "cd64bae3e95407659c36a05e0f30d50a7a91bb620932fbffa3e3d97dda5660c6",
}
ALLOWED_BLOCKERS = {
    None,
    "reviewed_candidate_registry_entry_missing_or_invalid",
    "selected_candidate_registry_evidence_mismatch",
    "selected_candidate_checkout_failed",
    "selected_candidate_target_test_hash_mismatch",
    "selected_candidate_support_file_hash_mismatch",
    "selected_candidate_environment_file_hash_mismatch",
    "selected_candidate_dependency_resolution_failed",
    "pre_repair_environmental_pass_blocked",
    "external_bug_signature_mismatch",
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
    "v2_28_artifact_ingest_verification.json",
    "artifact_repo_snapshot_comparison.json",
    "missing_capability_resolution_map_v2_29.json",
    "structural_repair_capability_coverage_v2_29.json",
    "selected_candidate_record.json",
    "selected_candidate_registry_entry_verification.json",
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
    "claim_boundary_v2_29.json",
    "roadmap_carry_forward_check_v2_29.json",
    "resolution_depth_diagnostic_v2_29.json",
    "SHA256SUMS.txt",
]


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
    expect(isinstance(entries, list) and len(entries) >= 7, errors, "proof ledger entries missing")
    if not isinstance(entries, list):
        return
    previous = "0" * 64
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            errors.append(f"proof ledger entry {index} is not an object")
            return
        expect(entry.get("index") == index, errors, f"proof ledger index mismatch at {index}")
        expect(entry.get("previous_entry_hash") == previous, errors, f"proof ledger previous hash mismatch at {index}")
        recorded = entry.get("entry_hash")
        payload = {key: value for key, value in entry.items() if key != "entry_hash"}
        computed = hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()
        expect(recorded == computed, errors, f"proof ledger hash mismatch at {index}")
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
    v228_ingest = load_json(OUTPUT_ROOT / "v2_28_artifact_ingest_verification.json", errors)
    v228_official = load_json(V228_ROOT / "v2_28_official_artifact_verification.json", errors)
    selected = load_json(OUTPUT_ROOT / "selected_candidate_record.json", errors)
    registry_verification = load_json(OUTPUT_ROOT / "selected_candidate_registry_entry_verification.json", errors)
    checkout = load_json(OUTPUT_ROOT / "selected_candidate_source_checkout_audit.json", errors)
    target_hashes = load_json(OUTPUT_ROOT / "selected_candidate_target_test_file_hashes.json", errors)
    support_hashes = load_json(OUTPUT_ROOT / "selected_candidate_support_file_hashes.json", errors)
    env_hashes = load_json(OUTPUT_ROOT / "selected_candidate_environment_file_hashes.json", errors)
    command = load_json(OUTPUT_ROOT / "selected_candidate_command_manifest.json", errors)
    env_preflight = load_json(OUTPUT_ROOT / "selected_candidate_environment_resolution_preflight.json", errors)
    pre_gate = load_json(OUTPUT_ROOT / "pre_repair_replay_gate_summary.json", errors)
    pre_signature = load_json(OUTPUT_ROOT / "pre_repair_failure_signature_verification.json", errors)
    structural = load_json(OUTPUT_ROOT / "structural_failure_signature.json", errors)
    executed = load_json(OUTPUT_ROOT / "executed_scope_manifest.json", errors)
    ast_manifest = load_json(OUTPUT_ROOT / "ast_dependency_closure_manifest.json", errors)
    ast_subset = load_json(OUTPUT_ROOT / "ast_dependency_closure_patchable_subset.json", errors)
    context_manifest = load_json(OUTPUT_ROOT / "context_pinching_filter_manifest.json", errors)
    context_hash = load_json(OUTPUT_ROOT / "context_pinching_filter_hash.json", errors)
    exclusion = load_json(OUTPUT_ROOT / "context_exclusion_audit.json", errors)
    pre_context_hash = load_json(OUTPUT_ROOT / "pre_generation_context_hash.json", errors)
    memory_trace = load_json(OUTPUT_ROOT / "failure_memory_weight_application_trace.json", errors)
    memory_after = load_json(OUTPUT_ROOT / "failure_memory_weight_ledger_after.json", errors)
    fragment_plan = load_json(OUTPUT_ROOT / "patch_fragment_plan.json", errors)
    fragment_safety = load_json(OUTPUT_ROOT / "patch_fragment_safety_checks.json", errors)
    assembly = load_json(OUTPUT_ROOT / "patch_fragment_assembly_report.json", errors)
    patch_safety = load_json(OUTPUT_ROOT / "patch_candidate_safety_check.json", errors)
    patch_cap = load_json(OUTPUT_ROOT / "patch_size_cap.json", errors)
    realtime = load_json(OUTPUT_ROOT / "realtime_patch_safety_trace.json", errors)
    handoff = load_json(OUTPUT_ROOT / "pre_post_handoff_consistency_gate.json", errors)
    hypothesis = load_json(OUTPUT_ROOT / "repair_hypothesis_trace.json", errors)
    context_alignment = load_json(OUTPUT_ROOT / "patch_context_alignment_audit.json", errors)
    application = load_json(OUTPUT_ROOT / "patch_application_step.json", errors)
    validation = load_json(OUTPUT_ROOT / "target_validation_result.json", errors)
    validation_alignment = load_json(OUTPUT_ROOT / "validation_context_alignment_audit.json", errors)
    duplicate = load_json(OUTPUT_ROOT / "duplicate_replay_summary.json", errors)
    reliability = load_json(OUTPUT_ROOT / "stochastic_replay_reliability.json", errors)
    post_analysis = load_json(OUTPUT_ROOT / "post_validation_workspace_analysis.json", errors)
    reward = load_json(OUTPUT_ROOT / "diagnostic_reward_signal.json", errors)
    transport = load_json(OUTPUT_ROOT / "nuclear_pore_transport_log.json", errors)
    public_language = load_json(OUTPUT_ROOT / "public_language_audit.json", errors)
    claim = load_json(OUTPUT_ROOT / "claim_boundary_v2_29.json", errors)
    roadmap = load_json(OUTPUT_ROOT / "roadmap_carry_forward_check_v2_29.json", errors)
    coverage = load_json(OUTPUT_ROOT / "structural_repair_capability_coverage_v2_29.json", errors)
    ledger = load_json(OUTPUT_ROOT / "proof_obligations_ledger.json", errors)
    matrix = load_json(CAPABILITY_MATRIX_PATH, errors)
    candidate = registry_candidate(errors)
    v223_block = load_json(V223_ROOT / "global_bugsinpy_provenance_block.json", errors)

    expect(v228_official.get("status") == "PASS", errors, "v2.28 official verification source not PASS")
    expect(v228_ingest.get("status") == "PASS", errors, "v2.28 ingest carry-forward not PASS")
    expect(v228_ingest.get("workflow_run_id") == 28264407539, errors, "v2.28 workflow run mismatch")
    expect(v228_ingest.get("artifact_id") == 7916096076, errors, "v2.28 artifact id mismatch")
    expect(v228_ingest.get("zip_sha256") == "1b7b905b5708063c9cdeb43e5dd6eafdf868b62b05ab3daa67cb2928c85071e1", errors, "v2.28 digest mismatch")
    expect(v223_block.get("status") == "BLOCK", errors, "benchmark framework global block not carried forward")
    expect(v223_block.get("candidate_selection_allowed") is False, errors, "benchmark framework selection not blocked")

    fresh_validation = registry_validator.validate_registry()
    expect(fresh_validation.get("registry_validation_status") == "PASS", errors, "fresh registry validation did not PASS")
    expect(candidate.get("candidate_id") == EXPECTED["candidate_id"], errors, "registry candidate id mismatch")
    expect(candidate.get("registry_review_status") == "reviewed", errors, "registry candidate not reviewed")
    expect(candidate.get("repo_url") == EXPECTED["repo_url"], errors, "registry repo mismatch")
    expect(candidate.get("buggy_commit_sha") == EXPECTED["buggy_commit_sha"], errors, "registry commit mismatch")
    expect(candidate.get("test_command") == EXPECTED["test_command"], errors, "registry command mismatch")
    signature = candidate.get("expected_failure_signature") if isinstance(candidate.get("expected_failure_signature"), dict) else {}
    expect(signature.get("log_hash") == EXPECTED["expected_normalized_log_hash"], errors, "registry expected normalized hash mismatch")
    expect(signature.get("exception_type") == EXPECTED["expected_failure_type"], errors, "registry expected failure type mismatch")
    expect(signature.get("failing_file") == EXPECTED["expected_failing_file"], errors, "registry expected failing file mismatch")
    expect(signature.get("failure_text_excerpt_hash") == EXPECTED["expected_failure_excerpt_hash"], errors, "registry expected excerpt hash mismatch")
    expect(selected.get("candidate", {}).get("candidate_id") == EXPECTED["candidate_id"], errors, "selected candidate mismatch")
    expect(registry_verification.get("status") == "PASS", errors, "selected candidate verification did not PASS")

    expect(checkout.get("repo_url") == EXPECTED["repo_url"], errors, "checkout repo mismatch")
    expect(checkout.get("buggy_commit_sha") == EXPECTED["buggy_commit_sha"], errors, "checkout commit mismatch")
    expect(checkout.get("exact_buggy_commit_only") is True, errors, "checkout not exact buggy commit only")
    expect(checkout.get("fixed_later_commit_contents_read") is False, errors, "fixed/later contents read")
    expect(checkout.get("fixed_diff_computed") is False, errors, "fixed diff computed")
    expect(checkout.get("pr_patch_content_used") is False, errors, "PR patch content used")
    expect(checkout.get("gold_patch_used") is False, errors, "gold patch used")
    expect(checkout.get("hidden_label_used") is False, errors, "hidden label used")
    expect(checkout.get("workspace_outside_repo") is True, errors, "runtime workspace not outside repo")
    expect(checkout.get("workspace_outside_onedrive") is True, errors, "runtime workspace under OneDrive")
    target = (target_hashes.get("target_test_files") or [{}])[0]
    support = (support_hashes.get("support_files") or [{}])[0]
    env_file = env_hashes.get("environment_lock_source") or {}
    expect(target.get("path") == EXPECTED["target_test_path"], errors, "target test path mismatch")
    expect(target.get("sha256") == EXPECTED["target_test_sha256"], errors, "target test SHA mismatch")
    expect(support.get("path") == EXPECTED["support_file_path"], errors, "support file path mismatch")
    expect(support.get("sha256") == EXPECTED["support_file_sha256"], errors, "support file SHA mismatch")
    expect(env_file.get("path") == EXPECTED["environment_lock_source"], errors, "environment source path mismatch")
    expect(env_file.get("sha256") == EXPECTED["environment_lock_source_sha256"], errors, "environment source SHA mismatch")
    expect(command.get("test_command") == EXPECTED["test_command"], errors, "command manifest mismatch")
    expect(command.get("external_network_required") is False, errors, "external network required")
    expect(env_preflight.get("fallback_attempted") is False, errors, "unexpected fallback install attempted")

    exact_blocker = results.get("exact_blocker")
    expect(exact_blocker in ALLOWED_BLOCKERS, errors, f"unexpected blocker {exact_blocker}")
    expect(pre_gate.get("target_executed") in {True, False}, errors, "pre-repair target execution missing")
    expect(pre_gate.get("expected_normalized_replay_log_sha256") == EXPECTED["expected_normalized_log_hash"], errors, "pre-repair expected hash mismatch")
    expect(pre_signature.get("artifact_hash_authoritative") is True, errors, "artifact hash not authoritative")
    if exact_blocker is None:
        expect(pre_gate.get("status") == "PASS", errors, "no blocker without pre-repair gate PASS")
        expect(pre_gate.get("normalized_hash_match") is True, errors, "no blocker without normalized hash match")
        expect(validation.get("status") == "PASS", errors, "no blocker without target validation PASS")
        expect(duplicate.get("status") == "PASS", errors, "no blocker without duplicate replay PASS")
        expect(reliability.get("observed_reliability") == 1.0, errors, "no blocker without replay reliability 1.0")
    else:
        if exact_blocker == "external_bug_signature_mismatch":
            expect(pre_gate.get("normalized_hash_match") is False, errors, "signature blocker without hash mismatch")
            expect(results.get("patch_attempted") is False, errors, "patch attempted after signature mismatch")

    expect(structural.get("target_test_node") == EXPECTED["test_command"], errors, "structural command mismatch")
    expect(structural.get("failure_excerpt_hash_expected") == EXPECTED["expected_failure_excerpt_hash"], errors, "structural excerpt expected mismatch")
    expect(executed.get("authorized_command") in {EXPECTED["test_command"], None}, errors, "executed scope command mismatch")
    expect(ast_manifest.get("status") in {"PASS", "BLOCK", "not_run_no_checkout"}, errors, "AST closure status invalid")
    if ast_manifest.get("status") == "PASS":
        patchable = ast_subset.get("patchable_files")
        expect(isinstance(patchable, list) and "src/py_bugger/utils/bug_utils.py" in patchable, errors, "repair source not in patchable subset")
        expect(all(isinstance(path, str) and path.startswith("src/") for path in patchable), errors, "non-source file in patchable subset")
    expect(context_manifest.get("forbidden_sources_excluded") is True, errors, "context forbidden-source exclusion failed")
    expect(exclusion.get("fixed_commit_contents_excluded") is True, errors, "fixed contents not excluded")
    expect(exclusion.get("later_commit_contents_excluded") is True, errors, "later contents not excluded")
    expect(exclusion.get("pr_patch_contents_excluded") is True, errors, "PR patch contents not excluded")
    expect(exclusion.get("gold_patch_excluded") is True, errors, "gold patch not excluded")
    expect(context_hash.get("context_pinching_filter_capsule_sha256") == pre_context_hash.get("sha256"), errors, "context hash mismatch")
    expect(memory_trace.get("diagnostic_only") is True, errors, "failure memory trace not diagnostic-only")
    expect(memory_trace.get("weights_used_as_correctness_evidence") is False, errors, "failure memory used as correctness evidence")
    expect(FAILURE_LEDGER_PATH.is_file(), errors, "failure memory ledger config missing")
    expect(isinstance(memory_after.get("entries"), list), errors, "failure memory ledger after missing entries")

    patch_generated = bool(results.get("patch_generated"))
    patch_authorized = bool(results.get("patch_authorized"))
    patch_attempted = bool(results.get("patch_attempted"))
    if patch_generated:
        patch_path = OUTPUT_ROOT / "source_patch.diff"
        patch_sha_path = OUTPUT_ROOT / "source_patch_sha256.txt"
        expect(patch_path.is_file(), errors, "patch generated but source_patch.diff missing")
        expect(patch_sha_path.is_file(), errors, "patch generated but source_patch_sha256 missing")
        patch_sha = sha256_path(patch_path)
        expect(patch_sha_path.read_text(encoding="utf-8").strip() == patch_sha, errors, "patch SHA file mismatch")
        patch_text = patch_path.read_text(encoding="utf-8")
        expect("src/py_bugger/utils/bug_utils.py" in patch_text, errors, "patch does not touch expected source")
        expect("tests/" not in patch_text, errors, "patch touches tests")
        expect(fragment_plan.get("final_patch_count") == 1, errors, "final patch count mismatch")
        expect(len(fragment_plan.get("fragments") or []) <= 3, errors, "too many patch fragments")
        expect(fragment_safety.get("status") == "PASS", errors, "fragment safety not PASS")
        expect(assembly.get("status") == "PASS", errors, "patch assembly not PASS")
        expect(assembly.get("assembled_once") is True, errors, "patch not assembled exactly once")
        expect(patch_safety.get("status") == "PASS", errors, "patch safety not PASS")
        expect(patch_safety.get("source_only") is True, errors, "patch not source-only")
        expect(not patch_safety.get("forbidden_files"), errors, "patch safety found forbidden files")
        expect(patch_cap.get("status") == "PASS", errors, "patch size cap not PASS")
        expect(realtime.get("status") == "PASS", errors, "realtime patch safety not PASS")
        expect(handoff.get("status") == "PASS", errors, "handoff gate not PASS")
        expect(hypothesis.get("forbidden_evidence_used") is False, errors, "hypothesis used forbidden evidence")
        expect(context_alignment.get("allowed_context_only") is True, errors, "patch context not allowed-only")
    else:
        expect(not (OUTPUT_ROOT / "source_patch.diff").exists(), errors, "source patch exists despite patch_generated=false")
        expect(not (OUTPUT_ROOT / "source_patch_sha256.txt").exists(), errors, "source patch SHA exists despite patch_generated=false")
        expect(patch_attempted is False, errors, "patch attempted without generated patch")

    if patch_attempted:
        expect((OUTPUT_ROOT / "target_validation_post_patch_log.txt").is_file(), errors, "patch attempted but post-patch log missing")
        expect(application.get("status") == "PASS", errors, "patch attempted but application not PASS")
        expect(application.get("forbidden_files_modified") == [], errors, "forbidden files modified")
        expect(validation_alignment.get("same_target_command") is True, errors, "validation target command mismatch")
        expect(validation_alignment.get("command_exit_status_authoritative") is True, errors, "validation not exit-status authoritative")
        expect(post_analysis.get("tests_unmodified") is True, errors, "tests modified")
        expect(post_analysis.get("support_files_unmodified") is True, errors, "support files modified")
        expect(post_analysis.get("dependency_config_workflow_files_unmodified") is True, errors, "dependency/config/workflow modified")
    if results.get("selected_candidate_scoreable") is True:
        expect(validation.get("status") == "PASS", errors, "scoreable without target validation PASS")
        expect(validation.get("exit_status") == 0, errors, "scoreable without validation exit 0")
        expect(duplicate.get("passed_replays") == 3, errors, "scoreable without 3 duplicate replays")
        expect(reliability.get("observed_reliability") == 1.0, errors, "scoreable without reliability 1.0")
    else:
        expect(claim.get("selected_candidate_scoreable") is False, errors, "claim scoreable mismatch")

    expect(reward.get("diagnostic_only") is True, errors, "reward not diagnostic-only")
    expect(reward.get("full_scoring_enabled") is False, errors, "reward enabled full scoring")
    expect(reward.get("memory_lift_claimed") is False, errors, "reward claimed memory lift")
    expect(transport.get("runtime_workspaces_committed") is False, errors, "runtime workspace committed")
    expect(transport.get("venvs_committed") is False, errors, "venv committed")
    expect(public_language.get("status") == "PASS", errors, "public language audit failed")
    expect(roadmap.get("status") == "PASS", errors, "roadmap carry-forward failed")
    expect(CAPABILITY_PLAN_PATH.is_file(), errors, "capability plan missing")
    expect(CAPABILITY_MATRIX_PATH.is_file(), errors, "capability matrix missing")
    expect(matrix.get("capabilities", {}).get("ast_dependency_closure") == "implemented_active", errors, "matrix AST closure status mismatch")
    for key, expected in {
        "ast_dependency_closure": "implemented_active",
        "context_pinching_filter": "implemented_active",
        "failure_memory_weight_ledger": "implemented_active_diagnostic_only",
        "fragmented_patch_assembly_gate": "implemented_bounded_single_patch",
        "pre_post_handoff_consistency_gate": "implemented_active",
        "multi_candidate_expansion": "not_run",
        "full_scoring": "not_run_disallowed",
        "memory_lift": "undemonstrated",
        "self_maintaining_software": "false_not_demonstrated",
    }.items():
        expect(coverage.get(key) == expected, errors, f"capability coverage {key} mismatch")
    expect(claim.get("current_protocol_version") == "v2.13", errors, "current protocol changed")
    expect(claim.get("v2_29_promoted_to_current") is False, errors, "v2.29 promoted to current")
    expect(claim.get("full_scoring") == "NOT_RUN", errors, "full scoring changed")
    expect(claim.get("full_scoring_allowed") is False, errors, "full scoring allowed")
    expect(claim.get("memory_lift_status") == "undemonstrated", errors, "memory lift claimed")
    expect(claim.get("self_maintaining_software_status") == "false/not_demonstrated", errors, "self-maintaining claim changed")
    expect(claim.get("benchmark_framework_candidate_acquisition_used") is False, errors, "benchmark framework acquisition used")
    expect(claim.get("pysnooper1_reopened") is False, errors, "PySnooper:1 reopened")
    expect(claim.get("pysnooper2_pursued") is False, errors, "PySnooper:2 pursued")
    expect(claim.get("ansible_candidate_selected") is False, errors, "Ansible candidate selected")
    expect(claim.get("final_non_ansible_positive_memory_count") == 0, errors, "non-Ansible positive-memory count changed")
    audit_proof_ledger(ledger, errors)

    print(f"v2.29 manifest entries checked: {checked}")
    for key in [
        "registry_verification_status",
        "pre_repair_replay_status",
        "pre_repair_normalized_hash_match_status",
        "ast_dependency_closure_status",
        "context_pinching_filter_status",
        "failure_memory_weight_ledger_status",
        "fragmented_patch_assembly_gate_status",
        "pre_post_handoff_consistency_gate_status",
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
        print("v2.29 audit FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("v2.29 audit PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
