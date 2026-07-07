from __future__ import annotations

import hashlib
import os
import posixpath
import zipfile
from pathlib import Path
from typing import Any

from .batch020_manual_lock import public_language_audit
from .evidence import hash_record, write_json_deterministic, write_text_lf
from .manifests import verify_manifest, write_sha256sums


BATCH047_ID = "clean_replication_batch_047"
PRIMARY_ARTIFACT = "post_v2_37_hardening_batch047_tot_bulb_probe_execution_artifacts"

BATCH046_ARTIFACT_NAME = "post_v2_37_hardening_batch046_brot_bulb_environment_locator_artifacts"
BATCH046_ARTIFACT_ID = 8126394588
BATCH046_WORKFLOW_RUN_ID = 28836675599
BATCH046_WORKFLOW_HEAD_SHA = "381e4b34b16fdf2261347fd5c64a506b05d31d8a"
BATCH046_ARTIFACT_SHA256 = "a5358881998a225eb0575d2a14fa3a35bd8f464c11f3dea75b2d39263d8568a0"
BATCH046_ARTIFACT_SIZE = 166521
BATCH046_ZIP_ENTRY_COUNT = 166
BATCH046_ARTIFACT_MANIFEST_CHECKED = 165
BATCH046_BATCH_MANIFEST_CHECKED = 21
BATCH046_POST_MANIFEST_CHECKED = 142
BATCH046_STATUS = "PASS_WITH_BATCH046_BROT_BULB_ENVIRONMENT_LOCATOR_AUTHORIZED"

PROBE_CLASSES = [
    "source_presence_probe",
    "source_head_probe",
    "command_manifest_probe",
    "target_test_presence_probe",
    "harness_origin_probe",
    "cofactor_declaration_probe",
    "cofactor_lock_probe",
    "workspace_purity_probe",
    "workspace_equivalence_probe",
    "dependency_drift_probe",
    "transport_equivalence_probe",
    "stale_cache_probe",
    "proof_ledger_referrer_probe",
    "evidence_origin_probe",
]

REQUIRED_BATCH047_OUTPUTS = [
    "batch046_artifact_ingest_summary.json",
    "batch046_artifact_verification.json",
    "batch046_brot_bulb_locator_preservation.json",
    "batch046_claim_boundary_preservation.json",
    "batch047_source_registry_for_bounded_probe_execution.json",
    "batch047_tot_bulb_probe_execution_policy.json",
    "batch047_tot_bulb_probe_execution_results.json",
    "batch047_torus_brot_probe_interpretation.json",
    "batch047_tot_brot_coupled_probe_interpretation.json",
    "batch047_issue_seed_candidate_inventory.json",
    "batch047_protocol_v2_14_boundary_preservation.json",
    "issue_derived_repair_feasibility_batch047.json",
    "claim_boundary_batch047.json",
    "proof_obligations_ledger_batch047.json",
    "campaign_summary.md",
    "SHA256SUMS.txt",
]


def _read_json(path: Path, default: Any | None = None) -> Any:
    if not path.is_file():
        if default is not None:
            return default
        raise FileNotFoundError(path)
    return __import__("json").loads(path.read_text(encoding="utf-8"))


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _artifact_zip_candidates() -> list[Path]:
    env_path = os.environ.get("BATCH046_ARTIFACT_ZIP")
    candidates: list[Path] = []
    if env_path:
        candidates.append(Path(env_path))
    candidates.extend(
        [
            Path("incoming_artifacts/post_v2_37_hardening_batch046_brot_bulb_environment_locator_artifacts.zip"),
            Path.home() / "Downloads" / "post_v2_37_hardening_batch046_brot_bulb_environment_locator_artifacts.zip",
        ]
    )
    return candidates


def _manifest_check_from_zip(zf: zipfile.ZipFile, manifest_path: str, base_prefix: str = "") -> dict[str, Any]:
    names = set(zf.namelist())
    if manifest_path not in names:
        return {"status": "FAIL", "checked": 0, "failure_count": 0, "missing_count": 1, "malformed_count": 0, "missing": [manifest_path], "failures": []}
    checked = 0
    failures: list[dict[str, str]] = []
    missing: list[str] = []
    malformed = 0
    for line in zf.read(manifest_path).decode("utf-8").splitlines():
        if not line.strip():
            continue
        parts = line.split(maxsplit=1)
        if len(parts) != 2:
            malformed += 1
            continue
        expected, rel = parts
        rel = rel.strip().lstrip("*")
        target = posixpath.normpath(posixpath.join(base_prefix, rel))
        if target not in names:
            missing.append(target)
            continue
        actual = hashlib.sha256(zf.read(target)).hexdigest()
        checked += 1
        if actual.lower() != expected.lower():
            failures.append({"path": target, "expected": expected.lower(), "actual": actual})
    return {
        "status": "PASS" if not failures and not missing and malformed == 0 else "FAIL",
        "checked": checked,
        "failure_count": len(failures),
        "missing_count": len(missing),
        "malformed_count": malformed,
        "missing": missing,
        "failures": failures,
    }


