from __future__ import annotations

from .probe_contract_v2 import ProbeContractV2


def probe_cost(probe: ProbeContractV2) -> dict[str, float]:
    return {
        "execution_cost": probe.execution_cost,
        "manual_review_cost": probe.manual_review_cost,
        "security_risk": probe.security_risk,
        "total_probe_cost": probe.total_cost,
    }
