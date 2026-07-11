from __future__ import annotations

from typing import Any


def build_backend_plan(requirements: list[str], cutoff: str) -> dict[str, Any]:
    return {"status": "PASS" if requirements else "NOT_RUN", "requirements": requirements, "cutoff": cutoff, "network_stage": "bounded_prefetch", "metadata_stage_network": "none", "test_execution_allowed": False}
