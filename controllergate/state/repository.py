from __future__ import annotations

import json
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .database import connect, initialize, transaction
from .event_store import append_event
from .integrity import canonical_hash, verify_event_chain
from .migrations import migrate


RUN_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")


class ControllerStateRepository:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.connection = connect(self.path)
        initialize(self.connection)
        migrate(self.connection)

    def close(self) -> None:
        self.connection.close()

    def create_run(self, run_id: str, candidate_id: str, manifest: dict[str, Any]) -> dict[str, object]:
        if not RUN_ID.fullmatch(run_id) or ".." in run_id:
            raise ValueError("unsafe run ID")
        now = datetime.now(timezone.utc).isoformat()
        manifest_json = json.dumps(manifest, sort_keys=True, separators=(",", ":"))
        with transaction(self.connection):
            self.connection.execute("INSERT INTO runs(run_id,candidate_id,status,created_at,updated_at) VALUES (?,?,?,?,?)", (run_id, candidate_id, "CREATED", now, now))
            self.connection.execute("INSERT INTO run_manifests(run_id,manifest_json,manifest_hash) VALUES (?,?,?)", (run_id, manifest_json, canonical_hash(manifest)))
            event = append_event(self.connection, event_id=f"{run_id}:created", run_id=run_id, event_type="RUN_CREATED", input_token_hashes=[], output_token_hashes=[], status="PASS", blocker=None, worker_identity="controllergate")
        return {"run_id": run_id, "status": "CREATED", "manifest_hash": canonical_hash(manifest), "event_hash": event["event_hash"]}

    def complete_stage(self, run_id: str, stage: str, input_tokens: list[str], output_tokens: list[str], worker: str = "controllergate") -> dict[str, object]:
        event_id = f"{run_id}:{stage}"
        existing = self.connection.execute("SELECT * FROM events WHERE event_id=?", (event_id,)).fetchone()
        if existing:
            return dict(existing)
        now = datetime.now(timezone.utc).isoformat()
        with transaction(self.connection):
            event = append_event(self.connection, event_id=event_id, run_id=run_id, event_type=stage, input_token_hashes=input_tokens, output_token_hashes=output_tokens, status="PASS", blocker=None, worker_identity=worker)
            self.connection.execute("UPDATE runs SET status=?,updated_at=? WHERE run_id=?", (stage, now, run_id))
            self.connection.execute("INSERT INTO checkpoints(run_id,stage,event_hash,state_json,committed_at) VALUES (?,?,?,?,?) ON CONFLICT(run_id) DO UPDATE SET stage=excluded.stage,event_hash=excluded.event_hash,state_json=excluded.state_json,committed_at=excluded.committed_at", (run_id, stage, event["event_hash"], json.dumps({"stage": stage, "output_tokens": output_tokens}, sort_keys=True), now))
        return event

    def load_run(self, run_id: str) -> dict[str, Any]:
        row = self.connection.execute("SELECT * FROM runs WHERE run_id=?", (run_id,)).fetchone()
        if not row:
            raise KeyError(run_id)
        integrity = verify_event_chain(self.connection, run_id)
        if integrity["status"] != "PASS":
            raise RuntimeError("controller state tamper detected")
        return {**dict(row), "integrity": integrity}

    def record_reaction_token(self, token: dict[str, Any]) -> None:
        if token.get("run_id") is None or token.get("token_hash") is None:
            raise ValueError("complete reaction token required")
        self.connection.execute(
            "INSERT OR IGNORE INTO reaction_tokens(token_hash,token_type,candidate_id,run_id,producer_event,input_token_hashes,payload_identity,independent_verifier,created_at) VALUES (?,?,?,?,?,?,?,?,?)",
            (token["token_hash"], token["token_type"], token["candidate_id"], token["run_id"], token["producer_event"], json.dumps(token.get("input_token_hashes", [])), token["payload_identity"], token["independent_verifier"], token.get("created_time", token.get("created_at"))),
        )

    def counts(self) -> dict[str, int]:
        rows = self.connection.execute("SELECT repair_class, COUNT(*) AS n FROM count_records WHERE decision='COUNT' GROUP BY repair_class").fetchall()
        values = {str(row["repair_class"]): int(row["n"]) for row in rows}
        return {"issue_derived": values.get("issue_derived", 0), "native_external": values.get("native_external", 0)}

    def record_failed_branch(self, record: dict[str, Any]) -> str:
        required = ("attempt_identity", "parent_event", "input_tokens", "candidate_id", "source_identity",
                    "provider_seal", "operation_identity", "failure_class", "new_information",
                    "rollback_target", "branch_closed", "reopen_condition", "next_legal_action")
        missing = [key for key in required if key not in record]
        if missing:
            raise ValueError(f"failed branch lineage incomplete: {','.join(missing)}")
        payload = {**record, "count_increment": False}
        branch_hash = canonical_hash(payload)
        now = datetime.now(timezone.utc).isoformat()
        self.connection.execute(
            "INSERT OR IGNORE INTO failed_branch_lineage(branch_hash,attempt_identity,parent_event,input_tokens,candidate_id,source_identity,provider_seal,operation_identity,patch_hash,failure_class,new_information,rollback_target,branch_closed,count_increment,reopen_condition,next_legal_action,created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (branch_hash, record["attempt_identity"], record["parent_event"], json.dumps(record["input_tokens"], sort_keys=True),
             record["candidate_id"], record["source_identity"], record["provider_seal"], record["operation_identity"],
             record.get("patch_hash"), record["failure_class"], json.dumps(record["new_information"], sort_keys=True),
             record["rollback_target"], int(bool(record["branch_closed"])), 0, record["reopen_condition"],
             record["next_legal_action"], now),
        )
        self.connection.commit()
        return branch_hash
