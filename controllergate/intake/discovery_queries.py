from __future__ import annotations

import hashlib
import json
import os
from typing import Any
from urllib.parse import quote
from urllib.request import Request, urlopen


QUERY_TEMPLATES = (
    'is:issue is:open language:Python "::test_" AssertionError created:>=2024-01-01',
    'is:issue is:open language:Python "FAILED tests/" pytest created:>=2024-01-01',
    'is:issue is:open language:Python TypeError traceback "test_" created:>=2024-01-01',
    'is:issue is:open language:Python "Python 3.13" regression pytest created:>=2024-01-01',
    'is:issue is:open language:Python "python -m pytest" FAILED created:>=2024-01-01',
)


def _get(url: str) -> dict[str, Any] | list[Any]:
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "ControllerGate-Batch074"}
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    with urlopen(Request(url, headers=headers), timeout=60) as response:
        return json.load(response)


def execute_discovery(*, per_query: int = 30, target_unique: int = 80) -> dict[str, Any]:
    unique: dict[int, dict[str, Any]] = {}
    records = []
    for position, query in enumerate(QUERY_TEMPLATES):
        url = f"https://api.github.com/search/issues?q={quote(query)}&sort=updated&order=desc&per_page={per_query}"
        payload = _get(url)
        items = list(payload.get("items", [])) if isinstance(payload, dict) else []
        records.append({"position": position, "query": query, "sort": "updated", "order": "desc", "page_limit": 1, "per_page": per_query, "result_ids": [item["id"] for item in items], "result_hash": hashlib.sha256(json.dumps(items, sort_keys=True, separators=(",", ":")).encode()).hexdigest()})
        for item in items:
            unique.setdefault(int(item["id"]), item)
    selected = list(unique.values())[:target_unique]
    return {"status": "PASS" if len(selected) >= 50 else "PARTIAL", "queries": records, "raw_unique_issue_count": len(selected), "issues": selected, "query_order_frozen": True, "adaptive_queries": False}


def github_json(url: str) -> dict[str, Any] | list[Any]:
    return _get(url)
