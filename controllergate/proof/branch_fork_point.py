from __future__ import annotations

from controllergate.reactions.stable_identity import stable_hash


def fork_point(parent_evidence_entry: str, parent_ledger_hash: str, repair_attempt_id: str) -> dict[str, str]:
    value = {"parent_evidence_entry": parent_evidence_entry, "parent_ledger_hash": parent_ledger_hash, "repair_attempt_id": repair_attempt_id}
    return {**value, "fork_hash": stable_hash(value)}
