from __future__ import annotations

from typing import Any


def candidate_sha_resolution_request_schema() -> dict[str, Any]:
    return {
        "status": "PASS",
        "required_fields": [
            "candidate_id",
            "repo_url",
            "issue_url",
            "why_sha_needed",
            "acceptable_sha_sources",
            "forbidden_sha_sources",
            "candidate_epoch_boundary",
            "preferred_resolution_method",
            "manual_resolution_instructions",
            "automated_resolution_possible",
            "risk_if_wrong_sha",
            "approval_condition",
        ],
        "audit_status": "PASS",
    }


def candidate_sha_resolution_policy() -> dict[str, Any]:
    return {
        "status": "PASS",
        "acceptable_sha_sources": [
            "issue-linked reproduction commit if verified",
            "release tag commit if issue explicitly targets that release and tag is decision-time safe",
            "buggy commit supplied in manual artifact with hash/provenance",
            "benchmark dataset commit with manifest",
            "prior approved registry entry",
        ],
        "forbidden_sha_sources": [
            "fix PR merge commit",
            "post-fix commit",
            "modern HEAD",
            "assistant guess",
            "issue-comment patch text",
            "unverified external summary",
            "floating branch name without commit hash",
        ],
        "approval_condition": "candidate SHA must resolve to a commit and be tied to decision-time-safe source evidence",
        "audit_status": "PASS",
    }


def build_candidate_sha_resolution_request(
    *,
    candidate_id: str,
    repo_url: str,
    issue_url: str,
    issue_created_at: str | None,
    candidate_sha_hints: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "candidate_id": candidate_id,
        "repo_url": repo_url,
        "issue_url": issue_url,
        "why_sha_needed": "candidate SHA is required before metadata scan, command orthology probe, test execution, or patch authorization",
        "acceptable_sha_sources": candidate_sha_resolution_policy()["acceptable_sha_sources"],
        "forbidden_sha_sources": candidate_sha_resolution_policy()["forbidden_sha_sources"],
        "candidate_epoch_boundary": {
            "issue_created_at": issue_created_at,
            "decision_time_safe_requirement": "candidate commit must be at or before the approved issue/reproduction epoch unless separately justified",
        },
        "preferred_resolution_method": "verify issue-linked or release-tag commit via GitHub API or isolated git object lookup",
        "manual_resolution_instructions": "provide exact 40-character commit SHA with provenance, source URL, observed-at/before evidence, and forbidden-evidence attestation",
        "automated_resolution_possible": bool(candidate_sha_hints),
        "candidate_sha_hints": candidate_sha_hints or [],
        "risk_if_wrong_sha": "wrong source commit can convert provider/materialization work into invalid repair evidence",
        "approval_condition": candidate_sha_resolution_policy()["approval_condition"],
        "audit_status": "PASS",
    }
