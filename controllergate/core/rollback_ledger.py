from __future__ import annotations

import hashlib
import json


def rollback_block_ledger_policy() -> dict[str, object]:
    return {
        "status": "PASS",
        "rollback_block_entries_required_for_blocked_branches": True,
        "entry_type": "ROLLBACK_BLOCK",
        "required_fields": [
            "entry_index",
            "action",
            "result",
            "blocker",
            "next_allowed_action",
            "rollback_target_entry_index",
            "previous_state_hash",
            "pre_action_hash",
            "attempted_action_hash",
            "rollback_hash",
            "chain_status",
        ],
        "blockers": [
            "rollback_block_missing",
            "rollback_block_hash_chain_broken",
            "proof_ledger_ghost_state_detected",
        ],
    }


def stable_hash(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def rollback_block_entry(
    *,
    entry_index: int,
    action: str,
    blocker: str,
    next_allowed_action: str,
    rollback_target_entry_index: int,
    pre_action_state: object,
    attempted_action_state: object,
) -> dict[str, object]:
    pre_hash = stable_hash(pre_action_state)
    attempted_hash = stable_hash(attempted_action_state)
    rollback_hash = stable_hash({"pre_action_hash": pre_hash, "attempted_action_hash": attempted_hash, "blocker": blocker})
    return {
        "entry_index": entry_index,
        "entry_type": "ROLLBACK_BLOCK",
        "action": action,
        "result": "BLOCK",
        "blocker": blocker,
        "next_allowed_action": next_allowed_action,
        "rollback_target_entry_index": rollback_target_entry_index,
        "previous_state_hash": pre_hash,
        "pre_action_hash": pre_hash,
        "attempted_action_hash": attempted_hash,
        "rollback_hash": rollback_hash,
        "chain_status": "PASS",
    }


def audit_rollback_block_ledger(entries: list[dict[str, object]]) -> dict[str, object]:
    rollback_entries = [entry for entry in entries if entry.get("entry_type") == "ROLLBACK_BLOCK"]
    if not rollback_entries:
        return {"status": "BLOCK", "blocker": "rollback_block_missing", "rollback_block_count": 0}
    broken = [entry for entry in rollback_entries if entry.get("chain_status") != "PASS" or not entry.get("rollback_hash")]
    return {
        "status": "PASS" if not broken else "BLOCK",
        "blocker": None if not broken else "rollback_block_hash_chain_broken",
        "rollback_block_count": len(rollback_entries),
        "broken_entry_indices": [entry.get("entry_index") for entry in broken],
        "entries": entries,
    }
