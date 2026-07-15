from __future__ import annotations

import json
from pathlib import Path

import pytest

from controllergate.execution.stage_registry import STAGE_REGISTRY, registered_stage


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "post_v2_37_hardening_batch090_evidence_delaundering_installed_vertical_closure"


def load(name: str) -> dict:
    return json.loads((OUT / name).read_text(encoding="utf-8"))


def lines(name: str) -> list[dict]:
    return [json.loads(line) for line in (OUT / name).read_text(encoding="utf-8").splitlines() if line]


def test_stage_registry_is_explicit_complete_and_independent() -> None:
    matrix = load("stage_executor_verifier_matrix.json")
    assert len(STAGE_REGISTRY) == matrix["stage_count"] == 25
    assert matrix["status"] == "PASS"
    assert all(row["complete"] and row["independent"] for row in matrix["rows"])
    with pytest.raises(ValueError):
        registered_stage("not-registered")


def test_default_stage_success_removed() -> None:
    audit = load("no_default_stage_success_audit.json")
    assert audit["status"] == "PASS"
    assert audit["default_success_stage_count"] == 0
    assert audit["stage_output_initial_state"] == {"status": "BLOCK", "verified": False}


def test_concrete_tokens_resolve_and_spent_license_is_rejected() -> None:
    source = load("source_ownership_proof_resolution.json")
    license_record = load("repair_license_proof_resolution.json")
    assert source["status"] == "PASS" and source["required"] == source["resolved"] == 12
    assert license_record["status"] == "PASS" and license_record["required"] == license_record["resolved"] == 19
    assert license_record["single_use"] and license_record["consumed"]
    assert load("generic_requirement_hash_negative_control.json")["generic_hash_accepted"] is False
    assert load("spent_token_reuse_negative_control.json")["reuse_accepted"] is False


def test_sqlite_is_operational_authority_not_schema_claim() -> None:
    population = load("sqlite_operational_population_audit.json")
    atomic = load("sqlite_atomic_transition_audit.json")
    empty = load("sqlite_empty_table_claim_negative_control.json")
    assert population["status"] == "PASS" and population["schema_version"] == 6
    assert not population["missing_operational_tables"]
    assert atomic["status"] == "PASS" and "mechanism_outcome" in atomic["atomic_bundle"]
    assert empty["row_count"] == 0 and empty["operational_claim_accepted"] is False


def test_installed_windows_wheel_has_no_repository_or_editable_leakage() -> None:
    identity = load("installed_wheel_identity_windows.json")
    assert identity["status"] == "PASS" and identity["scenario_pass_count"] == 6
    assert identity["repository_import_leakage_count"] == 0
    assert identity["editable_install"] is False
    assert "site-packages" in identity["import_root"].lower()


def test_installed_mechanism_scenarios_and_negative_control() -> None:
    trace = lines("installed_cli_vertical_trace_windows.jsonl")
    assert [row["scenario_id"] for row in trace] == [
        "plan_maturation_brokered_read", "unregistered_raw_plan_blocked",
        "exactly_once_transport_lost_ack_retry", "contradiction_rollback_alternate_probe",
        "single_use_local_actuation", "exact_local_rollback_cleanup",
    ]
    assert all(row["status"] == "PASS" and row["execution_depth"] == "INSTALLED_CLI_EXECUTION" for row in trace)
    negative = trace[1]
    assert negative["mechanism_result"]["status"] == "SAFE_ABSTENTION"
    assert negative["mechanism_outcomes"][-1]["observed_status"] == "BLOCK"
    assert negative["test_assertions"][-1]["assertion_status"] == "TEST_PASS"
    assert trace[-1]["cleanup_receipts"]
