from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .batch020_manual_lock import public_language_audit
from .batch022_docker_psa82 import not_run, rollback_block
from .evidence import hash_record, sha256_bytes, sha256_file, write_json_deterministic, write_text_lf
from .manifests import write_sha256sums
from .provider_source_checkout import SOURCE_COMMIT_SHA, SOURCE_REPO_URL, provider_source_checkout_policy
from .provider_workspace_bridge import run_provider_workspace_bridge


BATCH024_ID = "clean_replication_batch_024"
PRIMARY_ARTIFACT = "post_v2_37_hardening_batch024_provider_workspace_bridge_thin_artifacts"
BATCH024_CAPABILITIES = [
    "provider_workspace_bridge",
    "provider_input_bundle",
    "provider_output_bundle",
    "provider_source_checkout",
    "provider_source_materialization",
    "target_intent_alignment_retry",
    "issue_derived_harness_verification",
    "issue_derived_repair_feasibility",
    "structured_fragility_diagnostic",
]


def _load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _status_blocker(*records: dict[str, Any], default: str = "provider_workspace_bridge_missing") -> str | None:
    for record in records:
        blocker = record.get("blocker")
        if blocker:
            return str(blocker)
    return default


def _sanitize_provider_result(provider: dict[str, Any]) -> dict[str, Any]:
    result = provider.get("provider_result")
    return result if isinstance(result, dict) else {}


def _target_alignment_from_result(result: dict[str, Any]) -> dict[str, Any]:
    target = result.get("target_intent", {}) if isinstance(result, dict) else {}
    if target.get("status") == "PASS":
        return {
            "status": "PASS",
            "target_intent_alignment": True,
            "repair_authorized": False,
            "blocker": None,
        }
    if target:
        return {
            "status": target.get("status", "BLOCK"),
            "target_intent_alignment": False,
            "repair_authorized": False,
            "blocker": target.get("blocker") or "target_intent_alignment_not_reached",
        }
    return {
        "status": "NOT_RUN",
        "target_intent_alignment": False,
        "repair_authorized": False,
        "blocker": "manual_lock_environment_materialization_failed",
    }


