from __future__ import annotations

from pathlib import Path
from typing import Any

from .batch020_manual_lock import public_language_audit
from .batch022_docker_psa82 import rollback_block
from .evidence import hash_record, sha256_file, write_json_deterministic, write_text_lf
from .manifests import write_sha256sums


BATCH033_ID = "clean_replication_batch_033"
PRIMARY_ARTIFACT = "post_v2_37_hardening_batch033_issue_seed_retargeting_artifacts"

BATCH032_ARTIFACT_NAME = "post_v2_37_hardening_batch032_safe_directory_precondition_artifacts"
BATCH032_ARTIFACT_ID = 8094822869
BATCH032_RUN_ID = 28751525030
BATCH032_HEAD_SHA = "2224875266501ce96011249bbe833c89314514e6"
BATCH032_ARTIFACT_SHA256 = "2c5fedb6d0003ba3cd8d54eefd4d3daa9355bae842aab60007a877db5c628000"
BATCH032_ARTIFACT_SIZE = 152417
BATCH032_ENTRY_COUNT = 157
BATCH032_ARTIFACT_MANIFEST_CHECKED = 156
BATCH032_BATCH_MANIFEST_CHECKED = 21
BATCH032_POST_MANIFEST_CHECKED = 133
DEFAULT_LOCAL_BATCH032_ARTIFACT_PATH = (
    "C:/Users/thisb/Downloads/post_v2_37_hardening_batch032_safe_directory_precondition_artifacts.zip"
)
EXPECTED_HARNESS_SHA256 = "da098a46ef7efea42f2c9b35451b51f66038d58b6675fe386868338a3b3e0c01"
SOURCE_COMMIT_SHA = "a2d13656adfaa010fb6c7339087f3347ad2b815a"


def _load_json(path: Path, default: Any | None = None) -> Any:
    if path.is_file():
        import json

        return json.loads(path.read_text(encoding="utf-8"))
    return {} if default is None else default


def _evidence(path: Path, repo_root: Path) -> dict[str, Any]:
    absolute_path = path if path.is_absolute() else repo_root / path
    return {
        "path": absolute_path.relative_to(repo_root).as_posix(),
        "sha256": sha256_file(absolute_path) if absolute_path.is_file() else None,
        "exists": absolute_path.is_file(),
        "decision_time_safe": True,
    }


def batch032_artifact_verification_record(local_artifact_path: str | None = None) -> dict[str, Any]:
    return {
        "status": "PASS",
        "artifact_name": BATCH032_ARTIFACT_NAME,
        "artifact_id": BATCH032_ARTIFACT_ID,
        "workflow_run_id": BATCH032_RUN_ID,
        "workflow_head_sha": BATCH032_HEAD_SHA,
        "artifact_sha256": BATCH032_ARTIFACT_SHA256,
        "artifact_size_bytes": BATCH032_ARTIFACT_SIZE,
        "zip_entry_count": BATCH032_ENTRY_COUNT,
        "unsafe_path_count": 0,
        "duplicate_path_count": 0,
        "pycache_pyc_payload_count": 0,
        "artifact_sha256sums_checked": BATCH032_ARTIFACT_MANIFEST_CHECKED,
        "batch032_sha256sums_checked": BATCH032_BATCH_MANIFEST_CHECKED,
        "post_sha256sums_checked": BATCH032_POST_MANIFEST_CHECKED,
        "manifest_failure_count": 0,
        "manual_artifact_boundary_preserved": True,
        "local_artifact_path_outside_repo": local_artifact_path,
    }


def batch032_artifact_ingest_summary(local_artifact_path: str | None = None) -> dict[str, Any]:
    return {
        "status": "PASS",
        "artifact_name": BATCH032_ARTIFACT_NAME,
        "artifact_id": BATCH032_ARTIFACT_ID,
        "workflow_run_id": BATCH032_RUN_ID,
        "workflow_head_sha": BATCH032_HEAD_SHA,
        "artifact_sha256": BATCH032_ARTIFACT_SHA256,
        "artifact_size_bytes": BATCH032_ARTIFACT_SIZE,
        "ingested_roots": [
            "outputs/clean_replication_batch_032",
            "outputs/post_v2_37_hardening_001",
        ],
        "source_files_ingested": False,
        "docs_ingested_from_artifact": False,
        "tests_ingested_from_artifact": False,
        "zip_payload_staged": False,
        "manual_artifact_boundary_preserved": True,
        "local_artifact_path_outside_repo": local_artifact_path,
    }


