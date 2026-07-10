from __future__ import annotations

import re
from typing import Any


ALLOWED_EXTERNAL_SEED_APPROVAL_STATUSES = [
    "approved_for_command_orthology_probe",
    "approved_for_source_custody_probe",
    "approved_for_manual_artifact_request",
    "approved_for_runtime_connector_request",
    "routing_memory_only",
    "diagnostic_only",
    "rejected_future_or_gold_evidence",
    "rejected_missing_source_url",
    "rejected_missing_issue_url",
    "rejected_missing_candidate_sha",
    "rejected_untrusted_source",
    "rejected_duplicate_or_already_counted",
    "parked_with_reopen_condition",
]


REQUIRED_EXTERNAL_SEED_FIELDS = [
    "candidate_id",
    "repo_url",
    "issue_url",
    "source_url",
    "source_type",
    "reported_candidate_sha",
    "verified_candidate_sha",
    "sha_verification_status",
    "issue_derived_status",
    "source_created_before_fix_status",
    "decision_time_safety_status",
    "gold_fixed_future_exclusion_status",
    "issue_comment_fix_text_exclusion_status",
    "source_license_status",
    "candidate_family",
    "environment_family",
    "runner_family",
    "provider_family",
    "test_framework_family",
    "native_command_evidence_status",
    "harness_origin_status",
    "manual_artifact_required",
    "runtime_connector_required",
    "approval_status",
    "exact_blocker",
    "reopen_condition",
    "allowed_next_action",
    "forbidden_next_action",
    "audit_status",
]


def external_seed_intake_schema() -> dict[str, Any]:
    return {
        "status": "PASS",
        "schema_name": "external_seed_intake_schema",
        "required_fields": REQUIRED_EXTERNAL_SEED_FIELDS,
        "allowed_approval_statuses": ALLOWED_EXTERNAL_SEED_APPROVAL_STATUSES,
        "forbidden_status": "approved_without_source_identity",
        "candidate_sha_format": "40 lowercase hexadecimal characters when verified",
        "audit_status": "PASS",
    }


def _is_40_hex(value: object) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{40}", value) is not None


def classify_external_seed(record: dict[str, Any]) -> dict[str, Any]:
    missing = [field for field in REQUIRED_EXTERNAL_SEED_FIELDS if field not in record]
    errors: list[str] = []
    if not record.get("repo_url"):
        errors.append("repo_url_missing")
    if not record.get("issue_url"):
        errors.append("issue_url_missing")
    if not record.get("source_url"):
        errors.append("source_url_missing")
    sha = record.get("verified_candidate_sha") or record.get("reported_candidate_sha")
    sha_verified = _is_40_hex(sha) and record.get("sha_verification_status") == "verified_decision_time_safe"
    if record.get("approval_status") == "approved_for_command_orthology_probe" and not sha_verified:
        errors.append("approved_without_verified_candidate_sha")
    if record.get("approval_status") == "approved_without_source_identity":
        errors.append("forbidden_approval_status")
    if record.get("approval_status") not in ALLOWED_EXTERNAL_SEED_APPROVAL_STATUSES:
        errors.append("approval_status_not_allowed")
    for field in [
        "decision_time_safety_status",
        "gold_fixed_future_exclusion_status",
        "issue_comment_fix_text_exclusion_status",
        "source_license_status",
    ]:
        if not record.get(field):
            errors.append(f"{field}_missing")
    return {
        "status": "PASS" if not missing and not errors else "FAIL",
        "missing": missing,
        "errors": errors,
        "candidate_sha_verified": sha_verified,
    }


def build_unverified_external_lead(candidate_id: str, repo_url: str, issue_url: str, *, family: str) -> dict[str, Any]:
    record = {
        "candidate_id": candidate_id,
        "repo_url": repo_url,
        "issue_url": issue_url,
        "source_url": issue_url,
        "source_type": "external_search_lead_pending_source_identity",
        "reported_candidate_sha": None,
        "verified_candidate_sha": None,
        "sha_verification_status": "missing_verified_candidate_sha",
        "issue_derived_status": "lead_only_not_repair_evidence",
        "source_created_before_fix_status": "unverified",
        "decision_time_safety_status": "pending_source_identity_verification",
        "gold_fixed_future_exclusion_status": "pending",
        "issue_comment_fix_text_exclusion_status": "pending",
        "source_license_status": "repository_license_not_yet_verified",
        "candidate_family": family,
        "environment_family": "unknown_until_source_identity",
        "runner_family": "unknown_until_command_orthology",
        "provider_family": "unknown_until_provider_classification",
        "test_framework_family": "unknown_until_source_metadata",
        "native_command_evidence_status": "not_verified",
        "harness_origin_status": "not_verified",
        "manual_artifact_required": False,
        "runtime_connector_required": False,
        "approval_status": "parked_with_reopen_condition",
        "exact_blocker": "external_seed_candidate_sha_not_verified",
        "reopen_condition": "verify_source_url_issue_url_and_candidate_sha_from_decision_time_safe_source",
        "allowed_next_action": "batch068e_external_seed_source_identity_verification",
        "forbidden_next_action": ["patch_generation", "test_execution", "count_gate", "memory_lift_claim"],
        "audit_status": "PASS",
    }
    validation = classify_external_seed(record)
    record["validation"] = validation
    return record
