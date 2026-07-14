from __future__ import annotations

import sqlite3
from datetime import datetime, timezone


def load(connection: sqlite3.Connection, connector_id: str) -> dict[str, object]:
    row = connection.execute("SELECT * FROM connector_cursors WHERE connector_id=?", (connector_id,)).fetchone()
    return dict(row) if row else {"connector_id": connector_id, "cursor": None, "retry_count": 0, "circuit_state": "CLOSED"}


def save(connection: sqlite3.Connection, connector_id: str, cursor: str | None) -> None:
    connection.execute(
        "INSERT INTO connector_cursors(connector_id,cursor,last_successful_read,retry_count,next_retry_time,circuit_state) VALUES (?,?,?,?,?,?) "
        "ON CONFLICT(connector_id) DO UPDATE SET cursor=excluded.cursor,last_successful_read=excluded.last_successful_read,retry_count=0,next_retry_time=NULL,circuit_state='CLOSED'",
        (connector_id, cursor, datetime.now(timezone.utc).isoformat(), 0, None, "CLOSED"),
    )
