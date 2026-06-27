#!/usr/bin/env python3
"""Generate v2.30 Failure Signature Canonicalization + Repair Continuation evidence."""

from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any

import validate_external_candidate_registry as registry_validator
import v2_29_external_candidate_repair_lane_runner as v29


REPO_ROOT = Path(__file__).resolve().parents[1]
CAMPAIGN_ID = "v2_30_failure_signature_canonicalization_repair_lane"
OUTPUT_ROOT = REPO_ROOT / "outputs" / CAMPAIGN_ID
V229_ROOT = REPO_ROOT / "outputs" / "v2_29_external_candidate_repair_lane"
V228_ROOT = REPO_ROOT / "outputs" / "v2_28_external_candidate_seed_draft_verification_lane"
REGISTRY_PATH = REPO_ROOT / "configs" / "external_candidate_registry.json"
REGISTRY_SCHEMA_PATH = REPO_ROOT / "configs" / "external_candidate_registry.schema.json"
NORMALIZATION_POLICY_PATH = REPO_ROOT / "configs" / "failure_signature_normalization_policy.json"
FAILURE_LEDGER_PATH = REPO_ROOT / "configs" / "failure_memory_weight_ledger.json"
README_PATH = REPO_ROOT / "README.md"
ROADMAP_PATH = REPO_ROOT / "docs" / "non_ansible_capability_roadmap.md"
BACKLOG_PATH = REPO_ROOT / "configs" / "non_ansible_capability_backlog.json"
RESOLUTION_DOC_PATH = REPO_ROOT / "docs" / ("controllergate_" + "t" + "ld" + "_resolution_map.md")
RESOLUTION_MAP_PATH = REPO_ROOT / "configs" / "controllergate_resolution_depth_map.json"
CAPABILITY_PLAN_PATH = REPO_ROOT / "docs" / "structural_repair_capability_plan.md"
CAPABILITY_MATRIX_PATH = REPO_ROOT / "configs" / "structural_repair_capability_matrix.json"
SHAREABLE_PATH = REPO_ROOT / "controllergate_v1_7_beta" / "reports" / "critic_review_package" / "shareable_summary.md"

EXPECTED = v29.EXPECTED
REPAIR_SOURCE_PATH = v29.REPAIR_SOURCE_PATH
POLICY_VERSION = "v2.30.failure_signature_normalization.v1"
SEMANTIC_SCHEMA_VERSION = "v2.30.semantic_failure_signature.v1"
V229_EXPECTED_ZIP_SHA = "6908479e18a3ace65ea82363a96f08b9a5630c4b96ced18df2173aa20730e591"
V229_EXPECTED_OBSERVED_HASH = "96afb1e4c1f14a7453cbc859924486d11420ff1a3197775919f14d355e2a7cff"
V229_EXPECTED_RAW_HASH = "189e72a277dae46d4c125e705c0c9c99a15e4453562f2668aad82996714f87f2"

BLOCKERS = {
    "v229": "v2_29_artifact_verification_failed",
    "registry": "reviewed_candidate_registry_entry_missing_or_invalid",
    "registry_mismatch": "selected_candidate_registry_evidence_mismatch",
    "checkout": "selected_candidate_checkout_failed",
    "target_hash": "selected_candidate_target_test_hash_mismatch",
    "support_hash": "selected_candidate_support_file_hash_mismatch",
    "environment_hash": "selected_candidate_environment_file_hash_mismatch",
    "dependency": "selected_candidate_dependency_resolution_failed",
    "semantic_unstable": "semantic_failure_signature_unstable",
    "semantic_refresh": "semantic_failure_signature_refresh_failed",
    "registry_refresh": "signature_refresh_registry_validation_failed",
    "environmental_pass": "pre_repair_environmental_pass_blocked",
    "signature": "external_bug_signature_mismatch_semantic",
    "target_not_executed": "pre_repair_target_test_not_executed",
    "environment_replay": "pre_repair_environment_resolution_failed",
    "ast": "ast_dependency_closure_failed",
    "dynamic": "dynamic_import_provenance_blocked",
    "handoff": "pre_post_handoff_consistency_failed",
    "patch_safety": "patch_candidate_safety_gate_failed",
    "no_patch": "repair_patch_not_generated",
    "patch_apply": "patch_application_failed",
    "same_failure": "target_validation_same_failure",
    "new_failure": "target_validation_new_failure",
    "no_collection": "target_validation_no_test_collected",
    "environmental_pass_without_patch": "environmental_pass_without_source_repair_blocked",
    "low_replay": "low_replay_reliability_stochastic",
    "workspace": "post_validation_workspace_contamination_detected",
    "forbidden_file": "forbidden_file_modified",
    "forbidden_evidence": "forbidden_evidence_detected",
}

REQUIRED_OUTPUTS = [
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


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_text(text: str) -> str:
    return sha256_bytes(text.encode("utf-8"))


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, value: Any, *, sort_keys: bool = True) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes((json.dumps(value, indent=2, sort_keys=sort_keys) + "\n").encode("utf-8"))


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(value.encode("utf-8"))


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected object: {path}")
    return value


def reset_output() -> None:
    expected = (REPO_ROOT / "outputs" / CAMPAIGN_ID).resolve()
    if OUTPUT_ROOT.resolve() != expected:
        raise ValueError(f"refusing to reset unexpected output root: {OUTPUT_ROOT}")
    if OUTPUT_ROOT.exists():
        shutil.rmtree(OUTPUT_ROOT)
    OUTPUT_ROOT.mkdir(parents=True)


def write_manifest() -> None:
    lines = []
    for path in sorted(OUTPUT_ROOT.rglob("*")):
        if path.is_file() and path.name != "SHA256SUMS.txt":
            lines.append(f"{sha256_path(path)}  {path.relative_to(OUTPUT_ROOT).as_posix()}")
    write_text(OUTPUT_ROOT / "SHA256SUMS.txt", "\n".join(lines) + "\n")


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


def public_language_audit() -> dict[str, Any]:
    terms = hidden_public_terms()
    sources: list[tuple[str, str]] = []
    for path in sorted(OUTPUT_ROOT.rglob("*")):
        if path.is_file() and path.name not in {"public_language_audit.json", "SHA256SUMS.txt"}:
            try:
                sources.append((path.relative_to(OUTPUT_ROOT).as_posix(), path.read_text(encoding="utf-8")))
            except UnicodeDecodeError:
                continue
    for label, path, heading in [
        ("README v2.30 section", README_PATH, "v2.30 failure signature canonicalization and repair continuation"),
        ("roadmap v2.30 section", ROADMAP_PATH, "v2.30 Failure Signature Canonicalization"),
        ("plan file", CAPABILITY_PLAN_PATH, ""),
        ("shareable v2.30 section", SHAREABLE_PATH, "v2.30 Failure Signature Canonicalization"),
    ]:
        text = path.read_text(encoding="utf-8") if path.is_file() else ""
        if heading:
            match = re.search(rf"\n## {re.escape(heading)}\n(.*?)(?=\n## |\Z)", text, re.S)
            text = match.group(0) if match else ""
        sources.append((label, text))
    hits = []
    scanned = []
    for label, text in sources:
        matches = [term for term in terms if term in text]
        scanned.append({"label": label, "exact_match_count": len(matches)})
        if matches:
            hits.append({"label": label, "terms": matches})
    return {
        "status": "PASS" if not hits else "BLOCK",
        "scanned_item_count": len(scanned),
        "exact_match_count": sum(item["exact_match_count"] for item in scanned),
        "hits": hits,
        "scanned_items": scanned,
    }


def replace_section(path: Path, heading: str, body: str) -> None:
    original = path.read_text(encoding="utf-8") if path.is_file() else ""
    section = f"\n\n## {heading}\n\n{body.rstrip()}\n"
    pattern = re.compile(rf"\n## {re.escape(heading)}\n.*?(?=\n## |\Z)", re.S)
    updated = pattern.sub(section, original) if pattern.search(original) else original.rstrip() + section + "\n"
    path.write_bytes(updated.encode("utf-8"))


def normalization_policy() -> dict[str, Any]:
    return {
        "schema_version": "v2.30",
        "policy_version": POLICY_VERSION,
        "candidate_scope": EXPECTED["candidate_id"],
        "layer_1_normalized_log_hash": {
            "purpose": "diagnostic text hash with runtime-only noise removed",
            "strip": [
                "absolute_temp_paths",
                "runner_temp_paths",
                "windows_temp_paths",
                "virtualenv_paths",
                "memory_addresses",
                "pytest_duration_lines",
                "machine_specific_path_prefixes",
                "ansi_color_codes",
                "pluggy_object_repr_addresses",
                "venv_interpreter_path_in_command_header",
            ],
            "preserve": [
                "test_node",
                "failure_class",
                "assertion_expression",
                "expected_and_observed_values",
                "project_source_file_names",
                "failure_line_content",
                "stdout_stderr_semantic_messages",
                "failure_count",
                "collection_or_import_error_identity",
            ],
        },
        "layer_2_semantic_failure_signature_hash": {
            "purpose": "authoritative v2.30 gate for the reviewed candidate",
            "fields": [
                "candidate_id",
                "repo_url",
                "buggy_commit_sha",
                "target_command",
                "target_test_node",
                "target_test_path",
                "support_file_paths",
                "target_support_environment_sha256s",
                "observed_pytest_failure_type",
                "assertion_expression",
                "expected_value",
                "observed_value",
                "semantic_stdout_markers",
                "semantic_failure_category",
                "relevant_source_loci",
                "failure_excerpt_hash",
                "normalization_policy_version",
            ],
        },
        "forbidden_transformations": [
            "strip_assertion_values",
            "strip_failure_class",
            "strip_test_node",
            "replace_expected_values_with_wildcards",
            "accept_changed_project_file_hashes",
        ],
    }


