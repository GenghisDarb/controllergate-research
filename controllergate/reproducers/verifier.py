from __future__ import annotations

from typing import Any


def verify_duplicate_reproducer(first: dict[str, Any], second: dict[str, Any]) -> dict[str, Any]:
    stable = first.get("return_code") == second.get("return_code") and first.get("semantic_hash") == second.get("semantic_hash")
    return {"status": "PASS" if stable else "BLOCK", "duplicate_replay_stable": stable, "fresh_execution_count": 2}
