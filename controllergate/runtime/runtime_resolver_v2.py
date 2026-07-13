from __future__ import annotations

from typing import Any

from .runtime_authority import AUTHORITY_ORDER, runtime_authorized


def resolve_runtime(evidence: dict[str, Any]) -> dict[str, Any]:
    for source in AUTHORITY_ORDER:
        value = evidence.get(source)
        if value:
            return {"status": "PASS", "runtime": value, "authority": source, "weak_fallback_used": False}
    weak = evidence.get("commit_date_runtime")
    return {"status": "BLOCK", "runtime": weak, "authority": "commit_date" if weak else None, "weak_fallback_used": bool(weak), "admission_allowed": False}
