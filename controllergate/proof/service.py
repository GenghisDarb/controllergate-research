from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from typing import Any

from controllergate.state.integrity import ZERO_HASH, canonical_hash


REQUIRED_REPAIR_PROOFS = {
    "candidate_identity", "provider_identity", "prepatch_failure", "patch_identity",
    "target_validation", "duplicate_clean_replay", "rollback_ready", "claim_boundary",
}


def append_proof(connection: sqlite3.Connection, *, run_id: str, candidate_id: str, proof_type: str, payload: dict[str, Any]) -> str:
    previous = connection.execute("SELECT proof_hash FROM proof_events WHERE run_id=? ORDER BY rowid DESC LIMIT 1", (run_id,)).fetchone()
    parent = str(previous["proof_hash"]) if previous else ZERO_HASH
    value = {"run_id": run_id, "candidate_id": candidate_id, "proof_type": proof_type, "payload": payload, "parent_hash": parent, "created_at": datetime.now(timezone.utc).isoformat()}
    proof_hash = canonical_hash(value)
    connection.execute("INSERT INTO proof_events(proof_hash,run_id,candidate_id,proof_type,proof_json,parent_hash,created_at) VALUES (?,?,?,?,?,?,?)", (proof_hash, run_id, candidate_id, proof_type, json.dumps(payload, sort_keys=True), parent, value["created_at"]))
    return proof_hash


def repair_proof_complete(connection: sqlite3.Connection, candidate_id: str) -> dict[str, object]:
    rows = connection.execute("SELECT proof_type,proof_hash FROM proof_events WHERE candidate_id=?", (candidate_id,)).fetchall()
    present = {str(row["proof_type"]) for row in rows}
    missing = sorted(REQUIRED_REPAIR_PROOFS - present)
    return {"status": "PASS" if not missing else "BLOCK", "candidate_id": candidate_id, "proof_count": len(rows), "missing": missing}
