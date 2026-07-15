from __future__ import annotations

import json
import re
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .database import connect, initialize, transaction
from .event_store import append_event
from .integrity import canonical_hash, verify_event_chain
from .migrations import migrate
from .lease import acquire as acquire_worker_lease, release as release_worker_lease


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

    def acquire_lease(self, run_id: str, worker_identity: str, ttl_seconds: float = 30.0) -> bool:
        with transaction(self.connection):
            return acquire_worker_lease(self.connection, run_id, worker_identity, ttl_seconds)

    def release_lease(self, run_id: str, worker_identity: str) -> bool:
        with transaction(self.connection):
            return release_worker_lease(self.connection, run_id, worker_identity)

    def authorize(self, run_id: str, authorization_id: str, scope: dict[str, Any], nonce: str) -> dict[str, Any]:
        if not nonce or self.connection.execute("SELECT 1 FROM spent_nonces WHERE nonce=?", (nonce,)).fetchone():
            raise ValueError("authorization nonce missing or already spent")
        with transaction(self.connection):
            self.connection.execute(
                "INSERT INTO authorizations(authorization_id,run_id,scope_json,consumed) VALUES (?,?,?,0)",
                (authorization_id, run_id, json.dumps({**scope, "nonce": nonce}, sort_keys=True)),
            )
        return {"authorization_id": authorization_id, "nonce": nonce, "status": "AUTHORIZED"}

    def consume_authorization(self, run_id: str, authorization_id: str, nonce: str) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with transaction(self.connection):
            row = self.connection.execute(
                "SELECT scope_json,consumed FROM authorizations WHERE authorization_id=? AND run_id=?",
                (authorization_id, run_id),
            ).fetchone()
            if not row or row["consumed"] or json.loads(row["scope_json"]).get("nonce") != nonce:
                raise ValueError("authorization invalid, consumed, or nonce mismatch")
            self.connection.execute("INSERT INTO spent_nonces(nonce,run_id,spent_at) VALUES (?,?,?)", (nonce, run_id, now))
            self.connection.execute("UPDATE authorizations SET consumed=1 WHERE authorization_id=?", (authorization_id,))

    def record_broker_operation(self, run_id: str, record: dict[str, Any]) -> None:
        with transaction(self.connection):
            self.connection.execute(
                "INSERT INTO broker_records(record_hash,run_id,operation_id,stage_id,authorization_id,nonce,record_json,created_at) VALUES (?,?,?,?,?,?,?,?)",
                (record["record_hash"], run_id, record["operation_id"], record["stage_id"], record["authorization_id"],
                 record["nonce"], json.dumps(record, sort_keys=True), datetime.now(timezone.utc).isoformat()),
            )

    def _insert_scoped_evidence(self, run_id: str, scoped: dict[str, Any], now: str) -> None:
        outcome = scoped["outcome"]; assertion = scoped["assertion"]; receipt = scoped["receipt"]
        self.connection.execute("INSERT INTO mechanism_outcomes(outcome_id,run_id,mechanism_id,observed_status,blocker,raw_output_hashes_json,created_at) VALUES (?,?,?,?,?,?,?)", (outcome["outcome_id"], run_id, outcome["mechanism_id"], outcome["observed_status"], outcome.get("blocker"), json.dumps(outcome["raw_output_hashes"], sort_keys=True), now))
        self.connection.execute("INSERT INTO test_assertions(assertion_id,run_id,outcome_id,assertion_status,expected_mechanism_status,created_at) VALUES (?,?,?,?,?,?)", (assertion["assertion_id"], run_id, assertion["outcome_id"], assertion["assertion_status"], assertion["expected_mechanism_status"], now))
        self.connection.execute("INSERT INTO execution_receipts(receipt_id,run_id,producer_component,verifier_identity,execution_depth,mechanism_status,test_assertion_status,receipt_json,created_at) VALUES (?,?,?,?,?,?,?,?,?)", (receipt["receipt_id"], run_id, receipt["producer_component"], receipt["verifier_identity"], receipt["execution_depth"], receipt["mechanism_observed_status"], receipt["test_assertion_status"], json.dumps(receipt, sort_keys=True), now))
        for binding in scoped["bindings"]:
            self.connection.execute("INSERT INTO claim_bindings(claim_id,receipt_id,claim_type,binding_json,created_at) VALUES (?,?,?,?,?)", (binding["claim_id"], receipt["receipt_id"], binding["claim_type"], json.dumps(binding, sort_keys=True), now))

    def commit_stage(self, run_id: str, stage: str, input_tokens: list[str], token: dict[str, Any],
                     output: dict[str, Any], worker: str = "controllergate", scoped_evidence: dict[str, Any] | None = None) -> dict[str, Any]:
        input_identity = canonical_hash(input_tokens)
        event_id = f"{run_id}:{stage}:{input_identity[:16]}"
        existing = self.connection.execute("SELECT * FROM events WHERE event_id=?", (event_id,)).fetchone()
        if existing:
            return {**dict(existing), "idempotent_replay": True}
        now = datetime.now(timezone.utc).isoformat()
        output_hash = canonical_hash(output)
        with transaction(self.connection):
            event = append_event(self.connection, event_id=event_id, run_id=run_id, event_type=stage,
                                 input_token_hashes=input_tokens, output_token_hashes=[token["token_hash"]],
                                 status="PASS", blocker=None, worker_identity=worker)
            self.connection.execute(
                "INSERT INTO reaction_tokens(token_hash,token_type,candidate_id,run_id,producer_event,input_token_hashes,payload_identity,independent_verifier,created_at) VALUES (?,?,?,?,?,?,?,?,?)",
                (token["token_hash"], token["token_type"], token["candidate_id"], token["run_id"], token["producer_event"],
                 json.dumps(token.get("input_token_hashes", [])), token["payload_identity"], token["independent_verifier"],
                 token.get("created_time", now)),
            )
            self.connection.execute(
                "INSERT INTO stage_outputs(event_id,run_id,stage_id,input_identity,output_json,output_hash) VALUES (?,?,?,?,?,?)",
                (event_id, run_id, stage, input_identity, json.dumps(output, sort_keys=True), output_hash),
            )
            contract = {"stage": stage, "producer": token["producer_event"], "verifier": token["independent_verifier"]}
            contract_hash = canonical_hash(contract)
            self.connection.execute("INSERT OR IGNORE INTO reaction_contracts(contract_hash,reaction_type,contract_json,verifier_identity,created_at) VALUES (?,?,?,?,?)", (contract_hash, stage, json.dumps(contract, sort_keys=True), token["independent_verifier"], now))
            execution_hash = canonical_hash([run_id, stage, input_identity, output_hash, token["token_hash"]])
            self.connection.execute("INSERT INTO reaction_executions(execution_hash,run_id,contract_hash,stage,input_hash,output_hash,status,blocker,parent_execution_hash,created_at) VALUES (?,?,?,?,?,?,?,?,?,?)", (execution_hash, run_id, contract_hash, stage, input_identity, output_hash, "PASS", None, None, now))
            fact_hash = canonical_hash([run_id, stage, "verified-stage-output", output_hash])
            self.connection.execute("INSERT OR IGNORE INTO evidence_facts(fact_hash,run_id,subject,predicate,object_json,epistemic_state,decision_time_safe,source_hash,created_at) VALUES (?,?,?,?,?,?,?,?,?)", (fact_hash, run_id, stage, "observed_output", json.dumps(output, sort_keys=True), "VERIFIED", 1, output_hash, now))
            lineage_hash = canonical_hash([run_id, stage, execution_hash])
            self.connection.execute("INSERT OR IGNORE INTO lineage_nodes(node_hash,run_id,node_type,parent_hash,lineage_json,created_at) VALUES (?,?,?,?,?,?)", (lineage_hash, run_id, "stage_transition", None, json.dumps({"stage": stage, "execution_hash": execution_hash}, sort_keys=True), now))
            if scoped_evidence:
                self._insert_scoped_evidence(run_id, scoped_evidence, now)
            self.connection.execute("UPDATE runs SET status=?,updated_at=? WHERE run_id=?", (stage, now, run_id))
            self.connection.execute(
                "INSERT INTO checkpoints(run_id,stage,event_hash,state_json,committed_at) VALUES (?,?,?,?,?) "
                "ON CONFLICT(run_id) DO UPDATE SET stage=excluded.stage,event_hash=excluded.event_hash,state_json=excluded.state_json,committed_at=excluded.committed_at",
                (run_id, stage, event["event_hash"], json.dumps({"stage": stage, "token_hash": token["token_hash"]}, sort_keys=True), now),
            )
        return {**event, "output_hash": output_hash, "idempotent_replay": False}

    def commit_blocked_stage(self, run_id: str, stage: str, output: dict[str, Any], blocker: str,
                             worker: str, scoped_evidence: dict[str, Any]) -> dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat(); output_hash = canonical_hash(output)
        event_id = f"{run_id}:{stage}:blocked:{output_hash[:16]}"
        with transaction(self.connection):
            event = append_event(self.connection, event_id=event_id, run_id=run_id, event_type=stage,
                                 input_token_hashes=[], output_token_hashes=[], status="BLOCK", blocker=blocker,
                                 worker_identity=worker)
            self.connection.execute("INSERT INTO stage_outputs(event_id,run_id,stage_id,input_identity,output_json,output_hash) VALUES (?,?,?,?,?,?)", (event_id, run_id, stage, canonical_hash([]), json.dumps(output, sort_keys=True), output_hash))
            self.connection.execute("INSERT INTO failed_reactions(run_id,event_id,blocker,created_at) VALUES (?,?,?,?)", (run_id, event_id, blocker, now))
            self.connection.execute("INSERT INTO blockers(run_id,blocker,active,created_at) VALUES (?,?,1,?)", (run_id, blocker, now))
            self.connection.execute("INSERT INTO reopen_conditions(run_id,condition_json,satisfied) VALUES (?,?,0)", (run_id, json.dumps({"condition": "new_decision_time_safe_direct_evidence", "blocked_stage": stage}, sort_keys=True)))
            contract = {"stage": stage, "producer": "controllergate.engine._stage_output", "verifier": "controllergate.stage.block_verifier"}
            contract_hash = canonical_hash(contract)
            self.connection.execute("INSERT OR IGNORE INTO reaction_contracts(contract_hash,reaction_type,contract_json,verifier_identity,created_at) VALUES (?,?,?,?,?)", (contract_hash, stage, json.dumps(contract, sort_keys=True), contract["verifier"], now))
            execution_hash = canonical_hash([run_id, stage, output_hash, blocker])
            self.connection.execute("INSERT INTO reaction_executions(execution_hash,run_id,contract_hash,stage,input_hash,output_hash,status,blocker,parent_execution_hash,created_at) VALUES (?,?,?,?,?,?,?,?,?,?)", (execution_hash, run_id, contract_hash, stage, canonical_hash([]), output_hash, "BLOCK", blocker, None, now))
            fact_hash = canonical_hash([run_id, stage, "blocked-stage-output", output_hash])
            self.connection.execute("INSERT OR IGNORE INTO evidence_facts(fact_hash,run_id,subject,predicate,object_json,epistemic_state,decision_time_safe,source_hash,created_at) VALUES (?,?,?,?,?,?,?,?,?)", (fact_hash, run_id, stage, "observed_block", json.dumps({"output": output, "blocker": blocker}, sort_keys=True), "VERIFIED_BLOCK", 1, output_hash, now))
            self._insert_scoped_evidence(run_id, scoped_evidence, now)
            self.connection.execute("UPDATE runs SET status='SAFE_ABSTENTION',blocker=?,terminal=1,updated_at=? WHERE run_id=?", (blocker, now, run_id))
        return event

    def checkpoint(self, run_id: str) -> dict[str, Any] | None:
        row = self.connection.execute("SELECT * FROM checkpoints WHERE run_id=?", (run_id,)).fetchone()
        return dict(row) if row else None

    def tokens(self, run_id: str) -> list[dict[str, Any]]:
        return [dict(row) for row in self.connection.execute("SELECT * FROM reaction_tokens WHERE run_id=? ORDER BY rowid", (run_id,))]

    def record_release_decision(self, decision: dict[str, Any]) -> str:
        parent = self.connection.execute("SELECT decision_hash FROM release_decisions ORDER BY rowid DESC LIMIT 1").fetchone()
        value = {**decision, "parent_hash": str(parent["decision_hash"]) if parent else "0" * 64}
        decision_hash = canonical_hash(value)
        with transaction(self.connection):
            self.connection.execute(
                "INSERT INTO release_decisions(decision_hash,status,package_version,parent_hash,decision_json,created_at) VALUES (?,?,?,?,?,?)",
                (decision_hash, value["status"], value["package_version"], value["parent_hash"],
                 json.dumps(value, sort_keys=True), datetime.now(timezone.utc).isoformat()),
            )
        return decision_hash

    def latest_release_decision(self) -> dict[str, Any] | None:
        row = self.connection.execute("SELECT decision_hash,decision_json FROM release_decisions ORDER BY rowid DESC LIMIT 1").fetchone()
        return {**json.loads(row["decision_json"]), "decision_hash": row["decision_hash"]} if row else None

    def migrate_json_state(self, source: str | Path) -> dict[str, Any]:
        path = Path(source); raw = path.read_bytes(); source_hash = __import__("hashlib").sha256(raw).hexdigest()
        existing = self.connection.execute("SELECT * FROM json_state_migrations WHERE source_hash=?", (source_hash,)).fetchone()
        if existing:
            return {**dict(existing), "status": "PASS", "idempotent": True}
        value = json.loads(raw.decode("utf-8")); run_id = str(value.get("run_id", "")); candidate_id = str(value.get("candidate_id", "migrated-fixture"))
        if not RUN_ID.fullmatch(run_id):
            raise ValueError("JSON fixture state has unsafe or missing run_id")
        if not self.connection.execute("SELECT 1 FROM runs WHERE run_id=?", (run_id,)).fetchone():
            self.create_run(run_id, candidate_id, {"migration_source_hash": source_hash, "read_only_source": str(path.resolve())})
        result_hash = canonical_hash({"source_hash": source_hash, "run_id": run_id})
        with transaction(self.connection):
            self.connection.execute(
                "INSERT INTO json_state_migrations(source_hash,source_path,imported_run_id,result_hash,migrated_at) VALUES (?,?,?,?,?)",
                (source_hash, str(path.resolve()), run_id, result_hash, datetime.now(timezone.utc).isoformat()),
            )
        return {"status": "PASS", "source_hash": source_hash, "imported_run_id": run_id, "result_hash": result_hash, "idempotent": False}

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

    def record_proof_event(self, run_id: str, candidate_id: str, proof_type: str, proof: dict[str, Any], parent_hash: str = "0" * 64) -> str:
        value = {"run_id": run_id, "candidate_id": candidate_id, "proof_type": proof_type, "proof": proof, "parent_hash": parent_hash}
        proof_hash = canonical_hash(value)
        self.connection.execute(
            "INSERT OR IGNORE INTO proof_events(proof_hash,run_id,candidate_id,proof_type,proof_json,parent_hash,created_at) VALUES (?,?,?,?,?,?,?)",
            (proof_hash, run_id, candidate_id, proof_type, json.dumps(proof, sort_keys=True), parent_hash, datetime.now(timezone.utc).isoformat()),
        )
        return proof_hash

    def record_scoped_evidence(self, run_id: str, outcome: dict[str, Any], assertion: dict[str, Any], receipt: dict[str, Any], bindings: list[dict[str, Any]]) -> str:
        now = datetime.now(timezone.utc).isoformat()
        transaction_identity = canonical_hash([run_id, outcome, assertion, receipt, bindings])
        with transaction(self.connection):
            self._insert_scoped_evidence(run_id, {"outcome": outcome, "assertion": assertion, "receipt": receipt, "bindings": bindings}, now)
        return transaction_identity