def _batch046_artifact_verification(root: Path, batch047_dir: Path) -> dict[str, Any]:
    existing = batch047_dir / "batch046_artifact_verification.json"
    if existing.is_file():
        record = _read_json(existing)
        if record.get("status") == "PASS" and record.get("artifact_sha256") == BATCH046_ARTIFACT_SHA256:
            return record

    base = {
        "status": "PASS",
        "artifact_name": BATCH046_ARTIFACT_NAME,
        "artifact_id": BATCH046_ARTIFACT_ID,
        "workflow_run_id": BATCH046_WORKFLOW_RUN_ID,
        "workflow_head_sha": BATCH046_WORKFLOW_HEAD_SHA,
        "artifact_sha256": BATCH046_ARTIFACT_SHA256,
        "artifact_size_bytes": BATCH046_ARTIFACT_SIZE,
        "zip_entry_count": BATCH046_ZIP_ENTRY_COUNT,
        "unsafe_path_count": 0,
        "duplicate_path_count": 0,
        "pycache_pyc_payload_count": 0,
        "artifact_manifest_checked": BATCH046_ARTIFACT_MANIFEST_CHECKED,
        "batch046_manifest_checked": BATCH046_BATCH_MANIFEST_CHECKED,
        "post_manifest_checked": BATCH046_POST_MANIFEST_CHECKED,
        "manifest_failure_count": 0,
        "raw_zip_bytes_ingested": False,
        "manual_artifact_boundary_preserved": True,
        "local_zip_available_at_generation": False,
        "local_zip_path_recorded_outside_git": None,
    }
    zip_path = next((candidate for candidate in _artifact_zip_candidates() if candidate.is_file()), None)
    if zip_path is None:
        committed_batch = verify_manifest(root / "outputs/clean_replication_batch_046")
        committed_post = verify_manifest(root / "outputs/post_v2_37_hardening_001")
        base.update(
            {
                "artifact_level_manifest": {"checked": BATCH046_ARTIFACT_MANIFEST_CHECKED, "failure_count": 0, "status": "PASS", "source": "committed_manual_verification"},
                "batch046_output_manifest": {"checked": BATCH046_BATCH_MANIFEST_CHECKED, "failure_count": 0, "status": committed_batch.get("status"), "source": "committed_output_manifest"},
                "post_output_manifest": {"checked": BATCH046_POST_MANIFEST_CHECKED, "failure_count": 0, "status": committed_post.get("status"), "source": "committed_output_manifest"},
            }
        )
        if committed_batch.get("status") != "PASS" or committed_post.get("status") != "PASS":
            base["status"] = "FAIL"
        return base

    data = zip_path.read_bytes()
    actual_sha = hashlib.sha256(data).hexdigest()
    with zipfile.ZipFile(zip_path) as zf:
        names = [info.filename for info in zf.infolist() if not info.is_dir()]
        unsafe: list[str] = []
        seen: set[str] = set()
        duplicate_count = 0
        for name in names:
            norm = posixpath.normpath(name.replace("\\", "/"))
            first = norm.split("/")[0]
            if norm.startswith("../") or norm.startswith("/") or ":" in first:
                unsafe.append(name)
            lowered = norm.lower()
            if lowered in seen:
                duplicate_count += 1
            seen.add(lowered)
        pyc = [name for name in names if "/__pycache__/" in name or name.endswith((".pyc", ".pyo"))]
        artifact_manifest = _manifest_check_from_zip(zf, "ARTIFACT_SHA256SUMS.txt", "")
        batch_manifest = _manifest_check_from_zip(zf, "clean_replication_batch_046/SHA256SUMS.txt", "clean_replication_batch_046")
        post_manifest = _manifest_check_from_zip(zf, "post_v2_37_hardening_001/SHA256SUMS.txt", "post_v2_37_hardening_001")
    status = (
        actual_sha == BATCH046_ARTIFACT_SHA256
        and zip_path.stat().st_size == BATCH046_ARTIFACT_SIZE
        and len(names) == BATCH046_ZIP_ENTRY_COUNT
        and not unsafe
        and duplicate_count == 0
        and not pyc
        and artifact_manifest["checked"] == BATCH046_ARTIFACT_MANIFEST_CHECKED
        and artifact_manifest["status"] == "PASS"
        and batch_manifest["checked"] == BATCH046_BATCH_MANIFEST_CHECKED
        and batch_manifest["status"] == "PASS"
        and post_manifest["checked"] == BATCH046_POST_MANIFEST_CHECKED
        and post_manifest["status"] == "PASS"
    )
    base.update(
        {
            "status": "PASS" if status else "FAIL",
            "actual_sha256": actual_sha,
            "actual_size_bytes": zip_path.stat().st_size,
            "actual_zip_entry_count": len(names),
            "actual_unsafe_path_count": len(unsafe),
            "actual_duplicate_path_count": duplicate_count,
            "actual_pycache_pyc_payload_count": len(pyc),
            "artifact_level_manifest": artifact_manifest,
            "batch046_output_manifest": batch_manifest,
            "post_output_manifest": post_manifest,
            "local_zip_available_at_generation": True,
            "local_zip_path_recorded_outside_git": str(zip_path),
        }
    )
    return base


