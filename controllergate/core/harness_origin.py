from __future__ import annotations

ALLOWED_AUTHORITY_TYPES = {
    "pre_existing_reviewed_config",
    "immutable_public_repo_commit",
    "immutable_public_release_bundle",
    "reviewed_manual_bundle",
}

FORBIDDEN_AUTHORITY_TYPES = {
    "same_run_generated_hash",
    "floating_HEAD",
    "prompt_text_hash",
    "unverified_local_file",
    "fixed_gold_future_derived_test_content",
    "issue_body_pasted_fixture",
    "synthetic_test_reconstruction",
}

REQUIRED_HARNESS_ORIGIN_FIELDS = [
    "source_url_or_repo",
    "source_commit_sha_or_bundle_identity",
    "manifest_path",
    "expected_manifest_sha256",
    "observed_manifest_sha256",
    "authority_source",
    "authority_created_before_runtime",
    "self_referential_hash_detected",
    "target_test_path",
    "target_test_sha256",
    "harness_topology_files",
    "pre_execution_sha256",
    "post_execution_sha256",
    "integrity_status",
    "blocker_if_fail",
]


def validate_harness_origin_record(record: dict[str, object]) -> dict[str, object]:
    errors: list[str] = []
    for field in REQUIRED_HARNESS_ORIGIN_FIELDS:
        if field not in record:
            errors.append(f"missing:{field}")
    authority = record.get("authority_source")
    if authority not in ALLOWED_AUTHORITY_TYPES:
        errors.append(f"forbidden_or_unknown_authority:{authority}")
    if authority in FORBIDDEN_AUTHORITY_TYPES:
        errors.append("forbidden_authority_type")
    if record.get("authority_created_before_runtime") is not True:
        errors.append("authority_not_preexisting")
    if record.get("self_referential_hash_detected") is True:
        errors.append("self_referential_hash_detected")
    if record.get("expected_manifest_sha256") != record.get("observed_manifest_sha256"):
        errors.append("manifest_sha_mismatch")
    if record.get("integrity_status") != "PASS":
        errors.append("integrity_status_not_pass")
    return {
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "blocker": None if not errors else record.get("blocker_if_fail", "harness_origin_needed"),
    }


def harness_origin_policy() -> dict[str, object]:
    return {
        "status": "PASS",
        "allowed_authority_types": sorted(ALLOWED_AUTHORITY_TYPES),
        "forbidden_authority_types": sorted(FORBIDDEN_AUTHORITY_TYPES),
        "non_circular_required": True,
        "immutable_decision_time_safe_required": True,
    }
