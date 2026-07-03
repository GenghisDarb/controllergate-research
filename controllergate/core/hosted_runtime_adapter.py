from __future__ import annotations

from typing import Any


def hosted_runtime_adapter_status(required_python: str) -> dict[str, Any]:
    return {
        "status": "UNVERIFIED",
        "required_python_family": required_python,
        "hosted_runtime_label_allowed_as_evidence": False,
        "exact_runtime_probe_required": True,
        "current_lane_probe_executed": False,
        "target_replay_allowed": False,
        "blocker": "runtime_provider_unverified",
    }

