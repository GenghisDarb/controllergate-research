from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class FailureFamilyGraph:
    initial_families: list[str]
    eliminated_families: list[str] = field(default_factory=list)
    supporting_observations: list[dict] = field(default_factory=list)

    @property
    def remaining(self) -> list[str]:
        return [item for item in self.initial_families if item not in self.eliminated_families]
