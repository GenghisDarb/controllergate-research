from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .stable_identity import stable_hash


RESOURCE_KEYS = ("wall_time_ms", "cpu_ms", "memory_bytes", "disk_bytes", "network_requests",
                 "network_bytes", "subprocesses", "probes", "retries", "workers", "artifacts",
                 "log_bytes", "temporary_workspaces")


@dataclass
class ResourceLedger:
    limits: dict[str, int]
    consumed: dict[str, int] = field(default_factory=dict)
    events: list[dict[str, Any]] = field(default_factory=list)

    def consume(self, reaction_id: str, values: dict[str, int]) -> dict[str, object]:
        unknown = set(values) - set(RESOURCE_KEYS)
        if unknown:
            raise ValueError(f"unknown resources: {','.join(sorted(unknown))}")
        projected = {key: self.consumed.get(key, 0) + values.get(key, 0) for key in RESOURCE_KEYS}
        exceeded = [key for key, value in projected.items() if value > self.limits.get(key, 0)]
        event = {"reaction_id": reaction_id, "requested": values, "projected": projected,
                 "exceeded": exceeded, "status": "BLOCK" if exceeded else "PASS"}
        event["event_hash"] = stable_hash(event)
        self.events.append(event)
        if not exceeded:
            self.consumed = projected
        return event


def classify_residue(entity_type: str, *, active_reference: bool, evidence_required: bool,
                     rebuildable: bool) -> str:
    if active_reference or evidence_required:
        return "RETAIN_EVIDENCE"
    if rebuildable:
        return "RECYCLE_WITH_IDENTITY"
    if entity_type in {"sealed_truth", "proof_record", "release_decision"}:
        return "RETAIN_EVIDENCE"
    return "REMOVE_WITH_RECEIPT"