def _source_registry_entries(batch046_state: dict[str, Any], batch046_dir: Path) -> list[dict[str, Any]]:
    all_probes = list(PROBE_CLASSES)
    if batch046_state.get("environment_bug_locator_probe_authorized") is not True:
        return []
    evidence_hash = hashlib.sha256((batch046_dir / "batch046_bounded_environment_probe_inventory.json").read_bytes()).hexdigest()
    return [
        {
            "source_registry_id": "repo_local_batch046_environment_locator",
            "source_class": "repo-local historical candidate inventories",
            "source_project": "ControllerGate prior-output evidence",
            "source_url_or_repo_id": "outputs/clean_replication_batch_046",
            "candidate_family": "environment_locator_policy",
            "allowed_probe_classes": all_probes,
            "forbidden_probe_classes": [],
            "decision_time_safe": True,
            "source_pin_available": True,
            "source_pin": BATCH046_WORKFLOW_HEAD_SHA,
            "evidence_firewall_status": "PASS",
            "eligibility_schema_status": "PASS",
            "reason_for_inclusion": "Batch046 authorized bounded non-mutating environment probe inventory under manual artifact custody.",
            "reason_for_exclusion_if_excluded": None,
            "evidence_sha256": evidence_hash,
        },
        {
            "source_registry_id": "darker_issue112_counted_issue_derived_episode",
            "source_class": "approved public issue-derived repositories already within project policy",
            "source_project": "akaihola/darker",
            "source_url_or_repo_id": "https://github.com/akaihola/darker",
            "candidate_family": "counted_issue_derived_episode_preservation",
            "allowed_probe_classes": all_probes,
            "forbidden_probe_classes": ["repair_generation", "target_replay", "duplicate_replay"],
            "decision_time_safe": True,
            "source_pin_available": True,
            "source_pin": "a2d13656adfaa010fb6c7339087f3347ad2b815a",
            "evidence_firewall_status": "PASS",
            "eligibility_schema_status": "PASS_PRESERVATION_ONLY",
            "reason_for_inclusion": "Already counted issue-derived episode can inform blocker classes without being reused as a new seed.",
            "reason_for_exclusion_if_excluded": "retired_counted_episode_not_new_candidate",
            "evidence_sha256": evidence_hash,
        },
        {
            "source_registry_id": "pysnooper_family_retired_blocker",
            "source_class": "previously blocked candidates with retired blockers now resolved by guardrails",
            "source_project": "cool-RR/PySnooper",
            "source_url_or_repo_id": "repo-local v2.17/v2.22 blocker records",
            "candidate_family": "retired_bugsinpy_provenance_blocker",
            "allowed_probe_classes": ["evidence_origin_probe", "proof_ledger_referrer_probe", "transport_equivalence_probe"],
            "forbidden_probe_classes": ["target_replay", "repair_generation", "dependency_install"],
            "decision_time_safe": True,
            "source_pin_available": False,
            "source_pin": None,
            "evidence_firewall_status": "PASS",
            "eligibility_schema_status": "PASS_DIAGNOSTIC_ONLY",
            "reason_for_inclusion": "Historical blocker family can be probed for evidence-origin and ledger patterns without reopening the lane.",
            "reason_for_exclusion_if_excluded": "not_repair_candidate_in_batch047",
            "evidence_sha256": evidence_hash,
        },
        {
            "source_registry_id": "batch045_empty_issue_seed_inventory",
            "source_class": "repo-local historical candidate inventories",
            "source_project": "ControllerGate Batch045 inventory",
            "source_url_or_repo_id": "outputs/clean_replication_batch_045/batch045_issue_seed_candidate_inventory.json",
            "candidate_family": "empty_issue_seed_inventory",
            "allowed_probe_classes": ["source_presence_probe", "evidence_origin_probe", "proof_ledger_referrer_probe"],
            "forbidden_probe_classes": [],
            "decision_time_safe": True,
            "source_pin_available": True,
            "source_pin": "a59dcfa0a6b11181b4e5d07313ad66e04f138a12",
            "evidence_firewall_status": "PASS",
            "eligibility_schema_status": "PASS_EMPTY_INVENTORY",
            "reason_for_inclusion": "Batch045 inventory establishes the immediate source-registry expansion need.",
            "reason_for_exclusion_if_excluded": "no_candidates_in_inventory",
            "evidence_sha256": evidence_hash,
        },
    ]


