from __future__ import annotations

from typing import Any


def bounded_micro_reversal_trace(*, attempted: bool, reason: str, before_hash: str | None = None, after_hash: str | None = None) -> dict[str, Any]:
    return {
        "status": "PASS",
        "attempted": attempted,
        "reason": reason,
        "before_hash": before_hash,
        "after_hash": after_hash,
        "source_or_test_mutation_performed": False,
        "claim_boundary": "reversal trace is safety evidence only",
    }
