from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any

from controllergate.reactions.stable_identity import stable_hash


@dataclass
class RunState:
    run_id: str
    manifest_hash: str
    status: str = "CREATED"
    completed_stages: list[str] = field(default_factory=list)
    evidence: dict[str, Any] = field(default_factory=dict)
    blocker: str | None = None
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def advance(self, stage: str, evidence: Any) -> None:
        if stage not in self.completed_stages:
            self.completed_stages.append(stage)
        self.evidence[stage] = evidence
        self.status = "RUNNING"
        self.updated_at = datetime.now(timezone.utc).isoformat()

    def record(self) -> dict[str, Any]:
        value = asdict(self)
        value["state_hash"] = stable_hash(value)
        return value

    @classmethod
    def from_record(cls, value: dict[str, Any]) -> "RunState":
        fields = {key: value[key] for key in cls.__dataclass_fields__ if key in value}
        return cls(**fields)
