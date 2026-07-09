from __future__ import annotations

REQUIRED_FAILED_BRANCH_FIELDS = [
    "parent_evidence_entry",
    "pre_attempt_source_head",
    "pre_attempt_workspace_hash",
    "pre_attempt_environment_hash",
    "attempt_type",
    "patch_sha256",
    "provider_setup_hash",
    "command_manifest_hash",
    "attempt_status",
    "failure_classification",
    "rollback_required",
    "rollback_target_entry",
    "branch_closed_without_count_increment",
    "hash_chain_valid",
]


def make_failed_attempt_branch_record(**fields: object) -> dict[str, object]:
    record = {field: fields.get(field) for field in REQUIRED_FAILED_BRANCH_FIELDS}
    missing = [field for field, value in record.items() if value is None]
    record["status"] = "PASS" if not missing else "FAIL"
    record["missing"] = missing
    return record


def validate_failed_attempt_branch_record(record: dict[str, object]) -> dict[str, object]:
    missing = [field for field in REQUIRED_FAILED_BRANCH_FIELDS if field not in record or record.get(field) is None]
    count_safe = record.get("branch_closed_without_count_increment") is True
    hash_safe = record.get("hash_chain_valid") is True
    return {
        "status": "PASS" if not missing and count_safe and hash_safe else "FAIL",
        "missing": missing,
        "branch_closed_without_count_increment": count_safe,
        "hash_chain_valid": hash_safe,
    }


def proof_ledger_forkpoint_policy() -> dict[str, object]:
    return {
        "status": "PASS",
        "failed_attempt_is_not_ledger_corruption_when_closed": True,
        "required_fields": REQUIRED_FAILED_BRANCH_FIELDS,
    }
