from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from .stable_identity import stable_hash


class JunctionClass(str, Enum):
    CONFIDENTIALITY_BARRIER = "CONFIDENTIALITY_BARRIER"
    IDENTITY_ANCHOR = "IDENTITY_ANCHOR"
    BOUNDED_MESSAGE_CHANNEL = "BOUNDED_MESSAGE_CHANNEL"
    EXTERNAL_EVIDENCE_ANCHOR = "EXTERNAL_EVIDENCE_ANCHOR"
    DYNAMIC_ADAPTOR_JUNCTION = "DYNAMIC_ADAPTOR_JUNCTION"


@dataclass(frozen=True)
class JunctionContract:
    junction_id: str
    junction_class: JunctionClass
    producer: str
    consumer: str
    schema: str
    allowed_fields: frozenset[str]
    forbidden_fields: frozenset[str]
    maximum_bytes: int
    timeout_seconds: int
    retry_limit: int
    idempotent: bool

    @property
    def contract_hash(self) -> str:
        return stable_hash({"junction_id": self.junction_id, "class": self.junction_class.value,
                            "producer": self.producer, "consumer": self.consumer, "schema": self.schema,
                            "allowed": sorted(self.allowed_fields), "forbidden": sorted(self.forbidden_fields),
                            "maximum_bytes": self.maximum_bytes, "timeout_seconds": self.timeout_seconds,
                            "retry_limit": self.retry_limit, "idempotent": self.idempotent})

    def verify(self, message: dict[str, Any], *, producer: str, consumer: str) -> dict[str, object]:
        encoded = repr(sorted(message.items())).encode("utf-8")
        errors = []
        if producer != self.producer or consumer != self.consumer:
            errors.append("junction_identity_mismatch")
        if set(message) - self.allowed_fields:
            errors.append("unregistered_message_field")
        if set(message) & self.forbidden_fields:
            errors.append("forbidden_message_field")
        if len(encoded) > self.maximum_bytes:
            errors.append("message_budget_exceeded")
        return {"status": "PASS" if not errors else "BLOCK", "errors": errors,
                "contract_hash": self.contract_hash, "message_hash": stable_hash(message)}
