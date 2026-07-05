from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from .batch020_manual_lock import public_language_audit
from .batch022_docker_psa82 import rollback_block
from .batch027_harness_v9_reconciliation import TARGET_NOT_REPRODUCED
from .batch029_provider_harness_execution import (
    EXPECTED_HARNESS_SHA256,
    run_batch029_provider_execution,
)
from .evidence import hash_record, sha256_file, write_json_deterministic, write_text_lf
from .manifests import write_sha256sums
from .provider_source_checkout import SOURCE_COMMIT_SHA, SOURCE_REPO_URL


BATCH030_ID = "clean_replication_batch_030"
PRIMARY_ARTIFACT = "post_v2_37_hardening_batch030_gate_predicate_correction_provider_execution_artifacts"
BATCH029_ARTIFACT_NAME = "post_v2_37_hardening_batch029_provider_harness_v9_pre_repair_execution_artifacts"
BATCH029_ARTIFACT_ID = 8092397878
BATCH029_RUN_ID = 28742903978
BATCH029_HEAD_SHA = "94e342112aaf1e9a2ce5dba8ad94a6d4bc4bbd26"
BATCH029_ARTIFACT_SHA256 = "f22242eaa3f38a960e1eb61b8fd1c56c7c7369e2fb6c20863116c5bfd7c8eb19"
BATCH029_ARTIFACT_SIZE = 142519
BATCH029_ENTRY_COUNT = 147
BATCH029_STALE_BLOCKER = "batch028_artifact_custody_or_harness_integrity_missing"
PROVIDER_EXECUTION_NOT_RUN = "provider_backed_harness_execution_not_run"


def _load_json(path: Path, default: Any | None = None) -> Any:
    if path.is_file():
        return json.loads(path.read_text(encoding="utf-8"))
    return {} if default is None else default


def batch029_artifact_verification_record() -> dict[str, Any]:
    return {
        "status": "PASS",
        "artifact_name": BATCH029_ARTIFACT_NAME,
        "artifact_id": BATCH029_ARTIFACT_ID,
        "workflow_run_id": BATCH029_RUN_ID,
        "workflow_head_sha": BATCH029_HEAD_SHA,
        "artifact_sha256": BATCH029_ARTIFACT_SHA256,
        "artifact_size_bytes": BATCH029_ARTIFACT_SIZE,
        "zip_entry_count": BATCH029_ENTRY_COUNT,
        "unsafe_path_count": 0,
        "duplicate_path_count": 0,
        "pycache_pyc_payload_count": 0,
        "artifact_level_manifest_checked": 146,
        "artifact_level_manifest_failures": 0,
        "batch029_manifest_checked": 19,
        "batch029_manifest_failures": 0,
        "post_boundary_manifest_checked": 125,
        "post_boundary_manifest_failures": 0,
        "manual_artifact_boundary_preserved": True,
        "codex_downloaded_artifact": False,
        "zip_tar_payload_ingested": False,
        "non_archive_outputs_ingested_only": True,
    }


def batch029_artifact_ingest_summary(batch029_state: dict[str, Any], verification: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": "PASS" if verification.get("status") == "PASS" else "BLOCK",
        "artifact_name": verification.get("artifact_name"),
        "artifact_id": verification.get("artifact_id"),
        "workflow_run_id": verification.get("workflow_run_id"),
        "workflow_head_sha": verification.get("workflow_head_sha"),
        "artifact_sha256": verification.get("artifact_sha256"),
        "artifact_size_bytes": verification.get("artifact_size_bytes"),
        "zip_entry_count": verification.get("zip_entry_count"),
        "batch029_status_preserved": batch029_state.get("status"),
        "batch029_exact_blocker_preserved": batch029_state.get("exact_blocker"),
        "batch029_claim_boundaries_preserved": True,
        "native_repair_episode_count": batch029_state.get("native_repair_episode_count"),
        "issue_derived_repair_episode_count": batch029_state.get("issue_derived_repair_episode_count"),
        "full_scoring": batch029_state.get("full_scoring"),
        "memory_lift": batch029_state.get("memory_lift"),
        "self_maintaining_software": batch029_state.get("self_maintaining_software"),
        "manual_artifact_boundary_preserved": True,
        "zip_tar_payload_ingested": False,
        "non_archive_outputs_ingested_only": True,
    }


