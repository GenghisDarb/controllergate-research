from __future__ import annotations

from typing import Any

from .evidence import hash_record

REQUIRED_TAG_AUTHORITY_FIELDS = [
    "candidate_id",
    "candidate_repo",
    "candidate_sha",
    "candidate_workspace_path",
    "controllergate_repo_mutated",
    "global_environment_mutated",
    "baseline_registry_precheck_status",
    "candidate_isolated_runtime_status",
    "tag_ref_command",
    "tag_ref_output_hash",
    "tag_object_command",
    "tag_object_output_hash",
    "reachable_tag_filter_command",
    "reachable_tag_set",
    "unreachable_tag_set_count",
    "future_tag_refs_seen",
    "future_tag_refs_used",
    "future_tag_source_read",
    "git_describe_command",
    "git_describe_output",
    "setuptools_scm_version_before",
    "setuptools_scm_version_after",
    "version_origin_normalized",
    "decision_time_safe",
    "forbidden_evidence_checked",
    "audit_status",
    "exact_blocker",
]

ALLOWED_TAG_USE = "version_origin_reconstruction_only"
FORBIDDEN_TAG_USES = [
    "patch_authority",
    "repair_success_claim",
    "count_gate_evidence",
    "memory_lift_evidence",
    "gold_patch_substitute",
    "future_fix_evidence",
    "source_topology_authority",
]


def tag_authority_schema() -> dict[str, Any]:
    return {
        "status": "PASS",
        "required_fields": REQUIRED_TAG_AUTHORITY_FIELDS,
        "allowed_use": ALLOWED_TAG_USE,
        "forbidden_uses": FORBIDDEN_TAG_USES,
        "hard_blockers": [
            "blocked_no_predeclared_ancestor_tag_authority",
            "safe_tag_authority_unbounded_future_tag_exposure",
            "safe_tag_authority_no_reachable_ancestor_tag",
            "tag_authority_used_without_predeclared_manifest",
            "tag_source_bytes_read_forbidden",
            "future_tag_exposure_used_as_authority",
            "tag_authority_timestamp_inversion",
        ],
    }


def validate_tag_authority_record(record: dict[str, Any]) -> dict[str, Any]:
    missing = [field for field in REQUIRED_TAG_AUTHORITY_FIELDS if field not in record]
    errors: list[str] = []
    if record.get("controllergate_repo_mutated") is not False:
        errors.append("controllergate_repo_mutated")
    if record.get("global_environment_mutated") is not False:
        errors.append("global_environment_mutated")
    if record.get("future_tag_refs_used") not in {False, 0}:
        errors.append("future_tag_exposure_used_as_authority")
    if record.get("future_tag_source_read") is not False:
        errors.append("tag_source_bytes_read_forbidden")
    if record.get("decision_time_safe") is not True:
        errors.append("tag_authority_not_decision_time_safe")
    if record.get("audit_status") != "PASS":
        errors.append("tag_authority_audit_not_pass")
    return {"status": "PASS" if not missing and not errors else "FAIL", "missing": missing, "errors": errors}


def build_manifest_entry(
    *,
    candidate_id: str,
    candidate_sha: str,
    repo_url: str,
    remote_url: str,
    discovery_command: str,
    discovery_output_sha256: str,
    tag_ref: str,
    tag_object_sha_if_available: str | None,
    peeled_commit_sha: str,
    is_ancestor_of_candidate: bool,
) -> dict[str, Any]:
    return {
        "candidate_id": candidate_id,
        "candidate_sha": candidate_sha,
        "repo_url": repo_url,
        "remote_url": remote_url,
        "discovery_command": discovery_command,
        "discovery_output_sha256": discovery_output_sha256,
        "tag_ref": tag_ref,
        "tag_object_sha_if_available": tag_object_sha_if_available,
        "peeled_commit_sha": peeled_commit_sha,
        "is_ancestor_of_candidate": is_ancestor_of_candidate,
        "tag_authority_status": "reachable_ancestor_tag" if is_ancestor_of_candidate else "unreachable_future_or_side_tag",
        "allowed_use": ALLOWED_TAG_USE,
        "forbidden_use": FORBIDDEN_TAG_USES,
        "source_bytes_read": False,
        "future_tag_source_read": False,
        "decision_time_safe": is_ancestor_of_candidate,
        "manifest_created_before_version_recheck": True,
        "audit_status": "PASS" if is_ancestor_of_candidate else "EXCLUDED",
    }


def manifest_body_hash(entries: list[dict[str, Any]]) -> str:
    return hash_record({"entries": entries, "allowed_use": ALLOWED_TAG_USE, "forbidden_use": FORBIDDEN_TAG_USES})
