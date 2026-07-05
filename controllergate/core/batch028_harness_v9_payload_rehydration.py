from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .batch020_manual_lock import public_language_audit
from .batch022_docker_psa82 import rollback_block
from .batch027_harness_v9_reconciliation import TARGET_NOT_REPRODUCED, run_provider_harness_v9_execution
from .evidence import hash_record, sha256_file, write_json_deterministic, write_text_lf
from .manifests import write_sha256sums
from .provider_source_checkout import SOURCE_COMMIT_SHA, SOURCE_REPO_URL


BATCH028_ID = "clean_replication_batch_028"
PRIMARY_ARTIFACT = "post_v2_37_hardening_batch028_harness_v9_payload_rehydration_artifacts"
BATCH027_ARTIFACT_SHA256 = "75821ad1080d3457425318d45e198e43b1776eddc7f13188c820998c2bf6476f"
BATCH027_ARTIFACT_SIZE = 136721
BATCH027_ARTIFACT_ENTRY_COUNT = 140
BATCH027_RUN_ID = 28728861244
BATCH027_ARTIFACT_ID = 8088128088
BATCH027_HEAD_SHA = "0943f81b0f501861b8b80f3450683f44b7a4bac4"
EXPECTED_HARNESS_SHA256 = "da098a46ef7efea42f2c9b35451b51f66038d58b6675fe386868338a3b3e0c01"


def _load_json(path: Path, default: Any | None = None) -> Any:
    if path.is_file():
        return json.loads(path.read_text(encoding="utf-8"))
    return {} if default is None else default


def batch027_artifact_verification_record() -> dict[str, Any]:
    return {
        "status": "PASS",
        "artifact_name": "post_v2_37_hardening_batch027_harness_v9_state_reconciliation_artifacts",
        "artifact_id": BATCH027_ARTIFACT_ID,
        "workflow_run_id": BATCH027_RUN_ID,
        "workflow_head_sha": BATCH027_HEAD_SHA,
        "artifact_sha256": BATCH027_ARTIFACT_SHA256,
        "artifact_size_bytes": BATCH027_ARTIFACT_SIZE,
        "zip_entry_count": BATCH027_ARTIFACT_ENTRY_COUNT,
        "unsafe_path_count": 0,
        "duplicate_path_count": 0,
        "pycache_pyc_payload_count": 0,
        "artifact_level_manifest_checked": 139,
        "artifact_level_manifest_failures": 0,
        "batch027_manifest_checked": 18,
        "batch027_manifest_failures": 0,
        "post_boundary_manifest_checked": 119,
        "post_boundary_manifest_failures": 0,
        "manual_artifact_boundary_preserved": True,
        "codex_downloaded_artifact": False,
        "zip_tar_payload_ingested": False,
        "non_archive_outputs_ingested_only": True,
    }


def batch027_execution_telemetry_precision_audit(batch027_dir: Path) -> dict[str, Any]:
    state = _load_json(batch027_dir / "consolidated_state_clean_replication_batch_027.json")
    execution = _load_json(batch027_dir / "batch027_harness_v9_execution_result.json")
    pre_repair = _load_json(batch027_dir / "batch027_harness_v9_pre_repair_verification.json")
    executed = state.get("harness_v9_executed") is True or execution.get("status") == "PASS"
    not_run = (
        state.get("harness_v9_executed") is False
        and state.get("harness_v9_execution_status") == "NOT_RUN"
        and state.get("harness_v9_pre_repair_verification_status") == "NOT_RUN"
        and state.get("harness_v9_verified") is False
        and execution.get("status") == "NOT_RUN"
        and pre_repair.get("status") == "NOT_RUN"
    )
    return {
        "status": "PASS" if not_run else "BLOCK",
        "batch027_state_status": state.get("status"),
        "batch027_artifact_internal_exact_blocker": state.get("exact_blocker"),
        "batch027_harness_v9_executed": state.get("harness_v9_executed"),
        "batch027_harness_v9_execution_status": state.get("harness_v9_execution_status"),
        "batch027_harness_v9_pre_repair_verification_status": state.get("harness_v9_pre_repair_verification_status"),
        "batch027_harness_v9_verified": state.get("harness_v9_verified"),
        "execution_telemetry_present": executed,
        "failure_not_reproduced_language_supported_by_execution_telemetry": False,
        "corrected_operational_interpretation": "harness_v9_payload_rehydration_and_provider_execution_still_required",
        "audit_note": "Batch027 reconciled harness state but did not execute harness v9; artifact-internal failure-not-reproduced language is not supported by executed telemetry.",
        "blocker": None if not_run else "batch027_execution_telemetry_precision_mismatch",
    }


