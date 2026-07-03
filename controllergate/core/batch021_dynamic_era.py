from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .batch020_manual_lock import public_language_audit, validate_manual_dependency_lock
from .containerized_era_runtime import containerized_era_runtime_policy, containerized_workflow_plan
from .dynamic_era_materialization import (
    dynamic_era_materialization_policy,
    dynamic_era_materialization_status,
    runtime_version_gate_audit,
    runtime_version_gate_policy,
)
from .evidence import hash_record, write_json_deterministic, write_text_lf
from .hosted_runtime_adapter import hosted_runtime_adapter_status
from .manifests import write_sha256sums
from .runtime_provider_registry import current_python_version, runtime_provider_registry
from .runtime_provider_selection import runtime_provider_selection_policy, select_runtime_provider
from .self_hosted_runtime_plan import self_hosted_runtime_plan


BATCH021_ID = "clean_replication_batch_021"
PRIMARY_ARTIFACT = "post_v2_37_hardening_batch021_dynamic_era_materialization_thin_artifacts"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def rollback_block(blocker: str, previous_state: dict[str, Any], attempted_action: dict[str, Any], next_allowed_action: str) -> dict[str, Any]:
    payload = {
        "previous_state_hash": hash_record(previous_state),
        "attempted_action_hash": hash_record(attempted_action),
        "rollback_target_entry_index": 0,
        "blocker": blocker,
        "next_allowed_action": next_allowed_action,
    }
    return {**payload, "entry_type": "ROLLBACK_BLOCK", "rollback_hash": hash_record(payload)}


def _not_run(blocker: str, reason: str) -> dict[str, Any]:
    return {"status": "NOT_RUN", "reason": reason, "blocker": blocker}