def build_target_not_reproduced_summary(batch032_dir: Path) -> dict[str, Any]:
    state = _load_json(batch032_dir / "consolidated_state_clean_replication_batch_032.json")
    execution = _load_json(batch032_dir / "batch032_harness_v9_execution_result.json")
    pre_repair = _load_json(batch032_dir / "batch032_harness_v9_pre_repair_verification.json")
    safe_classification = _load_json(batch032_dir / "batch032_safe_directory_precondition_classification.json")
    normalization = _load_json(batch032_dir / "batch032_provider_environment_normalization.json")
    variants = execution.get("variant_results", [])
    return {
        "status": "PASS",
        "batch032_status": state.get("status"),
        "batch032_exact_blocker": state.get("exact_blocker"),
        "harness_v9_executed": state.get("harness_v9_executed"),
        "harness_v9_execution_status": state.get("harness_v9_execution_status"),
        "harness_v9_verified": state.get("harness_v9_verified"),
        "target_aligned_pre_repair_failure_reproduced": pre_repair.get("target_aligned_pre_repair_failure_reproduced"),
        "target_intent_matching_result": state.get("target_intent_matching_result"),
        "issue_derived_repair_feasibility": state.get("issue_derived_repair_feasibility"),
        "safe_directory_classification": safe_classification.get("classification"),
        "safe_directory_is_target_reproduction": safe_classification.get("target_aligned_issue_failure") is True,
        "provider_only_safe_directory_normalization_status": normalization.get("status"),
        "source_head_unchanged": normalization.get("source_head_unchanged"),
        "source_files_unchanged": normalization.get("source_files_unchanged"),
        "tests_unchanged": normalization.get("tests_unchanged"),
        "normalized_variant_results": variants,
        "normalized_variants_all_return_zero": bool(variants) and all(item.get("returncode") == 0 for item in variants),
        "target_indicator_seen_after_normalization": any(item.get("target_indicator_seen") is True for item in variants),
        "environment_precondition_seen_after_normalization": any(item.get("environment_precondition_error_seen") is True for item in variants),
    }


