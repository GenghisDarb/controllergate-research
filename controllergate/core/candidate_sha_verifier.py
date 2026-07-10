from __future__ import annotations

import re
from typing import Any

from .source_identity import github_api_json, parse_github_repo_url


def is_40_hex_sha(value: object) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{40}", value) is not None


def verify_candidate_sha(repo_url: str, candidate_sha: object) -> dict[str, Any]:
    repo = parse_github_repo_url(repo_url)
    if repo["status"] != "PASS":
        return {
            "status": "FAIL",
            "candidate_sha_status": "repo_url_invalid",
            "verification_command_or_api": None,
            "workspace_path": None,
            "candidate_sha": candidate_sha,
            "commit_resolves": False,
            "checkout_performed": False,
            "raw_clone_committed": False,
            "source_bytes_read": 0,
            "audit_status": "PASS",
        }
    if not candidate_sha:
        return {
            "status": "PASS",
            "candidate_sha_status": "candidate_sha_missing_resolution_required",
            "sha_verification_method": "not_run_no_candidate_sha_supplied",
            "verification_command_or_api": None,
            "workspace_path": None,
            "repo_url": repo_url,
            "candidate_sha": None,
            "git_object_type": None,
            "commit_resolves": False,
            "candidate_sha_resolves_to_commit": False,
            "candidate_sha_reachable_status": "not_checked_sha_missing",
            "candidate_sha_ref_source": "missing",
            "commit_author_date": None,
            "commit_committer_date": None,
            "verified_commit_sha": None,
            "fetch_strategy": "none_sha_missing",
            "fetch_depth": 0,
            "source_bytes_read": 0,
            "checkout_performed": False,
            "raw_clone_committed": False,
            "audit_status": "PASS",
        }
    sha = str(candidate_sha).lower()
    if not is_40_hex_sha(sha):
        return {
            "status": "PASS",
            "candidate_sha_status": "candidate_sha_not_40_hex",
            "sha_verification_method": "format_check_only",
            "verification_command_or_api": None,
            "workspace_path": None,
            "repo_url": repo_url,
            "candidate_sha": sha,
            "git_object_type": None,
            "commit_resolves": False,
            "candidate_sha_resolves_to_commit": False,
            "candidate_sha_reachable_status": "not_checked_format_invalid",
            "candidate_sha_ref_source": "reported_candidate_sha",
            "commit_author_date": None,
            "commit_committer_date": None,
            "verified_commit_sha": None,
            "fetch_strategy": "none_format_invalid",
            "fetch_depth": 0,
            "source_bytes_read": 0,
            "checkout_performed": False,
            "raw_clone_committed": False,
            "audit_status": "PASS",
        }
    owner, repo_name = repo["owner"], repo["repo"]
    endpoint = f"/repos/{owner}/{repo_name}/commits/{sha}"
    response = github_api_json(endpoint)
    if response.status != "PASS" or not response.data:
        return {
            "status": "PASS",
            "candidate_sha_status": "candidate_sha_does_not_resolve",
            "sha_verification_method": "github_api_commit_lookup",
            "verification_command_or_api": response.url,
            "workspace_path": None,
            "repo_url": repo_url,
            "candidate_sha": sha,
            "git_object_type": None,
            "commit_resolves": False,
            "candidate_sha_resolves_to_commit": False,
            "candidate_sha_reachable_status": "unreachable_or_not_commit",
            "candidate_sha_ref_source": "reported_candidate_sha",
            "commit_author_date": None,
            "commit_committer_date": None,
            "verified_commit_sha": None,
            "fetch_strategy": "github_api_commit_lookup",
            "fetch_depth": 0,
            "source_bytes_read": response.byte_count,
            "checkout_performed": False,
            "raw_clone_committed": False,
            "error": response.error,
            "audit_status": "PASS",
        }
    data = response.data
    verified_sha = data.get("sha")
    commit = data.get("commit") or {}
    return {
        "status": "PASS",
        "candidate_sha_status": "candidate_sha_verified" if verified_sha == sha else "candidate_sha_does_not_resolve",
        "sha_verification_method": "github_api_commit_lookup",
        "verification_command_or_api": response.url,
        "workspace_path": None,
        "repo_url": repo_url,
        "candidate_sha": sha,
        "git_object_type": "commit" if verified_sha == sha else None,
        "commit_resolves": verified_sha == sha,
        "candidate_sha_resolves_to_commit": verified_sha == sha,
        "candidate_sha_reachable_status": "reachable_commit" if verified_sha == sha else "unreachable_or_not_commit",
        "candidate_sha_ref_source": "reported_candidate_sha",
        "commit_author_date": (commit.get("author") or {}).get("date"),
        "commit_committer_date": (commit.get("committer") or {}).get("date"),
        "verified_commit_sha": verified_sha,
        "fetch_strategy": "github_api_commit_lookup",
        "fetch_depth": 0,
        "source_bytes_read": response.byte_count,
        "checkout_performed": False,
        "raw_clone_committed": False,
        "audit_status": "PASS",
    }
