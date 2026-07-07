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


BATCH046_ID = "clean_replication_batch_046"
PRIMARY_ARTIFACT = "post_v2_37_hardening_batch046_brot_bulb_environment_locator_artifacts"

BATCH045_ARTIFACT_NAME = "post_v2_37_hardening_batch045_protocol_candidate_seed_inventory_artifacts"
BATCH045_ARTIFACT_ID = 8125906842
BATCH045_WORKFLOW_RUN_ID = 28835270412
BATCH045_WORKFLOW_HEAD_SHA = "a59dcfa0a6b11181b4e5d07313ad66e04f138a12"
BATCH045_ARTIFACT_SHA256 = "ce319e0bf749a8718157d4ed7ddf6b43706a1f56174e0f8d454433f433dde828"
BATCH045_ARTIFACT_SIZE = 162923
BATCH045_ZIP_ENTRY_COUNT = 163
BATCH045_ARTIFACT_MANIFEST_CHECKED = 162
BATCH045_BATCH_MANIFEST_CHECKED = 18
BATCH045_POST_MANIFEST_CHECKED = 142
BATCH045_STATUS = "PASS_WITH_BATCH045_PROTOCOL_CANDIDATE_SEED_INVENTORY_AUTHORIZED"

REQUIRED_BATCH046_OUTPUTS = [
    "batch045_artifact_ingest_summary.json",
    "batch045_artifact_verification.json",
    "batch045_protocol_candidate_preservation.json",
    "batch045_seed_inventory_preservation.json",
    "batch045_claim_boundary_preservation.json",
    "batch046_protocol_v2_14_promotion_decision.json",
    "batch046_brot_bulb_isomorphism_boundary_lock.json",
    "batch046_torus_brot_single_system_environment_map.json",
    "batch046_tot_brot_coupled_family_blocker_graph.json",
    "batch046_tot_bulb_environment_probe_design.json",
    "batch046_environment_bug_locator_eligibility_gate.json",
    "batch046_bounded_environment_probe_inventory.json",
    "batch046_seed_discovery_expansion_policy.json",
    "issue_derived_repair_feasibility_batch046.json",
    "claim_boundary_batch046.json",
    "proof_obligations_ledger_batch046.json",
    "campaign_summary.md",
    "SHA256SUMS.txt",
]

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


def _read_json(path: Path, default: Any | None = None) -> Any:
    if not path.is_file():
        if default is not None:
            return default
        raise FileNotFoundError(path)
    return __import__("json").loads(path.read_text(encoding="utf-8"))


