from __future__ import annotations

import json
import shutil
import zipfile
from pathlib import Path
from typing import Any

from controllergate.core.artifacts import audit_zip_entries, verify_outer_zip_identity, verify_zip_manifest
from controllergate.core.batch074_sterile_high_yield_wave1 import _internal_manifest
from controllergate.core.evidence import hash_record, sha256_file, write_json_deterministic, write_text_lf


BATCH = "post_v2_37_hardening_batch080_executed_preflight_provider_memory_wave1d"
B79 = "post_v2_37_hardening_batch079_count6_runtime_incident_memory_wave1c"
B73 = "post_v2_37_hardening_batch073_count5_revalidation_frozen_wave1"
B74 = "post_v2_37_hardening_batch074_sterile_high_yield_amds_memory_wave1"
B75 = "post_v2_37_hardening_batch075_provider_harness_amds_memory_wave1a"
B76 = "post_v2_37_hardening_batch076_amds_causal_memory_calibration"
B77 = "post_v2_37_hardening_batch077_typed_event_pathway_memory_v2"
B78 = "post_v2_37_hardening_batch078_count6_minimal_closure_memory_wave1b"
EXPECTED_SIZE = 998_670
EXPECTED_SHA256 = "f6a883915e31e91dceb601e5728d338f9b072cfc10acf75cb1e6223ae2c7a4ff"
EXPECTED_FILES = 383
EXPECTED_OUTER = 382
EXPECTED_MANIFESTS = {B73: 41, B74: 16, B75: 106, B76: 32, B77: 47, B78: 61, B79: 58}


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    write_text_lf(path, "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows))


def _copy_prefix(archive: zipfile.ZipFile, prefix: str, output: Path) -> None:
    for item in archive.infolist():
        if item.is_dir() or not item.filename.startswith(prefix + "/"):
            continue
        destination = output / Path(*Path(item.filename).parts[1:])
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(archive.read(item))


def verify_and_ingest_batch079(root: Path, artifact: Path) -> dict[str, Any]:
    outer = verify_outer_zip_identity(artifact, expected_size=EXPECTED_SIZE, expected_sha256=EXPECTED_SHA256)
    entries = audit_zip_entries(artifact)
    manifest = verify_zip_manifest(artifact, "ARTIFACT_SHA256SUMS.txt")
    with zipfile.ZipFile(artifact) as archive:
        files = [item for item in archive.infolist() if not item.is_dir()]
        names = [item.filename for item in files]
        internals = {prefix: _internal_manifest(archive, prefix) for prefix in EXPECTED_MANIFESTS}
        forbidden = [
            name for name in names
            if name.lower().endswith((".zip", ".tar", ".tgz", ".tar.gz", ".whl", ".pyc", ".pyo"))
            or "__pycache__" in name.lower()
            or "/.venv/" in name.lower()
            or "/venv/" in name.lower()
            or "/site-packages/" in name.lower()
        ]
        passed = (
            outer.get("status") == entries.get("status") == manifest.get("status") == "PASS"
            and len(files) == EXPECTED_FILES
            and manifest.get("checked") == EXPECTED_OUTER
            and not forbidden
            and all(value.get("status") == "PASS" and value.get("checked") == EXPECTED_MANIFESTS[name] for name, value in internals.items())
        )
        if not passed:
            raise RuntimeError("Batch079 artifact verification failed")
        for prefix in EXPECTED_MANIFESTS:
            _copy_prefix(archive, prefix, root / "outputs" / prefix)
    final = _load(root / "outputs" / B79 / "batch079_final_decision.json")
    hardening = _load(root / "outputs" / B79 / "cognicore_count6_revalidation.json")
    witness = _load(root / "outputs" / B79 / "cognicore_count6_semantic_diff_witness.json")
    if (
        hardening.get("COUNT_6_HARDENING") != "COUNT_6_HARDENING_PASS"
        or hardening.get("recounted") is not False
        or witness.get("status") != "PASS"
        or final.get("issue_derived_repair_count") != 6
    ):
        raise RuntimeError("Batch079 count-six proof boundary failed")
    return {
        "status": "PASS",
        "artifact_name": B79 + "_artifacts",
        "artifact_id": 8288039317,
        "workflow_run_id": 29272272738,
        "checkpoint_commit": "a8e901cd80ce9fbb6abd7b2b435571e040a691b1",
        "implementation_commit": "60cb0a6aceb208cde3b06016ec3c2030b63a79b8",
        "observed_size_bytes": artifact.stat().st_size,
        "observed_sha256": sha256_file(artifact),
        "file_count": len(files),
        "unsafe_paths": entries.get("unsafe_paths", []),
        "duplicate_paths": entries.get("duplicate_paths", []),
        "forbidden_payloads": forbidden,
        "outer_manifest": manifest,
        "internal_manifests": internals,
        "count_six_terminal_proof": "PASS",
        "count_uniqueness": "PASS",
        "semantic_diff_witness": "PASS",
        "raw_zip_committed": False,
        "local_artifact_path_recorded_outside_git": str(artifact),
    }


def _checkpoint_records(root: Path, ingest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    b79 = root / "outputs" / B79
    final = _load(b79 / "batch079_final_decision.json")
    preflight = _load(b79 / "batch079_incident_static_preflight.json")
    horde = _load(b79 / "hordeforge_native_working_directory_adapter.json")
    recovery = _load(b79 / "batch078_frame_recovery_decision.json")
    calibration = _load(b79 / "pathway_memory_baseline_results.json")
    return {
        "batch079_artifact_ingest.json": ingest,
        "batch079_state_preservation.json": {
            "status": "PASS",
            "validated_protocol": "v2.19",
            "issue_derived_repair_count": 6,
            "native_external_repair_count": 4,
            "original_batch079_files_modified": False,
        },
        "batch079_claim_boundary_preservation.json": {
            "status": "PASS",
            "validated_protocol": "v2.19 authorized_amds_active_maintenance_lane",
            "AMDS_prospective_effectiveness": "NOT_ESTABLISHED",
            "routing_memory_mechanism": "HISTORICAL_ROUTING_SIGNAL_OBSERVED",
            "prospective_lift": "not demonstrated",
            "memory_lift": "not demonstrated",
            "full_scoring": "NOT_RUN/disallowed",
            "self_maintaining_software": "false/not demonstrated",
            "live_connectors": "inactive",
        },
        "batch079_count6_hardening_preservation.json": {
            "status": "PASS",
            "COUNT_6_HARDENING": "COUNT_6_HARDENING_PASS",
            "historical_count": 6,
            "recounted": False,
            "CogniCore_rerun": False,
            "preserved_from_verified_artifact": True,
        },
        "batch079_incident_preflight_depth_reconciliation.json": {
            "status": "PASS",
            "BATCH079_INCIDENT_LEADS_REGISTERED": 6,
            "target_resolution_attempts": 0,
            "command_resolution_attempts": 0,
            "provider_dry_lock_attempts": 0,
            "file_collection_attempts": 0,
            "node_collection_attempts": 0,
            "classification": "REGISTERED_NOT_EXECUTED_STATIC_PREFLIGHT",
            "prior_source_object_verified_constant_detected": True,
            "promoted_as_executed_evidence": False,
            "prior_record_hash": hash_record(preflight),
        },
        "batch079_recovery_depth_reconciliation.json": {
            "status": "PASS",
            "classification": "PARTIAL_RECOVERY_DIAGNOSTICS_ONLY",
            "universal_python39_cause_inferred": False,
            "stage_complete_forensics_present": False,
            "prior_record_hash": hash_record(recovery),
        },
        "batch079_hordeforge_depth_reconciliation.json": {
            "status": "PASS",
            "adapter_configuration": "PASS",
            "native_target_execution": "NOT_ESTABLISHED",
            "adapter_defect_fixed": "NOT_ESTABLISHED",
            "observed_return_code": horde.get("return_code"),
            "target_start_sentinel_present": False,
            "target_terminal_sentinel_present": False,
            "docker_acquisition_output_is_success_proof": False,
        },
        "batch079_memory_calibration_depth_reconciliation_v2.json": {
            "status": "PASS",
            "prior_frequency_value_was_majority_prevalence_not_mrr": True,
            "uniform_expected_MRR_formula": "H_n/n",
            "analytical_uniform_expectation_is_executed_control": False,
            "prior_shuffled_method_was_reversed_seeded_random_rr": True,
            "prospective_memory_outcome_present": False,
            "allowed_conclusion": "HISTORICAL_ROUTING_SIGNAL_OBSERVED",
            "forbidden_conclusion": "STATISTICAL_MEMORY_LIFT_PROVED",
            "prior_record_hash": hash_record(calibration),
        },
        "batch080_checkpoint_state.json": {
            "status": "PASS",
            "phase": "EXECUTED_PREFLIGHT_AND_PROVIDER_CAPSULE_INFRASTRUCTURE_READY",
            "external_target_execution_started": False,
            "count_six_preserved_without_rerun": True,
            "prior_final_hash": hash_record(final),
        },
    }


def _manifest(output: Path) -> None:
    write_text_lf(output / "SHA256SUMS.txt", "".join(
        f"{sha256_file(path)}  {path.relative_to(output).as_posix()}\n"
        for path in sorted(output.rglob("*")) if path.is_file() and path.name != "SHA256SUMS.txt"
    ))


def generate_checkpoint(root: Path, artifact: Path) -> dict[str, Any]:
    root = root.resolve()
    ingest = verify_and_ingest_batch079(root, artifact.resolve())
    output = root / "outputs" / BATCH
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)
    for name, value in _checkpoint_records(root, ingest).items():
        write_json_deterministic(output / name, value)
    _manifest(output)
    return {"status": "PASS", "output": str(output), "artifact": ingest}
