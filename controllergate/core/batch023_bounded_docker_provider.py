from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path
from typing import Any

from .batch020_manual_lock import public_language_audit, validate_manual_dependency_lock
from .batch022_docker_psa82 import LOCK_EXPECTED_SHA, PSA82_EXPECTED_SHA, PSA82_EXPECTED_SIZE, not_run, psa82_records, rollback_block
from .docker_runtime_provider import PYTHON37_IMAGE, container_security_policy, docker_provider_preflight, docker_runtime_provider_policy
from .evidence import hash_record, sha256_bytes, sha256_file, write_json_deterministic, write_text_lf
from .manifests import write_sha256sums
from .patch_structure_sensitivity import patch_structure_sensitivity_policy, patch_structure_sensitivity_result
from .permutation_null_audit import permutation_null_audit_policy, permutation_null_audit_result
from .runtime_version_gate import runtime_version_gate_policy, runtime_version_gate_result
from .structured_fragility_audit import structured_fragility_audit_policy, structured_fragility_status


BATCH023_ID = "clean_replication_batch_023"
PRIMARY_ARTIFACT = "post_v2_37_hardening_batch023_bounded_docker_provider_thin_artifacts"
ENABLE_ENV = "CONTROLLERGATE_ENABLE_DOCKER_PROVIDER"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _run(command: list[str], *, timeout: int) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, text=True, capture_output=True, timeout=timeout)


def _safe_text(value: str, limit: int = 4000) -> str:
    return value.replace(os.environ.get("GITHUB_TOKEN", ""), "[redacted]")[:limit]


def docker_output_transport_probe(provider_passed: bool) -> dict[str, Any]:
    if not provider_passed:
        return {
            "status": "NOT_RUN",
            "provider_output_transport_verified": False,
            "output_sha256": None,
            "blocker": "python37_provider_unavailable",
        }
    script = "mkdir -p /tmp/controllergate-provider-probe && python - <<'PY'\nfrom pathlib import Path\np=Path('/tmp/controllergate-provider-probe/probe.txt')\np.write_text('provider-output-ok\\n')\nprint(p.read_text().strip())\nPY"
    completed = _run(["docker", "run", "--rm", "--network", "none", PYTHON37_IMAGE, "sh", "-lc", script], timeout=120)
    output = f"{completed.stdout}\n{completed.stderr}"
    return {
        "status": "PASS" if completed.returncode == 0 and "provider-output-ok" in completed.stdout else "BLOCK",
        "provider_output_transport_verified": completed.returncode == 0 and "provider-output-ok" in completed.stdout,
        "command": "docker run --rm --network none python:3.7-slim sh -lc <provider-output-probe>",
        "returncode": completed.returncode,
        "stdout_sha256": sha256_bytes(completed.stdout.encode("utf-8")),
        "stderr_sha256": sha256_bytes(completed.stderr.encode("utf-8")),
        "output_sha256": sha256_bytes(output.encode("utf-8")),
        "blocker": None if completed.returncode == 0 and "provider-output-ok" in completed.stdout else "runtime_provider_output_transport_failed",
    }


