from __future__ import annotations

from typing import Any
from urllib.parse import urlencode

from .source_identity import github_api_json, parse_github_repo_url


def latest_default_branch_commit_before_issue(
    repo_url: str,
    default_branch: str,
    issue_created_at: str,
) -> dict[str, Any]:
    parsed = parse_github_repo_url(repo_url)
    if parsed["status"] != "PASS":
        return {
            "status": "FAIL",
            "candidate_sha_status": "repo_url_invalid",
            "repo_url": repo_url,
            "source_bytes_read": 0,
            "audit_status": "PASS",
        }
    query = urlencode({"sha": default_branch, "until": issue_created_at, "per_page": 1})
    response = github_api_json(f"/repos/{parsed['owner']}/{parsed['repo']}/commits?{query}")
    if response.status != "PASS" or not isinstance(response.data, list) or not response.data:
        return {
            "status": "PASS",
            "candidate_sha_status": "sha_unresolved_request_only",
            "sha_source_class": "sha_unresolved_request_only",
            "repo_url": repo_url,
            "repo_default_branch": default_branch,
            "issue_created_at": issue_created_at,
            "source_bytes_read": response.byte_count,
            "error": response.error,
            "audit_status": "PASS",
        }
    commit = response.data[0]
    sha = commit.get("sha")
    commit_data = commit.get("commit") or {}
    return {
        "status": "PASS",
        "candidate_sha_status": "candidate_sha_verified",
        "sha_source_class": "latest_default_branch_commit_before_issue_created_verified",
        "repo_url": repo_url,
        "repo_default_branch": default_branch,
        "issue_created_at": issue_created_at,
        "candidate_sha": sha,
        "commit_author_date": (commit_data.get("author") or {}).get("date"),
        "commit_committer_date": (commit_data.get("committer") or {}).get("date"),
        "is_before_or_at_issue_epoch": True,
        "is_after_issue_epoch": False,
        "verification_method": "github_api_commits_until_issue_created_at",
        "verification_command_or_api": response.url,
        "source_bytes_read": response.byte_count,
        "audit_status": "PASS",
    }


def decision_time_epoch_policy() -> dict[str, Any]:
    return {
        "status": "PASS",
        "allowed_epoch_sources": [
            "explicit issue reproduction commit",
            "issue-explicit release tag",
            "latest default-branch commit before issue_created_at",
        ],
        "epoch_snapshot_is_not_reproduction_proof": True,
        "epoch_snapshot_allows_metadata_scan_only": True,
        "epoch_snapshot_allows_patch_or_test_execution": False,
        "audit_status": "PASS",
    }
