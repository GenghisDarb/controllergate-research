from __future__ import annotations

RISK_CHANNELS = {
    "candidate_starvation_pressure": {
        "threshold": 10,
        "blocker": "candidate_starvation_threshold_reached",
        "action": "switch_to_next_safe_candidate_source_mode_or_stop",
    },
    "evidence_contamination_pressure": {
        "threshold": 0,
        "blocker": "evidence_contamination_pressure_exceeded",
        "action": "hard_block_and_purge_temp_references",
    },
    "dependency_complexity_pressure": {
        "threshold": 3,
        "blocker": "dependency_complexity_overflow",
        "action": "reject_or_demote_to_diagnostic",
    },
    "version_sprawl_pressure": {
        "threshold": 0,
        "blocker": "version_sprawl_consolidation_required",
        "action": "route_through_clean_protocol_or_reusable_workflow",
    },
    "public_claim_pressure": {
        "threshold": 0,
        "blocker": "public_claim_overreach_detected",
        "action": "rewrite_or_block_public_claim",
    },
    "exploration_budget_pressure": {
        "threshold": 0,
        "blocker": "exploration_budget_exhausted",
        "action": "graceful_bounded_exit",
    },
}


def evaluate_risk_channel(channel: str, metric: int) -> dict[str, object]:
    policy = RISK_CHANNELS[channel]
    threshold = int(policy["threshold"])
    if channel in {"evidence_contamination_pressure", "version_sprawl_pressure", "public_claim_pressure"}:
        exceeded = metric > threshold
    elif channel == "exploration_budget_pressure":
        exceeded = metric <= threshold
    else:
        exceeded = metric >= threshold
    return {
        "channel": channel,
        "metric": metric,
        "threshold": threshold,
        "status": "BLOCK" if exceeded else "PASS",
        "action": policy["action"] if exceeded else "continue",
        "blocker": policy["blocker"] if exceeded else None,
    }


def evaluate_homeostasis_state(metrics: dict[str, int]) -> dict[str, object]:
    channels = [evaluate_risk_channel(channel, int(metrics.get(channel, 0))) for channel in RISK_CHANNELS]
    blockers = [item["blocker"] for item in channels if item["blocker"]]
    return {
        "status": "BLOCK" if blockers else "PASS",
        "channels": channels,
        "blockers": blockers,
        "claim": "Safety and routing mechanism only; no memory-lift or self-maintaining claim.",
    }
