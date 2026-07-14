from __future__ import annotations

import sqlite3

from .integrity import canonical_hash


def snapshot(connection: sqlite3.Connection, run_id: str) -> dict[str, object]:
    run = dict(connection.execute("SELECT * FROM runs WHERE run_id=?", (run_id,)).fetchone())
    events = [dict(row) for row in connection.execute("SELECT * FROM events WHERE run_id=? ORDER BY rowid", (run_id,))]
    value: dict[str, object] = {"run": run, "events": events}
    value["snapshot_hash"] = canonical_hash(value)
    return value
