from __future__ import annotations

from typing import Any

from .commit_object_verifier import verify_commit_object
from .issue_epoch_snapshot import latest_default_branch_commit_before_issue
from .sha_resolution_confidence import classify_sha_resolution


def candidate_sha_resolution_engine_policy() -> dict[str, Any]:
    return {
        "status": "PASS",
        "supported_source_classes": [
            "explicit_issue_reproduction_commit_verified",
            "manual_artifact_buggy_commit_verified",
            "benchmark_manifest_commit_verified",
            "release_tag_explicitly_referenced_by_issue_verified",
            "latest_release_tag_before_issue_created_verified",
            "latest_default_branch_commit_before_issue_created_verified",
            "prior_approved_registry_commit_verified",
            "sha_unresolved_request_only",
        ],
        "forbidden_sha_sources": [
            "fix PR merge commit",
            "post-fix commit",
            "modern HEAD",
            "assistant guess",
            "issue-comment patch text",
            "unverified external summary",
            "floating branch name without a commit hash",
            "patch diff content",
            "gold/fixed source",
        ],
        "raw_clone_committed": False,
        "patch_authority": False,
        "test_execution_authority": False,
        "audit_status": "PASS",
    }


def acceptable_candidate_sha_source_policy() -> dict[str, Any]:
    return {
        "status": "PASS",
        "acceptable_sources": candidate_sha_resolution_engine_policy()["supported_source_classes"],
        "forbidden_sources": candidate_sha_resolution_engine_policy()["forbidden_sha_sources"],
        "epoch_snapshot_requires_label": True,
        "epoch_snapshot_is_not_issue_reproduction_proof": True,
        "audit_status": "PASS",
    }


