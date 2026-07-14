from __future__ import annotations

import sqlite3
from datetime import datetime, timezone

from controllergate.state.integrity import canonical_hash

from .service import repair_proof_complete


REPAIR_CLASSES = {"issue_derived", "native_external"}


def decide_count(connection: sqlite3.Connection, *, candidate_id: str, repair_class: str, proof_hash: str, historical_non_counting: bool = False) -> dict[str, object]:
    if repair_class not in REPAIR_CLASSES:
        return {"status": "BLOCK", "blocker": "unknown_repair_class"}
    if historical_non_counting:
        return {"status": "PASS", "decision": "NON_COUNTING_HISTORICAL", "candidate_id": candidate_id}
    complete = repair_proof_complete(connection, candidate_id)
    if complete["status"] != "PASS":
        return {"status": "BLOCK", "blocker": "proof_incomplete", **complete}
    row = connection.execute("SELECT count_hash FROM count_records WHERE candidate_id=?", (candidate_id,)).fetchone()
    if row:
        return {"status": "BLOCK", "blocker": "duplicate_count_rejected", "candidate_id": candidate_id}
    value = {"candidate_id": candidate_id, "repair_class": repair_class, "proof_hash": proof_hash, "decision": "COUNT"}
    count_hash = canonical_hash(value)
    connection.execute("INSERT INTO count_records(count_hash,proof_hash,candidate_id,repair_class,decision,created_at) VALUES (?,?,?,?,?,?)", (count_hash, proof_hash, candidate_id, repair_class, "COUNT", datetime.now(timezone.utc).isoformat()))
    return {"status": "PASS", "decision": "COUNT", "count_hash": count_hash}


def public_counts(connection: sqlite3.Connection) -> dict[str, int]:
    values = {name: 0 for name in REPAIR_CLASSES}
    for row in connection.execute("SELECT repair_class,COUNT(*) AS n FROM count_records WHERE decision='COUNT' GROUP BY repair_class"):
        values[str(row["repair_class"])] = int(row["n"])
    return values
