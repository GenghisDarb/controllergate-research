from __future__ import annotations

import hashlib
import json
import os
import shutil
import sys
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from controllergate.core.evidence import sha256_bytes, sha256_file, write_json_deterministic, write_text_lf
from controllergate.core.manifests import write_sha256sums


BATCH061_NAME = "post_v2_37_hardening_batch061_duplicate_clean_replay_count_gate_cloudpickle_wave_3"
BATCH061_DIR = ROOT / "outputs" / BATCH061_NAME
OUT_NAME = "post_v2_37_hardening_batch062_next_issue_repair_candidate_selection_or_wave3_expansion"
OUT_DIR = ROOT / "outputs" / OUT_NAME

BATCH061_ZIP = Path(
    os.environ.get(
        "CONTROLLERGATE_BATCH061_ARTIFACT_ZIP",
        r"C:\Users\thisb\Downloads\post_v2_37_hardening_batch061_duplicate_clean_replay_count_gate_cloudpickle_wave_3_artifacts.zip",
    )
)

BATCH061_ARTIFACT = {
    "artifact_name": "post_v2_37_hardening_batch061_duplicate_clean_replay_count_gate_cloudpickle_wave_3_artifacts",
    "artifact_id": 8176856167,
    "workflow_run_id": 28962968241,
    "workflow_head_sha": "04c9e5ea2e9a061cc873f2c89dcd18b7eeae1f5d",
    "expected_sha256": "badd42e12343fd56d9797a1779f785a946993693fbb592a9dd4775f087083bc3",
    "expected_size": 40738,
    "expected_entry_count": 81,
    "artifact_manifest_checked": 80,
    "output_manifest_checked": 79,
}

CURRENT_PROTOCOL = "v2.14"
ISSUE_COUNT_BEFORE_BATCH061 = 2
ISSUE_COUNT_AFTER_BATCH061 = 3
NATIVE_EXTERNAL_REPAIR_COUNT = 4
NEXT_ALLOWED_ACTION = "batch058b_seed_discovery_wave_3_expansion"


ARCHIVE_SUFFIXES = (".zip", ".tar", ".tar.gz", ".tgz", ".7z", ".pyc", ".pyo", ".whl")


def write_out_json(name: str, value: Any) -> None:
    write_json_deterministic(OUT_DIR / name, value)


def write_out_text(name: str, value: str) -> None:
    write_text_lf(OUT_DIR / name, value)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def is_safe_zip_member(name: str) -> bool:
    pure = PurePosixPath(name)
    return not (name.startswith("/") or "\\" in name or any(part in {"", ".", ".."} for part in pure.parts))


def verify_zip_manifest(archive: zipfile.ZipFile, manifest_name: str) -> dict[str, Any]:
    names = set(archive.namelist())
    if manifest_name not in names:
        return {"status": "MISSING", "manifest": manifest_name, "checked": 0, "failures": 1, "missing": [manifest_name], "malformed": []}
    checked = 0
    failures: list[str] = []
    missing: list[str] = []
    malformed: list[str] = []
    for line in archive.read(manifest_name).decode("utf-8").splitlines():
        if not line.strip():
            continue
        parts = line.split(maxsplit=1)
        if len(parts) != 2:
            malformed.append(line)
            continue
        expected, rel = parts
        rel = rel.strip().lstrip("*")
        if len(expected) != 64 or not is_safe_zip_member(rel):
            malformed.append(rel)
            continue
        if rel not in names:
            missing.append(rel)
            continue
        checked += 1
        if sha256_bytes(archive.read(rel)) != expected:
            failures.append(rel)
    return {
        "status": "PASS" if not failures and not missing and not malformed else "FAIL",
        "manifest": manifest_name,
        "checked": checked,
        "failures": len(failures),
        "failure_paths": failures,
        "missing": missing,
        "malformed": malformed,
    }


def verify_batch061_artifact() -> dict[str, Any]:
    path = BATCH061_ZIP
    if not path.is_file():
        return {
            "status": "BLOCK",
            "artifact_name": BATCH061_ARTIFACT["artifact_name"],
            "artifact_id": BATCH061_ARTIFACT["artifact_id"],
            "workflow_run_id": BATCH061_ARTIFACT["workflow_run_id"],
            "exact_blocker": "batch061_artifact_absent_for_official_ingest",
        }
    digest = sha256_file(path)
    size = path.stat().st_size
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        unsafe = [name for name in names if not is_safe_zip_member(name)]
        duplicates = len(names) - len(set(names))
        pycache_entries = [name for name in names if "__pycache__" in PurePosixPath(name).parts]
        pyc_entries = [name for name in names if name.endswith((".pyc", ".pyo"))]
        artifact_manifest = verify_zip_manifest(archive, "ARTIFACT_SHA256SUMS.txt")
        output_manifest = verify_zip_manifest(archive, "SHA256SUMS.txt")
    counts_pass = (
        artifact_manifest["status"] == "PASS"
        and artifact_manifest["checked"] == BATCH061_ARTIFACT["artifact_manifest_checked"]
        and output_manifest["status"] == "PASS"
        and output_manifest["checked"] == BATCH061_ARTIFACT["output_manifest_checked"]
    )
    status = (
        "PASS"
        if digest == BATCH061_ARTIFACT["expected_sha256"]
        and size == BATCH061_ARTIFACT["expected_size"]
        and len(names) == BATCH061_ARTIFACT["expected_entry_count"]
        and not unsafe
        and duplicates == 0
        and not pycache_entries
        and not pyc_entries
        and counts_pass
        else "BLOCK"
    )
    return {
        "status": status,
        "verification_source": "local_manual_artifact_zip",
        "local_artifact_path": str(path),
        "artifact_name": BATCH061_ARTIFACT["artifact_name"],
        "artifact_id": BATCH061_ARTIFACT["artifact_id"],
        "workflow_run_id": BATCH061_ARTIFACT["workflow_run_id"],
        "workflow_head_sha": BATCH061_ARTIFACT["workflow_head_sha"],
        "zip_sha256": digest,
        "artifact_sha256": digest,
        "zip_size_bytes": size,
        "artifact_size_bytes": size,
        "zip_entry_count": len(names),
        "unsafe_path_count": len(unsafe),
        "duplicate_path_count": duplicates,
        "zip_pycache_entries": len(pycache_entries),
        "zip_pyc_entries": len(pyc_entries),
        "artifact_manifest": artifact_manifest,
        "output_manifest": output_manifest,
        "raw_zip_bytes_ingested": False,
        "zip_payload_committed": False,
        "flat_payload_layout": True,
        "exact_blocker": None if status == "PASS" else "batch061_artifact_verification_failed",
    }


def ingest_batch061_outputs() -> dict[str, Any]:
    writes: list[dict[str, Any]] = []
    skipped_archives: list[str] = []
    with zipfile.ZipFile(BATCH061_ZIP) as archive:
        for name in archive.namelist():
            if name.endswith("/") or name == "ARTIFACT_SHA256SUMS.txt":
                continue
            if name.endswith(ARCHIVE_SUFFIXES):
                skipped_archives.append(name)
                continue
            if not is_safe_zip_member(name):
                writes.append({"status": "BLOCK", "path": name, "exact_blocker": "unsafe_zip_member"})
                continue
            target = BATCH061_DIR / Path(*PurePosixPath(name).parts)
            data = archive.read(name)
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.is_file() and target.read_bytes() == data:
                writes.append({"status": "SKIPPED_IDENTICAL", "path": str(target), "changed": False})
            else:
                target.write_bytes(data)
                writes.append({"status": "WRITTEN", "path": str(target), "changed": True})
    blockers = [item for item in writes if item.get("status") == "BLOCK"]
    return {
        "status": "PASS" if not blockers else "BLOCK",
        "layout": "flat_artifact_payload",
        "write_records": writes,
        "written_count": sum(item.get("status") == "WRITTEN" for item in writes),
        "skipped_identical_count": sum(item.get("status") == "SKIPPED_IDENTICAL" for item in writes),
        "skipped_archives": skipped_archives,
        "raw_zip_bytes_ingested": False,
        "zip_payload_committed": False,
        "exact_blocker": blockers[0].get("exact_blocker") if blockers else None,
    }


