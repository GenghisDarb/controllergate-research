from __future__ import annotations

from typing import Any

PRECONDITION_UNAVAILABLE_SURFACES = {
    "command_boundary_blocked",
    "harness_origin_missing",
    "provider_unavailable",
    "runner_target_collision_unresolved",
    "workspace_purity_blocked",
    "version_origin_missing_tags_without_safe_authority",
}

REQUIRED_REWARD_SIGNAL_FIELDS = [
    "candidate_id",
    "attempt_id",
    "failure_surface",
    "terminal_state",
    "graded_signal",
    "signal_reason",
    "precondition_unavailable",
    "repair_attempted",
    "patch_generated",
    "patch_applied",
    "target_replay_run",
    "target_failure_changed",
    "corruption_detected",
    "near_threshold_information_preserved",
    "memory_update_allowed",
    "memory_update_forbidden_reason",
    "audit_status",
]


def build_reward_signal(
    *,
    candidate_id: str,
    attempt_id: str,
    failure_surface: str,
    terminal_state: str,
    repair_attempted: bool,
    patch_generated: bool,
    patch_applied: bool,
    target_replay_run: bool,
    target_failure_changed: bool = False,
    corruption_detected: bool = False,
    near_threshold_information_preserved: bool = False,
) -> dict[str, Any]:
    precondition_unavailable = failure_surface in PRECONDITION_UNAVAILABLE_SURFACES
    if precondition_unavailable:
        graded_signal = 0.0
        memory_update_allowed = True
        memory_update_forbidden_reason = "repair_skill_memory_forbidden_routing_abstention_only"
        signal_reason = "precondition_unavailable"
    elif patch_generated and repair_attempted and target_replay_run and not corruption_detected:
        graded_signal = 0.5 if near_threshold_information_preserved else 0.1
        memory_update_allowed = False
        memory_update_forbidden_reason = "candidate_local_diagnostic_only_until_validated"
        signal_reason = "near_threshold_or_partial_repair_signal"
    else:
        graded_signal = 0.0
        memory_update_allowed = False
        memory_update_forbidden_reason = "reward_signal_surface_conflated"
        signal_reason = "reward_signal_surface_conflated"
    return {
        "candidate_id": candidate_id,
        "attempt_id": attempt_id,
        "failure_surface": failure_surface,
        "terminal_state": terminal_state,
        "graded_signal": graded_signal,
        "signal_reason": signal_reason,
        "precondition_unavailable": precondition_unavailable,
        "repair_attempted": repair_attempted,
        "patch_generated": patch_generated,
        "patch_applied": patch_applied,
        "target_replay_run": target_replay_run,
        "target_failure_changed": target_failure_changed,
        "corruption_detected": corruption_detected,
        "near_threshold_information_preserved": near_threshold_information_preserved,
        "memory_update_allowed": memory_update_allowed,
        "memory_update_forbidden_reason": memory_update_forbidden_reason,
        "audit_status": "PASS",
    }


def validate_reward_signal(signal: dict[str, Any]) -> dict[str, Any]:
    missing = [field for field in REQUIRED_REWARD_SIGNAL_FIELDS if field not in signal]
    errors: list[str] = []
    if signal.get("precondition_unavailable") is True and signal.get("graded_signal") != 0.0:
        errors.append("precondition_unavailable_signal_nonzero")
    if signal.get("precondition_unavailable") is True and signal.get("memory_update_forbidden_reason") != "repair_skill_memory_forbidden_routing_abstention_only":
        errors.append("precondition_memory_boundary_invalid")
    if signal.get("signal_reason") == "reward_signal_surface_conflated":
        errors.append("reward_signal_surface_conflated")
    return {"status": "PASS" if not missing and not errors else "FAIL", "missing": missing, "errors": errors}


def reward_signal_schema() -> dict[str, Any]:
    return {"status": "PASS", "required_fields": REQUIRED_REWARD_SIGNAL_FIELDS, "precondition_unavailable_signal": 0.0}