def resolve_candidate_sha(record: dict[str, Any]) -> dict[str, Any]:
    candidate_id = record["candidate_id"]
    repo_url = record["repo_url"]
    issue_created_at = record["issue_created_at"]
    default_branch = record.get("repo_default_branch") or "main"
    attempts: list[dict[str, Any]] = []

    supplied_sha = record.get("verified_candidate_sha") or record.get("reported_candidate_sha")
    if supplied_sha:
        verification = verify_commit_object(repo_url, supplied_sha)
        source_class = "explicit_issue_reproduction_commit_verified" if verification.get("commit_resolves") else "sha_unresolved_request_only"
        confidence = classify_sha_resolution(source_class, commit_resolves=bool(verification.get("commit_resolves")))
        attempts.append(
            {
                "candidate_id": candidate_id,
                "repo_url": repo_url,
                "candidate_sha_candidate": supplied_sha,
                "sha_source_class": source_class,
                **verification,
                "source_epoch_boundary": "reported_candidate_sha",
                "issue_created_at": issue_created_at,
                "issue_updated_at": record.get("issue_updated_at"),
                "is_before_or_at_issue_epoch": None,
                "is_after_issue_epoch": None,
                "allowed_use": confidence["allowed_use"],
                "forbidden_use": confidence["forbidden_use"],
            }
        )
    else:
        epoch = latest_default_branch_commit_before_issue(repo_url, default_branch, issue_created_at)
        source_class = epoch.get("sha_source_class", "sha_unresolved_request_only")
        verification = verify_commit_object(repo_url, epoch.get("candidate_sha")) if epoch.get("candidate_sha") else {
            "git_object_type": None,
            "commit_resolves": False,
            "verified_commit_sha": None,
            "commit_author_date": None,
            "commit_committer_date": None,
            "verification_method": epoch.get("verification_method"),
            "verification_command_or_api": epoch.get("verification_command_or_api"),
            "source_bytes_read": epoch.get("source_bytes_read", 0),
            "checkout_performed": False,
            "raw_clone_committed": False,
        }
        confidence = classify_sha_resolution(source_class, commit_resolves=bool(verification.get("commit_resolves")))
        attempts.append(
            {
                "candidate_id": candidate_id,
                "repo_url": repo_url,
                "candidate_sha_candidate": epoch.get("candidate_sha"),
                "sha_source_class": source_class,
                "verification_method": epoch.get("verification_method"),
                "verification_command_or_api": epoch.get("verification_command_or_api"),
                "git_object_type": verification.get("git_object_type"),
                "commit_resolves": verification.get("commit_resolves"),
                "verified_commit_sha": verification.get("verified_commit_sha"),
                "commit_author_date": verification.get("commit_author_date") or epoch.get("commit_author_date"),
                "commit_committer_date": verification.get("commit_committer_date") or epoch.get("commit_committer_date"),
                "source_epoch_boundary": "latest_default_branch_commit_before_or_at_issue_created_at",
                "issue_created_at": issue_created_at,
                "issue_updated_at": record.get("issue_updated_at"),
                "is_before_or_at_issue_epoch": epoch.get("is_before_or_at_issue_epoch") is True,
                "is_after_issue_epoch": epoch.get("is_after_issue_epoch") is True,
                "allowed_use": confidence["allowed_use"],
                "forbidden_use": confidence["forbidden_use"],
                "source_bytes_read": epoch.get("source_bytes_read", 0) + verification.get("source_bytes_read", 0),
                "checkout_performed": False,
                "raw_clone_committed": False,
                "audit_status": "PASS",
            }
        )

    selected = attempts[-1]
    confidence = classify_sha_resolution(selected["sha_source_class"], commit_resolves=bool(selected.get("commit_resolves")))
    decision = {
        "status": "PASS",
        "candidate_id": candidate_id,
        "candidate_sha_status": "candidate_sha_verified" if selected.get("commit_resolves") else "sha_unresolved_request_only",
        "verified_candidate_sha": selected.get("verified_commit_sha"),
        "sha_source_class": selected["sha_source_class"],
        "confidence": confidence["confidence"],
        "tier": confidence["tier"],
        "tier_label": confidence["tier_label"],
        "approved_for_metadata_scan": confidence["tier2_allowed"],
        "approved_for_command_orthology_dry_run": confidence["tier2_allowed"],
        "approved_for_test_execution": False,
        "approved_for_patch_generation": False,
        "exact_blocker": None if confidence["tier2_allowed"] else "candidate_sha_resolution_required",
        "reopen_condition": "metadata_scan_and_command_orthology_dry_run" if confidence["tier2_allowed"] else "supply_decision_time_safe_candidate_sha",
        "audit_status": "PASS",
    }
    return {
        "status": "PASS",
        "candidate_id": candidate_id,
        "attempts": attempts,
        "decision": decision,
        "verified_commit_object_record": selected,
        "decision_time_epoch_boundary": {
            "candidate_id": candidate_id,
            "issue_created_at": issue_created_at,
            "candidate_sha": selected.get("verified_commit_sha"),
            "sha_source_class": selected["sha_source_class"],
            "is_before_or_at_issue_epoch": selected.get("is_before_or_at_issue_epoch"),
            "is_after_issue_epoch": selected.get("is_after_issue_epoch"),
            "audit_status": "PASS",
        },
        "source_identity_tier_update": {
            "candidate_id": candidate_id,
            "prior_tier": record.get("autonomy_tier", 1),
            "new_tier": confidence["tier"],
            "new_tier_label": confidence["tier_label"],
            "audit_status": "PASS",
        },
        "terminal_state": {
            "candidate_id": candidate_id,
            "terminal_state": "tier2_sha_verified" if confidence["tier2_allowed"] else "sha_unresolved_request_only",
            "next_allowed_action": "batch068g_tier2_metadata_command_orthology_hardening" if confidence["tier2_allowed"] else "batch068g_candidate_sha_resolution_expansion",
            "patch_authority": False,
            "test_execution_authority": False,
            "audit_status": "PASS",
        },
    }