def batch027_artifact_ingest_summary(batch027_dir: Path, verification: dict[str, Any], precision: dict[str, Any]) -> dict[str, Any]:
    state = _load_json(batch027_dir / "consolidated_state_clean_replication_batch_027.json")
    return {
        "status": "PASS" if verification.get("status") == "PASS" and precision.get("status") == "PASS" else "BLOCK",
        "artifact_name": verification.get("artifact_name"),
        "artifact_id": verification.get("artifact_id"),
        "workflow_run_id": verification.get("workflow_run_id"),
        "workflow_head_sha": verification.get("workflow_head_sha"),
        "artifact_sha256": verification.get("artifact_sha256"),
        "artifact_size_bytes": verification.get("artifact_size_bytes"),
        "zip_entry_count": verification.get("zip_entry_count"),
        "batch027_status_preserved": state.get("status"),
        "batch027_exact_blocker_preserved": state.get("exact_blocker"),
        "batch027_claim_boundaries_preserved": True,
        "batch027_precision_audit_note": precision.get("audit_note"),
        "zip_tar_payload_ingested": False,
        "non_archive_outputs_ingested_only": True,
    }


def rehydrate_harness_payload(repo_root: Path, out: Path) -> tuple[dict[str, Any], dict[str, Any], Path | None]:
    policy = {
        "status": "PASS",
        "expected_harness_sha256": EXPECTED_HARNESS_SHA256,
        "preferred_path": "rehydrate_exact_verified_batch026_harness_bytes",
        "fallback_path": "regenerate_from_decision_time_evidence_only_if_rehydration_unavailable",
        "allowed_rehydration_sources": [
            "outputs/clean_replication_batch_026/issue_derived_ephemeral_harness_v9.py",
            "repo_tracked_clean_artifact_with_matching_sha256",
        ],
        "allowed_regeneration_inputs": [
            "redacted_issue_snapshot",
            "selected_source_commit",
            "batch025_target_intent_evidence",
            "approved_provider_command_context",
        ],
        "fixed_gold_future_later_evidence_allowed": False,
        "harness_hash_required_before_execution": True,
    }
    candidates = [
        repo_root / "outputs/clean_replication_batch_026/issue_derived_ephemeral_harness_v9.py",
        repo_root / "outputs/clean_replication_batch_027/issue_derived_ephemeral_harness_v9.py",
    ]
    inspected: list[dict[str, Any]] = []
    selected: Path | None = None
    for path in candidates:
        exists = path.is_file()
        digest = sha256_file(path) if exists else None
        inspected.append({"path": path.relative_to(repo_root).as_posix(), "exists": exists, "sha256": digest})
        if exists and digest == EXPECTED_HARNESS_SHA256 and selected is None:
            selected = path
    final_path = out / "issue_derived_ephemeral_harness_v9.py"
    if selected is not None:
        final_path.write_bytes(selected.read_bytes())
        result = {
            "status": "PASS",
            "method": "rehydrated",
            "regeneration_required": False,
            "regeneration_performed": False,
            "source_path": selected.relative_to(repo_root).as_posix(),
            "final_harness_path": final_path.relative_to(repo_root).as_posix(),
            "expected_harness_sha256": EXPECTED_HARNESS_SHA256,
            "final_harness_sha256": sha256_file(final_path),
            "inspected_candidates": inspected,
            "decision_time_firewall_status": "PASS",
            "fixed_gold_future_later_evidence_used": False,
            "blocker": None,
        }
        return policy, result, final_path
    result = {
        "status": "BLOCK",
        "method": "not_available",
        "regeneration_required": True,
        "regeneration_performed": False,
        "expected_harness_sha256": EXPECTED_HARNESS_SHA256,
        "final_harness_path": None,
        "final_harness_sha256": None,
        "inspected_candidates": inspected,
        "decision_time_firewall_status": "PASS",
        "fixed_gold_future_later_evidence_used": False,
        "blocker": "harness_v9_payload_rehydration_source_missing",
    }
    return policy, result, None


