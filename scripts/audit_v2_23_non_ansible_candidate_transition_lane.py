#!/usr/bin/env python3
"""Audit v2.23 source-acquisition method boundary evidence."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path, PurePosixPath
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_ROOT = REPO_ROOT / "outputs" / "v2_23_non_ansible_candidate_transition_lane"
V222_ROOT = REPO_ROOT / "outputs" / "v2_22_bugsinpy_target_test_materialization_lane"
CAMPAIGN_ID = "v2_23_non_ansible_candidate_transition_lane"
BUGSINPY_REPO = "https://github.com/soarsmu/BugsInPy.git"
BUGSINPY_COMMIT = "11c5f1eea954a42132cfd06bf257766a7963e0fd"
HARNESS_ORIGIN_SHA256 = "3706244b4618612fad4681578dd740d1e54dbe9069303072ab7802f656f0e608"
TARGET_TEST_SHA256 = "7a3d64cd702fdfa1eba8c08ac3c8934948a3ef0178f141c1f5599307c1fe59f3"
METHOD_ID = "bugsinpy_checkout_fixed_copy"
METHOD_SIGNATURE = "git_checkout_fixed_commit_then_copy_test_then_git_checkout_buggy_commit"
NORMALIZED_BEHAVIOR_SEQUENCE = "git_checkout_fixed_commit -> copy_target_test_or_harness_file -> git_checkout_buggy_commit"
BEHAVIORAL_SIGNATURE = hashlib.sha256(NORMALIZED_BEHAVIOR_SEQUENCE.encode("utf-8")).hexdigest()
BLOCKER = "blocked_bugsinpy_acquisition_method_fixed_commit_test_copy_global_or_unproven_candidate_specific_safety"
DECISION = "globally_blocked_under_current_provenance_rules"

REQUIRED_FILES = [
    "campaign_summary.md",
    "campaign_results.json",
    "v2_22_official_ingest_reference.json",
    "bugsinpy_acquisition_method_pattern_analysis.json",
    "bugsinpy_framework_checkout_logic_audit.json",
    "bugsinpy_fixed_copy_pattern_scan.json",
    "bugsinpy_checkout_offending_code_extract.json",
    "bugsinpy_checkout_offending_code_extract.txt",
    "bugsinpy_checkout_trace_to_source_mapping.json",
    "bugsinpy_runtime_trace_authority_record.json",
    "source_acquisition_method_risk_registry.json",
    "compound_provenance_combination_registry.json",
    "compound_provenance_combination_audit.json",
    "global_bugsinpy_provenance_block.json",
    "candidate_scope_expansion_required.json",
    "external_candidate_acquisition_recommendation.json",
    "v2_24_external_safe_source_lane_recommendation.json",
    "environmental_pass_guard.json",
    "roadmap_future_gate_sync_v2_23.json",
    "public_language_audit.json",
    "claim_boundary_v2_23.json",
    "SHA256SUMS.txt",
]

FORBIDDEN_SELECTED_CANDIDATE_OUTPUTS = {
    "selected_candidate_executed_scope_manifest.json",
    "selected_candidate_executed_scope_trace.log",
    "selected_candidate_executed_file_hashes.csv",
    "selected_candidate_static_import_graph.json",
    "selected_candidate_static_import_graph_edges.csv",
    "selected_candidate_static_import_graph_audit.json",
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


def expected_combination_hash() -> str:
    material = "|".join(
        [
            HARNESS_ORIGIN_SHA256,
            TARGET_TEST_SHA256,
            METHOD_ID,
            METHOD_SIGNATURE,
            BUGSINPY_REPO,
            BUGSINPY_COMMIT,
        ]
    )
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


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


def audit_v222_boundary(errors: list[str]) -> None:
    verification = load_json(V222_ROOT / "v2_22_official_artifact_verification.json", errors)
    expect(verification.get("status") == "PASS", errors, "v2.22 official ingest missing or not PASS")
    expect(
        verification.get("zip_sha256") == "32aaad406f10acecb373d3313722c5c7130fd4c4c87ae879e5feb83706cb852a",
        errors,
        "v2.22 artifact digest mismatch",
    )
    expect(verification.get("artifact_target_test_sha256") == TARGET_TEST_SHA256, errors, "v2.22 artifact target-test SHA mismatch")
    audit = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "audit_v2_22_bugsinpy_target_test_materialization_lane.py")],
        cwd=str(REPO_ROOT),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if audit.returncode != 0:
        errors.append("v2.22 audit did not pass from v2.23 audit")


def audit_outputs(root: Path, errors: list[str]) -> None:
    for rel in REQUIRED_FILES:
        expect((root / rel).is_file(), errors, f"missing required output: {rel}")
    for rel in FORBIDDEN_SELECTED_CANDIDATE_OUTPUTS:
        expect(not (root / rel).exists(), errors, f"unexpected selected-candidate or patch output: {rel}")

    manifest_errors, checked = verify_manifest(root)
    errors.extend(manifest_errors)
    expect(checked >= len(REQUIRED_FILES) - 1, errors, "manifest checked fewer files than required")

    results = load_json(root / "campaign_results.json", errors)
    ingest_ref = load_json(root / "v2_22_official_ingest_reference.json", errors)
    pattern = load_json(root / "bugsinpy_acquisition_method_pattern_analysis.json", errors)
    framework = load_json(root / "bugsinpy_framework_checkout_logic_audit.json", errors)
    scan = load_json(root / "bugsinpy_fixed_copy_pattern_scan.json", errors)
    extract = load_json(root / "bugsinpy_checkout_offending_code_extract.json", errors)
    mapping = load_json(root / "bugsinpy_checkout_trace_to_source_mapping.json", errors)
    runtime = load_json(root / "bugsinpy_runtime_trace_authority_record.json", errors)
    risk = load_json(root / "source_acquisition_method_risk_registry.json", errors)
    combo_registry = load_json(root / "compound_provenance_combination_registry.json", errors)
    combo_audit = load_json(root / "compound_provenance_combination_audit.json", errors)
    global_block = load_json(root / "global_bugsinpy_provenance_block.json", errors)
    scope = load_json(root / "candidate_scope_expansion_required.json", errors)
    external = load_json(root / "external_candidate_acquisition_recommendation.json", errors)
    v224 = load_json(root / "v2_24_external_safe_source_lane_recommendation.json", errors)
    environment = load_json(root / "environmental_pass_guard.json", errors)
    roadmap = load_json(root / "roadmap_future_gate_sync_v2_23.json", errors)
    public_language = load_json(root / "public_language_audit.json", errors)
    claim = load_json(root / "claim_boundary_v2_23.json", errors)

    combo_hash = expected_combination_hash()
    expect(results.get("campaign_id") == CAMPAIGN_ID, errors, "campaign ID mismatch")
    expect(results.get("status") == "PASS_WITH_GLOBAL_BUGSINPY_METHOD_PROVENANCE_BLOCK", errors, "campaign status mismatch")
    expect(results.get("v2_22_official_ingest_verified") is True, errors, "v2.22 official ingest not verified")
    expect(ingest_ref.get("status") == "PASS", errors, "v2.22 ingest reference not PASS")
    expect(ingest_ref.get("artifact_target_test_sha256") == TARGET_TEST_SHA256, errors, "ingest reference target-test SHA mismatch")

    expect(pattern.get("decision") == DECISION, errors, "method pattern decision mismatch")
    expect(pattern.get("target_test_sha256") == TARGET_TEST_SHA256, errors, "method pattern target-test SHA mismatch")
    expect(pattern.get("source_text_pattern_detected") is True, errors, "source-text method pattern not detected")
    expect(pattern.get("candidate_specific_exception_proven") is False, errors, "unexpected candidate-specific exception")
    expect(framework.get("status") == "PASS", errors, "framework checkout logic audit did not PASS")
    expect(framework.get("framework_repo") == BUGSINPY_REPO, errors, "framework repo mismatch")
    expect(framework.get("observed_framework_commit") == BUGSINPY_COMMIT, errors, "framework commit mismatch")
    expect(framework.get("source_text_available") is True, errors, "framework source text unavailable")
    expect(framework.get("gold_patch_files_read") is False, errors, "gold patch files were read")
    expect(framework.get("fixed_commit_contents_accessed") is False, errors, "fixed commit contents accessed")
    expect(framework.get("future_commit_contents_accessed") is False, errors, "future commit contents accessed")
    expect(scan.get("fixed_copy_pattern_detected") is True, errors, "fixed-copy pattern not detected")
    expect(scan.get("pattern_global_in_framework_command") is True, errors, "method pattern not recorded as command-level")
    expect(scan.get("candidate_specific_exception_proven") is False, errors, "scan claims candidate-specific exception")
    expect(extract.get("status") == "PASS", errors, "offending code extract did not PASS")
    expect(bool(extract.get("offending_code_excerpt")), errors, "offending code excerpt missing")
    expect((root / "bugsinpy_checkout_offending_code_extract.txt").is_file(), errors, "offending code text extract missing")
    expect(mapping.get("status") == "PASS", errors, "trace-to-source mapping did not PASS")
    expect(len(mapping.get("mappings") or []) >= 3, errors, "trace-to-source mapping incomplete")
    expect(runtime.get("status") == "PASS", errors, "runtime trace authority record did not PASS")
    expect(runtime.get("v2_22_artifact_sha256") == "32aaad406f10acecb373d3313722c5c7130fd4c4c87ae879e5feb83706cb852a", errors, "runtime trace lacks artifact anchoring")
    expect(runtime.get("v2_22_trace_file_sha256") == sha256_path(V222_ROOT / "official_bugsinpy_framework_materialization_trace.json"), errors, "runtime trace file hash mismatch")
    expect(bool(runtime.get("trace_excerpt")), errors, "runtime trace excerpt missing")
    if runtime.get("offending_source_text_location") == "runtime_trace_only":
        expect(runtime.get("safety_decision") == "fail_safe_global_or_inconclusive_block", errors, "runtime-only evidence lacks fail-safe decision")

    risk_records = risk.get("records")
    expect(risk.get("status") == "PASS", errors, "risk registry did not PASS")
    expect(isinstance(risk_records, list) and len(risk_records) == 1, errors, "risk registry record count mismatch")
    if isinstance(risk_records, list) and risk_records:
        record = risk_records[0]
        expect(record.get("method_id") == METHOD_ID, errors, "risk method ID mismatch")
        expect(record.get("method_signature") == METHOD_SIGNATURE, errors, "risk method signature missing or mismatch")
        expect(record.get("taint_status") == DECISION, errors, "risk taint status mismatch")
        expect(record.get("allowed_for_future_candidates") is False, errors, "risk registry incorrectly allows method")
        expect(bool(record.get("offending_code_excerpt")), errors, "global block lacks offending code excerpt")

    combo_records = combo_registry.get("records")
    expect(combo_registry.get("status") == "PASS", errors, "compound registry did not PASS")
    expect(isinstance(combo_records, list) and len(combo_records) == 1, errors, "compound registry record count mismatch")
    if isinstance(combo_records, list) and combo_records:
        record = combo_records[0]
        expect(record.get("combination_hash") == combo_hash, errors, "compound combination hash mismatch")
        expect(record.get("target_test_sha256") == TARGET_TEST_SHA256, errors, "compound target-test SHA mismatch")
        expect(record.get("acquisition_method_id") == METHOD_ID, errors, "compound method ID mismatch")
        expect(record.get("acquisition_method_signature") == METHOD_SIGNATURE, errors, "compound method signature mismatch")
        expect(record.get("decision") == "blocked_fixed_commit_derived_test_materialization", errors, "compound decision mismatch")
        expect(record.get("behavioral_signature") == BEHAVIORAL_SIGNATURE, errors, "behavioral signature mismatch")
        expect(record.get("normalized_behavior_sequence") == NORMALIZED_BEHAVIOR_SEQUENCE, errors, "behavior sequence mismatch")
        expect(record.get("behavior_block_applies_across_repos") is True, errors, "behavior block not cross-repo")
    expect(combo_audit.get("status") == "PASS", errors, "compound audit did not PASS")
    expect(combo_audit.get("combination_hash") == combo_hash, errors, "compound audit hash mismatch")
    expect(combo_audit.get("behavioral_signature") == BEHAVIORAL_SIGNATURE, errors, "compound audit behavioral signature missing")
    expect(combo_audit.get("blocked_behavior_bypassed_by_repo_url_change") is False, errors, "blocked behavior bypassed by repo URL")

    expect(global_block.get("status") == "BLOCK", errors, "global block status mismatch")
    expect(global_block.get("decision") == DECISION, errors, "global block decision mismatch")
    expect(global_block.get("candidate_selection_allowed") is False, errors, "candidate selection allowed after global block")
    for key in ["new_bugsinpy_candidate_selected", "s_engine_invoked", "dependency_recovery_run", "pre_repair_replay_run", "patch_generated", "patch_authorized", "patch_attempted"]:
        expect(global_block.get(key) is False, errors, f"forbidden action occurred after global block: {key}")
    expect(scope.get("candidate_scope_expansion_required") is True, errors, "candidate scope expansion not required")
    expect(scope.get("do_not_reopen_pysnooper1_without_external_reviewed_safe_target_test_provenance") is True, errors, "PySnooper:1 reopen condition missing")
    expect(scope.get("pysnooper2_pursued") is False, errors, "PySnooper:2 was pursued")
    expect(external.get("recommendation") == "external_safe_source_candidate_acquisition_lane", errors, "external safe-source recommendation mismatch")
    expect(v224.get("recommended_next_version") == "v2.24", errors, "v2.24 recommendation target mismatch")
    expect(v224.get("research_level_future_items_are_not_prerequisites") is True, errors, "research-level items became prerequisites")

    expect(environment.get("status") == "PASS", errors, "environmental pass guard did not PASS")
    expect(environment.get("guard_active_before_patch_generation") is True, errors, "environmental guard not active before patch generation")
    expect(environment.get("pre_repair_environmental_pass_detected") is False, errors, "pre-repair environmental pass detected")
    expect(environment.get("count_as_repair_success") is False, errors, "environment-only pass counted as repair success")
    expect(roadmap.get("status") == "PASS", errors, "roadmap sync did not PASS")
    expect(roadmap.get("v2_24_priority") == "External Safe-Source Candidate Acquisition Lane", errors, "v2.24 priority missing")
    expect(roadmap.get("future_safety_enhancements_not_prerequisites_for_v2_24_source_acquisition_pivot") is True, errors, "future enhancements block v2.24")
    expect(public_language.get("status") == "PASS", errors, "public language audit did not PASS")
    expect(public_language.get("exact_match_count") == 0, errors, "public language audit found exact disallowed terms in v2.23-owned text")

    expect(claim.get("status") == "PASS", errors, "claim boundary did not PASS")
    expect(claim.get("full_scoring") == "NOT_RUN", errors, "full scoring changed")
    expect(claim.get("full_scoring_allowed") is False, errors, "full scoring allowed")
    expect(claim.get("current_protocol_version") == "v2.13", errors, "current protocol changed")
    expect(claim.get("v2_23_promoted_to_current") is False, errors, "v2.23 promoted to current")
    expect(claim.get("memory_lift_status") == "undemonstrated", errors, "memory lift claimed")
    expect(claim.get("self_maintaining_software_status") == "false/not_demonstrated", errors, "self-maintaining claim changed")
    expect(claim.get("external_physics_validation_claimed") is False, errors, "external physics validation claimed")
    expect(claim.get("pysnooper1_status") == "terminally_blocked_under_current_safety_rules", errors, "PySnooper:1 boundary mismatch")
    expect(claim.get("pysnooper2_status") == "blocked_not_pursued", errors, "PySnooper:2 boundary mismatch")
    expect(claim.get("non_ansible_positive_memory_count") == 0, errors, "non-Ansible positive-memory count changed")

    expect(results.get("candidate_selection_status") == "not_run_global_method_block", errors, "candidate selection status mismatch")
    expect(results.get("selected_candidate") is None, errors, "candidate selected after global block")
    expect(results.get("s_engine_invoked") is False, errors, "S-Engine invoked after global block")
    expect(results.get("dependency_recovery_run") is False, errors, "dependency recovery ran after global block")
    expect(results.get("pre_repair_replay_run") is False, errors, "pre-repair replay ran after global block")
    expect(results.get("patch_generated") is False, errors, "patch generated after global block")
    expect(results.get("full_scoring") == "NOT_RUN", errors, "results full scoring changed")
    expect(results.get("full_scoring_allowed") is False, errors, "results full scoring allowed")
    expect(results.get("memory_lift_status") == "undemonstrated", errors, "results memory lift claimed")
    expect(results.get("self_maintaining_software_status") == "false/not_demonstrated", errors, "results self-maintaining claim changed")
    expect(results.get("current_protocol_version") == "v2.13", errors, "results current protocol changed")
    expect(results.get("exact_blocker") == BLOCKER, errors, "exact blocker mismatch")

    audit_v222_boundary(errors)

    print(f"v2.23 manifest entries checked: {checked}")
    for key in [
        "bugsinpy_method_provenance_pattern_decision",
        "offending_code_extract_status",
        "trace_to_source_mapping_status",
        "source_acquisition_method_risk_registry_status",
        "compound_provenance_combination_registry_status",
        "global_bugsinpy_block_status",
        "candidate_selection_status",
        "environmental_pass_guard_status",
        "v2_24_external_safe_source_recommendation_status",
        "full_scoring",
        "memory_lift_status",
        "self_maintaining_software_status",
        "current_protocol_version",
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
        print("v2.23 audit FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("v2.23 audit PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
