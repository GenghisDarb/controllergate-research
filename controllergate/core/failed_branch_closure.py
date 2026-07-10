from __future__ import annotations

REQUIRED_BRANCH_FIELDS = [
    "repair_attempt_id",
    "candidate_id",
    "parent_evidence_entry",
    "pre_attempt_source_head",
    "pre_attempt_workspace_hash",
    "pre_attempt_environment_hash",
    "patch_sha256_if_any",
    "patch_apply_status",
    "post_repair_replay_status",
    "failure_classification",
    "rollback_required",
    "rollback_target_entry",
    "branch_closed_without_count_increment",
    "repair_count_increment",
    "duplicate_replay_status",
    "audit_status",
]


def build_failed_branch_record(
    *,
    candidate_id: str,
    parent_evidence_entry: str,
    source_head: str,
    workspace_hash: str,
    environment_hash: str,
    failure_classification: str,
    rollback_target_entry: str,
) -> dict[str, object]:
    return {
        "repair_attempt_id": f"batch069b:{candidate_id}:no_patch_attempt",
        "candidate_id": candidate_id,
        "parent_evidence_entry": parent_evidence_entry,
        "pre_attempt_source_head": source_head,
        "pre_attempt_workspace_hash": workspace_hash,
        "pre_attempt_environment_hash": environment_hash,
        "patch_sha256_if_any": None,
        "patch_apply_status": "NOT_RUN_no_patch_generated",
        "post_repair_replay_status": "NOT_RUN_pre_repair_gate_blocked",
        "failure_classification": failure_classification,
        "rollback_required": False,
        "rollback_target_entry": rollback_target_entry,
        "branch_closed_without_count_increment": True,
        "repair_count_increment": False,
        "duplicate_replay_status": "NOT_RUN",
        "audit_status": "PASS",
    }


def validate_failed_branch_record(record: dict[str, object]) -> dict[str, object]:
    missing = [field for field in REQUIRED_BRANCH_FIELDS if field not in record]
    errors: list[str] = []
    if record.get("branch_closed_without_count_increment") is not True:
        errors.append("branch_not_closed_without_count_increment")
    if record.get("repair_count_increment") is not False:
        errors.append("repair_count_increment_not_false")
    if record.get("duplicate_replay_status") != "NOT_RUN":
        errors.append("duplicate_replay_status_not_not_run")
    if record.get("audit_status") != "PASS":
        errors.append("audit_status_not_pass")
    return {"status": "PASS" if not missing and not errors else "FAIL", "missing": missing, "errors": errors}