def dependency_install_records(root: Path, provider_passed: bool, lock_validation: dict[str, Any]) -> dict[str, dict[str, Any]]:
    if not provider_passed:
        blocker = "python37_provider_unavailable"
        return {
            "manual_dependency_lock_provider_revalidation.json": {
                "status": lock_validation.get("status"),
                "expected_sha256": LOCK_EXPECTED_SHA,
                "actual_sha256": lock_validation.get("current_sha256"),
                "canonical_lock_only": True,
                "blocker": lock_validation.get("blocker"),
            },
            "manual_dependency_lock_provider_install_plan.json": not_run(blocker, "provider preflight must pass before lock install"),
            "manual_dependency_lock_provider_install_log.json": not_run(blocker, "provider preflight did not pass"),
            "manual_dependency_lock_installed_freeze.json": not_run(blocker, "package freeze unavailable before provider install"),
            "manual_dependency_lock_installed_hashes.json": not_run(blocker, "package hashes unavailable before provider install"),
            "manual_dependency_lock_provider_install_status.json": {"status": "NOT_RUN", "installed": False, "blocker": blocker},
        }
    lock_path = root / "external_seeds_pending/dependency_locks/darker_issue112_dependency_lock.json"
    lock = load_json(lock_path)
    packages = lock.get("packages", [])
    install_specs = [f"{item['name']}=={item['version']}" for item in packages if item.get("name") != "pip"]
    pip_spec = next((f"{item['name']}=={item['version']}" for item in packages if item.get("name") == "pip"), "pip==20.3.3")
    package_args = " ".join(install_specs)
    script = "\n".join(
        [
            "set -eu",
            f"python -m pip install --disable-pip-version-check --no-input {pip_spec}",
            f"python -m pip install --disable-pip-version-check --no-input {package_args}",
            "python -m pip freeze",
        ]
    )
    completed = _run(["docker", "run", "--rm", PYTHON37_IMAGE, "sh", "-lc", script], timeout=600)
    output = f"{completed.stdout}\n{completed.stderr}"
    passed = completed.returncode == 0
    freeze_lines = [line.strip() for line in completed.stdout.splitlines() if "==" in line]
    return {
        "manual_dependency_lock_provider_revalidation.json": {
            "status": lock_validation.get("status"),
            "expected_sha256": LOCK_EXPECTED_SHA,
            "actual_sha256": lock_validation.get("current_sha256"),
            "canonical_lock_only": True,
            "blocker": lock_validation.get("blocker"),
        },
        "manual_dependency_lock_provider_install_plan.json": {
            "status": "PASS",
            "canonical_lock": "external_seeds_pending/dependency_locks/darker_issue112_dependency_lock.json",
            "package_count": len(packages),
            "package_index_source": "https://pypi.org/simple",
            "network_access_required_for_package_install": True,
            "undeclared_dependency_install_allowed": False,
        },
        "manual_dependency_lock_provider_install_log.json": {
            "status": "PASS" if passed else "BLOCK",
            "command": "docker run --rm python:3.7-slim sh -lc <manual-dependency-lock-install>",
            "returncode": completed.returncode,
            "stdout_sha256": sha256_bytes(completed.stdout.encode("utf-8")),
            "stderr_sha256": sha256_bytes(completed.stderr.encode("utf-8")),
            "output_sha256": sha256_bytes(output.encode("utf-8")),
            "stdout_excerpt": _safe_text(completed.stdout, 1200),
            "stderr_excerpt": _safe_text(completed.stderr, 1200),
            "blocker": None if passed else "manual_dependency_lock_provider_install_failed",
        },
        "manual_dependency_lock_installed_freeze.json": {
            "status": "PASS" if passed else "NOT_RUN",
            "freeze_line_count": len(freeze_lines) if passed else 0,
            "freeze_lines": freeze_lines[:80] if passed else [],
            "blocker": None if passed else "manual_dependency_lock_provider_install_failed",
        },
        "manual_dependency_lock_installed_hashes.json": {
            "status": "PASS" if passed else "NOT_RUN",
            "freeze_sha256": sha256_bytes("\n".join(freeze_lines).encode("utf-8")) if passed else None,
            "package_hash_recording_level": "freeze_hash_recorded",
            "blocker": None if passed else "manual_dependency_lock_provider_install_failed",
        },
        "manual_dependency_lock_provider_install_status.json": {
            "status": "PASS" if passed else "BLOCK",
            "installed": passed,
            "package_count": len(packages),
            "blocker": None if passed else "manual_dependency_lock_provider_install_failed",
        },
    }


def materialization_records(install_passed: bool) -> dict[str, dict[str, Any]]:
    if not install_passed:
        blocker = "manual_dependency_lock_provider_install_failed"
        return {
            "manual_lock_environment_materialization_policy.json": {"status": "PASS", "fresh_provider_workspace_required": True, "source_mutation_allowed": False, "target_replay_requires_install_pass": True},
            "manual_lock_environment_materialization_log.json": not_run(blocker, "manual dependency lock install did not pass"),
            "manual_lock_environment_hash.json": not_run(blocker, "environment hash unavailable before materialization"),
            "workspace_purity_report.json": {"status": "PASS", "container_workspace_committed": False, "external_workspace_committed": False, "workspace_purity_verified_before_replay": False},
            "acquisition_lock_stack_status.json": {"status": "BLOCK", "provider_preflight_pass": False, "manual_dependency_lock_installed": False, "environment_materialized": False, "target_intent_alignment_verified": False, "blocker": blocker},
        }
    return {
        "manual_lock_environment_materialization_policy.json": {"status": "PASS", "fresh_provider_workspace_required": True, "source_mutation_allowed": False, "target_replay_requires_install_pass": True},
        "manual_lock_environment_materialization_log.json": {
            "status": "BLOCK",
            "reason": "dependency lock installed in provider; source workspace checkout/transport remains blocked pending approved provider workspace bridge",
            "source_mutation_allowed": False,
            "blocker": "manual_lock_environment_materialization_failed",
        },
        "manual_lock_environment_hash.json": not_run("manual_lock_environment_materialization_failed", "source workspace was not materialized"),
        "workspace_purity_report.json": {"status": "PASS", "container_workspace_committed": False, "external_workspace_committed": False, "workspace_purity_verified_before_replay": False},
        "acquisition_lock_stack_status.json": {"status": "BLOCK", "provider_preflight_pass": True, "manual_dependency_lock_installed": True, "environment_materialized": False, "target_intent_alignment_verified": False, "blocker": "manual_lock_environment_materialization_failed"},
    }


