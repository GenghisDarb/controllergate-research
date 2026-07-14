from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .stable_identity import stable_hash


@dataclass(frozen=True)
class Entity:
    entity_id: str
    kind: str
    identity: str
    compartment: str
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def entity_hash(self) -> str:
        return stable_hash({"entity_id": self.entity_id, "kind": self.kind, "identity": self.identity,
                            "compartment": self.compartment, "metadata": self.metadata})
