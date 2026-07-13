from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from .stable_identity import stable_identity, state_hash


@dataclass(frozen=True)
class Regulator:
    name: str
    polarity: Literal["positive", "negative"]
    status: Literal["PASS", "BLOCK", "UNKNOWN"]
    evidence_reference: str

    @property
    def regulator_id(self) -> str:
        return stable_identity("regulator", {"name": self.name, "polarity": self.polarity, "evidence_reference": self.evidence_reference})

    def to_record(self) -> dict[str, Any]:
        record = {
            "regulator_id": self.regulator_id,
            "name": self.name,
            "polarity": self.polarity,
            "status": self.status,
            "evidence_reference": self.evidence_reference,
        }
        record["state_hash"] = state_hash(record)
        return record