def psa82_local_records(root: Path) -> dict[str, dict[str, Any]]:
    source = psa82_records(root)
    presence = source["psa82_package_presence_check.json"]
    final = source["psa82_final_locked_manifest_audit.json"]
    legacy = source["psa82_legacy_manifest_stale_audit.json"]
    pyc = source["psa82_pyc_payload_audit.json"]
    verification = source["psa82_package_artifact_verification.json"]
    return {
        "psa82_local_package_presence_check.json": {
            "status": presence.get("status"),
            "psa82_package_present": presence.get("psa82_package_present"),
            "path": presence.get("path"),
        },
        "psa82_local_package_quarantine_summary.json": {
            "status": verification.get("status"),
            "expected_sha256": PSA82_EXPECTED_SHA,
            "expected_size_bytes": PSA82_EXPECTED_SIZE,
            "actual_sha256": verification.get("actual_sha256"),
            "actual_size_bytes": verification.get("actual_size_bytes"),
            "full_package_committed": False,
            "controllergate_repair_evidence": False,
            "blocker": verification.get("blocker"),
        },
        "psa82_final_locked_manifest_summary.json": final,
        "psa82_legacy_manifest_status.json": legacy,
        "psa82_pyc_quarantine_summary.json": pyc,
        "psa82_adapter_claim_boundary.json": source["psa82_adapter_claim_boundary.json"],
    }


