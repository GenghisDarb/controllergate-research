from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs" / "post_v2_37_hardening_batch079_count6_runtime_incident_memory_wave1c"


def load(name: str):
    return json.loads((OUT / name).read_text(encoding="utf-8"))


def test_count_six_hardened_without_recount():
    record = load("cognicore_count6_revalidation.json")
    assert record["COUNT_6_HARDENING"] == "COUNT_6_HARDENING_PASS"
    assert record["historical_count"] == 6 and record["count_increment"] == 0 and not record["recounted"]


def test_static_preflight_stops_before_target_execution():
    preflight = load("batch079_incident_static_preflight.json")
    frame = load("batch079_incident_frame_freeze.json")
    assert preflight["target_execution_count"] == 0
    assert frame["frozen_before_target_execution"] and not frame["adaptive_replenishment"]


def test_no_synthetic_null_is_called_executed():
    result = load("batch079_executed_null_results.json")
    assert result["synthetic_replicates"] == 0 and result["executed_replicates"] == 0


def test_claim_boundary_remains_locked():
    final = load("batch079_final_decision.json")
    assert final["issue_derived_repair_count"] == 6
    assert final["native_external_repair_count"] == 4
    assert final["AMDS_PROSPECTIVE_EFFECTIVENESS"] == "NOT_ESTABLISHED"
    assert final["memory_lift"] == "not demonstrated"
    assert final["full_scoring"] == "NOT_RUN/disallowed"
    assert final["self_maintaining_software"] == "false/not demonstrated"