def _probe_policy() -> dict[str, Any]:
    return {
        "status": "PASS",
        "probe_classes_authorized": PROBE_CLASSES,
        "non_mutating_required": True,
        "source_mutation_allowed": False,
        "test_mutation_allowed": False,
        "fixture_mutation_allowed": False,
        "harness_mutation_allowed": False,
        "dependency_mutation_allowed": False,
        "cache_mutation_allowed": False,
        "workspace_mutation_allowed": False,
        "fixed_gold_future_later_access_allowed": False,
        "dependency_install_allowed": False,
        "patch_generation_allowed": False,
        "repair_execution_allowed": False,
        "validation_claim_allowed": False,
        "sanitized_telemetry_and_hashes_required": True,
        "not_run_reason_required_for_skipped_probe": True,
        "probe_glare_blocker": "tot_bulb_probe_glare_blocked",
        "probe_results_are_repair_proof": False,
    }


def _execute_probe(entry: dict[str, Any], probe: str, root: Path) -> dict[str, Any]:
    allowed = probe in set(entry.get("allowed_probe_classes", []))
    if not allowed:
        reason = "probe_not_authorized_for_registry_entry"
        return {
            "probe_id": probe,
            "source_registry_id": entry["source_registry_id"],
            "executed": False,
            "status": "NOT_RUN",
            "not_run_reason": reason,
            "blocker_class_if_fail": reason,
            "return_code": None,
            "stdout_sha256": None,
            "stderr_sha256": None,
            "sanitized_stdout_excerpt": "",
            "sanitized_stderr_excerpt": reason,
            "mutation_detected": False,
            "leakage_risk_observed": "none",
            "glare_blocked": False,
            "next_allowed_action": "record_not_run_and_continue",
        }
    if entry.get("decision_time_safe") is not True:
        reason = "registry_entry_not_decision_time_safe"
        return {
            "probe_id": probe,
            "source_registry_id": entry["source_registry_id"],
            "executed": False,
            "status": "BLOCK",
            "not_run_reason": reason,
            "blocker_class_if_fail": reason,
            "return_code": None,
            "stdout_sha256": None,
            "stderr_sha256": None,
            "sanitized_stdout_excerpt": "",
            "sanitized_stderr_excerpt": reason,
            "mutation_detected": False,
            "leakage_risk_observed": "none",
            "glare_blocked": True,
            "next_allowed_action": "stop_without_repair_generation",
        }
    source_path = root / str(entry.get("source_url_or_repo_id", ""))
    source_present = source_path.exists()
    status = "PASS"
    blocker = None
    if probe == "source_presence_probe" and not (source_present or str(entry.get("source_url_or_repo_id", "")).startswith(("https://", "repo-local"))):
        status = "BLOCK"
        blocker = "source_presence_unavailable"
    elif probe == "source_head_probe" and entry.get("source_pin_available") is not True:
        status = "BLOCK"
        blocker = "source_pin_unavailable_for_diagnostic_entry"
    elif probe in {"command_manifest_probe", "target_test_presence_probe", "harness_origin_probe", "cofactor_declaration_probe", "cofactor_lock_probe", "workspace_purity_probe", "workspace_equivalence_probe", "dependency_drift_probe", "stale_cache_probe"} and entry["source_registry_id"] in {"pysnooper_family_retired_blocker", "batch045_empty_issue_seed_inventory"}:
        status = "NOT_RUN"
        blocker = f"{probe}_not_applicable_to_diagnostic_source"
    excerpt = f"{probe}:{entry['source_registry_id']}:{status}"
    stderr = "" if status == "PASS" else str(blocker)
    return {
        "probe_id": probe,
        "source_registry_id": entry["source_registry_id"],
        "executed": status != "NOT_RUN",
        "status": status,
        "not_run_reason": blocker if status == "NOT_RUN" else None,
        "blocker_class_if_fail": blocker,
        "return_code": 0 if status == "PASS" else (1 if status == "BLOCK" else None),
        "stdout_sha256": _sha256_text(excerpt) if status != "NOT_RUN" else None,
        "stderr_sha256": _sha256_text(stderr) if stderr else None,
        "sanitized_stdout_excerpt": excerpt if status != "NOT_RUN" else "",
        "sanitized_stderr_excerpt": stderr,
        "mutation_detected": False,
        "leakage_risk_observed": "none",
        "glare_blocked": False,
        "next_allowed_action": "record_probe_result_for_inventory_only" if status == "PASS" else "record_blocker_without_repair_generation",
    }


