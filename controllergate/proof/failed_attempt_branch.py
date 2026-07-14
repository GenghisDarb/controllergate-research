from __future__ import annotations

from controllergate.reactions.stable_identity import stable_hash


REQUIRED = {
    "repair_attempt_id", "candidate_id", "parent_evidence_entry", "parent_ledger_hash", "pre_attempt_source_head",
    "pre_attempt_workspace_hash", "provider_seal", "patch_sha256", "patch_apply_status", "post_repair_target_status",
    "native_invariant_status", "duplicate_replay_status", "canary_status", "rollback_status", "failure_classification",
    "new_information", "rollback_required", "rollback_target_entry", "next_legal_action", "reopen_condition",
    "branch_closed_without_count_increment",
}


def seal_failed_attempt(record: dict[str, object]) -> dict[str, object]:
    missing = REQUIRED - set(record)
    if missing:
        raise ValueError(f"failed_attempt_fields_missing:{','.join(sorted(missing))}")
    return {**record, "branch_hash": stable_hash(record)}