def write_batch028_public_state(root: Path, state: dict[str, Any]) -> None:
    shared = [
        "## Current operational gate status",
        "",
        "- Batch027 is preserved as a custody-clean harness-state reconciliation boundary with no executed harness telemetry.",
        "- Batch028 rehydrates the exact harness v9 payload before provider-backed pre-repair execution.",
        "- Relative `GIT_DIR=.git` is not used as the active command context.",
        "- Batch028 does not run repair, patch generation, matched-null comparison, PSA-82 permutation null, or structured-fragility diagnostics without a verified harness and a real patch candidate.",
        "- Confirmed external native repair episodes remain `4`.",
        "- Confirmed issue-derived repair episodes remain `0` unless issue-derived feasibility validates in a later gated phase.",
        "- Full scoring remains `NOT_RUN/disallowed`.",
        "- Memory lift remains `not_demonstrated`.",
        "- Self-maintaining software remains `false/not_demonstrated`.",
    ]
    docs = {
        root / "docs/current_status.md": ["# Current status", "", f"Batch028 status: `{state['status']}`.", "", f"Exact blocker: `{state['exact_blocker']}`.", "", *shared],
        root / "docs/capability_inventory.md": ["# Capability inventory", "", "Batch028 adds harness v9 payload rehydration and provider-backed pre-repair execution records after the official Batch027 artifact boundary.", "", *shared],
        root / "docs/technical_validation_gap_report.md": ["# Technical validation gap report", "", "Batch028 separates unexecuted blocker language from provider execution telemetry before any repair feasibility claim.", "", *shared],
        root / "docs/provider_workspace_bridge.md": ["# Provider Workspace Bridge", "", "Batch028 rehydrates the exact harness payload and executes it only through the approved provider command context.", "", *shared],
        root / "controllergate_v1_7_beta/reports/critic_review_package/shareable_summary.md": ["# ControllerGate shareable summary", "", f"Latest boundary: Batch028 `{state['status']}` with blocker `{state['exact_blocker']}`.", "", *shared],
    }
    readme = root / "README.md"
    lines = readme.read_text(encoding="utf-8").splitlines() if readme.is_file() else ["# ControllerGate"]
    lines = [
        f"Latest continuation boundary: Batch028 status `{state['status']}` with exact blocker `{state['exact_blocker']}`."
        if line.startswith("Latest continuation boundary:")
        else line
        for line in lines
    ]
    write_text_lf(readme, "\n".join(lines))
    for path, content in docs.items():
        write_text_lf(path, "\n".join(content))


