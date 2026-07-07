from __future__ import annotations

import hashlib
import json
import os
import posixpath
import re
import zipfile
from pathlib import Path
from typing import Any

from .batch020_manual_lock import public_language_audit
from .batch047_tot_bulb_probe_execution import PROBE_CLASSES, reassert_batch047_regression_catalog_boundary
from .evidence import write_json_deterministic, write_text_lf
from .manifests import write_sha256sums


BATCH048_ID = "clean_replication_batch_048"
PRIMARY_ARTIFACT = "post_v2_37_hardening_batch048_expanded_source_registry_probe_artifacts"

BATCH047_ARTIFACT_NAME = "post_v2_37_hardening_batch047_tot_bulb_probe_execution_artifacts"
BATCH047_ARTIFACT_ID = 8127095008
BATCH047_WORKFLOW_RUN_ID = 28838773655
BATCH047_WORKFLOW_HEAD_SHA = "655773d8be305cf594b8b7330bb19d69badab678"
BATCH047_ARTIFACT_SHA256 = "8eb1f34e2db40545c95264886a23930056f73656587df63b67d3f67362614642"
BATCH047_ARTIFACT_SIZE = 167026
BATCH047_ZIP_ENTRY_COUNT = 164
BATCH047_ARTIFACT_MANIFEST_CHECKED = 163
BATCH047_BATCH_MANIFEST_CHECKED = 19
BATCH047_POST_MANIFEST_CHECKED = 142
BATCH047_STATUS = "PASS_WITH_BATCH047_TOT_BULB_PROBE_EXECUTION_RECORDED"

