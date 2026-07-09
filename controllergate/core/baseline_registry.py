from __future__ import annotations

from typing import Any

from .evidence import hash_record

REQUIRED_BASELINE_FIELDS = [
    "baseline_record_id",
    "candidate_id",
    "repair_count_status",
    "source_head_sha",
    "patch_sha256",
    "provider_capsule_hash",
    "command_manifest_hash",
    "environment_lock_hash",
    "expected_replay_command",
    "current_global_environment_hash",
    "current_provider_capsule_hash",
    "current_command_manifest_hash",
    "drift_detected",
    "drift_type",
    "dry_run_replay_required",
    "acquisition_allowed",
    "materialization_allowed",
    "exact_blocker",
]


def make_baseline_record(
    *,
    baseline_record_id: str,
    candidate_id: str,
    repair_count_status: str,
    source_head_sha: str,
    patch_sha256: str,
    provider_capsule: dict[str, Any],
    command_manifest: dict[str, Any],
    environment_lock: dict[str, Any],
    expected_replay_command: str,
    isolated_runtime: bool,
) -> dict[str, Any]:
    provider_hash = hash_record(provider_capsule)
    command_hash = hash_record(command_manifest)
    environment_hash = hash_record(environment_lock)
    drift = False
    return {
        "baseline_record_id": baseline_record_id,
        "candidate_id": candidate_id,
        "repair_count_status": repair_count_status,
        "source_head_sha": source_head_sha,
        "patch_sha256": patch_sha256,
        "provider_capsule_hash": provider_hash,
        "command_manifest_hash": command_hash,
        "environment_lock_hash": environment_hash,
        "expected_replay_command": expected_replay_command,
        "current_global_environment_hash": hash_record({"runtime": "isolated_per_candidate", "global_mutation": False}),
        "current_provider_capsule_hash": provider_hash,
        "current_command_manifest_hash": command_hash,
        "drift_detected": drift,
        "drift_type": "none",
        "dry_run_replay_required": False,
        "acquisition_allowed": isolated_runtime and not drift,
        "materialization_allowed": isolated_runtime and not drift,
        "exact_blocker": None if isolated_runtime and not drift else "baseline_drift_blocking_acquisition",
    }


def validate_baseline_record(record: dict[str, Any]) -> dict[str, Any]:
    missing = [field for field in REQUIRED_BASELINE_FIELDS if field not in record]
    blocked = record.get("drift_detected") is True and (record.get("acquisition_allowed") or record.get("materialization_allowed"))
    return {"status": "PASS" if not missing and not blocked else "FAIL", "missing": missing, "drift_blocking_rule_violated": blocked}


def baseline_registry_snapshot_schema() -> dict[str, Any]:
    return {"status": "PASS", "required_fields": REQUIRED_BASELINE_FIELDS, "hard_blocker": "baseline_drift_blocking_acquisition"}