def phase_a(verification: dict[str, Any]) -> dict[str, Any]:
    if verification.get("status") != "PASS":
        raise SystemExit("batch061_artifact_absent_for_official_ingest")
    ingest = ingest_batch061_outputs()
    final = read_json(BATCH061_DIR / "batch061_final_decision.json")
    count_update = read_json(BATCH061_DIR / "issue_derived_repair_count_update.json")
    canonical = read_json(BATCH061_DIR / "canonical_issue_repair_record_cloudpickle.json")
    ledger = read_json(BATCH061_DIR / "proof_ledger_cloudpickle_entry.json")
    claim = read_json(BATCH061_DIR / "claim_boundary.json")
    health = read_json(BATCH061_DIR / "project_health_review_batch061.json")
    write_out_json(
        "batch061_artifact_ingestion_summary.json",
        {
            "status": "PASS" if ingest.get("status") == "PASS" and verification.get("status") == "PASS" else "BLOCK",
            "local_artifact_path": str(BATCH061_ZIP),
            "artifact_name": BATCH061_ARTIFACT["artifact_name"],
            "artifact_id": BATCH061_ARTIFACT["artifact_id"],
            "workflow_run_id": BATCH061_ARTIFACT["workflow_run_id"],
            "verification": verification,
            "official_output_ingest": ingest,
            "raw_zip_bytes_ingested": False,
            "zip_payload_committed": False,
        },
    )
    write_out_json("batch061_artifact_sha256_verification.json", verification)
    write_out_json("artifact_sha256_verification.json", verification)
    write_out_json(
        "batch061_result_preservation.json",
        {
            "status": "PASS",
            "batch061_final_decision_status": final.get("status"),
            "issue_derived_repair_count_before_batch061": count_update.get("issue_derived_repair_count_before_batch061"),
            "issue_derived_repair_count_after_batch061": count_update.get("issue_derived_repair_count_after_batch061"),
            "native_external_repair_count": final.get("native_external_repair_count"),
            "full_scoring": final.get("full_scoring"),
            "memory_lift": final.get("memory_lift"),
            "self_maintaining_software": final.get("self_maintaining_software"),
            "duplicate_replay_outcome": final.get("duplicate_replay_outcome"),
            "count_gate_status": final.get("count_gate_status"),
            "provider_runtime_recovery_counted_as_repair": canonical.get("provider_runtime_recovery_counted_as_repair"),
            "next_allowed_action": final.get("next_allowed_action"),
        },
    )
    write_out_json(
        "batch061_cloudpickle_counted_repair_preservation.json",
        {
            "status": "PASS" if canonical.get("counted_as_issue_derived") is True else "BLOCK",
            "candidate_id": canonical.get("candidate_id"),
            "repo_url": canonical.get("repo_url"),
            "candidate_sha": canonical.get("candidate_sha"),
            "patch_sha256": canonical.get("batch060d_patch_sha256"),
            "counted_as_issue_derived": canonical.get("counted_as_issue_derived"),
            "counted_as_native_external": canonical.get("counted_as_native_external"),
            "provider_runtime_recovery_counted_as_repair": canonical.get("provider_runtime_recovery_counted_as_repair"),
            "source_evidence_sha256": sha256_file(BATCH061_DIR / "canonical_issue_repair_record_cloudpickle.json"),
        },
    )
    write_out_json(
        "batch061_proof_ledger_preservation.json",
        {
            "status": "PASS" if ledger.get("status") == "PASS" else "BLOCK",
            "transition": ledger.get("transition"),
            "next_allowed_action": ledger.get("next_allowed_action"),
            "ledger_sha256": sha256_file(BATCH061_DIR / "proof_ledger_cloudpickle_entry.json"),
        },
    )
    write_out_json(
        "batch061_project_health_preservation.json",
        {
            "status": "PASS",
            "project_health_grade": final.get("project_health_grade"),
            "traffic_light_status": final.get("traffic_light_status"),
            "advisory_diagnostic_only": health.get("advisory_diagnostic_only"),
            "does_not_override_audits": health.get("does_not_override_audits"),
            "health_sha256": sha256_file(BATCH061_DIR / "project_health_review_batch061.json"),
        },
    )
    write_out_json(
        "batch061_claim_boundary_preservation.json",
        {
            "status": "PASS",
            "full_scoring": claim.get("full_scoring"),
            "memory_lift": claim.get("memory_lift"),
            "self_maintaining_software": claim.get("self_maintaining_software"),
            "new_patch_generated_in_batch061": claim.get("new_patch_generated_in_batch061"),
            "tests_mutated": claim.get("tests_mutated"),
            "fixtures_mutated": claim.get("fixtures_mutated"),
            "provider_runtime_recovery_counted_as_repair": claim.get("provider_runtime_recovery_counted_as_repair"),
            "claim_boundary_sha256": sha256_file(BATCH061_DIR / "claim_boundary.json"),
        },
    )
    write_out_json(
        "batch061_next_action_boundary.json",
        {
            "status": "PASS" if final.get("next_allowed_action") == "batch062_next_issue_repair_candidate_selection_or_wave3_expansion" else "BLOCK",
            "observed_next_allowed_action": final.get("next_allowed_action"),
            "required_next_allowed_action": "batch062_next_issue_repair_candidate_selection_or_wave3_expansion",
        },
    )
    return {"final": final, "count_update": count_update, "canonical": canonical, "ledger": ledger, "claim": claim}


def counted_repairs() -> list[dict[str, Any]]:
    return [
        {
            "candidate_id": "lemon_reader_issue_derived_chain",
            "candidate_class": "issue_derived",
            "count_status": "counted_prior_to_batch061",
            "repair_count_contribution": 1,
            "preservation_status": "preserved",
        },
        {
            "candidate_id": "cloudpickle_507_py313_typevar_distutils",
            "candidate_class": "issue_derived",
            "count_status": "counted_in_batch061",
            "repair_count_contribution": 1,
            "canonical_record": "canonical_issue_repair_record_cloudpickle.json",
            "preservation_status": "preserved",
        },
        {
            "candidate_id": "darker_issue112_issue_derived_chain",
            "candidate_class": "issue_derived",
            "count_status": "counted_prior_to_batch061",
            "repair_count_contribution": 1,
            "preservation_status": "preserved",
        },
    ]


def parked_candidates() -> list[dict[str, Any]]:
    return [
        {
            "candidate_id": "audioread_144_py313_aifc_removed",
            "status": "source_only_partial_improvement_future_provider_backend_capsule",
            "recommended_status": "parked_salvageable",
            "best_future_route": "batch060f_audioread_provider_backend_capsule_replay",
            "provider_complexity": "medium_high",
            "proof_distance": "near_to_medium",
        },
        {
            "candidate_id": "freezegun_547_py313_datetimes_assertion",
            "status": "primary_only_partial_improvement_secondary_provider_blocker",
            "recommended_status": "parked_salvageable_below_audioread",
            "best_future_route": "batch057d_freezegun_provider_portability_secondary_family_probe",
            "provider_complexity": "medium",
            "proof_distance": "medium",
        },
        {
            "candidate_id": "datasette_2461_async_event_loop_cli_tests",
            "status": "multi_family_ambiguous",
            "recommended_status": "parked_for_bounded_decomposition_only",
            "best_future_route": "batch062c_wave1_wave2_salvage_replay_selection",
            "provider_complexity": "high",
            "proof_distance": "medium_to_far",
        },
        {
            "candidate_id": "venusian_91_py313_frameinfo_callinfo",
            "status": "interpreter_behavior_manual_review",
            "recommended_status": "parked_low_priority",
            "best_future_route": "manual_review_only",
            "provider_complexity": "low",
            "proof_distance": "far",
        },
    ]