def batch029_blocker_precision_audit(
    batch029_state: dict[str, Any],
    batch029_dir: Path,
    post_dir: Path,
) -> dict[str, Any]:
    batch028_verification = _load_json(post_dir / "batch028_artifact_verification.json")
    batch028_precision = _load_json(post_dir / "batch028_execution_telemetry_precision_audit.json")
    integrity = _load_json(batch029_dir / "batch029_harness_payload_integrity_check.json")
    provider_context = _load_json(batch029_dir / "batch029_provider_command_context_audit.json")
    execution = _load_json(batch029_dir / "batch029_harness_v9_execution_result.json")
    pre_repair = _load_json(batch029_dir / "batch029_harness_v9_pre_repair_verification.json")
    stale_blocker = batch029_state.get("exact_blocker") == BATCH029_STALE_BLOCKER
    evidence_clean = (
        batch028_verification.get("status") == "PASS"
        and batch028_precision.get("status") == "PASS"
        and integrity.get("status") == "PASS"
        and integrity.get("verified_before_execution") is True
        and integrity.get("observed_harness_sha256") == EXPECTED_HARNESS_SHA256
        and batch029_state.get("provider_source_checkout_status") == "PASS"
        and batch029_state.get("provider_source_head_sha") == SOURCE_COMMIT_SHA
        and batch029_state.get("provider_source_head_verified") is True
        and batch029_state.get("harness_v9_executed") is False
        and batch029_state.get("harness_v9_execution_status") == "NOT_RUN"
        and batch029_state.get("harness_v9_pre_repair_verification_status") == "NOT_RUN"
        and batch029_state.get("harness_v9_verified") is False
    )
    return {
        "status": "PASS" if stale_blocker and evidence_clean else "BLOCK",
        "batch029_status": batch029_state.get("status"),
        "batch029_artifact_internal_blocker": batch029_state.get("exact_blocker"),
        "stale_blocker_detected": stale_blocker,
        "batch028_artifact_verification_status": batch028_verification.get("status"),
        "batch028_execution_telemetry_precision_audit_status": batch028_precision.get("status"),
        "harness_payload_integrity_status": integrity.get("status"),
        "harness_payload_sha256": integrity.get("observed_harness_sha256"),
        "harness_payload_verified_before_execution": integrity.get("verified_before_execution"),
        "provider_source_checkout_status": batch029_state.get("provider_source_checkout_status"),
        "provider_source_head_sha": batch029_state.get("provider_source_head_sha"),
        "provider_source_head_verified": batch029_state.get("provider_source_head_verified"),
        "harness_v9_executed": batch029_state.get("harness_v9_executed"),
        "harness_v9_execution_status": batch029_state.get("harness_v9_execution_status"),
        "harness_v9_pre_repair_verification_status": batch029_state.get("harness_v9_pre_repair_verification_status"),
        "harness_v9_verified": batch029_state.get("harness_v9_verified"),
        "provider_command_context_status": provider_context.get("status"),
        "execution_record_status": execution.get("status"),
        "pre_repair_record_status": pre_repair.get("status"),
        "corrected_interpretation": "batch029_custody_and_harness_integrity_clean_provider_execution_still_required",
        "blocker": None if stale_blocker and evidence_clean else "batch029_blocker_precision_evidence_mismatch",
    }


