from __future__ import annotations

import sqlite3

from controllergate.state.integrity import canonical_hash


def event_identity(event: dict[str, object]) -> str:
    return canonical_hash(event)


def seen(connection: sqlite3.Connection, event: dict[str, object]) -> bool:
    return connection.execute("SELECT 1 FROM candidate_queue WHERE event_hash=?", (event_identity(event),)).fetchone() is not None