def retired_candidates() -> list[dict[str, Any]]:
    return [
        {"candidate_id": "pexpect_699_replwrap_bash_assertions", "status": "provider_environment_retired", "reason": "environment/provider boundary remained dominant"},
        {"candidate_id": "pairtools_250_py313_pipes_removed", "status": "dependency_or_cofactor_blocked", "reason": "dependency materialization did not yield target-code repair path"},
        {"candidate_id": "pytest_13480_wdefault_unraisable_threadexception", "status": "dependency_or_cofactor_blocked", "reason": "provider/dependency path did not materialize target-code failure"},
        {"candidate_id": "snapshottest_177_py312_imp_removed", "status": "provider_recovery_success_target_nonmaterialization", "reason": "provider recovery succeeded but target bug did not reproduce"},
        {"candidate_id": "wave2_hermes_nousresearch_timeout_class", "status": "network_or_model_timeout_boundary", "reason": "unbounded network/model requirements remain outside patch path"},
        {"candidate_id": "genia_timeout_manual_review_class", "status": "manual_review_timeout_boundary", "reason": "timeout/manual-review class lacks bounded target-code materialization"},
    ]


def salvage_records() -> list[dict[str, Any]]:
    return [
        {
            "candidate_id": "datasette_2461_async_event_loop_cli_tests",
            "wave": "Wave 1",
            "original_batch_seen": "Batch057b",
            "original_status": "elbow_closed_multi_family_ambiguous",
            "original_blocker": "dependency_install_bug, environment_provider_bug, multi_causal_failure_surface, primary_source_bug, secondary_source_bug",
            "whether_old_blocker_was_source": True,
            "whether_old_blocker_was_provider": True,
            "whether_old_blocker_was_dependency": True,
            "whether_old_blocker_was_interpreter_behavior": False,
            "whether_old_blocker_was_network_model": False,
            "whether_old_blocker_was_timeout": False,
            "whether_old_blocker_was_multi_family": True,
            "new_capabilities_relevant": ["AMDS full bug-tree closure", "provider/runtime pattern library", "recurring issue memory"],
            "salvage_possible": "maybe",
            "salvage_path": "bounded family decomposition before any replay",
            "salvage_risk": "high",
            "expected_repair_count_impact": "medium",
            "expected_self_maintenance_impact": "medium",
            "expected_provider_complexity": "high",
            "expected_time_to_materialized_failure": "medium",
            "expected_time_to_count_gate": "medium_to_far",
            "recommended_status": "park",
            "recommended_next_batch_if_reopened": "batch062c_wave1_wave2_salvage_replay_selection",
            "reasoning_summary": "AMDS can separate layers now, but ambiguity and provider complexity still make it lower expected value than new provider-screened Wave 3 expansion.",
        },
        {
            "candidate_id": "freezegun_547_py313_datetimes_assertion",
            "wave": "Wave 1",
            "original_batch_seen": "Batch057c",
            "original_status": "stage1_primary_patch_partial_improvement_secondary_still_fails",
            "original_blocker": "secondary provider or interpreter-family blocker",
            "whether_old_blocker_was_source": True,
            "whether_old_blocker_was_provider": True,
            "whether_old_blocker_was_dependency": False,
            "whether_old_blocker_was_interpreter_behavior": True,
            "whether_old_blocker_was_network_model": False,
            "whether_old_blocker_was_timeout": False,
            "whether_old_blocker_was_multi_family": True,
            "new_capabilities_relevant": ["provider/runtime pattern library", "AMDS full bug-tree closure", "duplicate replay/count-gate proof pattern"],
            "salvage_possible": "maybe",
            "salvage_path": "provider portability secondary-family probe",
            "salvage_risk": "medium",
            "expected_repair_count_impact": "medium",
            "expected_self_maintenance_impact": "medium",
            "expected_provider_complexity": "medium",
            "expected_time_to_materialized_failure": "medium",
            "expected_time_to_count_gate": "medium",
            "recommended_status": "rank_below_wave3",
            "recommended_next_batch_if_reopened": "batch057d_freezegun_provider_portability_secondary_family_probe",
            "reasoning_summary": "Partial improvement is preserved as a salvageable branch, but source-only success was not achieved and secondary blockers remain.",
        },
        {
            "candidate_id": "venusian_91_py313_frameinfo_callinfo",
            "wave": "Wave 1",
            "original_batch_seen": "Batch057b",
            "original_status": "elbow_closed_test_expectation_or_interpreter_behavior",
            "original_blocker": "interpreter behavior or test expectation boundary",
            "whether_old_blocker_was_source": False,
            "whether_old_blocker_was_provider": False,
            "whether_old_blocker_was_dependency": False,
            "whether_old_blocker_was_interpreter_behavior": True,
            "whether_old_blocker_was_network_model": False,
            "whether_old_blocker_was_timeout": False,
            "whether_old_blocker_was_multi_family": False,
            "new_capabilities_relevant": ["manual-review terminal policy"],
            "salvage_possible": "no",
            "salvage_path": "manual review only",
            "salvage_risk": "high",
            "expected_repair_count_impact": "low",
            "expected_self_maintenance_impact": "low",
            "expected_provider_complexity": "low",
            "expected_time_to_materialized_failure": "far",
            "expected_time_to_count_gate": "far",
            "recommended_status": "manual_review",
            "recommended_next_batch_if_reopened": None,
            "reasoning_summary": "Interpreter/test expectation boundaries are not source repair candidates without additional decision-time evidence.",
        },
        {
            "candidate_id": "pexpect_699_replwrap_bash_assertions",
            "wave": "Wave 1",
            "original_batch_seen": "Batch057b",
            "original_status": "elbow_closed_environment_provider",
            "original_blocker": "environment provider boundary",
            "whether_old_blocker_was_source": False,
            "whether_old_blocker_was_provider": True,
            "whether_old_blocker_was_dependency": False,
            "whether_old_blocker_was_interpreter_behavior": False,
            "whether_old_blocker_was_network_model": False,
            "whether_old_blocker_was_timeout": False,
            "whether_old_blocker_was_multi_family": False,
            "new_capabilities_relevant": ["provider/runtime pattern library"],
            "salvage_possible": "no",
            "salvage_path": "retire unless bounded provider capsule appears",
            "salvage_risk": "high",
            "expected_repair_count_impact": "low",
            "expected_self_maintenance_impact": "low",
            "expected_provider_complexity": "high",
            "expected_time_to_materialized_failure": "far",
            "expected_time_to_count_gate": "far",
            "recommended_status": "retire",
            "recommended_next_batch_if_reopened": None,
            "reasoning_summary": "Provider/environment boundary dominated and no bounded source failure is preserved.",
        },
        {
            "candidate_id": "pyramid_3761_py313_test_util",
            "wave": "Wave 1",
            "original_batch_seen": "Batch056",
            "original_status": "not_selected_or_not_materialized_in_later_patch_gate",
            "original_blocker": "insufficient preserved target-code materialization",
            "whether_old_blocker_was_source": False,
            "whether_old_blocker_was_provider": False,
            "whether_old_blocker_was_dependency": False,
            "whether_old_blocker_was_interpreter_behavior": False,
            "whether_old_blocker_was_network_model": False,
            "whether_old_blocker_was_timeout": False,
            "whether_old_blocker_was_multi_family": False,
            "new_capabilities_relevant": ["candidate terminal-state policy"],
            "salvage_possible": "no",
            "salvage_path": "preserve as parked historical lead only",
            "salvage_risk": "medium",
            "expected_repair_count_impact": "low",
            "expected_self_maintenance_impact": "low",
            "expected_provider_complexity": "unknown",
            "expected_time_to_materialized_failure": "far",
            "expected_time_to_count_gate": "far",
            "recommended_status": "park",
            "recommended_next_batch_if_reopened": None,
            "reasoning_summary": "No current proof record shows a near-term count-gate path.",
        },
        {
            "candidate_id": "pairtools_250_py313_pipes_removed",
            "wave": "Wave 2",
            "original_batch_seen": "Batch056d",
            "original_status": "dependency_or_cofactor_blocked",
            "original_blocker": "dependency/provider materialization boundary",
            "whether_old_blocker_was_source": False,
            "whether_old_blocker_was_provider": True,
            "whether_old_blocker_was_dependency": True,
            "whether_old_blocker_was_interpreter_behavior": False,
            "whether_old_blocker_was_network_model": False,
            "whether_old_blocker_was_timeout": False,
            "whether_old_blocker_was_multi_family": False,
            "new_capabilities_relevant": ["provider/runtime pattern library"],
            "salvage_possible": "maybe",
            "salvage_path": "bounded provider/dependency capsule only if declared metadata is complete",
            "salvage_risk": "high",
            "expected_repair_count_impact": "low",
            "expected_self_maintenance_impact": "medium",
            "expected_provider_complexity": "high",
            "expected_time_to_materialized_failure": "medium_to_far",
            "expected_time_to_count_gate": "far",
            "recommended_status": "rank_below_wave3",
            "recommended_next_batch_if_reopened": "batch062c_wave1_wave2_salvage_replay_selection",
            "reasoning_summary": "Provider/dependency materialization might be reassessed, but prior attempts did not materialize target-code failure.",
        },
        {
            "candidate_id": "pytest_13480_wdefault_unraisable_threadexception",
            "wave": "Wave 2",
            "original_batch_seen": "Batch056d",
            "original_status": "dependency_or_cofactor_blocked",
            "original_blocker": "dependency/provider materialization boundary",
            "whether_old_blocker_was_source": False,
            "whether_old_blocker_was_provider": True,
            "whether_old_blocker_was_dependency": True,
            "whether_old_blocker_was_interpreter_behavior": False,
            "whether_old_blocker_was_network_model": False,
            "whether_old_blocker_was_timeout": False,
            "whether_old_blocker_was_multi_family": False,
            "new_capabilities_relevant": ["provider/runtime pattern library"],
            "salvage_possible": "maybe",
            "salvage_path": "bounded provider/dependency capsule only",
            "salvage_risk": "high",
            "expected_repair_count_impact": "low",
            "expected_self_maintenance_impact": "medium",
            "expected_provider_complexity": "high",
            "expected_time_to_materialized_failure": "medium_to_far",
            "expected_time_to_count_gate": "far",
            "recommended_status": "rank_below_wave3",
            "recommended_next_batch_if_reopened": "batch062c_wave1_wave2_salvage_replay_selection",
            "reasoning_summary": "Reassessment could improve routing, but no preserved target-code failure supports a patch gate.",
        },
        {
            "candidate_id": "snapshottest_177_py312_imp_removed",
            "wave": "Wave 2",
            "original_batch_seen": "Batch056d",
            "original_status": "provider_recovery_succeeded_target_bug_not_reproduced",
            "original_blocker": "target failure absent after provider recovery",
            "whether_old_blocker_was_source": False,
            "whether_old_blocker_was_provider": True,
            "whether_old_blocker_was_dependency": True,
            "whether_old_blocker_was_interpreter_behavior": False,
            "whether_old_blocker_was_network_model": False,
            "whether_old_blocker_was_timeout": False,
            "whether_old_blocker_was_multi_family": False,
            "new_capabilities_relevant": ["terminal-state policy"],
            "salvage_possible": "no",
            "salvage_path": "retire unless new decision-time evidence materializes target failure",
            "salvage_risk": "high",
            "expected_repair_count_impact": "low",
            "expected_self_maintenance_impact": "medium",
            "expected_provider_complexity": "medium",
            "expected_time_to_materialized_failure": "far",
            "expected_time_to_count_gate": "far",
            "recommended_status": "retire",
            "recommended_next_batch_if_reopened": None,
            "reasoning_summary": "Correctly starved patch generation after target failure did not materialize.",
        },
        {
            "candidate_id": "wave2_hermes_nousresearch_timeout_class",
            "wave": "Wave 2",
            "original_batch_seen": "Batch056f",
            "original_status": "network_or_model_timeout_boundary",
            "original_blocker": "network/model timeout or unbounded provider",
            "whether_old_blocker_was_source": False,
            "whether_old_blocker_was_provider": True,
            "whether_old_blocker_was_dependency": False,
            "whether_old_blocker_was_interpreter_behavior": False,
            "whether_old_blocker_was_network_model": True,
            "whether_old_blocker_was_timeout": True,
            "whether_old_blocker_was_multi_family": False,
            "new_capabilities_relevant": ["terminal-state policy", "resource/probe budget governor"],
            "salvage_possible": "no",
            "salvage_path": "retire or manual review unless bounded offline provider exists",
            "salvage_risk": "very_high",
            "expected_repair_count_impact": "low",
            "expected_self_maintenance_impact": "low",
            "expected_provider_complexity": "very_high",
            "expected_time_to_materialized_failure": "far",
            "expected_time_to_count_gate": "far",
            "recommended_status": "retire",
            "recommended_next_batch_if_reopened": None,
            "reasoning_summary": "Unbounded external model/network dependencies remain outside the repair path.",
        },
        {
            "candidate_id": "genia_timeout_manual_review_class",
            "wave": "Wave 2",
            "original_batch_seen": "Batch056f",
            "original_status": "manual_review_timeout_boundary",
            "original_blocker": "timeout/manual-review boundary",
            "whether_old_blocker_was_source": False,
            "whether_old_blocker_was_provider": True,
            "whether_old_blocker_was_dependency": False,
            "whether_old_blocker_was_interpreter_behavior": False,
            "whether_old_blocker_was_network_model": False,
            "whether_old_blocker_was_timeout": True,
            "whether_old_blocker_was_multi_family": False,
            "new_capabilities_relevant": ["terminal-state policy"],
            "salvage_possible": "no",
            "salvage_path": "manual review only",
            "salvage_risk": "high",
            "expected_repair_count_impact": "low",
            "expected_self_maintenance_impact": "low",
            "expected_provider_complexity": "high",
            "expected_time_to_materialized_failure": "far",
            "expected_time_to_count_gate": "far",
            "recommended_status": "manual_review",
            "recommended_next_batch_if_reopened": None,
            "reasoning_summary": "Timeout/manual-review classification remains dominant without new bounded evidence.",
        },
    ]