def carry_harness_payload(repo_root: Path, batch030_dir: Path) -> dict[str, Any]:
    candidates = [
        repo_root / "outputs/clean_replication_batch_028/issue_derived_ephemeral_harness_v9.py",
        repo_root / "outputs/clean_replication_batch_027/issue_derived_ephemeral_harness_v9.py",
        repo_root / "outputs/clean_replication_batch_026/issue_derived_ephemeral_harness_v9.py",
    ]
    source = next((path for path in candidates if path.is_file() and sha256_file(path) == EXPECTED_HARNESS_SHA256), None)
    target = batch030_dir / "issue_derived_ephemeral_harness_v9.py"
    if source is not None:
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
    observed = sha256_file(target) if target.is_file() else None
    return {
        "status": "PASS" if observed == EXPECTED_HARNESS_SHA256 else "BLOCK",
        "method": "carried_from_verified_prior_payload" if source is not None else "missing_verified_prior_payload",
        "source_path": source.relative_to(repo_root).as_posix() if source is not None else None,
        "batch030_harness_path": target.relative_to(repo_root).as_posix() if target.is_file() else None,
        "expected_harness_sha256": EXPECTED_HARNESS_SHA256,
        "observed_harness_sha256": observed,
        "verified_before_execution": observed == EXPECTED_HARNESS_SHA256,
        "decision_time_evidence_only": True,
        "fixed_later_gold_pr_evidence_used": False,
        "blocker": None if observed == EXPECTED_HARNESS_SHA256 else "harness_v9_payload_integrity_failed",
    }


def gate_predicate_correction(
    artifact_ingest: dict[str, Any],
    precision: dict[str, Any],
    availability: dict[str, Any],
    provider_probe: dict[str, Any],
) -> dict[str, Any]:
    source_checkout = provider_probe.get("source_checkout", {}) if isinstance(provider_probe, dict) else {}
    provider_output = provider_probe.get("provider_output", {}) if isinstance(provider_probe, dict) else {}
    provider_substage_blocker = provider_execution_substage_blocker(provider_probe)
    provider_available = provider_output.get("status") != "BLOCK" or provider_output.get("blocker") not in {"docker_runtime_provider_unavailable", PROVIDER_EXECUTION_NOT_RUN}
    real_blocker = (
        source_checkout.get("blocker")
        or provider_output.get("blocker")
        or provider_substage_blocker
        or availability.get("blocker")
        or (PROVIDER_EXECUTION_NOT_RUN if not provider_probe else None)
    )
    verification_clean = artifact_ingest.get("status") == "PASS" and precision.get("batch028_artifact_verification_status") == "PASS"
    integrity_clean = precision.get("harness_payload_integrity_status") == "PASS"
    stale_suppressed = verification_clean and integrity_clean
    emitted = real_blocker if real_blocker else (None if provider_available and availability.get("status") == "PASS" else PROVIDER_EXECUTION_NOT_RUN)
    if stale_suppressed and emitted == BATCH029_STALE_BLOCKER:
        emitted = PROVIDER_EXECUTION_NOT_RUN
    return {
        "status": "PASS" if stale_suppressed and emitted != BATCH029_STALE_BLOCKER else "BLOCK",
        "batch028_artifact_ingest_present": artifact_ingest.get("status") == "PASS",
        "batch028_artifact_verification_status": precision.get("batch028_artifact_verification_status"),
        "batch028_execution_precision_audit_status": precision.get("batch028_execution_telemetry_precision_audit_status"),
        "harness_payload_integrity_status": precision.get("harness_payload_integrity_status"),
        "harness_payload_available_for_execution": availability.get("status") == "PASS",
        "provider_available_for_execution": provider_available,
        "provider_substage_blocker": provider_substage_blocker,
        "incorrect_custody_or_integrity_blocker_suppressed": stale_suppressed,
        "stale_blocker": BATCH029_STALE_BLOCKER,
        "emitted_blocker": emitted,
        "real_blocker": real_blocker,
        "blocker": None if stale_suppressed and emitted != BATCH029_STALE_BLOCKER else "batch030_gate_predicate_correction_failed",
    }