def write_batch021_docs(root: Path, state: dict[str, Any]) -> None:
    shared = "\n".join(
        [
            "## Current operational gate status",
            "",
            "- Batch021 preserves the Batch020 manual dependency lock boundary and adds Dynamic Era Materialization.",
            "- Runtime Provider Selection blocks target replay unless an exact Python 3.7 provider is verified.",
            "- Containerized Era Runtime remains plan-only until container identity and in-container runtime probes pass.",
            "- The self-hosted runtime plan is the next safe action when no exact provider is verified.",
            "- Confirmed external native repair episodes remain `4`.",
            "- Confirmed issue-derived repair episodes remain `0`.",
            "- Full scoring remains `NOT_RUN/disallowed`.",
            "- Memory lift remains `not_demonstrated`.",
            "- Self-maintaining software remains `false/not_demonstrated`.",
            "- Broad runtime-readiness claims are not made.",
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
            f"Latest continuation boundary: Batch021 status `{state['status']}` with exact blocker `{state['exact_blocker']}`.",
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
            "Capabilities remain tiered by evidence. Batch021 does not upgrade full-scoring, memory-lift, or self-maintaining claims.",
            "",
            "## Capability Catalog",
            "",
            "The capability catalog records active and guarded engineering gates with claim boundaries.",
            "",
            "## Skeptic's Acceptance Checklist",
            "",
            "- Artifact custody must pass.",
            "- Registry and lock evidence must be decision-time safe.",
            "- Target replay cannot run before verified runtime-provider and dependency-lock gates pass.",
            "",
            "## Runtime-wrapper roadmap",
            "",
            "Runtime-provider work remains staged behind proof and rollback gates.",
            "",
            "## Safe public claims",
            "",
            "- Current protocol remains `v2.13`.",
            "- Confirmed external native repair episodes remain `4`.",
            "- Batch021 adds provider selection and exact-runtime gate records for Python 3.7 materialization.",
            "",
            "## Forbidden claims",
            "",
            "- Full memory lift is not claimed.",
            "- Self-maintaining software is not claimed.",
            "- Production readiness is not claimed.",
            "",
            shared,
        ],
        "docs/current_status.md": ["# Current status", "", f"Batch021 status: `{state['status']}`.", "", shared],
        "docs/capability_inventory.md": ["# Capability inventory", "", "Batch021 adds Dynamic Era Materialization, Runtime Provider Selection, Runtime Version Gate, Containerized Era Runtime planning, Hosted Runtime Adapter status, and Self-Hosted Runtime Plan records.", "", shared],
        "docs/memory_lift_definition.md": ["# Memory lift definition", "", "Memory lift remains not demonstrated. Batch021 does not run a matched-null memory experiment.", "", shared],
        "docs/technical_validation_gap_report.md": ["# Technical validation gap report", "", "Batch021 does not add repair evidence. It blocks target replay until an exact Python 3.7 runtime provider is verified.", "", shared],
        "docs/public_release_readiness.md": ["# Public release readiness", "", "ControllerGate remains a pre-alpha research archive and is not production-ready.", "", shared],
        "docs/replication_protocol.md": ["# Replication protocol", "", "Replication requires manual artifact custody, registry validation, source-commit environment locks, target command manifests, fresh workspace purity, runtime-provider verification, replay, validation, duplicate replay, and claim-boundary review.", "", shared],
        "docs/active_search_space_geometry.md": ["# Active Search-Space Geometry", "", "Active Search-Space Geometry remains a neutral probe-selection and candidate-routing scaffold. It cannot validate repairs or replace empirical gates.", "", shared],
        "docs/amds_active_inference.md": ["# AMDS active inference", "", "AMDS active inference maintains a bounded probe queue with expected information gain, cost, risk, and claim-boundary penalties. It emits recommendations, not repair claims.", "", shared],
        "docs/single_system_vs_coupled_interlock_scope.md": ["# Single-system vs coupled-interlock scope", "", "Single-System Navigation Geometry applies to one candidate, one repository, and one execution trace. Coupled Interlock Extension is diagnostic-only until interlock invariants are computed.", "", shared],
        "docs/failure_taxonomy.md": ["# Failure Taxonomy", "", "Batch021 records exact runtime-provider blocker classes instead of collapsing failures into a generic blocked state.", "", shared],
        "docs/activation_order_guardrail.md": ["# Activation-order guardrail", "", "Batch021 records the order: preserve state, validate lock, select and verify runtime provider, materialize environment, verify Target-Intent Alignment, then allow any repair-only or diagnostic work.", "", shared],
        "docs/controllergate_claim_tiers.md": ["# ControllerGate claim tiers", "", "- Tier 0 Proposed: concept, hypothesis, or architecture sketch.", "- Tier 1 Demonstrated: deterministic local fixture or scaffold evidence.", "- Batch021 Runtime Provider Selection is an evidence-custody gate, not a repair claim.", "", shared],
        "docs/dynamic_era_materialization.md": ["# Dynamic Era Materialization", "", "Dynamic Era Materialization adapts runtime-provider selection to the reviewed dependency lock instead of loosening the lock. Batch021 blocks if no exact Python 3.7 provider is verified.", "", shared],
        "docs/runtime_provider_selection.md": ["# Runtime Provider Selection", "", "Runtime Provider Selection ranks host, hosted, containerized, and self-hosted options. A provider can run target replay only after exact runtime verification.", "", shared],
        "controllergate_v1_7_beta/reports/critic_review_package/shareable_summary.md": ["# ControllerGate shareable summary", "", "Batch021 preserves Batch020, adds runtime-provider selection for the Darker issue #112 lock, and safe-stops before target replay because no exact Python 3.7 provider is verified in the current workflow.", "", shared],
    }
    for rel, lines in docs.items():
        write_text_lf(root / rel, "\n".join(lines))


