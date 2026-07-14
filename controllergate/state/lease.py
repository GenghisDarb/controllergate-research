from __future__ import annotations

import sqlite3
import time


def acquire(connection: sqlite3.Connection, run_id: str, worker_identity: str, ttl_seconds: float = 30.0) -> bool:
    now = time.time()
    row = connection.execute("SELECT worker_identity, expires_at FROM worker_leases WHERE run_id=?", (run_id,)).fetchone()
    if row and float(row["expires_at"]) > now and row["worker_identity"] != worker_identity:
        return False
    connection.execute(
        "INSERT INTO worker_leases(run_id,worker_identity,acquired_at,expires_at) VALUES (?,?,?,?) ON CONFLICT(run_id) DO UPDATE SET worker_identity=excluded.worker_identity,acquired_at=excluded.acquired_at,expires_at=excluded.expires_at",
        (run_id, worker_identity, now, now + ttl_seconds),
    )
    return True


def release(connection: sqlite3.Connection, run_id: str, worker_identity: str) -> bool:
    cursor = connection.execute("DELETE FROM worker_leases WHERE run_id=? AND worker_identity=?", (run_id, worker_identity))
    return cursor.rowcount == 1
