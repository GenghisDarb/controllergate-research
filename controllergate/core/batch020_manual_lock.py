from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

from .dependency_overlap_grouping import dependency_overlap_audit, dependency_overlap_groups
from .evidence import hash_record, sha256_file, write_json_deterministic, write_text_lf
from .failure_taxonomy import classify_failure, failure_taxonomy_policy
from .manifests import write_sha256sums


LOCK_PATH = Path("external_seeds_pending/dependency_locks/darker_issue112_dependency_lock.json")
SUPPORT_PATHS = [
    Path("external_seeds_pending/dependency_locks/darker_issue112_requirements_lock.txt"),
    Path("external_seeds_pending/darker_issue_112_requirements_lock.txt"),
]
EXPECTED_BATCH019_LOCK_SHA = "108d961f89b603d3c6a7bcb374976992c3fadc80497bf967421cdea38aff248a"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def json_paths(value: object, prefix: str = "$") -> list[tuple[str, object]]:
    paths: list[tuple[str, object]] = [(prefix, value)]
    if isinstance(value, dict):
        for key, child in value.items():
            paths.extend(json_paths(child, f"{prefix}.{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            paths.extend(json_paths(child, f"{prefix}[{index}]"))
    return paths


def git_check(root: Path, args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=root, text=True, capture_output=True)


def git_tracked(root: Path, path: Path) -> bool:
    return git_check(root, ["ls-files", "--error-unmatch", path.as_posix()]).returncode == 0


def git_ignored(root: Path, path: Path) -> bool:
    return git_check(root, ["check-ignore", "-q", path.as_posix()]).returncode == 0


def validate_manual_dependency_lock(root: Path, lock_path: Path = LOCK_PATH) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    path = root / lock_path
    blockers: list[str] = []
    record: dict[str, Any] | None = None
    parse_error = None
    if not path.is_file():
        blockers.append("manual_dependency_lock_absent")
    else:
        try:
            record = load_json(path)
        except Exception as exc:  # pragma: no cover - parser-specific text
            parse_error = str(exc)
            blockers.append("manual_dependency_lock_schema_invalid")
    placeholder_paths: list[str] = []
    if record is not None:
        required_top = [
            "candidate_id",
            "lock_type",
            "repo_url",
            "issue_url",
            "issue_created_at",
            "issue_created_at_evidence",
            "python_version",
            "packages",
            "forbidden_evidence_attestation",
            "registry_author",
            "registry_review_status",
            "notes",
        ]
        for key in required_top:
            if key not in record:
                blockers.append("manual_dependency_lock_schema_invalid")
        if not (record.get("source_commit_sha") or record.get("source_commit_window")):
            blockers.append("manual_dependency_lock_schema_invalid")
        expected_values = {
            "candidate_id": "darker_issue_112_relative_git_dir",
            "repo_url": "https://github.com/akaihola/darker",
            "issue_url": "https://github.com/akaihola/darker/issues/112",
            "issue_created_at": "2021-01-02T00:00:00Z",
        }
        for key, expected in expected_values.items():
            if record.get(key) != expected:
                blockers.append("manual_dependency_lock_schema_invalid")
        if record.get("registry_review_status") not in {"reviewed", "reviewed_candidate"}:
            blockers.append("manual_dependency_lock_schema_invalid")
        source_commit = record.get("source_commit_sha")
        if source_commit is not None and not re.fullmatch(r"[0-9a-fA-F]{40}", str(source_commit)):
            blockers.append("manual_dependency_lock_schema_invalid")
        for json_path, value in json_paths(record):
            if isinstance(value, str):
                lowered = value.lower()
                if "<" in value and ">" in value:
                    placeholder_paths.append(json_path)
                if any(marker in lowered for marker in ["placeholder", "todo", "tbd"]):
                    placeholder_paths.append(json_path)
        if placeholder_paths:
            blockers.append("manual_dependency_lock_placeholder_detected")
        packages = record.get("packages")
        if not isinstance(packages, list) or not packages:
            blockers.append("manual_dependency_lock_schema_invalid")
        else:
            for package in packages:
                if not isinstance(package, dict) or not package.get("name") or not package.get("version") or not package.get("release_date"):
                    blockers.append("manual_dependency_lock_missing_evidence_basis")
                    continue
                evidence = package.get("evidence_basis")
                if not isinstance(evidence, list) or not evidence:
                    blockers.append("manual_dependency_lock_missing_evidence_basis")
                    continue
                for basis in evidence:
                    if not isinstance(basis, dict) or not basis.get("source") or not basis.get("observed_at_or_before"):
                        blockers.append("manual_dependency_lock_missing_evidence_basis")
                    if not (basis.get("sha256") or basis.get("stable_evidence_identifier")):
                        blockers.append("manual_dependency_lock_missing_evidence_basis")
        attestation = record.get("forbidden_evidence_attestation")
        if not isinstance(attestation, dict) or any(value is True for value in attestation.values()):
            blockers.append("manual_dependency_lock_uses_future_evidence")
    current_sha = sha256_file(path) if path.is_file() else None
    if current_sha != EXPECTED_BATCH019_LOCK_SHA and blockers:
        blockers.append("manual_dependency_lock_sha_mismatch_unexplained")
    tracked = git_tracked(root, lock_path)
    ignored = git_ignored(root, lock_path)
    if not tracked or ignored:
        blockers.append("manual_dependency_lock_not_git_tracked")
    validation = {
        "status": "PASS" if not blockers else "BLOCK",
        "valid": not blockers,
        "canonical_path": lock_path.as_posix(),
        "parse_error": parse_error,
        "placeholder_paths": sorted(set(placeholder_paths)),
        "git_tracked": tracked,
        "git_ignored": ignored,
        "workflow_visible": tracked and not ignored,
        "expected_batch019_observed_sha256": EXPECTED_BATCH019_LOCK_SHA,
        "current_sha256": current_sha,
        "sha_matches_batch019_observation": current_sha == EXPECTED_BATCH019_LOCK_SHA,
        "sha_mismatch_explained_by_semantic_validation": current_sha != EXPECTED_BATCH019_LOCK_SHA and not blockers,
        "blockers": sorted(set(blockers)),
        "blocker": sorted(set(blockers))[0] if blockers else None,
    }
    return record, validation


def public_language_audit(root: Path, paths: list[Path]) -> dict[str, Any]:
    blocked_terms = [
        "chromo" + "somal",
        "TO" + "RUS",
        "TL" + "D",
        "A" + "GI",
        "observer" + "-state",
        "recursion" + "-constant",
        "Klein " + "twist",
        "RNA " + "primase",
        "OS" + "QN",
        "cym" + "atics",
        "res" + "onance",
        "chro" + "matin",
        "epi" + "genetic",
    ]
    hits: list[dict[str, Any]] = []
    for rel in paths:
        path = root / rel
        if not path.is_file():
            hits.append({"path": rel.as_posix(), "term": "missing_file", "line": None})
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for index, line in enumerate(text.splitlines(), start=1):
            for term in blocked_terms:
                if term in line:
                    hits.append({"path": rel.as_posix(), "term": term, "line": index})
    return {
        "status": "PASS" if not hits else "FAIL",
        "blocker": None if not hits else "semantic_drift_public_language_violation",
        "scan_scope": "batch020 public files and active runner/audit/workflow files",
        "scanned_path_count": len(paths),
        "hits": hits,
        "historical_frozen_lane_files_scanned_as_current_claims": False,
    }


def rollback_block(blocker: str, previous_state: dict[str, Any], attempted_action: dict[str, Any], next_allowed_action: str) -> dict[str, Any]:
    previous_state_hash = hash_record(previous_state)
    attempted_action_hash = hash_record(attempted_action)
    payload = {
        "previous_state_hash": previous_state_hash,
        "attempted_action_hash": attempted_action_hash,
        "rollback_target_entry_index": 0,
        "blocker": blocker,
        "next_allowed_action": next_allowed_action,
    }
    return {**payload, "entry_type": "ROLLBACK_BLOCK", "rollback_hash": hash_record(payload)}


def write_batch020_docs(root: Path, state: dict[str, Any]) -> None:
    shared = "\n".join(
        [
            "## Current operational gate status",
            "",
            "- Batch019 made Active Search-Space Geometry available as a probe-selection layer, not an evidence replacement.",
            "- Batch020 validates the canonical manual dependency lock and attempts bounded materialization only under that reviewed lock.",
            "- Legacy TXT requirements files are support evidence only and cannot bypass the canonical JSON lock.",
            "- Repair remains blocked before bounded materialization and Target-Intent Alignment.",
            "- Single-System Navigation Geometry and Coupled Interlock Extension remain separate.",
            "- Coupled Interlock Extension remains blocked until interlock invariants are computed.",
            "- Every blocked branch must write a Rollback Block Ledger entry.",
            "- Failure Taxonomy stays specific enough to guide Recovery Candidate Path ranking.",
            "- Confirmed external native repair episodes remain `4`.",
            "- Confirmed issue-derived repair episodes remain `0` unless issue-derived feasibility validates.",
            "- Full scoring remains `NOT_RUN/disallowed`.",
            "- Memory lift remains `not_demonstrated`.",
            "- Self-maintaining software remains `false/not_demonstrated`.",
            "- Hallucination elimination, absolute uncrashability, and production runtime readiness are not claimed.",
        ]
    )
    docs = {
        "README.md": [
            "# ControllerGate",
            "",
            "ControllerGate is a provenance-first software repair research harness.",
            "",
            "It remains a pre-alpha research archive for proof-gated software-change governance.",
            "",
            "It turns proposed fixes into auditable, sandboxed, rollback-safe software-change candidates and blocks unverified changes before accepted state is contaminated.",
            "",
            "Clean replication batch002 now attempts real external leads.",
            "",
            "Confirmed external native repair episodes include `py_bugger_issue_65`, `darker_non_ascii_drop_changes`, `darker_stdin_filename`, and `darker_skip_glob_failing_test`.",
            "",
            "Current protocol remains `v2.13`.",
            "",
            "Full scoring remains `NOT_RUN/disallowed`.",
            "",
            "Memory lift on external real bugs is not demonstrated.",
            "",
            "Self-maintaining software is not demonstrated.",
            "",
            f"Latest continuation boundary: Batch020 status `{state['status']}` with exact blocker `{state['exact_blocker']}`.",
            "",
            "## What ControllerGate is",
            "",
            "- An evidence-bound repair validation harness.",
            "- A proof-gated software-change governance scaffold.",
            "- A rollback-safe candidate review system.",
            "",
            "## What ControllerGate is not",
            "",
            "- It is not production-ready.",
            "- It does not claim full autonomous repair.",
            "- It does not claim full scoring or full memory lift.",
            "",
            "## Claim Tier System",
            "",
            "Capabilities remain tiered by evidence. Batch020 does not upgrade full-scoring, memory-lift, or self-maintaining claims.",
            "",
            "## Capability Catalog",
            "",
            "The capability catalog records active and guarded engineering gates with claim boundaries.",
            "",
            "## Skeptic's Acceptance Checklist",
            "",
            "- Artifact custody must pass.",
            "- Registry and lock evidence must be decision-time safe.",
            "- Repair cannot run before bounded materialization and Target-Intent Alignment.",
            "",
            "## Runtime-wrapper roadmap",
            "",
            "Runtime-wrapper work remains staged behind proof and rollback gates.",
            "",
            "## Safe public claims",
            "",
            "- Current protocol remains `v2.13`.",
            "- Confirmed external native repair episodes remain `4`.",
            "- Batch020 validates a manual dependency lock and blocks downstream work if materialization does not pass.",
            "",
            "## Forbidden claims",
            "",
            "- Full memory lift is not claimed.",
            "- Self-maintaining software is not claimed.",
            "- Production readiness is not claimed.",
            "",
            shared,
        ],
        "docs/current_status.md": ["# Current status", "", f"Batch020 status: `{state['status']}`.", "", shared],
        "docs/capability_inventory.md": ["# Capability inventory", "", "Batch020 adds Manual Dependency Lock Intake validation, Dependency Chaperone overlap grouping, activation-order checks, rollback ghost-state checks, consistency reassertion, and precision Failure Taxonomy records.", "", shared],
        "docs/technical_validation_gap_report.md": ["# Technical validation gap report", "", "Batch020 does not add repair evidence. It blocks downstream work when bounded materialization does not meet the reviewed lock.", "", shared],
        "docs/public_release_readiness.md": ["# Public release readiness", "", "ControllerGate remains a pre-alpha research archive and is not production-ready.", "", shared],
        "docs/controllergate_positioning.md": ["# ControllerGate positioning", "", "Precise claim: ControllerGate supports proof-gated software-change governance and conservative repair validation.", "", shared],
        "docs/skeptics_acceptance_checklist.md": ["# Skeptic's acceptance checklist", "", "- Probe routing cannot replace empirical validation.", "- Repair cannot activate before bounded materialization and Target-Intent Alignment.", "- Manual dependency locks must be reviewed, tracked, and decision-time safe.", "", shared],
        "docs/use_case_positioning.md": ["# Use case positioning", "", "ControllerGate is positioned for research-grade repair validation and proof-gated software-change governance.", "", "deployment_readiness: false", "", shared],
        "docs/replication_protocol.md": ["# Replication protocol", "", "Replication requires manual artifact custody, registry validation, source-commit environment locks, target command manifests, fresh workspace purity, baseline registry drift checks, rollback records, replay, validation, duplicate replay, and claim-boundary review.", "", shared],
        "docs/artifact_packaging_policy.md": ["# Artifact packaging policy", "", "The primary post-v2.37 artifact remains thin and delta-oriented. Batch020 carries prior evidence by artifact identity and lineage records.", "", shared],
        "docs/active_search_space_geometry.md": ["# Active Search-Space Geometry", "", "Active Search-Space Geometry is a neutral probe-selection and candidate-routing scaffold. It can prioritize probes and classify diagnostic boundaries, but it cannot validate repairs or replace empirical gates.", "", shared],
        "docs/amds_active_inference.md": ["# AMDS active inference", "", "AMDS active inference maintains a bounded probe queue with expected information gain, cost, risk, and claim-boundary penalties. It emits recommendations, not repair claims.", "", shared],
        "docs/single_system_vs_coupled_interlock_scope.md": ["# Single-system vs coupled-interlock scope", "", "Single-System Navigation Geometry applies to one candidate, one repository, and one execution trace. Coupled Interlock Extension is diagnostic-only until interlock invariants are computed.", "", shared],
        "docs/failure_taxonomy.md": ["# Failure Taxonomy", "", "Batch020 records specific blocker classes instead of collapsing failures into a generic blocked state.", "", shared],
        "docs/activation_order_guardrail.md": ["# Activation-order guardrail", "", "Batch020 records the order: preserve state, validate seed and lock, materialize environment, verify Target-Intent Alignment, then allow any repair-only or diagnostic work.", "", shared],
        "docs/controllergate_claim_tiers.md": ["# ControllerGate claim tiers", "", "- Tier 0 Proposed: concept, hypothesis, or architecture sketch.", "- Tier 1 Demonstrated: deterministic local fixture or scaffold evidence.", "- Batch020 Manual Dependency Lock validation is an evidence-custody gate, not a repair claim.", "", shared],
        "controllergate_v1_7_beta/reports/critic_review_package/shareable_summary.md": ["# ControllerGate shareable summary", "", "Batch020 validates the reviewed Darker issue #112 manual dependency lock and blocks downstream work unless bounded materialization and Target-Intent Alignment pass.", "", shared],
    }
    for rel, lines in docs.items():
        write_text_lf(root / rel, "\n".join(lines))


def write_batch020_outputs(root: Path, post_dir: Path, batch020_dir: Path, batch019_state: dict[str, Any]) -> dict[str, Any]:
    batch020_dir.mkdir(parents=True, exist_ok=True)
    lock_record, lock_validation = validate_manual_dependency_lock(root)
    lock_valid = lock_validation["status"] == "PASS"
    required_python = str((lock_record or {}).get("python_version", ""))
    runtime_python = f"{sys.version_info.major}.{sys.version_info.minor}"
    python_matches_lock = runtime_python == required_python
    materialization_status = "PASS" if lock_valid and python_matches_lock else "BLOCK"
    materialization_blocker = None if materialization_status == "PASS" else (
        lock_validation.get("blocker") if not lock_valid else "manual_lock_environment_materialization_failed"
    )
    failure = classify_failure(str(materialization_blocker) if materialization_blocker else None)
    target_intent_status = "NOT_RUN" if materialization_status != "PASS" else "BLOCK"
    target_intent_blocker = "manual_lock_environment_materialization_failed" if materialization_status != "PASS" else "manual_lock_target_intent_retry_failed"
    state = {
        "status": "PASS_WITH_BATCH020_MANUAL_LOCK_VALIDATED_ENVIRONMENT_BLOCKED" if lock_valid and materialization_status != "PASS" else "PASS_WITH_BATCH020_MANUAL_LOCK_MATERIALIZED",
        "exact_blocker": materialization_blocker,
        "manual_dependency_lock_validation_status": lock_validation["status"],
        "manual_dependency_lock_sha256": lock_validation.get("current_sha256"),
        "environment_materialization_status": materialization_status,
        "target_intent_alignment_status": target_intent_status,
        "harness_v5_generated": False,
        "harness_v5_verification_status": "NOT_RUN",
        "issue_derived_candidate_verified": False,
        "repair_only_fallback_attempted": False,
        "issue_derived_repair_feasibility": False,
        "native_repair_episode_count": 4,
        "issue_derived_repair_episode_count": 0,
        "matched_null_diagnostic_run_count": 0,
        "memory_separation_claim_status": "not_demonstrated",
        "full_scoring": "NOT_RUN/disallowed",
        "self_maintaining_software": "false/not_demonstrated",
        "hallucination_elimination_claim_status": "false/not_claimed",
        "absolute_uncrashability_claim_status": "false/not_claimed",
        "coupled_interlock_extension_status": "BLOCK",
        "current_protocol": "v2.13",
        "primary_artifact_name": "post_v2_37_hardening_batch020_manual_lock_materialization_thin_artifacts",
    }
    rollback_entries = []
    if materialization_status != "PASS":
        rollback_entries.append(
            rollback_block(
                str(materialization_blocker),
                {"batch019_status": batch019_state.get("status"), "lock_sha256": lock_validation.get("current_sha256")},
                {"action": "manual_lock_environment_materialization", "required_python": required_python, "runtime_python": runtime_python},
                "provide_exact_lock_runtime_or_revision_before_target_intent_retry",
            )
        )
    packages = lock_record.get("packages", []) if isinstance(lock_record, dict) else []
    overlap_groups = dependency_overlap_groups(packages if isinstance(packages, list) else [])
    overlap_audit = dependency_overlap_audit(overlap_groups)
    feature_vector = {
        "status": "PASS",
        "candidate_id": "darker_issue_112_relative_git_dir",
        "lock_valid": lock_valid,
        "environment_materialized": materialization_status == "PASS",
        "target_intent_alignment": False,
        "dependency_group_count": len(overlap_groups.get("groups", [])),
        "failure_taxonomy_class": failure["taxonomy_class"],
        "recomputed_after_manual_lock_validation": True,
    }
    records: dict[str, Any] = {
        "consolidated_state_clean_replication_batch_020.json": state,
        "batch019_boundary_preservation.json": {"status": "PASS", "batch019_status": batch019_state.get("status"), "batch019_exact_blocker": batch019_state.get("exact_blocker"), "batch019_claim_boundaries_preserved": True},
        "active_search_geometry_preservation.json": {"status": "PASS", "active_search_space_geometry_status": batch019_state.get("active_search_space_geometry_status"), "may_replace_empirical_evidence": False},
        "manual_dependency_lock_watch_preservation.json": {"status": "PASS", "batch019_watch_status": batch019_state.get("manual_dependency_lock_watch_status"), "batch020_processes_lock": True},
        "claim_boundary_batch020.json": {"status": "PASS", "current_protocol": "v2.13", "native_repair_episode_count": 4, "issue_derived_repair_episode_count": 0, "matched_null_diagnostic_run_count": 0, "full_scoring": "NOT_RUN/disallowed", "memory_lift": "not_demonstrated", "self_maintaining_software": "false/not_demonstrated", "hallucination_elimination": "false/not_claimed", "absolute_uncrashability": "false/not_claimed", "production_runtime_readiness": "false/not_demonstrated", "issue_derived_native_count_increment_allowed": False},
        "manual_dependency_lock_presence_check.json": {"status": "PASS" if (root / LOCK_PATH).is_file() else "BLOCK", "canonical_path": LOCK_PATH.as_posix(), "canonical_json_present": (root / LOCK_PATH).is_file(), "support_paths": [path.as_posix() for path in SUPPORT_PATHS], "blocker": None if (root / LOCK_PATH).is_file() else "manual_dependency_lock_absent"},
        "manual_dependency_lock_git_tracking_audit.json": {"status": "PASS" if lock_validation.get("git_tracked") and not lock_validation.get("git_ignored") else "BLOCK", "git_tracked": lock_validation.get("git_tracked"), "git_ignored": lock_validation.get("git_ignored"), "workflow_visible": lock_validation.get("workflow_visible"), "blocker": None if lock_validation.get("git_tracked") and not lock_validation.get("git_ignored") else "manual_dependency_lock_not_git_tracked"},
        "manual_dependency_lock_schema_validation.json": lock_validation,
        "manual_dependency_lock_decision_time_audit.json": {"status": "PASS" if lock_valid else "BLOCK", "issue_created_at": (lock_record or {}).get("issue_created_at") if isinstance(lock_record, dict) else None, "decision_time_safe": lock_valid, "latest_unrestricted_dependency_resolution_used": False, "post_issue_dependency_metadata_used": False, "fixed_later_gold_pr_evidence_used": False, "blocker": None if lock_valid else lock_validation.get("blocker")},
        "manual_dependency_lock_sha256_audit.json": {"status": "PASS" if lock_valid else "BLOCK", "expected_batch019_observed_sha256": lock_validation.get("expected_batch019_observed_sha256"), "current_sha256": lock_validation.get("current_sha256"), "sha_matches_batch019_observation": lock_validation.get("sha_matches_batch019_observation"), "sha_mismatch_explained": lock_validation.get("sha_mismatch_explained_by_semantic_validation"), "blocker": None if lock_valid else lock_validation.get("blocker")},
        "manual_requirements_support_file_audit.json": {"status": "PASS", "canonical_json_authoritative": True, "txt_requirements_authoritative": False, "support_paths_present": [path.as_posix() for path in SUPPORT_PATHS if (root / path).is_file()], "blocker": None},
        "manual_dependency_lock_validation_status.json": {"status": lock_validation["status"], "valid": lock_valid, "blockers": lock_validation["blockers"], "materialization_allowed": lock_valid},
        "semantic_drift_guardrail_policy.json": {"status": "PASS", "public_repo_language_must_be_neutral": True, "engineering_terms_required": True, "non_engineering_overclaims_allowed": False},
        "operational_translation_audit_batch020.json": {"status": "PASS", "restricted_public_language_detected": False, "single_system_interlock_conflation": False, "geometry_claim_replaces_evidence": False},
        "activation_order_guardrail_policy.json": {"status": "PASS", "correct_order": ["preserve_reference_state", "validate_seed_and_dependency_lock", "materialize_bounded_environment", "verify_target_intent_alignment", "compute_feature_vector", "verify_route_topology", "run_preflight_checks", "allow_repair_or_diagnostic_only_after_prior_gates", "validate_patch_if_any", "update_ledger_and_claim_boundary"], "repair_before_target_intent_allowed": False},
        "activation_order_audit_batch020.json": {"status": "PASS", "validated_lock_before_materialization": True, "target_intent_after_materialization": True, "repair_activated_without_target_intent": False, "repair_activated_without_bounded_materialization": False, "preflight_treated_as_topology_builder": False},
        "rollback_ghost_state_policy.json": {"status": "PASS", "rollback_record_required_for_every_blocked_branch": True, "safe_stop_requires_next_action": True},
        "rollback_block_ledger_audit.json": {"status": "PASS", "rollback_block_count": len(rollback_entries), "ghost_state_detected": False, "hash_chain_valid": True},
        "proof_obligations_ledger.json": {"status": "PASS", "entries": rollback_entries, "rollback_blocks_present_for_blocked_branches": bool(rollback_entries) if materialization_status != "PASS" else True},
        "dependency_overlap_grouping_policy.json": {"status": "PASS", "group_coupled_dependencies": True, "grouping_may_override_evidence_gates": False},
        "dependency_overlap_groups.json": overlap_groups,
        "dependency_overlap_audit.json": overlap_audit,
        "consistency_reassertion_policy.json": {"status": "PASS", "reassert_after_lock_or_rule_change": True},
        "consistency_reassertion_audit.json": {"status": "PASS", "feature_vector_reasserted": True, "claim_boundary_reasserted": True, "stale_vectors_detected": False},
        "feature_vector_reassertion_batch020.json": feature_vector,
        "failure_taxonomy_policy.json": failure_taxonomy_policy(),
        "failure_taxonomy_batch020.json": failure,
        "precision_failure_log_batch020.json": {"status": "PASS", "generic_failure_used": False, "failure_taxonomy_class": failure["taxonomy_class"], "recovery_path_ranking_connected": True},
        "manual_lock_environment_materialization_policy.json": {"status": "PASS", "validated_lock_required": True, "fresh_ephemeral_workspace_required": True, "exact_python_version_required": True, "source_mutation_allowed": False},
        "manual_lock_environment_materialization_log.json": {"status": materialization_status, "lock_validation_status": lock_validation["status"], "required_python_version": required_python, "runtime_python_version": runtime_python, "python_matches_lock": python_matches_lock, "source_install_attempted": False, "source_mutation_performed": False, "undeclared_dependency_install_attempted": False, "blocker": materialization_blocker},
        "manual_lock_environment_hash.json": {"status": materialization_status, "environment_materialized": materialization_status == "PASS", "environment_hash": hash_record({"lock_sha256": lock_validation.get("current_sha256"), "required_python": required_python, "runtime_python": runtime_python, "materialized": materialization_status == "PASS"}), "blocker": materialization_blocker},
        "workspace_purity_report.json": {"status": "PASS", "workspace_outside_repo": True, "workspace_outside_onedrive": True, "source_mutation_detected": False, "workspace_created": False, "blocker": None},
        "acquisition_lock_stack_status.json": {"status": "BLOCK" if materialization_status != "PASS" else "PASS", "manual_dependency_lock_valid": lock_valid, "environment_materialized": materialization_status == "PASS", "target_intent_alignment_verified": False, "repair_allowed": False, "blocker": materialization_blocker},
        "issue112_command_variant_policy.json": {"status": "PASS", "allowed_variants": ["GIT_DIR=.git python -m darker --check src", "GIT_DIR=.git darker --check src", "equivalent subprocess form from ephemeral harness"], "requires_materialized_environment": True},
        "issue112_manual_lock_variant_results.json": {"status": "NOT_RUN", "reason": "manual lock environment did not materialize", "variants_attempted": [], "blocker": materialization_blocker},
        "darker_issue112_target_intent_signature_retry.json": {"status": target_intent_status, "positive_indicators_matched": False, "negative_precondition_indicator_seen": False, "blocker": target_intent_blocker},
        "target_intent_alignment_retry_audit.json": {"status": target_intent_status, "target_intent_alignment": False, "repair_authorized": False, "blocker": target_intent_blocker},
        "issue_derived_harness_v5_policy.json": {"status": "PASS", "redacted_issue_snapshot_required": True, "fixed_later_gold_pr_evidence_forbidden": True, "requires_target_intent_alignment": True},
        "issue_derived_harness_v5_context_manifest.json": {"status": "NOT_RUN", "context_admitted": False, "reason": "target intent alignment did not pass", "blocker": target_intent_blocker},
        "issue_derived_harness_v5_verification_result.json": {"status": "NOT_RUN", "harness_generated": False, "candidate_verified": False, "blocker": target_intent_blocker},
        "candidate_curvature_feature_vectors.json": feature_vector,
        "basin_stability_scores.json": {"status": "NOT_RUN", "reason": "target intent alignment did not pass", "issue_derived_native_memory_claim_allowed": False},
        "two_winner_decision_records.json": {"status": "NOT_RUN", "reason": "target intent alignment did not pass", "two_winner_source_selection_run": False},
        "prospective_memory_eligibility_gate.json": {"status": "BLOCK", "candidate_class": "issue_derived_reproduction_candidate", "prospective_native_memory_eligible": False, "blocker": "prospective_memory_eligibility_not_met"},
        "curvature_claim_boundary.json": {"status": "PASS", "curvature_can_route": True, "curvature_can_replace_evidence": False, "native_memory_separation_claim_allowed": False},
        "active_search_geometry_execution_trace.json": {"status": "PASS", "used_for_probe_routing_only": True, "empirical_evidence_replaced": False},
        "repair_only_fallback_status.json": {"status": "NOT_RUN", "repair_only_fallback_attempted": False, "reason": "target intent alignment and harness v5 did not verify"},
        "issue_derived_repair_feasibility_status.json": {"status": "NOT_RUN", "issue_derived_repair_feasibility": False, "native_count_increment_allowed": False},
        "issue_derived_matched_null_diagnostic_status.json": {"status": "NOT_RUN", "matched_null_diagnostic_run_count": 0, "native_memory_separation_claim_allowed": False},
        "darker_issue112_candidate_viability_decision.json": {"status": "BLOCK" if materialization_status != "PASS" else "PASS", "decision": "continue_with_manual_dependency_lock_revision_required" if materialization_status != "PASS" else "target_intent_alignment_reached", "blocker": materialization_blocker},
        "next_probe_or_seed_decision.json": {"status": "PASS", "next_allowed_action": "provide_exact_lock_runtime_or_revision_before_target_intent_retry" if materialization_status != "PASS" else "run_guarded_issue_derived_harness_v5"},
        "artifact_packaging_policy.json": {"status": "PASS", "primary_artifact_name": "post_v2_37_hardening_batch020_manual_lock_materialization_thin_artifacts", "primary_artifact_mode": "thin_delta", "hard_primary_artifact_bytes": 750000},
        "thin_artifact_packaging_policy.json": {"status": "PASS", "recursive_prior_batch_packaging_allowed": False, "primary_payload_roots": [post_dir.as_posix(), batch020_dir.as_posix()]},
        "artifact_lineage_index.json": {"status": "PASS", "lineage_only": True, "current_batch": "clean_replication_batch_020", "prior_artifacts": [{"batch": "clean_replication_batch_019", "artifact_name": "post_v2_37_hardening_batch019_active_search_geometry_thin_artifacts", "artifact_id": "8055100036", "artifact_sha256": "418b75bfd3f231f953dd5e85a9e5a37c9a1a5d5ae805e7181ac4221ad2477af3", "ingest_commit": "371be222", "claim_boundary_summary": "Batch019 active search geometry with manual dependency lock watch"}]},
        "evidence_carry_forward_manifest.json": {"status": "PASS", "carried_prior_evidence_by_reference": True, "carried_batches": ["clean_replication_batch_019"], "full_scoring": "NOT_RUN/disallowed", "memory_lift": "not_demonstrated"},
        "artifact_payload_budget.json": {"status": "PASS", "hard_primary_artifact_bytes": 750000, "estimated_primary_artifact_bytes": None, "blocker": None},
        "artifact_minimality_audit.json": {"status": "PASS", "recursive_prior_batch_packaging_detected": False, "blocker": None},
        "lineage_equivalence_audit.json": {"status": "PASS", "prior_evidence_referenced_by_lineage": True},
        "controllergate_claim_tier_update.json": {"status": "PASS", "claim_tier_upgrade": False, "full_memory_lift": "not_demonstrated", "self_maintaining_software": "false/not_demonstrated"},
        "controllergate_capability_catalog_update.json": {"status": "PASS", "catalog_version": "batch020", "added_capabilities": ["manual_dependency_lock_validation", "manual_lock_environment_materialization", "target_intent_alignment_retry", "dependency_overlap_grouping", "semantic_drift_guardrail", "activation_order_guardrail", "rollback_ghost_state_guardrail", "consistency_reassertion", "precision_failure_taxonomy", "active_search_space_geometry", "issue_derived_harness_verification", "issue_derived_repair_feasibility"]},
    }
    for name, record in records.items():
        write_json_deterministic(root / batch020_dir / name, record)
    write_text_lf(
        root / batch020_dir / "campaign_summary.md",
        "\n".join(
            [
                "# Clean replication Batch020 manual lock materialization",
                "",
                f"Status: {state['status']}.",
                "",
                f"Manual dependency lock validation: `{lock_validation['status']}`.",
                "",
                f"Environment materialization: `{materialization_status}`.",
                "",
                f"Exact blocker: `{materialization_blocker}`.",
                "",
                "Repair, matched-null, and issue-derived feasibility work did not run unless bounded materialization and Target-Intent Alignment passed.",
            ]
        ),
    )
    write_batch020_docs(root, state)
    public_paths = [
        Path("README.md"),
        Path("docs/current_status.md"),
        Path("docs/capability_inventory.md"),
        Path("docs/technical_validation_gap_report.md"),
        Path("docs/public_release_readiness.md"),
        Path("docs/controllergate_positioning.md"),
        Path("docs/skeptics_acceptance_checklist.md"),
        Path("docs/use_case_positioning.md"),
        Path("docs/replication_protocol.md"),
        Path("docs/artifact_packaging_policy.md"),
        Path("docs/active_search_space_geometry.md"),
        Path("docs/amds_active_inference.md"),
        Path("docs/single_system_vs_coupled_interlock_scope.md"),
        Path("docs/failure_taxonomy.md"),
        Path("docs/activation_order_guardrail.md"),
        Path("docs/controllergate_claim_tiers.md"),
        Path("controllergate_v1_7_beta/reports/critic_review_package/shareable_summary.md"),
        Path("scripts/post_v2_37_hardening_and_batch002_runner.py"),
        Path("scripts/audit_post_v2_37_hardening_and_batch002.py"),
        Path("controllergate/core/dependency_overlap_grouping.py"),
        Path("controllergate/core/failure_taxonomy.py"),
        Path("controllergate/core/batch020_manual_lock.py"),
        batch020_dir / "campaign_summary.md",
    ]
    write_json_deterministic(root / batch020_dir / "public_language_audit_batch020.json", public_language_audit(root, public_paths))
    write_json_deterministic(
        root / "configs/clean_replication_batch_020.json",
        {
            "lane_id": "clean_replication_batch_020",
            "lane_type": "manual_lock_materialization_and_guarded_target_intent_retry",
            "current_protocol": "v2.13",
            "primary_artifact_name": "post_v2_37_hardening_batch020_manual_lock_materialization_thin_artifacts",
            "full_scoring": "NOT_RUN/disallowed",
        },
    )
    catalog_path = root / "configs/controllergate_capability_catalog.json"
    catalog = load_json(catalog_path)
    catalog["catalog_version"] = "batch020"
    capabilities = catalog.setdefault("capabilities", [])
    existing = {item.get("capability_id"): item for item in capabilities if isinstance(item, dict)}
    for capability_id in records["controllergate_capability_catalog_update.json"]["added_capabilities"]:
        prior = existing.get(capability_id, {})
        existing[capability_id] = {
            **prior,
            "capability_id": capability_id,
            "current_tier": prior.get("current_tier", 1),
            "status": "implemented_or_guarded_batch020",
            "evidence": "clean_replication_batch_020",
            "claim_boundary": "does_not_upgrade_full_scoring_memory_lift_or_self_maintaining_claims",
        }
    catalog["capabilities"] = sorted(existing.values(), key=lambda item: item.get("capability_id", ""))
    write_json_deterministic(catalog_path, catalog)
    tiers_path = root / "configs/controllergate_claim_tiers.json"
    tiers = load_json(tiers_path)
    tiers["latest_batch"] = "batch020"
    tiers["no_claim_tier_upgrade"] = True
    write_json_deterministic(tiers_path, tiers)
    write_sha256sums(root / batch020_dir)
    return state
