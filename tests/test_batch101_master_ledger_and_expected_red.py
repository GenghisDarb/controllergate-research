from __future__ import annotations

import json
from pathlib import Path


LEDGER = Path("configs/controllergate_master_completion_ledger_v2.json")
OUT = Path("outputs/post_v2_37_hardening_batch101_canonical_semantic_replay_exact_incident_salvage_ownership_closure")


def test_official_batch100_ingest_goal_is_complete() -> None:
    data = json.loads(LEDGER.read_text(encoding="utf-8"))
    goals = {row["goal_id"]: row for row in data["goals"]}
    goal = goals["CG-GOAL-021-OFFICIAL-BATCH100-INGEST"]
    assert goal["status"] == "COMPLETE"
    assert goal["completion_commit"] == "ffb74368beeb0b4e85b1bf0288d91f9a0a169a97"
    assert len(goal["current_evidence"]) == 6
    assert all(len(value) == 64 for value in goal["evidence_hashes"].values())


def test_inherited_goal_transitions_preserve_previous_status() -> None:
    data = json.loads(LEDGER.read_text(encoding="utf-8"))
    transitions = [row for row in data["supersession_receipts"] if row.get("transition_id", "").startswith("batch101:")]
    assert len(transitions) == 8
    assert all(row["previous_status"] and row["new_status"] for row in transitions)
    assert all(row["evidence_paths"] and row["evidence_sha256s"] for row in transitions)


def test_expected_red_has_all_40_bound_findings() -> None:
    path = OUT / "batch101_pre_exact_incident_salvage_expected_failure.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["status"] == "BATCH101_PRE_EXACT_INCIDENT_SALVAGE_FAIL_EXPECTED"
    assert data["finding_count"] == 40
    required = {"commit", "path", "symbol", "line_range", "risk", "observed_batch100_evidence", "required_correction", "red_to_green_test"}
    assert all(required <= row.keys() for row in data["findings"])