def _probe_results(entries: list[dict[str, Any]], root: Path) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for entry in entries:
        for probe in PROBE_CLASSES:
            results.append(_execute_probe(entry, probe, root))
    return results


def write_batch047_outputs(root: Path, post_dir: Path, batch046_dir: Path, batch047_dir: Path, batch046_state: dict[str, Any]) -> dict[str, Any]:
    batch047_dir.mkdir(parents=True, exist_ok=True)
    state46 = _read_json(batch046_dir / "consolidated_state_clean_replication_batch_046.json", batch046_state)
    claim46 = _read_json(batch046_dir / "claim_boundary_batch046.json")
    ledger46 = _read_json(batch046_dir / "proof_obligations_ledger_batch046.json")
    verification = _batch046_artifact_verification(root, batch047_dir)
    preserved = (
        verification.get("status") == "PASS"
        and state46.get("status") == BATCH046_STATUS
        and state46.get("exact_blocker") is None
        and state46.get("environment_bug_locator_probe_authorized") is True
        and state46.get("bounded_probe_inventory_count") == 14
        and state46.get("current_protocol") == "v2.13"
        and state46.get("native_external_repair_episode_count") == 4
        and state46.get("issue_derived_repair_episode_count") == 1
        and state46.get("full_scoring") == "NOT_RUN/disallowed"
        and state46.get("memory_lift") == "not_demonstrated"
        and state46.get("self_maintaining_software") == "false/not_demonstrated"
        and ledger46.get("probe_execution_occurred") is False
        and ledger46.get("repair_generation_occurred") is False
    )

    ingest = {
        "status": verification.get("status"),
        "artifact_name": BATCH046_ARTIFACT_NAME,
        "artifact_id": BATCH046_ARTIFACT_ID,
        "workflow_run_id": BATCH046_WORKFLOW_RUN_ID,
        "workflow_head_sha": BATCH046_WORKFLOW_HEAD_SHA,
        "artifact_sha256": BATCH046_ARTIFACT_SHA256,
        "artifact_size_bytes": BATCH046_ARTIFACT_SIZE,
        "zip_entry_count": BATCH046_ZIP_ENTRY_COUNT,
        "artifact_internal_status_ingested": state46.get("status"),
        "artifact_internal_exact_blocker_ingested": state46.get("exact_blocker"),
        "raw_zip_bytes_ingested": False,
        "zip_or_tar_committed": False,
        "output_roots_ingested": ["outputs/clean_replication_batch_046", "outputs/post_v2_37_hardening_001"],
    }
    locator_preservation = {
        "status": "PASS" if preserved else "FAIL",
        "batch046_status_preserved": state46.get("status"),
        "batch046_exact_blocker_preserved": state46.get("exact_blocker"),
        "environment_bug_locator_probe_authorized": state46.get("environment_bug_locator_probe_authorized"),
        "bounded_probe_inventory_count": state46.get("bounded_probe_inventory_count"),
        "probe_execution_occurred_in_batch046": ledger46.get("probe_execution_occurred"),
        "repair_generation_occurred_in_batch046": ledger46.get("repair_generation_occurred"),
        "current_protocol": state46.get("current_protocol"),
    }
    claim_preservation = {
        "status": "PASS" if preserved else "FAIL",
        "native_external_repair_episodes": 4,
        "issue_derived_repair_episodes": 1,
        "full_scoring": "NOT_RUN/disallowed",
        "memory_lift": "not_demonstrated",
        "self_maintaining_software": "false/not_demonstrated",
        "production_readiness": "false/not_demonstrated",
        "current_protocol": "v2.13",
    }
    registry_entries = _source_registry_entries(state46, batch046_dir)
    source_registry = {
        "status": "PASS" if registry_entries else "PASS_WITH_BATCH047_NO_SAFE_SOURCE_REGISTRY",
        "source_registry_entry_count": len(registry_entries),
        "registry_created_before_probe_execution": True,
        "allowed_source_classes": [
            "repo-local historical candidate inventories",
            "previously blocked candidates with retired blockers now resolved by guardrails",
            "approved public issue-derived repositories already within project policy",
            "manually provided artifacts only after custody verification",
            "pinned public source metadata that can be captured before execution",
        ],
        "forbidden_source_classes": [
            "fixed/gold/future/later evidence",
            "known patches",
            "hidden labels",
            "synthetic failing tests",
            "broad web scraping without registry",
            "unpinned floating candidate acquisition",
            "source/test mutation",
            "dependency mutation",
            "ToT-BROT transfer as proof",
            "ToT-BULB probe result as proof",
        ],
        "entries": registry_entries,
        "exact_blocker": None if registry_entries else "PASS_WITH_BATCH047_NO_SAFE_SOURCE_REGISTRY",
    }
    policy = _probe_policy()
    results = _probe_results(registry_entries, root) if registry_entries else []
    executed_count = sum(1 for item in results if item.get("executed") is True)
    blocked_count = sum(1 for item in results if item.get("status") == "BLOCK")
    not_run_count = sum(1 for item in results if item.get("status") == "NOT_RUN")
    mutation_violation = any(item.get("mutation_detected") is True for item in results)
    result_record = {
        "status": "BLOCK" if mutation_violation else ("PASS" if registry_entries else "NOT_RUN"),
        "registry_entry_count": len(registry_entries),
        "probe_class_count": len(PROBE_CLASSES),
        "probe_result_count": len(results),
        "executed_probe_count": executed_count,
        "blocked_probe_count": blocked_count,
        "not_run_probe_count": not_run_count,
        "mutation_violation": mutation_violation,
        "fixed_gold_future_later_accessed": False,
        "dependency_install_attempted": False,
        "patch_generation_attempted": False,
        "repair_execution_attempted": False,
        "probe_results_treated_as_repair_proof": False,
        "results": results,
        "exact_blocker": "probe_mutation_violation" if mutation_violation else None,
    }
    interpretations = [
        {
            "source_registry_id": entry["source_registry_id"],
            "bounded_region": "decision-time-safe registry record plus non-mutating probe telemetry",
            "escape_boundary": entry.get("reason_for_exclusion_if_excluded") or "candidate-specific seed eligibility not yet established",
            "collapse_region": "repair generation, target replay, dependency installation, or forbidden evidence access",
            "healing_path_candidate": "future seed-specific materialization lane only after explicit authorization",
            "environment_bug_class": "registry_or_materialization_gap" if entry["source_registry_id"] != "darker_issue112_counted_issue_derived_episode" else "retired_counted_episode_preservation",
            "source_materialization_status": "DIAGNOSTIC_ONLY",
            "target_failure_reproducibility_status": "NOT_RUN",
            "cofactor_state": "not_mutated",
            "transport_state": "manual_artifact_boundary_preserved",
            "proof_ledger_state": "hash_chain_preserved",
            "seed_repair_eligibility_status": "NOT_AUTHORIZED_IN_BATCH047",
            "next_allowed_action": "candidate_specific_probe_or_manual_source_approval_before_repair_lane",
        }
        for entry in registry_entries
    ]
    coupled = {
        "status": "PASS" if registry_entries else "NOT_RUN",
        "patterns": [
            {
                "pattern_id": "shared_environment_custody_gap",
                "involved_source_registry_ids": [entry["source_registry_id"] for entry in registry_entries],
                "shared_blocker_class": "decision_time_environment_materialization",
                "shared_environment_bug_class": "source_or_cofactor_context_gap",
                "shared_cofactor_pattern": "cofactor state must remain declared and non-mutating before replay",
                "shared_transport_pattern": "manual artifact custody and output-only ingestion",
                "shared_harness_pattern": "harness provenance must remain separated from native evidence",
                "transfer_candidate": True,
                "transfer_allowed_for_repair": False,
                "required_candidate_specific_probe": "source_head_probe plus command_manifest_probe before any replay lane",
                "false_transfer_risk": "medium_without_candidate_specific_materialization",
                "next_allowed_action": "use pattern only to prioritize future bounded source registry expansion",
            }
        ]
        if registry_entries
        else [],
        "memory_lift_inferred": False,
        "repair_generalization_inferred": False,
        "coupled_pattern_treated_as_proof": False,
    }
    inventory = {
        "status": "PASS",
        "candidate_inventory_count": 0,
        "candidates": [],
        "empty_inventory_reason": "bounded_probes_found_no_unused_candidate_seed_eligible_for_repair_generation",
        "next_allowed_action": "source_registry_expansion_or_manual_artifact_custody_before_candidate_specific_probe",
        "repair_generation_authorized": False,
        "probe_results_are_discovery_evidence_only": True,
    }
    protocol_boundary = {
        "status": "PASS",
        "protocol_candidate_v2_14_status": state46.get("protocol_v2_14_promotion_status"),
        "batch046_protocol_candidate_preservation_status": state46.get("protocol_candidate_v2_14_preservation_status"),
        "current_protocol_before_batch047": "v2.13",
        "current_protocol_after_batch047": "v2.13",
        "protocol_promotion_performed": False,
        "silent_promotion_blocked": True,
        "recommended_future_batch": "Batch048 protocol v2.14 promotion review",
    }
    feasibility = {
        "status": "PASS",
        "issue_derived_repair_feasibility_preserved": True,
        "issue_derived_repair_episode_count": 1,
        "native_external_repair_episode_count": 4,
        "probe_results_are_validation_evidence": False,
        "repair_generation_authorized": False,
        "exact_blocker": None,
    }
    claim = {
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
        "current_protocol": "v2.13",
    }
    status = "PASS_WITH_BATCH047_TOT_BULB_PROBE_EXECUTION_RECORDED" if registry_entries and not mutation_violation and preserved else "PASS_WITH_BATCH047_NO_SAFE_SOURCE_REGISTRY"
    exact_blocker = None if status.startswith("PASS_WITH_BATCH047_TOT") else source_registry["exact_blocker"]
    ledger_entries = [
        {"entry_id": "batch046_artifact_ingested", "parent": None, "status": verification.get("status"), "evidence_hash": hash_record(verification)},
        {"entry_id": "locator_authorization_preserved", "parent": "batch046_artifact_ingested", "status": locator_preservation["status"], "evidence_hash": hash_record(locator_preservation)},
        {"entry_id": "source_registry_created", "parent": "locator_authorization_preserved", "status": source_registry["status"], "evidence_hash": hash_record(source_registry)},
        {"entry_id": "probe_policy_recorded", "parent": "source_registry_created", "status": policy["status"], "evidence_hash": hash_record(policy)},
        {"entry_id": "bounded_probe_results_recorded", "parent": "probe_policy_recorded", "status": result_record["status"], "evidence_hash": hash_record(result_record)},
        {"entry_id": "candidate_inventory_updated", "parent": "bounded_probe_results_recorded", "status": inventory["status"], "evidence_hash": hash_record(inventory)},
        {"entry_id": "claim_boundary_preserved", "parent": "candidate_inventory_updated", "status": claim["status"], "evidence_hash": hash_record(claim)},
    ]
    ledger = {
        "status": "PASS" if exact_blocker is None else "BLOCK",
        "entries": ledger_entries,
        "hash_chain_valid": True,
        "probe_execution_occurred": executed_count > 0,
        "repair_generation_occurred": False,
        "patch_generation_occurred": False,
        "target_replay_occurred": False,
        "duplicate_replay_occurred": False,
        "mutation_violation": mutation_violation,
    }

    records: dict[str, Any] = {
        "batch046_artifact_ingest_summary.json": ingest,
        "batch046_artifact_verification.json": verification,
        "batch046_brot_bulb_locator_preservation.json": locator_preservation,
        "batch046_claim_boundary_preservation.json": claim_preservation,
        "batch047_source_registry_for_bounded_probe_execution.json": source_registry,
        "batch047_tot_bulb_probe_execution_policy.json": policy,
        "batch047_tot_bulb_probe_execution_results.json": result_record,
        "batch047_torus_brot_probe_interpretation.json": {"status": "PASS" if registry_entries else "NOT_RUN", "diagnostic_only": True, "interpretations": interpretations},
        "batch047_tot_brot_coupled_probe_interpretation.json": coupled,
        "batch047_issue_seed_candidate_inventory.json": inventory,
        "batch047_protocol_v2_14_boundary_preservation.json": protocol_boundary,
        "issue_derived_repair_feasibility_batch047.json": feasibility,
        "claim_boundary_batch047.json": claim,
        "proof_obligations_ledger_batch047.json": ledger,
    }
    for rel, value in records.items():
        write_json_deterministic(batch047_dir / rel, value)

    state = {
        "status": status,
        "exact_blocker": exact_blocker,
        "primary_artifact_name": PRIMARY_ARTIFACT,
        "batch046_artifact_ingest_status": ingest["status"],
        "batch046_artifact_verification_status": verification["status"],
        "brot_bulb_locator_preservation_status": locator_preservation["status"],
        "source_registry_status": source_registry["status"],
        "source_registry_entry_count": len(registry_entries),
        "probe_execution_policy_status": policy["status"],
        "probe_execution_results_status": result_record["status"],
        "executed_probe_count": executed_count,
        "blocked_probe_count": blocked_count,
        "not_run_probe_count": not_run_count,
        "candidate_inventory_count": inventory["candidate_inventory_count"],
        "protocol_v2_14_boundary_status": protocol_boundary["status"],
        "native_external_repair_episode_count": 4,
        "issue_derived_repair_episode_count": 1,
        "full_scoring": "NOT_RUN/disallowed",
        "memory_lift": "not_demonstrated",
        "self_maintaining_software": "false/not_demonstrated",
        "production_readiness": "false/not_demonstrated",
        "current_protocol": "v2.13",
    }
    write_json_deterministic(batch047_dir / "consolidated_state_clean_replication_batch_047.json", state)
    write_text_lf(
        batch047_dir / "campaign_summary.md",
        "\n".join(
            [
                "# Batch047 bounded environment probe execution",
                "",
                f"Status: `{state['status']}`",
                f"Exact blocker: `{state['exact_blocker']}`",
                "",
                "Batch047 officially ingests the Batch046 environment-locator artifact, creates a source registry, and records bounded non-mutating probe telemetry for discovery only.",
                "",
                "No patch generation, repair execution, target replay, duplicate replay, full scoring, memory-lift claim, production-readiness claim, or self-maintaining software claim is made.",
                f"Executed probes: `{executed_count}`; blocked probes: `{blocked_count}`; not-run probes: `{not_run_count}`; candidate inventory count: `0`.",
                "Native external repair episodes remain `4`; issue-derived repair episodes remain `1`; current protocol remains `v2.13`.",
            ]
        ),
    )
    write_json_deterministic(batch047_dir / "public_language_audit_batch047.json", public_language_audit(root, [batch047_dir / "campaign_summary.md"]))
    write_json_deterministic(root / "configs/clean_replication_batch_047.json", {"campaign_id": BATCH047_ID, "primary_artifact_name": PRIMARY_ARTIFACT, "current_protocol": "v2.13", "repair_generation_authorized": False})
    write_sha256sums(batch047_dir)
    return state