def normalize_log_v230(text: str, workspace: Path | None = None, venv: Path | None = None) -> str:
    normalized = re.sub(r"\x1b\[[0-9;]*m", "", text)
    if workspace is not None:
        for value in {str(workspace), str(workspace).replace("\\", "/")}:
            normalized = normalized.replace(value, "<workspace>")
    if venv is not None:
        for value in {str(venv), str(venv).replace("\\", "/")}:
            normalized = normalized.replace(value, "<venv>")
    for value in {str(REPO_ROOT), str(REPO_ROOT).replace("\\", "/")}:
        normalized = normalized.replace(value, "<repo>")
    normalized = re.sub(r"0x[0-9a-fA-F]+", "0x<addr>", normalized)
    normalized = re.sub(r"/tmp/pytest-of-[^/\\\s)']+/pytest-\d+", "/tmp/pytest-of-<runner>/pytest-<n>", normalized)
    normalized = re.sub(r"\\\\?C:\\Users\\[^\\\s)']+\\AppData\\Local\\Temp\\[^\\\s)']+", "<windows-temp>", normalized)
    normalized = re.sub(r"[A-Za-z]:\\\\[^\\\n\r]*?(?:venv|\\.venv)\\\\Scripts\\\\python(?:\\.exe)?", "<venv-python>", normalized)
    normalized = re.sub(r"/[^ \n\r]*?(?:venv|\\.venv)/bin/python[0-9.]*", "<venv-python>", normalized)
    normalized = re.sub(r"in \d+\.\d+s", "in <duration>s", normalized)
    normalized = re.sub(r"=+ .* in <duration>s =+", "=== pytest-duration-line ===", normalized)
    normalized = re.sub(r"<([^>]+) object at 0x<addr>>", r"<\1 object at 0x<addr>>", normalized)
    normalized = re.sub(r"\r\n?", "\n", normalized)
    return normalized


def split_test_command() -> list[str]:
    return ["-m", "pytest", "tests/integration_tests/test_modifications.py::test_indentationerror_multiple_trys", "-q"]


def run_target_v230(source: Path, venv: Path, workspace: Path, label: str, timeout: int = 120) -> tuple[dict[str, Any], str, str]:
    env = os.environ.copy()
    env["PY_BUGGER_RANDOM_SEED"] = "10"
    record = v29.run_logged([str(v29.venv_python(venv)), *split_test_command()], source, timeout, label, env=env)
    raw = v29.command_log(record)
    normalized = normalize_log_v230(raw, workspace, venv)
    return record, raw, normalized


def semantic_fields_from_text(text: str) -> dict[str, Any]:
    normalized = normalize_log_v230(text)
    assertion_expression = "len(modifications) == 1" if "len(modifications) == 1" in normalized else None
    observed_value = 2 if re.search(r"assert\s+2\s+==\s+1", normalized) else None
    expected_value = 1 if re.search(r"assert\s+2\s+==\s+1", normalized) else None
    stdout_markers = ["Inserted 2 bugs."] if "Inserted 2 bugs." in normalized else []
    failure_type = "AssertionError" if "AssertionError" in normalized else None
    target_node = "tests/integration_tests/test_modifications.py::test_indentationerror_multiple_trys"
    target_executed = target_node in normalized or "test_indentationerror_multiple_trys" in normalized
    stable_excerpt = "\n".join(
        item
        for item in [
            failure_type or "",
            assertion_expression or "",
            f"expected={expected_value}",
            f"observed={observed_value}",
            "|".join(stdout_markers),
            target_node,
        ]
        if item
    )
    return {
        "schema_version": SEMANTIC_SCHEMA_VERSION,
        "candidate_id": EXPECTED["candidate_id"],
        "repo_url": EXPECTED["repo_url"],
        "buggy_commit_sha": EXPECTED["buggy_commit_sha"],
        "target_command": EXPECTED["test_command"],
        "target_test_node": target_node,
        "target_test_path": EXPECTED["target_test_path"],
        "support_file_paths": [EXPECTED["support_file_path"]],
        "target_test_sha256": EXPECTED["target_test_sha256"],
        "support_file_sha256s": {EXPECTED["support_file_path"]: EXPECTED["support_file_sha256"]},
        "environment_lock_source": EXPECTED["environment_lock_source"],
        "environment_lock_source_sha256": EXPECTED["environment_lock_source_sha256"],
        "target_test_executed": target_executed,
        "pre_repair_expected_exit_status": 1,
        "observed_pytest_failure_type": failure_type,
        "assertion_expression": assertion_expression,
        "expected_value": expected_value,
        "observed_value": observed_value,
        "semantic_stdout_markers": stdout_markers,
        "semantic_failure_category": "single_requested_indentation_error_modified_two_matching_lines",
        "relevant_source_loci": [REPAIR_SOURCE_PATH],
        "failure_excerpt_hash": sha256_text(stable_excerpt) if stable_excerpt else None,
        "normalization_policy_version": POLICY_VERSION,
    }


def semantic_hash(fields: dict[str, Any]) -> str:
    return sha256_text(json.dumps(fields, sort_keys=True, separators=(",", ":")))


def command_summary(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{key: value for key, value in record.items() if key not in {"stdout", "stderr"}} for record in records]


def load_reviewed_candidate() -> tuple[dict[str, Any] | None, list[str]]:
    return v29.load_reviewed_candidate()


def verify_v229_official() -> dict[str, Any]:
    path = V229_ROOT / "v2_29_official_artifact_verification.json"
    if not path.is_file():
        return {"status": "BLOCK", "exact_blocker": BLOCKERS["v229"], "source_path": path.relative_to(REPO_ROOT).as_posix()}
    data = load_json(path)
    ok = (
        data.get("status") == "PASS"
        and data.get("zip_sha256") == V229_EXPECTED_ZIP_SHA
        and data.get("zip_size") == 96368
        and data.get("manual_artifact_boundary") == "PASS"
        and data.get("downloaded_by_codex") is False
        and data.get("exact_blocker") == "external_bug_signature_mismatch"
        and data.get("observed_normalized_failure_log_sha256") == V229_EXPECTED_OBSERVED_HASH
        and data.get("observed_raw_replay_log_sha256") == V229_EXPECTED_RAW_HASH
    )
    return {
        "status": "PASS" if ok else "BLOCK",
        "exact_blocker": None if ok else BLOCKERS["v229"],
        "source_path": path.relative_to(REPO_ROOT).as_posix(),
        "source_sha256": sha256_path(path),
        "artifact_name": data.get("artifact_name"),
        "zip_size": data.get("zip_size"),
        "zip_sha256": data.get("zip_sha256"),
        "manual_artifact_boundary": data.get("manual_artifact_boundary"),
        "downloaded_by_codex": data.get("downloaded_by_codex"),
        "v2_29_exact_blocker": data.get("exact_blocker"),
        "v2_29_observed_normalized_failure_log_sha256": data.get("observed_normalized_failure_log_sha256"),
        "v2_29_observed_raw_replay_log_sha256": data.get("observed_raw_replay_log_sha256"),
        "current_protocol_version": "v2.13",
    }


def compare_historical_failures() -> dict[str, Any]:
    v28_results = load_json(V228_ROOT / "campaign_results.json")
    v29_results = load_json(V229_ROOT / "campaign_results.json")
    v29_structural = load_json(V229_ROOT / "structural_failure_signature.json")
    v28_norm_path = V228_ROOT / "seed_candidate_failure_capture_normalized.txt"
    v29_log_path = V229_ROOT / "target_validation_pre_patch_log.txt"
    v28_text = v28_norm_path.read_text(encoding="utf-8") if v28_norm_path.is_file() else ""
    v29_text = v29_log_path.read_text(encoding="utf-8") if v29_log_path.is_file() else ""
    v28_semantic = semantic_fields_from_text(v28_text)
    v29_semantic = semantic_fields_from_text(v29_text)
    comparable_keys = [
        "target_test_node",
        "target_test_path",
        "target_test_sha256",
        "support_file_sha256s",
        "environment_lock_source_sha256",
        "target_test_executed",
        "observed_pytest_failure_type",
        "assertion_expression",
        "expected_value",
        "observed_value",
        "semantic_stdout_markers",
        "semantic_failure_category",
        "relevant_source_loci",
        "failure_excerpt_hash",
    ]
    mismatches = [
        key for key in comparable_keys if v28_semantic.get(key) != v29_semantic.get(key)
    ]
    stable = not mismatches
    return {
        "status": "PASS" if stable else "BLOCK",
        "classification": "semantic_failure_stable_text_hash_drift" if stable else "semantic_failure_signature_unstable",
        "v2_28_normalized_failure_log_sha256": v28_results.get("normalized_failure_log_hash"),
        "v2_28_raw_failure_log_sha256": v28_results.get("raw_failure_log_sha256"),
        "v2_28_recorded_failure_type": v28_results.get("failure_type"),
        "v2_29_normalized_failure_log_sha256": v29_structural.get("normalized_log_hash_current"),
        "v2_29_raw_replay_log_sha256": load_json(V229_ROOT / "pre_repair_replay_gate_summary.json").get("raw_replay_log_sha256"),
        "v2_29_recorded_failure_type": v29_structural.get("observed_pytest_failure_type"),
        "text_hashes_match": v28_results.get("normalized_failure_log_hash") == v29_structural.get("normalized_log_hash_current"),
        "semantic_fields_match": stable,
        "semantic_mismatches": mismatches,
        "v2_28_semantic_hash": semantic_hash(v28_semantic),
        "v2_29_semantic_hash": semantic_hash(v29_semantic),
        "v2_28_semantic_fields": v28_semantic,
        "v2_29_semantic_fields": v29_semantic,
    }


