from __future__ import annotations

import hashlib
import json
import os
import re
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any


GITHUB_API = "https://api.github.com"
USER_AGENT = "ControllerGate-Batch068e"
SHA_HINT_RE = re.compile(r"\b[0-9a-fA-F]{40}\b")


@dataclass(frozen=True)
class GitHubResponse:
    status: str
    url: str
    data: dict[str, Any] | None
    raw_sha256: str | None
    byte_count: int
    error: str | None = None


def sha256_text(value: str | None) -> str:
    return hashlib.sha256((value or "").encode("utf-8")).hexdigest()


def sha256_json(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def parse_github_repo_url(repo_url: str) -> dict[str, Any]:
    match = re.fullmatch(r"https://github\.com/([^/\s]+)/([^/\s#?]+?)/?", repo_url)
    if not match:
        return {"status": "FAIL", "error": "repo_url_not_github_https"}
    return {"status": "PASS", "owner": match.group(1), "repo": match.group(2)}


def parse_github_issue_url(issue_url: str) -> dict[str, Any]:
    match = re.fullmatch(r"https://github\.com/([^/\s]+)/([^/\s#?]+)/issues/(\d+)/?", issue_url)
    if not match:
        return {"status": "FAIL", "error": "issue_url_not_github_issue_https"}
    return {
        "status": "PASS",
        "owner": match.group(1),
        "repo": match.group(2),
        "issue_number": int(match.group(3)),
    }


def github_api_json(path: str, *, timeout_seconds: int = 30) -> GitHubResponse:
    url = path if path.startswith("https://") else f"{GITHUB_API}{path}"
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": USER_AGENT,
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(
        url,
        headers=headers,
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            raw = response.read()
    except urllib.error.HTTPError as exc:
        return GitHubResponse(status="FAIL", url=url, data=None, raw_sha256=None, byte_count=0, error=f"HTTP {exc.code}")
    except Exception as exc:  # pragma: no cover - exercised only by network failures
        return GitHubResponse(status="FAIL", url=url, data=None, raw_sha256=None, byte_count=0, error=type(exc).__name__)
    try:
        data = json.loads(raw.decode("utf-8"))
    except Exception as exc:
        return GitHubResponse(status="FAIL", url=url, data=None, raw_sha256=hashlib.sha256(raw).hexdigest(), byte_count=len(raw), error=f"json_parse:{type(exc).__name__}")
    return GitHubResponse(status="PASS", url=url, data=data, raw_sha256=hashlib.sha256(raw).hexdigest(), byte_count=len(raw))


def verify_repo_identity(repo_url: str) -> dict[str, Any]:
    parsed = parse_github_repo_url(repo_url)
    if parsed["status"] != "PASS":
        return {
            "status": "FAIL",
            "repo_url": repo_url,
            "repo_identity_status": "repo_url_invalid",
            "error": parsed["error"],
            "source_bytes_read": 0,
            "audit_status": "PASS",
        }
    owner, repo = parsed["owner"], parsed["repo"]
    response = github_api_json(f"/repos/{owner}/{repo}")
    if response.status != "PASS" or not response.data:
        return {
            "status": "FAIL",
            "repo_url": repo_url,
            "repo_owner": owner,
            "repo_name": repo,
            "repo_identity_status": "repo_unreachable",
            "error": response.error,
            "api_url": response.url,
            "source_bytes_read": response.byte_count,
            "audit_status": "PASS",
        }
    data = response.data
    return {
        "status": "PASS",
        "repo_url": repo_url,
        "repo_owner": owner,
        "repo_name": repo,
        "repo_full_name": data.get("full_name"),
        "repo_identity_status": "repo_verified",
        "repo_default_branch": data.get("default_branch"),
        "repo_visibility": data.get("visibility") or ("private" if data.get("private") else "public"),
        "repo_archived_status": bool(data.get("archived")),
        "repo_disabled_status": bool(data.get("disabled")),
        "repo_api_url": response.url,
        "repo_api_sha256": response.raw_sha256,
        "source_bytes_read": response.byte_count,
        "source_checkout_committed": False,
        "audit_status": "PASS",
    }


def verify_issue_identity(issue_url: str) -> dict[str, Any]:
    parsed = parse_github_issue_url(issue_url)
    if parsed["status"] != "PASS":
        return {
            "status": "FAIL",
            "issue_url": issue_url,
            "issue_identity_status": "issue_url_invalid",
            "error": parsed["error"],
            "source_bytes_read": 0,
            "audit_status": "PASS",
        }
    owner, repo, issue_number = parsed["owner"], parsed["repo"], parsed["issue_number"]
    response = github_api_json(f"/repos/{owner}/{repo}/issues/{issue_number}")
    if response.status != "PASS" or not response.data:
        return {
            "status": "FAIL",
            "issue_url": issue_url,
            "repo_owner": owner,
            "repo_name": repo,
            "issue_number": issue_number,
            "issue_identity_status": "issue_unreachable",
            "error": response.error,
            "api_url": response.url,
            "source_bytes_read": response.byte_count,
            "audit_status": "PASS",
        }
    data = response.data
    body = data.get("body") or ""
    title = data.get("title") or ""
    sha_hints = sorted({match.group(0).lower() for match in SHA_HINT_RE.finditer(f"{title}\n{body}")})
    return {
        "status": "PASS",
        "issue_url": issue_url,
        "repo_owner": owner,
        "repo_name": repo,
        "issue_number": issue_number,
        "issue_identity_status": "issue_verified",
        "issue_created_at": data.get("created_at"),
        "issue_updated_at": data.get("updated_at"),
        "issue_state": data.get("state"),
        "issue_title_hash": sha256_text(title),
        "issue_body_hash": sha256_text(body),
        "issue_comments_hash_if_collected": "not_collected",
        "candidate_sha_hint_count": len(sha_hints),
        "candidate_sha_hints": sha_hints,
        "candidate_sha_hints_hash": sha256_json(sha_hints),
        "candidate_sha_hints_are_approved_sha": False,
        "issue_api_url": response.url,
        "issue_api_sha256": response.raw_sha256,
        "source_bytes_read": response.byte_count,
        "raw_issue_body_committed": False,
        "audit_status": "PASS",
    }
