from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
import json
from typing import Any


@dataclass(frozen=True)
class EventMessage:
    event_id: str
    namespace: str
    receptor: str
    payload_hash: str
    inhibitory: bool = False


@dataclass
class EventPlane:
    receptors: set[tuple[str, str]] = field(default_factory=set)
    queue: list[EventMessage] = field(default_factory=list)
    delivered: set[str] = field(default_factory=set)
    dead_letters: list[dict[str, str]] = field(default_factory=list)
    capacity: int = 32

    def message(self, namespace: str, receptor: str, payload: Any, *, inhibitory: bool = False) -> EventMessage:
        body = {"namespace": namespace, "receptor": receptor, "payload": payload, "inhibitory": inhibitory}
        return EventMessage(sha256(json.dumps(body, sort_keys=True).encode()).hexdigest(), namespace, receptor, sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest(), inhibitory)

    def publish(self, message: EventMessage, *, direct: bool = False) -> dict[str, Any]:
        if (message.namespace, message.receptor) not in self.receptors:
            self.dead_letters.append({"event_id": message.event_id, "reason": "wrong_receptor_or_namespace"})
            return {"status": "DEAD_LETTER", "event_id": message.event_id}
        if message.event_id in self.delivered:
            return {"status": "DUPLICATE_SUPPRESSED", "event_id": message.event_id}
        if direct:
            self.delivered.add(message.event_id)
            return {"status": "DELIVERED", "channel": "DIRECT", "event_id": message.event_id, "acknowledged": True}
        if len(self.queue) >= self.capacity:
            return {"status": "BACKPRESSURE", "event_id": message.event_id, "refractory": True}
        if message.inhibitory:
            self.queue.insert(0, message)
        else:
            self.queue.append(message)
        return {"status": "QUEUED", "event_id": message.event_id}

    def drain(self) -> list[dict[str, Any]]:
        receipts = []
        while self.queue:
            message = self.queue.pop(0)
            self.delivered.add(message.event_id)
            receipts.append({"status": "DELIVERED", "channel": "DURABLE", "event_id": message.event_id, "acknowledged": True, "inhibitory": message.inhibitory})
        return receipts