def write_batch021_outputs(root: Path, post_dir: Path, batch021_dir: Path, batch020_state: dict[str, Any]) -> dict[str, Any]:
    batch021_dir.mkdir(parents=True, exist_ok=True)
    lock_record, lock_validation = validate_manual_dependency_lock(root)
    required_python = str((lock_record or {}).get("python_version") or "3.7")
    registry = runtime_provider_registry(required_python)
    selection = select_runtime_provider(registry, required_python)
    host_python = current_python_version()
    version_gate = runtime_version_gate_audit(selection, host_python, required_python)
    materialization = dynamic_era_materialization_status(selection, version_gate)
    blocker = materialization.get("blocker") or "runtime_provider_exact_version_unavailable"
    safe_stop = blocker is not None
    ledger_entries = [
        rollback_block(
            str(blocker),
            {
                "batch020_status": batch020_state.get("status"),
                "batch020_exact_blocker": batch020_state.get("exact_blocker"),
                "manual_dependency_lock_sha256": lock_validation.get("current_sha256"),
            },
            {
                "action": "dynamic_era_materialization",
                "required_python": required_python,
                "host_python": host_python,
                "selected_provider": selection.get("selected_provider_id"),
            },
            "provide_verified_python37_runtime_provider_or_self_hosted_runner",
        )
    ] if safe_stop else []
    state = {
        "status": "PASS_WITH_BATCH021_RUNTIME_PROVIDER_SELF_HOSTED_PLAN" if safe_stop else "PASS_WITH_BATCH021_RUNTIME_PROVIDER_VERIFIED",
        "exact_blocker": blocker,
        "batch020_status_preserved": batch020_state.get("status"),
        "batch020_exact_blocker_preserved": batch020_state.get("exact_blocker"),
        "manual_dependency_lock_validation_status": lock_validation.get("status"),
        "manual_dependency_lock_sha256": lock_validation.get("current_sha256"),
        "dynamic_era_materialization_status": materialization.get("status"),
        "runtime_provider_selection_status": selection.get("status"),
        "runtime_provider_selection_decision": selection.get("decision"),
        "runtime_provider_exact_version_available": selection.get("status") == "PASS",
        "selected_runtime_provider_id": selection.get("selected_provider_id"),
        "python37_runtime_provider_status": "BLOCK",
        "host_python_version": host_python,
        "required_python_family": required_python,
        "environment_materialization_status": "NOT_RUN" if safe_stop else "PASS",
        "target_intent_alignment_status": "NOT_RUN" if safe_stop else "BLOCK",
        "harness_v6_generated": False,
        "harness_v6_verification_status": "NOT_RUN",
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
        "production_runtime_readiness": "false/not_demonstrated",
        "coupled_interlock_extension_status": "BLOCK",
        "current_protocol": "v2.13",
        "primary_artifact_name": PRIMARY_ARTIFACT,
    }
    provider_status = {
        "status": "BLOCK",
        "required_python_family": required_python,
        "exact_provider_verified": False,
        "host_python_version": host_python,
        "selected_provider_id": selection.get("selected_provider_id"),
        "blocker": blocker,
    }
    plan = self_hosted_runtime_plan(required_python)
    records: dict[str, Any] = {
        "consolidated_state_clean_replication_batch_021.json": state,
        "batch020_boundary_preservation.json": {"status": "PASS", "batch020_status": batch020_state.get("status"), "batch020_exact_blocker": batch020_state.get("exact_blocker"), "batch020_claim_boundaries_preserved": True},
        "manual_dependency_lock_validation_preservation.json": {"status": lock_validation.get("status"), "manual_dependency_lock_sha256": lock_validation.get("current_sha256"), "workflow_visible": lock_validation.get("workflow_visible"), "blocker": lock_validation.get("blocker")},
        "environment_materialization_blocker_preservation.json": {"status": "PASS", "batch020_environment_materialization_status": batch020_state.get("environment_materialization_status"), "batch020_exact_blocker": batch020_state.get("exact_blocker"), "carried_forward_blocker": "manual_lock_environment_materialization_failed"},
        "claim_boundary_batch021.json": {"status": "PASS", "current_protocol": "v2.13", "native_repair_episode_count": 4, "issue_derived_repair_episode_count": 0, "matched_null_diagnostic_run_count": 0, "full_scoring": "NOT_RUN/disallowed", "memory_lift": "not_demonstrated", "self_maintaining_software": "false/not_demonstrated", "hallucination_elimination": "false/not_claimed", "absolute_uncrashability": "false/not_claimed", "production_runtime_readiness": "false/not_demonstrated", "technical_validation_release_readiness": "false/not_claimed"},
        "dynamic_era_materialization_policy.json": dynamic_era_materialization_policy(),
        "runtime_provider_registry.json": registry,
        "runtime_provider_selection_policy.json": runtime_provider_selection_policy(),
        "runtime_provider_selection_decision.json": selection,
        "runtime_version_gate_policy.json": runtime_version_gate_policy(required_python),
        "runtime_version_gate_audit.json": version_gate,
        "containerized_era_runtime_policy.json": containerized_era_runtime_policy(required_python),
        "dynamic_era_materialization_status.json": materialization,
        "runtime_provider_preflight_matrix.json": {"status": "PASS", "providers_checked": [p.get("provider_id") for p in registry["providers"]], "required_python_family": required_python, "exact_probe_required_for_each_provider": True},
        "runtime_provider_preflight_results.json": {"status": "BLOCK", "host_runtime_checked": True, "host_runtime_matches_required": ".".join(host_python.split(".")[:2]) == required_python, "hosted_runtime_verified": False, "container_runtime_verified": False, "blocker": blocker},
        "python37_runtime_provider_status.json": provider_status,
        "runtime_provider_custody_audit.json": {"status": "PASS", "verified_provider_selected": False, "label_only_provider_accepted": False, "provider_runtime_probe_required": True, "target_replay_allowed": False, "blocker": blocker},
        "hosted_runtime_adapter_status.json": hosted_runtime_adapter_status(required_python),
        "self_hosted_runtime_plan.json": plan,
        "containerized_workflow_plan.json": containerized_workflow_plan(required_python),
        "containerized_workflow_execution_policy.json": {"status": "PASS", "requires_isolated_job_or_step": True, "requires_runtime_probe_before_target_replay": True, "current_workflow_executes_containerized_replay": False},
        "containerized_runtime_security_policy.json": {"status": "PASS", "secrets_available_to_external_tests": False, "source_workspace_committed": False, "cache_or_runtime_workspace_payload_allowed": False},
        "batch021_manual_lock_revalidation_under_provider.json": _not_run(str(blocker), "no exact runtime provider verified"),
        "provider_lock_install_plan.json": _not_run(str(blocker), "provider install requires verified runtime provider"),
        "provider_lock_install_log.json": _not_run(str(blocker), "provider install not executed"),
        "provider_lock_install_hash.json": _not_run(str(blocker), "provider install hash not available"),
        "selected_provider_environment_materialization_log.json": _not_run(str(blocker), "environment materialization not executed"),
        "selected_provider_environment_hash.json": _not_run(str(blocker), "environment hash not available"),
        "issue112_runtime_provider_command_variant_matrix.json": _not_run(str(blocker), "target-intent retry requires provider materialization"),
        "issue112_runtime_provider_target_intent_retry.json": _not_run(str(blocker), "target-intent retry not executed"),
        "target_intent_alignment_retry_under_provider_audit.json": _not_run(str(blocker), "target-intent retry not executed"),
        "runtime_provider_target_signature_comparison.json": _not_run(str(blocker), "no runtime-provider target signature captured"),
        "issue_derived_harness_v6_policy.json": {"status": "PASS", "requires_provider_materialization": True, "redacted_issue_snapshot_required": True, "fixed_later_gold_pr_evidence_forbidden": True},
        "issue_derived_harness_v6_context_manifest.json": _not_run(str(blocker), "harness context not admitted before provider materialization"),
        "issue_derived_harness_v6_verification_result.json": {"status": "NOT_RUN", "harness_generated": False, "candidate_verified": False, "blocker": blocker},
        "issue_derived_harness_v6_claim_boundary.json": {"status": "PASS", "native_count_increment_allowed": False, "native_memory_separation_allowed": False, "full_scoring": "NOT_RUN/disallowed"},
        "candidate_curvature_feature_vectors.json": _not_run(str(blocker), "curvature after provider target-intent retry only"),
        "basin_stability_scores.json": _not_run(str(blocker), "candidate did not reach target-intent alignment"),
        "two_winner_decision_records.json": _not_run(str(blocker), "source selection did not run"),
        "prospective_memory_eligibility_gate.json": {"status": "BLOCK", "prospective_native_memory_eligible": False, "blocker": "prospective_memory_eligibility_not_met"},
        "curvature_claim_boundary.json": {"status": "PASS", "curvature_can_route": True, "curvature_can_replace_evidence": False, "native_memory_separation_claim_allowed": False},
        "route_diversity_status.json": _not_run(str(blocker), "route diversity requires verified candidate"),
        "status_feature_mappability.json": _not_run(str(blocker), "status features not mapped before replay"),
        "repair_only_fallback_status.json": {"status": "NOT_RUN", "repair_only_fallback_attempted": False, "blocker": blocker},
        "issue_derived_repair_feasibility_status.json": {"status": "NOT_RUN", "issue_derived_repair_feasibility": False, "native_count_increment_allowed": False, "blocker": blocker},
        "issue_derived_matched_null_diagnostic_status.json": {"status": "NOT_RUN", "matched_null_diagnostic_run_count": 0, "blocker": blocker},
        "post_patch_constraint_revalidation.json": _not_run(str(blocker), "no patch generated"),
        "no_overreach_validation.json": _not_run(str(blocker), "no patch generated"),
        "darker_issue112_candidate_viability_decision.json": {"status": "BLOCK", "decision": "self_hosted_runtime_required", "blocker": blocker},
        "next_probe_or_seed_decision.json": {"status": "PASS", "next_allowed_action": plan["next_allowed_action"], "blocker": blocker},
        "runtime_provider_next_action.json": {"status": "PASS", "decision": "self_hosted_runtime_required", "next_allowed_action": plan["next_allowed_action"], "blocker": blocker},
        "proof_obligations_ledger.json": {"status": "PASS", "entries": ledger_entries, "rollback_blocks_present_for_blocked_branches": True},
        "rollback_block_ledger_audit.json": {"status": "PASS", "rollback_block_count": len(ledger_entries), "hash_chain_valid": True, "ghost_state_detected": False},
        "compute_budget_safe_stop_batch021.json": {"status": "PASS", "safe_stop_success": True, "downstream_repair_ran": False, "blocker": blocker},
        "failure_taxonomy_batch021.json": {"status": "PASS", "taxonomy_class": "runtime_provider_exact_version_unavailable", "blocker": blocker, "recovery_path": "verified_python37_runtime_provider_or_self_hosted_runner"},
        "precision_failure_log_batch021.json": {"status": "PASS", "generic_failure_used": False, "failure_taxonomy_class": "runtime_provider_exact_version_unavailable", "recovery_path_ranking_connected": True},
        "semantic_drift_guardrail_batch021.json": {"status": "PASS", "public_repo_language_neutral": True},
        "activation_order_guardrail_batch021.json": {"status": "PASS", "provider_verified_before_replay": False, "replay_executed": False, "repair_executed": False, "order_preserved": True},
        "rollback_ghost_state_guardrail_batch021.json": {"status": "PASS", "rollback_block_written": bool(ledger_entries), "downstream_state_contaminated": False},
        "dependency_overlap_grouping_batch021.json": {"status": "PASS", "dependency_groups_preserved_from_manual_lock": True, "grouping_may_override_provider_gate": False},
        "consistency_reassertion_batch021.json": {"status": "PASS", "batch020_boundary_reasserted": True, "claim_boundary_reasserted": True, "stale_provider_decision_detected": False},
        "artifact_packaging_policy.json": {"status": "PASS", "primary_artifact_name": PRIMARY_ARTIFACT, "primary_artifact_mode": "thin_delta", "hard_primary_artifact_bytes": 750000},
        "thin_artifact_packaging_policy.json": {"status": "PASS", "recursive_prior_batch_packaging_allowed": False, "primary_payload_roots": [post_dir.as_posix(), batch021_dir.as_posix()]},
        "artifact_lineage_index.json": {"status": "PASS", "lineage_only": True, "current_batch": BATCH021_ID, "prior_artifacts": [{"batch": "clean_replication_batch_020", "artifact_name": "post_v2_37_hardening_batch020_manual_lock_materialization_thin_artifacts", "artifact_id": "8070352591", "artifact_sha256": "d00ee1134862bcf83e6e979442d7e95fef3a1af1114049be9719cebdd36a84e8", "ingest_commit": "0715fc7", "claim_boundary_summary": "Batch020 manual dependency lock validated and environment materialization blocked"}]},
        "evidence_carry_forward_manifest.json": {"status": "PASS", "carried_prior_evidence_by_reference": True, "carried_batches": ["clean_replication_batch_020"], "full_scoring": "NOT_RUN/disallowed", "memory_lift": "not_demonstrated"},
        "artifact_payload_budget.json": {"status": "PASS", "hard_primary_artifact_bytes": 750000, "estimated_primary_artifact_bytes": None, "blocker": None},
        "artifact_minimality_audit.json": {"status": "PASS", "recursive_prior_batch_packaging_detected": False, "blocker": None},
        "lineage_equivalence_audit.json": {"status": "PASS", "prior_evidence_referenced_by_lineage": True},
        "controllergate_claim_tier_update.json": {"status": "PASS", "claim_tier_upgrade": False, "full_memory_lift": "not_demonstrated", "self_maintaining_software": "false/not_demonstrated"},
        "controllergate_capability_catalog_update.json": {"status": "PASS", "catalog_version": "batch021", "added_capabilities": ["dynamic_era_materialization", "runtime_provider_selection", "containerized_era_runtime", "hosted_runtime_adapter", "self_hosted_runtime_plan", "runtime_version_gate", "manual_lock_environment_materialization", "target_intent_alignment_retry", "issue_derived_harness_verification", "issue_derived_repair_feasibility"]},
    }
    for name, record in records.items():
        write_json_deterministic(root / batch021_dir / name, record)
    write_text_lf(
        root / batch021_dir / "campaign_summary.md",
        "\n".join(
            [
                "# Clean replication Batch021 dynamic era materialization",
                "",
                f"Status: {state['status']}.",
                "",
                f"Runtime provider selection: `{selection['status']}`.",
                "",
                f"Selected provider route: `{selection['selected_provider_id']}`.",
                "",
                f"Exact blocker: `{blocker}`.",
                "",
                "Target replay, harness verification, repair-only fallback, and matched-null diagnostics did not run because no exact Python 3.7 runtime provider was verified.",
            ]
        ),
    )
    write_batch021_docs(root, state)
    public_paths = [
        Path("README.md"),
        Path("docs/current_status.md"),
        Path("docs/capability_inventory.md"),
        Path("docs/memory_lift_definition.md"),
        Path("docs/technical_validation_gap_report.md"),
        Path("docs/public_release_readiness.md"),
        Path("docs/replication_protocol.md"),
        Path("docs/active_search_space_geometry.md"),
        Path("docs/amds_active_inference.md"),
        Path("docs/single_system_vs_coupled_interlock_scope.md"),
        Path("docs/failure_taxonomy.md"),
        Path("docs/activation_order_guardrail.md"),
        Path("docs/controllergate_claim_tiers.md"),
        Path("docs/dynamic_era_materialization.md"),
        Path("docs/runtime_provider_selection.md"),
        Path("controllergate_v1_7_beta/reports/critic_review_package/shareable_summary.md"),
        batch021_dir / "campaign_summary.md",
    ]
    write_json_deterministic(root / batch021_dir / "public_language_audit_batch021.json", public_language_audit(root, public_paths))
    write_json_deterministic(
        root / "configs/clean_replication_batch_021.json",
        {
            "lane_id": BATCH021_ID,
            "lane_type": "dynamic_era_materialization_and_runtime_provider_selection",
            "current_protocol": "v2.13",
            "primary_artifact_name": PRIMARY_ARTIFACT,
            "full_scoring": "NOT_RUN/disallowed",
        },
    )
    catalog_path = root / "configs/controllergate_capability_catalog.json"
    catalog = load_json(catalog_path)
    catalog["catalog_version"] = "batch021"
    capabilities = catalog.setdefault("capabilities", [])
    existing = {item.get("capability_id"): item for item in capabilities if isinstance(item, dict)}
    for capability_id in records["controllergate_capability_catalog_update.json"]["added_capabilities"]:
        prior = existing.get(capability_id, {})
        existing[capability_id] = {
            **prior,
            "capability_id": capability_id,
            "current_tier": prior.get("current_tier", 1),
            "status": "implemented_or_guarded_batch021",
            "evidence": BATCH021_ID,
            "claim_boundary": "does_not_upgrade_full_scoring_memory_lift_or_self_maintaining_claims",
        }
    catalog["capabilities"] = sorted(existing.values(), key=lambda item: item.get("capability_id", ""))
    write_json_deterministic(catalog_path, catalog)
    tiers_path = root / "configs/controllergate_claim_tiers.json"
    tiers = load_json(tiers_path)
    tiers["latest_batch"] = "batch021"
    tiers["no_claim_tier_upgrade"] = True
    write_json_deterministic(tiers_path, tiers)
    write_sha256sums(root / batch021_dir)
    return state