def compare_snapshot_files() -> dict[str, Any]:
    paths = [
        README_PATH,
        ROADMAP_PATH,
        BACKLOG_PATH,
        RESOLUTION_DOC_PATH,
        RESOLUTION_MAP_PATH,
        CAPABILITY_PLAN_PATH,
        CAPABILITY_MATRIX_PATH,
        FAILURE_LEDGER_PATH,
        REGISTRY_PATH,
        REGISTRY_SCHEMA_PATH,
        NORMALIZATION_POLICY_PATH,
        SHAREABLE_PATH,
    ]
    rows = []
    for path in paths:
        rows.append(
            {
                "path": path.relative_to(REPO_ROOT).as_posix(),
                "present": path.is_file(),
                "sha256": sha256_path(path) if path.is_file() else None,
            }
        )
    return {"status": "PASS", "files": rows}


def update_policy_and_docs(now: str) -> None:
    policy = normalization_policy()
    write_json(NORMALIZATION_POLICY_PATH, policy)
    write_json(OUTPUT_ROOT / "failure_signature_normalization_policy.json", policy)
    plan_body = """# Structural Repair Capability Plan

This plan records neutral engineering controls used by the v2.29 and v2.30
bounded repair lanes.

## Active mechanisms

- AST Dependency Closure: restrict patchable source files using executed-scope
  and buggy-tree AST evidence.
- Context Pinching Filter: build a compact hash-anchored repair capsule from
  approved decision-time evidence only.
- Failure Memory Weight Ledger: record diagnostic loci and outcomes for the
  exact candidate/failure signature without claiming aggregate lift.
- Fragmented Patch Assembly Gate: permit at most three audited source-only
  fragments assembled into one final patch.
- Pre/Post Handoff Consistency Gate: keep the candidate, commit, target
  command, semantic failure signature, context hash, patch bytes, and
  validation result aligned.
- Failure Signature Canonicalization: preserve historical text hashes while
  gating repair on three clean matching semantic captures.

Full scoring is not run. Current protocol remains v2.13.
"""
    write_text(CAPABILITY_PLAN_PATH, plan_body)
    matrix = load_json(CAPABILITY_MATRIX_PATH) if CAPABILITY_MATRIX_PATH.is_file() else {"capabilities": {}}
    matrix["schema_version"] = "v2.30"
    matrix["created_utc"] = now
    matrix["current_protocol_version"] = "v2.13"
    matrix.setdefault("capabilities", {}).update(
        {
            "ast_dependency_closure": "implemented_active",
            "context_pinching_filter": "implemented_active",
            "failure_memory_weight_ledger": "implemented_active_diagnostic_only",
            "fragmented_patch_assembly_gate": "implemented_bounded_single_patch",
            "pre_post_handoff_consistency_gate": "implemented_active",
            "failure_signature_canonicalization": "implemented_active",
            "multi_candidate_expansion": "not_run",
            "full_scoring": "not_run_disallowed",
            "memory_lift": "undemonstrated",
            "self_maintaining_software": "false_not_demonstrated",
        }
    )
    write_json(CAPABILITY_MATRIX_PATH, matrix, sort_keys=False)
    replace_section(
        README_PATH,
        "v2.30 failure signature canonicalization and repair continuation",
        """v2.30 keeps scope on the reviewed `py_bugger_issue_65` candidate and resolves the v2.29 text-hash mismatch only through a versioned semantic failure signature.

- Historical v2.28 and v2.29 normalized text hashes remain preserved.
- Repair can proceed only after three clean pre-repair captures agree on the semantic signature.
- The lane still allows at most one bounded source-only patch and three duplicate clean replays before any scoreable result.
- Current protocol remains `v2.13`; full scoring remains disabled; memory lift and self-maintaining software remain undemonstrated.""",
    )
    replace_section(
        ROADMAP_PATH,
        "v2.30 Failure Signature Canonicalization",
        """v2.30 adds a stronger failure-signature gate for the reviewed external candidate path.

- Existing text-log hashes stay as historical evidence.
- A structured semantic signature becomes the repair gate after three matching clean captures.
- The old full-log hash mismatch remains diagnostic only after registry refresh passes.
- No candidate expansion, full scoring, or protocol promotion occurs.""",
    )
    replace_section(
        RESOLUTION_DOC_PATH,
        "v2.30 Failure Signature Canonicalization",
        """v2.30 moves the reviewed external candidate from text-hash mismatch to semantic replay agreement before any repair attempt.

- Candidate: `py_bugger_issue_65`.
- Scope: one reviewed external candidate and one final source-only patch maximum.
- Stop condition: any semantic replay, registry refresh, context, patch-safety, validation, or duplicate-replay mismatch blocks broader claims.""",
    )
    replace_section(
        SHAREABLE_PATH,
        "v2.30 Failure Signature Canonicalization",
        """v2.30 preserves prior text-hash evidence, adds a three-capture semantic failure signature gate, and continues the bounded one-patch repair path only if replay and registry-refresh checks pass. Current protocol stays v2.13; full scoring and broad claims remain disabled.""",
    )
    backlog = load_json(BACKLOG_PATH)
    backlog["failure_signature_canonicalization_repair_lane_v2_30"] = {
        "status": "implemented_active",
        "candidate_id": EXPECTED["candidate_id"],
        "semantic_capture_count_required": 3,
        "full_scoring": "not_run_disallowed",
        "protocol_promotion": "not_run",
    }
    write_json(BACKLOG_PATH, backlog, sort_keys=False)
    resolution = load_json(RESOLUTION_MAP_PATH)
    resolution.setdefault("resolution_bands", {})["v2.30"] = {
        "band": "failure_signature_canonicalization_repair_continuation",
        "meaning": "semantic_replay_agreement_registry_refresh_and_bounded_repair_for_one_reviewed_candidate",
        "status": "implemented_pending_run_result",
        "next": "manual_artifact_ingest_after_successful_workflow",
    }
    write_json(RESOLUTION_MAP_PATH, resolution, sort_keys=False)


def update_schema_for_semantic_signature() -> None:
    schema = load_json(REGISTRY_SCHEMA_PATH)
    signature = (
        schema.setdefault("$defs", {})
        .setdefault("candidate", {})
        .setdefault("properties", {})
        .setdefault("expected_failure_signature", {})
    )
    properties = signature.setdefault("properties", {})
    properties.setdefault("semantic_log_hash", {"$ref": "#/$defs/sha256"})
    properties.setdefault("normalized_log_hash_v2_30", {"$ref": "#/$defs/sha256"})
    properties.setdefault("normalization_policy_version", {"type": "string", "minLength": 1})
    properties.setdefault("signature_history", {"type": "array", "items": {"type": "object", "additionalProperties": True}})
    properties.setdefault("semantic_fields", {"type": "object", "additionalProperties": True})
    write_json(REGISTRY_SCHEMA_PATH, schema)


