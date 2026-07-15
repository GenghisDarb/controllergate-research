from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from hashlib import sha256
import json
from typing import Any


class DispositionState(str, Enum):
    RECEIVED = "RECEIVED"
    QUARANTINED = "QUARANTINED"
    ADMITTED = "ADMITTED"
    DISPOSED = "DISPOSED"
    REJECTED = "REJECTED"


@dataclass
class PayloadDispositionService:
    toxicity_budget: int

    def dispose(self, payload: dict[str, Any], *, authorization: str | None, toxicity: int) -> dict[str, Any]:
        payload_hash = sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
        if toxicity > self.toxicity_budget:
            return {"status": DispositionState.QUARANTINED.value, "payload_hash": payload_hash, "effect_authority": False}
        if not authorization:
            return {"status": DispositionState.REJECTED.value, "payload_hash": payload_hash, "effect_authority": False}
        return {"status": DispositionState.DISPOSED.value, "payload_hash": payload_hash, "effect_authority": False, "disposition_receipt": sha256((payload_hash + authorization).encode()).hexdigest()}


@dataclass
class AdaptationController:
    maximum_repeats: int
    recovery_observations: int
    counts: dict[str, int] = field(default_factory=dict)

    def observe(self, signal_hash: str, *, measured_recovery: bool = False) -> dict[str, Any]:
        if measured_recovery:
            self.counts[signal_hash] = max(0, self.counts.get(signal_hash, 0) - self.recovery_observations)
            return {"status": "RECOVERING", "remaining_adaptation": self.counts[signal_hash]}
        self.counts[signal_hash] = self.counts.get(signal_hash, 0) + 1
        return {"status": "DESENSITIZED" if self.counts[signal_hash] > self.maximum_repeats else "ACTIVE", "count": self.counts[signal_hash]}


@dataclass(frozen=True)
class DestinationDescriptor:
    destination_id: str
    receptor: str
    schema: str
    activation_policy: str


def verify_destination(descriptor: DestinationDescriptor, *, destination_id: str, receptor: str, schema: str) -> dict[str, Any]:
    errors = []
    if descriptor.destination_id != destination_id: errors.append("wrong_destination")
    if descriptor.receptor != receptor: errors.append("wrong_receptor")
    if descriptor.schema != schema: errors.append("destination_schema_mismatch")
    return {"status": "PASS" if not errors else "BLOCK", "errors": errors, "activation_allowed": not errors and descriptor.activation_policy == "after_docking"}


@dataclass
class MalformedProductController:
    backlog_limit: int
    backlog: list[dict[str, Any]] = field(default_factory=list)

    def inspect(self, product: dict[str, Any], required: set[str]) -> dict[str, Any]:
        missing = sorted(required - set(product))
        if not missing:
            return {"status": "CONFORMANT", "product_hash": sha256(json.dumps(product, sort_keys=True).encode()).hexdigest()}
        if len(self.backlog) >= self.backlog_limit:
            return {"status": "BLOCK", "blocker": "malformed_product_backlog_saturated"}
        record = {"product_hash": sha256(json.dumps(product, sort_keys=True).encode()).hexdigest(), "missing": missing, "authority": "NONE"}
        self.backlog.append(record)
        return {"status": "QUARANTINED", **record}
