from __future__ import annotations

from typing import Any

from .candidate_sha_verifier import verify_candidate_sha
from .source_identity import parse_github_issue_url, parse_github_repo_url, verify_issue_identity, verify_repo_identity


def verify_external_seed_identity(seed: dict[str, Any]) -> dict[str, Any]:
    repo = verify_repo_identity(seed["repo_url"])
    issue = verify_issue_identity(seed["issue_url"])
    sha = verify_candidate_sha(seed["repo_url"], seed.get("verified_candidate_sha") or seed.get("reported_candidate_sha"))
    repo_parse = parse_github_repo_url(seed["repo_url"])
    issue_parse = parse_github_issue_url(seed["issue_url"])
    source_bytes_read = repo.get("source_bytes_read", 0) + issue.get("source_bytes_read", 0) + sha.get("source_bytes_read", 0)
    repo_issue_verified = repo.get("repo_identity_status") == "repo_verified" and issue.get("issue_identity_status") == "issue_verified"
    candidate_sha_status = sha.get("candidate_sha_status")
    if repo_issue_verified and candidate_sha_status == "candidate_sha_verified":
        approval_status = "approved_source_identity_verified"
        exact_blocker = None
        autonomy_tier = 2
        allowed_next_action = "batch068f_external_seed_metadata_command_orthology_hardening"
    elif repo_issue_verified and candidate_sha_status == "candidate_sha_missing_resolution_required":
        approval_status = "approved_issue_identity_verified_sha_missing"
        exact_blocker = "candidate_sha_missing_resolution_required"
        autonomy_tier = 1
        allowed_next_action = "batch068f_candidate_sha_resolution_intake"
    elif repo.get("repo_identity_status") != "repo_verified":
        approval_status = "rejected_repo_unreachable"
        exact_blocker = "repo_identity_unverified"
        autonomy_tier = 0
        allowed_next_action = "repair_repo_source_identity"
    elif issue.get("issue_identity_status") != "issue_verified":
        approval_status = "rejected_issue_unreachable"
        exact_blocker = "issue_identity_unverified"
        autonomy_tier = 0
        allowed_next_action = "repair_issue_source_identity"
    else:
        approval_status = "parked_candidate_sha_unverified"
        exact_blocker = candidate_sha_status
        autonomy_tier = 1
        allowed_next_action = "batch068f_candidate_sha_resolution_intake"
    return {
        "candidate_id": seed["candidate_id"],
        "repo_url": seed["repo_url"],
        "repo_owner": repo.get("repo_owner") or repo_parse.get("owner"),
        "repo_name": repo.get("repo_name") or repo_parse.get("repo"),
        "repo_identity_status": repo.get("repo_identity_status"),
        "repo_default_branch": repo.get("repo_default_branch"),
        "repo_visibility": repo.get("repo_visibility"),
        "repo_archived_status": repo.get("repo_archived_status"),
        "issue_url": seed["issue_url"],
        "issue_number": issue.get("issue_number") or issue_parse.get("issue_number"),
        "issue_identity_status": issue.get("issue_identity_status"),
        "issue_created_at": issue.get("issue_created_at"),
        "issue_updated_at": issue.get("issue_updated_at"),
        "issue_state": issue.get("issue_state"),
        "issue_title_hash": issue.get("issue_title_hash"),
        "issue_body_hash": issue.get("issue_body_hash"),
        "issue_comments_hash_if_collected": issue.get("issue_comments_hash_if_collected"),
        "reported_candidate_sha": seed.get("reported_candidate_sha"),
        "verified_candidate_sha": sha.get("verified_commit_sha"),
        "candidate_sha_status": candidate_sha_status,
        "sha_verification_method": sha.get("sha_verification_method"),
        "sha_verification_log_hash": sha.get("verification_command_or_api"),
        "candidate_sha_resolves_to_commit": sha.get("candidate_sha_resolves_to_commit"),
        "candidate_sha_reachable_status": sha.get("candidate_sha_reachable_status"),
        "candidate_sha_ref_source": sha.get("candidate_sha_ref_source"),
        "decision_time_safe_source_manifest_path": f"outputs/post_v2_37_hardening_batch068e_external_seed_source_identity_verification/decision_time_safe_source_manifest_{seed['candidate_id']}_batch068e.json",
        "source_bytes_read": source_bytes_read,
        "source_checkout_committed": False,
        "fixed_or_future_source_read": False,
        "gold_patch_read": False,
        "issue_fix_text_used": False,
        "allowed_use": "source_identity_tracking_only" if autonomy_tier == 1 else "metadata_scan_only_after_sha_verification" if autonomy_tier == 2 else "routing_memory_only",
        "forbidden_use": ["patch_generation", "test_execution", "count_gate", "memory_lift_claim", "full_scoring"],
        "approval_status": approval_status,
        "exact_blocker": exact_blocker,
        "reopen_condition": "supply_or_verify_decision_time_safe_candidate_sha" if autonomy_tier < 2 else "metadata_scan_and_command_orthology_dry_run",
        "autonomy_tier": autonomy_tier,
        "candidate_sha_hints": issue.get("candidate_sha_hints") or [],
        "audit_status": "PASS",
        "_repo_identity": repo,
        "_issue_identity": issue,
        "_sha_verification": sha,
    }