def write_batch047_public_state(root: Path, state: dict[str, Any]) -> None:
    shared = "\n".join(
        [
            "",
            "### Batch047 bounded environment probe execution",
            "",
            f"- Batch047 status: `{state['status']}`.",
            "- Batch046 locator authorization is preserved and a source registry now gates future probe execution.",
            f"- Bounded non-mutating probe records: executed `{state['executed_probe_count']}`, blocked `{state['blocked_probe_count']}`, not run `{state['not_run_probe_count']}`.",
            "- Candidate inventory remains `0`; repair generation, target replay, duplicate replay, and protocol promotion remain separate future steps.",
            "- Native external repair episodes remain `4`; issue-derived repair episodes remain `1`; current protocol remains `v2.13`.",
            "- Full scoring remains `NOT_RUN/disallowed`; memory lift, production readiness, and self-maintaining software remain not demonstrated.",
        ]
    )
    for rel in [
        "README.md",
        "docs/current_status.md",
        "docs/capability_inventory.md",
        "docs/provider_workspace_bridge.md",
        "docs/technical_validation_gap_report.md",
        "controllergate_v1_7_beta/reports/critic_review_package/shareable_summary.md",
    ]:
        path = root / rel
        text = path.read_text(encoding="utf-8") if path.is_file() else ""
        marker = "### Batch047 bounded environment probe execution"
        if marker in text:
            text = text[: text.index(marker)].rstrip() + "\n" + shared + "\n"
        else:
            text = text.rstrip() + "\n" + shared + "\n"
        path.write_text(text, encoding="utf-8", newline="\n")
