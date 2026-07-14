from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .entity import Entity
from .event import ReactionEvent, ReactionResult


@dataclass
class ReactionPathway:
    pathway_id: str
    events: list[ReactionEvent]

    def execute(self, entities: list[Entity], context: dict[str, Any]) -> list[ReactionResult]:
        results: list[ReactionResult] = []
        parent: str | None = None
        current = list(entities)
        for event in self.events:
            result = event.execute(current, context, parent_token_hash=parent,
                                   verifier=lambda value: value.get("status") == "PASS")
            results.append(result)
            if result.output_token is None:
                break
            parent = result.output_token.token_hash
            current.append(Entity(result.output_token.token_id, "verified_output_token", parent,
                                  event.destination_compartment))
        return results
