from __future__ import annotations

import hashlib
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from .source_identity import github_api_json, parse_github_repo_url

ROOT_METADATA_NAMES = {
    "pyproject.toml",
    "tox.ini",
    "noxfile.py",
    "setup.cfg",
    "setup.py",
    "pytest.ini",
    "requirements.txt",
    "requirements-dev.txt",
    "requirements-test.txt",
    "requirements_tests.txt",
}


def github_tree(repo_url: str, candidate_sha: str) -> dict[str, Any]:
    parsed = parse_github_repo_url(repo_url)
    if parsed["status"] != "PASS":
        return {"status": "BLOCK", "blocker": "repo_identity_invalid", "entries": []}
    response = github_api_json(f"/repos/{parsed['owner']}/{parsed['repo']}/git/trees/{candidate_sha}?recursive=1")
    if response.status != "PASS" or not response.data:
        return {"status": "BLOCK", "blocker": "decision_time_metadata_acquisition_failed", "entries": [], "error": response.error}
    entries = [
        {"path": item.get("path"), "type": item.get("type"), "git_object_sha": item.get("sha"), "size": item.get("size")}
        for item in response.data.get("tree", [])
        if item.get("type") == "blob"
    ]
    return {
        "status": "PASS",
        "entries": sorted(entries, key=lambda item: str(item["path"])),
        "tree_api_sha256": response.raw_sha256,
        "tree_truncated": bool(response.data.get("truncated")),
    }


def select_metadata_paths(entries: list[dict[str, Any]], *, max_workflows: int = 8, max_docs: int = 5) -> list[str]:
    paths = [str(item["path"]) for item in entries]
    selected = {path for path in paths if "/" not in path and path.lower() in ROOT_METADATA_NAMES}
    selected.update(sorted(path for path in paths if path.startswith(".github/workflows/") and path.endswith((".yml", ".yaml")))[:max_workflows])
    selected.update(
        sorted(
            path for path in paths
            if path.lower().endswith((".md", ".rst"))
            and any(token in path.lower() for token in ("test", "contribut", "develop"))
        )[:max_docs]
    )
    return sorted(selected)


def fetch_pinned_file(repo_url: str, candidate_sha: str, path: str, *, timeout_seconds: int = 30) -> dict[str, Any]:
    parsed = parse_github_repo_url(repo_url)
    if parsed["status"] != "PASS":
        return {"status": "BLOCK", "path": path, "blocker": "repo_identity_invalid"}
    quoted = "/".join(urllib.parse.quote(part, safe="") for part in path.split("/"))
    url = f"https://raw.githubusercontent.com/{parsed['owner']}/{parsed['repo']}/{candidate_sha}/{quoted}"
    request = urllib.request.Request(url, headers={"User-Agent": "ControllerGate-Frontier-Static"})
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        return {"status": "BLOCK", "path": path, "url": url, "blocker": "pinned_metadata_fetch_failed", "error": type(exc).__name__}
    return {
        "status": "PASS",
        "path": path,
        "url": url,
        "sha256": hashlib.sha256(raw).hexdigest(),
        "byte_count": len(raw),
        "text": raw.decode("utf-8", errors="replace"),
        "candidate_sha": candidate_sha,
    }


def extract_explicit_test_paths(issue_text: str) -> list[str]:
    matches = re.findall(r"(?<![A-Za-z0-9_.-])((?:tests?|testing)/[A-Za-z0-9_./-]+\.py(?:[:]{2}[A-Za-z0-9_./:-]+)?)", issue_text)
    return sorted({
        match.split("::", 1)[0]
        for match in matches
        if match.split("::", 1)[0].rsplit("/", 1)[-1] not in {"conftest.py", "__init__.py"}
    })


def infer_issue_url(repo_url: str, candidate_id: str) -> str | None:
    match = re.search(r"_issues?_(\d+)(?:_|$)", candidate_id)
    if not match:
        numbers = re.findall(r"(?:^|_)(\d{2,})(?:_|$)", candidate_id)
        if not numbers:
            return None
        issue_number = numbers[0]
    else:
        issue_number = match.group(1)
    return f"{repo_url.rstrip('/')}/issues/{issue_number}"


def fetch_issue_target_intent(issue_url: str | None) -> dict[str, Any]:
    if not issue_url:
        return {"status": "BLOCK", "blocker": "issue_identity_unavailable", "test_paths": [], "command_authority": False}
    parsed = re.fullmatch(r"https://github\.com/([^/]+)/([^/]+)/issues/(\d+)", issue_url)
    if not parsed:
        return {"status": "BLOCK", "blocker": "issue_identity_invalid", "test_paths": [], "command_authority": False}
    response = github_api_json(f"/repos/{parsed.group(1)}/{parsed.group(2)}/issues/{parsed.group(3)}")
    if response.status != "PASS" or not response.data:
        return {"status": "BLOCK", "blocker": "issue_identity_unreachable", "test_paths": [], "command_authority": False}
    title = str(response.data.get("title") or "")
    body = str(response.data.get("body") or "")
    return {
        "status": "PASS",
        "issue_url": issue_url,
        "issue_created_at": response.data.get("created_at"),
        "issue_title_sha256": hashlib.sha256(title.encode()).hexdigest(),
        "issue_body_sha256": hashlib.sha256(body.encode()).hexdigest(),
        "target_intent_sha256": hashlib.sha256((title + "\n" + body).encode()).hexdigest(),
        "test_paths": extract_explicit_test_paths(title + "\n" + body),
        "command_authority": False,
        "raw_issue_text_committed": False,
        "solution_or_remedy_text_used": False,
    }


def github_auth_available() -> bool:
    return bool(os.environ.get("GITHUB_TOKEN"))