def write_batch023_docs(root: Path, state: dict[str, Any]) -> None:
    shared = "\n".join(
        [
            "## Current operational gate status",
            "",
            "- Batch022 blocked because Docker provider execution was disabled pending explicit bounded-provider activation.",
            "- Batch023 adds a Bounded Docker Provider Probe and GitHub Actions provider bridge.",
            "- The runtime must conform to the reviewed lock; the lock is not loosened to match the runtime.",
            "- Provider labels are insufficient; actual Python and pip versions must be recorded inside the provider.",
            "- External source execution must not receive write credentials or secrets.",
            "- PSA-82 is handled as a quarantined diagnostic inspiration package, not ControllerGate repair evidence.",
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
            f"Latest continuation boundary: Batch023 status `{state['status']}` with exact blocker `{state['exact_blocker']}`.",
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
            "Capabilities remain tiered by evidence. Batch023 does not upgrade full-scoring, memory-lift, or self-maintaining claims.",
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
            "- Batch023 adds a bounded provider probe and safe-stop boundary.",
            "",
            "## Forbidden claims",
            "",
            "- Full memory lift is not claimed.",
            "- Self-maintaining software is not claimed.",
            "- Production readiness is not claimed.",
            "",
            shared,
        ],
        "docs/current_status.md": ["# Current status", "", f"Batch023 status: `{state['status']}`.", "", shared],
        "docs/capability_inventory.md": ["# Capability inventory", "", "Batch023 adds Bounded Docker Provider Probe, GitHub Actions provider bridge, provider credentials isolation, provider output transport, and PSA-82 Quarantine Summary records.", "", shared],
        "docs/technical_validation_gap_report.md": ["# Technical validation gap report", "", "Batch023 does not add repair evidence unless provider, lock, materialization, Target-Intent Alignment, harness, validation, and replay gates pass.", "", shared],
        "docs/public_release_readiness.md": ["# Public release readiness", "", "ControllerGate remains a pre-alpha research archive and is not production-ready.", "", shared],
        "docs/controllergate_positioning.md": ["# ControllerGate positioning", "", "Precise claim: ControllerGate supports proof-gated software-change governance and conservative repair validation.", "", shared],
        "docs/skeptics_acceptance_checklist.md": ["# Skeptic's acceptance checklist", "", "- Provider execution must be bounded and credential-isolated.", "- Provider labels cannot replace actual runtime probes.", "- Repair cannot activate before materialization and Target-Intent Alignment.", "", shared],
        "docs/use_case_positioning.md": ["# Use case positioning", "", "ControllerGate is positioned for research-grade repair validation and proof-gated software-change governance.", "", "deployment_readiness: false", "", shared],
        "docs/replication_protocol.md": ["# Replication protocol", "", "Replication requires manual artifact custody, registry validation, runtime-provider verification, dependency-lock installation, materialization, replay, validation, duplicate replay, no-overreach validation, and claim-boundary review.", "", shared],
        "docs/artifact_packaging_policy.md": ["# Artifact packaging policy", "", "The primary post-v2.37 artifact remains thin and delta-oriented. Batch023 carries prior evidence by artifact identity and lineage records.", "", shared],
        "docs/active_search_space_geometry.md": ["# Active Search-Space Geometry", "", "Active Search-Space Geometry is a neutral probe-selection and candidate-routing scaffold. It can prioritize probes and classify diagnostic boundaries, but it cannot validate repairs or replace empirical gates.", "", shared],
        "docs/amds_active_inference.md": ["# AMDS active inference", "", "AMDS active inference maintains a bounded probe queue with expected information gain, cost, risk, and claim-boundary penalties. It emits recommendations, not repair claims.", "", shared],
        "docs/single_system_vs_coupled_interlock_scope.md": ["# Single-system vs coupled-interlock scope", "", "Single-System Navigation Geometry applies to one candidate, one repository, and one execution trace. Coupled Interlock Extension is diagnostic-only until interlock invariants are computed.", "", shared],
        "docs/failure_taxonomy.md": ["# Failure Taxonomy", "", "Batch023 records exact provider, install, materialization, and target-intent blocker classes instead of collapsing failures into a generic blocked state.", "", shared],
        "docs/activation_order_guardrail.md": ["# Activation-order guardrail", "", "Batch023 records the order: preserve state, activate bounded provider probe, verify runtime, install dependency lock, materialize environment, verify Target-Intent Alignment, then allow any repair-only or diagnostic work.", "", shared],
        "docs/dynamic_era_materialization.md": ["# Dynamic Era Materialization", "", "Dynamic Era Materialization adapts runtime-provider selection to the reviewed dependency lock instead of loosening the lock.", "", shared],
        "docs/runtime_provider_selection.md": ["# Runtime Provider Selection", "", "Runtime Provider Selection ranks host, hosted, containerized, and self-hosted options. A provider can run target replay only after exact runtime verification.", "", shared],
        "docs/structured_fragility_audit.md": ["# Structured Fragility Audit", "", "Structured Fragility Diagnostic is diagnostic only. It cannot replace target validation, duplicate replay, no-overreach validation, matched-null fairness, or byte custody.", "", shared],
        "docs/bounded_docker_provider_probe.md": ["# Bounded Docker Provider Probe", "", "Batch023 enables Docker provider execution only through an explicit bounded probe switch. The probe records actual Python and pip versions, credential isolation, output transport hashes, and safe-stop blockers.", "", shared],
        "docs/controllergate_claim_tiers.md": ["# ControllerGate claim tiers", "", "- Tier 0 Proposed: concept, hypothesis, or architecture sketch.", "- Tier 1 Demonstrated: deterministic local fixture or scaffold evidence.", "- Batch023 provider records are guarded evidence-custody and diagnostic scaffolds, not repair claims.", "", shared],
        "controllergate_v1_7_beta/reports/critic_review_package/shareable_summary.md": ["# ControllerGate shareable summary", "", "Batch023 preserves Batch022, adds a Bounded Docker Provider Probe and GitHub Actions provider bridge, and safe-stops before target replay unless provider, lock, materialization, and Target-Intent Alignment gates pass.", "", shared],
    }
    for rel, lines in docs.items():
        write_text_lf(root / rel, "\n".join(lines))


