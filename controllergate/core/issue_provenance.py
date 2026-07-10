from __future__ import annotations

import re
from typing import Any

from .source_identity import sha256_json, sha256_text


SHA_RE = re.compile(r"\b[0-9a-fA-F]{40}\b")


def extract_candidate_sha_hints(issue_title: str | None, issue_body: str | None) -> dict[str, Any]:
    text = "\n".join([issue_title or "", issue_body or ""])
    hints = sorted({match.group(0).lower() for match in SHA_RE.finditer(text)})
    return {
        "status": "PASS",
        "candidate_sha_hint_count": len(hints),
        "candidate_sha_hints": hints,
        "candidate_sha_hints_hash": sha256_json(hints),
        "hints_are_approved_sha": False,
        "approval_condition": "hint must resolve to commit and be tied to decision-time-safe source before approval",
        "audit_status": "PASS",
    }


def issue_provenance_policy() -> dict[str, Any]:
    return {
        "status": "PASS",
        "issue_title_hash_allowed": True,
        "issue_body_hash_allowed": True,
        "issue_comments_default": "not_collected",
        "issue_comment_fix_text_patch_guidance_allowed": False,
        "raw_issue_body_committed": False,
        "candidate_sha_hints_are_not_approved_sha": True,
        "audit_status": "PASS",
    }


def issue_hash_summary(title: str | None, body: str | None) -> dict[str, Any]:
    return {
        "status": "PASS",
        "issue_title_hash": sha256_text(title),
        "issue_body_hash": sha256_text(body),
        "raw_issue_text_committed": False,
        "audit_status": "PASS",
    }
