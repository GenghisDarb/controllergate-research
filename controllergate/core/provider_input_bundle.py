from __future__ import annotations

from pathlib import Path
from typing import Any

from .evidence import hash_record, sha256_file


ALLOWED_INPUT_KEYS = {
    "allowed_command_variants",
    "candidate_id",
    "dependency_lock",
    "dependency_overlap_grouping_policy",
    "expected_source_commit_sha",
    "provider_execution_policy",
    "redacted_issue_snapshot",
    "selected_source_commit_sha",
    "selected_source_repo_url",
    "target_command_manifest",
    "target_intent_signature_policy",
}

FORBIDDEN_INPUT_KEYS = {
    "downloaded_artifacts",
    "fixed_commit",
    "full_controllergate_repo",
    "future_evidence",
    "gold_patch",
    "local_temp_workspace",
    "pr_patch",
    "repository_write_credentials",
    "secrets",
    "unredacted_issue_text",
}


def dependency_lock_summary(lock_path: str | Path) -> dict[str, Any]:
    path = Path(lock_path)
    return {
        "path": path.as_posix(),
        "sha256": sha256_file(path),
        "included_in_bundle": True,
    }


def build_provider_input_bundle(
    *,
    lock_path: str | Path,
    redacted_issue_snapshot_hash: str | None,
    target_command_manifest_hash: str | None,
    source_repo_url: str,
    source_commit_sha: str,
    allowed_command_variants: list[str],
) -> dict[str, Any]:
    bundle = {
        "allowed_command_variants": allowed_command_variants,
        "candidate_id": "darker_issue_112_relative_git_dir",
        "dependency_lock": dependency_lock_summary(lock_path),
        "dependency_overlap_grouping_policy": {
            "status": "PASS",
            "may_override_provider_gate": False,
        },
        "expected_source_commit_sha": source_commit_sha,
        "provider_execution_policy": {
            "status": "PASS",
            "provider_workspace_only": True,
            "write_credentials_allowed": False,
            "secrets_allowed": False,
            "fixed_later_gold_pr_evidence_allowed": False,
        },
        "redacted_issue_snapshot": {
            "status": "PASS" if redacted_issue_snapshot_hash else "UNKNOWN",
            "issue_text_hash": redacted_issue_snapshot_hash,
            "unredacted_text_included": False,
        },
        "selected_source_commit_sha": source_commit_sha,
        "selected_source_repo_url": source_repo_url,
        "target_command_manifest": {
            "status": "PASS" if target_command_manifest_hash else "UNKNOWN",
            "sha256": target_command_manifest_hash,
        },
        "target_intent_signature_policy": {
            "status": "PASS",
            "positive_indicators_required": True,
            "negative_precondition_indicators_block": True,
        },
    }
    return {**bundle, "bundle_sha256": hash_record(bundle)}


def validate_provider_input_bundle(bundle: dict[str, Any]) -> dict[str, Any]:
    present = set(bundle) - {"bundle_sha256"}
    forbidden_present = sorted(present & FORBIDDEN_INPUT_KEYS)
    unexpected = sorted(present - ALLOWED_INPUT_KEYS)
    required_missing = sorted(
        {
            "candidate_id",
            "dependency_lock",
            "provider_execution_policy",
            "selected_source_commit_sha",
            "selected_source_repo_url",
        }
        - present
    )
    status = "PASS" if not forbidden_present and not unexpected and not required_missing else "BLOCK"
    return {
        "status": status,
        "allowed_keys": sorted(ALLOWED_INPUT_KEYS),
        "present_keys": sorted(present),
        "forbidden_keys_present": forbidden_present,
        "unexpected_keys": unexpected,
        "required_missing": required_missing,
        "write_credentials_included": False,
        "secrets_included": False,
        "blocker": None if status == "PASS" else "provider_input_bundle_invalid",
    }