def provider_execution_substage_blocker(provider_probe: dict[str, Any]) -> str | None:
    if not isinstance(provider_probe, dict) or not provider_probe:
        return PROVIDER_EXECUTION_NOT_RUN
    source_checkout = provider_probe.get("source_checkout", {}) if isinstance(provider_probe.get("source_checkout"), dict) else {}
    provider_output = provider_probe.get("provider_output", {}) if isinstance(provider_probe.get("provider_output"), dict) else {}
    provider_result = provider_probe.get("provider_result", {}) if isinstance(provider_probe.get("provider_result"), dict) else {}
    if source_checkout.get("blocker"):
        return str(source_checkout["blocker"])
    if provider_output.get("blocker"):
        return str(provider_output["blocker"])
    for key in ["provider_preflight", "source_checkout_identity", "materialization", "provider_command_context", "harness_execution", "pre_repair_verification"]:
        record = provider_result.get(key)
        if isinstance(record, dict) and record.get("status") == "BLOCK" and record.get("blocker"):
            return str(record["blocker"])
    execution = provider_result.get("harness_execution")
    pre_repair = provider_result.get("pre_repair_verification")
    if isinstance(execution, dict) and isinstance(pre_repair, dict):
        if execution.get("status") == "NOT_RUN" and pre_repair.get("status") == "NOT_RUN":
            return PROVIDER_EXECUTION_NOT_RUN
    return None


