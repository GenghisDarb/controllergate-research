from __future__ import annotations

import json
from hashlib import sha256
from typing import Any

ALLOWED_ACTION_TYPES = {
    "repair_candidate_admitted",
    "repair_candidate_rejected",
    "environment_restore_required",
    "sandbox_probe_required",
    "patch_ready_for_review",
    "shadow_deploy_ready",
    "rollback_required",
    "safe_stop_required",
    "runtime_monitoring_required",
}

RUNTIME_ACTIONS = {"patch_ready_for_review", "shadow_deploy_ready"}


def _hash(value: Any) -> str:
    return sha256(json.dumps(value, sort_keys=True, default=str).encode("utf-8")).hexdigest()


def compile_action_manifest(proof_record: dict[str, Any], lock_sequence: list[str], action_type: str) -> dict[str, Any]:
    if action_type not in ALLOWED_ACTION_TYPES:
        return {"status": "BLOCK", "blocker": "unsupported_action_type", "action_type": action_type}
    required_validation = ["target_validation", "duplicate_replay", "post_patch_constraint_revalidation", "no_overreach_validation"]
    has_runtime_evidence = all(proof_record.get(name) == "PASS" for name in required_validation)
    if action_type in RUNTIME_ACTIONS and not has_runtime_evidence:
        return {
            "status": "BLOCK",
            "blocker": "runtime_action_missing_validation_replay_or_no_overreach",
            "action_type": action_type,
            "lock_sequence": lock_sequence,
            "evidence_hash": _hash(proof_record),
        }
    if proof_record.get("status") != "PASS":
        return {
            "status": "BLOCK",
            "blocker": "proof_record_not_passed",
            "action_type": action_type,
            "lock_sequence": lock_sequence,
            "evidence_hash": _hash(proof_record),
        }
    return {
        "status": "PASS",
        "action_type": action_type,
        "lock_sequence": lock_sequence,
        "evidence_hash": _hash(proof_record),
        "executes_action": False,
        "manifest_hash": _hash({"action_type": action_type, "lock_sequence": lock_sequence, "proof_record": proof_record}),
    }
