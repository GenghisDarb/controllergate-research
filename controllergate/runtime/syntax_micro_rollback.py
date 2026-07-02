from __future__ import annotations

import ast
from hashlib import sha256
from typing import Any


def validate_fragment(fragment: str, retry_count: int = 0) -> dict[str, Any]:
    fragment_hash = sha256(fragment.encode("utf-8")).hexdigest()
    try:
        ast.parse(fragment)
    except SyntaxError as exc:
        rollback = f"rollback:{fragment_hash}:{exc.lineno}:{exc.offset}"
        return {
            "status": "ROLLBACK",
            "fragment_hash": fragment_hash,
            "syntax_valid": False,
            "failure_reason": str(exc),
            "rollback_hash": sha256(rollback.encode("utf-8")).hexdigest(),
            "retry_count": retry_count,
            "accepted_repair_evidence": False,
        }
    return {
        "status": "PASS",
        "fragment_hash": fragment_hash,
        "syntax_valid": True,
        "failure_reason": None,
        "rollback_hash": None,
        "retry_count": retry_count,
        "accepted_repair_evidence": True,
    }
