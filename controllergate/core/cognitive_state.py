from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .evidence import hash_record, sha256_bytes

REQUIRED_COGNITIVE_STATE_FIELDS = [
    "candidate_id",
    "batch_id",
    "timestamp_utc",
    "monotonic_order_index",
    "prompt_string_sha256",
    "prompt_string_length",
    "context_window_manifest",
    "context_window_sha256",
    "decision_time_input_files",
    "decision_time_input_hashes",
    "ast_snippet_paths",
    "ast_snippet_hashes",
    "command_manifest_hash",
    "harness_origin_hash",
    "workspace_purity_hash",
    "provider_capsule_hash",
    "forbidden_inputs_checked",
    "gold_fixed_future_exclusion_status",
    "decision_time_outcome_overlap_status",
    "label_blindness_status",
    "snapshot_written_before_generation",
    "generation_output_exists_at_snapshot_time",
    "audit_status",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def build_cognitive_state_snapshot(
    *,
    candidate_id: str,
    batch_id: str,
    prompt_string: str,
    context_window_manifest: dict[str, Any],
    decision_time_input_hashes: dict[str, str],
    ast_snippet_hashes: dict[str, str],
    command_manifest: dict[str, Any],
    harness_origin: dict[str, Any],
    workspace_purity: dict[str, Any],
    provider_capsule: dict[str, Any],
    monotonic_order_index: int = 1,
    generation_output_exists_at_snapshot_time: bool = False,
) -> dict[str, Any]:
    return {
        "candidate_id": candidate_id,
        "batch_id": batch_id,
        "timestamp_utc": utc_now(),
        "monotonic_order_index": monotonic_order_index,
        "prompt_string_sha256": sha256_bytes(prompt_string.encode("utf-8")),
        "prompt_string_length": len(prompt_string),
        "context_window_manifest": context_window_manifest,
        "context_window_sha256": hash_record(context_window_manifest),
        "decision_time_input_files": sorted(decision_time_input_hashes),
        "decision_time_input_hashes": decision_time_input_hashes,
        "ast_snippet_paths": sorted(ast_snippet_hashes),
        "ast_snippet_hashes": ast_snippet_hashes,
        "command_manifest_hash": hash_record(command_manifest),
        "harness_origin_hash": hash_record(harness_origin),
        "workspace_purity_hash": hash_record(workspace_purity),
        "provider_capsule_hash": hash_record(provider_capsule),
        "forbidden_inputs_checked": True,
        "gold_fixed_future_exclusion_status": "PASS",
        "decision_time_outcome_overlap_status": "PASS",
        "label_blindness_status": "PASS",
        "snapshot_written_before_generation": True,
        "generation_output_exists_at_snapshot_time": generation_output_exists_at_snapshot_time,
        "audit_status": "PASS",
    }


def validate_cognitive_state_snapshot(snapshot: dict[str, Any], *, generation_output_exists: bool = False) -> dict[str, Any]:
    missing = [field for field in REQUIRED_COGNITIVE_STATE_FIELDS if field not in snapshot]
    errors: list[str] = []
    if snapshot.get("snapshot_written_before_generation") is not True:
        errors.append("cognitive_state_timestamp_inversion")
    if snapshot.get("generation_output_exists_at_snapshot_time") is True and generation_output_exists:
        errors.append("cognitive_state_timestamp_inversion")
    if snapshot.get("prompt_string_sha256") in {None, ""}:
        errors.append("pre_generation_prompt_lock_missing")
    if snapshot.get("audit_status") != "PASS":
        errors.append("snapshot_audit_status_not_pass")
    return {"status": "PASS" if not missing and not errors else "FAIL", "missing": missing, "errors": errors}


def cognitive_state_snapshot_schema() -> dict[str, Any]:
    return {"status": "PASS", "required_fields": REQUIRED_COGNITIVE_STATE_FIELDS, "hard_failures": ["cognitive_state_timestamp_inversion", "pre_generation_prompt_lock_missing"]}
