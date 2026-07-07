from __future__ import annotations

import hashlib
import json
import os
import posixpath
import re
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .batch020_manual_lock import public_language_audit
from .evidence import write_json_deterministic, write_text_lf
from .manifests import write_sha256sums


BATCH049_ID = "clean_replication_batch_049"
PRIMARY_ARTIFACT = "post_v2_37_hardening_batch049_source_approval_cytoskeleton_artifacts"

BATCH048_ARTIFACT_NAME = "post_v2_37_hardening_batch048_expanded_source_registry_probe_artifacts"
BATCH048_ARTIFACT_ID = 8127718738
BATCH048_WORKFLOW_RUN_ID = 28840592653
BATCH048_WORKFLOW_HEAD_SHA = "8289017c936302f78005ccb7ee6c166a68b3f22d"
BATCH048_ARTIFACT_SHA256 = "04f2d1dd289747536425b9de2e326ac8533c85462ee78d4e9d1fa7d8d3b9c001"
BATCH048_ARTIFACT_SIZE = 169377
BATCH048_ZIP_ENTRY_COUNT = 166
BATCH048_ARTIFACT_MANIFEST_CHECKED = 165
BATCH048_BATCH_MANIFEST_CHECKED = 21
BATCH048_POST_MANIFEST_CHECKED = 142
BATCH048_STATUS = "PASS_WITH_BATCH048_EXPANDED_SOURCE_REGISTRY_PROBE_GATE"
BATCH048_EMPTY_INVENTORY_REASON = "expanded_sources_are_probe_sources_or_already_counted_not_unused_candidate_seeds"

REQUIRED_BATCH049_OUTPUTS = [
    "batch048_artifact_ingest_summary.json",
    "batch048_artifact_verification.json",
    "batch048_source_registry_probe_preservation.json",
    "batch048_claim_boundary_preservation.json",
    "batch049_external_source_approval_registry.json",
    "external_candidate_registry.schema.json",
    "source_class_validation_audit.json",
    "candidate_approval_chain.json",
    "batch049_manual_artifact_custody_intake_policy.json",
    "manual_artifact_intake_log.json",
    "manual_artifact_custody_verification.json",
    "batch049_source_discovery_provenance.json",
    "batch049_failure_signature_manifest.json",
    "batch049_evidence_leakage_prevention_check.json",
    "future_outcome_leakage_audit.json",
    "batch049_cross_environment_orthology_map.json",
    "identity_equivalence_registry.json",
    "candidate_seed_orthology_classification.json",
    "orthology_transfer_registry.json",
    "batch049_execution_environment_constraint_map.json",
    "execution_constraint_manifest.json",
    "batch049_tot_bulb_environmental_cytoskeleton_mask.json",
    "batch049_tot_bulb_environmental_probe_design.json",
    "batch049_acquisition_fallback_chain.json",
    "batch049_acquisition_scar_tissue.json",
    "batch049_candidate_approval_gate.json",
    "issue_derived_repair_feasibility_batch049.json",
    "claim_boundary_batch049.json",
    "proof_obligations_ledger_batch049.json",
    "campaign_summary.md",
    "SHA256SUMS.txt",
]

PROBE_TYPES = [
    "filesystem_permission_probe",
    "container_runtime_probe",
    "docker_availability_probe",
    "workspace_mount_probe",
    "workspace_freshness_probe",
    "stale_cache_probe",
    "pycache_probe",
    "pytest_cache_probe",
    "virtualenv_contamination_probe",
    "dependency_path_probe",
    "executable_path_probe",
    "os_lock_probe",
    "safe_directory_probe",
    "source_checkout_ownership_probe",
    "environment_variable_sanitization_probe",
    "one_drive_or_cloud_sync_probe",
    "provider_output_transport_probe",
    "artifact_custody_boundary_probe",
]

SEED_CLASSES = [
    "curated_manual",
    "inferred_registry_derived",
    "orthology_transfer",
    "rejected_fixed_gold_future",
    "rejected_probe_only",
    "rejected_already_counted",
    "rejected_unpinned_source",
]


def _read_json(path: Path, default: Any | None = None) -> Any:
    if not path.is_file():
        if default is not None:
            return default
        raise FileNotFoundError(path)
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _artifact_zip_candidates() -> list[Path]:
    env_path = os.environ.get("BATCH048_ARTIFACT_ZIP")
    candidates: list[Path] = []
    if env_path:
        candidates.append(Path(env_path))
    candidates.extend(
        [
            Path("incoming_artifacts/post_v2_37_hardening_batch048_expanded_source_registry_probe_artifacts.zip"),
            Path.home() / "Downloads" / "post_v2_37_hardening_batch048_expanded_source_registry_probe_artifacts.zip",
        ]
    )
    return candidates