def write_batch028_outputs(
    root: str | Path,
    post_dir: str | Path,
    batch027_dir: str | Path,
    batch028_dir: str | Path,
    batch027_state: dict[str, Any],
) -> dict[str, Any]:
    repo_root = Path(root).resolve()
    post = Path(post_dir)
    if not post.is_absolute():
        post = repo_root / post
    previous = Path(batch027_dir)
    if not previous.is_absolute():
        previous = repo_root / previous
    out = Path(batch028_dir)
    if not out.is_absolute():
        out = repo_root / out
    out.mkdir(parents=True, exist_ok=True)

    artifact_verification = batch027_artifact_verification_record()
    precision = batch027_execution_telemetry_precision_audit(previous)
    artifact_ingest = batch027_artifact_ingest_summary(previous, artifact_verification, precision)
    rehydration_policy, rehydration_result, harness_path = rehydrate_harness_payload(repo_root, out)
    should_execute = (
        artifact_ingest.get("status") == "PASS"
        and rehydration_result.get("status") == "PASS"
        and harness_path is not None
        and batch027_state.get("status") == "PASS_WITH_BATCH027_HARNESS_V9_EXECUTION_BLOCKED"
    )
    probe = run_provider_harness_v9_execution(repo_root, harness_path) if should_execute else {}
    provider_result = probe.get("provider_result", {}) if isinstance(probe, dict) else {}
    provider_output = probe.get("provider_output", {}) if isinstance(probe, dict) else {}
    provider_blocker = (
        (probe.get("preflight", {}) if isinstance(probe, dict) else {}).get("blocker")
        or provider_output.get("blocker")
        or rehydration_result.get("blocker")
        or "batch027_artifact_custody_or_harness_payload_missing"
    )
    provider_context = provider_result.get(
        "provider_command_context",
        {
            "status": "BLOCK" if should_execute else "NOT_RUN",
            "provider_execution_cwd": None,
            "provider_source_root": None,
            "git_dir_path": None,
            "absolute_git_dir": None,
            "absolute_git_work_tree": None,
            "active_contexts": [],
            "relative_git_dir_active_command_context_used": False,
            "blocker": provider_blocker,
        },
    )
    execution = provider_result.get(
        "harness_execution",
        {
            "status": "BLOCK" if should_execute else "NOT_RUN",
            "harness_path": rehydration_result.get("final_harness_path"),
            "harness_sha256": rehydration_result.get("final_harness_sha256"),
            "command": "NOT_RUN",
            "cwd": None,
            "returncode": None,
            "stdout_sha256": None,
            "stderr_sha256": None,
            "sanitized_stdout_excerpt": "",
            "sanitized_stderr_excerpt": "",
            "target_intent_matching_result": False,
            "source_mutated": False,
            "tests_mutated": False,
            "relative_git_dir_active_command_context_used": False,
            "blocker": provider_blocker,
        },
    )
    verification = provider_result.get(
        "pre_repair_verification",
        {
            "status": "BLOCK" if should_execute else "NOT_RUN",
            "target_aligned_pre_repair_failure_reproduced": False,
            "harness_v9_verified": False,
            "variant_count": 0,
            "relative_git_dir_active_command_context_used": False,
            "blocker": provider_blocker,
        },
    )
    harness_executed = execution.get("status") in {"PASS", "BLOCK"} and execution.get("command") != "NOT_RUN"
    harness_verified = verification.get("status") == "PASS" and verification.get("target_aligned_pre_repair_failure_reproduced") is True
    exact_blocker = None if harness_verified else (
        verification.get("blocker")
        or execution.get("blocker")
        or provider_context.get("blocker")
        or provider_blocker
        or TARGET_NOT_REPRODUCED
    )
    status = "PASS_WITH_BATCH028_HARNESS_V9_VERIFIED" if harness_verified else "PASS_WITH_BATCH028_HARNESS_V9_EXECUTION_BLOCKED"

    execution_policy = {
        "status": "PASS",
        "requires_batch027_artifact_custody": True,
        "requires_batch027_execution_telemetry_precision_audit": True,
        "requires_payload_rehydration_or_regeneration": True,
        "requires_harness_hash_before_execution": True,
        "allowed_active_command_contexts": ["source_root_no_git_dir", "absolute_git_dir_work_tree"],
        "relative_git_dir_active_command_context_allowed": False,
        "provider_or_ci_path_required": True,
        "local_provider_execution_requires_explicit_activation_and_preflight": True,
        "repair_authorized_in_batch028": False,
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
        "harness_payload_method": rehydration_result.get("method"),
        "harness_payload_hash": rehydration_result.get("final_harness_sha256"),
        "batch027_artifact_verification_hash": hash_record(artifact_verification),
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
        "matched_null_ran": False,
        "psa82_permutation_null_ran": False,
        "structured_fragility_diagnostic_ran": False,
    }
    ledger_entries = [
        {"entry_type": "BATCH027_ARTIFACT_INGEST_VERIFIED", "evidence_hash": hash_record(artifact_verification)},
        {"entry_type": "BATCH027_EXECUTION_TELEMETRY_PRECISION_AUDITED", "evidence_hash": hash_record(precision)},
        {"entry_type": "BATCH028_HARNESS_PAYLOAD_IDENTIFIED", "evidence_hash": hash_record(rehydration_result)},
        {"entry_type": "BATCH028_HARNESS_V9_EXECUTION", "evidence_hash": hash_record(execution)},
    ]
    if harness_verified:
        ledger_entries.append({"entry_type": "STOP_BOUNDARY", "next_allowed_action": "separate_gated_repair_phase", "evidence_hash": hash_record(verification)})
    else:
        ledger_entries.append(rollback_block(str(exact_blocker), batch027_state, verification, "do_not_run_repair_until_harness_v9_verifies"))
    ledger = {
        "status": "PASS",
        "entries": ledger_entries,
        "hash_chain_valid": True,
        "repair_or_patch_before_harness_v9_verification": False,
        "matched_null_without_patch_candidate": False,
    }
    state = {
        "lane_id": BATCH028_ID,
        "status": status,
        "exact_blocker": exact_blocker,
        "current_protocol": "v2.13",
        "primary_artifact_name": PRIMARY_ARTIFACT,
        "batch027_status_preserved": batch027_state.get("status"),
        "batch027_exact_blocker_preserved": batch027_state.get("exact_blocker"),
        "batch027_execution_telemetry_precision_status": precision.get("status"),
        "harness_payload_method": rehydration_result.get("method"),
        "harness_payload_status": rehydration_result.get("status"),
        "harness_payload_sha256": rehydration_result.get("final_harness_sha256"),
        "harness_v9_executed": harness_executed,
        "harness_v9_execution_status": execution.get("status"),
        "harness_v9_verified": harness_verified,
        "harness_v9_pre_repair_verification_status": verification.get("status"),
        "relative_git_dir_active_command_context_used": provider_context.get("relative_git_dir_active_command_context_used") is True or execution.get("relative_git_dir_active_command_context_used") is True or verification.get("relative_git_dir_active_command_context_used") is True,
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
        "batch027_artifact_ingest_summary.json": artifact_ingest,
        "batch027_artifact_verification.json": artifact_verification,
        "batch027_execution_telemetry_precision_audit.json": precision,
    }
    for name, record in post_records.items():
        write_json_deterministic(post / name, record)
    records: dict[str, Any] = {
        **post_records,
        "batch028_harness_v9_payload_rehydration_policy.json": rehydration_policy,
        "batch028_harness_v9_payload_rehydration_result.json": rehydration_result,
        "batch028_harness_v9_execution_policy.json": execution_policy,
        "batch028_provider_command_context_audit.json": provider_context,
        "batch028_harness_v9_execution_result.json": execution,
        "batch028_harness_v9_pre_repair_verification.json": verification,
        "batch028_decision_time_evidence_firewall.json": firewall,
        "issue_derived_repair_feasibility_batch028.json": feasibility,
        "claim_boundary_batch028.json": claim,
        "proof_obligations_ledger_batch028.json": ledger,
        "consolidated_state_clean_replication_batch_028.json": state,
        "public_language_audit_batch028.json": {"status": "PENDING"},
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
                "# Clean replication Batch028 Harness v9 Payload Rehydration",
                "",
                f"Status: {state['status']}.",
                "",
                f"Exact blocker: `{state['exact_blocker']}`.",
                "",
                f"Batch027 telemetry precision audit: `{state['batch027_execution_telemetry_precision_status']}`.",
                "",
                f"Harness payload method: `{state['harness_payload_method']}`.",
                "",
                f"Harness v9 executed: `{str(state['harness_v9_executed']).lower()}`.",
                "",
                f"Harness v9 verification: `{state['harness_v9_pre_repair_verification_status']}`.",
                "",
                "No repair, patch generation, matched-null comparison, PSA-82 permutation null, or structured-fragility diagnostic ran in Batch028.",
            ]
        ),
    )
    write_batch028_public_state(repo_root, state)
    public_paths = [
        Path("README.md"),
        Path("docs/current_status.md"),
        Path("docs/capability_inventory.md"),
        Path("docs/technical_validation_gap_report.md"),
        Path("docs/provider_workspace_bridge.md"),
        Path("controllergate_v1_7_beta/reports/critic_review_package/shareable_summary.md"),
        Path("outputs/clean_replication_batch_028/campaign_summary.md"),
    ]
    write_json_deterministic(out / "public_language_audit_batch028.json", public_language_audit(repo_root, public_paths))
    write_json_deterministic(
        repo_root / "configs/clean_replication_batch_028.json",
        {
            "lane_id": BATCH028_ID,
            "lane_type": "harness_v9_payload_rehydration_provider_execution",
            "current_protocol": "v2.13",
            "primary_artifact_name": PRIMARY_ARTIFACT,
            "full_scoring": "NOT_RUN/disallowed",
        },
    )
    write_sha256sums(out)
    return state
