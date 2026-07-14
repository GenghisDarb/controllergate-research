from __future__ import annotations

from controllergate.reactions.stable_identity import stable_hash


def verify_branch(record: dict[str, object]) -> dict[str, object]:
    branch_hash = record.get("branch_hash")
    payload = {key: value for key, value in record.items() if key != "branch_hash"}
    errors = []
    if branch_hash != stable_hash(payload):
        errors.append("branch_hash_mismatch")
    if not record.get("branch_closed_without_count_increment"):
        errors.append("failed_branch_not_closed")
    if record.get("rollback_required") and not record.get("rollback_target_entry"):
        errors.append("rollback_target_missing")
    return {"status": "PASS" if not errors else "FAIL", "errors": errors}
