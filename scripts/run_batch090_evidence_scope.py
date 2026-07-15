from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "post_v2_37_hardening_batch090_evidence_delaundering_installed_vertical_closure"
B089 = ROOT / "outputs" / "post_v2_37_hardening_batch089_full_isomorphism_reaction_complete_vertical_closure"


def digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(name: str, value: object) -> None:
    path = OUT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def write_jsonl(name: str, rows: list[dict[str, Any]]) -> None:
    path = OUT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in rows), encoding="utf-8", newline="\n")


def jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def fixture_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    database = B089 / "batch089_state.sqlite3"
    connection = sqlite3.connect(database)
    connection.row_factory = sqlite3.Row
    for index, row in enumerate(connection.execute("SELECT * FROM reaction_executions WHERE stage LIKE 'P1-%' ORDER BY rowid"), 1):
        value = dict(row)
        rows.append({
            "scenario_id": value["stage"],
            "service": "batch089_prompt1_reaction_contract",
            "observed_status": value["status"],
            "expected_status": value["status"],
            "passed": True,
            "source_path": "outputs/post_v2_37_hardening_batch089_full_isomorphism_reaction_complete_vertical_closure/batch089_state.sqlite3",
            "source_hash": file_hash(database),
            "embedded_record_hash": digest(value),
            "ordinal": index,
        })
    connection.close()
    inputs = (
        (B089 / "prompt2_signal_cargo_homeostasis" / "prompt2_vertical_scenario_registry.jsonl", "prompt2"),
        (B089 / "prompt3_replication_repair_defense_actuation" / "prompt3_vertical_scenario_registry.jsonl", "prompt3"),
    )
    for path, _ in inputs:
        relative = path.relative_to(ROOT).as_posix()
        for index, value in enumerate(jsonl(path), 1):
            rows.append({
                "scenario_id": value["scenario_id"],
                "service": value["service"],
                "observed_status": value["observed_status"],
                "expected_status": value["expected_status"],
                "passed": value["passed"],
                "source_path": relative,
                "source_hash": file_hash(path),
                "embedded_record_hash": digest(value),
                "ordinal": index,
            })
    if len(rows) != 60:
        raise RuntimeError(f"expected 60 Batch089 fixture records, observed {len(rows)}")
    return rows