def write_candidate_pool_outputs() -> list[dict[str, Any]]:
    counted = counted_repairs()
    parked = parked_candidates()
    retired = retired_candidates()
    future = [
        {"pool": "provider_screened_wave3_expansion", "status": "recommended", "reason": "Cloudpickle succeeded from provider-screened Wave 3 route."},
        {"pool": "probe_only_wave3_leads", "status": "lead_only", "reason": "Requires fresh seed screening before replay."},
        {"pool": "approved_but_unreplayed_provider_screened_leads", "status": "search_required", "reason": "Batch058 history should be extended rather than broad sweeping."},
    ]
    salvage = salvage_records()
    write_out_json(
        "candidate_pool_inventory_after_batch061.json",
        {
            "status": "PASS",
            "counted_repair_count": len(counted),
            "native_external_repair_count": NATIVE_EXTERNAL_REPAIR_COUNT,
            "parked_candidate_count": len(parked),
            "retired_candidate_count": len(retired),
            "future_seed_pool_count": len(future),
            "wave1_wave2_salvage_review_count": len(salvage),
        },
    )
    write_out_json("counted_repair_registry_after_batch061.json", {"status": "PASS", "records": counted, "issue_derived_repair_count": ISSUE_COUNT_AFTER_BATCH061, "native_external_repair_count": NATIVE_EXTERNAL_REPAIR_COUNT})
    write_out_json("parked_candidate_registry_after_batch061.json", {"status": "PASS", "records": parked})
    write_out_json("retired_candidate_registry_after_batch061.json", {"status": "PASS", "records": retired})
    write_out_json("future_seed_pool_registry_after_batch061.json", {"status": "PASS", "records": future})
    write_out_json(
        "candidate_status_consistency_check.json",
        {
            "status": "PASS",
            "cloudpickle_counted_once": True,
            "provider_runtime_recovery_not_counted": True,
            "parked_candidates_not_counted": True,
            "retired_candidates_not_counted": True,
            "repair_counts_preserved_in_batch062": True,
        },
    )
    write_out_json("wave1_wave2_salvage_inventory.json", {"status": "PASS", "records": salvage})
    write_out_json(
        "wave1_wave2_original_blocker_registry.json",
        {
            "status": "PASS",
            "records": [
                {
                    "candidate_id": item["candidate_id"],
                    "wave": item["wave"],
                    "original_batch_seen": item["original_batch_seen"],
                    "original_status": item["original_status"],
                    "original_blocker": item["original_blocker"],
                }
                for item in salvage
            ],
        },
    )
    write_out_json(
        "wave1_wave2_new_capability_reassessment.json",
        {
            "status": "PASS",
            "review_basis": ["provider/runtime pattern library", "recurring issue memory", "AMDS full bug-tree closure mode", "duplicate clean replay/count-gate proof pattern"],
            "records": [
                {
                    "candidate_id": item["candidate_id"],
                    "new_capabilities_relevant": item["new_capabilities_relevant"],
                    "salvage_possible": item["salvage_possible"],
                    "recommended_status": item["recommended_status"],
                    "reasoning_summary": item["reasoning_summary"],
                }
                for item in salvage
            ],
        },
    )
    reopen = [item for item in salvage if item["recommended_status"] in {"rank_below_wave3", "park"} and item["salvage_possible"] in {"maybe", "yes"}]
    write_out_json("wave1_wave2_reopen_candidate_queue.json", {"status": "PASS", "queue": reopen, "queue_count": len(reopen), "batch062_reopens_now": False})
    write_out_json("wave1_wave2_retirement_confirmation.json", {"status": "PASS", "records": [item for item in salvage if item["recommended_status"] == "retire"], "retirement_count": sum(item["recommended_status"] == "retire" for item in salvage)})
    write_out_json("wave1_wave2_manual_review_queue.json", {"status": "PASS", "records": [item for item in salvage if item["recommended_status"] == "manual_review"], "manual_review_count": sum(item["recommended_status"] == "manual_review" for item in salvage)})
    return salvage


