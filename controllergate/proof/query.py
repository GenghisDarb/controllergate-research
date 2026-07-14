from __future__ import annotations

import sqlite3


def count_records(connection: sqlite3.Connection) -> list[dict[str, object]]:
    return [dict(row) for row in connection.execute(
        "SELECT candidate_id,repair_class,decision,proof_hash,count_hash,created_at FROM count_records ORDER BY rowid"
    )]


def proof_summary(connection: sqlite3.Connection) -> dict[str, object]:
    proofs = int(connection.execute("SELECT COUNT(*) FROM proof_events").fetchone()[0])
    counts = int(connection.execute("SELECT COUNT(*) FROM count_records WHERE decision='COUNT'").fetchone()[0])
    return {"status": "PASS", "proof_events": proofs, "count_records": counts}
