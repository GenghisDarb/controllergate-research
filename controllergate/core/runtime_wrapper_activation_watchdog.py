from __future__ import annotations

from typing import Any


def runtime_wrapper_activation_watchdog(
    *,
    issue_derived_repair_count: int,
    threshold: int = 20,
) -> dict[str, Any]:
    activation_allowed = issue_derived_repair_count >= threshold
    return {
        "status": "PASS",
        "activation_state": "requires_dedicated_future_batch_with_named_batch" if activation_allowed else "activation_threshold_not_met",
        "issue_derived_repair_count": issue_derived_repair_count,
        "activation_threshold_issue_derived_repairs": threshold,
        "runtime_wrapper_activation_allowed": False,
        "hard_warning_for_next_stage": activation_allowed,
        "current_batch_may_activate_runtime_connectors": False,
        "live_device_repair_enabled": False,
        "self_maintaining_software_claim_allowed": False,
        "audit_status": "PASS",
    }
