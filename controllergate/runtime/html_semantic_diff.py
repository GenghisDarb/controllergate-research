from __future__ import annotations

import hashlib
import re
from typing import Any


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _extract(pattern: str, text: str) -> list[str]:
    return re.findall(pattern, text, flags=re.IGNORECASE | re.DOTALL)


def compare_html_semantics(before: str, after: str) -> dict[str, Any]:
    before_titles = [re.sub(r"\s+", " ", value).strip() for value in _extract(r"<title>(.*?)</title>", before)]
    after_titles = [re.sub(r"\s+", " ", value).strip() for value in _extract(r"<title>(.*?)</title>", after)]
    before_without_title = re.sub(r"<title>.*?</title>", "<title>__TITLE__</title>", before, flags=re.I | re.S)
    after_without_title = re.sub(r"<title>.*?</title>", "<title>__TITLE__</title>", after, flags=re.I | re.S)
    contracts = {
        "route_registrations": (_extract(r"@app\.(?:get|post|put|delete|patch)\([^\n]+", before), _extract(r"@app\.(?:get|post|put|delete|patch)\([^\n]+", after)),
        "scripts": (_extract(r"<script\b[^>]*>(.*?)</script>", before), _extract(r"<script\b[^>]*>(.*?)</script>", after)),
        "css": (_extract(r"<style\b[^>]*>(.*?)</style>", before), _extract(r"<style\b[^>]*>(.*?)</style>", after)),
        "api_paths": (sorted(set(re.findall(r"/api/[A-Za-z0-9_./{}-]+", before))), sorted(set(re.findall(r"/api/[A-Za-z0-9_./{}-]+", after)))),
        "html_outside_title": ([before_without_title], [after_without_title]),
    }
    unchanged = {name: left == right for name, (left, right) in contracts.items()}
    hashes = {
        name: {"before": _hash(repr(left)), "after": _hash(repr(right))}
        for name, (left, right) in contracts.items()
    }
    title_only = (
        len(before_titles) == len(after_titles) == 1
        and before_titles[0] != after_titles[0]
        and all(unchanged.values())
    )
    return {
        "status": "PASS" if title_only else "BLOCK",
        "changed_node_path": "html/head/title/text()" if title_only else None,
        "old_value": before_titles[0] if len(before_titles) == 1 else None,
        "new_value": after_titles[0] if len(after_titles) == 1 else None,
        "unchanged_nodes": unchanged,
        "unchanged_node_hashes": hashes,
        "title_only_change": title_only,
    }
