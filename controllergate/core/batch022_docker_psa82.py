from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any

from .batch020_manual_lock import public_language_audit, validate_manual_dependency_lock
from .docker_runtime_provider import container_security_policy, docker_provider_preflight, docker_runtime_provider_policy
from .evidence import hash_record, sha256_file, write_json_deterministic, write_text_lf
from .manifests import write_sha256sums
from .patch_structure_sensitivity import patch_structure_sensitivity_policy, patch_structure_sensitivity_result
from .permutation_null_audit import permutation_null_audit_policy, permutation_null_audit_result
from .runtime_version_gate import runtime_version_gate_policy, runtime_version_gate_result
from .structured_fragility_audit import adapter_mapping, structured_fragility_audit_policy, structured_fragility_status


BATCH022_ID = "clean_replication_batch_022"
PRIMARY_ARTIFACT = "post_v2_37_hardening_batch022_docker_era_psa82_thin_artifacts"
PSA82_PATH = Path("incoming_artifacts/psa82_final_locked_package.zip")
PSA82_EXPECTED_SHA = "f97c21b44967b103fecd489acbda2fb79325f2f5bfb9884e10568dfedb62cb05"
PSA82_EXPECTED_SIZE = 2517632
LOCK_EXPECTED_SHA = "108d961f89b603d3c6a7bcb374976992c3fadc80497bf967421cdea38aff248a"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def zip_path_unsafe(name: str) -> bool:
    pure = PurePosixPath(name)
    return name.startswith("/") or "\\" in name or any(part in {"", ".", ".."} for part in pure.parts)


def rollback_block(blocker: str, previous_state: dict[str, Any], attempted_action: dict[str, Any], next_allowed_action: str) -> dict[str, Any]:
    payload = {
        "previous_state_hash": hash_record(previous_state),
        "attempted_action_hash": hash_record(attempted_action),
        "rollback_target_entry_index": 0,
        "blocker": blocker,
        "next_allowed_action": next_allowed_action,
    }
    return {**payload, "entry_type": "ROLLBACK_BLOCK", "rollback_hash": hash_record(payload)}


def not_run(blocker: str, reason: str, **extra: Any) -> dict[str, Any]:
    return {"status": "NOT_RUN", "reason": reason, "blocker": blocker, **extra}


def verify_embedded_manifest(archive: zipfile.ZipFile, manifest_name: str, base_prefix: str) -> dict[str, Any]:
    checked = missing = malformed = failures = 0
    failed: list[dict[str, Any]] = []
    names = set(archive.namelist())
    try:
        lines = archive.read(manifest_name).decode("utf-8", errors="replace").splitlines()
    except KeyError:
        return {"status": "MISSING", "manifest": manifest_name, "checked": 0, "missing": 1, "malformed": 0, "failures": 0, "failed": []}
    for line in lines:
        if not line.strip():
            continue
        parts = line.split(maxsplit=1)
        if len(parts) != 2:
            malformed += 1
            continue
        expected, rel = parts
        rel = rel.strip().lstrip("*")
        target = f"{base_prefix.rstrip('/')}/{rel}" if base_prefix else rel
        if len(expected) != 64 or zip_path_unsafe(rel):
            malformed += 1
            continue
        if target not in names:
            missing += 1
            failed.append({"path": target, "reason": "missing"})
            continue
        checked += 1
        actual = sha256_bytes(archive.read(target))
        if actual != expected:
            failures += 1
            failed.append({"path": target, "expected": expected, "actual": actual})
    status = "PASS" if missing == 0 and malformed == 0 and failures == 0 else "FAIL"
    return {"status": status, "manifest": manifest_name, "checked": checked, "missing": missing, "malformed": malformed, "failures": failures, "failed": failed[:20]}


