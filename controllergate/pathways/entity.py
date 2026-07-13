from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .compartment import require_compartment
from .stable_identity import contextual_identity, stable_identity, state_hash, versioned_identity_record


@dataclass(frozen=True)
class Entity:
    entity_type: str
    payload_hash: str
    compartment: str
    role: str
    label: str = ""

    @property
    def underlying_identity(self) -> str:
        return stable_identity("entity-payload", {"entity_type": self.entity_type, "payload_hash": self.payload_hash})

    @property
    def entity_id(self) -> str:
        return contextual_identity(self.underlying_identity, require_compartment(self.compartment), self.role)

    def to_record(self) -> dict[str, Any]:
        record = {
            "entity_id": self.entity_id,
            "underlying_identity": self.underlying_identity,
            "entity_type": self.entity_type,
            "payload_hash": self.payload_hash,
            "compartment": require_compartment(self.compartment),
            "role": self.role,
            "label": self.label,
        }
        record.update(versioned_identity_record("entity", {"underlying": self.underlying_identity, "context": self.entity_id}, version=1))
        record["state_hash"] = state_hash(record)
        return record
