from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs/post_v2_37_hardening_batch094_value_bound_rpir_fresh_amds_cohort_historical_closure"


def load(name: str) -> dict:
    return json.loads((OUT / name).read_text(encoding="utf-8"))


def test_frozen_cohort_blocks_without_substitution() -> None:
    cohort = load("historical_frozen_cohort_v2.json")
    assert cohort["status"] == "BLOCK"
    assert cohort["blocker"] == "BLOCK_MINIMUM_COHORT_NOT_MET"
    assert cohort["frozen_candidate_count"] == 8
    assert cohort["materialized_candidate_count"] < 8
    assert cohort["replacement_count"] == 0
    assert cohort["patch_operation_count"] == 0


def test_role_and_amds_gates_do_not_fabricate_receipts() -> None:
    role = load("role_measurement_quality_gate_v2.json")
    amds = load("amds_historical_quality_gate_v3.json")
    assert role["executed_role_receipt_count"] == 0
    assert role["amds_probe_execution_allowed"] is False
    assert amds["probe_count"] == 0
    assert not (OUT / "role_measurement_execution_receipts_v2.jsonl").exists()
    assert not (OUT / "amds_decision_frames_v3.jsonl").exists()


def test_human_authorization_is_not_active_first_blocker() -> None:
    gate = load("external_human_authorization_gate.json")
    assert gate["status"] == "HUMAN_AUTHORIZATION_BLOCKED_EXACT"
    assert gate["active_first_blocker"] is False
    assert gate["upstream_first_blocker"] == "BLOCK_MINIMUM_COHORT_NOT_MET"
    assert gate["run_historical_actuation"] is False


def test_no_downstream_actuation_or_count() -> None:
    gate = load("batch094_downstream_gate_status.json")
    assert gate["historical_lifecycles"] == "NOT_RUN"
    assert gate["deployment"] == "NOT_RUN"
    assert gate["patch_operation_count"] == 0
    assert gate["historical_count_increment"] == 0