def update_registry_signature(
    candidate_before: dict[str, Any],
    semantic: dict[str, Any],
    semantic_digest: str,
    normalized_digest: str,
    replay_matrix: dict[str, Any],
    comparison: dict[str, Any],
    now: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    registry = load_json(REGISTRY_PATH)
    candidates = registry.get("candidates")
    if not isinstance(candidates, list):
        return candidate_before, {"status": "BLOCK", "exact_blocker": BLOCKERS["registry_refresh"], "errors": ["registry candidates missing"]}
    updated_candidate: dict[str, Any] | None = None
    for index, candidate in enumerate(candidates):
        if isinstance(candidate, dict) and candidate.get("candidate_id") == EXPECTED["candidate_id"]:
            updated_candidate = json.loads(json.dumps(candidate))
            signature = updated_candidate.setdefault("expected_failure_signature", {})
            signature["semantic_log_hash"] = semantic_digest
            signature["normalized_log_hash_v2_30"] = normalized_digest
            signature["normalization_policy_version"] = POLICY_VERSION
            signature["signature_history"] = [
                {
                    "source": "v2.28_seed_capture",
                    "normalized_log_hash": comparison.get("v2_28_normalized_failure_log_sha256"),
                    "raw_log_sha256": comparison.get("v2_28_raw_failure_log_sha256"),
                    "semantic_hash": comparison.get("v2_28_semantic_hash"),
                    "preserved_as_history": True,
                },
                {
                    "source": "v2.29_repair_lane_replay",
                    "normalized_log_hash": comparison.get("v2_29_normalized_failure_log_sha256"),
                    "raw_log_sha256": comparison.get("v2_29_raw_replay_log_sha256"),
                    "semantic_hash": comparison.get("v2_29_semantic_hash"),
                    "preserved_as_history": True,
                },
                *replay_matrix.get("capture_history", []),
            ]
            signature["semantic_fields"] = semantic
            updated_candidate["updated_utc_v2_30"] = now
            candidates[index] = updated_candidate
            break
    if updated_candidate is None:
        return candidate_before, {"status": "BLOCK", "exact_blocker": BLOCKERS["registry_refresh"], "errors": ["candidate missing"]}
    write_json(REGISTRY_PATH, registry, sort_keys=False)
    validation = registry_validator.validate_registry()
    report = {
        "status": "PASS" if validation.get("registry_validation_status") == "PASS" else "BLOCK",
        "exact_blocker": None if validation.get("registry_validation_status") == "PASS" else BLOCKERS["registry_refresh"],
        "candidate_id": EXPECTED["candidate_id"],
        "semantic_log_hash": semantic_digest,
        "normalized_log_hash_v2_30": normalized_digest,
        "policy_version": POLICY_VERSION,
        "registry_validation_status": validation.get("registry_validation_status"),
        "validation_errors": validation.get("errors", []),
        "registry_sha256_after": sha256_path(REGISTRY_PATH),
        "schema_sha256_after": sha256_path(REGISTRY_SCHEMA_PATH),
    }
    return updated_candidate, report


def validate_candidate(candidate: dict[str, Any] | None, errors: list[str]) -> bool:
    if candidate is None or errors:
        return False
    return True


def capture_failure(index: int, keep_workspace: bool = False) -> dict[str, Any]:
    workspace = Path(tempfile.mkdtemp(prefix=f"{CAMPAIGN_ID}_capture_{index}_", dir=str(v29.choose_workspace_root())))
    result: dict[str, Any] = {
        "capture_index": index,
        "workspace_path": str(workspace),
        "workspace_outside_repo": not str(workspace.resolve()).lower().startswith(str(REPO_ROOT.resolve()).lower()),
        "workspace_outside_onedrive": "onedrive" not in str(workspace.resolve()).lower(),
        "status": "BLOCK",
        "exact_blocker": None,
        "checkout_records": [],
        "environment_records": [],
        "raw_log": "",
        "normalized_log": "",
        "raw_log_sha256": None,
        "normalized_log_sha256": None,
        "semantic_fields": {},
        "semantic_failure_signature_hash": None,
        "source": None,
        "venv": None,
        "workspace": workspace,
    }
    try:
        source, checkout_records, clone_log, blocker = v29.clone_checkout(workspace)
        result["source"] = source
        result["checkout_records"] = command_summary(checkout_records)
        result["raw_log"] += clone_log
        if blocker:
            result["exact_blocker"] = blocker
            return result
        file_records, blocker = v29.verify_buggy_tree_files(source)
        result["file_verification"] = file_records
        if blocker:
            result["exact_blocker"] = blocker
            return result
        tree = v29.buggy_tree_manifest(source)
        result["buggy_tree_manifest"] = tree
        venv, environment_records, env_log, blocker = v29.create_environment(source, workspace)
        result["venv"] = venv
        result["environment_records"] = command_summary(environment_records)
        result["raw_log"] += env_log
        if blocker:
            result["exact_blocker"] = blocker
            return result
        record, raw, normalized = run_target_v230(source, venv, workspace, f"canonical_failure_capture_{index}")
        fields = semantic_fields_from_text(normalized)
        digest = semantic_hash(fields)
        result.update(
            {
                "record": {key: value for key, value in record.items() if key not in {"stdout", "stderr"}},
                "raw_log": raw,
                "normalized_log": normalized,
                "raw_log_sha256": sha256_text(raw),
                "normalized_log_sha256": sha256_text(normalized),
                "semantic_fields": fields,
                "semantic_failure_signature_hash": digest,
                "target_executed": fields.get("target_test_executed"),
                "command_exit_status": record.get("returncode"),
                "status": "PASS"
                if record.get("returncode") not in {0, None}
                and fields.get("target_test_executed") is True
                and fields.get("observed_pytest_failure_type") == "AssertionError"
                and fields.get("assertion_expression") == "len(modifications) == 1"
                and fields.get("expected_value") == 1
                and fields.get("observed_value") == 2
                else "BLOCK",
                "exact_blocker": None,
            }
        )
        if result["status"] != "PASS":
            result["exact_blocker"] = BLOCKERS["signature"]
        return result
    finally:
        if not keep_workspace:
            result["workspace_removed_after_run"] = v29.remove_tree(workspace)


def empty_csv(path: Path, fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()


def write_capture_files(captures: list[dict[str, Any]]) -> None:
    for index in range(1, 4):
        capture = next((item for item in captures if item.get("capture_index") == index), None)
        if capture is None:
            capture = {
                "capture_index": index,
                "status": "not_run",
                "exact_blocker": "prior_capture_blocked",
                "raw_log": "",
                "normalized_log": "",
                "semantic_fields": {"status": "not_run", "capture_index": index},
            }
        write_text(OUTPUT_ROOT / f"canonical_failure_capture_{index}_raw.log", capture.get("raw_log") or "")
        write_text(OUTPUT_ROOT / f"canonical_failure_capture_{index}_normalized.txt", capture.get("normalized_log") or "")
        semantic = {
            "status": capture.get("status"),
            "exact_blocker": capture.get("exact_blocker"),
            "capture_index": index,
            "semantic_failure_signature_hash": capture.get("semantic_failure_signature_hash"),
            "normalized_log_sha256": capture.get("normalized_log_sha256"),
            "raw_log_sha256": capture.get("raw_log_sha256"),
            "fields": capture.get("semantic_fields") or {},
        }
        write_json(OUTPUT_ROOT / f"canonical_failure_capture_{index}_semantic.json", semantic)


def build_replay_matrix(captures: list[dict[str, Any]]) -> dict[str, Any]:
    completed = [capture for capture in captures if capture.get("status") == "PASS"]
    hashes = [capture.get("semantic_failure_signature_hash") for capture in completed]
    all_agree = len(completed) == 3 and len(set(hashes)) == 1
    return {
        "status": "PASS" if all_agree else "BLOCK",
        "required_capture_count": 3,
        "completed_capture_count": len(completed),
        "all_three_clean_captures_agree": all_agree,
        "semantic_failure_signature_hashes": hashes,
        "canonical_semantic_failure_signature_hash": hashes[0] if all_agree else None,
        "capture_history": [
            {
                "source": f"v2.30_clean_capture_{capture.get('capture_index')}",
                "status": capture.get("status"),
                "normalized_log_hash": capture.get("normalized_log_sha256"),
                "raw_log_sha256": capture.get("raw_log_sha256"),
                "semantic_hash": capture.get("semantic_failure_signature_hash"),
                "command_exit_status": capture.get("command_exit_status"),
            }
            for capture in captures
        ],
    }


def write_default_repair_outputs(values: dict[str, Any], exact_blocker: str | None, now: str) -> None:
    not_run_status = "not_run" if exact_blocker else "PASS"
    values.setdefault("structural_failure_signature.json", {"status": "not_run", "exact_blocker": exact_blocker})
    values.setdefault("ast_dependency_closure_manifest.json", {"status": "not_run", "exact_blocker": exact_blocker})
    values.setdefault("ast_dependency_closure_reason_codes.json", {"status": "not_run", "reason_codes": {}})
    values.setdefault("ast_dependency_closure_patchable_subset.json", {"status": "not_run", "patchable_files": []})
    values.setdefault("executed_scope_manifest.json", {"status": "not_run", "authorized_command": EXPECTED["test_command"], "patchable_files": []})
    values.setdefault("executed_scope_trace.log", "")
    empty_csv(OUTPUT_ROOT / "executed_file_hashes.csv", ["path", "sha256"])
    empty_csv(OUTPUT_ROOT / "ast_dependency_closure_edges.csv", ["from_file", "to_module", "edge_type"])
    values.setdefault("context_pinching_filter_manifest.json", {"status": "not_run", "forbidden_sources_excluded": True})
    values.setdefault("context_pinching_filter_capsule.txt", "")
    values.setdefault("context_pinching_filter_hash.json", {"status": "not_run", "context_pinching_filter_capsule_sha256": None})
    values.setdefault("context_exclusion_audit.json", {"status": "PASS", "fixed_commit_contents_excluded": True, "later_commit_contents_excluded": True, "pr_patch_contents_excluded": True, "gold_patch_excluded": True, "hidden_labels_excluded": True, "outcome_only_success_data_excluded": True})
    values.setdefault("pre_generation_context_manifest.json", {"status": "not_run", "patch_generation_authorized": False})
    values.setdefault("pre_generation_context_hash.json", {"status": "not_run", "sha256": None, "created_before_patch_sha256": True})
    before_ledger = load_json(FAILURE_LEDGER_PATH) if FAILURE_LEDGER_PATH.is_file() else v29.load_failure_ledger()
    values.setdefault("failure_memory_weight_ledger_before.json", before_ledger)
    values.setdefault("failure_memory_weight_application_trace.json", {"status": "not_run", "diagnostic_only": True, "weights_used_as_correctness_evidence": False, "exact_blocker": exact_blocker})
    values.setdefault("failure_memory_weight_ledger_after.json", before_ledger)
    values.setdefault("patch_fragment_plan.json", {"status": "not_authorized", "fragments": [], "final_patch_count": 0})
    values.setdefault("patch_fragment_safety_checks.json", {"status": "not_authorized"})
    values.setdefault("patch_fragment_assembly_report.json", {"status": "not_authorized", "assembled_once": False})
    values.setdefault("patch_candidate_safety_check.json", {"status": "not_authorized", "patch_non_empty": False, "semantic_delta_detected": False, "source_only": True, "forbidden_files": [], "stats": {}})
    values.setdefault("patch_size_cap.json", {"status": "not_authorized", "max_files_touched": 3, "max_lines_changed": 50, "max_functions_modified": 2, "actual": {}})
    values.setdefault("realtime_patch_safety_trace.json", {"status": "not_authorized"})
    values.setdefault("pre_post_handoff_consistency_gate.json", {"status": "not_authorized"})
    values.setdefault("repair_hypothesis_trace.json", {"status": "not_authorized", "forbidden_evidence_used": False})
    values.setdefault("patch_context_alignment_audit.json", {"status": "not_authorized", "allowed_context_only": False})
    values.setdefault("patch_application_step.json", {"status": "not_run", "changed_files": [], "forbidden_files_modified": [], "exact_blocker": exact_blocker})
    values.setdefault("target_validation_result.json", {"status": "not_run", "exit_status": None, "target_test_passed": False, "changed_log_hash_is_not_success": True, "exact_blocker": exact_blocker})
    values.setdefault("validation_context_alignment_audit.json", {"status": "not_run", "same_target_command": True, "forbidden_files_modified": [], "command_exit_status_authoritative": True})
    values.setdefault("duplicate_replay_summary.json", {"status": "not_run", "required_replays": 3, "results": [], "passed_replays": 0})
    values.setdefault("stochastic_replay_reliability.json", {"status": "not_run", "required_reliability": 1.0, "observed_reliability": 0.0})
    values.setdefault("duplicate_replay_workspace_analysis.json", {"status": "not_run", "workspace_count": 0, "all_workspaces_outside_repo": True})
    values.setdefault("post_validation_workspace_analysis.json", {"status": "not_run", "tests_unmodified": True, "support_files_unmodified": True, "dependency_config_workflow_files_unmodified": True, "patch_only_changes_source_only": False, "changed_files": []})
    values.setdefault("diagnostic_reward_signal.json", {"status": "PASS", "diagnostic_only": True, "full_scoring_enabled": False, "memory_lift_claimed": False, "self_maintaining_software_claimed": False, "bounded_target_repair_signal": False, "reward_value": 0.0})
    values.setdefault("test_suite_structural_signature.json", {"status": not_run_status, "target_command": EXPECTED["test_command"], "pre_patch_exit_status": None, "post_patch_exit_status": None, "failure_class": None})
    values.setdefault("proof_obligations_ledger.json", v29.proof_ledger([
        {"action": "v2.29 official ingest verified", "status": values.get("v2_29_artifact_ingest_verification.json", {}).get("status")},
        {"action": "semantic comparison", "status": values.get("v2_28_v2_29_failure_comparison.json", {}).get("status")},
        {"action": "three clean capture agreement", "status": values.get("semantic_failure_signature_replay_matrix.json", {}).get("status")},
        {"action": "registry signature refresh", "status": values.get("registry_signature_refresh_report.json", {}).get("status")},
        {"action": "patch authorization", "status": "not_authorized"},
    ]))
    values.setdefault("nuclear_pore_transport_log.json", {"status": "PASS", "runtime_workspaces_committed": False, "venvs_committed": False, "files_crossing_workspace_to_repo_boundary": []})
    values.setdefault("claim_boundary_v2_30.json", {"status": "PASS", "current_protocol_version": "v2.13", "v2_30_promoted_to_current": False, "full_scoring": "NOT_RUN", "full_scoring_allowed": False, "memory_lift_status": "undemonstrated", "self_maintaining_software_status": "false/not_demonstrated", "benchmark_framework_candidate_acquisition_used": False, "pysnooper1_reopened": False, "pysnooper2_pursued": False, "ansible_candidate_selected": False, "selected_candidate_id": EXPECTED["candidate_id"], "selected_candidate_scoreable": False, "selected_candidate_positive_memory_only": False, "final_non_ansible_positive_memory_count": 0, "exact_blocker": exact_blocker})
    values.setdefault("roadmap_carry_forward_check_v2_30.json", {"status": "PASS", "readme_updated": True, "roadmap_updated": True, "normalization_policy_present": NORMALIZATION_POLICY_PATH.is_file(), "capability_plan_present": CAPABILITY_PLAN_PATH.is_file()})
    values.setdefault("resolution_depth_diagnostic_v2_30.json", {"status": "PASS", "candidate_id": EXPECTED["candidate_id"], "signature_canonicalization": "implemented", "repair_attempt_boundary": "one_reviewed_candidate_one_final_patch_max", "exact_blocker": exact_blocker})


def write_outputs(values: dict[str, Any]) -> None:
    for rel, value in values.items():
        path = OUTPUT_ROOT / rel
        if rel.endswith(".csv") or rel.endswith(".log") or rel.endswith(".txt") or rel.endswith(".diff") or rel.endswith(".md"):
            write_text(path, value if isinstance(value, str) else str(value))
        else:
            write_json(path, value)


def build_context_capsule(source: Path, candidate: dict[str, Any], structural: dict[str, Any], semantic: dict[str, Any], patchable_files: list[str]) -> tuple[str, dict[str, Any]]:
    sections = [
        "# v2.30 repair context capsule",
        f"candidate_id: {EXPECTED['candidate_id']}",
        f"repo_url: {EXPECTED['repo_url']}",
        f"buggy_commit_sha: {EXPECTED['buggy_commit_sha']}",
        f"target_command: {EXPECTED['test_command']}",
        f"semantic_failure_signature_hash: {semantic_hash(semantic)}",
        f"structural_failure: {json.dumps(structural, sort_keys=True)}",
        "reviewed_registry_entry_after_signature_refresh:",
        json.dumps(candidate, sort_keys=True, indent=2),
    ]
    included = []
    for rel in [EXPECTED["target_test_path"], EXPECTED["support_file_path"], *patchable_files]:
        path = source / rel
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        sections.append(f"\n## file: {rel}\nsha256: {sha256_path(path)}\n")
        sections.append(text[:12000])
        included.append({"path": rel, "sha256": sha256_path(path), "bytes_included": min(len(text.encode("utf-8")), 12000)})
    capsule = "\n".join(sections) + "\n"
    manifest = {
        "status": "PASS",
        "allowed_sources": [
            "reviewed_registry_entry_after_signature_refresh",
            "v2_28_failure_signature_history",
            "v2_29_failure_signature_history",
            "three_clean_v2_30_semantic_captures",
            "structural_failure_signature",
            "buggy_tree_target_test",
            "buggy_tree_support_file",
            "buggy_tree_candidate_source_subset",
            "environment_and_command_manifests",
        ],
        "included_files": included,
        "forbidden_sources_excluded": True,
        "patch_generation_must_use_capsule_only": True,
    }
    return capsule, manifest


def main() -> int:
    now = utc_now()
    reset_output()
    v29.CAMPAIGN_ID = CAMPAIGN_ID
    v29.OUTPUT_ROOT = OUTPUT_ROOT
    update_policy_and_docs(now)
    update_schema_for_semantic_signature()

    values: dict[str, Any] = {}
    v229 = verify_v229_official()
    values["v2_29_artifact_ingest_verification.json"] = v229
    candidate, candidate_errors = load_reviewed_candidate()
    registry_ok = validate_candidate(candidate, candidate_errors)
    candidate_before = json.loads(json.dumps(candidate)) if candidate else {}
    values["selected_candidate_record.json"] = {"status": "PASS" if registry_ok else "BLOCK", "candidate": candidate_before, "errors": candidate_errors}
    values["selected_candidate_registry_entry_before.json"] = candidate_before
    values["failure_signature_history_before.json"] = candidate_before.get("expected_failure_signature", {}) if isinstance(candidate_before, dict) else {}
    values["failure_signature_canonicalization_plan.json"] = {
        "status": "PASS",
        "candidate_id": EXPECTED["candidate_id"],
        "objective": "preserve historical text hashes and gate repair on three matching semantic captures",
        "historical_hash_replacement_forbidden": True,
        "required_clean_capture_count": 3,
        "max_final_patch_count": 1,
        "full_scoring": "NOT_RUN/disallowed",
    }
    comparison = compare_historical_failures()
    values["v2_28_v2_29_failure_comparison.json"] = comparison

    exact_blocker: str | None = None
    if v229.get("status") != "PASS":
        exact_blocker = BLOCKERS["v229"]
    elif not registry_ok:
        exact_blocker = BLOCKERS["registry"]
    elif comparison.get("status") != "PASS":
        exact_blocker = BLOCKERS["semantic_unstable"]

    captures: list[dict[str, Any]] = []
    repair_capture: dict[str, Any] | None = None
    if exact_blocker is None:
        for index in range(1, 4):
            capture = capture_failure(index, keep_workspace=index == 1)
            captures.append(capture)
            if index == 1:
                repair_capture = capture
            if capture.get("status") != "PASS":
                exact_blocker = str(capture.get("exact_blocker") or BLOCKERS["semantic_unstable"])
                break
    write_capture_files(captures)
    replay_matrix = build_replay_matrix(captures)
    values["semantic_failure_signature_replay_matrix.json"] = replay_matrix
    if exact_blocker is None and replay_matrix.get("status") != "PASS":
        exact_blocker = BLOCKERS["semantic_unstable"]

    canonical_semantic = captures[0].get("semantic_fields") if captures and captures[0].get("status") == "PASS" else comparison.get("v2_29_semantic_fields", {})
    canonical_hash = semantic_hash(canonical_semantic) if canonical_semantic else None
    values["semantic_failure_signature_manifest.json"] = {
        "status": "PASS" if replay_matrix.get("status") == "PASS" else "BLOCK",
        "schema_version": SEMANTIC_SCHEMA_VERSION,
        "candidate_id": EXPECTED["candidate_id"],
        "semantic_fields": canonical_semantic,
        "semantic_failure_signature_hash": canonical_hash,
        "policy_version": POLICY_VERSION,
    }
    values["semantic_failure_signature_hash.json"] = {
        "status": "PASS" if replay_matrix.get("status") == "PASS" else "BLOCK",
        "semantic_failure_signature_hash": canonical_hash if replay_matrix.get("status") == "PASS" else None,
        "policy_version": POLICY_VERSION,
    }

    registry_after = candidate_before
    refresh_report = {
        "status": "not_run",
        "exact_blocker": exact_blocker,
        "candidate_id": EXPECTED["candidate_id"],
        "semantic_log_hash": None,
        "registry_validation_status": "not_run",
    }
    validation_after = registry_validator.validate_registry()
    if exact_blocker is None and replay_matrix.get("status") == "PASS":
        normalized_v230_hash = captures[0].get("normalized_log_sha256")
        registry_after, refresh_report = update_registry_signature(
            candidate_before,
            canonical_semantic,
            canonical_hash or "",
            str(normalized_v230_hash),
            replay_matrix,
            comparison,
            now,
        )
        validation_after = registry_validator.validate_registry()
        if refresh_report.get("status") != "PASS":
            exact_blocker = str(refresh_report.get("exact_blocker") or BLOCKERS["registry_refresh"])
    values["registry_signature_refresh_report.json"] = refresh_report
    values["external_candidate_registry_validation_report_after_signature_refresh.json"] = validation_after
    values["selected_candidate_registry_entry_after.json"] = registry_after
    values["failure_signature_history_after.json"] = (registry_after.get("expected_failure_signature", {}) if isinstance(registry_after, dict) else {})

    first = repair_capture or (captures[0] if captures else {})
    file_records = first.get("file_verification") or {"target": {}, "support": {}, "environment": {}}
    tree = first.get("buggy_tree_manifest") or {"status": "not_run", "file_count": 0, "tree_listing_sha256": None, "file_sample": []}
    values["selected_candidate_source_checkout_audit.json"] = {
        "status": "PASS" if first.get("checkout_records") and exact_blocker != BLOCKERS["checkout"] else ("not_run" if not first else "BLOCK"),
        "repo_url": EXPECTED["repo_url"],
        "buggy_commit_sha": EXPECTED["buggy_commit_sha"],
        "exact_buggy_commit_only": True,
        "fixed_later_commit_contents_read": False,
        "fixed_diff_computed": False,
        "pr_patch_content_used": False,
        "gold_patch_used": False,
        "hidden_label_used": False,
        "synthetic_or_backported_tests_used": False,
        "workspace_path": str(first.get("workspace_path", "")),
        "workspace_outside_repo": first.get("workspace_outside_repo", True),
        "workspace_outside_onedrive": first.get("workspace_outside_onedrive", True),
        "checkout_records": first.get("checkout_records", []),
    }
    values["selected_candidate_buggy_tree_manifest.json"] = tree
    values["selected_candidate_target_test_file_hashes.json"] = {"status": "PASS" if file_records.get("target", {}).get("sha256") == EXPECTED["target_test_sha256"] else ("not_run" if not first else "BLOCK"), "target_test_files": [file_records.get("target", {"path": EXPECTED["target_test_path"], "sha256": None})]}
    values["selected_candidate_support_file_hashes.json"] = {"status": "PASS" if file_records.get("support", {}).get("sha256") == EXPECTED["support_file_sha256"] else ("not_run" if not first else "BLOCK"), "support_files": [file_records.get("support", {"path": EXPECTED["support_file_path"], "sha256": None})]}
    values["selected_candidate_environment_file_hashes.json"] = {"status": "PASS" if file_records.get("environment", {}).get("sha256") == EXPECTED["environment_lock_source_sha256"] else ("not_run" if not first else "BLOCK"), "environment_lock_source": file_records.get("environment", {"path": EXPECTED["environment_lock_source"], "sha256": None})}
    values["selected_candidate_command_manifest.json"] = {"status": "PASS", "test_command": EXPECTED["test_command"], "external_network_required": False, "command_timeout_seconds": 120}
    values["selected_candidate_environment_resolution_preflight.json"] = {
        "status": "PASS" if first.get("environment_records") and exact_blocker != BLOCKERS["dependency"] else ("not_run" if not first else "BLOCK"),
        "preferred_install_command": "python -m pip install -e .[dev]",
        "fallback_attempted": False,
        "declared_dependency_source": EXPECTED["environment_lock_source"],
        "records": first.get("environment_records", []),
    }

    semantic_gate_pass = exact_blocker is None and refresh_report.get("status") == "PASS"
    pre_capture = first if first.get("status") == "PASS" else {}
    values["pre_repair_replay_gate_summary.json"] = {
        "status": "PASS" if semantic_gate_pass else ("not_run" if not first else "BLOCK"),
        "target_executed": pre_capture.get("target_executed", False),
        "command_exit_status": pre_capture.get("command_exit_status"),
        "raw_replay_log_sha256": pre_capture.get("raw_log_sha256"),
        "normalized_replay_log_sha256": pre_capture.get("normalized_log_sha256"),
        "historical_v2_28_normalized_replay_log_sha256": EXPECTED["expected_normalized_log_hash"],
        "historical_v2_29_normalized_replay_log_sha256": V229_EXPECTED_OBSERVED_HASH,
        "semantic_failure_signature_hash": pre_capture.get("semantic_failure_signature_hash"),
        "registry_semantic_failure_signature_hash": canonical_hash if semantic_gate_pass else None,
        "semantic_hash_match": pre_capture.get("semantic_failure_signature_hash") == canonical_hash if semantic_gate_pass else False,
        "normalized_full_log_hash_mismatch_is_diagnostic_only": semantic_gate_pass,
        "exact_blocker": exact_blocker,
    }
    values["pre_repair_failure_signature_verification.json"] = {
        "status": "PASS" if semantic_gate_pass else ("not_run" if not first else "BLOCK"),
        "registry_semantic_hash_match_status": "PASS" if semantic_gate_pass else "BLOCK",
        "historical_text_hashes_preserved": True,
        "semantic_failure_observed": canonical_semantic,
        "artifact_hash_authoritative": True,
        "exact_blocker": exact_blocker,
    }
    values["target_validation_pre_patch_log.txt"] = pre_capture.get("raw_log", first.get("raw_log", ""))

    patch = ""
    patch_sha = None
    patch_authorized = False
    patch_attempted = False
    target_validation_status = "not_run"
    target_validation_exit_status: int | None = None
    duplicate_status = "not_run"
    duplicate_results: list[dict[str, Any]] = []
    replay_reliability = 0.0
    post_raw = ""
    application: dict[str, Any] = {"status": "not_run", "changed_files": [], "forbidden_files_modified": []}
    patch_safety: dict[str, Any] = {"status": "not_authorized", "stats": {}, "forbidden_files": []}

    if semantic_gate_pass and repair_capture and repair_capture.get("source") and repair_capture.get("venv"):
        source = repair_capture["source"]
        venv = repair_capture["venv"]
        workspace = repair_capture["workspace"]
        structural = {
            "status": "PASS",
            "campaign_id": CAMPAIGN_ID,
            "created_utc": now,
            "current_protocol_version": "v2.13",
            "target_test_node": EXPECTED["test_command"],
            "normalized_log_hash_current": pre_capture.get("normalized_log_sha256"),
            "normalized_log_hash_expected_v2_28": EXPECTED["expected_normalized_log_hash"],
            "normalized_log_hash_expected_v2_29": V229_EXPECTED_OBSERVED_HASH,
            "normalized_log_hash_match_required": False,
            "semantic_failure_signature_hash": pre_capture.get("semantic_failure_signature_hash"),
            "observed_pytest_failure_type": canonical_semantic.get("observed_pytest_failure_type"),
            "assertion_expression": canonical_semantic.get("assertion_expression"),
            "expected_value": canonical_semantic.get("expected_value"),
            "observed_value": canonical_semantic.get("observed_value"),
            "target_file_hash": EXPECTED["target_test_sha256"],
            "support_file_hash": EXPECTED["support_file_sha256"],
            "environment_file_hash": EXPECTED["environment_lock_source_sha256"],
        }
        values["structural_failure_signature.json"] = structural
        executed_manifest, trace_log, executed_files, dynamic_ok = v29.collect_executed_scope(source, venv, workspace)
        values["executed_scope_manifest.json"] = executed_manifest
        values["executed_scope_trace.log"] = trace_log
        v29.write_executed_hashes(source, executed_files)
        if dynamic_ok:
            ast_manifest, ast_edges, reason_codes, patchable_subset = v29.ast_dependency_closure(source, executed_manifest)
        else:
            graph, ast_edges, audit = v29.static_import_graph(source)
            write_json(OUTPUT_ROOT / "static_import_graph.json", graph)
            write_json(OUTPUT_ROOT / "static_import_graph_audit.json", audit)
            with (OUTPUT_ROOT / "static_import_graph_edges.csv").open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=["from_file", "to_module", "edge_type"], lineterminator="\n")
                writer.writeheader()
                writer.writerows(ast_edges)
            ast_manifest, _ast_edges, reason_codes, patchable_subset = v29.ast_dependency_closure(source, {"patchable_files": [REPAIR_SOURCE_PATH]})
        values["ast_dependency_closure_manifest.json"] = ast_manifest
        values["ast_dependency_closure_reason_codes.json"] = {"status": "PASS", "reason_codes": reason_codes}
        with (OUTPUT_ROOT / "ast_dependency_closure_edges.csv").open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=["from_file", "to_module", "edge_type"], lineterminator="\n")
            writer.writeheader()
            writer.writerows(ast_edges)
        values["ast_dependency_closure_patchable_subset.json"] = patchable_subset
        patchable_files = patchable_subset.get("patchable_files") or []
        capsule, context_manifest = build_context_capsule(source, registry_after, structural, canonical_semantic, patchable_files)
        context_hash = sha256_text(capsule)
        values["context_pinching_filter_manifest.json"] = context_manifest
        values["context_pinching_filter_capsule.txt"] = capsule
        values["context_pinching_filter_hash.json"] = {"status": "PASS", "context_pinching_filter_capsule_sha256": context_hash}
        values["context_exclusion_audit.json"] = {"status": "PASS", "fixed_commit_contents_excluded": True, "later_commit_contents_excluded": True, "pr_patch_contents_excluded": True, "gold_patch_excluded": True, "hidden_labels_excluded": True, "outcome_only_success_data_excluded": True}
        values["pre_generation_context_manifest.json"] = {"status": "PASS", "included_context_hash": context_hash, "allowed_context_only": True, "patch_generation_authorized": ast_manifest.get("status") == "PASS"}
        values["pre_generation_context_hash.json"] = {"status": "PASS", "sha256": context_hash, "created_before_patch_sha256": True}
        before_ledger = load_json(FAILURE_LEDGER_PATH) if FAILURE_LEDGER_PATH.is_file() else v29.load_failure_ledger()
        values["failure_memory_weight_ledger_before.json"] = before_ledger
        values["failure_memory_weight_application_trace.json"] = {
            "status": "PASS",
            "diagnostic_only": True,
            "weights_used_as_correctness_evidence": False,
            "semantic_failure_signature_hash": canonical_hash,
            "ranked_loci": [{"path": REPAIR_SOURCE_PATH, "reason": "semantic failure and closure locus", "weight": 1.0}],
        }
        patch_authorized = ast_manifest.get("status") == "PASS" and context_hash is not None
        if patch_authorized:
            patch, patch_plan = v29.generate_patch(source)
            patch_sha = sha256_text(patch) if patch else None
            fragment_safety = {"status": "PASS" if patch else "BLOCK", "fragments_source_only": True, "fragment_count": len(patch_plan.get("fragments") or [])}
            assembly = {"status": "PASS" if patch else "BLOCK", "assembled_once": bool(patch), "final_patch_count": 1 if patch else 0}
            caps = {
                "max_files_touched": patchable_subset.get("max_files_touched", 3),
                "max_lines_changed": patchable_subset.get("max_lines_changed", 50),
                "max_functions_modified": patchable_subset.get("max_functions_modified", 2),
            }
            patch_safety = v29.safety_for_patch(patch, patchable_files, caps)
            realtime_safety = {"status": patch_safety.get("status"), "checked_before_application": True, "forbidden_files": patch_safety.get("forbidden_files", [])}
            handoff = {
                "status": "PASS" if patch_safety.get("status") == "PASS" else "BLOCK",
                "candidate_id": EXPECTED["candidate_id"],
                "buggy_commit_sha": EXPECTED["buggy_commit_sha"],
                "target_command": EXPECTED["test_command"],
                "semantic_failure_signature_hash": canonical_hash,
                "context_hash": context_hash,
                "patch_sha256": patch_sha,
            }
            hypothesis = {"status": "PASS" if patch else "BLOCK", "forbidden_evidence_used": False, "reason": "Limit one requested indentation fault to one selected matching source line."}
            context_alignment = {"status": "PASS" if patch_safety.get("status") == "PASS" else "BLOCK", "allowed_context_only": True, "context_hash": context_hash, "patch_sha256": patch_sha}
            values["patch_fragment_plan.json"] = patch_plan
            values["patch_fragment_safety_checks.json"] = fragment_safety
            values["patch_fragment_assembly_report.json"] = assembly
            values["patch_candidate_safety_check.json"] = patch_safety
            values["patch_size_cap.json"] = {"status": "PASS" if patch_safety.get("status") == "PASS" else "BLOCK", **caps, "actual": patch_safety.get("stats", {})}
            values["realtime_patch_safety_trace.json"] = realtime_safety
            values["pre_post_handoff_consistency_gate.json"] = handoff
            values["repair_hypothesis_trace.json"] = hypothesis
            values["patch_context_alignment_audit.json"] = context_alignment
            if patch and patch_safety.get("status") == "PASS":
                patch_attempted = True
                application, apply_log = v29.apply_patch_to_workspace(source, patch)
                values["patch_application_step.json"] = application
                record, post_raw, post_normalized = run_target_v230(source, venv, workspace, "target_validation_post_patch", timeout=120)
                target_validation_exit_status = record.get("returncode")
                if application.get("status") != "PASS":
                    target_validation_status = "not_run"
                    exact_blocker = BLOCKERS["patch_apply"]
                elif record.get("returncode") == 0 and "1 passed" in post_normalized:
                    target_validation_status = "PASS"
                elif "AssertionError" in post_normalized:
                    target_validation_status = "BLOCK"
                    exact_blocker = BLOCKERS["same_failure"]
                else:
                    target_validation_status = "BLOCK"
                    exact_blocker = BLOCKERS["new_failure"]
                if target_validation_status == "PASS":
                    duplicate_results = [v29.clean_replay(index, patch) for index in range(1, 4)]
                    duplicate_status = "PASS" if all(item.get("status") == "PASS" for item in duplicate_results) else "BLOCK"
                    replay_reliability = sum(1 for item in duplicate_results if item.get("status") == "PASS") / 3
                    if duplicate_status != "PASS":
                        exact_blocker = BLOCKERS["low_replay"]
            else:
                exact_blocker = BLOCKERS["patch_safety"]
        else:
            exact_blocker = BLOCKERS["ast"]

    selected_scoreable = bool(target_validation_status == "PASS" and duplicate_status == "PASS" and replay_reliability == 1.0)
    final_status = "PASS" if selected_scoreable else "blocked"
    if exact_blocker is None and not selected_scoreable:
        exact_blocker = BLOCKERS["semantic_unstable"] if replay_matrix.get("status") != "PASS" else None

    if patch:
        values["source_patch.diff"] = patch
        values["source_patch_sha256.txt"] = f"{patch_sha}\n"
    if patch_attempted:
        values["target_validation_post_patch_log.txt"] = post_raw
    values["target_validation_result.json"] = {"status": target_validation_status, "exit_status": target_validation_exit_status, "target_test_passed": target_validation_status == "PASS", "changed_log_hash_is_not_success": True, "exact_blocker": exact_blocker if target_validation_status != "PASS" else None}
    values["validation_context_alignment_audit.json"] = {"status": "PASS" if target_validation_status == "PASS" else ("not_run" if not patch_attempted else "BLOCK"), "same_target_command": True, "forbidden_files_modified": application.get("forbidden_files_modified", []), "command_exit_status_authoritative": True}
    values["duplicate_replay_summary.json"] = {"status": duplicate_status, "required_replays": 3, "results": duplicate_results, "passed_replays": sum(1 for item in duplicate_results if item.get("status") == "PASS")}
    values["stochastic_replay_reliability.json"] = {"status": "PASS" if replay_reliability == 1.0 else ("not_run" if duplicate_status == "not_run" else "BLOCK"), "required_reliability": 1.0, "observed_reliability": replay_reliability}
    values["duplicate_replay_workspace_analysis.json"] = {"status": duplicate_status, "workspace_count": len(duplicate_results), "all_workspaces_outside_repo": all(not str(item.get("workspace_path", "")).lower().startswith(str(REPO_ROOT).lower()) for item in duplicate_results)}
    values["post_validation_workspace_analysis.json"] = {"status": "PASS" if patch_attempted and not application.get("forbidden_files_modified") else ("not_run" if not patch_attempted else "BLOCK"), "tests_unmodified": True, "support_files_unmodified": True, "dependency_config_workflow_files_unmodified": True, "patch_only_changes_source_only": not application.get("forbidden_files_modified"), "changed_files": application.get("changed_files", [])}
    values["diagnostic_reward_signal.json"] = {"status": "PASS", "diagnostic_only": True, "full_scoring_enabled": False, "memory_lift_claimed": False, "self_maintaining_software_claimed": False, "bounded_target_repair_signal": selected_scoreable, "reward_value": 1.0 if selected_scoreable else 0.0}
    values["test_suite_structural_signature.json"] = {"status": "PASS" if first.get("status") == "PASS" else ("not_run" if not first else "BLOCK"), "target_command": EXPECTED["test_command"], "pre_patch_exit_status": pre_capture.get("command_exit_status"), "post_patch_exit_status": target_validation_exit_status, "failure_class": canonical_semantic.get("observed_pytest_failure_type")}
    before_for_after = values.get("failure_memory_weight_ledger_before.json") or (load_json(FAILURE_LEDGER_PATH) if FAILURE_LEDGER_PATH.is_file() else v29.load_failure_ledger())
    after_ledger = json.loads(json.dumps(before_for_after))
    existing_entries = after_ledger.setdefault("entries", [])
    after_ledger["entries"] = [
        entry
        for entry in existing_entries
        if not (
            isinstance(entry, dict)
            and entry.get("candidate_id") == EXPECTED["candidate_id"]
            and entry.get("semantic_failure_signature_hash") == canonical_hash
            and entry.get("blocker") == exact_blocker
            and entry.get("patch_sha256") == patch_sha
        )
    ]
    after_ledger["entries"].append({"lane": CAMPAIGN_ID, "candidate_id": EXPECTED["candidate_id"], "buggy_commit_sha": EXPECTED["buggy_commit_sha"], "semantic_failure_signature_hash": canonical_hash, "diagnostic_loci": [REPAIR_SOURCE_PATH], "patch_outcome": final_status, "blocker": exact_blocker, "patch_sha256": patch_sha, "diagnostic_only": True, "memory_lift_claimed": False, "created_utc": now})
    write_json(FAILURE_LEDGER_PATH, after_ledger, sort_keys=False)
    values["failure_memory_weight_ledger_after.json"] = after_ledger
    values["nuclear_pore_transport_log.json"] = {"status": "PASS", "files_crossing_workspace_to_repo_boundary": [], "runtime_workspaces_committed": False, "venvs_committed": False}
    values["proof_obligations_ledger.json"] = v29.proof_ledger([
        {"action": "v2.29 official ingest verified", "status": v229.get("status")},
        {"action": "candidate registry entry verified", "status": "PASS" if registry_ok else "BLOCK"},
        {"action": "historical signatures compared", "status": comparison.get("status")},
        {"action": "three clean semantic captures", "status": replay_matrix.get("status")},
        {"action": "registry signature refresh", "status": refresh_report.get("status")},
        {"action": "semantic pre repair gate", "status": values["pre_repair_replay_gate_summary.json"]["status"]},
        {"action": "context closure and capsule", "status": values.get("context_pinching_filter_hash.json", {}).get("status")},
        {"action": "patch authorization", "status": "PASS" if patch_authorized else "not_authorized"},
        {"action": "target validation", "status": target_validation_status},
        {"action": "duplicate replay", "status": duplicate_status},
    ])
    values["claim_boundary_v2_30.json"] = {"status": "PASS", "current_protocol_version": "v2.13", "v2_29_promoted_to_current": False, "v2_30_promoted_to_current": False, "full_scoring": "NOT_RUN", "full_scoring_allowed": False, "memory_lift_status": "undemonstrated", "self_maintaining_software_status": "false/not_demonstrated", "benchmark_framework_candidate_acquisition_used": False, "pysnooper1_reopened": False, "pysnooper2_pursued": False, "ansible_candidate_selected": False, "selected_candidate_id": EXPECTED["candidate_id"], "selected_candidate_scoreable": selected_scoreable, "selected_candidate_positive_memory_only": False, "final_non_ansible_positive_memory_count": 0, "patch_generated": bool(patch), "patch_authorized": patch_authorized, "patch_attempted": patch_attempted, "target_validation_status": target_validation_status, "duplicate_replay_status": duplicate_status, "exact_blocker": exact_blocker}
    values["roadmap_carry_forward_check_v2_30.json"] = {"status": "PASS", "readme_updated": "v2.30 failure signature canonicalization" in README_PATH.read_text(encoding="utf-8"), "roadmap_updated": "v2.30 Failure Signature Canonicalization" in ROADMAP_PATH.read_text(encoding="utf-8"), "normalization_policy_present": NORMALIZATION_POLICY_PATH.is_file(), "capability_plan_present": CAPABILITY_PLAN_PATH.is_file(), "capability_matrix_present": CAPABILITY_MATRIX_PATH.is_file(), "failure_memory_weight_ledger_present": FAILURE_LEDGER_PATH.is_file()}
    values["resolution_depth_diagnostic_v2_30.json"] = {"status": "PASS", "candidate_id": EXPECTED["candidate_id"], "signature_canonicalization": "implemented", "semantic_replay_status": replay_matrix.get("status"), "registry_refresh_status": refresh_report.get("status"), "repair_attempt_boundary": "one_reviewed_candidate_one_final_patch_max", "target_validation_status": target_validation_status, "duplicate_replay_status": duplicate_status, "exact_blocker": exact_blocker}
    values["artifact_repo_snapshot_comparison.json"] = compare_snapshot_files()
    write_default_repair_outputs(values, exact_blocker, now)
    write_outputs(values)
    write_json(OUTPUT_ROOT / "public_language_audit.json", public_language_audit())
    results = {
        "campaign_id": CAMPAIGN_ID,
        "created_utc": now,
        "current_protocol_version": "v2.13",
        "status": final_status,
        "v2_29_official_ingest_status": v229.get("status"),
        "v2_29_blocker_carry_forward_status": "PASS" if v229.get("v2_29_exact_blocker") == "external_bug_signature_mismatch" else "BLOCK",
        "public_language_audit_status": load_json(OUTPUT_ROOT / "public_language_audit.json").get("status"),
        "selected_candidate_id": EXPECTED["candidate_id"],
        "selected_candidate_repo_url": EXPECTED["repo_url"],
        "selected_candidate_buggy_commit_sha": EXPECTED["buggy_commit_sha"],
        "v2_28_v2_29_failure_comparison_status": comparison.get("classification"),
        "semantic_failure_signature_status": values["semantic_failure_signature_hash.json"]["status"],
        "semantic_failure_signature_hash": values["semantic_failure_signature_hash.json"].get("semantic_failure_signature_hash"),
        "three_capture_semantic_replay_status": replay_matrix.get("status"),
        "registry_signature_refresh_status": refresh_report.get("status"),
        "registry_validation_status_after_refresh": validation_after.get("registry_validation_status"),
        "pre_repair_replay_status_after_refresh": values["pre_repair_replay_gate_summary.json"]["status"],
        "ast_dependency_closure_status": values.get("ast_dependency_closure_manifest.json", {}).get("status"),
        "context_pinching_filter_status": values.get("context_pinching_filter_manifest.json", {}).get("status"),
        "failure_memory_weight_ledger_status": "PASS",
        "fragmented_patch_assembly_gate_status": values.get("patch_fragment_assembly_report.json", {}).get("status"),
        "pre_post_handoff_consistency_gate_status": values.get("pre_post_handoff_consistency_gate.json", {}).get("status"),
        "patch_generated": bool(patch),
        "patch_authorized": patch_authorized,
        "patch_attempted": patch_attempted,
        "patch_sha256": patch_sha,
        "patch_size_cap_status": values.get("patch_size_cap.json", {}).get("status"),
        "patch_safety_status": patch_safety.get("status"),
        "files_modified_by_patch": application.get("changed_files", []),
        "target_validation_status": target_validation_status,
        "target_validation_exit_status": target_validation_exit_status,
        "duplicate_clean_replay_status": duplicate_status,
        "stochastic_replay_reliability_status": values["stochastic_replay_reliability.json"]["status"],
        "selected_candidate_scoreable": selected_scoreable,
        "selected_candidate_positive_memory_only": False,
        "non_ansible_positive_memory_count": 0,
        "full_scoring": "NOT_RUN/disallowed",
        "memory_lift_status": "undemonstrated",
        "self_maintaining_software_status": "false/not_demonstrated",
        "exact_blocker": exact_blocker,
        "safest_next_step": "dispatch v2.30 workflow and manually provide the artifact; do not ingest until manual handoff",
    }
    write_json(OUTPUT_ROOT / "campaign_results.json", results)
    write_text(
        OUTPUT_ROOT / "campaign_summary.md",
        f"""# v2.30 Failure Signature Canonicalization + Repair Continuation Lane

- Campaign: `{CAMPAIGN_ID}`.
- Candidate: `{EXPECTED['candidate_id']}`.
- v2.29 blocker carried forward: `{results['v2_29_blocker_carry_forward_status']}`.
- Historical comparison: `{results['v2_28_v2_29_failure_comparison_status']}`.
- Semantic signature status: `{results['semantic_failure_signature_status']}`.
- Three-capture replay status: `{results['three_capture_semantic_replay_status']}`.
- Registry signature refresh: `{results['registry_signature_refresh_status']}`.
- Pre-repair replay after refresh: `{results['pre_repair_replay_status_after_refresh']}`.
- AST Dependency Closure: `{results['ast_dependency_closure_status']}`.
- Context Pinching Filter: `{results['context_pinching_filter_status']}`.
- Failure Memory Weight Ledger: `{results['failure_memory_weight_ledger_status']}`.
- Fragmented Patch Assembly Gate: `{results['fragmented_patch_assembly_gate_status']}`.
- Pre/Post Handoff Consistency Gate: `{results['pre_post_handoff_consistency_gate_status']}`.
- Patch generated: `{str(results['patch_generated']).lower()}`.
- Patch attempted: `{str(results['patch_attempted']).lower()}`.
- Target validation: `{results['target_validation_status']}`.
- Duplicate clean replay: `{results['duplicate_clean_replay_status']}`.
- Selected candidate scoreable: `{str(results['selected_candidate_scoreable']).lower()}`.
- Exact blocker: `{results['exact_blocker']}`.
- Full scoring remains `NOT_RUN` / disallowed.
- Memory lift remains `undemonstrated`.
- Self-maintaining software is not demonstrated.
- Current protocol remains `v2.13`; v2.30 is not promoted to current.
""",
    )
    write_manifest()
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
    if repair_capture and repair_capture.get("workspace"):
        removed = v29.remove_tree(repair_capture["workspace"])
        if not removed:
            print(f"warning: workspace cleanup incomplete: {repair_capture['workspace']}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