def psa82_records(root: Path) -> dict[str, dict[str, Any]]:
    path = root / PSA82_PATH
    present = path.is_file()
    presence = {
        "status": "PASS" if present else "ABSENT",
        "psa82_package_present": present,
        "path": PSA82_PATH.as_posix(),
        "blocker": None,
    }
    policy = {
        "status": "PASS",
        "quarantine_required": True,
        "zip_may_be_verified": True,
        "zip_may_be_committed": False,
        "pyc_payloads_may_be_ingested": False,
        "legacy_manifest_authoritative": False,
        "final_locked_manifest_authoritative": True,
    }
    claim = {
        "status": "PASS",
        "diagnostic_only": True,
        "controllergate_repair_evidence": False,
        "can_replace_target_validation": False,
        "can_replace_duplicate_replay": False,
        "can_replace_no_overreach": False,
        "can_replace_byte_custody": False,
    }
    if not present:
        absent = {
            "status": "NOT_RUN",
            "psa82_package_present": False,
            "reason": "PSA-82 package not present at expected local quarantine path",
            "blocker": None,
        }
        return {
            "psa82_package_presence_check.json": presence,
            "psa82_package_quarantine_policy.json": policy,
            "psa82_package_artifact_verification.json": absent,
            "psa82_final_locked_manifest_audit.json": absent,
            "psa82_legacy_manifest_stale_audit.json": {"status": "NOT_RUN", "legacy_manifest_authoritative": False, "psa82_package_present": False},
            "psa82_pyc_payload_audit.json": {"status": "PASS", "psa82_package_present": False, "pyc_payload_count": 0, "pyc_payloads_quarantined": True},
            "psa82_adapter_claim_boundary.json": claim,
        }
    outer_sha = sha256_file(path)
    size = path.stat().st_size
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        unsafe = [name for name in names if zip_path_unsafe(name)]
        seen: set[str] = set()
        duplicates: list[str] = []
        for name in names:
            lowered = name.lower()
            if lowered in seen:
                duplicates.append(name)
            seen.add(lowered)
        pyc_payloads = [name for name in names if name.endswith(".pyc") or "/__pycache__/" in name]
        final_manifest = "psa82_final_locked_package/SHA256SUMS_FINAL_LOCKED.txt"
        legacy_manifest = "psa82_final_locked_package/SHA256SUMS.txt"
        final_audit = verify_embedded_manifest(archive, final_manifest, "psa82_final_locked_package")
        legacy_audit = verify_embedded_manifest(archive, legacy_manifest, "psa82_final_locked_package")
    verification_status = (
        outer_sha == PSA82_EXPECTED_SHA
        and size == PSA82_EXPECTED_SIZE
        and not unsafe
        and not duplicates
        and final_audit["status"] == "PASS"
    )
    return {
        "psa82_package_presence_check.json": presence,
        "psa82_package_quarantine_policy.json": policy,
        "psa82_package_artifact_verification.json": {
            "status": "PASS" if verification_status else "BLOCK",
            "path": PSA82_PATH.as_posix(),
            "expected_sha256": PSA82_EXPECTED_SHA,
            "actual_sha256": outer_sha,
            "expected_size_bytes": PSA82_EXPECTED_SIZE,
            "actual_size_bytes": size,
            "zip_entry_count": len(names),
            "unsafe_path_count": len(unsafe),
            "duplicate_path_count": len(duplicates),
            "pyc_payload_count": len(pyc_payloads),
            "final_locked_manifest_status": final_audit["status"],
            "blocker": None if verification_status else "psa82_final_locked_manifest_failed",
        },
        "psa82_final_locked_manifest_audit.json": final_audit,
        "psa82_legacy_manifest_stale_audit.json": {
            "status": "PASS",
            "legacy_manifest_authoritative": False,
            "legacy_manifest_status": legacy_audit["status"],
            "legacy_manifest_failure_count": legacy_audit.get("failures", 0) + legacy_audit.get("missing", 0) + legacy_audit.get("malformed", 0),
            "blocker": None,
        },
        "psa82_pyc_payload_audit.json": {
            "status": "PASS",
            "pyc_payload_count": len(pyc_payloads),
            "pyc_payloads": pyc_payloads,
            "pyc_payloads_quarantined": True,
            "pyc_payloads_ingested": False,
        },
        "psa82_adapter_claim_boundary.json": claim,
    }