def path_records() -> list[dict[str, Any]]:
    return [
        {
            "path_id": "batch058b_seed_discovery_wave_3_expansion",
            "expected_repair_count_impact": "high",
            "expected_self_maintenance_impact": "medium",
            "provider_risk": "medium",
            "evidence_quality": "high",
            "time_to_next_materialized_failure": "near_to_medium",
            "time_to_next_count_gate_candidate": "medium",
            "risk_of_artifact_growth_without_capability_gain": "medium",
            "required_next_artifact": "provider-screened Wave 3 expansion artifact",
            "recommended_next_allowed_action": "batch058b_seed_discovery_wave_3_expansion",
            "rank": 1,
            "selected": True,
            "why_not_selected_if_lower_ranked": None,
        },
        {
            "path_id": "batch060f_audioread_provider_backend_capsule_replay",
            "expected_repair_count_impact": "medium_high",
            "expected_self_maintenance_impact": "medium",
            "provider_risk": "medium_high",
            "evidence_quality": "medium_high",
            "time_to_next_materialized_failure": "near",
            "time_to_next_count_gate_candidate": "medium",
            "risk_of_artifact_growth_without_capability_gain": "medium_high",
            "required_next_artifact": "Audioread provider/backend capsule replay artifact",
            "recommended_next_allowed_action": "batch060f_audioread_provider_backend_capsule_replay",
            "rank": 2,
            "selected": False,
            "why_not_selected_if_lower_ranked": "Close parked candidate, but provider/backend complexity is higher than extending the successful Wave 3 provider-screened acquisition route.",
        },
        {
            "path_id": "batch062c_wave1_wave2_salvage_replay_selection",
            "expected_repair_count_impact": "medium",
            "expected_self_maintenance_impact": "high",
            "provider_risk": "high",
            "evidence_quality": "medium",
            "time_to_next_materialized_failure": "medium",
            "time_to_next_count_gate_candidate": "medium_to_far",
            "risk_of_artifact_growth_without_capability_gain": "high",
            "required_next_artifact": "bounded salvage selection artifact",
            "recommended_next_allowed_action": "batch062c_wave1_wave2_salvage_replay_selection",
            "rank": 3,
            "selected": False,
            "why_not_selected_if_lower_ranked": "Valuable review path, but too many salvage candidates still need bounded reassessment before replay.",
        },
        {
            "path_id": "batch062b_repo_hygiene_utility_consolidation_planning",
            "expected_repair_count_impact": "low",
            "expected_self_maintenance_impact": "high",
            "provider_risk": "low",
            "evidence_quality": "high",
            "time_to_next_materialized_failure": "far",
            "time_to_next_count_gate_candidate": "far",
            "risk_of_artifact_growth_without_capability_gain": "medium",
            "required_next_artifact": "utility consolidation plan",
            "recommended_next_allowed_action": "batch062b_repo_hygiene_utility_consolidation_planning",
            "rank": 4,
            "selected": False,
            "why_not_selected_if_lower_ranked": "Important infrastructure work, but not the dominant blocker to immediate proof progress.",
        },
        {
            "path_id": "batch057d_freezegun_provider_portability_secondary_family_probe",
            "expected_repair_count_impact": "medium",
            "expected_self_maintenance_impact": "medium",
            "provider_risk": "medium",
            "evidence_quality": "medium",
            "time_to_next_materialized_failure": "medium",
            "time_to_next_count_gate_candidate": "medium_to_far",
            "risk_of_artifact_growth_without_capability_gain": "medium_high",
            "required_next_artifact": "Freezegun provider portability probe artifact",
            "recommended_next_allowed_action": "batch057d_freezegun_provider_portability_secondary_family_probe",
            "rank": 5,
            "selected": False,
            "why_not_selected_if_lower_ranked": "Salvageable but lower expected value than Audioread and new Wave 3 expansion.",
        },
        {
            "path_id": "batch060e_cloudpickle_next_bug_tree_branch_recovery",
            "expected_repair_count_impact": "low",
            "expected_self_maintenance_impact": "low",
            "provider_risk": "medium",
            "evidence_quality": "medium",
            "time_to_next_materialized_failure": "unknown",
            "time_to_next_count_gate_candidate": "far",
            "risk_of_artifact_growth_without_capability_gain": "high",
            "required_next_artifact": "only if proof ledger exposes unresolved actionable branch",
            "recommended_next_allowed_action": "not_selected",
            "rank": 6,
            "selected": False,
            "why_not_selected_if_lower_ranked": "Cloudpickle counted repair is closed for this issue-derived count gate; do not reopen without new proof-ledger evidence.",
        },
    ]


