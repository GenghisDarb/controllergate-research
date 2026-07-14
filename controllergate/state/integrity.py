from __future__ import annotations

import hashlib
import json
import sqlite3
from typing import Any


ZERO_HASH = "0" * 64


def canonical_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


def event_hash(event: dict[str, Any]) -> str:
    return canonical_hash({key: event[key] for key in (
        "event_id", "run_id", "event_type", "parent_event_hash", "input_token_hashes",
        "output_token_hashes", "status", "blocker", "created_at", "worker_identity",
    )})


def verify_event_chain(connection: sqlite3.Connection, run_id: str) -> dict[str, object]:
    rows = connection.execute("SELECT * FROM events WHERE run_id=? ORDER BY rowid", (run_id,)).fetchall()
    parent = ZERO_HASH
    errors: list[str] = []
    for row in rows:
        value = dict(row)
        if value["parent_event_hash"] != parent:
            errors.append(f"parent_mismatch:{value['event_id']}")
        if event_hash(value) != value["event_hash"]:
            errors.append(f"hash_mismatch:{value['event_id']}")
        parent = value["event_hash"]
    return {"status": "PASS" if not errors else "FAIL", "event_count": len(rows), "chain_head": parent, "errors": errors}