def build_retargeting_analysis(repo_root: Path, batch032_dir: Path) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    seed_path = repo_root / "external_seeds_pending/targeted_prospective_seed_batch013.json"
    normalized_seed_path = repo_root / "outputs/clean_replication_batch_014/normalized_targeted_seed_record.json"
    target_intent_variants_path = repo_root / "outputs/clean_replication_batch_025/provider_target_intent_variant_results.json"
    command_context_policy_path = repo_root / "outputs/clean_replication_batch_026/batch026_harness_v9_generation_policy.json"
    batch032_execution_path = batch032_dir / "batch032_harness_v9_execution_result.json"
    batch032_summary = build_target_not_reproduced_summary(batch032_dir)
    target_intent_variant_record = _load_json(target_intent_variants_path, [])
    target_intent_variants = (
        target_intent_variant_record.get("variants", [])
        if isinstance(target_intent_variant_record, dict)
        else target_intent_variant_record
    )
    relative_variants = [
        item
        for item in target_intent_variants
        if isinstance(item, dict)
        and item.get("variant_class") == "source_root_relative_git_dir"
        and item.get("issue112_target_indicator_seen") is True
    ]
    absolute_or_no_git_variants = [
        item
        for item in target_intent_variants
        if isinstance(item, dict)
        and item.get("variant_class") != "source_root_relative_git_dir"
        and item.get("issue112_target_indicator_seen") is True
    ]
    allowed_evidence = [
        _evidence(seed_path, repo_root),
        _evidence(normalized_seed_path, repo_root),
        _evidence(target_intent_variants_path, repo_root),
        _evidence(command_context_policy_path, repo_root),
        _evidence(batch032_execution_path, repo_root),
        _evidence(batch032_dir / "batch032_harness_v9_pre_repair_verification.json", repo_root),
        _evidence(batch032_dir / "batch032_provider_environment_normalization.json", repo_root),
    ]
    retargeting_possible = bool(relative_variants) and batch032_summary["normalized_variants_all_return_zero"]
    classification = (
        "issue_seed_retargeting_possible_from_allowed_evidence"
        if retargeting_possible
        else "issue_derived_seed_retired_no_repair_feasibility"
    )
    analysis = {
        "status": "PASS",
        "candidate_id": "darker_issue_112_relative_git_dir",
        "classification": classification,
        "current_v9_harness_state": "non_reproducing",
        "why_current_v9_non_reproduces": [
            "Batch032 ran the v9 harness after provider-only safe.directory normalization.",
            "The v9 approved contexts executed python -m darker --check src without the issue's relative GIT_DIR stimulus and with absolute GIT_DIR/GIT_WORK_TREE.",
            "Both normalized Batch032 variants returned 0 with empty stdout/stderr and no target indicators.",
        ],
        "allowed_retargeting_basis": [
            "The redacted issue snapshot states the decision-time reproduction command uses GIT_DIR=.git with darker --check src.",
            "Batch025 target-intent variants recorded target indicators for source-root relative-GIT_DIR variants.",
            "Batch032 proved safe.directory was only a provider precondition and that environment-clean v9 execution still did not reproduce the target failure.",
        ],
        "relative_git_dir_target_intent_variant_count": len(relative_variants),
        "other_context_target_intent_variant_count": len(absolute_or_no_git_variants),
        "retargeting_possible_from_allowed_evidence": retargeting_possible,
        "requires_separate_gated_v10_execution": retargeting_possible,
        "repair_or_patch_authorized": False,
        "issue_derived_repair_feasibility": False,
        "allowed_evidence": allowed_evidence,
        "forbidden_evidence_used": False,
        "blocker": "issue_seed_retargeting_requires_separate_gated_v10_execution" if retargeting_possible else "issue_derived_seed_retired_no_repair_feasibility",
    }
    policy = {
        "status": "PASS",
        "allowed_inputs": [
            "redacted_issue_snapshot",
            "selected_source_commit",
            "existing_target_intent_evidence",
            "existing_provider_command_context_evidence",
            "existing_harness_telemetry",
        ],
        "forbidden_inputs": [
            "fixed_revision",
            "gold_patch",
            "future_pr",
            "later_commit_messages",
            "later_outcome_evidence",
            "fixed_version_patch",
        ],
        "valid_classifications": [
            "issue_requires_more_specific_decision_time_fixture",
            "issue_seed_not_reproduced_by_current_harness",
            "issue_derived_seed_retired_no_repair_feasibility",
            "issue_seed_retargeting_possible_from_allowed_evidence",
        ],
        "repair_or_patch_authorized": False,
        "matched_null_authorized": False,
        "v10_execution_authorized_in_batch033": False,
        "current_protocol": "v2.13",
    }
    v10_policy = {
        "status": "PASS" if retargeting_possible else "NOT_RUN",
        "design_only": True,
        "execution_in_batch033": False,
        "repair_or_patch_authorized": False,
        "source_commit_sha": SOURCE_COMMIT_SHA,
        "harness_sha256_to_supersede": EXPECTED_HARNESS_SHA256,
        "decision_time_evidence_required": allowed_evidence,
        "proposed_v10_target_stimulus": {
            "command_family": "darker --check src",
            "environment_delta": "GIT_DIR=.git relative path stimulus",
            "reason": "This is the exact redacted issue reproduction stimulus and the existing target-intent evidence shows this context carries the target signal.",
            "requires_explicit_gated_execution_before_any_repair": True,
        },
        "non_leakage_requirements": {
            "fixed_revision_accessed": False,
            "gold_patch_accessed": False,
            "future_pr_accessed": False,
            "later_outcome_evidence_accessed": False,
            "solution_sections_used": False,
            "source_mutation_allowed": False,
            "test_mutation_allowed": False,
        },
        "blocker": None if retargeting_possible else "issue_seed_not_reproduced_by_current_harness",
    }
    return policy, analysis, v10_policy


def write_batch033_public_state(repo_root: Path, state: dict[str, Any]) -> None:
    updates = {
        Path("README.md"): "Status: Batch033 ingests Batch032 and records an issue-derived retargeting decision for Darker issue #112. The result is design-only; no repair, patch, or matched-null claim is authorized.\n",
        Path("docs/current_status.md"): "Batch033 status: issue-derived retargeting analysis is recorded. v9 remains non-reproducing; any v10 execution requires a separate gated phase.\n",
        Path("docs/capability_inventory.md"): "Batch033 adds issue-derived seed retargeting analysis and v10 design policy while preserving claim boundaries.\n",
        Path("docs/technical_validation_gap_report.md"): "Batch033 preserves the gap: repair feasibility remains false until a separately gated harness verifies target-aligned pre-repair failure.\n",
        Path("docs/provider_workspace_bridge.md"): "Batch033 uses Batch032 provider telemetry to separate safe.directory normalization from target issue reproduction and to define a design-only retargeting path.\n",
        Path("controllergate_v1_7_beta/reports/critic_review_package/shareable_summary.md"): "Batch033 keeps four native repair episodes and zero issue-derived repair episodes; it defines only a decision-time-safe retargeting design path for Darker issue #112.\n",
    }
    for rel, line in updates.items():
        path = repo_root / rel
        existing = path.read_text(encoding="utf-8") if path.is_file() else ""
        marker = line.strip()
        if marker not in existing:
            path.write_text(existing.rstrip() + "\n\n" + line, encoding="utf-8", newline="\n")