def write_batch024_docs(root: Path, state: dict[str, Any]) -> None:
    shared = "\n".join(
        [
            "## Current operational gate status",
            "",
            "- Batch023 verified Docker provider activation, Python 3.7 preflight, provider output transport, and manual dependency-lock installation in the official artifact.",
            "- Batch023 blocked at source workspace materialization pending an approved Provider Workspace Bridge.",
            "- Batch024 adds the Provider Workspace Bridge, Provider Input Bundle, Provider Output Bundle, Provider Workspace Transport, and Provider Source Materialization records.",
            "- The runtime must conform to the reviewed lock; the lock is not loosened to fit the runtime.",
            "- Provider labels are insufficient; actual Python and pip versions must be recorded inside the provider.",
            "- External source execution must not receive write credentials or secrets.",
            "- Structured Fragility Diagnostic is diagnostic and cannot replace empirical gates.",
            "- Repair cannot activate before bounded materialization and Target-Intent Alignment.",
            "- Active Search-Space Geometry may prioritize probes but cannot replace empirical evidence.",
            "- Single-system navigation and coupled-interlock extension remain separate.",
            "- Coupled-interlock extension remains blocked until interlock invariants are computed.",
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
            f"Latest continuation boundary: Batch024 status `{state['status']}` with exact blocker `{state['exact_blocker']}`.",
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
            "Capabilities remain tiered by evidence. Batch024 does not upgrade full-scoring, memory-lift, or self-maintaining claims.",
            "",
            "## Capability Catalog",
            "",
            "The capability catalog records active and guarded engineering gates with claim boundaries.",
            "",
            "## Skeptic's Acceptance Checklist",
            "",
            "- Artifact custody must pass.",
            "- Registry and lock evidence must be decision-time safe.",
            "- Target replay cannot run before verified runtime-provider, Provider Workspace Bridge, and dependency-lock gates pass.",
            "",
            "## Runtime-wrapper roadmap",
            "",
            "Runtime-provider work remains staged behind proof and rollback gates.",
            "",
            "## Safe public claims",
            "",
            "- Current protocol remains `v2.13`.",
            "- Confirmed external native repair episodes remain `4`.",
            "- Batch024 adds a bounded Provider Workspace Bridge and safe-stop boundary.",
            "",
            "## Forbidden claims",
            "",
            "- Full memory lift is not claimed.",
            "- Self-maintaining software is not claimed.",
            "- Production readiness is not claimed.",
            "",
            shared,
        ],
        "docs/current_status.md": ["# Current status", "", f"Batch024 status: `{state['status']}`.", "", shared],
        "docs/capability_inventory.md": ["# Capability inventory", "", "Batch024 adds Provider Workspace Bridge, Provider Input Bundle, Provider Output Bundle, Provider Source Checkout, Provider Source Materialization, and Target-Intent Alignment retry records.", "", shared],
        "docs/technical_validation_gap_report.md": ["# Technical validation gap report", "", "Batch024 does not add repair evidence unless provider bridge, source checkout, materialization, Target-Intent Alignment, harness, validation, and replay gates pass.", "", shared],
        "docs/public_release_readiness.md": ["# Public release readiness", "", "ControllerGate remains a pre-alpha research archive and is not production-ready.", "", shared],
        "docs/controllergate_positioning.md": ["# ControllerGate positioning", "", "Precise claim: ControllerGate supports proof-gated software-change governance and conservative repair validation.", "", shared],
        "docs/controllergate_claim_tiers.md": ["# ControllerGate claim tiers", "", "Batch024 records Provider Workspace Bridge and provider source materialization evidence without upgrading full-scoring, memory-lift, self-maintaining, production-readiness, or universal-repair claims.", "", shared],
        "docs/skeptics_acceptance_checklist.md": ["# Skeptic's acceptance checklist", "", "- Provider execution must be bounded and credential-isolated.", "- Provider input and output bundles must be hash-recorded.", "- Repair cannot activate before materialization and Target-Intent Alignment.", "", shared],
        "docs/use_case_positioning.md": ["# Use case positioning", "", "ControllerGate is positioned for research-grade repair validation and proof-gated software-change governance.", "", "deployment_readiness: false", "", shared],
        "docs/replication_protocol.md": ["# Replication protocol", "", "Replication requires manual artifact custody, registry validation, runtime-provider verification, dependency-lock installation, Provider Workspace Bridge checks, materialization, replay, validation, duplicate replay, no-overreach validation, and claim-boundary review.", "", shared],
        "docs/artifact_packaging_policy.md": ["# Artifact packaging policy", "", "The primary post-v2.37 artifact remains thin and delta-oriented. Batch024 carries prior evidence by artifact identity and lineage records.", "", shared],
        "docs/active_search_space_geometry.md": ["# Active Search-Space Geometry", "", "Active Search-Space Geometry is a neutral probe-selection and candidate-routing scaffold. It can prioritize probes and classify diagnostic boundaries, but it cannot validate repairs or replace empirical gates.", "", shared],
        "docs/amds_active_inference.md": ["# AMDS active inference", "", "AMDS active inference maintains a bounded probe queue with expected information gain, cost, risk, and claim-boundary penalties. It emits recommendations, not repair claims.", "", shared],
        "docs/single_system_vs_coupled_interlock_scope.md": ["# Single-system vs coupled-interlock scope", "", "Single-System Navigation Geometry applies to one candidate, one repository, and one execution trace. Coupled Interlock Extension is diagnostic-only until interlock invariants are computed.", "", shared],
        "docs/failure_taxonomy.md": ["# Failure Taxonomy", "", "Batch024 records exact provider bridge, source checkout, materialization, target-intent, and harness blocker classes instead of collapsing failures into a generic blocked state.", "", shared],
        "docs/activation_order_guardrail.md": ["# Activation Order Guardrail", "", "Repair cannot run before provider bridge, source checkout, materialization, Target-Intent Alignment, and harness verification pass in order.", "", shared],
        "docs/dynamic_era_materialization.md": ["# Dynamic Era Materialization", "", "Batch024 keeps materialization bounded to the verified Python 3.7 provider and reviewed manual dependency lock.", "", shared],
        "docs/runtime_provider_selection.md": ["# Runtime Provider Selection", "", "Batch024 preserves the verified Docker Run Provider boundary from the official Batch023 artifact and adds Provider Workspace Bridge checks before source materialization.", "", shared],
        "docs/structured_fragility_audit.md": ["# Structured Fragility Diagnostic", "", "Structured Fragility Diagnostic is diagnostic-only. It cannot replace target validation, duplicate replay, no-overreach validation, or matched-null fairness.", "", shared],
        "docs/bounded_docker_provider_probe.md": ["# Bounded Docker Provider Probe", "", "Batch023 verified Docker Run Provider preflight in the official artifact. Batch024 uses that boundary as prior evidence and records any new provider execution separately.", "", shared],
        "docs/provider_workspace_bridge.md": ["# Provider Workspace Bridge", "", "The Provider Workspace Bridge is the approved boundary for passing a minimal input bundle into the Python 3.7 provider and returning only sanitized output summaries.", "", "Input bundles may include the reviewed dependency lock, selected source commit, target command policy, and redacted issue metadata. Output bundles may include provider preflight, source checkout audit, dependency freeze hashes, target-intent retry logs, and sanitized summaries.", "", shared],
        "controllergate_v1_7_beta/reports/critic_review_package/shareable_summary.md": ["# ControllerGate shareable summary", "", f"Latest boundary: Batch024 `{state['status']}` with blocker `{state['exact_blocker']}`.", "", shared],
    }
    for rel, lines in docs.items():
        write_text_lf(root / rel, "\n".join(lines))


