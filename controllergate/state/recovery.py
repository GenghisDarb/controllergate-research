from __future__ import annotations

import sqlite3


def recover_run(connection: sqlite3.Connection, run_id: str) -> dict[str, object]:
    checkpoint = connection.execute("SELECT * FROM checkpoints WHERE run_id=?", (run_id,)).fetchone()
    if not checkpoint:
        return {"status": "RESTART_FROM_BEGINNING", "run_id": run_id}
    return {"status": "RESUME_FROM_COMMITTED_STAGE", "run_id": run_id, "stage": checkpoint["stage"], "event_hash": checkpoint["event_hash"]}
