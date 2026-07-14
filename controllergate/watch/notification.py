from __future__ import annotations

import sqlite3
from datetime import datetime, timezone

from controllergate.state.integrity import canonical_hash


def record(connection: sqlite3.Connection, connector_id: str, payload: dict[str, object]) -> str:
    digest = canonical_hash(payload)
    identity = canonical_hash({"connector_id": connector_id, "payload_hash": digest})
    connection.execute("INSERT OR IGNORE INTO notifications(notification_id,connector_id,payload_hash,created_at) VALUES (?,?,?,?)", (identity, connector_id, digest, datetime.now(timezone.utc).isoformat()))
    return identity
