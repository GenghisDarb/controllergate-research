from __future__ import annotations

from typing import Any


TERMINAL_STATES = {"BLOCK", "MANUAL_REVIEW"}
FORBIDDEN_TRANSITIONS = {
    ("artifact_custody_blocked", "runtime_execution"),
    ("provider_capsule_blocked", "collection"),
    ("collection_blocked", "patch_generation"),
    ("target_validation_missing", "duplicate_replay"),
    ("duplicate_replay_missing", "count_gate"),
    ("count_gate_missing", "runtime_activation"),
}


def transition_allowed(prior: str, proposed: str, policy: dict[str, Any]) -> bool:
    if (prior, proposed) in FORBIDDEN_TRANSITIONS:
        return False
    allowed_prior = set(policy.get("allowed_prior_states") or ["*"])
    allowed_next = set(policy.get("allowed_next_states") or ["*"])
    return ("*" in allowed_prior or prior in allowed_prior) and ("*" in allowed_next or proposed in allowed_next)


def terminal_behavior(decision: str) -> str:
    return "stop_and_close_branch" if decision in TERMINAL_STATES else "continue_if_all_interlocks_pass"
