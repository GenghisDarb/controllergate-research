from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Requirement:
    entity_id: str
    multiplicity: int = 1
    required: bool = True