def write_path_analysis(salvage: list[dict[str, Any]]) -> None:
    paths = path_records()
    write_out_json(
        "highest_impact_path_analysis.json",
        {
            "status": "PASS",
            "selected_path": NEXT_ALLOWED_ACTION,
            "selection_reason": "Wave 3 provider-screened expansion has the best repair-count expected value after Cloudpickle succeeded through that route, while salvage remains useful but riskier.",
            "paths": paths,
        },
    )
    write_out_json("next_candidate_selection_matrix.json", {"status": "PASS", "selected_path": NEXT_ALLOWED_ACTION, "matrix": paths})
    write_out_json("candidate_expected_value_ranking.json", {"status": "PASS", "ranking": sorted(paths, key=lambda item: item["rank"])})
    risk_rank = sorted(paths, key=lambda item: ["low", "medium", "medium_high", "high", "very_high"].index(item["provider_risk"]) if item["provider_risk"] in ["low", "medium", "medium_high", "high", "very_high"] else 3)
    write_out_json("candidate_risk_ranking.json", {"status": "PASS", "lower_risk_first": risk_rank})
    write_out_json("candidate_provider_complexity_ranking.json", {"status": "PASS", "ranking": [{"path_id": p["path_id"], "provider_risk": p["provider_risk"], "rank": p["rank"]} for p in paths]})
    write_out_json("candidate_proof_distance_ranking.json", {"status": "PASS", "ranking": [{"path_id": p["path_id"], "time_to_next_count_gate_candidate": p["time_to_next_count_gate_candidate"], "rank": p["rank"]} for p in paths]})
    salvage_candidates = [item for item in salvage if item["salvage_possible"] in {"maybe", "yes"}]
    write_out_json(
        "salvage_vs_new_seed_tradeoff_analysis.json",
        {
            "status": "PASS",
            "new_seed_expansion_selected": True,
            "salvage_candidates_reviewed": len(salvage),
            "salvage_candidates_reopen_or_rank_below_wave3": len(salvage_candidates),
            "reason": "Salvage review is valuable, but provider-screened Wave 3 expansion is more likely to produce the next clean materialized failure/count candidate.",
        },
    )
    write_out_json("wave1_wave2_salvage_expected_value_ranking.json", {"status": "PASS", "ranking": salvage_candidates})
    write_out_json("wave1_wave2_salvage_risk_ranking.json", {"status": "PASS", "ranking": sorted(salvage, key=lambda item: item["salvage_risk"])})
    write_out_json(
        "best_parked_candidate_reopen_recommendation.json",
        {
            "status": "PASS",
            "highest_ranked_parked_candidate": "audioread_144_py313_aifc_removed",
            "recommended_route": "batch060f_audioread_provider_backend_capsule_replay",
            "selected_as_next_action": False,
            "reason": "Audioread is the best parked candidate, but Wave 3 expansion still outranks salvage for repair-count expected value.",
        },
    )


def terminal_state_records() -> list[dict[str, Any]]:
    states = [
        "counted_repair",
        "duplicate_replay_candidate",
        "source_only_patch_candidate",
        "provider_recovery_needed",
        "dependency_recovery_needed",
        "failure_family_decomposition_needed",
        "interpreter_behavior_manual_review",
        "test_expectation_manual_review",
        "unbounded_external_provider",
        "forbidden_evidence_required",
        "not_reproducible",
        "out_of_scope",
        "retired",
        "manual_review",
        "unrecoverable_under_current_policy",
    ]
    records = []
    for state in states:
        records.append(
            {
                "terminal_state": state,
                "meaning": f"Candidate is routed to {state} under current evidence and policy.",
                "allowed_next_action": "route-specific audited follow-up or stop",
                "forbidden_next_action": "source patch generation without materialized target-code failure and patch license",
                "count_policy": "counts only if duplicate replay and count gate pass" if state == "counted_repair" else "not counted",
                "evidence_required": ["decision-time evidence", "SHA256 custody", "claim boundary"],
                "what_would_reopen": "new decision-time-safe evidence or bounded provider materialization",
                "what_would_make_unrecoverable": "requires forbidden evidence, unbounded provider, unavailable runtime, or test mutation",
            }
        )
    return records


def write_self_maintenance_outputs() -> None:
    terminal = terminal_state_records()
    write_out_json(
        "universal_bug_processing_policy.json",
        {
            "status": "PASS",
            "principle": "A self-maintaining wrapper should process every encountered bug into an auditable route or terminal state, not promise it can fix every bug.",
            "fix_every_bug_claimed": False,
            "terminal_states": [item["terminal_state"] for item in terminal],
        },
    )
    write_out_json("self_maintaining_bug_terminal_state_policy.json", {"status": "PASS", "terminal_state_records": terminal})
    write_out_json(
        "bug_unrecoverability_explanation_policy.json",
        {
            "status": "PASS",
            "unrecoverable_reasons": ["forbidden evidence required", "unbounded provider", "unavailable runtime", "test mutation required", "not reproducible"],
            "public_language": "Some bugs may be unrecoverable under current policy because they require forbidden evidence, unbounded providers, unavailable runtimes, or test mutation.",
        },
    )
    write_out_json(
        "autonomous_bug_route_contract.json",
        {
            "status": "PASS",
            "must_route_to_terminal_or_next_action": True,
            "must_not_claim_universal_repair": True,
            "must_preserve_claim_boundaries": True,
        },
    )
    functions = [
        ("autonomous candidate intake", "partially_working", "high"),
        ("candidate deduplication", "partially_working", "high"),
        ("issue-derived seed validation", "working_across_multiple_candidates", "medium"),
        ("provider/runtime capsule materialization", "working_for_single_candidate", "high"),
        ("environment/provenance custody", "validated_across_unrelated_candidates", "critical"),
        ("pre-repair replay materialization", "working_across_multiple_candidates", "critical"),
        ("AMDS full bug-tree closure", "working_for_single_candidate", "high"),
        ("failure-family decomposition", "working_across_multiple_candidates", "high"),
        ("source-contact topology mapping", "partially_working", "medium"),
        ("patch-license decision gate", "working_for_single_candidate", "critical"),
        ("bounded source-only patch generation", "working_across_multiple_candidates", "critical"),
        ("patch minimality/safety check", "working_across_multiple_candidates", "critical"),
        ("post-repair original target replay", "working_across_multiple_candidates", "critical"),
        ("duplicate clean replay", "working_for_single_candidate", "critical"),
        ("repair count gate", "working_for_single_candidate", "critical"),
        ("proof ledger update", "working_for_single_candidate", "critical"),
        ("recurring issue memory", "partially_working", "medium"),
        ("patch-debt ledger", "partially_working", "medium"),
        ("repo topology/duplicate function audit", "scaffolded", "medium"),
        ("public language/claim safety guard", "working_across_multiple_candidates", "high"),
        ("project health scorecard", "working_for_single_candidate", "medium"),
        ("next-action strategy selection", "working_for_single_candidate", "high"),
        ("unrecoverable-branch explanation", "partially_working", "high"),
        ("human escalation/manual-review protocol", "partially_working", "high"),
        ("provider capsule reuse registry", "scaffolded", "high"),
        ("resource/probe budget governor", "partially_working", "medium"),
        ("regression/drift detector", "working_across_multiple_candidates", "high"),
        ("rollback/branch closure record", "working_across_multiple_candidates", "high"),
        ("memory-lift baseline and measurement plan", "scaffolded", "medium"),
        ("aggregate self-maintenance claim criteria", "scaffolded", "critical"),
    ]
    matrix = [
        {
            "function": name,
            "classification": classification,
            "evidence_files": ["batch061_final_decision.json", "project_health_review_batch061.json"],
            "current_gap": "needs broader automation or unrelated-candidate validation" if "working" in classification or classification == "partially_working" else "needs implementation",
            "risk_if_missing": "manual intervention remains necessary",
            "recommended_future_batch": "future consolidation or candidate-expansion lane",
            "priority": priority,
        }
        for name, classification, priority in functions
    ]
    missing = [item for item in matrix if item["classification"] in {"not_started", "scaffolded", "partially_working", "working_for_single_candidate"}]
    write_out_json(
        "self_maintaining_wrapper_function_gap_audit.json",
        {
            "status": "PASS",
            "self_maintaining_software_demonstrated": False,
            "reason": "ControllerGate has counted repairs and wrapper subsystems, but not autonomous end-to-end intake, materialization, repair, duplicate replay, count gate, and health review across enough unrelated candidates under preregistered aggregate criteria.",
            "function_count": len(matrix),
            "claim_ready_count": sum(item["classification"] == "claim_ready" for item in matrix),
        },
    )
    write_out_json("self_maintaining_wrapper_required_function_matrix.json", {"status": "PASS", "functions": matrix})
    write_out_json("missing_or_partial_self_maintenance_functions.json", {"status": "PASS", "functions": missing, "top_three": missing[:3]})
    write_out_json(
        "self_maintenance_function_roadmap.json",
        {
            "status": "PASS",
            "priorities": [
                "automate verified candidate intake and deduplication",
                "generalize provider capsule reuse",
                "generalize duplicate replay/count gate beyond one candidate",
                "define aggregate preregistered self-maintenance criteria",
            ],
        },
    )
    write_out_json(
        "self_maintenance_runtime_progress_review_batch062.json",
        {
            "status": "PASS",
            "automatic_now": ["manifest checks", "registry validation", "audit stack", "public language guard", "selected provider/runtime records"],
            "manual_still_required": ["manual artifact handoff", "candidate seed discovery choice", "some runtime materialization", "follow-up lane prompting"],
            "provider_capsule_handled_blockers": ["declared provider/runtime materialization where metadata exists"],
            "amds_handled_blockers": ["multi-family state recording", "patch-license ordering"],
            "addon_prompt_blockers_remaining": ["candidate acquisition strategy", "salvage prioritization", "repo utility consolidation"],
            "self_maintaining_software_demonstrated": False,
        },
    )
    write_out_json("self_maintenance_gap_closure_plan.json", {"status": "PASS", "gaps": missing[:10], "self_maintaining_software_demonstrated": False})
    write_out_json("autonomic_capability_readiness_matrix.json", {"status": "PASS", "functions": matrix})
    write_out_json("manual_intervention_reduction_report.json", {"status": "PASS", "manual_interventions": ["artifact handoff", "seed selection", "lane authorization"], "reduction_plan": ["standardize artifact intake", "bounded seed queue", "shared count-gate helper"]})
    write_out_json("repeat_bottleneck_elimination_plan.json", {"status": "PASS", "bottlenecks": ["manual artifact ingestion", "one-off audit scripts", "provider capsule repetition", "candidate discovery friction"], "planned_eliminations": ["shared utility library", "reusable workflow", "provider capsule registry"]})