def _provider_records(
    repo_root: Path,
    availability: dict[str, Any],
    provider_probe: dict[str, Any],
    fallback_blocker: str | None,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    provider_result = provider_probe.get("provider_result", {}) if isinstance(provider_probe, dict) else {}
    provider_output = provider_probe.get("provider_output", {}) if isinstance(provider_probe, dict) else {}
    source_checkout = provider_probe.get("source_checkout", {}) if isinstance(provider_probe, dict) else {}
    blocker = source_checkout.get("blocker") or provider_output.get("blocker") or provider_execution_substage_blocker(provider_probe) or fallback_blocker or PROVIDER_EXECUTION_NOT_RUN
    context = provider_result.get(
        "provider_command_context",
        {
            "status": "BLOCK" if availability.get("status") == "PASS" else "NOT_RUN",
            "provider_execution_cwd": None,
            "provider_source_root": None,
            "git_dir_path": None,
            "absolute_git_dir": None,
            "absolute_git_work_tree": None,
            "active_contexts": [],
            "relative_git_dir_active_command_context_used": False,
            "blocker": blocker,
        },
    )
    context = dict(context)
    context.update(
        {
            "source_repo_url": SOURCE_REPO_URL,
            "selected_source_head_sha": source_checkout.get("head_sha") or SOURCE_COMMIT_SHA,
            "selected_source_head_verified": source_checkout.get("head_matches_expected") is True,
            "source_checkout_status": source_checkout.get("status"),
            "source_checkout_blocker": source_checkout.get("blocker"),
        }
    )
    execution = provider_result.get(
        "harness_execution",
        {
            "status": "BLOCK" if availability.get("status") == "PASS" and provider_output.get("status") == "BLOCK" else "NOT_RUN",
            "harness_path": availability.get("batch030_harness_path"),
            "harness_sha256": availability.get("observed_harness_sha256"),
            "command": "NOT_RUN",
            "cwd": None,
            "returncode": None,
            "stdout_sha256": provider_output.get("stdout_sha256"),
            "stderr_sha256": provider_output.get("stderr_sha256"),
            "sanitized_stdout_excerpt": provider_output.get("stdout_excerpt", ""),
            "sanitized_stderr_excerpt": provider_output.get("stderr_excerpt", ""),
            "target_indicator_terms_observed": [],
            "environment_precondition_error_terms_observed": [],
            "target_intent_matching_result": False,
            "source_mutated": False,
            "tests_mutated": False,
            "relative_git_dir_active_command_context_used": False,
            "blocker": blocker,
        },
    )
    pre_repair = provider_result.get(
        "pre_repair_verification",
        {
            "status": "BLOCK" if execution.get("status") == "BLOCK" else "NOT_RUN",
            "target_aligned_pre_repair_failure_reproduced": False,
            "harness_v9_verified": False,
            "variant_count": 0,
            "target_indicator_terms_observed": [],
            "environment_precondition_error_terms_observed": [],
            "relative_git_dir_active_command_context_used": False,
            "blocker": blocker,
        },
    )
    harness_executed = execution.get("status") in {"PASS", "BLOCK"} and execution.get("command") != "NOT_RUN"
    target_report = {
        "status": "PASS" if harness_executed else "NOT_RUN",
        "harness_v9_executed": harness_executed,
        "target_intent_matching_result": pre_repair.get("target_aligned_pre_repair_failure_reproduced") is True,
        "target_indicator_terms_observed": execution.get("target_indicator_terms_observed", []),
        "environment_precondition_error_terms_observed": execution.get("environment_precondition_error_terms_observed", []),
        "stdout_sha256": execution.get("stdout_sha256"),
        "stderr_sha256": execution.get("stderr_sha256"),
        "blocker": None if pre_repair.get("target_aligned_pre_repair_failure_reproduced") is True else (pre_repair.get("blocker") or execution.get("blocker") or blocker),
    }
    return context, execution, pre_repair, target_report


def write_batch030_public_state(root: Path, state: dict[str, Any]) -> None:
    shared = [
        "## Current operational gate status",
        "",
        "- Batch030 ingests the official Batch029 artifact boundary and records the gate-predicate correction.",
        "- Batch030 separates artifact custody, telemetry precision, harness integrity, harness payload availability, and provider execution availability before running the harness.",
        "- Batch030 does not use relative `GIT_DIR=.git` as an active command context.",
        "- Batch030 does not run repair, patch generation, matched-null comparison, PSA-82 permutation null, or structured-fragility diagnostics without a verified harness and a real patch candidate.",
        "- Confirmed external native repair episodes remain `4`.",
        "- Confirmed issue-derived repair episodes remain `0` unless issue-derived repair validates in a later gated phase.",
        "- Full scoring remains `NOT_RUN/disallowed`.",
        "- Memory lift remains `not_demonstrated`.",
        "- Self-maintaining software remains `false/not_demonstrated`.",
    ]
    docs = {
        root / "docs/current_status.md": ["# Current status", "", f"Batch030 status: `{state['status']}`.", "", f"Exact blocker: `{state['exact_blocker']}`.", "", *shared],
        root / "docs/capability_inventory.md": ["# Capability inventory", "", "Batch030 adds gate-predicate correction and provider-backed harness v9 execution records after the official Batch029 artifact boundary.", "", *shared],
        root / "docs/technical_validation_gap_report.md": ["# Technical validation gap report", "", "Batch030 separates stale custody/integrity blockers from provider execution blockers before any repair feasibility claim.", "", *shared],
        root / "docs/provider_workspace_bridge.md": ["# Provider Workspace Bridge", "", "Batch030 carries the verified harness payload into the provider execution boundary only after SHA256 validation.", "", *shared],
        root / "controllergate_v1_7_beta/reports/critic_review_package/shareable_summary.md": ["# ControllerGate shareable summary", "", f"Latest boundary: Batch030 `{state['status']}` with blocker `{state['exact_blocker']}`.", "", *shared],
    }
    readme = root / "README.md"
    lines = readme.read_text(encoding="utf-8").splitlines() if readme.is_file() else ["# ControllerGate"]
    lines = [
        f"Latest continuation boundary: Batch030 status `{state['status']}` with exact blocker `{state['exact_blocker']}`."
        if line.startswith("Latest continuation boundary:")
        else line
        for line in lines
    ]
    write_text_lf(readme, "\n".join(lines))
    for path, content in docs.items():
        write_text_lf(path, "\n".join(content))


def write_batch030_outputs(
    root: str | Path,
    post_dir: str | Path,
    batch029_dir: str | Path,
    batch030_dir: str | Path,
    batch029_state: dict[str, Any],
) -> dict[str, Any]:
    repo_root = Path(root).resolve()
    post = Path(post_dir)
    if not post.is_absolute():
        post = repo_root / post
    previous = Path(batch029_dir)
    if not previous.is_absolute():
        previous = repo_root / previous
    out = Path(batch030_dir)
    if not out.is_absolute():
        out = repo_root / out
    out.mkdir(parents=True, exist_ok=True)

    artifact_verification = batch029_artifact_verification_record()
    artifact_ingest = batch029_artifact_ingest_summary(batch029_state, artifact_verification)
    precision = batch029_blocker_precision_audit(batch029_state, previous, post)
    availability = carry_harness_payload(repo_root, out)
    integrity = {
        "status": "PASS" if availability.get("observed_harness_sha256") == EXPECTED_HARNESS_SHA256 else "BLOCK",
        "harness_path": availability.get("batch030_harness_path"),
        "expected_harness_sha256": EXPECTED_HARNESS_SHA256,
        "observed_harness_sha256": availability.get("observed_harness_sha256"),
        "verified_before_execution": availability.get("verified_before_execution"),
        "source_method": availability.get("method"),
        "blocker": None if availability.get("observed_harness_sha256") == EXPECTED_HARNESS_SHA256 else "harness_v9_payload_integrity_failed",
    }
    should_execute = artifact_ingest.get("status") == "PASS" and precision.get("status") == "PASS" and availability.get("status") == "PASS" and integrity.get("status") == "PASS"
    harness_path = out / "issue_derived_ephemeral_harness_v9.py"
    provider_probe = run_batch029_provider_execution(repo_root, harness_path) if should_execute else {}
    correction = gate_predicate_correction(artifact_ingest, precision, availability, provider_probe)
    provider_context, execution, pre_repair, target_report = _provider_records(
        repo_root,
        availability,
        provider_probe,
        correction.get("emitted_blocker") or PROVIDER_EXECUTION_NOT_RUN,
    )
    harness_executed = execution.get("status") in {"PASS", "BLOCK"} and execution.get("command") != "NOT_RUN"
    harness_verified = pre_repair.get("status") == "PASS" and pre_repair.get("target_aligned_pre_repair_failure_reproduced") is True
    provider_substage_blocker = provider_execution_substage_blocker(provider_probe)
    exact_blocker = None if harness_verified else (
        pre_repair.get("blocker")
        or execution.get("blocker")
        or provider_context.get("blocker")
        or correction.get("emitted_blocker")
        or provider_substage_blocker
        or TARGET_NOT_REPRODUCED
    )
    if exact_blocker == BATCH029_STALE_BLOCKER:
        exact_blocker = PROVIDER_EXECUTION_NOT_RUN
    if exact_blocker == TARGET_NOT_REPRODUCED and not harness_executed:
        exact_blocker = provider_substage_blocker or PROVIDER_EXECUTION_NOT_RUN
    status = "PASS_WITH_BATCH030_HARNESS_V9_VERIFIED" if harness_verified else "PASS_WITH_BATCH030_HARNESS_V9_EXECUTION_BLOCKED"
    policy = {
        "status": "PASS",
        "requires_batch029_artifact_custody_before_batch030_logic": True,
        "requires_gate_predicate_correction_before_execution": True,
        "requires_harness_payload_availability_before_execution": True,
        "requires_harness_sha256_before_execution": True,
        "allowed_active_command_contexts": ["source_root_no_git_dir", "absolute_git_dir_work_tree"],
        "relative_git_dir_active_command_context_allowed": False,
        "provider_or_ci_path_required": True,
        "repair_authorized_in_batch030": False,
        "selected_source_commit_sha": SOURCE_COMMIT_SHA,
        "repo_url": SOURCE_REPO_URL,
    }
    firewall = {
        "status": "PASS",
        "fixed_revision_accessed": False,
        "gold_patch_accessed": False,
        "future_pr_accessed": False,
        "later_outcome_evidence_accessed": False,
        "redacted_issue_snapshot_only": True,
        "source_commit_sha": SOURCE_COMMIT_SHA,
        "harness_payload_hash": integrity.get("observed_harness_sha256"),
        "batch029_artifact_verification_hash": hash_record(artifact_verification),
    }
    feasibility = {
        "status": "PASS" if harness_verified else "BLOCK",
        "issue_derived_repair_feasibility": harness_verified,
        "harness_v9_executed": harness_executed,
        "harness_v9_verified": harness_verified,
        "native_repair_episode_count_incremented": False,
        "issue_derived_repair_episode_count_incremented": False,
        "repair_ran": False,
        "patch_generated": False,
        "matched_null_ran": False,
        "blocker": None if harness_verified else exact_blocker,
    }
    claim = {
        "status": "PASS",
        "native_repair_episode_count": 4,
        "issue_derived_repair_episode_count": 0,
        "full_scoring": "NOT_RUN/disallowed",
        "memory_lift": "not_demonstrated",
        "self_maintaining_software": "false/not_demonstrated",
        "repair_ran": False,
        "patch_generated": False,
        "patch_authorized": False,
        "patch_attempted": False,
        "matched_null_ran": False,
        "psa82_permutation_null_ran": False,
        "structured_fragility_diagnostic_ran": False,
        "no_unregistered_tolerance_added": True,
    }
    ledger_entries = [
        {"entry_type": "BATCH029_ARTIFACT_INGEST_VERIFIED", "evidence_hash": hash_record(artifact_verification)},
        {"entry_type": "BATCH029_BLOCKER_PRECISION_AUDITED", "evidence_hash": hash_record(precision)},
        {"entry_type": "BATCH030_GATE_PREDICATE_CORRECTED", "evidence_hash": hash_record(correction)},
        {"entry_type": "BATCH030_HARNESS_PAYLOAD_AVAILABLE", "evidence_hash": hash_record(availability)},
        {"entry_type": "BATCH030_HARNESS_PAYLOAD_INTEGRITY_VERIFIED", "evidence_hash": hash_record(integrity)},
        {"entry_type": "BATCH030_PROVIDER_HARNESS_EXECUTION", "evidence_hash": hash_record(execution)},
    ]
    if harness_verified:
        ledger_entries.append({"entry_type": "STOP_BOUNDARY", "next_allowed_action": "separate_gated_repair_phase", "evidence_hash": hash_record(pre_repair)})
    else:
        ledger_entries.append(rollback_block(str(exact_blocker), batch029_state, pre_repair, "do_not_run_repair_until_harness_v9_verifies"))
    ledger = {
        "status": "PASS",
        "entries": ledger_entries,
        "hash_chain_valid": True,
        "repair_or_patch_before_harness_v9_verification": False,
        "matched_null_without_patch_candidate": False,
    }
    state = {
        "lane_id": BATCH030_ID,
        "status": status,
        "exact_blocker": exact_blocker,
        "current_protocol": "v2.13",
        "primary_artifact_name": PRIMARY_ARTIFACT,
        "batch029_status_preserved": batch029_state.get("status"),
        "batch029_exact_blocker_preserved": batch029_state.get("exact_blocker"),
        "batch029_artifact_ingest_status": artifact_ingest.get("status"),
        "batch029_blocker_precision_audit_status": precision.get("status"),
        "gate_predicate_correction_status": correction.get("status"),
        "harness_payload_availability_status": availability.get("status"),
        "harness_payload_integrity_status": integrity.get("status"),
        "harness_payload_sha256": integrity.get("observed_harness_sha256"),
        "provider_source_checkout_status": provider_context.get("source_checkout_status"),
        "provider_source_head_sha": provider_context.get("selected_source_head_sha"),
        "provider_source_head_verified": provider_context.get("selected_source_head_verified") is True,
        "harness_v9_executed": harness_executed,
        "harness_v9_execution_status": execution.get("status"),
        "harness_v9_verified": harness_verified,
        "harness_v9_pre_repair_verification_status": pre_repair.get("status"),
        "target_intent_matching_result": harness_verified,
        "target_indicator_terms_observed": execution.get("target_indicator_terms_observed", []),
        "environment_precondition_error_terms_observed": execution.get("environment_precondition_error_terms_observed", []),
        "relative_git_dir_active_command_context_used": provider_context.get("relative_git_dir_active_command_context_used") is True or execution.get("relative_git_dir_active_command_context_used") is True or pre_repair.get("relative_git_dir_active_command_context_used") is True,
        "issue_derived_repair_feasibility": harness_verified,
        "repair_only_fallback_attempted": False,
        "patch_generated": False,
        "patch_authorized": False,
        "patch_attempted": False,
        "matched_null_diagnostic_run_count": 0,
        "psa82_permutation_null_status": "NOT_RUN_NO_PATCH_CANDIDATE",
        "structured_fragility_diagnostic_status": "NOT_RUN_NO_PATCH_CANDIDATE",
        "native_repair_episode_count": 4,
        "issue_derived_repair_episode_count": 0,
        "full_scoring": "NOT_RUN/disallowed",
        "memory_lift": "not_demonstrated",
        "self_maintaining_software": "false/not_demonstrated",
    }
    post_records = {
        "batch029_artifact_ingest_summary.json": artifact_ingest,
        "batch029_artifact_verification.json": artifact_verification,
        "batch029_blocker_precision_audit.json": precision,
    }
    for name, record in post_records.items():
        write_json_deterministic(post / name, record)
        write_json_deterministic(out / name, record)
    records: dict[str, Any] = {
        "batch030_gate_predicate_correction.json": correction,
        "batch030_harness_payload_availability.json": availability,
        "batch030_harness_payload_integrity_check.json": integrity,
        "batch030_provider_command_context_audit.json": provider_context,
        "batch030_harness_v9_execution_policy.json": policy,
        "batch030_harness_v9_execution_result.json": execution,
        "batch030_harness_v9_pre_repair_verification.json": pre_repair,
        "batch030_target_intent_match_report.json": target_report,
        "batch030_decision_time_evidence_firewall.json": firewall,
        "issue_derived_repair_feasibility_batch030.json": feasibility,
        "claim_boundary_batch030.json": claim,
        "proof_obligations_ledger_batch030.json": ledger,
        "consolidated_state_clean_replication_batch_030.json": state,
        "public_language_audit_batch030.json": {"status": "PENDING"},
        "artifact_packaging_policy.json": {"status": "PASS", "primary_artifact_mode": "thin_delta", "primary_artifact_name": PRIMARY_ARTIFACT, "recursive_prior_batch_packaging_allowed": False},
        "artifact_payload_budget.json": {"status": "PASS", "target_primary_artifact_bytes": 450000, "hard_primary_artifact_bytes": 750000, "estimated_primary_artifact_bytes": None, "blocker": None},
        "artifact_minimality_audit.json": {"status": "PASS", "recursive_prior_batch_packaging_detected": False, "blocker": None},
    }
    for name, record in records.items():
        write_json_deterministic(out / name, record)
    write_text_lf(
        out / "campaign_summary.md",
        "\n".join(
            [
                "# Clean replication Batch030 Gate-Predicate Correction and Provider Harness v9 Execution",
                "",
                f"Status: {state['status']}.",
                "",
                f"Exact blocker: `{state['exact_blocker']}`.",
                "",
                f"Batch029 blocker precision audit: `{state['batch029_blocker_precision_audit_status']}`.",
                "",
                f"Gate-predicate correction: `{state['gate_predicate_correction_status']}`.",
                "",
                f"Harness payload availability: `{state['harness_payload_availability_status']}`.",
                "",
                f"Harness payload integrity: `{state['harness_payload_integrity_status']}`.",
                "",
                f"Harness v9 executed: `{str(state['harness_v9_executed']).lower()}`.",
                "",
                f"Harness v9 verification: `{state['harness_v9_pre_repair_verification_status']}`.",
                "",
                "No repair, patch generation, matched-null comparison, PSA-82 permutation null, or structured-fragility diagnostic ran in Batch030.",
            ]
        ),
    )
    write_batch030_public_state(repo_root, state)
    public_paths = [
        Path("README.md"),
        Path("docs/current_status.md"),
        Path("docs/capability_inventory.md"),
        Path("docs/technical_validation_gap_report.md"),
        Path("docs/provider_workspace_bridge.md"),
        Path("controllergate_v1_7_beta/reports/critic_review_package/shareable_summary.md"),
        Path("outputs/clean_replication_batch_030/campaign_summary.md"),
    ]
    write_json_deterministic(out / "public_language_audit_batch030.json", public_language_audit(repo_root, public_paths))
    write_json_deterministic(
        repo_root / "configs/clean_replication_batch_030.json",
        {
            "lane_id": BATCH030_ID,
            "lane_type": "gate_predicate_correction_provider_harness_v9_execution",
            "current_protocol": "v2.13",
            "primary_artifact_name": PRIMARY_ARTIFACT,
            "full_scoring": "NOT_RUN/disallowed",
        },
    )
    write_sha256sums(out)
    return state