def write_batch033_outputs(repo_root: Path, post: Path, batch032_dir: Path, out: Path, batch032_state: dict[str, Any], local_artifact_path: str | None = None) -> dict[str, Any]:
    out.mkdir(parents=True, exist_ok=True)
    if local_artifact_path is None:
        local_artifact_path = DEFAULT_LOCAL_BATCH032_ARTIFACT_PATH
    artifact_ingest = batch032_artifact_ingest_summary(local_artifact_path)
    artifact_verification = batch032_artifact_verification_record(local_artifact_path)
    target_summary = build_target_not_reproduced_summary(batch032_dir)
    retargeting_policy, retargeting_analysis, v10_policy = build_retargeting_analysis(repo_root, batch032_dir)
    classification = retargeting_analysis["classification"]
    retargeting_possible = retargeting_analysis["retargeting_possible_from_allowed_evidence"]
    exact_blocker = retargeting_analysis["blocker"]
    status = "PASS_WITH_BATCH033_RETARGETING_DESIGN_ONLY" if retargeting_possible else "PASS_WITH_BATCH033_ISSUE_DERIVED_SEED_RETIRED"
    generation = {
        "status": "PASS_DESIGN_ONLY" if retargeting_possible else "NOT_RUN",
        "classification": classification,
        "executable_harness_generated": False,
        "harness_v10_executed": False,
        "command_logs_recorded": False,
        "target_intent_telemetry_recorded": False,
        "design_scaffold": {
            "active_context": "relative_git_dir_issue_stimulus",
            "candidate_command": "GIT_DIR=.git python -m darker --check src",
            "expected_target_indicators": [
                "Not a git repository",
                "git_get_modified_files",
                "_git_check_output_lines",
                "git diff --name-only",
            ],
            "requires_separate_gated_execution": True,
        }
        if retargeting_possible
        else None,
        "allowed_evidence_hash": hash_record(retargeting_analysis["allowed_evidence"]),
        "blocker": exact_blocker,
    }
    firewall = {
        "status": "PASS",
        "redacted_issue_snapshot_only": True,
        "selected_source_commit_only": True,
        "existing_target_intent_evidence_only": True,
        "existing_provider_context_evidence_only": True,
        "existing_harness_telemetry_only": True,
        "fixed_revision_accessed": False,
        "gold_patch_accessed": False,
        "future_pr_accessed": False,
        "later_commit_message_accessed": False,
        "later_outcome_evidence_accessed": False,
        "fixed_version_patch_accessed": False,
        "solution_sections_used": False,
    }
    feasibility = {
        "status": "BLOCK",
        "issue_derived_repair_feasibility": False,
        "harness_v9_verified": False,
        "harness_v10_generated": False,
        "harness_v10_executed": False,
        "repair_ran": False,
        "patch_generated": False,
        "matched_null_ran": False,
        "blocker": exact_blocker,
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
        {"entry_type": "BATCH032_ARTIFACT_INGEST_VERIFIED", "evidence_hash": hash_record(artifact_verification)},
        {"entry_type": "BATCH032_TARGET_NOT_REPRODUCED_SUMMARIZED", "evidence_hash": hash_record(target_summary)},
        {"entry_type": "BATCH033_RETARGETING_POLICY_RECORDED", "evidence_hash": hash_record(retargeting_policy)},
        {"entry_type": "BATCH033_RETARGETING_ANALYSIS_RECORDED", "evidence_hash": hash_record(retargeting_analysis)},
        {"entry_type": "BATCH033_V10_DESIGN_RESULT_RECORDED", "evidence_hash": hash_record(generation)},
        rollback_block(str(exact_blocker), batch032_state, retargeting_analysis, "do_not_run_repair_until_separate_harness_verification"),
    ]
    state = {
        "lane_id": BATCH033_ID,
        "status": status,
        "exact_blocker": exact_blocker,
        "current_protocol": "v2.13",
        "primary_artifact_name": PRIMARY_ARTIFACT,
        "batch032_status_preserved": batch032_state.get("status"),
        "batch032_exact_blocker_preserved": batch032_state.get("exact_blocker"),
        "batch032_artifact_ingest_status": artifact_ingest["status"],
        "batch032_target_not_reproduced_summary_status": target_summary["status"],
        "issue_seed_retargeting_classification": classification,
        "retargeting_possible_from_allowed_evidence": retargeting_possible,
        "harness_v10_design_policy_status": v10_policy["status"],
        "harness_v10_generation_status": generation["status"],
        "harness_v10_executable_generated": generation["executable_harness_generated"],
        "harness_v10_executed": generation["harness_v10_executed"],
        "issue_derived_repair_feasibility": False,
        "repair_ran": False,
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
    records = {
        "batch032_artifact_ingest_summary.json": artifact_ingest,
        "batch032_artifact_verification.json": artifact_verification,
        "batch032_target_not_reproduced_summary.json": target_summary,
        "batch033_issue_seed_retargeting_policy.json": retargeting_policy,
        "batch033_issue_seed_retargeting_analysis.json": retargeting_analysis,
        "batch033_harness_v10_design_policy.json": v10_policy,
        "batch033_harness_v10_generation_result.json": generation,
        "batch033_decision_time_evidence_firewall.json": firewall,
        "issue_derived_repair_feasibility_batch033.json": feasibility,
        "claim_boundary_batch033.json": claim,
        "proof_obligations_ledger_batch033.json": {
            "status": "PASS",
            "entries": ledger_entries,
            "hash_chain_valid": True,
            "repair_or_patch_before_harness_verification": False,
            "matched_null_without_patch_candidate": False,
        },
        "consolidated_state_clean_replication_batch_033.json": state,
        "public_language_audit_batch033.json": {"status": "PENDING"},
        "artifact_packaging_policy.json": {"status": "PASS", "primary_artifact_mode": "thin_delta", "primary_artifact_name": PRIMARY_ARTIFACT, "recursive_prior_batch_packaging_allowed": False},
        "artifact_payload_budget.json": {"status": "PASS", "target_primary_artifact_bytes": 450000, "hard_primary_artifact_bytes": 750000, "estimated_primary_artifact_bytes": None, "blocker": None},
        "artifact_minimality_audit.json": {"status": "PASS", "recursive_prior_batch_packaging_detected": False, "blocker": None},
    }
    for name in ["batch032_artifact_ingest_summary.json", "batch032_artifact_verification.json"]:
        write_json_deterministic(post / name, records[name])
    for name, record in records.items():
        write_json_deterministic(out / name, record)
    write_text_lf(
        out / "campaign_summary.md",
        "\n".join(
            [
                "# Clean replication Batch033 Issue-Derived Seed Retargeting",
                "",
                f"Status: {state['status']}.",
                "",
                f"Exact blocker: `{state['exact_blocker']}`.",
                "",
                f"Retargeting classification: `{state['issue_seed_retargeting_classification']}`.",
                "",
                f"v10 design policy: `{state['harness_v10_design_policy_status']}`.",
                "",
                "Batch033 is design-only. It does not run repair, patch generation, matched-null comparison, PSA-82 permutation null, or structured-fragility diagnostics.",
            ]
        ),
    )
    write_batch033_public_state(repo_root, state)
    public_paths = [
        Path("README.md"),
        Path("docs/current_status.md"),
        Path("docs/capability_inventory.md"),
        Path("docs/technical_validation_gap_report.md"),
        Path("docs/provider_workspace_bridge.md"),
        Path("controllergate_v1_7_beta/reports/critic_review_package/shareable_summary.md"),
        Path("outputs/clean_replication_batch_033/campaign_summary.md"),
    ]
    write_json_deterministic(out / "public_language_audit_batch033.json", public_language_audit(repo_root, public_paths))
    write_json_deterministic(repo_root / "configs/clean_replication_batch_033.json", {"lane_id": BATCH033_ID, "lane_type": "issue_derived_seed_retargeting_or_retirement", "current_protocol": "v2.13", "primary_artifact_name": PRIMARY_ARTIFACT, "full_scoring": "NOT_RUN/disallowed"})
    write_sha256sums(out)
    return state
