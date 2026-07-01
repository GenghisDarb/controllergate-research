from __future__ import annotations

import hashlib
import json


BATCH013_GATE_ORDER = [
    "baseline_registry_drift_precheck",
    "source_commit_environment_lock",
    "target_command_manifest",
    "fresh_workspace_purity",
    "targeted_seed_presence_and_git_tracking",
    "targeted_seed_schema_validation",
    "targeted_seed_forbidden_evidence_audit",
    "native_first_replay_or_issue_derived_fallback",
    "curvature_feature_mapping",
    "prospective_memory_eligibility",
    "matched_null_preregistration",
]


def stable_hash(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def batch013_gate_chain_policy() -> dict[str, object]:
    return {
        "status": "PASS",
        "gate_order": BATCH013_GATE_ORDER,
        "downstream_execution_requires_all_upstream_pass": True,
        "seed_gate_requires_tracked_file": True,
        "blocker_if_order_violated": "gate_chain_order_violation",
        "blocker_if_seed_missing": "targeted_prospective_seed_missing_or_invalid_after_locks_ready",
    }


def gate_entry(
    *,
    index: int,
    gate_id: str,
    status: str,
    inputs: object,
    outputs: object,
    blocker: str | None = None,
    blocked_by_gate: str | None = None,
) -> dict[str, object]:
    return {
        "gate_index": index,
        "gate_id": gate_id,
        "status": status,
        "input_hash": stable_hash(inputs),
        "output_hash": stable_hash(outputs),
        "blocker": blocker,
        "blocked_by_gate": blocked_by_gate,
    }


def audit_gate_dependency(entries: list[dict[str, object]]) -> dict[str, object]:
    errors: list[str] = []
    seen_block = False
    for expected_index, expected_id in enumerate(BATCH013_GATE_ORDER, start=1):
        if expected_index > len(entries):
            errors.append(f"missing_gate:{expected_id}")
            continue
        entry = entries[expected_index - 1]
        if entry.get("gate_id") != expected_id:
            errors.append(f"gate_order_mismatch:{expected_id}")
        status = entry.get("status")
        if seen_block and status != "NOT_RUN":
            errors.append(f"downstream_gate_ran_after_block:{expected_id}")
        if status == "BLOCK":
            seen_block = True
    return {
        "status": "PASS" if not errors else "BLOCK",
        "errors": errors,
        "gate_count": len(entries),
        "blocked_gate": next((entry.get("gate_id") for entry in entries if entry.get("status") == "BLOCK"), None),
    }
