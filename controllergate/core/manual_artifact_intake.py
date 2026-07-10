from __future__ import annotations

REQUIRED_NATIVE_COMMAND_ARTIFACT_FIELDS = [
    "candidate_id",
    "repo_url",
    "issue_url",
    "candidate_sha",
    "native_target_command",
    "command_source_path",
    "command_source_sha256",
    "command_source_type",
    "source_snapshot_identity",
    "provenance_note",
    "artifact_author",
    "artifact_created_at_utc",
    "artifact_source_url_or_local_path",
    "artifact_sha256",
    "decision_time_safety_claim",
    "forbidden_evidence_exclusion",
    "gold_fixed_future_exclusion",
    "issue_comment_fix_text_exclusion",
    "test_mutation_exclusion",
    "fixture_injection_exclusion",
    "allowed_use",
    "forbidden_use",
    "approval_condition",
    "audit_status",
]

ALLOWED_ARTIFACT_USES = [
    "command_boundary_recovery",
    "harness_origin_planning",
    "pre_repair_replay_gate_planning",
    "manual_artifact_queue_resolution",
]

FORBIDDEN_ARTIFACT_USES = [
    "patch_guidance",
    "repair_proof",
    "count_gate_evidence",
    "memory_lift_evidence",
    "full_scoring_evidence",
    "self_maintaining_claim_evidence",
    "gold_fixed_future_substitute",
]


def native_command_artifact_schema() -> dict[str, object]:
    return {
        "status": "PASS",
        "required_fields": REQUIRED_NATIVE_COMMAND_ARTIFACT_FIELDS,
        "allowed_use": ALLOWED_ARTIFACT_USES,
        "forbidden_use": FORBIDDEN_ARTIFACT_USES,
        "raw_artifact_commit_allowed": False,
    }


def validate_native_command_artifact(record: dict[str, object]) -> dict[str, object]:
    missing = [field for field in REQUIRED_NATIVE_COMMAND_ARTIFACT_FIELDS if field not in record]
    errors: list[str] = []
    allowed_use = record.get("allowed_use") or []
    forbidden_use = record.get("forbidden_use") or []
    if not isinstance(allowed_use, list) or not set(allowed_use).issubset(ALLOWED_ARTIFACT_USES):
        errors.append("allowed_use_invalid")
    if not isinstance(forbidden_use, list) or not set(FORBIDDEN_ARTIFACT_USES).issubset(forbidden_use):
        errors.append("forbidden_use_incomplete")
    for key in [
        "forbidden_evidence_exclusion",
        "gold_fixed_future_exclusion",
        "issue_comment_fix_text_exclusion",
        "test_mutation_exclusion",
        "fixture_injection_exclusion",
    ]:
        if record.get(key) is not True:
            errors.append(f"{key}_not_true")
    if record.get("audit_status") != "PASS":
        errors.append("audit_status_not_pass")
    return {"status": "PASS" if not missing and not errors else "FAIL", "missing": missing, "errors": errors}


def native_command_artifact_template() -> dict[str, object]:
    return {
        "candidate_id": "<required>",
        "repo_url": "<required>",
        "issue_url": "<required>",
        "candidate_sha": "<40_hex_candidate_sha>",
        "native_target_command": "<exact_candidate_era_command>",
        "command_source_path": "<candidate_era_path>",
        "command_source_sha256": "<sha256_of_command_source>",
        "command_source_type": "candidate_local_metadata_or_ci_log_or_verified_manual_snapshot",
        "source_snapshot_identity": "<commit_sha_or_artifact_identity>",
        "provenance_note": "<who_verified_what_and_when>",
        "artifact_author": "<reviewer_or_source>",
        "artifact_created_at_utc": "<ISO-8601-UTC>",
        "artifact_source_url_or_local_path": "<source_url_or_quarantine_path>",
        "artifact_sha256": "<sha256_of_this_artifact>",
        "decision_time_safety_claim": "artifact is tied to the candidate-era source snapshot and excludes future/fixed/gold evidence",
        "forbidden_evidence_exclusion": True,
        "gold_fixed_future_exclusion": True,
        "issue_comment_fix_text_exclusion": True,
        "test_mutation_exclusion": True,
        "fixture_injection_exclusion": True,
        "allowed_use": ALLOWED_ARTIFACT_USES,
        "forbidden_use": FORBIDDEN_ARTIFACT_USES,
        "approval_condition": "hash_and_provenance_verified_without_forbidden_evidence",
        "audit_status": "PASS",
    }