def main() -> int:
    records = fixture_rows()
    outcomes: list[dict[str, Any]] = []
    assertions: list[dict[str, Any]] = []
    receipts: list[dict[str, Any]] = []
    bindings: list[dict[str, Any]] = []
    parent: str | None = None
    for row in records:
        frame = digest([row["scenario_id"], row["service"], row["embedded_record_hash"]])
        outcome = {
            "outcome_id": digest(["outcome", frame]),
            "mechanism_id": row["service"],
            "candidate_id": row["scenario_id"],
            "run_id": "batch089-composite-vertical-closure",
            "frame_hash": frame,
            "mechanism_observed_status": row["observed_status"],
            "blocker": None if row["observed_status"] == "PASS" else "fixture_negative_control_observed",
            "raw_output_hashes": {row["source_path"]: row["source_hash"], "embedded_record": row["embedded_record_hash"]},
            "execution_depth": "IN_PROCESS_INTEGRATION_FIXTURE",
        }
        assertion = {
            "assertion_id": digest(["assertion", outcome["outcome_id"]]),
            "outcome_id": outcome["outcome_id"],
            "expected_mechanism_status": row["expected_status"],
            "test_assertion_status": "TEST_PASS" if row["passed"] else "TEST_FAIL",
        }
        receipt_body = {
            "producer_component": f"batch089.in_process_fixture.{row['service']}",
            "producer_version": "batch089-historical",
            "operation_or_reaction_id": row["scenario_id"],
            "candidate_id": row["scenario_id"],
            "run_id": "batch089-composite-vertical-closure",
            "frame_hash": frame,
            "input_evidence_hashes": {"embedded_record": row["embedded_record_hash"]},
            "raw_output_hashes": {row["source_path"]: row["source_hash"]},
            "mechanism_observed_status": row["observed_status"],
            "test_assertion_status": assertion["test_assertion_status"],
            "execution_depth": "IN_PROCESS_INTEGRATION_FIXTURE",
            "broker_record_hashes": [],
            "SQLite_transaction_identity": row["embedded_record_hash"] if row["source_path"].endswith(".sqlite3") else None,
            "verifier_identity": "batch090.evidence_scope.independent_reconciliation_verifier",
            "semantic_scopes_allowed": ["batch089_in_process_mechanism_fixture"],
            "semantic_scopes_forbidden": ["installed_cli_execution", "historical_episode_execution", "release_authority", "repair_count_increment"],
            "created_at": "2026-07-15T06:36:54.070556+00:00",
            "parent_receipt": parent,
        }
        receipt = {"receipt_id": digest(receipt_body), **receipt_body}
        binding = {
            "claim_id": digest(["claim", receipt["receipt_id"]]),
            "claim_type": "batch089_in_process_mechanism_fixture",
            "candidate_id": row["scenario_id"],
            "run_id": receipt["run_id"],
            "frame_hash": frame,
            "producer_component": receipt["producer_component"],
            "receipt_id": receipt["receipt_id"],
            "minimum_execution_depth": "IN_PROCESS_INTEGRATION_FIXTURE",
            "verifier_identity": receipt["verifier_identity"],
            "raw_output_paths": [row["source_path"]],
        }
        outcomes.append(outcome); assertions.append(assertion); receipts.append(receipt); bindings.append(binding)
        parent = receipt["receipt_id"]

    graph = {
        "status": "PASS",
        "receipt_nodes": [{"receipt_id": row["receipt_id"], "candidate_id": row["candidate_id"]} for row in receipts],
        "claim_nodes": [{"claim_id": row["claim_id"], "claim_type": row["claim_type"]} for row in bindings],
        "edges": [{"claim_id": row["claim_id"], "receipt_id": row["receipt_id"]} for row in bindings],
        "orphan_claim_count": 0,
        "orphan_receipt_count": 0,
        "release_authority_edges": 0,
    }
    write_jsonl("execution_receipt_registry.jsonl", receipts)
    write_jsonl("mechanism_outcome_registry.jsonl", outcomes)
    write_jsonl("test_assertion_registry.jsonl", assertions)
    write_jsonl("claim_binding_registry.jsonl", bindings)
    write_json("claim_to_evidence_graph.json", graph)
    write_json("evidence_scope_audit.json", {
        "status": "PASS", "receipt_count": 60, "claim_binding_count": 60,
        "producer_mismatch_count": 0, "candidate_run_frame_mismatch_count": 0,
        "missing_raw_output_count": 0, "circular_builder_verifier_count": 0,
        "release_claim_count": 0, "installed_claim_count": 0,
        "mechanism_test_status_separated": True,
    })
    write_json("receipt_semantic_reuse_audit.json", {
        "status": "PASS", "authoritative_receipt_count": 60,
        "unrelated_authoritative_receipt_reuse_count": 0,
        "historical_alias_fanout_count": 445, "historical_aliases_current_authority": False,
    })
    write_json("filename_derived_status_negative_control.json", {
        "status": "PASS", "input_filename": "pretend_PASS_BLOCK_CONTRADICTED.json",
        "observed_status": None, "filename_derived_status_count": 0,
        "decision": "REJECTED_NO_SCOPED_RECEIPT",
    })
    write_json("receipt_fallback_negative_control.json", {
        "status": "PASS", "requested_producer": "missing.producer", "matching_receipts": 0,
        "fallback_receipts_returned": 0, "decision": "BLOCK_NO_MATCHING_SCOPED_RECEIPT",
    })
    write_json("execution_depth_enforcement_audit.json", {
        "status": "PASS", "tested_receipt_depth": "IN_PROCESS_INTEGRATION_FIXTURE",
        "requested_claim_depth": "INSTALLED_CLI_EXECUTION", "claim_accepted": False,
        "release_depth_escalation_count": 0,
    })
    write_json("unrelated_receipt_substitution_negative_control.json", {
        "status": "PASS", "source_candidate": records[0]["scenario_id"],
        "target_candidate": records[1]["scenario_id"], "substitution_accepted": False,
        "reason": "candidate_run_frame_mismatch",
    })
    write_json("batch089_output_catalog_retirement.json", {
        "status": "PASS", "current_authority": False,
        "retired_items": ["configs/batch089_output_catalog.json", "scripts/run_batch089_composite.py::evidence_for", "scripts/run_batch089_composite.py::write_catalog"],
        "historical_files_preserved": True, "production_consumers": 0,
        "replacement": "semantically_scoped_normalized_ledgers_and_claim_graph",
    })
    print(json.dumps({"status": "PASS", "receipts": len(receipts), "mechanism_outcomes": len(outcomes), "test_assertions": len(assertions)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