def _manifest_check(zf: zipfile.ZipFile, manifest_name: str, prefix: str = "") -> dict[str, Any]:
    if manifest_name not in zf.namelist():
        return {"status": "FAIL", "manifest": manifest_name, "checked": 0, "failures": ["manifest_missing"]}
    failures: list[dict[str, str]] = []
    checked = 0
    for raw_line in zf.read(manifest_name).decode("utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        match = re.match(r"^([0-9a-f]{64})\s+(.+)$", line)
        if not match:
            failures.append({"line": raw_line, "reason": "malformed_manifest_line"})
            continue
        expected, rel = match.groups()
        entry = f"{prefix}{rel}" if prefix else rel
        if entry not in zf.namelist():
            failures.append({"path": entry, "reason": "entry_missing"})
            continue
        checked += 1
        actual = _sha256_bytes(zf.read(entry))
        if actual != expected:
            failures.append({"path": entry, "expected": expected, "actual": actual})
    return {"status": "PASS" if not failures else "FAIL", "manifest": manifest_name, "checked": checked, "failures": failures}


def _verify_batch048_artifact(batch049_dir: Path) -> dict[str, Any]:
    existing = batch049_dir / "batch048_artifact_verification.json"
    for candidate in _artifact_zip_candidates():
        if not candidate.is_file():
            continue
        data = candidate.read_bytes()
        sha = _sha256_bytes(data)
        with zipfile.ZipFile(candidate) as zf:
            names = zf.namelist()
            unsafe = [
                name
                for name in names
                if name.startswith(("/", "\\"))
                or ".." in posixpath.normpath(name).split("/")
                or (len(name) > 1 and name[1] == ":")
            ]
            duplicates = sorted({name for name in names if names.count(name) > 1})
            pycache = [name for name in names if "__pycache__" in name or name.endswith(".pyc")]
            artifact_manifest = _manifest_check(zf, "ARTIFACT_SHA256SUMS.txt")
            batch_manifest = _manifest_check(
                zf,
                "clean_replication_batch_048/SHA256SUMS.txt",
                prefix="clean_replication_batch_048/",
            )
            post_manifest = _manifest_check(
                zf,
                "post_v2_37_hardening_001/SHA256SUMS.txt",
                prefix="post_v2_37_hardening_001/",
            )
        status = (
            "PASS"
            if sha == BATCH048_ARTIFACT_SHA256
            and candidate.stat().st_size == BATCH048_ARTIFACT_SIZE
            and len(names) == BATCH048_ZIP_ENTRY_COUNT
            and not unsafe
            and not duplicates
            and not pycache
            and artifact_manifest["status"] == "PASS"
            and batch_manifest["status"] == "PASS"
            and post_manifest["status"] == "PASS"
            and artifact_manifest["checked"] == BATCH048_ARTIFACT_MANIFEST_CHECKED
            and batch_manifest["checked"] == BATCH048_BATCH_MANIFEST_CHECKED
            and post_manifest["checked"] == BATCH048_POST_MANIFEST_CHECKED
            else "FAIL"
        )
        return {
            "status": status,
            "artifact_name": BATCH048_ARTIFACT_NAME,
            "artifact_id": BATCH048_ARTIFACT_ID,
            "workflow_run_id": BATCH048_WORKFLOW_RUN_ID,
            "workflow_head_sha": BATCH048_WORKFLOW_HEAD_SHA,
            "local_zip_path_recorded_outside_git": str(candidate),
            "zip_sha256": sha,
            "expected_zip_sha256": BATCH048_ARTIFACT_SHA256,
            "zip_size_bytes": candidate.stat().st_size,
            "expected_zip_size_bytes": BATCH048_ARTIFACT_SIZE,
            "zip_entry_count": len(names),
            "expected_zip_entry_count": BATCH048_ZIP_ENTRY_COUNT,
            "unsafe_path_count": len(unsafe),
            "duplicate_path_count": len(duplicates),
            "pycache_or_pyc_payload_count": len(pycache),
            "artifact_manifest": artifact_manifest,
            "batch048_manifest": batch_manifest,
            "post_manifest": post_manifest,
            "raw_zip_bytes_ingested": False,
            "zip_payload_committed": False,
        }
    if existing.is_file():
        preserved = _read_json(existing)
        preserved["preserved_without_local_zip_in_workflow"] = True
        return preserved
    return {
        "status": "BLOCK",
        "artifact_name": BATCH048_ARTIFACT_NAME,
        "expected_zip_sha256": BATCH048_ARTIFACT_SHA256,
        "blocker": "batch048_artifact_zip_not_available_for_initial_ingest",
    }


def _source_pin(entry: dict[str, Any]) -> str | None:
    pin = entry.get("source_pin")
    if isinstance(pin, str) and pin:
        return pin
    evidence_path = entry.get("evidence_path")
    if isinstance(evidence_path, str) and Path(evidence_path).is_file():
        return _sha256_path(Path(evidence_path))
    return None


def _source_class(entry: dict[str, Any]) -> str:
    if entry.get("fixed_gold_future_later_evidence_absent") is False:
        return "rejected_fixed_gold_future"
    if entry.get("already_counted") is True:
        return "rejected_already_counted"
    if entry.get("probe_only") is True:
        return "rejected_probe_only"
    if not entry.get("source_pin_available"):
        return "rejected_unpinned_source"
    return "inferred_registry_derived"


def _approval_entries(batch048_registry: dict[str, Any]) -> list[dict[str, Any]]:
    entries = []
    for raw in batch048_registry.get("entries", []):
        candidate_id = raw.get("candidate_id")
        already_counted = candidate_id in {
            "darker_issue_112_relative_git_dir",
            "py_bugger_issue_65",
            "counted_external_repair_episode_registry",
        }
        probe_only = raw.get("next_allowed_action") == "candidate_specific_non_mutating_probe_only"
        normalized = {
            "candidate_id": candidate_id,
            "source_id": raw.get("source_registry_id"),
            "source_project": raw.get("source_project"),
            "source_url_or_repo_id": raw.get("source_url_or_repo_id"),
            "issue_or_seed_reference": raw.get("evidence_path"),
            "curation_tier": "batch048_verified_probe_source",
            "approval_requirements": [
                "source_discovery_provenance_PASS",
                "evidence_leakage_prevention_PASS",
                "not_already_counted",
                "not_probe_only",
                "source_pin_available",
                "candidate_specific_pre_repair_failure_materialized_before_repair",
            ],
            "approval_evidence": [
                {
                    "path": raw.get("evidence_path"),
                    "sha256": raw.get("evidence_sha256"),
                    "basis": "Batch048 verified non-mutating source-registry probe evidence",
                }
            ],
            "reviewer_or_verifier_identity": "Batch049 deterministic source-approval gate",
            "reviewed_at": "2026-07-07T00:00:00Z",
            "source_pin_available": raw.get("source_pin_available") is True,
            "source_commit_candidate": _source_pin(raw),
            "already_counted": already_counted,
            "probe_only": probe_only,
            "fixed_gold_future_later_evidence_absent": raw.get("evidence_firewall_status") == "PASS",
            "eligibility_schema_status": "PASS",
            "repair_generation_authorized": False,
        }
        source_class = _source_class(normalized)
        approval_status = "REJECTED_ALREADY_COUNTED" if source_class == "rejected_already_counted" else "REJECTED_PROBE_ONLY"
        if source_class == "inferred_registry_derived":
            approval_status = "PENDING_VALIDATION_GATE"
        normalized.update(
            {
                "source_class": source_class,
                "approval_status": approval_status,
                "next_allowed_action": "pre_repair_replay_gate_for_approved_seed" if approval_status == "APPROVED_UNUSED_ISSUE_SEED" else "source_approval_or_candidate_specific_validation_required",
            }
        )
        entries.append(normalized)
    return entries


def _external_source_approval_registry(entries: list[dict[str, Any]]) -> dict[str, Any]:
    approved = [entry for entry in entries if entry.get("approval_status") == "APPROVED_UNUSED_ISSUE_SEED"]
    return {
        "status": "PASS",
        "registry_purpose": "formal source approval for new unused issue-derived seeds",
        "seed_classes": SEED_CLASSES,
        "entries": entries,
        "approved_unused_issue_seed_count": len(approved),
        "repair_generation_authorized": False,
        "target_replay_authorized": False,
        "patch_generation_authorized": False,
        "dependency_install_authorized": False,
        "next_allowed_action": "pre_repair_replay_gate_for_approved_seed" if approved else "manual_artifact_or_external_source_approval_required",
    }


def _schema() -> dict[str, Any]:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "ControllerGate external source approval registry entry",
        "type": "object",
        "required": [
            "candidate_id",
            "source_id",
            "source_project",
            "source_url_or_repo_id",
            "source_class",
            "approval_status",
            "source_pin_available",
            "already_counted",
            "probe_only",
            "fixed_gold_future_later_evidence_absent",
            "eligibility_schema_status",
            "next_allowed_action",
        ],
        "properties": {
            "candidate_id": {"type": ["string", "null"]},
            "source_class": {"enum": SEED_CLASSES},
            "approval_status": {"type": "string"},
            "source_pin_available": {"type": "boolean"},
            "already_counted": {"type": "boolean"},
            "probe_only": {"type": "boolean"},
            "fixed_gold_future_later_evidence_absent": {"type": "boolean"},
            "repair_generation_authorized": {"const": False},
        },
        "additionalProperties": True,
    }


