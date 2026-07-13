from __future__ import annotations

from typing import Any


def timeout_stage_plan() -> list[dict[str, Any]]:
    return [
        {"stage": "early_stack_capture", "timeout_seconds": 60, "faulthandler": True, "progress_output": True},
        {"stage": "extended_causal_capture", "timeout_seconds": 180, "faulthandler": True, "progress_output": True},
        {"stage": "upper_bound_not_success_criterion", "timeout_seconds": 600, "execute_by_default": False},
    ]


def classify_timeout_evidence(*, stacks: list[str], subprocesses: list[str], last_step: str | None, fixture_completed: bool | None, direct_invocation_stalled: bool | None) -> str:
    joined = "\n".join(stacks).lower()
    if any(value for value in subprocesses):
        return "EXTERNAL_SERVICE_WAIT"
    if "site-packages" in joined and "/source/" not in joined:
        return "PROVIDER_OR_IMPORT_STALL"
    if fixture_completed is False:
        return "HARNESS_FIXTURE_STALL"
    if direct_invocation_stalled is True and "/source/" in joined:
        return "SOURCE_LOOP_OR_DEADLOCK"
    if last_step and "assert" in last_step.lower():
        return "TARGET_ASSERTION_REPRODUCED"
    return "INSUFFICIENT_EVIDENCE"
