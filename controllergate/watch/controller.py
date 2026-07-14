from __future__ import annotations

from pathlib import Path
from typing import Iterable

from controllergate.state.database import transaction
from controllergate.state.repository import ControllerStateRepository

from .cursor import load, save
from .deduplication import seen
from .notification import record as notify
from .queue import enqueue


class WatchController:
    """Durable read-only event observer; it has no public write capability."""

    def __init__(self, database: str | Path):
        self.repository = ControllerStateRepository(database)

    def observe(self, connector_id: str, events: Iterable[dict[str, object]], cursor: str | None) -> dict[str, object]:
        state = load(self.repository.connection, connector_id)
        if state.get("circuit_state") == "OPEN":
            return {"status": "BLOCK", "blocker": "watch_circuit_open", "write_authority": "READ_ONLY"}
        added = duplicates = 0
        with transaction(self.repository.connection):
            for event in events:
                if seen(self.repository.connection, event):
                    duplicates += 1
                    continue
                added += int(enqueue(self.repository.connection, connector_id, event))
            save(self.repository.connection, connector_id, cursor)
            if added:
                notify(self.repository.connection, connector_id, {"new_events": added, "cursor": cursor})
        return {"status": "PASS", "new_events": added, "duplicates_suppressed": duplicates, "cursor": cursor, "write_authority": "READ_ONLY", "public_writes": 0}