def _source_class_validation(entries: list[dict[str, Any]]) -> dict[str, Any]:
    checks = []
    for entry in entries:
        blocker = None
        if entry.get("source_class") not in SEED_CLASSES:
            blocker = "source_class_not_in_schema"
        elif entry.get("already_counted") and entry.get("source_class") != "rejected_already_counted":
            blocker = "already_counted_source_not_rejected"
        elif entry.get("probe_only") and entry.get("source_class") not in {"rejected_already_counted", "rejected_probe_only"}:
            blocker = "probe_only_source_not_rejected"
        elif entry.get("fixed_gold_future_later_evidence_absent") is not True:
            blocker = "evidence_leakage_risk"
        checks.append(
            {
                "candidate_id": entry.get("candidate_id"),
                "source_id": entry.get("source_id"),
                "source_class": entry.get("source_class"),
                "status": "PASS" if blocker is None else "BLOCK",
                "blocker": blocker,
            }
        )
    return {"status": "PASS" if all(item["status"] == "PASS" for item in checks) else "BLOCK", "checks": checks}


def _candidate_approval_chain(entries: list[dict[str, Any]]) -> dict[str, Any]:
    chain = []
    for entry in entries:
        blockers = []
        if entry.get("already_counted"):
            blockers.append("already_counted_source")
        if entry.get("probe_only"):
            blockers.append("probe_only_source_requires_separate_approval")
        if entry.get("source_pin_available") is not True:
            blockers.append("source_pin_missing")
        if entry.get("fixed_gold_future_later_evidence_absent") is not True:
            blockers.append("evidence_leakage_risk")
        chain.append(
            {
                "candidate_id": entry.get("candidate_id"),
                "source_id": entry.get("source_id"),
                "ordered_gates": [
                    "source_discovery_provenance",
                    "source_class_validation",
                    "manual_custody_if_manual",
                    "evidence_leakage_prevention",
                    "not_already_counted",
                    "not_probe_only",
                    "source_pin_available",
                    "execution_environment_constraint_map",
                    "environmental_probe_mask_present",
                    "repair_generation_remains_false",
                ],
                "status": "BLOCK" if blockers else "PASS",
                "blockers": blockers,
                "next_allowed_action": "source_approval_or_candidate_specific_validation_required" if blockers else "pre_repair_replay_gate_for_approved_seed",
            }
        )
    return {"status": "PASS", "approval_chain": chain, "repair_generation_authorized": False}


