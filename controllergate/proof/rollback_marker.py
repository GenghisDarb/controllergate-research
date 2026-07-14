from __future__ import annotations

from controllergate.reactions.stable_identity import stable_hash


def rollback_marker(repair_attempt_id: str, rollback_target_entry: str, restored_source_hash: str) -> dict[str, str]:
    value = {"repair_attempt_id": repair_attempt_id, "rollback_target_entry": rollback_target_entry, "restored_source_hash": restored_source_hash}
    return {**value, "rollback_marker_hash": stable_hash(value)}
