from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


@dataclass(frozen=True)
class Regulator:
    regulator_id: str
    predicate: Callable[[dict[str, Any]], bool]
    positive: bool = True

    def allows(self, context: dict[str, Any]) -> bool:
        value = bool(self.predicate(context))
        return value if self.positive else not value
