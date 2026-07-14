from __future__ import annotations

import sqlite3
import time


def record_failure(connection: sqlite3.Connection, connector_id: str, *, limit: int = 3) -> dict[str, object]:
    row = connection.execute("SELECT retry_count FROM connector_cursors WHERE connector_id=?", (connector_id,)).fetchone()
    retry = (int(row[0]) if row else 0) + 1
    circuit = "OPEN" if retry >= limit else "CLOSED"
    delay = min(60.0, float(2 ** min(retry, 5)))
    connection.execute(
        "INSERT INTO connector_cursors(connector_id,retry_count,next_retry_time,circuit_state) VALUES (?,?,?,?) "
        "ON CONFLICT(connector_id) DO UPDATE SET retry_count=excluded.retry_count,next_retry_time=excluded.next_retry_time,circuit_state=excluded.circuit_state",
        (connector_id, retry, time.time() + delay, circuit),
    )
    return {"retry_count": retry, "next_retry_seconds": delay, "circuit_state": circuit}
