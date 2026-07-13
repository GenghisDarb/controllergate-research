from __future__ import annotations

from collections.abc import Mapping
from typing import Any


MANDATORY_INVARIANTS: tuple[str, ...] = (
    "candidate_identity",
    "source_identity",
    "provider_identity",
    "command_authority",
    "target_identity",
    "harness_origin",
    "runner_target_origin",
    "network_policy",
    "source_test_immutability",
    "authorization",
    "rollback_readiness",
    "proof_readiness",
)


def validate_mandatory_invariants(
    states: Mapping[str, Any], *, memory_condition: str | None = None
) -> dict[str, Any]:
    """Validate invariants that no routing or memory condition may waive."""
    missing = [name for name in MANDATORY_INVARIANTS if name not in states]
    failed = [
        name
        for name in MANDATORY_INVARIANTS
        if name in states and states[name] not in {True, "PASS", "VERIFIED", "READY"}
    ]
    status = "PASS" if not missing and not failed else "BLOCK"
    return {
        "status": status,
        "mandatory_invariants": list(MANDATORY_INVARIANTS),
        "missing": missing,
        "failed": failed,
        "memory_condition": memory_condition,
        "memory_can_waive": False,
        "next_allowed_action": "evaluate_causal_closure" if status == "PASS" else "resolve_mandatory_invariants",
    }
