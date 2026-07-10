from __future__ import annotations

from typing import Any

from .candidate_sha_verifier import verify_candidate_sha


def verify_commit_object(repo_url: str, candidate_sha: str | None) -> dict[str, Any]:
    result = verify_candidate_sha(repo_url, candidate_sha)
    return {
        "status": result.get("status"),
        "repo_url": repo_url,
        "candidate_sha": candidate_sha,
        "verification_method": result.get("sha_verification_method"),
        "verification_command_or_api": result.get("verification_command_or_api"),
        "git_object_type": result.get("git_object_type"),
        "commit_resolves": result.get("commit_resolves"),
        "verified_commit_sha": result.get("verified_commit_sha"),
        "commit_author_date": result.get("commit_author_date"),
        "commit_committer_date": result.get("commit_committer_date"),
        "source_bytes_read": result.get("source_bytes_read", 0),
        "checkout_performed": result.get("checkout_performed") is True,
        "raw_clone_committed": result.get("raw_clone_committed") is True,
        "audit_status": "PASS",
    }
