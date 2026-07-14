from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


@dataclass
class Catalyst:
    catalyst_id: str
    operation: Callable[[dict[str, Any]], dict[str, Any]]
    active_units: int = 1

    def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        if self.active_units < 1:
            return {"status": "BLOCKED_CATALYST_INACTIVE"}
        return self.operation(context)
