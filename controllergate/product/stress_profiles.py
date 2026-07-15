from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class StressFamily(str, Enum):
    RESOURCE_EXHAUSTION = "RESOURCE_EXHAUSTION"
    REPLICATION_STALL = "REPLICATION_STALL"
    PERSISTENT_DAMAGE = "PERSISTENT_DAMAGE"
    TRANSPORT_SATURATION = "TRANSPORT_SATURATION"
    PROVIDER_UNAVAILABLE = "PROVIDER_UNAVAILABLE"


@dataclass(frozen=True)
class StressProfile:
    family: StressFamily
    threshold: float
    response: str
    inhibitor: str
    recovery_condition: str


class StressResponseController:
    def __init__(self, profiles: list[StressProfile]) -> None:
        self.profiles = {item.family: item for item in profiles}

    def evaluate(self, family: StressFamily, signal: float, *, cofactor_available: bool) -> dict[str, Any]:
        profile = self.profiles[family]
        if signal < profile.threshold:
            return {"status": "NORMAL", "family": family.value, "authority_escalation": False}
        response = profile.response if cofactor_available else "QUIESCENT_WAITING_FOR_COFACTOR"
        return {"status": "STRESS_RESPONSE", "family": family.value, "response": response, "inhibitor": profile.inhibitor, "recovery_condition": profile.recovery_condition, "authority_escalation": False}
