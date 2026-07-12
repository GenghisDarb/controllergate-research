from __future__ import annotations

from datetime import datetime, timezone
import hashlib
from typing import Any

from .contamination_classifier import classify_contamination, sanitize_issue_record
from .discovery_queries import github_json


def snapshot_issue(item: dict[str, Any]) -> dict[str, Any]:
    issue = github_json(str(item["url"]))
    comments_url = str(issue.get("comments_url")) + "?per_page=100"
    comments_payload = github_json(comments_url)
    comments = "\n".join(str(entry.get("body") or "") for entry in comments_payload if isinstance(entry, dict))
    body = str(issue.get("body") or "")
    classification = classify_contamination(body, comments)
    sanitized = sanitize_issue_record(title=str(issue.get("title") or ""), body=body, comments=comments, classification=classification)
    return {"status": "PASS", "issue_id": issue["id"], "issue_number": issue["number"], "html_url": issue["html_url"], "state": issue["state"], "created_at": issue["created_at"], "updated_at": issue["updated_at"], "snapshotted_at": datetime.now(timezone.utc).isoformat(), "raw_body_sha256": hashlib.sha256(body.encode()).hexdigest(), "raw_comments_sha256": hashlib.sha256(comments.encode()).hexdigest(), "sanitized": sanitized, "contamination": classification, "raw_text_committed": False}
