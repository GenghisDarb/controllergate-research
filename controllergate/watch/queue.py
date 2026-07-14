from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone

from .deduplication import event_identity


def enqueue(connection: sqlite3.Connection, connector_id: str, event: dict[str, object]) -> bool:
    digest = event_identity(event)
    cursor = connection.execute(
        "INSERT OR IGNORE INTO candidate_queue(event_hash,connector_id,event_json,state,created_at) VALUES (?,?,?,?,?)",
        (digest, connector_id, json.dumps(event, sort_keys=True), "STATIC_PREFLIGHT_QUEUED", datetime.now(timezone.utc).isoformat()),
    )
    return cursor.rowcount == 1