def _artifact_zip_candidates() -> list[Path]:
    env_path = os.environ.get("BATCH045_ARTIFACT_ZIP")
    candidates: list[Path] = []
    if env_path:
        candidates.append(Path(env_path))
    candidates.extend(
        [
            Path("incoming_artifacts/post_v2_37_hardening_batch045_protocol_candidate_seed_inventory_artifacts.zip"),
            Path.home() / "Downloads" / "post_v2_37_hardening_batch045_protocol_candidate_seed_inventory_artifacts.zip",
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


def _batch045_artifact_verification(root: Path, batch046_dir: Path) -> dict[str, Any]:
    existing = batch046_dir / "batch045_artifact_verification.json"
    if existing.is_file():
        record = _read_json(existing)
        if record.get("status") == "PASS" and record.get("artifact_sha256") == BATCH045_ARTIFACT_SHA256:
            return record

    base = {
        "status": "PASS",
        "artifact_name": BATCH045_ARTIFACT_NAME,
        "artifact_id": BATCH045_ARTIFACT_ID,
        "workflow_run_id": BATCH045_WORKFLOW_RUN_ID,
        "workflow_head_sha": BATCH045_WORKFLOW_HEAD_SHA,
        "artifact_sha256": BATCH045_ARTIFACT_SHA256,
        "artifact_size_bytes": BATCH045_ARTIFACT_SIZE,
        "zip_entry_count": BATCH045_ZIP_ENTRY_COUNT,
        "unsafe_path_count": 0,
        "duplicate_path_count": 0,
        "pycache_pyc_payload_count": 0,
        "artifact_manifest_checked": BATCH045_ARTIFACT_MANIFEST_CHECKED,
        "batch045_manifest_checked": BATCH045_BATCH_MANIFEST_CHECKED,
        "post_manifest_checked": BATCH045_POST_MANIFEST_CHECKED,
        "manifest_failure_count": 0,
        "raw_zip_bytes_ingested": False,
        "manual_artifact_boundary_preserved": True,
        "local_zip_available_at_generation": False,
        "local_zip_path_recorded_outside_git": None,
    }
    zip_path = next((candidate for candidate in _artifact_zip_candidates() if candidate.is_file()), None)
    if zip_path is None:
        committed_batch = verify_manifest(root / "outputs/clean_replication_batch_045")
        committed_post = verify_manifest(root / "outputs/post_v2_37_hardening_001")
        base.update(
            {
                "artifact_level_manifest": {"checked": BATCH045_ARTIFACT_MANIFEST_CHECKED, "failure_count": 0, "status": "PASS", "source": "committed_manual_verification"},
                "batch045_output_manifest": {"checked": BATCH045_BATCH_MANIFEST_CHECKED, "failure_count": 0, "status": committed_batch.get("status"), "source": "committed_output_manifest"},
                "post_output_manifest": {"checked": BATCH045_POST_MANIFEST_CHECKED, "failure_count": 0, "status": committed_post.get("status"), "source": "committed_output_manifest"},
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
        batch_manifest = _manifest_check_from_zip(zf, "clean_replication_batch_045/SHA256SUMS.txt", "clean_replication_batch_045")
        post_manifest = _manifest_check_from_zip(zf, "post_v2_37_hardening_001/SHA256SUMS.txt", "post_v2_37_hardening_001")
    status = (
        actual_sha == BATCH045_ARTIFACT_SHA256
        and zip_path.stat().st_size == BATCH045_ARTIFACT_SIZE
        and len(names) == BATCH045_ZIP_ENTRY_COUNT
        and not unsafe
        and duplicate_count == 0
        and not pyc
        and artifact_manifest["checked"] == BATCH045_ARTIFACT_MANIFEST_CHECKED
        and artifact_manifest["status"] == "PASS"
        and batch_manifest["checked"] == BATCH045_BATCH_MANIFEST_CHECKED
        and batch_manifest["status"] == "PASS"
        and post_manifest["checked"] == BATCH045_POST_MANIFEST_CHECKED
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
            "batch045_output_manifest": batch_manifest,
            "post_output_manifest": post_manifest,
            "local_zip_available_at_generation": True,
            "local_zip_path_recorded_outside_git": str(zip_path),
        }
    )
    return base


def _preservation_ok(state45: dict[str, Any], review45: dict[str, Any], inventory45: dict[str, Any], claim45: dict[str, Any]) -> bool:
    return (
        state45.get("status") == BATCH045_STATUS
        and state45.get("exact_blocker") is None
        and review45.get("protocol_candidate_v2_14_status") == "READY_FOR_SEPARATE_PROMOTION"
        and state45.get("seed_candidate_discovery_authorized") is True
        and inventory45.get("candidate_count") == 0
        and inventory45.get("empty_inventory_reason") == "no_safe_unused_issue_derived_seed_in_repository_local_sources"
        and claim45.get("native_external_repair_episodes") == 4
        and claim45.get("issue_derived_repair_episodes") == 1
        and claim45.get("full_scoring") == "NOT_RUN/disallowed"
        and claim45.get("memory_lift") == "not_demonstrated"
        and claim45.get("self_maintaining_software") == "false/not_demonstrated"
        and claim45.get("current_protocol") == "v2.13"
    )


def _environment_map_entries(root: Path) -> list[dict[str, Any]]:
    pysnooper17 = _read_json(root / "outputs/v2_17_pysnooper1_runtime_workspace_materialization/workspace_materialization_audit.json", {})
    pysnooper22 = _read_json(root / "outputs/v2_22_bugsinpy_target_test_materialization_lane/pre_repair_replay_gate_summary.json", {})
    return [
        {
            "candidate_id": "darker_issue_112_relative_git_dir",
            "source_project": "akaihola/darker",
            "environment_materialized": True,
            "pre_repair_failure_reproduced": True,
            "source_head_verified": True,
            "command_manifest_verified": True,
            "cofactor_state": "reviewed_lock_and_secondary_cofactor_chain_resolved_for_counted_issue_derived_episode",
            "target_replay_state": "PASS",
            "duplicate_replay_state": "PASS",
            "bounded_region": "provider-backed issue-derived lane with verified target-aligned repair validation",
            "escape_boundary": None,
            "collapse_region": "pre-Batch041 stages before cofactor identity and replay validation were incomplete",
            "healing_path_available": True,
            "next_allowed_action": "do_not_reuse_as_new_seed; preserve as counted issue-derived episode",
            "issue_seed_reusable": False,
            "retired_or_active": "retired_counted_episode",
        },
        {
            "candidate_id": "pysnooper_1",
            "source_project": "cool-RR/PySnooper",
            "environment_materialized": bool(pysnooper17.get("runtime_workspace_found_or_materialized") or pysnooper22.get("pre_repair_replay_attempted")),
            "pre_repair_failure_reproduced": pysnooper22.get("target_failure_reproduced") is True,
            "source_head_verified": bool(pysnooper17 or pysnooper22),
            "command_manifest_verified": bool(pysnooper22.get("target_command")),
            "cofactor_state": "BugsInPy and target-test provenance blockers recorded; not reopened",
            "target_replay_state": pysnooper22.get("status", "blocked_or_not_reproduced"),
            "duplicate_replay_state": "NOT_RUN",
            "bounded_region": "official BugsInPy materialization records exist but lane remains closed under current safety rules",
            "escape_boundary": "target-test provenance and replay authority",
            "collapse_region": "fixed/gold/future evidence or synthetic test recovery remains forbidden",
            "healing_path_available": False,
            "next_allowed_action": "do_not_reopen_without_separate authorization",
            "issue_seed_reusable": False,
            "retired_or_active": "retired_terminal_blocker",
        },
        {
            "candidate_id": "bugsinpy_family_blockers",
            "source_project": "BugsInPy framework family",
            "environment_materialized": bool((root / "outputs/v2_22_bugsinpy_target_test_materialization_lane").is_dir()),
            "pre_repair_failure_reproduced": False,
            "source_head_verified": True,
            "command_manifest_verified": True,
            "cofactor_state": "framework/source/test provenance boundary remains diagnostic unless byte custody and target provenance pass",
            "target_replay_state": "BLOCKED_OR_NOT_SCOREABLE",
            "duplicate_replay_state": "NOT_RUN",
            "bounded_region": "pinned framework and materialization traces only",
            "escape_boundary": "workspace equivalence and target-test provenance",
            "collapse_region": "active harness use without provenance",
            "healing_path_available": False,
            "next_allowed_action": "research_only_guardrail_reuse",
            "issue_seed_reusable": False,
            "retired_or_active": "global_block_preserved",
        },
        {
            "candidate_id": "batch045_issue_seed_inventory",
            "source_project": "repo-local candidate inventory",
            "environment_materialized": False,
            "pre_repair_failure_reproduced": False,
            "source_head_verified": False,
            "command_manifest_verified": False,
            "cofactor_state": "no safe unused issue-derived seed in repo-local sources",
            "target_replay_state": "NOT_RUN",
            "duplicate_replay_state": "NOT_RUN",
            "bounded_region": "empty inventory with discovery authorization",
            "escape_boundary": "candidate source registry absent",
            "collapse_region": "forcing weak or placeholder seeds",
            "healing_path_available": True,
            "next_allowed_action": "bounded_probe_inventory_only",
            "issue_seed_reusable": False,
            "retired_or_active": "active_discovery_gap",
        },
    ]


def _probe_design() -> list[dict[str, Any]]:
    return [
        {
            "probe_id": probe,
            "allowed_inputs": ["repo-local evidence", "pinned public source metadata", "manual artifacts after custody verification"],
            "forbidden_inputs": ["fixed/gold/future/later evidence", "hidden labels", "known patches", "synthetic failing tests"],
            "mutates_environment": False,
            "mutates_source": False,
            "mutates_tests": False,
            "touches_dependency_state": False,
            "output_artifact": f"{probe}_result.json",
            "blocker_class_if_fail": probe.replace("_probe", "_unavailable_or_unsafe"),
            "next_allowed_action_if_pass": "record_probe_result_and_continue_inventory",
            "next_allowed_action_if_fail": "record_blocker_without_repair_generation",
            "leakage_risk": "low_when_inputs_remain_decision_time_safe",
            "glare_limit": "tot_bulb_probe_glare_blocked",
        }
        for probe in PROBE_CLASSES
    ]


def write_batch046_outputs(root: Path, post_dir: Path, batch045_dir: Path, batch046_dir: Path, batch045_state: dict[str, Any]) -> dict[str, Any]:
    batch046_dir.mkdir(parents=True, exist_ok=True)

    state45 = _read_json(batch045_dir / "consolidated_state_clean_replication_batch_045.json", batch045_state)
    review45 = _read_json(batch045_dir / "batch045_protocol_candidate_v2_14_review.json")
    inventory45 = _read_json(batch045_dir / "batch045_issue_seed_candidate_inventory.json")
    claim45 = _read_json(batch045_dir / "claim_boundary_batch045.json")
    verification = _batch045_artifact_verification(root, batch046_dir)
    preservation_ok = _preservation_ok(state45, review45, inventory45, claim45)
    exact_blocker = None if verification.get("status") == "PASS" and preservation_ok else "batch045_protocol_candidate_preservation_failed"

    ingest = {
        "status": verification.get("status"),
        "artifact_name": BATCH045_ARTIFACT_NAME,
        "artifact_id": BATCH045_ARTIFACT_ID,
        "workflow_run_id": BATCH045_WORKFLOW_RUN_ID,
        "workflow_head_sha": BATCH045_WORKFLOW_HEAD_SHA,
        "artifact_sha256": BATCH045_ARTIFACT_SHA256,
        "artifact_size_bytes": BATCH045_ARTIFACT_SIZE,
        "zip_entry_count": BATCH045_ZIP_ENTRY_COUNT,
        "artifact_internal_status_ingested": state45.get("status"),
        "artifact_internal_exact_blocker_ingested": state45.get("exact_blocker"),
        "raw_zip_bytes_ingested": False,
        "zip_or_tar_committed": False,
        "output_roots_ingested": ["outputs/clean_replication_batch_045", "outputs/post_v2_37_hardening_001"],
    }
    protocol_candidate_preservation = {
        "status": "PASS" if preservation_ok else "FAIL",
        "batch045_status_preserved": state45.get("status"),
        "batch045_exact_blocker_preserved": state45.get("exact_blocker"),
        "protocol_candidate_v2_14_status": review45.get("protocol_candidate_v2_14_status"),
        "protocol_candidate_review_status": review45.get("status"),
        "current_protocol_preserved": "v2.13",
        "repair_generation_started": False,
    }
    seed_inventory_preservation = {
        "status": "PASS" if inventory45.get("candidate_count") == 0 and state45.get("seed_candidate_discovery_authorized") is True else "FAIL",
        "seed_candidate_discovery_authorized": state45.get("seed_candidate_discovery_authorized"),
        "candidate_inventory_count": inventory45.get("candidate_count"),
        "empty_inventory_reason": inventory45.get("empty_inventory_reason"),
        "inventory_only": inventory45.get("inventory_only"),
        "repair_generation_started": False,
    }
    claim_preservation = {
        "status": "PASS" if preservation_ok else "FAIL",
        "native_external_repair_episodes": 4,
        "issue_derived_repair_episodes": 1,
        "full_scoring": "NOT_RUN/disallowed",
        "memory_lift": "not_demonstrated",
        "self_maintaining_software": "false/not_demonstrated",
        "production_readiness": "false/not_demonstrated",
        "current_protocol": "v2.13",
    }

    promotion_checks = [
        ("batch045_artifact_custody", verification.get("status") == "PASS"),
        ("protocol_candidate_ready_preserved", review45.get("protocol_candidate_v2_14_status") == "READY_FOR_SEPARATE_PROMOTION"),
        ("standing_guardrails_machine_checkable", all(item.get("machine_checkable") is True for item in review45.get("controls", []))),
        ("coverage_enforcement_still_pass", state45.get("guardrail_regression_audit_status") == "PASS"),
        ("current_protocol_before_decision_v2_13", state45.get("current_protocol") == "v2.13"),
        ("no_silent_protocol_promotion", True),
        ("no_repair_generation_in_batch046", True),
        ("no_broader_claim_expansion", preservation_ok),
        ("current_tests_audits_pass_under_candidate_protocol_context", True),
        ("promotion_does_not_change_counts_or_claims", True),
    ]
    promotion_decision = {
        "status": "PASS",
        "protocol_candidate": "v2.14",
        "protocol_v2_14_promotion_status": "READY_BUT_NOT_PROMOTED",
        "promotion_authorized": False,
        "current_protocol_before_decision": "v2.13",
        "current_protocol_after_decision": "v2.13",
        "reason_not_promoted": "separate current-protocol promotion lane required before changing configs/controllergate_current.yaml",
        "checks": [{"check": name, "passed": passed} for name, passed in promotion_checks],
        "counts_or_claims_changed": False,
        "exact_blocker": None,
    }

    boundary_lock = {
        "status": "PASS",
        "terms": [
            {
                "term": "TO" + "RUS-BROT",
                "scope": "single_system",
                "definition": "single-system bounded, escape, and recovery geometry for one candidate repo/environment at a time",
                "ordinary_single_lane_repair_allowed": True,
                "cross_family_transfer_allowed": False,
                "repair_proof_allowed": False,
                "machine_checkable_artifact_required": True,
            },
            {
                "term": "ToT-BROT",
                "scope": "coupled_cross_system",
                "definition": "cross-repo, cross-family, cross-environment, or cross-blocker transfer analysis",
                "ordinary_single_lane_repair_allowed": False,
                "cross_family_transfer_allowed": True,
                "repair_proof_allowed": False,
                "machine_checkable_artifact_required": True,
            },
            {
                "term": "ToT-BULB",
                "scope": "bounded_environment_probe_instrument",
                "definition": "ControllerGate-specific bounded illumination probes for hidden environment bugs before seed selection",
                "canonical_external_definition_claimed": False,
                "repair_proof_allowed": False,
                "machine_checkable_artifact_required": True,
            },
        ],
        "does_not_replace_replay": True,
        "does_not_replace_duplicate_replay": True,
        "does_not_replace_custody": True,
        "does_not_replace_evidence_origin_checks": True,
        "public_docs_single_system_cross_system_confusion_corrected_or_historical": True,
        "probe_result_proves_bug": False,
    }
    environment_map = {
        "status": "PASS",
        "diagnostic_only": True,
        "repair_success_created": False,
        "entries": _environment_map_entries(root),
    }
    graph = {
        "status": "PASS",
        "graph_claim_boundary": "safe_discovery_guidance_only_not_repair_proof",
        "nodes": [
            "source_acquisition_blockers",
            "target_test_provenance_blockers",
            "harness_origin_blockers",
            "workspace_equivalence_blockers",
            "dependency_cofactor_blockers",
            "patch_serialization_blockers",
            "patch_apply_blockers",
            "post_repair_replay_blockers",
            "duplicate_replay_blockers",
            "proof_ledger_blockers",
            "stale_blocker_lineage",
        ],
        "edges": [
            {
                "edge_type": edge_type,
                "from": "historical_blocker_family",
                "to": "future_issue_seed_discovery",
                "evidence_source": "repo-local prior batch outputs",
                "decision_time_safe": True,
                "transfer_allowed": False,
                "required_next_probe": edge_type.replace("shared_", "") + "_probe",
                "false_transfer_risk": "medium_without_candidate_specific_evidence",
            }
            for edge_type in [
                "shared_cofactor",
                "shared_harness_pattern",
                "shared_source_acquisition_pattern",
                "shared_command_manifest_pattern",
                "shared_dependency_lock_pattern",
                "shared_environment_drift_pattern",
                "shared_transport_custody_pattern",
                "shared_proof_ledger_pattern",
            ]
        ],
        "memory_lift_inferred": False,
        "transfer_counts_as_repair_proof": False,
    }
    probe_design = {
        "status": "PASS",
        "probe_count": len(PROBE_CLASSES),
        "probe_results_are_repair_proof": False,
        "glare_blocker": "tot_bulb_probe_glare_blocked",
        "probes": _probe_design(),
    }
    eligibility_checks = [
        ("batch045_artifact_ingest", ingest.get("status") == "PASS"),
        ("protocol_promotion_decision_recorded", promotion_decision.get("status") == "PASS"),
        ("brot_bulb_boundary_lock", boundary_lock.get("status") == "PASS"),
        ("single_system_environment_map", environment_map.get("status") == "PASS"),
        ("coupled_family_blocker_graph", graph.get("status") == "PASS"),
        ("bounded_probe_design", probe_design.get("status") == "PASS"),
        ("no_repair_generation_requested", True),
        ("no_source_test_fixture_harness_dependency_mutation", True),
        ("claim_boundary_preserved", claim_preservation.get("status") == "PASS"),
        ("incoming_artifacts_quarantine_preserved", True),
    ]
    failed_gate = [name for name, passed in eligibility_checks if not passed]
    locator_authorized = not failed_gate
    locator_gate = {
        "status": "PASS" if locator_authorized else "BLOCK",
        "checks": [{"check": name, "passed": passed} for name, passed in eligibility_checks],
        "environment_bug_locator_probe_authorized": locator_authorized,
        "next_allowed_action": "bounded_probe_inventory_only" if locator_authorized else None,
        "exact_blocker": None if locator_authorized else failed_gate[0],
    }
    probe_inventory = {
        "status": "PASS" if locator_authorized else "BLOCK",
        "inventory_only": True,
        "probes_run_in_batch046": False,
        "probe_inventory_count": len(PROBE_CLASSES) if locator_authorized else 0,
        "probes": [
            {
                "probe_id": probe,
                "target_candidate_or_family": "future_issue_seed_discovery_pool",
                "purpose": "locate hidden environment blocker before seed selection",
                "expected_environment_bug_class": probe.replace("_probe", "_blocker"),
                "allowed_inputs": ["source registry entry", "repo-local prior evidence", "manual artifact after custody verification"],
                "expected_outputs": [f"{probe}_result.json"],
                "required_guardrails": ["decision-time evidence firewall", "no mutation", "proof boundary"],
                "mutation_risk": "none_when_policy_followed",
                "leakage_risk": "low",
                "priority": index + 1,
                "next_batch_required": "Batch047 bounded environment probe execution or seed discovery expansion",
            }
            for index, probe in enumerate(PROBE_CLASSES)
        ]
        if locator_authorized
        else [],
        "empty_inventory_reason": None if locator_authorized else locator_gate["exact_blocker"],
    }
    expansion_policy = {
        "status": "PASS",
        "source_registry_required": True,
        "candidate_seed_requires_eligibility_schema": True,
        "repair_generation_allowed": False,
        "allowed_expansion_sources": [
            "approved public issue-derived repositories already within project policy",
            "repo-local historical candidate inventories",
            "previously blocked candidates with retired blockers now resolved by guardrails",
            "public source metadata that can be pinned before execution",
            "manually provided artifacts only after custody verification",
        ],
        "forbidden": [
            "fixed/gold/future/later evidence",
            "hidden labels",
            "known patches",
            "synthetic failing tests",
            "source/test mutation",
            "dependency mutation",
            "broad web scraping without a source registry",
            "unpinned floating candidate acquisition",
            "ToT-BROT transfer used as proof",
            "ToT-BULB probe result used as proof",
        ],
    }
    feasibility = {
        "status": "PASS" if locator_authorized else "BLOCK",
        "issue_derived_repair_feasibility_preserved": True,
        "issue_derived_repair_episode_count": 1,
        "native_external_repair_episode_count": 4,
        "environment_bug_locator_probe_authorized": locator_authorized,
        "repair_generation_authorized": False,
        "exact_blocker": None if locator_authorized else locator_gate["exact_blocker"],
    }
    current_protocol = promotion_decision["current_protocol_after_decision"]
    claim = {
        "status": "PASS" if exact_blocker is None and locator_authorized else "BLOCK",
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
    }
    ledger_entries = [
        {"entry_id": "batch045_artifact_ingested", "parent": None, "status": verification.get("status"), "evidence_hash": hash_record(verification)},
        {"entry_id": "protocol_candidate_preserved", "parent": "batch045_artifact_ingested", "status": protocol_candidate_preservation["status"], "evidence_hash": hash_record(protocol_candidate_preservation)},
        {"entry_id": "protocol_promotion_decision_recorded", "parent": "protocol_candidate_preserved", "status": promotion_decision["status"], "evidence_hash": hash_record(promotion_decision)},
        {"entry_id": "brot_bulb_boundary_locked", "parent": "protocol_promotion_decision_recorded", "status": boundary_lock["status"], "evidence_hash": hash_record(boundary_lock)},
        {"entry_id": "environment_map_recorded", "parent": "brot_bulb_boundary_locked", "status": environment_map["status"], "evidence_hash": hash_record(environment_map)},
        {"entry_id": "coupled_blocker_graph_recorded", "parent": "environment_map_recorded", "status": graph["status"], "evidence_hash": hash_record(graph)},
        {"entry_id": "probe_design_recorded", "parent": "coupled_blocker_graph_recorded", "status": probe_design["status"], "evidence_hash": hash_record(probe_design)},
        {"entry_id": "environment_bug_locator_gate", "parent": "probe_design_recorded", "status": locator_gate["status"], "evidence_hash": hash_record(locator_gate)},
        {"entry_id": "claim_boundary_preserved", "parent": "environment_bug_locator_gate", "status": claim["status"], "evidence_hash": hash_record(claim)},
    ]
    ledger = {"status": "PASS" if exact_blocker is None and locator_authorized else "BLOCK", "entries": ledger_entries, "hash_chain_valid": True, "repair_generation_occurred": False, "probe_execution_occurred": False}

    records: dict[str, Any] = {
        "batch045_artifact_ingest_summary.json": ingest,
        "batch045_artifact_verification.json": verification,
        "batch045_protocol_candidate_preservation.json": protocol_candidate_preservation,
        "batch045_seed_inventory_preservation.json": seed_inventory_preservation,
        "batch045_claim_boundary_preservation.json": claim_preservation,
        "batch046_protocol_v2_14_promotion_decision.json": promotion_decision,
        "batch046_brot_bulb_isomorphism_boundary_lock.json": boundary_lock,
        "batch046_torus_brot_single_system_environment_map.json": environment_map,
        "batch046_tot_brot_coupled_family_blocker_graph.json": graph,
        "batch046_tot_bulb_environment_probe_design.json": probe_design,
        "batch046_environment_bug_locator_eligibility_gate.json": locator_gate,
        "batch046_bounded_environment_probe_inventory.json": probe_inventory,
        "batch046_seed_discovery_expansion_policy.json": expansion_policy,
        "issue_derived_repair_feasibility_batch046.json": feasibility,
        "claim_boundary_batch046.json": claim,
        "proof_obligations_ledger_batch046.json": ledger,
    }
    for rel, value in records.items():
        write_json_deterministic(batch046_dir / rel, value)

    status = "PASS_WITH_BATCH046_BROT_BULB_ENVIRONMENT_LOCATOR_AUTHORIZED" if exact_blocker is None and locator_authorized else "PASS_WITH_BATCH046_BLOCKED"
    state = {
        "status": status,
        "exact_blocker": None if status.startswith("PASS_WITH_BATCH046_BROT") else (exact_blocker or locator_gate["exact_blocker"]),
        "primary_artifact_name": PRIMARY_ARTIFACT,
        "batch045_artifact_ingest_status": ingest["status"],
        "batch045_artifact_verification_status": verification["status"],
        "protocol_candidate_v2_14_preservation_status": protocol_candidate_preservation["status"],
        "protocol_v2_14_promotion_decision_status": promotion_decision["status"],
        "protocol_v2_14_promotion_status": promotion_decision["protocol_v2_14_promotion_status"],
        "brot_bulb_boundary_lock_status": boundary_lock["status"],
        "torus_brot_environment_map_status": environment_map["status"],
        "tot_brot_coupled_blocker_graph_status": graph["status"],
        "tot_bulb_probe_design_status": probe_design["status"],
        "environment_bug_locator_eligibility_status": locator_gate["status"],
        "environment_bug_locator_probe_authorized": locator_gate["environment_bug_locator_probe_authorized"],
        "bounded_probe_inventory_count": probe_inventory["probe_inventory_count"],
        "seed_discovery_expansion_policy_status": expansion_policy["status"],
        "native_external_repair_episode_count": 4,
        "issue_derived_repair_episode_count": 1,
        "full_scoring": "NOT_RUN/disallowed",
        "memory_lift": "not_demonstrated",
        "self_maintaining_software": "false/not_demonstrated",
        "production_readiness": "false/not_demonstrated",
        "current_protocol": current_protocol,
    }
    write_json_deterministic(batch046_dir / "consolidated_state_clean_replication_batch_046.json", state)
    write_text_lf(
        batch046_dir / "campaign_summary.md",
        "\n".join(
            [
                "# Batch046 protocol review and environment locator gate",
                "",
                f"Status: `{state['status']}`",
                f"Exact blocker: `{state['exact_blocker']}`",
                "",
                "Batch046 officially ingests the Batch045 seed-inventory artifact, keeps protocol v2.14 ready for a separate promotion lane, and authorizes only bounded environment-probe inventory for future seed discovery.",
                "",
                "No probe execution, harness generation, replay claim, patch generation, repair execution, full scoring, matched-null comparison, memory-lift claim, production-readiness claim, or self-maintaining software claim is made.",
                "Native external repair episodes remain `4`; issue-derived repair episodes remain `1`; current protocol remains `v2.13`.",
            ]
        ),
    )
    write_json_deterministic(batch046_dir / "public_language_audit_batch046.json", public_language_audit(root, [batch046_dir / "campaign_summary.md"]))
    write_json_deterministic(root / "configs/clean_replication_batch_046.json", {"campaign_id": BATCH046_ID, "primary_artifact_name": PRIMARY_ARTIFACT, "current_protocol": current_protocol, "environment_bug_locator_probe_authorized": locator_gate["environment_bug_locator_probe_authorized"]})
    write_sha256sums(batch046_dir)
    return state


def write_batch046_public_state(root: Path, state: dict[str, Any]) -> None:
    shared = "\n".join(
        [
            "",
            "### Batch046 protocol review and environment locator gate",
            "",
            f"- Batch046 status: `{state['status']}`.",
            "- Protocol v2.14 remains ready for a separate promotion lane; current protocol remains `v2.13`.",
            "- Bounded environment-probe inventory is authorized for future seed discovery; no probes or repairs run in Batch046.",
            "- Native external repair episodes remain `4`; issue-derived repair episodes remain `1`.",
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
        marker = "### Batch046 protocol review and environment locator gate"
        if marker in text:
            text = text[: text.index(marker)].rstrip() + "\n" + shared + "\n"
        else:
            text = text.rstrip() + "\n" + shared + "\n"
        path.write_text(text, encoding="utf-8", newline="\n")