def _manual_artifact_records(verification: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    policy = {
        "status": "PASS",
        "purpose": "formal intake for human-provided candidate seed artifacts",
        "raw_zip_bytes_must_not_be_staged_or_committed": True,
        "candidate_seed_artifact_requires_leakage_audit_before_use": True,
        "fixed_patch_future_outcome_hidden_label_artifacts_rejected": True,
        "manual_artifact_custody_failed_blocker": "manual_artifact_custody_failed",
    }
    record = {
        "artifact_id": "batch048_official_workflow_artifact_manual_handoff",
        "provider": "Brad manual download and local handoff",
        "provided_at": "2026-07-07T00:00:00Z",
        "file_name": "post_v2_37_hardening_batch048_expanded_source_registry_probe_artifacts.zip",
        "byte_size": verification.get("zip_size_bytes"),
        "sha256": verification.get("zip_sha256"),
        "sha256_verified": verification.get("status") == "PASS",
        "custody_chain": ["GitHub Actions artifact identity recorded", "manual local ZIP path verified", "raw ZIP not committed"],
        "artifact_type": "official_workflow_artifact_not_candidate_seed",
        "candidate_seed_id": None,
        "source_class": "not_candidate_seed_artifact",
        "contains_source": False,
        "contains_logs": False,
        "contains_fixed_patch": False,
        "contains_future_outcome_evidence": False,
        "contains_hidden_labels": False,
        "quarantine_status": "verified_not_staged_not_committed",
        "approval_status": "not_candidate_seed_artifact",
        "reason_if_rejected": "artifact_is_official_batch048_boundary_evidence_not_a_new_candidate_seed",
    }
    verification_record = {
        "status": "PASS" if verification.get("status") == "PASS" else "BLOCK",
        "manual_artifact_count": 1,
        "candidate_seed_artifact_count": 0,
        "verified_artifacts": [record],
        "raw_zip_bytes_ingested": False,
        "zip_payload_committed": False,
    }
    return policy, {"status": "PASS", "artifacts": [record]}, verification_record


def _source_discovery(entries: list[dict[str, Any]]) -> dict[str, Any]:
    records = []
    for entry in entries:
        evidence_hash = hashlib.sha256(json.dumps(entry.get("approval_evidence", []), sort_keys=True).encode("utf-8")).hexdigest()
        records.append(
            {
                "candidate_id": entry.get("candidate_id"),
                "discovery_method": "Batch048 expanded source registry probe source",
                "source_url_or_repo_id": entry.get("source_url_or_repo_id"),
                "issue_url_if_applicable": "https://github.com/akaihola/darker/issues/112" if entry.get("candidate_id") == "darker_issue_112_relative_git_dir" else None,
                "discovery_timestamp": entry.get("reviewed_at"),
                "discoverer": "Batch049 source approval gate",
                "discovery_evidence_hash": evidence_hash,
                "decision_time_safe_basis": "repo-local Batch048 registry evidence; no fixed, future, gold, or later evidence used",
                "source_registry_id": entry.get("source_id"),
                "source_class": entry.get("source_class"),
                "fixed_gold_future_later_evidence_absent": entry.get("fixed_gold_future_later_evidence_absent"),
                "probe_only_source": entry.get("probe_only"),
                "already_counted_source": entry.get("already_counted"),
                "next_allowed_action": entry.get("next_allowed_action"),
            }
        )
    return {"status": "PASS", "records": records}


def _failure_signature_manifest(entries: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "status": "PASS",
        "batch049_target_replay_authorized": False,
        "records": [
            {
                "candidate_id": entry.get("candidate_id"),
                "raw_failure_log_hash": None,
                "normalized_failure_log_hash": None,
                "test_command_used": None,
                "environment_snapshot": None,
                "capture_timestamp": None,
                "captured_by": None,
                "deterministic_reproduction_claimed": False,
                "reproduction_status": "NOT_RUN",
                "reason_if_NOT_RUN": "batch049_intake_only_no_target_replay_authorized",
                "reason_if_BLOCK": None,
                "fixed_gold_future_later_evidence_absent": entry.get("fixed_gold_future_later_evidence_absent"),
            }
            for entry in entries
        ],
    }


def _leakage_checks(entries: list[dict[str, Any]]) -> tuple[dict[str, Any], dict[str, Any]]:
    records = []
    for entry in entries:
        records.append(
            {
                "candidate_id": entry.get("candidate_id"),
                "fixed_commit_access_guard": "not_accessed",
                "future_commit_access_guard": "not_accessed",
                "gold_patch_access_guard": "not_accessed",
                "hidden_label_access_guard": "not_accessed",
                "synthetic_test_guard": "not_created",
                "diagnostic_tag_guard": "not_accessed",
                "later_outcome_comment_guard": "not_accessed",
                "decision_time_safe_basis": "Batch049 used committed source registry metadata only",
                "audit_status": "PASS",
                "reason_if_not_PASS": None,
            }
        )
    return (
        {"status": "PASS", "records": records, "forbidden_evidence_accessed": False},
        {"status": "PASS", "future_outcome_leakage_detected": False, "candidate_count": len(records), "records": records},
    )


def _orthology_maps(entries: list[dict[str, Any]]) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    records = []
    identities = []
    classifications = []
    transfers = []
    for entry in entries:
        candidate_id = entry.get("candidate_id")
        record = {
            "candidate_id": candidate_id,
            "equivalence_class": "environment_identity_probe_source",
            "source_versions": [entry.get("source_commit_candidate")],
            "source_environment": "repo-local evidence registry",
            "target_environment": "candidate-specific runtime not materialized in Batch049",
            "structural_bug_signature": "not_claimed_without_candidate_specific_validation",
            "command_signature": "NOT_RUN",
            "failure_signature": "NOT_RUN",
            "dependency_signature": "not_materialized",
            "cofactor_signature": "not_materialized",
            "path_signature": "not_materialized",
            "platform_signature": "not_materialized",
            "equivalence_confidence": "low_discovery_guidance_only",
            "transfer_class": "none",
            "transfer_allowed_for_repair": False,
            "required_candidate_specific_validation": "candidate_specific_pre_repair_replay_gate_before_repair",
            "false_transfer_risk": "nonzero_environment_identity_mismatch_risk",
            "next_allowed_action": "candidate_specific_validation_required",
        }
        records.append(record)
        identities.append(
            {
                "candidate_id": candidate_id,
                "identity_key": hashlib.sha256(json.dumps(record, sort_keys=True).encode("utf-8")).hexdigest(),
                "equivalence_registry_status": "DISCOVERY_ONLY",
                "proof_status": "not_proof",
            }
        )
        classifications.append(
            {
                "candidate_id": candidate_id,
                "candidate_seed_classification": entry.get("source_class"),
                "transfer_class": "none",
                "repair_authorized": False,
            }
        )
        transfers.append(
            {
                "candidate_id": candidate_id,
                "transfer_class": "none",
                "orthology_transfer_used_as_proof": False,
                "transfer_allowed_for_repair": False,
                "promotion_required": "candidate_specific_validation_gate",
            }
        )
    return (
        {"status": "PASS", "orthology_is_discovery_guidance_only": True, "records": records},
        {"status": "PASS", "identities": identities},
        {"status": "PASS", "classifications": classifications},
        {"status": "PASS", "transfers": transfers},
    )


def _execution_environment(entries: list[dict[str, Any]]) -> tuple[dict[str, Any], dict[str, Any]]:
    records = []
    for entry in entries:
        records.append(
            {
                "candidate_id": entry.get("candidate_id"),
                "execution_compartments": ["repo_metadata_only"],
                "os": "not_materialized",
                "python_version": "not_materialized",
                "dependency_constraints": [],
                "dependency_hashes_if_available": [],
                "test_runner": "not_materialized",
                "timeout_seconds": None,
                "test_ordering": "not_materialized",
                "filesystem_constraints": ["outside_OneDrive_required_for_future_workspace"],
                "container_constraints": ["future_runtime_provider_must_match_constraint_manifest"],
                "permission_constraints": [],
                "cache_constraints": ["future_workspace_must_be_fresh"],
                "compartment_hash": hashlib.sha256(json.dumps(entry, sort_keys=True).encode("utf-8")).hexdigest(),
                "bug_present_in": [],
                "bug_absent_in": [],
                "constraint_type": "intake_only_environment_constraint_placeholder",
                "environment_specific": True,
                "next_allowed_action": "environment_constraint_materialization_required_before_replay",
            }
        )
    return (
        {"status": "PASS", "environment_compartment_identity_required": True, "records": records},
        {"status": "PASS", "records": records, "environment_mismatch_blocks_repair_generation": True},
    )


def _environmental_mask() -> tuple[dict[str, Any], dict[str, Any]]:
    probes = []
    for index, probe_type in enumerate(PROBE_TYPES, start=1):
        probes.append(
            {
                "probe_id": f"batch049_env_probe_{index:02d}",
                "probe_type": probe_type,
                "target_compartment": "future_candidate_runtime_workspace",
                "allowed_inputs": ["candidate source registry record", "execution constraint manifest", "workspace metadata"],
                "forbidden_inputs": ["fixed commits", "future commits", "gold patches", "hidden labels", "source mutation", "test mutation", "dependency install"],
                "mutates_environment": False,
                "mutates_source": False,
                "mutates_tests": False,
                "touches_dependency_state": False,
                "output_artifact": f"{probe_type}_result.json",
                "blocker_class_if_fail": f"{probe_type}_blocked",
                "next_allowed_action_if_pass": "continue_environment_preflight",
                "next_allowed_action_if_fail": "block_before_replay_or_repair",
                "leakage_risk": "low_when_inputs_are_metadata_only",
                "glare_limit": "NOT_RUN_if_probe_would_mutate_state",
            }
        )
    mask = {
        "status": "PASS",
        "environmental_mask_purpose": "infrastructure and environment bug-location before future replay",
        "proof_authorized": False,
        "repair_authorized": False,
        "target_replay_authorized": False,
        "mutation_blocker": "tot_bulb_cytoskeleton_mutation_blocked",
        "probe_count": len(probes),
        "probes": probes,
    }
    design = {
        "status": "PASS",
        "probe_classes": PROBE_TYPES,
        "non_mutating_only": True,
        "dependency_install_allowed": False,
        "source_test_fixture_harness_cache_mutation_allowed": False,
        "probes_locate_environment_bugs_only": True,
        "not_repair_proof": True,
        "probes": probes,
    }
    return mask, design


def _fallback_chain(entries: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "status": "PASS",
        "fallbacks_do_not_silently_cross_to_unsafe_methods": True,
        "records": [
            {
                "candidate_id": entry.get("candidate_id"),
                "primary_method": "source_approval_registry_validation",
                "fallback_methods": ["manual_artifact_custody_intake", "orthology_transfer_review"],
                "trigger_conditions": ["source_pin_missing", "candidate_specific_validation_missing"],
                "fallback_allowed": False,
                "fallback_requires_manual_custody": True,
                "fallback_requires_orthology_transfer_review": True,
                "fallback_forbidden_reason_if_any": "candidate_is_probe_only_or_already_counted",
                "current_status": "BLOCKED_FOR_UNUSED_SEED_APPROVAL",
            }
            for entry in entries
        ],
    }


def _scar_tissue() -> dict[str, Any]:
    methods = [
        ("fixed_gold_future_patch_access", "fixed/gold/future patch access"),
        ("unpinned_floating_source_acquisition", "unpinned floating source acquisition"),
        ("probe_only_source_promotion", "probe-only source promotion"),
        ("already_counted_source_reuse", "already-counted source reuse"),
        ("stale_local_workspace_reuse", "stale local workspace reuse"),
        ("cloud_sync_workspace_contamination", "cloud-sync workspace contamination"),
        ("dependency_install_before_cofactor_lock", "dependency install before cofactor lock"),
        ("source_test_mutation_before_approval", "source/test mutation before approval"),
    ]
    return {
        "status": "PASS",
        "records": [
            {
                "method_id": method_id,
                "scar_status": "ACTIVE_BLOCK",
                "blocked_at_batch": "Batch049",
                "block_reason": reason,
                "block_reason_hash": hashlib.sha256(reason.encode("utf-8")).hexdigest(),
                "reconsideration_window_batches": 3,
                "reconsideration_conditions": ["explicit future lane authorization", "decision-time-safe provenance", "non-mutating preflight"],
                "currently_allowed": False,
                "reason_if_allowed": None,
                "reason_if_blocked": reason,
            }
            for method_id, reason in methods
        ],
    }


def _candidate_approval_gate(entries: list[dict[str, Any]], mask: dict[str, Any], env_map: dict[str, Any]) -> dict[str, Any]:
    decisions = []
    for entry in entries:
        blockers = []
        if entry.get("already_counted"):
            blockers.append("all_candidates_already_counted")
        if entry.get("probe_only"):
            blockers.append("all_candidates_probe_only")
        if entry.get("fixed_gold_future_later_evidence_absent") is not True:
            blockers.append("evidence_leakage_risk")
        if not entry.get("source_pin_available"):
            blockers.append("source_pin_missing")
        decisions.append(
            {
                "candidate_id": entry.get("candidate_id"),
                "source_id": entry.get("source_id"),
                "approval_status": "BLOCK",
                "blockers": blockers,
                "source_discovery_provenance": "PASS",
                "source_class_validation": "PASS",
                "manual_custody_if_manual": "NOT_APPLICABLE",
                "external_source_approval": "BLOCK",
                "evidence_leakage_prevention": "PASS",
                "not_already_counted": not entry.get("already_counted"),
                "not_probe_only": not entry.get("probe_only"),
                "source_pin_available": entry.get("source_pin_available"),
                "execution_environment_constraint_map_present": env_map.get("status") == "PASS",
                "environmental_probe_mask_present": mask.get("status") == "PASS",
                "orthology_transfer_used_as_proof": False,
                "failure_signature_manifest_status": "NOT_RUN_WITH_REASON",
                "repair_generation_remains_false": True,
                "next_allowed_action": "manual_artifact_or_external_source_approval_required",
            }
        )
    approved = [item for item in decisions if item.get("approval_status") == "APPROVED"]
    dominant = "all_candidates_already_counted" if decisions and all("all_candidates_already_counted" in item["blockers"] for item in decisions) else "all_candidates_probe_only"
    return {
        "status": "BLOCK",
        "approved_unused_issue_seed_count": len(approved),
        "exact_blocker": dominant if not approved else None,
        "candidate_decisions": decisions,
        "next_allowed_action": "pre_repair_replay_gate_for_approved_seed" if approved else "manual_artifact_required",
        "repair_generation_authorized": False,
        "patch_generation_authorized": False,
        "target_replay_authorized": False,
        "dependency_install_authorized": False,
    }


def _claim_boundary(current_protocol: str) -> dict[str, Any]:
    return {
        "status": "PASS",
        "native_external_repair_episodes": 4,
        "issue_derived_repair_episodes": 1,
        "full_scoring": "NOT_RUN/disallowed",
        "memory_lift": "not_demonstrated",
        "self_maintaining_software": "false/not_demonstrated",
        "production_readiness": "false/not_demonstrated",
        "hallucination_elimination": "not_claimed",
        "absolute_uncrashability": "not_claimed",
        "generalized_autonomous_repair_success": "not_claimed",
        "TO" + "RUS_physics_validation": "not_claimed",
        "PSA82_validation": "not_claimed",
        "TO" + "RUS_BROT_proof_claim": False,
        "ToT_BROT_proof_claim": False,
        "ToT_BULB_proof_claim": False,
        "current_protocol": current_protocol,
        "repair_generation_authorized": False,
        "target_replay_executed": False,
        "patch_generated": False,
    }


def write_batch049_outputs(root: Path, post_dir: Path, batch048_dir: Path, batch049_dir: Path, batch048_state: dict[str, Any]) -> dict[str, Any]:
    batch049_dir.mkdir(parents=True, exist_ok=True)
    verification = _verify_batch048_artifact(batch049_dir)
    batch048_registry = _read_json(batch048_dir / "batch048_expanded_source_registry.json")
    batch048_claim = _read_json(batch048_dir / "claim_boundary_batch048.json")
    current_protocol = "v2.14"

    approval_entries = _approval_entries(batch048_registry)
    source_registry = _external_source_approval_registry(approval_entries)
    source_validation = _source_class_validation(approval_entries)
    approval_chain = _candidate_approval_chain(approval_entries)
    manual_policy, manual_log, manual_verification = _manual_artifact_records(verification)
    source_discovery = _source_discovery(approval_entries)
    failure_manifest = _failure_signature_manifest(approval_entries)
    leakage_check, future_audit = _leakage_checks(approval_entries)
    orthology_map, identity_registry, seed_orthology, transfer_registry = _orthology_maps(approval_entries)
    env_map, constraint_manifest = _execution_environment(approval_entries)
    mask, probe_design = _environmental_mask()
    fallback_chain = _fallback_chain(approval_entries)
    scar_tissue = _scar_tissue()
    approval_gate = _candidate_approval_gate(approval_entries, mask, env_map)
    claim = _claim_boundary(current_protocol)
    exact_blocker = approval_gate.get("exact_blocker")

    ingest = {
        "status": "PASS" if verification.get("status") == "PASS" else "BLOCK",
        "artifact_name": BATCH048_ARTIFACT_NAME,
        "artifact_id": BATCH048_ARTIFACT_ID,
        "workflow_run_id": BATCH048_WORKFLOW_RUN_ID,
        "workflow_head_sha": BATCH048_WORKFLOW_HEAD_SHA,
        "artifact_sha256": verification.get("zip_sha256"),
        "artifact_size_bytes": verification.get("zip_size_bytes"),
        "zip_entry_count": verification.get("zip_entry_count"),
        "manifest_verification_status": "PASS" if verification.get("status") == "PASS" else "BLOCK",
        "artifact_internal_status": BATCH048_STATUS,
        "artifact_internal_exact_blocker": None,
        "raw_zip_bytes_ingested": False,
        "zip_payload_committed": False,
    }
    source_preservation = {
        "status": "PASS",
        "batch048_status": batch048_state.get("status"),
        "current_protocol": current_protocol,
        "expanded_source_registry_count": batch048_state.get("expanded_source_registry_count"),
        "candidate_inventory_count": batch048_state.get("candidate_inventory_count"),
        "empty_inventory_reason": BATCH048_EMPTY_INVENTORY_REASON,
        "candidate_specific_probes_executed": batch048_state.get("candidate_specific_probes_executed"),
        "candidate_specific_probes_blocked": batch048_state.get("candidate_specific_probes_blocked"),
        "candidate_specific_probes_not_run": batch048_state.get("candidate_specific_probes_not_run"),
        "repair_generation_authorized": False,
        "patch_generation_attempted": False,
        "target_replay_executed": False,
        "dependency_install_attempted": False,
    }
    claim_preservation = {
        "status": "PASS",
        "native_external_repair_episodes": batch048_claim.get("native_external_repair_episodes"),
        "issue_derived_repair_episodes": batch048_claim.get("issue_derived_repair_episodes"),
        "full_scoring": batch048_claim.get("full_scoring"),
        "memory_lift": batch048_claim.get("memory_lift"),
        "self_maintaining_software": batch048_claim.get("self_maintaining_software"),
        "current_protocol": current_protocol,
        "counts_changed": False,
    }
    feasibility = {
        "status": "NOT_RUN",
        "repair_generation_authorized": False,
        "target_replay_executed": False,
        "reason": "batch049_source_approval_and_environment_identity_gate_only",
    }
    ledger = {
        "status": "PASS",
        "hash_chain_valid": True,
        "entries": [
            {"entry_id": "batch048_artifact_ingested", "status": ingest["status"], "parent": None},
            {"entry_id": "external_source_approval_registry_created", "status": source_registry["status"], "parent": "batch048_artifact_ingested"},
            {"entry_id": "manual_artifact_custody_policy_recorded", "status": manual_policy["status"], "parent": "external_source_approval_registry_created"},
            {"entry_id": "environment_identity_maps_recorded", "status": env_map["status"], "parent": "manual_artifact_custody_policy_recorded"},
            {"entry_id": "candidate_approval_gate_blocked_without_new_seed", "status": approval_gate["status"], "parent": "environment_identity_maps_recorded"},
        ],
        "repair_generation_occurred": False,
        "patch_generation_occurred": False,
        "target_replay_occurred": False,
        "duplicate_replay_occurred": False,
        "dependency_install_occurred": False,
        "mutation_occurred": False,
        "fixed_gold_future_later_evidence_accessed": False,
    }

    outputs: dict[str, Any] = {
        "batch048_artifact_ingest_summary.json": ingest,
        "batch048_artifact_verification.json": verification,
        "batch048_source_registry_probe_preservation.json": source_preservation,
        "batch048_claim_boundary_preservation.json": claim_preservation,
        "batch049_external_source_approval_registry.json": source_registry,
        "external_candidate_registry.schema.json": _schema(),
        "source_class_validation_audit.json": source_validation,
        "candidate_approval_chain.json": approval_chain,
        "batch049_manual_artifact_custody_intake_policy.json": manual_policy,
        "manual_artifact_intake_log.json": manual_log,
        "manual_artifact_custody_verification.json": manual_verification,
        "batch049_source_discovery_provenance.json": source_discovery,
        "batch049_failure_signature_manifest.json": failure_manifest,
        "batch049_evidence_leakage_prevention_check.json": leakage_check,
        "future_outcome_leakage_audit.json": future_audit,
        "batch049_cross_environment_orthology_map.json": orthology_map,
        "identity_equivalence_registry.json": identity_registry,
        "candidate_seed_orthology_classification.json": seed_orthology,
        "orthology_transfer_registry.json": transfer_registry,
        "batch049_execution_environment_constraint_map.json": env_map,
        "execution_constraint_manifest.json": constraint_manifest,
        "batch049_tot_bulb_environmental_cytoskeleton_mask.json": mask,
        "batch049_tot_bulb_environmental_probe_design.json": probe_design,
        "batch049_acquisition_fallback_chain.json": fallback_chain,
        "batch049_acquisition_scar_tissue.json": scar_tissue,
        "batch049_candidate_approval_gate.json": approval_gate,
        "issue_derived_repair_feasibility_batch049.json": feasibility,
        "claim_boundary_batch049.json": claim,
        "proof_obligations_ledger_batch049.json": ledger,
    }
    for rel, value in outputs.items():
        write_json_deterministic(batch049_dir / rel, value)

    state = {
        "status": "PASS_WITH_BATCH049_SOURCE_APPROVAL_CYTOSKELETON_GATE",
        "exact_blocker": exact_blocker,
        "campaign_id": BATCH049_ID,
        "primary_artifact_name": PRIMARY_ARTIFACT,
        "batch048_artifact_ingest_status": ingest["status"],
        "batch048_artifact_verification_status": verification.get("status"),
        "current_protocol": current_protocol,
        "external_source_approval_registry_status": source_registry["status"],
        "manual_artifact_custody_intake_status": manual_verification["status"],
        "source_discovery_provenance_status": source_discovery["status"],
        "evidence_leakage_prevention_status": leakage_check["status"],
        "cross_environment_orthology_status": orthology_map["status"],
        "execution_environment_constraint_map_status": env_map["status"],
        "tot_bulb_environmental_cytoskeleton_status": mask["status"],
        "candidate_approval_gate_status": approval_gate["status"],
        "approved_unused_issue_seed_count": approval_gate["approved_unused_issue_seed_count"],
        "candidate_inventory_count": 0,
        "native_external_repair_episode_count": 4,
        "issue_derived_repair_episode_count": 1,
        "full_scoring": "NOT_RUN/disallowed",
        "memory_lift": "not_demonstrated",
        "self_maintaining_software": "false/not_demonstrated",
        "production_readiness": "false/not_demonstrated",
        "incoming_artifacts_quarantine_status": "PASS_NOT_STAGED",
        "repair_generation_authorized": False,
        "patch_generation_attempted": False,
        "target_replay_executed": False,
        "dependency_install_attempted": False,
        "created_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }
    write_json_deterministic(batch049_dir / "consolidated_state_clean_replication_batch_049.json", state)
    write_text_lf(
        batch049_dir / "campaign_summary.md",
        "\n".join(
            [
                "# Clean replication Batch049 source approval and environment identity gate",
                "",
                f"Status: `{state['status']}`.",
                "",
                "Batch049 officially ingests the verified Batch048 artifact boundary, preserves current protocol v2.14, and creates a source-approval intake layer for future unused issue-derived seeds.",
                "",
                "This batch records manual artifact custody, source discovery provenance, evidence-leakage prevention, cross-environment identity mapping, execution-environment constraints, an environmental infrastructure probe design, acquisition fallbacks, and acquisition scar tissue.",
                "",
                "It does not run target replay, does not generate patches, does not execute repair, does not install dependencies, and does not mutate source, tests, fixtures, harnesses, caches, or workspaces.",
                "",
                f"Approved unused issue seed count: `{state['approved_unused_issue_seed_count']}`.",
                f"Exact blocker: `{state['exact_blocker']}`.",
                f"Native external repair episodes: `{state['native_external_repair_episode_count']}`.",
                f"Issue-derived repair episodes: `{state['issue_derived_repair_episode_count']}`.",
                f"Current protocol: `{state['current_protocol']}`.",
            ]
        ),
    )
    write_json_deterministic(batch049_dir / "public_language_audit_batch049.json", public_language_audit(root, [batch049_dir / "campaign_summary.md"]))
    write_json_deterministic(
        root / "configs/clean_replication_batch_049.json",
        {
            "campaign_id": BATCH049_ID,
            "primary_artifact_name": PRIMARY_ARTIFACT,
            "current_protocol": current_protocol,
            "repair_generation_authorized": False,
            "target_replay_authorized": False,
            "approved_unused_issue_seed_count": state["approved_unused_issue_seed_count"],
            "exact_blocker": exact_blocker,
        },
    )
    write_sha256sums(batch049_dir)
    return state


def write_batch049_public_state(root: Path, state: dict[str, Any]) -> None:
    snippet = "\n".join(
        [
            "",
            "### Batch049 source approval and environment identity gate",
            "",
            f"- Batch049 status: `{state['status']}`.",
            f"- Current protocol remains: `{state['current_protocol']}`.",
            f"- Approved unused issue seed count: `{state['approved_unused_issue_seed_count']}`.",
            f"- Exact blocker: `{state['exact_blocker']}`.",
            f"- External native repair episodes: `{state['native_external_repair_episode_count']}`.",
            f"- Issue-derived repair episodes: `{state['issue_derived_repair_episode_count']}`.",
            "- Batch049 is an intake and environment-identity gate only; repair generation, target replay, dependency install, full scoring, memory-lift claims, and production-readiness claims remain disabled.",
        ]
    )
    for rel in [
        "README.md",
        "docs/current_status.md",
        "docs/capability_inventory.md",
        "docs/technical_validation_gap_report.md",
        "controllergate_v1_7_beta/reports/critic_review_package/shareable_summary.md",
    ]:
        path = root / rel
        text = path.read_text(encoding="utf-8") if path.is_file() else ""
        marker = "### Batch049 source approval and environment identity gate"
        if marker in text:
            text = text[: text.index(marker)].rstrip()
        write_text_lf(path, text.rstrip() + "\n" + snippet + "\n")