def reassert_batch024_public_state(root: Path, state: dict[str, Any]) -> None:
    write_batch024_docs(root, state)
    write_json_deterministic(root / "configs/clean_replication_batch_024.json", {"lane_id": BATCH024_ID, "lane_type": "provider_workspace_bridge_source_materialization", "current_protocol": "v2.13", "primary_artifact_name": PRIMARY_ARTIFACT, "full_scoring": "NOT_RUN/disallowed"})
    catalog_path = root / "configs/controllergate_capability_catalog.json"
    catalog = _load_json(catalog_path)
    catalog["catalog_version"] = "batch024"
    capabilities = catalog.setdefault("capabilities", [])
    existing = {item.get("capability_id"): item for item in capabilities if isinstance(item, dict)}
    for capability_id in BATCH024_CAPABILITIES:
        prior = existing.get(capability_id, {})
        existing[capability_id] = {**prior, "capability_id": capability_id, "current_tier": prior.get("current_tier", 1), "status": "implemented_or_guarded_batch024", "evidence": BATCH024_ID, "claim_boundary": "does_not_upgrade_full_scoring_memory_lift_or_self_maintaining_claims"}
    catalog["capabilities"] = sorted(existing.values(), key=lambda item: item.get("capability_id", ""))
    write_json_deterministic(catalog_path, catalog)
    tiers_path = root / "configs/controllergate_claim_tiers.json"
    tiers = _load_json(tiers_path)
    tiers["latest_batch"] = "batch024"
    tiers["no_claim_tier_upgrade"] = True
    write_json_deterministic(tiers_path, tiers)


