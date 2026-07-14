from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone

from .integrity import ZERO_HASH, event_hash


def append_event(
    connection: sqlite3.Connection, *, event_id: str, run_id: str, event_type: str,
    input_token_hashes: list[str], output_token_hashes: list[str], status: str,
    blocker: str | None, worker_identity: str,
) -> dict[str, object]:
    row = connection.execute("SELECT event_hash FROM events WHERE run_id=? ORDER BY rowid DESC LIMIT 1", (run_id,)).fetchone()
    value = {
        "event_id": event_id, "run_id": run_id, "event_type": event_type,
        "parent_event_hash": str(row["event_hash"]) if row else ZERO_HASH,
        "input_token_hashes": json.dumps(input_token_hashes, separators=(",", ":")),
        "output_token_hashes": json.dumps(output_token_hashes, separators=(",", ":")),
        "status": status, "blocker": blocker,
        "created_at": datetime.now(timezone.utc).isoformat(), "worker_identity": worker_identity,
    }
    value["event_hash"] = event_hash(value)
    connection.execute(
        "INSERT INTO events(event_id,run_id,event_type,parent_event_hash,input_token_hashes,output_token_hashes,status,blocker,created_at,worker_identity,event_hash) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        tuple(value[key] for key in ("event_id","run_id","event_type","parent_event_hash","input_token_hashes","output_token_hashes","status","blocker","created_at","worker_identity","event_hash")),
    )
    return value
