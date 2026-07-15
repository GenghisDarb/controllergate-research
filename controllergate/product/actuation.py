from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
import json
from typing import Any


@dataclass(frozen=True)
class ActuatorAuthorization:
    authorization_id: str
    actuator_id: str
    target: str
    resource_units: int


@dataclass
class Actuator:
    actuator_id: str
    capabilities: set[str]
    available_resources: int
    consumed: set[str] = field(default_factory=set)
    emergency_stopped: bool = False

    def authorize(self, capability: str, target: str, resource_units: int) -> ActuatorAuthorization:
        if capability not in self.capabilities or resource_units <= 0 or resource_units > self.available_resources:
            raise PermissionError("actuator_capability_or_resource_gate_failed")
        identity = sha256(json.dumps({"actuator": self.actuator_id, "capability": capability, "target": target, "resources": resource_units}, sort_keys=True).encode()).hexdigest()
        return ActuatorAuthorization(identity, self.actuator_id, target, resource_units)

    def execute(self, authorization: ActuatorAuthorization, effect: dict[str, Any], *, target: str) -> dict[str, Any]:
        if self.emergency_stopped:
            return {"status": "BLOCK", "blocker": "actuator_emergency_stopped"}
        if authorization.authorization_id in self.consumed:
            return {"status": "BLOCK", "blocker": "single_effect_authorization_reused"}
        if authorization.actuator_id != self.actuator_id or authorization.target != target:
            return {"status": "BLOCK", "blocker": "target_coupling_mismatch"}
        self.consumed.add(authorization.authorization_id)
        self.available_resources -= authorization.resource_units
        return {"status": "EFFECT_COMMITTED", "authorization_id": authorization.authorization_id, "effect_hash": sha256(json.dumps(effect, sort_keys=True).encode()).hexdigest(), "reset": True}

    def emergency_stop(self, reason: str) -> dict[str, Any]:
        self.emergency_stopped = True
        return {"status": "EMERGENCY_STOPPED", "reason": reason}