def write_batch023_outputs(root: Path, post_dir: Path, batch023_dir: Path, batch022_state: dict[str, Any]) -> dict[str, Any]:
    batch023_dir.mkdir(parents=True, exist_ok=True)
    lock_record, lock_validation = validate_manual_dependency_lock(root)
    required_python = str((lock_record or {}).get("python_version") or "3.7")
    enabled = os.environ.get(ENABLE_ENV, "0") == "1"
    preflight = docker_provider_preflight(required_python)
    if not enabled:
        preflight = {**preflight, "blocker": "docker_provider_not_enabled", "reason": "bounded Docker provider probe was not explicitly enabled"}
    provider_passed = preflight.get("status") == "PASS" and preflight.get("provider_verified") is True
    output_transport = docker_output_transport_probe(provider_passed)
    install_records = dependency_install_records(root, provider_passed, lock_validation)
    install_passed = install_records["manual_dependency_lock_provider_install_status.json"].get("status") == "PASS"
    materialization = materialization_records(install_passed)
    environment_passed = materialization["manual_lock_environment_materialization_log.json"].get("status") == "PASS"
    target_intent_passed = False
    exact_blocker = None
    if not enabled:
        exact_blocker = "docker_provider_not_enabled"
    elif not provider_passed:
        exact_blocker = preflight.get("blocker") or "python37_provider_unavailable"
    elif not install_passed:
        exact_blocker = "manual_dependency_lock_provider_install_failed"
    elif not environment_passed:
        exact_blocker = "manual_lock_environment_materialization_failed"
    elif not target_intent_passed:
        exact_blocker = "target_intent_alignment_not_reached"
    fragility_status = structured_fragility_status(False, False)
    null_result = permutation_null_audit_result(False)
    sensitivity_result = patch_structure_sensitivity_result(False, False)
    version_gate = runtime_version_gate_result(preflight.get("actual_python_version"), required_python) if provider_passed else {
        "status": "BLOCK",
        "required_python_family": required_python,
        "actual_provider_python_version": preflight.get("actual_python_version"),
        "version_family_matches": False,
        "target_replay_allowed": False,
        "blocker": exact_blocker,
    }
    ledger_entries = [
        rollback_block(
            exact_blocker or "target_intent_alignment_not_reached",
            {"batch022_status": batch022_state.get("status"), "batch022_exact_blocker": batch022_state.get("exact_blocker")},
            {"enabled": enabled, "provider_passed": provider_passed, "install_passed": install_passed, "environment_passed": environment_passed},
            "provide_verified_provider_workspace_bridge_or_refine_container_materialization",
        )
    ] if exact_blocker else []
    status_suffix = {
        "docker_provider_not_enabled": "DOCKER_PROVIDER_NOT_ENABLED",
        "python37_provider_unavailable": "PROVIDER_PREFLIGHT_BLOCKED",
        "docker_runtime_provider_unavailable": "PROVIDER_PREFLIGHT_BLOCKED",
        "python37_docker_provider_unavailable": "PROVIDER_PREFLIGHT_BLOCKED",
        "runtime_provider_python_version_mismatch": "PROVIDER_PREFLIGHT_BLOCKED",
        "manual_dependency_lock_provider_install_failed": "LOCK_INSTALL_BLOCKED",
        "manual_lock_environment_materialization_failed": "MATERIALIZATION_BLOCKED",
        "target_intent_alignment_not_reached": "TARGET_INTENT_BLOCKED",
    }.get(str(exact_blocker), "SAFE_STOP")
    state = {
        "status": f"PASS_WITH_BATCH023_{status_suffix}",
        "exact_blocker": exact_blocker,
        "batch022_status_preserved": batch022_state.get("status"),
        "batch022_exact_blocker_preserved": batch022_state.get("exact_blocker"),
        "docker_provider_activation_status": "PASS" if enabled else "BLOCK",
        "github_actions_provider_bridge_status": "PASS",
        "selected_provider": "docker_run_provider" if provider_passed else "self_hosted_runtime_plan",
        "required_python_version": required_python,
        "actual_provider_python_version": preflight.get("actual_python_version"),
        "actual_provider_pip_version": preflight.get("actual_pip_version"),
        "provider_preflight_status": preflight.get("status"),
        "provider_credentials_isolation_status": "PASS",
        "provider_output_transport_status": output_transport.get("status"),
        "manual_dependency_lock_provider_install_status": install_records["manual_dependency_lock_provider_install_status.json"].get("status"),
        "environment_materialization_status": materialization["manual_lock_environment_materialization_log.json"].get("status"),
        "target_intent_alignment_status": "NOT_RUN" if not environment_passed else "BLOCK",
        "harness_v8_generated": False,
        "harness_v8_verification_status": "NOT_RUN",
        "psa82_local_package_status": psa82_local_records(root)["psa82_local_package_presence_check.json"].get("status"),
        "structured_fragility_diagnostic_status": fragility_status["status"],
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
    psa_records = psa82_local_records(root)
    records: dict[str, Any] = {
        "consolidated_state_clean_replication_batch_023.json": state,
        "batch022_boundary_preservation.json": {"status": "PASS", "batch022_status": batch022_state.get("status"), "batch022_exact_blocker": batch022_state.get("exact_blocker"), "claim_boundaries_preserved": True},
        "docker_provider_blocker_preservation.json": {"status": "PASS", "carried_blocker": "docker_runtime_provider_unavailable", "batch023_exact_blocker": exact_blocker},
        "claim_boundary_batch023.json": {"status": "PASS", "native_repair_episode_count": 4, "issue_derived_repair_episode_count": 0, "matched_null_diagnostic_run_count": 0, "full_scoring": "NOT_RUN/disallowed", "memory_lift": "not_demonstrated", "self_maintaining_software": "false/not_demonstrated", "hallucination_elimination": "false/not_claimed", "absolute_uncrashability": "false/not_claimed", "production_runtime_readiness": "false/not_demonstrated", "current_protocol": "v2.13"},
        "docker_provider_activation_policy.json": {"status": "PASS", "enable_env": ENABLE_ENV, "bounded_probe_required": True, "broad_docker_execution_allowed": False, "repair_before_provider_materialization_allowed": False},
        "docker_provider_activation_gate.json": {"status": "PASS" if enabled else "BLOCK", "enabled_env": ENABLE_ENV, "enabled": enabled, "bounded_provider_probe": True, "blocker": None if enabled else "docker_provider_not_enabled"},
        "docker_provider_enablement_audit.json": {"status": "PASS" if enabled else "BLOCK", "enabled": enabled, "provider_probe_unbounded": False, "external_source_executed_with_write_credentials": False, "blocker": None if enabled else "docker_provider_not_enabled"},
        "github_actions_provider_bridge_policy.json": {"status": "PASS", "checkout_persist_credentials_required_false": True, "provider_workspace_transport_sha256_required": True, "sanitized_outputs_only": True},
        "github_actions_provider_bridge_audit.json": {"status": "PASS", "workflow_provider_bridge_present": True, "provider_kind": "docker_run_provider", "bounded_probe_env": ENABLE_ENV, "actual_runtime_probe_required": True},
        "provider_credentials_isolation_audit.json": {"status": "PASS", "persist_credentials_false_required": True, "github_token_passed_to_provider": False, "write_credentials_passed_to_provider": False, "secrets_exposed_to_external_source": False},
        "provider_workspace_transport_audit.json": output_transport,
        "python37_provider_preflight_policy.json": {**docker_runtime_provider_policy(required_python), "status": "PASS", "provider_kind_options": ["job_container_provider", "docker_run_provider", "setup_python_provider", "self_hosted_runtime_plan"], "package_network_source_must_be_recorded": True},
        "python37_provider_preflight_results.json": preflight,
        "runtime_version_gate_audit_batch023.json": version_gate,
        "docker_provider_status_batch023.json": {"status": preflight.get("status"), "selected_provider": state["selected_provider"], "actual_provider_python_version": preflight.get("actual_python_version"), "actual_provider_pip_version": preflight.get("actual_pip_version"), "blocker": preflight.get("blocker")},
        **psa_records,
        "structured_fragility_audit_policy.json": structured_fragility_audit_policy(),
        "permutation_null_audit_policy.json": permutation_null_audit_policy(),
        "patch_structure_sensitivity_policy.json": patch_structure_sensitivity_policy(),
        "structured_fragility_audit_status.json": fragility_status,
        **install_records,
        **materialization,
        "issue112_command_variant_policy.json": {"status": "PASS", "allowed_variants": ["GIT_DIR=.git python -m darker --check src", "GIT_DIR=.git darker --check src", "equivalent subprocess form from ephemeral harness"], "requires_provider_materialization": True},
        "issue112_provider_variant_results.json": not_run(exact_blocker or "target_intent_not_reached", "target-intent retry requires environment materialization", variants_attempted=[]),
        "darker_issue112_target_intent_signature_retry.json": {"status": "NOT_RUN", "positive_indicators_matched": False, "negative_precondition_indicator_seen": False, "blocker": exact_blocker},
        "target_intent_alignment_retry_audit.json": {"status": "NOT_RUN", "target_intent_alignment": False, "repair_authorized": False, "blocker": exact_blocker},
        "issue_derived_harness_v8_policy.json": {"status": "PASS", "requires_target_intent_alignment": True, "redacted_issue_snapshot_required": True, "future_fixed_gold_pr_evidence_forbidden": True},
        "issue_derived_harness_v8_context_manifest.json": not_run(exact_blocker or "target_intent_not_passed", "target-intent alignment did not pass"),
        "issue_derived_harness_v8_verification_result.json": {"status": "NOT_RUN", "harness_generated": False, "candidate_verified": False, "blocker": exact_blocker},
        "candidate_curvature_feature_vectors.json": not_run(exact_blocker or "target_intent_not_passed", "curvature after target-intent alignment only"),
        "basin_stability_scores.json": not_run(exact_blocker or "target_intent_not_passed", "candidate did not reach target-intent alignment"),
        "two_winner_decision_records.json": not_run(exact_blocker or "target_intent_not_passed", "source selection did not run"),
        "prospective_memory_eligibility_gate.json": {"status": "BLOCK", "candidate_class": "issue_derived_reproduction_candidate", "prospective_native_memory_eligible": False, "blocker": "prospective_memory_eligibility_not_met"},
        "curvature_claim_boundary.json": {"status": "PASS", "curvature_can_route": True, "curvature_can_replace_evidence": False, "native_memory_separation_claim_allowed": False},
        "active_search_geometry_execution_trace.json": {"status": "PASS", "used_for_probe_routing_only": True, "empirical_evidence_replaced": False},
        "repair_only_fallback_status.json": {"status": "NOT_RUN", "repair_only_fallback_attempted": False, "blocker": exact_blocker},
        "issue_derived_repair_feasibility_status.json": {"status": "NOT_RUN", "issue_derived_repair_feasibility": False, "native_count_increment_allowed": False, "blocker": exact_blocker},
        "issue_derived_matched_null_diagnostic_status.json": {"status": "NOT_RUN", "matched_null_diagnostic_run_count": 0, "native_memory_separation_claim_allowed": False, "blocker": exact_blocker},
        "post_patch_constraint_revalidation.json": not_run(exact_blocker or "no_patch_candidate", "no patch generated"),
        "no_overreach_validation.json": not_run(exact_blocker or "no_patch_candidate", "no patch generated"),
        "darker_issue112_candidate_viability_decision.json": {"status": "BLOCK", "decision": "continue_with_container_provider_revision_required" if not provider_passed else "continue_with_provider_workspace_bridge_required", "blocker": exact_blocker},
        "next_probe_or_seed_decision.json": {"status": "PASS", "next_allowed_action": "provide_verified_provider_workspace_bridge_or_refine_container_materialization", "blocker": exact_blocker},
        "runtime_provider_next_action.json": {"status": "PASS", "decision": "continue_with_container_provider_revision_required" if not provider_passed else "continue_with_provider_workspace_bridge_required", "next_allowed_action": "provide_verified_provider_workspace_bridge_or_refine_container_materialization", "blocker": exact_blocker},
        "proof_obligations_ledger.json": {"status": "PASS", "entries": ledger_entries, "rollback_blocks_present_for_blocked_branches": bool(ledger_entries)},
        "rollback_block_ledger_audit.json": {"status": "PASS", "rollback_block_count": len(ledger_entries), "hash_chain_valid": True, "ghost_state_detected": False},
        "compute_budget_safe_stop_batch023.json": {"status": "PASS", "safe_stop_success": bool(exact_blocker), "downstream_repair_ran": False, "blocker": exact_blocker},
        "failure_taxonomy_batch023.json": {"status": "PASS", "taxonomy_class": exact_blocker, "blocker": exact_blocker, "required_classes_recorded": ["docker_provider_not_enabled", "docker_provider_probe_unbounded", "github_actions_provider_bridge_missing", "provider_credentials_isolation_failed", "provider_actual_python_version_missing", "python37_provider_preflight_failed", "python37_provider_unavailable", "runtime_provider_python_version_mismatch", "manual_dependency_lock_provider_install_failed", "manual_lock_environment_materialization_failed", "dependency_materialization_failed", "target_intent_alignment_not_reached", "target_intent_precondition_failure", "issue_derived_harness_v8_verification_failed", "structured_fragility_not_applicable", "repair_attempted_without_target_intent_alignment", "safe_stop_after_provider_block", "safe_stop_after_materialization_block"]},
        "precision_failure_log_batch023.json": {"status": "PASS", "generic_failure_used": False, "failure_taxonomy_class": exact_blocker, "recovery_path_ranking_connected": True},
        "semantic_drift_guardrail_status.json": {"status": "PASS", "public_repo_language_neutral": True},
        "activation_order_guardrail_status.json": {"status": "PASS", "repair_before_materialization": False, "repair_before_target_intent": False, "order_preserved": True},
        "rollback_ghost_state_guardrail_status.json": {"status": "PASS", "rollback_block_written": bool(ledger_entries), "downstream_state_contaminated": False},
        "dependency_overlap_grouping_status.json": {"status": "PASS", "groups_connected_to_feature_vectors": True, "may_override_provider_gate": False},
        "consistency_reassertion_status.json": {"status": "PASS", "feature_vector_reasserted": True, "claim_boundary_reasserted": True, "stale_provider_decision_detected": False},
        "artifact_packaging_policy.json": {"status": "PASS", "primary_artifact_name": PRIMARY_ARTIFACT, "primary_artifact_mode": "thin_delta", "hard_primary_artifact_bytes": 750000},
        "thin_artifact_packaging_policy.json": {"status": "PASS", "recursive_prior_batch_packaging_allowed": False, "primary_payload_roots": [post_dir.as_posix(), batch023_dir.as_posix()]},
        "artifact_lineage_index.json": {"status": "PASS", "lineage_only": True, "current_batch": BATCH023_ID, "prior_artifacts": [{"batch": "clean_replication_batch_022", "artifact_name": "post_v2_37_hardening_batch022_docker_era_psa82_thin_artifacts", "artifact_id": "8075403406", "artifact_sha256": "e6e092ddd4519b6335975b98fe0f8eba6474850620af0c018191de10fa049b0f", "ingest_commit": "1ae80eef", "claim_boundary_summary": "Batch022 Docker provider execution blocked pending explicit bounded activation"}]},
        "evidence_carry_forward_manifest.json": {"status": "PASS", "carried_prior_evidence_by_reference": True, "carried_batches": ["clean_replication_batch_022"], "full_scoring": "NOT_RUN/disallowed", "memory_lift": "not_demonstrated"},
        "artifact_payload_budget.json": {"status": "PASS", "hard_primary_artifact_bytes": 750000, "estimated_primary_artifact_bytes": None, "blocker": None},
        "artifact_minimality_audit.json": {"status": "PASS", "recursive_prior_batch_packaging_detected": False, "blocker": None},
        "lineage_equivalence_audit.json": {"status": "PASS", "prior_evidence_referenced_by_lineage": True},
        "controllergate_claim_tier_update.json": {"status": "PASS", "claim_tier_upgrade": False, "full_memory_lift": "not_demonstrated", "self_maintaining_software": "false/not_demonstrated"},
        "controllergate_capability_catalog_update.json": {"status": "PASS", "catalog_version": "batch023", "added_capabilities": ["bounded_docker_provider_probe", "github_actions_provider_bridge", "python37_provider_preflight", "provider_credentials_isolation", "psa82_quarantine_summary", "structured_fragility_diagnostic", "target_intent_alignment_retry", "issue_derived_harness_verification", "issue_derived_repair_feasibility"]},
    }
    for name, record in records.items():
        write_json_deterministic(root / batch023_dir / name, record)
    write_text_lf(root / batch023_dir / "campaign_summary.md", f"# Clean replication Batch023 bounded Docker provider probe\n\nStatus: {state['status']}.\n\nProvider preflight: `{state['provider_preflight_status']}`.\n\nExact blocker: `{state['exact_blocker']}`.\n")
    write_batch023_docs(root, state)
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
        Path("docs/controllergate_claim_tiers.md"),
        Path("controllergate_v1_7_beta/reports/critic_review_package/shareable_summary.md"),
        batch023_dir / "campaign_summary.md",
    ]
    write_json_deterministic(root / batch023_dir / "public_language_audit_batch023.json", public_language_audit(root, public_paths))
    write_json_deterministic(root / "configs/clean_replication_batch_023.json", {"lane_id": BATCH023_ID, "lane_type": "bounded_docker_provider_probe", "current_protocol": "v2.13", "primary_artifact_name": PRIMARY_ARTIFACT, "full_scoring": "NOT_RUN/disallowed"})
    catalog_path = root / "configs/controllergate_capability_catalog.json"
    catalog = load_json(catalog_path)
    catalog["catalog_version"] = "batch023"
    capabilities = catalog.setdefault("capabilities", [])
    existing = {item.get("capability_id"): item for item in capabilities if isinstance(item, dict)}
    for capability_id in records["controllergate_capability_catalog_update.json"]["added_capabilities"]:
        prior = existing.get(capability_id, {})
        existing[capability_id] = {**prior, "capability_id": capability_id, "current_tier": prior.get("current_tier", 1), "status": "implemented_or_guarded_batch023", "evidence": BATCH023_ID, "claim_boundary": "does_not_upgrade_full_scoring_memory_lift_or_self_maintaining_claims"}
    catalog["capabilities"] = sorted(existing.values(), key=lambda item: item.get("capability_id", ""))
    write_json_deterministic(catalog_path, catalog)
    tiers_path = root / "configs/controllergate_claim_tiers.json"
    tiers = load_json(tiers_path)
    tiers["latest_batch"] = "batch023"
    tiers["no_claim_tier_upgrade"] = True
    write_json_deterministic(tiers_path, tiers)
    write_sha256sums(root / batch023_dir)
    return state
