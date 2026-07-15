from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
import json
from typing import Any


@dataclass
class ContainmentController:
    active: dict[str, dict[str, Any]] = field(default_factory=dict)

    def contain(self, incident_id: str, scope: tuple[str, ...], *, breach_proven: bool, secondary: bool = False) -> dict[str, Any]:
        if not breach_proven:
            return {"status": "BLOCK", "blocker": "containment_without_breach"}
        if not scope:
            return {"status": "BLOCK", "blocker": "containment_scope_missing"}
        record = {"incident_id": incident_id, "scope": sorted(set(scope)), "layer": "SECONDARY" if secondary else "PRIMARY", "status": "CONTAINED"}
        record["containment_hash"] = sha256(json.dumps(record, sort_keys=True).encode()).hexdigest()
        self.active[incident_id] = record
        return record

    def resolve(self, incident_id: str, *, barrier_restored: bool, threat_resolved: bool) -> dict[str, Any]:
        if incident_id not in self.active:
            return {"status": "BLOCK", "blocker": "containment_not_active"}
        if not barrier_restored or not threat_resolved:
            return {"status": "BLOCK", "blocker": "premature_containment_dissolution"}
        record = self.active.pop(incident_id)
        return {"status": "DISSOLVED", "incident_id": incident_id, "barrier_restored": True, "prior_hash": record["containment_hash"]}
