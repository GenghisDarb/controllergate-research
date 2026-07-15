from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class FineGrainedChannel:
    channel_id: str
    source: str
    destination: str
    credits: int
    max_payload_bytes: int
    events: list[dict[str, Any]] = field(default_factory=list)

    def send(self, source: str, destination: str, payload: bytes) -> dict[str, Any]:
        if source != self.source or destination != self.destination:
            return {"status": "BLOCK", "blocker": "channel_directionality_violation"}
        if len(payload) > self.max_payload_bytes:
            return {"status": "BLOCK", "blocker": "fine_grained_payload_too_large"}
        if self.credits < len(payload):
            return {"status": "BLOCK", "blocker": "channel_saturation"}
        self.credits -= len(payload)
        event = {"status": "DELIVERED", "bytes": len(payload), "remaining_credits": self.credits}
        self.events.append(event)
        return event

    def coupled_exchange(self, outgoing: bytes, incoming: bytes, *, atomic: bool) -> dict[str, Any]:
        if not atomic:
            return {"status": "BLOCK", "blocker": "atomic_coupled_exchange_required"}
        required = len(outgoing) + len(incoming)
        if required > self.credits:
            return {"status": "BLOCK", "blocker": "channel_saturation"}
        self.credits -= required
        return {"status": "COUPLED_EXCHANGE_COMMITTED", "outgoing_bytes": len(outgoing), "incoming_bytes": len(incoming), "leak_detected": False, "remaining_credits": self.credits}
