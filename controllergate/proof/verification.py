from __future__ import annotations

import json
import sqlite3

from controllergate.state.integrity import ZERO_HASH, canonical_hash


def verify_proof_chain(connection: sqlite3.Connection, run_id: str) -> dict[str, object]:
    parent = ZERO_HASH
    checked = 0
    for row in connection.execute("SELECT * FROM proof_events WHERE run_id=? ORDER BY rowid", (run_id,)):
        payload = json.loads(row["proof_json"])
        value = {
            "run_id": row["run_id"], "candidate_id": row["candidate_id"],
            "proof_type": row["proof_type"], "payload": payload,
            "parent_hash": parent, "created_at": row["created_at"],
        }
        if row["parent_hash"] != parent or row["proof_hash"] != canonical_hash(value):
            return {"status": "FAIL", "blocker": "proof_hash_chain_invalid", "checked": checked}
        parent = str(row["proof_hash"])
        checked += 1
    return {"status": "PASS", "checked": checked, "head": parent}