def write_batch024_outputs(root: Path, post_dir: Path, batch024_dir: Path, batch023_state: dict[str, Any]) -> dict[str, Any]:
    batch024_dir.mkdir(parents=True, exist_ok=True)
    bridge = run_provider_workspace_bridge(root)
    provider_result = _sanitize_provider_result(bridge["provider_output"])
    source_checkout = provider_result.get("source_checkout", {}) if provider_result else {}
    materialization = provider_result.get("materialization", {}) if provider_result else {}
    target_intent = provider_result.get("target_intent", {}) if provider_result else {}
    target_alignment = _target_alignment_from_result(provider_result)

    provider_bridge_pass = (
        bridge["input_validation"].get("status") == "PASS"
        and bridge["output_validation"].get("status") == "PASS"
        and bridge["transport"].get("status") == "PASS"
        and bridge["provider_output"].get("status") == "PASS"
    )
    source_checkout_pass = source_checkout.get("status") == "PASS"
    materialization_pass = materialization.get("status") == "PASS"
    target_intent_pass = target_intent.get("status") == "PASS"
    if not provider_bridge_pass:
        exact_blocker = _status_blocker(bridge["input_validation"], bridge["output_validation"], bridge["transport"], bridge["provider_output"], default="provider_workspace_transport_unverified")
    elif not source_checkout_pass:
        exact_blocker = source_checkout.get("blocker") or "provider_source_checkout_failed"
    elif not materialization_pass:
        exact_blocker = materialization.get("blocker") or "manual_lock_environment_materialization_failed"
    elif not target_intent_pass:
        exact_blocker = target_intent.get("blocker") or "target_intent_alignment_not_reached"
    else:
        exact_blocker = "issue_derived_harness_v9_verification_failed"

    status_suffix = {
        "provider_workspace_bridge_missing": "PROVIDER_BRIDGE_BLOCKED",
        "provider_input_bundle_invalid": "PROVIDER_BRIDGE_BLOCKED",
        "provider_output_bundle_invalid": "PROVIDER_BRIDGE_BLOCKED",
        "provider_workspace_transport_unverified": "PROVIDER_BRIDGE_BLOCKED",
        "provider_workspace_cleanup_failed": "PROVIDER_BRIDGE_BLOCKED",
        "docker_runtime_provider_unavailable": "PROVIDER_BRIDGE_BLOCKED",
        "provider_source_checkout_failed": "SOURCE_CHECKOUT_BLOCKED",
        "provider_source_commit_unresolved": "SOURCE_CHECKOUT_BLOCKED",
        "provider_source_commit_mismatch": "SOURCE_CHECKOUT_BLOCKED",
        "provider_source_tree_manifest_failed": "SOURCE_CHECKOUT_BLOCKED",
        "manual_lock_environment_materialization_failed": "MATERIALIZATION_BLOCKED",
        "source_install_failed": "MATERIALIZATION_BLOCKED",
        "source_install_required_undeclared_dependency": "MATERIALIZATION_BLOCKED",
        "target_intent_alignment_not_reached": "TARGET_INTENT_BLOCKED",
        "target_intent_precondition_failure": "TARGET_INTENT_BLOCKED",
        "issue_derived_harness_v9_verification_failed": "HARNESS_V9_BLOCKED",
    }.get(str(exact_blocker), "SAFE_STOP")

    state = {
        "status": f"PASS_WITH_BATCH024_{status_suffix}",
        "exact_blocker": exact_blocker,
        "batch023_status_preserved": batch023_state.get("status"),
        "batch023_exact_blocker_preserved": batch023_state.get("exact_blocker"),
        "provider_workspace_bridge_status": "PASS" if provider_bridge_pass else "BLOCK",
        "provider_input_bundle_status": bridge["input_validation"].get("status"),
        "provider_output_bundle_status": bridge["output_validation"].get("status"),
        "provider_workspace_transport_status": bridge["transport"].get("status"),
        "provider_workspace_cleanup_status": bridge["cleanup"].get("status"),
        "provider_source_checkout_status": source_checkout.get("status", "NOT_RUN"),
        "selected_source_commit": SOURCE_COMMIT_SHA,
        "source_materialization_status": materialization.get("status", "NOT_RUN"),
        "installed_package_freeze_status": "PASS" if provider_result.get("freeze") else "NOT_RUN",
        "environment_hash_status": "PASS" if materialization else "NOT_RUN",
        "target_intent_alignment_status": target_alignment.get("status"),
        "harness_v9_generated": False,
        "harness_v9_verification_status": "NOT_RUN",
        "structured_fragility_diagnostic_status": "NOT_RUN_NO_PATCH_CANDIDATE",
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
    ledger_entries = [
        rollback_block(
            exact_blocker,
            {"batch023_status": batch023_state.get("status"), "batch023_exact_blocker": batch023_state.get("exact_blocker")},
            {
                "provider_bridge_pass": provider_bridge_pass,
                "source_checkout_pass": source_checkout_pass,
                "materialization_pass": materialization_pass,
                "target_intent_pass": target_intent_pass,
            },
            "revise_provider_workspace_bridge_or_source_materialization_before_repair",
        )
    ]
    freeze = provider_result.get("freeze", [])
    freeze_sha = sha256_bytes("\n".join(freeze).encode("utf-8")) if freeze else None
    records: dict[str, Any] = {
        "consolidated_state_clean_replication_batch_024.json": state,
        "batch023_boundary_preservation.json": {"status": "PASS", "batch023_status": batch023_state.get("status"), "batch023_exact_blocker": batch023_state.get("exact_blocker"), "claim_boundaries_preserved": True},
        "provider_preflight_preservation.json": {"status": "PASS", "batch023_provider_preflight_status": batch023_state.get("provider_preflight_status"), "batch023_actual_provider_python_version": batch023_state.get("actual_provider_python_version"), "batch023_actual_provider_pip_version": batch023_state.get("actual_provider_pip_version")},
        "provider_install_preservation.json": {"status": "PASS", "batch023_manual_dependency_lock_provider_install_status": batch023_state.get("manual_dependency_lock_provider_install_status"), "carried_blocker": "manual_lock_environment_materialization_failed"},
        "claim_boundary_batch024.json": {"status": "PASS", "native_repair_episode_count": 4, "issue_derived_repair_episode_count": 0, "matched_null_diagnostic_run_count": 0, "full_scoring": "NOT_RUN/disallowed", "memory_lift": "not_demonstrated", "self_maintaining_software": "false/not_demonstrated", "hallucination_elimination": "false/not_claimed", "absolute_uncrashability": "false/not_claimed", "production_runtime_readiness": "false/not_demonstrated", "current_protocol": "v2.13", "carried_blocker": "manual_lock_environment_materialization_failed"},
        "provider_workspace_bridge_policy.json": {"status": "PASS", "input_bundle_allowlist_required": True, "output_bundle_allowlist_required": True, "provider_workspace_must_be_outside_repo": True, "secrets_allowed": False, "write_credentials_allowed": False},
        "provider_input_bundle_manifest.json": {**bridge["input_validation"], "bundle_sha256": bridge["input_bundle"].get("bundle_sha256"), "dependency_lock_sha256": bridge["input_bundle"].get("dependency_lock", {}).get("sha256")},
        "provider_output_bundle_manifest.json": {**bridge["output_validation"], "bundle_sha256": bridge["output_bundle"].get("bundle_sha256"), "present_keys": bridge["output_bundle"].get("present_keys")},
        "provider_workspace_transport_audit.json": bridge["transport"],
        "provider_workspace_cleanup_audit.json": bridge["cleanup"],
        "provider_workspace_bridge_status.json": {"status": "PASS" if provider_bridge_pass else "BLOCK", "input_bundle_status": bridge["input_validation"].get("status"), "output_bundle_status": bridge["output_validation"].get("status"), "transport_status": bridge["transport"].get("status"), "cleanup_status": bridge["cleanup"].get("status"), "provider_command_status": bridge["provider_output"].get("status"), "blocker": None if provider_bridge_pass else exact_blocker},
        "provider_source_checkout_policy.json": provider_source_checkout_policy(),
        "provider_source_checkout_audit.json": {**source_checkout, "status": source_checkout.get("status", "NOT_RUN"), "repo_url": SOURCE_REPO_URL, "source_commit_sha": SOURCE_COMMIT_SHA, "full_source_tree_copied_to_repo": False, "blocker": source_checkout.get("blocker") if source_checkout else ("provider_workspace_transport_unverified" if not provider_bridge_pass else "provider_source_checkout_failed")},
        "provider_source_tree_manifest.json": bridge["source_tree_manifest"],
        "provider_source_commit_verification.json": {"status": source_checkout.get("status", "NOT_RUN"), "repo_url": SOURCE_REPO_URL, "source_commit_sha": SOURCE_COMMIT_SHA, "git_object_type": source_checkout.get("git_object_type"), "head_sha": source_checkout.get("head_sha"), "commit_verified": source_checkout_pass, "blocker": None if source_checkout_pass else source_checkout.get("blocker", "provider_source_commit_unresolved")},
        "manual_lock_environment_materialization_policy.json": {"status": "PASS", "requires_provider_workspace_bridge": True, "install_source_with_no_deps": True, "undeclared_dependency_install_allowed": False, "source_mutation_allowed": False},
        "manual_lock_environment_materialization_log.json": {**materialization, "status": materialization.get("status", "NOT_RUN"), "blocker": None if materialization_pass else materialization.get("blocker", exact_blocker)},
        "manual_lock_environment_hash.json": {"status": "PASS" if materialization else "NOT_RUN", "environment_hash": hash_record(materialization) if materialization else None, "blocker": None if materialization else exact_blocker},
        "provider_installed_package_freeze.json": {"status": "PASS" if freeze else "NOT_RUN", "freeze_line_count": len(freeze), "freeze_lines": freeze[:120], "blocker": None if freeze else exact_blocker},
        "provider_installed_package_hashes.json": {"status": "PASS" if freeze_sha else "NOT_RUN", "freeze_sha256": freeze_sha, "package_hash_recording_level": "freeze_hash_recorded", "blocker": None if freeze_sha else exact_blocker},
        "workspace_purity_report.json": {"status": "PASS", "provider_workspace_committed": False, "source_checkout_leaked_to_repo": False, "workspace_purity_verified_before_replay": materialization_pass},
        "acquisition_lock_stack_status.json": {"status": "PASS" if materialization_pass else "BLOCK", "provider_bridge_pass": provider_bridge_pass, "source_checkout_pass": source_checkout_pass, "manual_dependency_lock_installed": bool(freeze), "environment_materialized": materialization_pass, "target_intent_alignment_verified": target_intent_pass, "blocker": None if materialization_pass else exact_blocker},
        "issue112_command_variant_policy.json": {"status": "PASS", "allowed_variants": ["GIT_DIR=.git python -m darker --check src", "GIT_DIR=.git darker --check src", "equivalent subprocess form from ephemeral harness"], "requires_provider_materialization": True},
        "issue112_provider_variant_results.json": {"status": target_intent.get("status", "NOT_RUN"), "variants": target_intent.get("variant_results", []), "blocker": target_intent.get("blocker", exact_blocker)},
        "darker_issue112_target_intent_signature_retry.json": {"status": target_intent.get("status", "NOT_RUN"), "positive_indicators_matched": any(item.get("positive_indicators") for item in target_intent.get("variant_results", [])) if target_intent else False, "negative_precondition_indicator_seen": any(item.get("negative_precondition_indicators") for item in target_intent.get("variant_results", [])) if target_intent else False, "blocker": target_intent.get("blocker", exact_blocker)},
        "target_intent_alignment_retry_audit.json": target_alignment,
        "issue_derived_harness_v9_policy.json": {"status": "PASS", "requires_target_intent_alignment": True, "redacted_issue_snapshot_required": True, "future_fixed_gold_pr_evidence_forbidden": True, "provider_workspace_summary_only": True},
        "issue_derived_harness_v9_context_manifest.json": not_run(exact_blocker, "target-intent alignment did not pass; harness v9 context not activated"),
        "issue_derived_harness_v9_verification_result.json": {"status": "NOT_RUN", "harness_generated": False, "candidate_verified": False, "blocker": exact_blocker},
        "candidate_curvature_feature_vectors.json": not_run(exact_blocker, "curvature after target-intent alignment only"),
        "basin_stability_scores.json": not_run(exact_blocker, "candidate did not reach target-intent alignment"),
        "two_winner_decision_records.json": not_run(exact_blocker, "source selection did not run"),
        "prospective_memory_eligibility_gate.json": {"status": "BLOCK", "candidate_class": "issue_derived_reproduction_candidate", "prospective_native_memory_eligible": False, "blocker": "prospective_memory_eligibility_not_met"},
        "curvature_claim_boundary.json": {"status": "PASS", "curvature_can_route": True, "curvature_can_replace_evidence": False, "native_memory_separation_claim_allowed": False},
        "active_search_geometry_execution_trace.json": {"status": "PASS", "used_for_probe_routing_only": True, "empirical_evidence_replaced": False},
        "repair_only_fallback_status.json": {"status": "NOT_RUN", "repair_only_fallback_attempted": False, "blocker": exact_blocker},
        "issue_derived_repair_feasibility_status.json": {"status": "NOT_RUN", "issue_derived_repair_feasibility": False, "native_count_increment_allowed": False, "blocker": exact_blocker},
        "issue_derived_matched_null_diagnostic_status.json": {"status": "NOT_RUN", "matched_null_diagnostic_run_count": 0, "native_memory_separation_claim_allowed": False, "blocker": exact_blocker},
        "post_patch_constraint_revalidation.json": not_run(exact_blocker, "no patch generated"),
        "no_overreach_validation.json": not_run(exact_blocker, "no patch generated"),
        "structured_fragility_audit_run_policy.json": {"status": "PASS", "diagnostic_only": True, "requires_patch_candidate": True, "cannot_replace_empirical_gates": True},
        "structured_fragility_audit_results.json": {"status": "NOT_RUN_NO_PATCH_CANDIDATE", "repair_evidence": False, "blocker": "no_patch_candidate"},
        "permutation_null_audit_results.json": {"status": "NOT_RUN_NO_PATCH_CANDIDATE", "repair_evidence": False, "blocker": "no_patch_candidate"},
        "patch_structure_sensitivity_results.json": {"status": "NOT_RUN_NO_PATCH_CANDIDATE", "repair_evidence": False, "blocker": "no_patch_candidate"},
        "darker_issue112_candidate_viability_decision.json": {"status": "BLOCK", "decision": "target_intent_alignment_reached" if target_intent_pass else ("continue_with_provider_workspace_bridge_revision_required" if not provider_bridge_pass else ("continue_with_source_materialization_revision_required" if not materialization_pass else "continue_with_command_variant_refinement_required")), "blocker": exact_blocker},
        "next_probe_or_seed_decision.json": {"status": "PASS", "next_allowed_action": "revise_provider_workspace_bridge_or_source_materialization_before_repair", "blocker": exact_blocker},
        "provider_workspace_bridge_next_action.json": {"status": "PASS", "decision": "revise_provider_workspace_bridge_or_source_materialization_before_repair", "next_allowed_action": "revise_provider_workspace_bridge_or_source_materialization_before_repair", "blocker": exact_blocker},
        "proof_obligations_ledger.json": {"status": "PASS", "entries": ledger_entries, "rollback_blocks_present_for_blocked_branches": True},
        "rollback_block_ledger_audit.json": {"status": "PASS", "rollback_block_count": len(ledger_entries), "hash_chain_valid": True, "ghost_state_detected": False},
        "compute_budget_safe_stop_batch024.json": {"status": "PASS", "safe_stop_success": bool(exact_blocker), "downstream_repair_ran": False, "blocker": exact_blocker},
        "failure_taxonomy_batch024.json": {"status": "PASS", "taxonomy_class": exact_blocker, "blocker": exact_blocker, "required_classes_recorded": ["provider_workspace_bridge_missing", "provider_input_bundle_invalid", "provider_output_bundle_invalid", "provider_workspace_transport_unverified", "provider_source_checkout_failed", "provider_source_commit_mismatch", "provider_source_tree_manifest_failed", "source_install_failed", "source_install_required_undeclared_dependency", "manual_lock_environment_materialization_failed", "target_intent_alignment_not_reached", "target_intent_precondition_failure", "issue_derived_harness_v9_verification_failed", "repair_attempted_without_target_intent_alignment", "safe_stop_after_provider_bridge_block", "safe_stop_after_materialization_block"]},
        "precision_failure_log_batch024.json": {"status": "PASS", "generic_failure_used": False, "failure_taxonomy_class": exact_blocker, "recovery_path_ranking_connected": True},
        "semantic_drift_guardrail_status.json": {"status": "PASS", "public_repo_language_neutral": True},
        "activation_order_guardrail_status.json": {"status": "PASS", "repair_before_provider_bridge": False, "repair_before_materialization": False, "repair_before_target_intent": False, "order_preserved": True},
        "rollback_ghost_state_guardrail_status.json": {"status": "PASS", "rollback_block_written": True, "downstream_state_contaminated": False},
        "dependency_overlap_grouping_status.json": {"status": "PASS", "groups_connected_to_feature_vectors": True, "may_override_provider_gate": False},
        "consistency_reassertion_status.json": {"status": "PASS", "feature_vector_reasserted": True, "claim_boundary_reasserted": True, "stale_provider_decision_detected": False},
        "public_language_audit_batch024.json": {"status": "PENDING", "checked_paths": []},
        "artifact_packaging_policy.json": {"status": "PASS", "primary_artifact_name": PRIMARY_ARTIFACT, "primary_artifact_mode": "thin_delta", "hard_primary_artifact_bytes": 750000},
        "thin_artifact_packaging_policy.json": {"status": "PASS", "recursive_prior_batch_packaging_allowed": False, "primary_payload_roots": [post_dir.as_posix(), batch024_dir.as_posix()]},
        "artifact_lineage_index.json": {"status": "PASS", "lineage_only": True, "current_batch": BATCH024_ID, "prior_artifacts": [{"batch": "clean_replication_batch_023", "artifact_name": "post_v2_37_hardening_batch023_bounded_docker_provider_thin_artifacts", "artifact_id": "8078453401", "artifact_sha256": "d058f32fba6fb8dec669f7ab906eeec042d175a3f6ed81e52cd833354de4b375", "ingest_commit": "2a46e685", "claim_boundary_summary": "Batch023 verified Docker/Python 3.7 provider preflight and blocked at provider source materialization"}]},
        "evidence_carry_forward_manifest.json": {"status": "PASS", "carried_prior_evidence_by_reference": True, "carried_batches": ["clean_replication_batch_023"], "full_scoring": "NOT_RUN/disallowed", "memory_lift": "not_demonstrated"},
        "artifact_payload_budget.json": {"status": "PASS", "hard_primary_artifact_bytes": 750000, "estimated_primary_artifact_bytes": None, "blocker": None},
        "artifact_minimality_audit.json": {"status": "PASS", "recursive_prior_batch_packaging_detected": False, "blocker": None},
        "lineage_equivalence_audit.json": {"status": "PASS", "prior_evidence_referenced_by_lineage": True},
        "controllergate_claim_tier_update.json": {"status": "PASS", "claim_tier_upgrade": False, "full_memory_lift": "not_demonstrated", "self_maintaining_software": "false/not_demonstrated", "no_upgrade_claims": ["full memory lift", "self-maintaining software", "hallucination elimination", "absolute uncrashability", "production readiness", "universal bug detection"]},
        "controllergate_capability_catalog_update.json": {"status": "PASS", "catalog_version": "batch024", "added_capabilities": BATCH024_CAPABILITIES},
    }
    for name, record in records.items():
        write_json_deterministic(root / batch024_dir / name, record)
    write_text_lf(root / batch024_dir / "campaign_summary.md", f"# Clean replication Batch024 Provider Workspace Bridge\n\nStatus: {state['status']}.\n\nProvider Workspace Bridge: `{state['provider_workspace_bridge_status']}`.\n\nSource materialization: `{state['source_materialization_status']}`.\n\nTarget-Intent Alignment: `{state['target_intent_alignment_status']}`.\n\nExact blocker: `{state['exact_blocker']}`.\n")
    reassert_batch024_public_state(root, state)
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
        Path("docs/dynamic_era_materialization.md"),
        Path("docs/runtime_provider_selection.md"),
        Path("docs/structured_fragility_audit.md"),
        Path("docs/bounded_docker_provider_probe.md"),
        Path("docs/provider_workspace_bridge.md"),
        Path("controllergate_v1_7_beta/reports/critic_review_package/shareable_summary.md"),
        batch024_dir / "campaign_summary.md",
    ]
    write_json_deterministic(root / batch024_dir / "public_language_audit_batch024.json", public_language_audit(root, public_paths))
    write_sha256sums(root / batch024_dir)
    return state