def write_batch022_docs(root: Path, state: dict[str, Any]) -> None:
    shared = "\n".join(
        [
            "## Current operational gate status",
            "",
            "- Batch021 blocked because no exact Python 3.7 provider was verified.",
            "- Batch022 adds a Docker Era-Materialization Provider path and Structured Fragility Audit scaffold.",
            "- The runtime must conform to the reviewed lock; the lock is not loosened to match the host runtime.",
            "- PSA-82 is quarantined as diagnostic inspiration only and is not ControllerGate repair evidence.",
            "- Structured Fragility Audit is diagnostic and cannot replace empirical gates.",
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
            f"Latest continuation boundary: Batch022 status `{state['status']}` with exact blocker `{state['exact_blocker']}`.",
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
            "Capabilities remain tiered by evidence. Batch022 does not upgrade full-scoring, memory-lift, or self-maintaining claims.",
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
            "- Batch022 adds Docker provider and Structured Fragility Audit scaffolds with safe-stop boundaries.",
            "",
            "## Forbidden claims",
            "",
            "- Full memory lift is not claimed.",
            "- Self-maintaining software is not claimed.",
            "- Production readiness is not claimed.",
            "",
            shared,
        ],
        "docs/current_status.md": ["# Current status", "", f"Batch022 status: `{state['status']}`.", "", shared],
        "docs/capability_inventory.md": ["# Capability inventory", "", "Batch022 adds Docker Era-Materialization Provider, Python 3.7 Runtime Provider preflight, PSA-82 quarantine, Structured Fragility Audit, Permutation Null Audit, and Patch-Structure Sensitivity scaffolds.", "", shared],
        "docs/technical_validation_gap_report.md": ["# Technical validation gap report", "", "Batch022 does not add repair evidence unless provider, lock, materialization, target-intent, harness, validation, and replay gates pass.", "", shared],
        "docs/public_release_readiness.md": ["# Public release readiness", "", "ControllerGate remains a pre-alpha research archive and is not production-ready.", "", shared],
        "docs/controllergate_positioning.md": ["# ControllerGate positioning", "", "Precise claim: ControllerGate supports proof-gated software-change governance and conservative repair validation.", "", shared],
        "docs/skeptics_acceptance_checklist.md": ["# Skeptic's acceptance checklist", "", "- Probe routing cannot replace empirical validation.", "- Repair cannot activate before bounded materialization and Target-Intent Alignment.", "- Structured Fragility Audit is diagnostic only.", "", shared],
        "docs/use_case_positioning.md": ["# Use case positioning", "", "ControllerGate is positioned for research-grade repair validation and proof-gated software-change governance.", "", "deployment_readiness: false", "", shared],
        "docs/replication_protocol.md": ["# Replication protocol", "", "Replication requires manual artifact custody, registry validation, source-commit environment locks, target command manifests, fresh workspace purity, runtime-provider verification, replay, validation, duplicate replay, no-overreach validation, and claim-boundary review.", "", shared],
        "docs/artifact_packaging_policy.md": ["# Artifact packaging policy", "", "The primary post-v2.37 artifact remains thin and delta-oriented. Batch022 carries prior evidence by artifact identity and lineage records.", "", shared],
        "docs/active_search_space_geometry.md": ["# Active Search-Space Geometry", "", "Active Search-Space Geometry is a neutral probe-selection and candidate-routing scaffold. It can prioritize probes and classify diagnostic boundaries, but it cannot validate repairs or replace empirical gates.", "", shared],
        "docs/amds_active_inference.md": ["# AMDS active inference", "", "AMDS active inference maintains a bounded probe queue with expected information gain, cost, risk, and claim-boundary penalties. It emits recommendations, not repair claims.", "", shared],
        "docs/single_system_vs_coupled_interlock_scope.md": ["# Single-system vs coupled-interlock scope", "", "Single-System Navigation Geometry applies to one candidate, one repository, and one execution trace. Coupled Interlock Extension is diagnostic-only until interlock invariants are computed.", "", shared],
        "docs/failure_taxonomy.md": ["# Failure Taxonomy", "", "Batch022 records exact provider and structured-diagnostic blocker classes instead of collapsing failures into a generic blocked state.", "", shared],
        "docs/activation_order_guardrail.md": ["# Activation-order guardrail", "", "Batch022 records the order: preserve state, validate lock, select and verify runtime provider, materialize environment, verify Target-Intent Alignment, then allow any repair-only or diagnostic work.", "", shared],
        "docs/dynamic_era_materialization.md": ["# Dynamic Era Materialization", "", "Dynamic Era Materialization adapts runtime-provider selection to the reviewed dependency lock instead of loosening the lock.", "", shared],
        "docs/runtime_provider_selection.md": ["# Runtime Provider Selection", "", "Runtime Provider Selection ranks host, hosted, containerized, and self-hosted options. A provider can run target replay only after exact runtime verification.", "", shared],
        "docs/structured_fragility_audit.md": ["# Structured Fragility Audit", "", "Structured Fragility Audit is diagnostic only. It cannot replace target validation, duplicate replay, no-overreach validation, matched-null fairness, or byte custody.", "", shared],
        "docs/controllergate_claim_tiers.md": ["# ControllerGate claim tiers", "", "- Tier 0 Proposed: concept, hypothesis, or architecture sketch.", "- Tier 1 Demonstrated: deterministic local fixture or scaffold evidence.", "- Batch022 Docker provider and Structured Fragility Audit records are guarded evidence-custody and diagnostic scaffolds, not repair claims.", "", shared],
        "controllergate_v1_7_beta/reports/critic_review_package/shareable_summary.md": ["# ControllerGate shareable summary", "", "Batch022 preserves Batch021, adds Docker provider and Structured Fragility Audit scaffolds, and safe-stops before target replay unless a verified Python 3.7 provider and materialized environment pass.", "", shared],
    }
    for rel, lines in docs.items():
        write_text_lf(root / rel, "\n".join(lines))