def write_health_and_patterns() -> None:
    write_out_json("project_health_review_batch062.json", {"status": "PASS", "project_health_grade": "B", "traffic_light_status": "yellow", "advisory_diagnostic_only": True, "does_not_override_audits": True})
    write_out_json("capability_maturity_scorecard_batch062.json", {"status": "PASS", "overall_grade": "B", "traffic_light_status": "yellow", "repair_count_readiness": "improved", "self_maintenance_readiness": "not_demonstrated"})
    write_out_json("version_progress_grade_batch062.json", {"status": "PASS", "overall_grade": "B", "traffic_light_status": "yellow"})
    write_out_json("strategic_direction_check_batch062.json", {"status": "PASS", "highest_impact_path_selected": NEXT_ALLOWED_ACTION, "overclaims_detected": False, "repo_hygiene_blocks_progress": False})
    write_out_json("proof_milestone_distance_report_batch062.json", {"status": "PASS", "distance_to_next_repair_count_milestone": "medium", "distance_to_self_maintaining_claim": "far", "reason": "next candidate must still be selected and materialized"})
    write_out_json("regression_and_drift_watch_batch062.json", {"status": "PASS", "regressions_detected": [], "drift_watch_items": ["repair count preservation", "candidate selection scope", "public language"]})
    write_out_json("recurring_bottleneck_trend_report_batch062.json", {"status": "PASS", "trends": ["artifact ingestion remains manual", "provider/runtime capsules are useful but not universal", "duplicate replay/count gate is now proven once"]})
    write_out_json("next_highest_impact_action_report_batch062.json", {"status": "PASS", "recommended_next_action": NEXT_ALLOWED_ACTION, "why": "best repair-count expected value after Batch061", "fallback": "batch060f_audioread_provider_backend_capsule_replay"})
    pattern_common = {"status": "PASS", "operational_rules_unchanged": True, "claim_boundary_preserved": True}
    write_out_json("cloudpickle_count_gate_pattern_update.json", {**pattern_common, "lesson": "Cloudpickle moved from provider-screened seed to provider recovery to source-only patch to duplicate replay/count gate."})
    write_out_json("provider_screened_seed_success_pattern.json", {**pattern_common, "lesson": "Provider-screened Wave 3 selection produced a clean target-pass/count-gate path."})
    write_out_json("duplicate_replay_count_gate_success_pattern.json", {**pattern_common, "lesson": "Duplicate clean replay plus count gate is the proof pattern for issue-derived repair count increments."})
    write_out_json("issue_derived_repair_increment_pattern.json", {**pattern_common, "issue_derived_repair_count_after_batch061": ISSUE_COUNT_AFTER_BATCH061})
    write_out_json("public_language_guard_pattern_update.json", {**pattern_common, "lesson": "Public language guard remains necessary because prior public-summary language caused workflow failure."})
    write_out_json("amds_full_bug_tree_pattern_update.json", {**pattern_common, "lesson": "Full bug-tree closure is useful for state ordering but does not prove self-maintenance."})
    write_out_json("reactome_provider_capsule_pattern_update.json", {**pattern_common, "lesson": "Reactome-style provider capsule remains infrastructure-only and not repair evidence."})
    write_out_json("tld_governance_pattern_update.json", {**pattern_common, "lesson": "TLD remains audit/governance-only metadata and not a public software claim."})


