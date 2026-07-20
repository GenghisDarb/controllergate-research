import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs/post_v2_37_hardening_batch101_canonical_semantic_replay_exact_incident_salvage_ownership_closure"


def rows(name):
    return [json.loads(line) for line in (OUT / name).read_text().splitlines() if line.strip()]


def test_complete_cell_accounting_and_raw_custody():
    ledger = rows("batch101_registered_cell_execution_ledger_v1.jsonl")
    assert len(ledger) == 33
    assert sum(row["execution_status"] == "EXECUTED" for row in ledger) == 28
    assert sum(row["execution_status"] == "BLOCKED" for row in ledger) == 5
    assert len(rows("raw_execution_observations_v1.jsonl")) == 56


def test_pybugger_corrected_incident_is_materialized_without_ownership():
    ledger = {row["cell_id"]: row for row in rows("batch101_registered_cell_execution_ledger_v1.jsonl")}
    assert ledger["cell:batch100-py-bugger-65-accounting:all-attempts-succeed"]["predicate_result"] is True
    assert ledger["cell:batch100-py-bugger-65-accounting:subset-attempts-fail"]["predicate_result"] is True
    pair = next(row for row in rows("pair_validity_receipts_v3.jsonl") if row["program_id"] == "batch100-py-bugger-65-accounting")
    assert pair["status"] == "VALID_FACTORIAL_PAIR"
    proof = next(row for row in rows("ownership_support_receipts_v2.jsonl") if row["program_id"] == pair["program_id"])
    assert proof["ownership_supported"] is False


def test_incomplete_factorial_and_missing_incidents_do_not_validate():
    pairs = {row["program_id"]: row for row in rows("pair_validity_receipts_v3.jsonl")}
    assert pairs["batch100-cloudpickle-507-distutils"]["status"] != "VALID_FACTORIAL_PAIR"
    assert pairs["batch100-openbb-7585-topology"]["status"] == "INCIDENT_NOT_EXECUTED"
    assert pairs["batch100-pytest-13480-warning-mode"]["status"] == "INCIDENT_NOT_MATERIALIZED"


def test_all_terminals_safely_abstain_and_claims_are_unchanged():
    terminals = rows("controller_audit_counterfactual_terminal_records_v4.jsonl")
    assert len(terminals) == 9
    assert {row["terminal_class"] for row in terminals} == {"INSUFFICIENT_EVIDENCE"}
    assert all(not row["ownership_supported"] for row in terminals)


def test_mutation_campaign_rejects_all_complete_copied_tree_mutations():
    summary = json.loads((OUT / "critic/batch101_semantic_mutation_campaign_summary.json").read_text())
    assert summary["semantic_mutations_executed"] >= 60
    assert summary["semantic_mutations_rejected"] == summary["semantic_mutations_executed"]
    assert summary["semantic_mutations_accepted"] == 0
