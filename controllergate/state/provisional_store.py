from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Mapping

from controllergate.state.integrity import canonical_hash


class ProvisionalEvidenceStore:
    def __init__(self, path: Path) -> None:
        self.path=path; self.connection=sqlite3.connect(path)
        self.connection.executescript("""
        CREATE TABLE IF NOT EXISTS branches(branch_id TEXT PRIMARY KEY,parent_id TEXT,status TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS facts(fact_id TEXT PRIMARY KEY,branch_id TEXT NOT NULL,payload TEXT NOT NULL,parent_ids TEXT NOT NULL,promoted INTEGER NOT NULL DEFAULT 0);
        CREATE TABLE IF NOT EXISTS checkpoints(checkpoint_id TEXT PRIMARY KEY,branch_id TEXT NOT NULL,state_hash TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS nogoods(nogood_id TEXT PRIMARY KEY,branch_id TEXT NOT NULL,reason TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS nonces(nonce TEXT PRIMARY KEY,spent INTEGER NOT NULL);
        CREATE TABLE IF NOT EXISTS promotions(fact_id TEXT PRIMARY KEY,controller_audit_receipt TEXT NOT NULL,promotion_hash TEXT NOT NULL);
        """); self.connection.commit()

    def create_branch(self, branch_id: str, parent_id: str | None=None) -> None:
        self.connection.execute("INSERT INTO branches VALUES(?,?,?)",(branch_id,parent_id,"ACTIVE")); self.connection.commit()

    def add_fact(self, branch_id: str, payload: Mapping[str, Any], parent_ids: list[str]) -> str:
        fact_id=canonical_hash({"branch_id":branch_id,"payload":dict(payload),"parents":parent_ids})
        self.connection.execute("INSERT INTO facts VALUES(?,?,?,?,0)",(fact_id,branch_id,json.dumps(dict(payload),sort_keys=True),json.dumps(parent_ids))); self.connection.commit(); return fact_id

    def checkpoint(self, branch_id: str) -> str:
        rows=self.connection.execute("SELECT fact_id,payload FROM facts WHERE branch_id=? ORDER BY fact_id",(branch_id,)).fetchall(); value=canonical_hash(rows)
        checkpoint_id=canonical_hash({"branch":branch_id,"state":value}); self.connection.execute("INSERT INTO checkpoints VALUES(?,?,?)",(checkpoint_id,branch_id,value)); self.connection.commit(); return checkpoint_id

    def promote(self, fact_id: str, controller_audit_receipt: str | None) -> str:
        if not controller_audit_receipt: raise ValueError("ControllerAudit receipt required")
        promotion=canonical_hash({"fact":fact_id,"controller_audit_receipt":controller_audit_receipt})
        self.connection.execute("UPDATE facts SET promoted=1 WHERE fact_id=?",(fact_id,)); self.connection.execute("INSERT INTO promotions VALUES(?,?,?)",(fact_id,controller_audit_receipt,promotion)); self.connection.commit(); return promotion

    def export(self) -> dict[str, list[dict[str, Any]]]:
        tables={}
        for name in ("branches","facts","checkpoints","nogoods","nonces","promotions"):
            cursor=self.connection.execute(f"SELECT * FROM {name} ORDER BY 1"); columns=[x[0] for x in cursor.description]; tables[name]=[dict(zip(columns,row)) for row in cursor.fetchall()]
        return tables

    def close(self) -> None: self.connection.close()