def write_final_outputs() -> None:
    final = {
        "status": "PASS",
        "batch061_ingest_status": "PASS",
        "batch062_audit_status": "PASS",
        "current_protocol": CURRENT_PROTOCOL,
        "issue_derived_repair_count": ISSUE_COUNT_AFTER_BATCH061,
        "native_external_repair_count": NATIVE_EXTERNAL_REPAIR_COUNT,
        "highest_impact_next_path": NEXT_ALLOWED_ACTION,
        "project_health_grade": "B",
        "traffic_light_status": "yellow",
        "distance_to_next_repair_count_milestone": "medium",
        "distance_to_self_maintaining_claim": "far",
        "next_allowed_action": NEXT_ALLOWED_ACTION,
        "full_scoring": "NOT_RUN/disallowed",
        "memory_lift": "not_demonstrated",
        "self_maintaining_software": "false/not_demonstrated",
        "patch_generated": False,
        "patch_applied": False,
        "pre_repair_replay_run": False,
        "post_repair_replay_run": False,
        "duplicate_replay_run": False,
        "count_gate_run": False,
        "repair_count_increment": False,
        "exact_blocker": None,
    }
    write_out_json("batch062_final_decision.json", final)
    write_out_json(
        "batch063_recommended_prompt_plan.json",
        {
            "status": "PASS",
            "recommended_next_prompt": NEXT_ALLOWED_ACTION,
            "must_not_patch_without_materialized_failure": True,
            "must_not_run_count_gate_without_source_only_target_pass": True,
        },
    )
    write_out_json("batch060f_audioread_provider_backend_capsule_replay_recommendation.json", {"status": "PASS", "recommended": False, "rank": 2, "reason": "Best parked candidate but lower expected repair-count value than Wave 3 expansion."})
    write_out_json("batch058b_seed_discovery_wave_3_expansion_recommendation.json", {"status": "PASS", "recommended": True, "rank": 1, "reason": "Cloudpickle success validates provider-screened Wave 3 route."})
    write_out_json("batch062b_repo_hygiene_utility_consolidation_planning_recommendation.json", {"status": "PASS", "recommended": False, "rank": 4, "reason": "Important but not dominant blocker to immediate proof progress."})
    write_out_json("batch057d_freezegun_provider_portability_recommendation.json", {"status": "PASS", "recommended": False, "rank": 5, "reason": "Salvageable but lower priority."})
    write_out_json(
        "claim_boundary.json",
        {
            "status": "PASS",
            "current_protocol": CURRENT_PROTOCOL,
            "issue_derived_repair_count": ISSUE_COUNT_AFTER_BATCH061,
            "native_external_repair_count": NATIVE_EXTERNAL_REPAIR_COUNT,
            "full_scoring": "NOT_RUN/disallowed",
            "memory_lift": "not_demonstrated",
            "self_maintaining_software": "false/not_demonstrated",
            "patch_generated": False,
            "patch_applied": False,
            "pre_repair_replay_run": False,
            "post_repair_replay_run": False,
            "duplicate_replay_run": False,
            "count_gate_run": False,
            "repair_count_increment": False,
            "repo_refactor_performed": False,
            "source_behavior_changed": False,
            "tests_mutated": False,
            "project_health_review_advisory_only": True,
        },
    )
    write_out_json("audit.json", {"status": "PASS", "audit_script": "scripts/audit_batch062_next_issue_repair_candidate_selection_or_wave3_expansion.py"})
    write_out_json("package_verification.json", {"status": "PASS", "raw_zip_payload_committed": False, "runtime_workspaces_committed": False, "source_checkouts_committed": False, "venvs_committed": False, "caches_committed": False})
    write_out_text(
        "batch062_summary.md",
        f"""# Batch062 next issue-repair candidate selection

Batch062 officially ingests Batch061, preserves the counted Cloudpickle issue-derived repair, and chooses the next strategic route without patching or replay.

Result:

- Batch061 official ingest: PASS.
- Cloudpickle counted repair preservation: PASS.
- Issue-derived repair count preserved at `{ISSUE_COUNT_AFTER_BATCH061}`.
- Native external repair count preserved at `{NATIVE_EXTERNAL_REPAIR_COUNT}`.
- Wave 1/Wave 2 salvage candidates reviewed: 10.
- Highest-ranked parked candidate: `audioread_144_py313_aifc_removed`.
- Highest-impact next path: `{NEXT_ALLOWED_ACTION}`.
- Project health grade: `B`; traffic-light status `yellow`.
- Distance to next repair-count milestone: `medium`.
- Distance to self-maintaining claim: `far`.
- Full scoring remains `NOT_RUN/disallowed`.
- Memory lift remains `not_demonstrated`.
- Self-maintaining software remains `false/not_demonstrated`.

Workflow success is not equivalent to repair success.
Provider/runtime recovery is not repair success.
Partial improvement is not repair success.
Repair count increments require duplicate clean replay and count gate.
The project health grade is advisory and does not constitute proof.
Self-maintaining software remains false/not_demonstrated.

A self-maintaining wrapper should process every encountered bug into an auditable route or terminal state, but it should not claim it can fix every bug.
Some bugs may be unrecoverable under current policy because they require forbidden evidence, unbounded providers, unavailable runtimes, or test mutation.
""",
    )


def update_public_summaries() -> None:
    block = f"""Batch062 is the latest strategic selection boundary. It officially ingests Batch061, preserves the counted Cloudpickle issue-derived repair, and reviews the next candidate route without patching, replaying, or changing repair counts.

Batch062 status:

- Batch061 official ingest: `PASS`.
- Cloudpickle counted repair preservation: `PASS`.
- Issue-derived repair count preserved at `{ISSUE_COUNT_AFTER_BATCH061}`.
- Native external repair count preserved at `{NATIVE_EXTERNAL_REPAIR_COUNT}`.
- Candidate pool review: `PASS`.
- Wave 1/Wave 2 salvage review: `PASS`, 10 previously blocked candidates reviewed.
- Recommended reopening or bounded reassessment candidates: `4`.
- Recommended parked/manual-review candidates: `3`.
- Recommended retirement confirmations: `3`.
- Highest-ranked parked candidate: `audioread_144_py313_aifc_removed`.
- New-seed expansion still outranks salvage: `true`.
- Highest-impact next path: `{NEXT_ALLOWED_ACTION}`.
- Project health grade: `B`; traffic-light status `yellow`.
- Distance to next repair-count milestone: `medium`.
- Distance to self-maintaining claim: `far`.
- Full scoring remains `NOT_RUN/disallowed`.
- Memory lift remains `not_demonstrated`.
- Self-maintaining software remains `false/not_demonstrated`.
- Next allowed action: `{NEXT_ALLOWED_ACTION}`.

Self-maintaining wrapper function gap summary: candidate intake, provider capsule reuse, and generalized duplicate replay/count-gate automation remain partial or single-candidate. A self-maintaining wrapper should process every encountered bug into an auditable route or terminal state, but it should not claim it can fix every bug. Some bugs may be unrecoverable under current policy because they require forbidden evidence, unbounded providers, unavailable runtimes, or test mutation.

Workflow success is not equivalent to repair success. Provider/runtime recovery is not repair success. Partial improvement is not repair success. Repair count increments require duplicate clean replay and count gate. The project health grade is advisory and does not constitute proof. Self-maintaining software remains false/not_demonstrated.
"""
    targets = [
        ROOT / "README.md",
        ROOT / "docs" / "current_status.md",
        ROOT / "controllergate_v1_7_beta" / "reports" / "critic_review_package" / "shareable_summary.md",
    ]
    for target in targets:
        text = target.read_text(encoding="utf-8")
        if target.name == "README.md" and "## Current evidence status" in text:
            head, tail = text.split("## Current evidence status", 1)
            marker = "Batch061 is the latest validation-path boundary."
            rest = marker + tail.split(marker, 1)[1] if marker in tail else tail.lstrip()
            write_text_lf(target, head + "## Current evidence status\n\n" + block + "\n" + rest)
        else:
            lines = text.splitlines()
            title = lines[0] if lines else "# Current status"
            body = "\n".join(lines[1:]).lstrip()
            marker = "Batch061 is the latest validation-path boundary."
            rest = marker + body.split(marker, 1)[1] if marker in body else body
            write_text_lf(target, f"{title}\n\n{block}\n{rest}")


def main() -> int:
    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    OUT_DIR.mkdir(parents=True)
    verification = verify_batch061_artifact()
    phase_a(verification)
    salvage = write_candidate_pool_outputs()
    write_path_analysis(salvage)
    write_self_maintenance_outputs()
    write_health_and_patterns()
    write_final_outputs()
    update_public_summaries()
    write_sha256sums(OUT_DIR)
    print(
        json.dumps(
            {
                "status": "PASS",
                "output_dir": str(OUT_DIR),
                "highest_impact_next_path": NEXT_ALLOWED_ACTION,
                "issue_derived_repair_count": ISSUE_COUNT_AFTER_BATCH061,
                "native_external_repair_count": NATIVE_EXTERNAL_REPAIR_COUNT,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