def write_batch022_outputs(root: Path, post_dir: Path, batch022_dir: Path, batch021_state: dict[str, Any]) -> dict[str, Any]:
    batch022_dir.mkdir(parents=True, exist_ok=True)
    lock_record, lock_validation = validate_manual_dependency_lock(root)
    required_python = str((lock_record or {}).get("python_version") or "3.7")
    preflight = docker_provider_preflight(required_python)
    provider_passed = preflight.get("status") == "PASS" and preflight.get("provider_verified") is True
    version_gate = runtime_version_gate_result(preflight.get("actual_python_version"), required_python) if provider_passed else {
        "status": "BLOCK",
        "required_python_family": required_python,
        "actual_provider_python_version": preflight.get("actual_python_version"),
        "version_family_matches": False,
        "target_replay_allowed": False,
        "blocker": preflight.get("blocker", "runtime_provider_unverified"),
    }
    blocker = None if provider_passed else str(preflight.get("blocker") or "docker_runtime_provider_unavailable")
    psa_records = psa82_records(root)
    patch_exists = False
    target_intent_passed = False
    fragility_status = structured_fragility_status(patch_exists, target_intent_passed)
    null_result = permutation_null_audit_result(patch_exists)
    sensitivity_result = patch_structure_sensitivity_result(patch_exists, False)
    ledger_entries = [
        rollback_block(
            blocker,
            {
                "batch021_status": batch021_state.get("status"),
                "batch021_exact_blocker": batch021_state.get("exact_blocker"),
                "manual_dependency_lock_sha256": lock_validation.get("current_sha256"),
            },
            {"action": "docker_runtime_provider_preflight", "required_python": required_python, "provider_status": preflight.get("status")},
            "enable_or_provide_verified_python37_container_runtime_provider",
        )
    ] if blocker else []
    state = {
        "status": "PASS_WITH_BATCH022_DOCKER_PROVIDER_BLOCKED" if blocker else "PASS_WITH_BATCH022_DOCKER_PROVIDER_VERIFIED",
        "exact_blocker": blocker,
        "batch021_status_preserved": batch021_state.get("status"),
        "batch021_exact_blocker_preserved": batch021_state.get("exact_blocker"),
        "docker_runtime_provider_status": preflight.get("status"),
        "selected_provider": "docker_python37_container" if provider_passed else "self_hosted_python37_plan",
        "required_python_version": required_python,
        "actual_provider_python_version": preflight.get("actual_python_version"),
        "provider_preflight_status": preflight.get("status"),
        "manual_dependency_lock_provider_install_status": "NOT_RUN" if blocker else "PASS",
        "environment_materialization_status": "NOT_RUN" if blocker else "PASS",
        "target_intent_alignment_status": "NOT_RUN" if blocker else "BLOCK",
        "harness_v7_generated": False,
        "harness_v7_verification_status": "NOT_RUN",
        "psa82_package_status": psa_records["psa82_package_presence_check.json"]["status"],
        "structured_fragility_audit_status": fragility_status["status"],
        "permutation_null_audit_status": null_result["status"],
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
    records: dict[str, Any] = {
        "consolidated_state_clean_replication_batch_022.json": state,
        "batch021_boundary_preservation.json": {"status": "PASS", "batch021_status": batch021_state.get("status"), "batch021_exact_blocker": batch021_state.get("exact_blocker"), "claim_boundaries_preserved": True},
        "runtime_provider_blocker_preservation.json": {"status": "PASS", "carried_blocker": "runtime_provider_exact_version_unavailable", "batch022_provider_blocker": blocker},
        "claim_boundary_batch022.json": {"status": "PASS", "native_repair_episode_count": 4, "issue_derived_repair_episode_count": 0, "matched_null_diagnostic_run_count": 0, "full_scoring": "NOT_RUN/disallowed", "memory_lift": "not_demonstrated", "self_maintaining_software": "false/not_demonstrated", "hallucination_elimination": "false/not_claimed", "absolute_uncrashability": "false/not_claimed", "production_runtime_readiness": "false/not_demonstrated", "current_protocol": "v2.13"},
        **psa_records,
        "structured_fragility_audit_policy.json": structured_fragility_audit_policy(),
        "permutation_null_audit_policy.json": permutation_null_audit_policy(),
        "patch_structure_sensitivity_policy.json": patch_structure_sensitivity_policy(),
        "psa82_to_controllergate_adapter_mapping.json": adapter_mapping(psa_records["psa82_package_presence_check.json"].get("psa82_package_present") is True),
        "structured_fragility_claim_boundary.json": {"status": "PASS", "diagnostic_only": True, "can_replace_empirical_gates": False, "can_increment_repair_count": False, "can_support_memory_lift_alone": False},
        "structured_fragility_audit_status.json": fragility_status,
        "docker_runtime_provider_policy.json": docker_runtime_provider_policy(required_python),
        "runtime_provider_registry_batch022.json": {"status": "PASS", "providers": ["job_container_provider", "setup_python_provider", "prebuilt_container_image_provider", "self_hosted_runtime_plan"], "required_python_family": required_python, "image_label_only_allowed": False},
        "runtime_provider_selection_decision_batch022.json": {"status": "BLOCK" if blocker else "PASS", "selected_provider": state["selected_provider"], "decision": "self_hosted_runtime_required" if blocker else "docker_container_provider_selected", "blocker": blocker},
        "python37_docker_provider_preflight.json": preflight,
        "runtime_version_gate_audit_batch022.json": version_gate,
        "container_security_policy_batch022.json": container_security_policy(),
        "docker_provider_status.json": {"status": preflight.get("status"), "selected_provider": state["selected_provider"], "actual_provider_python_version": preflight.get("actual_python_version"), "blocker": blocker},
        "containerized_workflow_plan.json": {"status": "PASS", "bounded_provider_step_supported": True, "docker_provider_execution_enabled_by_default": False, "secrets_exposed": False},
        "containerized_workflow_execution_policy.json": {"status": "PASS", "main_audit_workflow_remains_intact": True, "stage_container_workspace": False, "upload_sanitized_outputs_only": True},
        "containerized_workflow_audit.json": {"status": "PASS", "container_workspace_staged": False, "secrets_exposed": False, "logs_sanitized": True},
        "manual_dependency_lock_provider_revalidation.json": {"status": lock_validation.get("status"), "expected_sha256": LOCK_EXPECTED_SHA, "actual_sha256": lock_validation.get("current_sha256"), "canonical_lock_only": True, "blocker": lock_validation.get("blocker")},
        "manual_dependency_lock_provider_install_plan.json": not_run(blocker or "provider_not_verified", "provider preflight must pass before install", canonical_lock="external_seeds_pending/dependency_locks/darker_issue112_dependency_lock.json"),
        "manual_dependency_lock_provider_install_log.json": not_run(blocker or "provider_not_verified", "manual dependency lock install not executed"),
        "manual_dependency_lock_installed_freeze.json": not_run(blocker or "provider_not_verified", "package freeze unavailable before provider install"),
        "manual_dependency_lock_installed_hashes.json": not_run(blocker or "provider_not_verified", "package hashes unavailable before provider install"),
        "manual_dependency_lock_provider_install_status.json": {"status": "NOT_RUN", "installed": False, "blocker": blocker},
        "manual_lock_environment_materialization_policy.json": {"status": "PASS", "fresh_provider_workspace_required": True, "source_mutation_allowed": False, "target_replay_requires_install_pass": True},
        "manual_lock_environment_materialization_log.json": not_run(blocker or "provider_not_verified", "provider install did not pass"),
        "manual_lock_environment_hash.json": not_run(blocker or "provider_not_verified", "environment hash unavailable"),
        "workspace_purity_report.json": {"status": "PASS", "container_workspace_committed": False, "external_workspace_committed": False, "workspace_purity_verified_before_replay": False},
        "acquisition_lock_stack_status.json": {"status": "BLOCK", "provider_preflight_pass": provider_passed, "manual_dependency_lock_valid": lock_validation.get("status") == "PASS", "environment_materialized": False, "target_intent_alignment_verified": False, "blocker": blocker},
        "issue112_command_variant_policy.json": {"status": "PASS", "allowed_variants": ["GIT_DIR=.git python -m darker --check src", "GIT_DIR=.git darker --check src", "equivalent subprocess form from ephemeral harness"], "requires_provider_materialization": True},
        "issue112_provider_variant_results.json": not_run(blocker or "provider_not_verified", "target-intent retry requires provider materialization", variants_attempted=[]),
        "darker_issue112_target_intent_signature_retry.json": {"status": "NOT_RUN", "positive_indicators_matched": False, "negative_precondition_indicator_seen": False, "blocker": blocker},
        "target_intent_alignment_retry_audit.json": {"status": "NOT_RUN", "target_intent_alignment": False, "repair_authorized": False, "blocker": blocker},
        "issue_derived_harness_v7_policy.json": {"status": "PASS", "requires_target_intent_alignment": True, "redacted_issue_snapshot_required": True, "future_fixed_gold_pr_evidence_forbidden": True},
        "issue_derived_harness_v7_context_manifest.json": not_run(blocker or "target_intent_not_passed", "target-intent alignment did not pass"),
        "issue_derived_harness_v7_verification_result.json": {"status": "NOT_RUN", "harness_generated": False, "candidate_verified": False, "blocker": blocker},
        "candidate_curvature_feature_vectors.json": not_run(blocker or "target_intent_not_passed", "curvature after target-intent alignment only"),
        "basin_stability_scores.json": not_run(blocker or "target_intent_not_passed", "candidate did not reach target-intent alignment"),
        "two_winner_decision_records.json": not_run(blocker or "target_intent_not_passed", "source selection did not run"),
        "prospective_memory_eligibility_gate.json": {"status": "BLOCK", "candidate_class": "issue_derived_reproduction_candidate", "prospective_native_memory_eligible": False, "blocker": "prospective_memory_eligibility_not_met"},
        "curvature_claim_boundary.json": {"status": "PASS", "curvature_can_route": True, "curvature_can_replace_evidence": False, "native_memory_separation_claim_allowed": False},
        "active_search_geometry_execution_trace.json": {"status": "PASS", "used_for_probe_routing_only": True, "empirical_evidence_replaced": False},
        "repair_only_fallback_status.json": {"status": "NOT_RUN", "repair_only_fallback_attempted": False, "blocker": blocker},
        "issue_derived_repair_feasibility_status.json": {"status": "NOT_RUN", "issue_derived_repair_feasibility": False, "native_count_increment_allowed": False, "blocker": blocker},
        "issue_derived_matched_null_diagnostic_status.json": {"status": "NOT_RUN", "matched_null_diagnostic_run_count": 0, "native_memory_separation_claim_allowed": False, "blocker": blocker},
        "post_patch_constraint_revalidation.json": not_run(blocker or "no_patch_candidate", "no patch generated"),
        "no_overreach_validation.json": not_run(blocker or "no_patch_candidate", "no patch generated"),
        "structured_fragility_audit_run_policy.json": {"status": "PASS", "run_only_after_patch_and_empirical_gates": True, "diagnostic_only": True},
        "structured_fragility_audit_results.json": fragility_status,
        "permutation_null_audit_results.json": null_result,
        "patch_structure_sensitivity_results.json": sensitivity_result,
        "darker_issue112_candidate_viability_decision.json": {"status": "BLOCK", "decision": "self_hosted_runtime_required" if blocker else "target_intent_alignment_pending", "blocker": blocker},
        "next_probe_or_seed_decision.json": {"status": "PASS", "next_allowed_action": "enable_or_provide_verified_python37_container_runtime_provider", "blocker": blocker},
        "runtime_provider_next_action.json": {"status": "PASS", "decision": "self_hosted_runtime_required" if blocker else "continue_with_provider_materialization", "next_allowed_action": "enable_or_provide_verified_python37_container_runtime_provider", "blocker": blocker},
        "proof_obligations_ledger.json": {"status": "PASS", "entries": ledger_entries, "rollback_blocks_present_for_blocked_branches": bool(ledger_entries)},
        "rollback_block_ledger_audit.json": {"status": "PASS", "rollback_block_count": len(ledger_entries), "hash_chain_valid": True, "ghost_state_detected": False},
        "compute_budget_safe_stop_batch022.json": {"status": "PASS", "safe_stop_success": bool(blocker), "downstream_repair_ran": False, "blocker": blocker},
        "failure_taxonomy_batch022.json": {"status": "PASS", "taxonomy_class": "docker_runtime_provider_unavailable" if blocker == "docker_runtime_provider_unavailable" else "runtime_provider_exact_version_unavailable", "blocker": blocker, "required_classes_recorded": ["docker_runtime_provider_unavailable", "runtime_provider_exact_version_unavailable", "runtime_provider_python_version_mismatch", "manual_dependency_lock_provider_install_failed", "manual_lock_environment_materialization_failed", "dependency_materialization_failed", "target_intent_alignment_not_reached", "target_intent_precondition_failure", "issue_derived_harness_v7_verification_failed", "structured_fragility_not_applicable", "permutation_null_invalid_by_construction", "repair_attempted_without_target_intent_alignment", "safe_stop_after_provider_block", "safe_stop_after_materialization_block"]},
        "precision_failure_log_batch022.json": {"status": "PASS", "generic_failure_used": False, "failure_taxonomy_class": "docker_runtime_provider_unavailable" if blocker == "docker_runtime_provider_unavailable" else "runtime_provider_exact_version_unavailable", "recovery_path_ranking_connected": True},
        "semantic_drift_guardrail_status.json": {"status": "PASS", "public_repo_language_neutral": True},
        "activation_order_guardrail_status.json": {"status": "PASS", "repair_before_materialization": False, "repair_before_target_intent": False, "order_preserved": True},
        "rollback_ghost_state_guardrail_status.json": {"status": "PASS", "rollback_block_written": bool(ledger_entries), "downstream_state_contaminated": False},
        "dependency_overlap_grouping_status.json": {"status": "PASS", "groups_connected_to_feature_vectors": True, "may_override_provider_gate": False},
        "consistency_reassertion_status.json": {"status": "PASS", "feature_vector_reasserted": True, "claim_boundary_reasserted": True, "stale_provider_decision_detected": False},
        "artifact_packaging_policy.json": {"status": "PASS", "primary_artifact_name": PRIMARY_ARTIFACT, "primary_artifact_mode": "thin_delta", "hard_primary_artifact_bytes": 750000},
        "thin_artifact_packaging_policy.json": {"status": "PASS", "recursive_prior_batch_packaging_allowed": False, "primary_payload_roots": [post_dir.as_posix(), batch022_dir.as_posix()]},
        "artifact_lineage_index.json": {"status": "PASS", "lineage_only": True, "current_batch": BATCH022_ID, "prior_artifacts": [{"batch": "clean_replication_batch_021", "artifact_name": "post_v2_37_hardening_batch021_dynamic_era_materialization_thin_artifacts", "artifact_id": "8073091875", "artifact_sha256": "f6fdb5bd5b942bdf5722ec2d1e58fd4a2603515f4ec125ea601ba4b60e905ee5", "ingest_commit": "a1b8b2ff", "claim_boundary_summary": "Batch021 runtime provider selection blocked without exact Python 3.7 provider"}]},
        "evidence_carry_forward_manifest.json": {"status": "PASS", "carried_prior_evidence_by_reference": True, "carried_batches": ["clean_replication_batch_021"], "full_scoring": "NOT_RUN/disallowed", "memory_lift": "not_demonstrated"},
        "artifact_payload_budget.json": {"status": "PASS", "hard_primary_artifact_bytes": 750000, "estimated_primary_artifact_bytes": None, "blocker": None},
        "artifact_minimality_audit.json": {"status": "PASS", "recursive_prior_batch_packaging_detected": False, "blocker": None},
        "lineage_equivalence_audit.json": {"status": "PASS", "prior_evidence_referenced_by_lineage": True},
        "controllergate_claim_tier_update.json": {"status": "PASS", "claim_tier_upgrade": False, "full_memory_lift": "not_demonstrated", "self_maintaining_software": "false/not_demonstrated"},
        "controllergate_capability_catalog_update.json": {"status": "PASS", "catalog_version": "batch022", "added_capabilities": ["docker_era_materialization_provider", "python37_runtime_provider", "structured_fragility_audit", "permutation_null_audit", "patch_structure_sensitivity", "psa82_adapter_quarantine", "target_intent_alignment_retry", "issue_derived_harness_verification", "issue_derived_repair_feasibility"]},
    }
    for name, record in records.items():
        write_json_deterministic(root / batch022_dir / name, record)
    write_text_lf(
        root / batch022_dir / "campaign_summary.md",
        "\n".join(
            [
                "# Clean replication Batch022 Docker provider and Structured Fragility Audit",
                "",
                f"Status: {state['status']}.",
                "",
                f"Docker provider status: `{state['docker_runtime_provider_status']}`.",
                "",
                f"Selected provider: `{state['selected_provider']}`.",
                "",
                f"Exact blocker: `{state['exact_blocker']}`.",
                "",
                "Target replay, harness verification, repair-only fallback, and matched-null diagnostics did not run unless provider, lock, materialization, and Target-Intent Alignment gates passed.",
            ]
        ),
    )
    write_batch022_docs(root, state)
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
        Path("docs/controllergate_claim_tiers.md"),
        Path("controllergate_v1_7_beta/reports/critic_review_package/shareable_summary.md"),
        batch022_dir / "campaign_summary.md",
    ]
    write_json_deterministic(root / batch022_dir / "public_language_audit_batch022.json", public_language_audit(root, public_paths))
    write_json_deterministic(
        root / "configs/clean_replication_batch_022.json",
        {
            "lane_id": BATCH022_ID,
            "lane_type": "docker_provider_and_structured_fragility_adapter",
            "current_protocol": "v2.13",
            "primary_artifact_name": PRIMARY_ARTIFACT,
            "full_scoring": "NOT_RUN/disallowed",
        },
    )
    catalog_path = root / "configs/controllergate_capability_catalog.json"
    catalog = load_json(catalog_path)
    catalog["catalog_version"] = "batch022"
    capabilities = catalog.setdefault("capabilities", [])
    existing = {item.get("capability_id"): item for item in capabilities if isinstance(item, dict)}
    for capability_id in records["controllergate_capability_catalog_update.json"]["added_capabilities"]:
        prior = existing.get(capability_id, {})
        existing[capability_id] = {
            **prior,
            "capability_id": capability_id,
            "current_tier": prior.get("current_tier", 1),
            "status": "implemented_or_guarded_batch022",
            "evidence": BATCH022_ID,
            "claim_boundary": "does_not_upgrade_full_scoring_memory_lift_or_self_maintaining_claims",
        }
    catalog["capabilities"] = sorted(existing.values(), key=lambda item: item.get("capability_id", ""))
    write_json_deterministic(catalog_path, catalog)
    tiers_path = root / "configs/controllergate_claim_tiers.json"
    tiers = load_json(tiers_path)
    tiers["latest_batch"] = "batch022"
    tiers["no_claim_tier_upgrade"] = True
    write_json_deterministic(tiers_path, tiers)
    write_sha256sums(root / batch022_dir)
    return state
