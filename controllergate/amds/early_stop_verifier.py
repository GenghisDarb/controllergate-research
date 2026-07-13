from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from controllergate.core.evidence import hash_record


def verify_early_stop(closure: Mapping[str, Any], *, verifier_identity: str) -> dict[str, Any]:
    interlock = closure.get("mandatory_invariant_interlock", {})
    passed = (
        closure.get("status") == "PASS"
        and interlock.get("status") == "PASS"
        and not closure.get("missing_required_edges")
        and not closure.get("essential_alternatives_unresolved")
        and bool(verifier_identity)
    )
    return {
        "status": "PASS" if passed else "BLOCK",
        "independent_verifier": verifier_identity,
        "closure_hash": hash_record(dict(closure)),
        "remaining_edges_nonessential": not closure.get("essential_alternatives_unresolved", True),
        "terminal_action": closure.get("terminal_action"),
    }