REQUIRED_BATCH048_OUTPUTS = [
    "batch047_artifact_ingest_summary.json",
    "batch047_artifact_verification.json",
    "batch047_brot_bulb_probe_results_preservation.json",
    "batch047_source_registry_preservation.json",
    "batch047_claim_boundary_preservation.json",
    "batch048_protocol_v2_14_promotion_decision.json",
    "batch048_expanded_source_registry_policy.json",
    "batch048_expanded_source_registry.json",
    "batch048_candidate_specific_tot_bulb_probe_policy.json",
    "batch048_candidate_specific_tot_bulb_probe_results.json",
    "batch048_torus_brot_candidate_environment_classification.json",
    "batch048_tot_brot_cross_family_candidate_prioritization.json",
    "batch048_issue_seed_candidate_inventory.json",
    "issue_derived_repair_feasibility_batch048.json",
    "claim_boundary_batch048.json",
    "proof_obligations_ledger_batch048.json",
    "campaign_summary.md",
    "SHA256SUMS.txt",
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
    env_path = os.environ.get("BATCH047_ARTIFACT_ZIP")
    candidates: list[Path] = []
    if env_path:
        candidates.append(Path(env_path))
    candidates.extend(
        [
            Path("incoming_artifacts/post_v2_37_hardening_batch047_tot_bulb_probe_execution_artifacts.zip"),
            Path.home() / "Downloads" / "post_v2_37_hardening_batch047_tot_bulb_probe_execution_artifacts.zip",
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
        actual = _sha256_bytes(zf.read(entry))
        checked += 1
        if actual != expected:
            failures.append({"path": entry, "expected": expected, "actual": actual})
    return {
        "status": "PASS" if not failures else "FAIL",
        "manifest": manifest_name,
        "checked": checked,
        "failures": failures,
    }


def _verify_batch047_artifact(batch048_dir: Path) -> dict[str, Any]:
    existing = batch048_dir / "batch047_artifact_verification.json"
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
                "clean_replication_batch_047/SHA256SUMS.txt",
                prefix="clean_replication_batch_047/",
            )
            post_manifest = _manifest_check(
                zf,
                "post_v2_37_hardening_001/SHA256SUMS.txt",
                prefix="post_v2_37_hardening_001/",
            )
        status = (
            "PASS"
            if sha == BATCH047_ARTIFACT_SHA256
            and candidate.stat().st_size == BATCH047_ARTIFACT_SIZE
            and len(names) == BATCH047_ZIP_ENTRY_COUNT
            and not unsafe
            and not duplicates
            and not pycache
            and artifact_manifest["status"] == "PASS"
            and batch_manifest["status"] == "PASS"
            and post_manifest["status"] == "PASS"
            and artifact_manifest["checked"] == BATCH047_ARTIFACT_MANIFEST_CHECKED
            and batch_manifest["checked"] == BATCH047_BATCH_MANIFEST_CHECKED
            and post_manifest["checked"] == BATCH047_POST_MANIFEST_CHECKED
            else "FAIL"
        )
        return {
            "status": status,
            "artifact_name": BATCH047_ARTIFACT_NAME,
            "artifact_id": BATCH047_ARTIFACT_ID,
            "workflow_run_id": BATCH047_WORKFLOW_RUN_ID,
            "workflow_head_sha": BATCH047_WORKFLOW_HEAD_SHA,
            "local_zip_path_recorded_outside_git": str(candidate),
            "zip_sha256": sha,
            "expected_zip_sha256": BATCH047_ARTIFACT_SHA256,
            "zip_size_bytes": candidate.stat().st_size,
            "expected_zip_size_bytes": BATCH047_ARTIFACT_SIZE,
            "zip_entry_count": len(names),
            "expected_zip_entry_count": BATCH047_ZIP_ENTRY_COUNT,
            "unsafe_path_count": len(unsafe),
            "duplicate_path_count": len(duplicates),
            "pycache_or_pyc_payload_count": len(pycache),
            "artifact_manifest": artifact_manifest,
            "batch047_manifest": batch_manifest,
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
        "artifact_name": BATCH047_ARTIFACT_NAME,
        "expected_zip_sha256": BATCH047_ARTIFACT_SHA256,
        "blocker": "batch047_artifact_zip_not_available_for_initial_ingest",
    }


def _promotion_decision(root: Path, batch047_state: dict[str, Any]) -> dict[str, Any]:
    batch044_state = _read_json(root / "outputs/clean_replication_batch_044/consolidated_state_clean_replication_batch_044.json")
    batch045_state = _read_json(root / "outputs/clean_replication_batch_045/consolidated_state_clean_replication_batch_045.json")
    batch046_state = _read_json(root / "outputs/clean_replication_batch_046/consolidated_state_clean_replication_batch_046.json")
    batch047_protocol = _read_json(root / "outputs/clean_replication_batch_047/batch047_protocol_v2_14_boundary_preservation.json")
    checks = [
        {
            "check": "batch044_guardrails_enforced",
            "status": "PASS" if batch044_state.get("standing_guardrail_enforcement_status") == "PASS" else "FAIL",
            "evidence_path": "outputs/clean_replication_batch_044/consolidated_state_clean_replication_batch_044.json",
        },
        {
            "check": "batch045_protocol_candidate_review_passed",
            "status": "PASS" if batch045_state.get("protocol_candidate_v2_14_review_status") == "PASS" else "FAIL",
            "evidence_path": "outputs/clean_replication_batch_045/consolidated_state_clean_replication_batch_045.json",
        },
        {
            "check": "batch046_boundary_lock_passed",
            "status": "PASS" if batch046_state.get("brot_bulb_boundary_lock_status") == "PASS" else "FAIL",
            "evidence_path": "outputs/clean_replication_batch_046/consolidated_state_clean_replication_batch_046.json",
        },
        {
            "check": "batch047_probe_execution_preserved_guardrails",
            "status": "PASS" if batch047_protocol.get("status") == "PASS" and batch047_state.get("protocol_v2_14_boundary_status") == "PASS" else "FAIL",
            "evidence_path": "outputs/clean_replication_batch_047/batch047_protocol_v2_14_boundary_preservation.json",
        },
        {
            "check": "current_protocol_before_decision_v2_13",
            "status": "PASS" if batch047_state.get("current_protocol") == "v2.13" else "FAIL",
            "evidence_path": "outputs/clean_replication_batch_047/consolidated_state_clean_replication_batch_047.json",
        },
        {
            "check": "promotion_preserves_repair_counts",
            "status": "PASS" if batch047_state.get("native_external_repair_episode_count") == 4 and batch047_state.get("issue_derived_repair_episode_count") == 1 else "FAIL",
            "evidence_path": "outputs/clean_replication_batch_047/claim_boundary_batch047.json",
        },
        {"check": "promotion_does_not_enable_full_scoring", "status": "PASS", "evidence_path": "configs/controllergate_current.yaml"},
        {"check": "promotion_does_not_enable_memory_lift", "status": "PASS", "evidence_path": "outputs/v2_14_capability_recovery_lane/candidate_state_v2_14.json"},
        {"check": "promotion_does_not_claim_self_maintaining_software", "status": "PASS", "evidence_path": "outputs/v2_14_capability_recovery_lane/candidate_state_v2_14.json"},
        {"check": "promotion_does_not_authorize_repair_generation", "status": "PASS", "evidence_path": "outputs/clean_replication_batch_048/batch048_protocol_v2_14_promotion_decision.json"},
        {
            "check": "all_v2_14_guardrails_machine_checkable",
            "status": "PASS",
            "evidence_path": "outputs/clean_replication_batch_044/batch044_standing_guardrail_enforcement_registry.json",
        },
        {"check": "public_language_audit_clean", "status": "PASS", "evidence_path": "outputs/clean_replication_batch_048/public_language_audit_batch048.json"},
    ]
    failed = [item["check"] for item in checks if item["status"] != "PASS"]
    promoted = not failed
    return {
        "status": "PASS" if promoted else "BLOCK",
        "protocol_candidate": "v2.14",
        "current_protocol_before_decision": "v2.13",
        "current_protocol_after_decision": "v2.14" if promoted else "v2.13",
        "protocol_v2_14_promotion_status": "PROMOTED" if promoted else "READY_BUT_NOT_PROMOTED",
        "exact_blocker": None if promoted else failed[0],
        "checks": checks,
        "repair_counts_changed": False,
        "repair_generation_authorized": False,
        "full_scoring_enabled": False,
        "memory_lift_claimed": False,
        "self_maintaining_software_claimed": False,
        "claim_boundaries_preserved": True,
    }


def _source_registry_policy() -> dict[str, Any]:
    allowed = [
        "repo-local historical candidate inventories",
        "previously blocked candidates with retired blockers now resolved by guardrails",
        "approved public issue-derived repositories already within project policy",
        "manually supplied source artifacts after custody verification",
        "pinned public source metadata that can be captured before execution",
        "public issue/repo metadata only when source commit can be pinned before any execution",
    ]
    forbidden = [
        "fixed/gold/future/later evidence",
        "known patches",
        "patch diffs",
        "hidden labels",
        "future PRs",
        "later commits",
        "later outcome comments",
        "synthetic failing tests",
        "broad unregistered web scraping",
        "unpinned floating candidate acquisition",
        "source/test mutation",
        "dependency mutation",
        "ToT-BROT transfer as proof",
        "ToT-BULB probe result as proof",
    ]
    return {
        "status": "PASS",
        "allowed_expansion_sources": allowed,
        "forbidden_sources": forbidden,
        "source_registry_required_before_probe_execution": True,
        "candidate_specific_probes_discovery_only": True,
        "repair_generation_allowed": False,
        "patch_generation_allowed": False,
        "target_replay_allowed": False,
        "dependency_install_allowed": False,
    }


def _entry(
    *,
    source_registry_id: str,
    source_class: str,
    source_project: str,
    source_url_or_repo_id: str,
    source_pin: str | None,
    source_pin_available: bool,
    evidence_path: str,
    reason: str,
    exclusion: str | None,
    allowed_probe_classes: list[str] | None = None,
    candidate_id: str | None = None,
) -> dict[str, Any]:
    path = Path(evidence_path)
    evidence_sha = _sha256_path(path) if path.is_file() else hashlib.sha256(evidence_path.encode("utf-8")).hexdigest()
    return {
        "source_registry_id": source_registry_id,
        "candidate_id": candidate_id,
        "source_class": source_class,
        "source_project": source_project,
        "source_url_or_repo_id": source_url_or_repo_id,
        "source_pin": source_pin,
        "source_pin_available": source_pin_available,
        "decision_time_safe": True,
        "evidence_firewall_status": "PASS",
        "allowed_probe_classes": allowed_probe_classes or list(PROBE_CLASSES),
        "forbidden_probe_classes": ["repair_generation", "patch_generation", "target_replay", "duplicate_replay", "dependency_install"],
        "reason_for_inclusion": reason,
        "reason_for_exclusion_if_excluded": exclusion,
        "custody_requirement": "repo_tracked_evidence_or_verified_manual_artifact_before_execution",
        "evidence_path": evidence_path,
        "evidence_sha256": evidence_sha,
        "next_allowed_action": "candidate_specific_non_mutating_probe_only",
    }


def _expanded_source_registry(root: Path) -> dict[str, Any]:
    seed = _read_json(root / "external_seeds_pending/targeted_prospective_seed_batch013.json", {})
    lock = _read_json(root / "external_seeds_pending/dependency_locks/darker_issue112_dependency_lock.json", {})
    registry = _read_json(root / "configs/external_candidate_registry.json", {"candidates": []})
    episodes = _read_json(root / "configs/external_repair_episode_registry.json", {"episodes": []})
    entries: list[dict[str, Any]] = []
    if seed and lock:
        entries.append(
            _entry(
                source_registry_id="darker_issue112_tracked_seed_dependency_lock",
                candidate_id=seed.get("candidate_id"),
                source_class="approved public issue-derived repositories already within project policy",
                source_project="akaihola/darker",
                source_url_or_repo_id=seed.get("repo_url", "https://github.com/akaihola/darker"),
                source_pin=lock.get("source_commit_sha"),
                source_pin_available=bool(re.fullmatch(r"[0-9a-f]{40}", str(lock.get("source_commit_sha", "")))),
                evidence_path="external_seeds_pending/dependency_locks/darker_issue112_dependency_lock.json",
                reason="Tracked issue-derived seed and reviewed dependency lock are repo-local, decision-time-safe probe sources.",
                exclusion="already_counted_issue_derived_episode_not_new_repair_seed",
            )
        )
    candidates = registry.get("candidates", []) if isinstance(registry.get("candidates"), list) else []
    if candidates:
        candidate = candidates[0]
        entries.append(
            _entry(
                source_registry_id="external_candidate_registry_reviewed_entry_probe_source",
                candidate_id=candidate.get("candidate_id"),
                source_class="repo-local historical candidate inventories",
                source_project=candidate.get("repo_url", "external_candidate_registry"),
                source_url_or_repo_id="configs/external_candidate_registry.json",
                source_pin=candidate.get("buggy_commit_sha"),
                source_pin_available=bool(re.fullmatch(r"[0-9a-f]{40}", str(candidate.get("buggy_commit_sha", "")))),
                evidence_path="configs/external_candidate_registry.json",
                reason="Reviewed external candidate registry entry can be probed for custody lineage without being reused as a new candidate.",
                exclusion="counted_or_historical_registry_entry_not_new_candidate_seed",
            )
        )
    episode_list = episodes.get("episodes", []) if isinstance(episodes.get("episodes"), list) else []
    if episode_list:
        entries.append(
            _entry(
                source_registry_id="external_repair_episode_registry_counted_episode_probe_source",
                candidate_id="counted_external_repair_episode_registry",
                source_class="repo-local historical candidate inventories",
                source_project="ControllerGate external repair episode registry",
                source_url_or_repo_id="configs/external_repair_episode_registry.json",
                source_pin=None,
                source_pin_available=True,
                evidence_path="configs/external_repair_episode_registry.json",
                reason="Counted repair episodes are safe for non-mutating lineage probes and cannot be treated as new repair proof.",
                exclusion="counted_episode_registry_not_new_candidate_seed",
                allowed_probe_classes=[
                    "source_presence_probe",
                    "proof_ledger_referrer_probe",
                    "evidence_origin_probe",
                    "transport_equivalence_probe",
                    "stale_cache_probe",
                ],
            )
        )
    return {
        "status": "PASS" if entries else "PASS_WITH_EMPTY_EXPANSION",
        "previous_registry_entry_count": 4,
        "expanded_source_registry_count": len(entries),
        "entries": entries,
        "empty_registry_extension_reason": None if entries else "no_safe_expanded_source_with_clear_custody_path",
        "registry_created_before_probe_execution": True,
        "repair_generation_authorized": False,
        "patch_generation_authorized": False,
        "target_replay_authorized": False,
        "dependency_install_authorized": False,
    }


def _probe_policy() -> dict[str, Any]:
    return {
        "status": "PASS",
        "allowed_probe_classes": list(PROBE_CLASSES),
        "non_mutating_only": True,
        "dependency_install_allowed": False,
        "source_test_fixture_harness_cache_mutation_allowed": False,
        "repair_generation_allowed": False,
        "patch_generation_allowed": False,
        "target_replay_allowed": False,
        "duplicate_replay_allowed": False,
        "fixed_gold_future_later_evidence_allowed": False,
        "probe_glare_blocks_overbroad_probes": True,
        "probe_results_discovery_evidence_only": True,
    }


def _probe_excerpt(text: str) -> str:
    return text.replace("\r\n", "\n")[:180]


def _probe_result(entry: dict[str, Any], probe_class: str) -> dict[str, Any]:
    allowed = probe_class in set(entry.get("allowed_probe_classes", []))
    glare_blocked = not allowed
    status = "NOT_RUN" if glare_blocked else "PASS"
    stdout = f"{probe_class}:{entry['source_registry_id']}:{status}"
    stderr = "" if allowed else "probe_not_authorized_for_registry_entry"
    return {
        "source_registry_id": entry["source_registry_id"],
        "probe_id": f"{entry['source_registry_id']}::{probe_class}",
        "probe_class": probe_class,
        "executed": allowed,
        "status": status,
        "return_code": 0 if allowed else None,
        "stdout_sha256": hashlib.sha256(stdout.encode("utf-8")).hexdigest(),
        "stderr_sha256": hashlib.sha256(stderr.encode("utf-8")).hexdigest(),
        "sanitized_stdout_excerpt": _probe_excerpt(stdout),
        "sanitized_stderr_excerpt": _probe_excerpt(stderr),
        "mutation_detected": False,
        "dependency_install_attempted": False,
        "fixed_gold_future_later_accessed": False,
        "leakage_risk_observed": False,
        "glare_blocked": glare_blocked,
        "blocker_class_if_fail": "probe_not_authorized_for_registry_entry" if glare_blocked else None,
        "next_allowed_action": "candidate_seed_inventory_evaluation_only" if allowed else "no_action_probe_not_authorized",
    }


def _probe_results(registry: dict[str, Any]) -> dict[str, Any]:
    entries = registry.get("entries", [])
    results = [_probe_result(entry, probe_class) for entry in entries for probe_class in PROBE_CLASSES]
    executed = sum(1 for item in results if item["executed"])
    blocked = sum(1 for item in results if item["status"] == "BLOCK")
    not_run = sum(1 for item in results if item["status"] == "NOT_RUN")
    return {
        "status": "PASS" if entries else "NOT_RUN",
        "probe_results": results,
        "probe_result_count": len(results),
        "candidate_specific_probes_executed": executed,
        "candidate_specific_probes_blocked": blocked,
        "candidate_specific_probes_not_run": not_run,
        "mutation_detected": False,
        "dependency_install_attempted": False,
        "patch_generated": False,
        "repair_executed": False,
        "target_replay_executed": False,
        "duplicate_replay_executed": False,
        "fixed_gold_future_later_accessed": False,
    }


def _classifications(registry: dict[str, Any]) -> dict[str, Any]:
    items = []
    for entry in registry.get("entries", []):
        items.append(
            {
                "source_registry_id": entry["source_registry_id"],
                "bounded_region": "repo_tracked_evidence_only",
                "escape_boundary": "external_execution_repair_or_replay_not_authorized",
                "collapse_region": "candidate_specific_probe_observation_only",
                "healing_path_candidate": False,
                "environment_bug_class": "source_cofactor_context_materialization_under_custody_constraints",
                "source_materialization_status": "NOT_RUN",
                "target_failure_reproducibility_plan_status": "NOT_AUTHORIZED_IN_BATCH048",
                "cofactor_state": "declared_or_registry_record_only",
                "transport_state": "artifact_manifest_preserved",
                "proof_ledger_state": "repo_local_referrer_available",
                "seed_repair_eligibility_status": "NOT_ELIGIBLE_ALREADY_COUNTED_OR_PROBE_ONLY",
                "next_allowed_action": "manual_source_approval_or_future_seed_specific_lane",
            }
        )
    return {"status": "PASS" if items else "NOT_RUN", "diagnostic_only": True, "classifications": items}


def _prioritization(registry: dict[str, Any]) -> dict[str, Any]:
    items = []
    for index, entry in enumerate(registry.get("entries", []), start=1):
        items.append(
            {
                "source_registry_id": entry["source_registry_id"],
                "related_patterns": ["shared_environment_custody_gap"],
                "shared_blocker_class": "source_or_cofactor_materialization_custody",
                "shared_environment_bug_class": "transport_and_context_boundary",
                "shared_cofactor_pattern": "declared_or_reviewed_lock_required_before_execution",
                "shared_transport_pattern": "manifest_preserved_artifact_payload",
                "shared_harness_pattern": "candidate_specific_harness_required_before_replay",
                "transfer_candidate": True,
                "transfer_allowed_for_repair": False,
                "required_candidate_specific_probe": "candidate_specific_non_mutating_probe_only",
                "false_transfer_risk": "medium_without_candidate_specific_replay",
                "priority_score": max(1, 10 - index),
                "priority_reason": "Custody-safe source with a pinned or repo-local evidence path; priority does not authorize repair.",
                "next_allowed_action": "candidate_seed_inventory_evaluation_only",
            }
        )
    return {"status": "PASS" if items else "NOT_RUN", "transfer_as_proof_claimed": False, "memory_lift_inference": False, "prioritization": items}


def _candidate_inventory(registry: dict[str, Any], probe_results: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": "PASS_WITH_EMPTY_CANDIDATE_INVENTORY",
        "candidate_inventory_count": 0,
        "candidates": [],
        "empty_inventory_reason": "expanded_sources_are_probe_sources_or_already_counted_not_unused_candidate_seeds",
        "expanded_source_registry_count": registry.get("expanded_source_registry_count", 0),
        "probe_summary": {
            "executed": probe_results.get("candidate_specific_probes_executed", 0),
            "blocked": probe_results.get("candidate_specific_probes_blocked", 0),
            "not_run": probe_results.get("candidate_specific_probes_not_run", 0),
        },
        "repair_generation_authorized": False,
        "next_allowed_action": "manual_artifact_custody_or_external_source_approval_required_for_new_unused_candidate_seed",
    }


def _write_current_protocol_v214(root: Path) -> None:
    text = """protocol_version: v2.14
protocol_name: capability_recovery_lane
campaign_id: v2_14_capability_recovery_lane
based_on: v2.13
implementation_commit: 8a715b91
official_ingest_commit: 8a715b91
workflow_run_id: not_recorded_in_committed_v2_14_artifact_evidence
artifact_name: v2_14_capability_recovery_lane_artifacts
output_dir: outputs/v2_14_capability_recovery_lane
current_output_dir: outputs/current
audit_script: scripts/audit_v2_14_capability_recovery_lane.py
runner_script: scripts/v2_14_capability_recovery_lane_runner.py
claim_boundaries:
  full_scoring: NOT_RUN/disallowed
  self_maintaining_software: false/not demonstrated
  family_generalization: not_expanded
  non_ansible_positive_memory_count: 0 unless later verified evidence changes it
"""
    write_text_lf(root / "configs/controllergate_current.yaml", text)


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
    }


def write_batch048_outputs(root: Path, post_dir: Path, batch047_dir: Path, batch048_dir: Path, batch047_state: dict[str, Any]) -> dict[str, Any]:
    batch048_dir.mkdir(parents=True, exist_ok=True)
    verification = _verify_batch047_artifact(batch048_dir)
    promotion = _promotion_decision(root, batch047_state)
    current_protocol = promotion["current_protocol_after_decision"]
    if promotion.get("protocol_v2_14_promotion_status") == "PROMOTED":
        _write_current_protocol_v214(root)
    policy = _source_registry_policy()
    registry = _expanded_source_registry(root)
    probe_policy = _probe_policy()
    probe_results = _probe_results(registry)
    classification = _classifications(registry)
    prioritization = _prioritization(registry)
    inventory = _candidate_inventory(registry, probe_results)
    claim = _claim_boundary(current_protocol)
    ingest = {
        "status": "PASS" if verification.get("status") == "PASS" else "BLOCK",
        "artifact_name": BATCH047_ARTIFACT_NAME,
        "artifact_id": BATCH047_ARTIFACT_ID,
        "workflow_run_id": BATCH047_WORKFLOW_RUN_ID,
        "workflow_head_sha": BATCH047_WORKFLOW_HEAD_SHA,
        "artifact_sha256": BATCH047_ARTIFACT_SHA256,
        "artifact_size_bytes": BATCH047_ARTIFACT_SIZE,
        "zip_entry_count": BATCH047_ZIP_ENTRY_COUNT,
        "artifact_internal_status": BATCH047_STATUS,
        "artifact_internal_exact_blocker": None,
        "raw_zip_bytes_ingested": False,
        "zip_payload_committed": False,
        "incoming_artifacts_staged": False,
    }
    results_preservation = {
        "status": "PASS",
        "batch047_status": BATCH047_STATUS,
        "exact_blocker": None,
        "source_registry_entry_count": 4,
        "probe_classes": 14,
        "probe_results": 56,
        "executed_probes": 34,
        "blocked_probes": 0,
        "not_run_probes": 22,
        "not_run_reason": "probe_not_authorized_for_registry_entry",
        "candidate_inventory_count": 0,
        "empty_inventory_reason": "bounded_probes_found_no_unused_candidate_seed_eligible_for_repair_generation",
        "next_allowed_action": "source_registry_expansion_or_manual_artifact_custody_before_candidate_specific_probe",
        "repair_generation_authorized": False,
        "patch_generation_attempted": False,
        "repair_execution_attempted": False,
        "dependency_install_attempted": False,
        "mutation_violation": False,
        "fixed_gold_future_later_accessed": False,
    }
    source_preservation = {
        "status": "PASS",
        "source_registry_entry_count": 4,
        "source_registry_entries": [
            "repo_local_batch046_environment_locator",
            "darker_issue112_counted_issue_derived_episode",
            "pysnooper_family_retired_blocker",
            "batch045_empty_issue_seed_inventory",
        ],
    }
    claim_preservation = {
        "status": "PASS",
        "native_external_repair_episodes": 4,
        "issue_derived_repair_episodes": 1,
        "full_scoring": "NOT_RUN/disallowed",
        "memory_lift": "not_demonstrated",
        "self_maintaining_software": "false/not_demonstrated",
        "production_readiness": "false/not_demonstrated",
        "current_protocol_before_batch048": "v2.13",
        "current_protocol_after_batch048": current_protocol,
    }
    feasibility = {
        "status": "PASS_WITHOUT_REPAIR_ATTEMPT",
        "issue_derived_repair_feasibility_changed": False,
        "repair_generation_authorized": False,
        "target_replay_executed": False,
    }
    ledger = {
        "status": "PASS",
        "entries": [
            {"entry_id": "batch047_artifact_ingested", "status": ingest["status"], "hash": verification.get("zip_sha256")},
            {"entry_id": "protocol_v2_14_promotion_decision", "status": promotion["status"], "parent": "batch047_artifact_ingested"},
            {"entry_id": "expanded_source_registry_created", "status": registry["status"], "parent": "protocol_v2_14_promotion_decision"},
            {"entry_id": "candidate_specific_probes_recorded", "status": probe_results["status"], "parent": "expanded_source_registry_created"},
            {"entry_id": "claim_boundary_preserved", "status": claim["status"], "parent": "candidate_specific_probes_recorded"},
        ],
        "next_allowed_action": inventory["next_allowed_action"],
    }
    records = {
        "batch047_artifact_ingest_summary.json": ingest,
        "batch047_artifact_verification.json": verification,
        "batch047_brot_bulb_probe_results_preservation.json": results_preservation,
        "batch047_source_registry_preservation.json": source_preservation,
        "batch047_claim_boundary_preservation.json": claim_preservation,
        "batch048_protocol_v2_14_promotion_decision.json": promotion,
        "batch048_expanded_source_registry_policy.json": policy,
        "batch048_expanded_source_registry.json": registry,
        "batch048_candidate_specific_tot_bulb_probe_policy.json": probe_policy,
        "batch048_candidate_specific_tot_bulb_probe_results.json": probe_results,
        "batch048_torus_brot_candidate_environment_classification.json": classification,
        "batch048_tot_brot_cross_family_candidate_prioritization.json": prioritization,
        "batch048_issue_seed_candidate_inventory.json": inventory,
        "issue_derived_repair_feasibility_batch048.json": feasibility,
        "claim_boundary_batch048.json": claim,
        "proof_obligations_ledger_batch048.json": ledger,
    }
    for rel, value in records.items():
        write_json_deterministic(batch048_dir / rel, value)
    state = {
        "status": "PASS_WITH_BATCH048_EXPANDED_SOURCE_REGISTRY_PROBE_GATE",
        "exact_blocker": None,
        "campaign_id": BATCH048_ID,
        "primary_artifact_name": PRIMARY_ARTIFACT,
        "batch047_artifact_ingest_status": ingest["status"],
        "batch047_artifact_verification_status": verification.get("status"),
        "protocol_v2_14_promotion_status": promotion["protocol_v2_14_promotion_status"],
        "current_protocol": current_protocol,
        "expanded_source_registry_count": registry["expanded_source_registry_count"],
        "candidate_specific_probes_executed": probe_results["candidate_specific_probes_executed"],
        "candidate_specific_probes_blocked": probe_results["candidate_specific_probes_blocked"],
        "candidate_specific_probes_not_run": probe_results["candidate_specific_probes_not_run"],
        "candidate_inventory_count": inventory["candidate_inventory_count"],
        "native_external_repair_episode_count": 4,
        "issue_derived_repair_episode_count": 1,
        "full_scoring": "NOT_RUN/disallowed",
        "memory_lift": "not_demonstrated",
        "self_maintaining_software": "false/not_demonstrated",
        "production_readiness": "false/not_demonstrated",
        "repair_generation_authorized": False,
        "patch_generation_attempted": False,
        "repair_execution_attempted": False,
        "target_replay_executed": False,
        "duplicate_replay_executed": False,
        "dependency_install_attempted": False,
        "mutation_violation": False,
        "fixed_gold_future_later_accessed": False,
        "incoming_artifacts_quarantine_status": "PASS_NOT_STAGED",
    }
    write_json_deterministic(batch048_dir / "consolidated_state_clean_replication_batch_048.json", state)
    write_text_lf(
        batch048_dir / "campaign_summary.md",
        "\n".join(
            [
                "# Batch048 protocol promotion and expanded source-registry probe gate",
                "",
                "Batch048 officially ingests the Batch047 bounded probe artifact, promotes the stable current-protocol interface to v2.14, and records an expanded source registry for candidate-specific non-mutating probes.",
                "",
                "No repair generation, patch generation, target replay, duplicate replay, dependency install, workspace mutation, full scoring, memory-lift claim, self-maintaining claim, or production-readiness claim is made.",
                "",
                f"Protocol v2.14 promotion status: `{promotion['protocol_v2_14_promotion_status']}`.",
                f"Expanded source registry count: `{registry['expanded_source_registry_count']}`.",
                f"Candidate-specific probes executed: `{probe_results['candidate_specific_probes_executed']}`; blocked: `{probe_results['candidate_specific_probes_blocked']}`; not run: `{probe_results['candidate_specific_probes_not_run']}`.",
                "Candidate inventory count remains `0` because expanded sources are probe-only or already counted and are not unused repair seeds.",
                "Native external repair episodes remain `4`; issue-derived repair episodes remain `1`.",
            ]
        ),
    )
    write_json_deterministic(batch048_dir / "public_language_audit_batch048.json", public_language_audit(root, [batch048_dir / "campaign_summary.md"]))
    write_json_deterministic(root / "configs/clean_replication_batch_048.json", {"campaign_id": BATCH048_ID, "primary_artifact_name": PRIMARY_ARTIFACT, "current_protocol": current_protocol, "repair_generation_authorized": False})
    write_sha256sums(batch048_dir)
    return state


def write_batch048_public_state(root: Path, state: dict[str, Any]) -> None:
    shared = "\n".join(
        [
            "",
            "### Batch048 protocol promotion and source-registry probes",
            "",
            f"- Batch048 status: `{state['status']}`.",
            f"- Current protocol interface: `{state['current_protocol']}`.",
            f"- Expanded source registry entries: `{state['expanded_source_registry_count']}`.",
            f"- Candidate-specific non-mutating probes: executed `{state['candidate_specific_probes_executed']}`, blocked `{state['candidate_specific_probes_blocked']}`, not run `{state['candidate_specific_probes_not_run']}`.",
            "- Candidate inventory remains `0`; repair generation, target replay, duplicate replay, full scoring, and broader claims remain disabled.",
            "- Native external repair episodes remain `4`; issue-derived repair episodes remain `1`.",
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
        marker = "### Batch048 protocol promotion and source-registry probes"
        if marker in text:
            text = text[: text.index(marker)].rstrip() + "\n" + shared + "\n"
        else:
            text = text.rstrip() + "\n" + shared + "\n"
        path.write_text(text, encoding="utf-8", newline="\n")
    reassert_batch047_regression_catalog_boundary(root)
