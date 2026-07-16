from __future__ import annotations

import json
from pathlib import Path

from controllergate.amds.role_measurement import ROLE_CONTRACTS, measure_role, verify_role_measurement


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "outputs/post_v2_37_hardening_batch093_structured_rpir_executable_isomorphism_amds_role_cohort_closure"


def _json(name: str) -> dict:
    return json.loads((OUTPUT / name).read_text(encoding="utf-8"))


def test_role_measurement_requires_fresh_semantic_fields() -> None:
    role = "source_revision"
    stale = measure_role("candidate", role, {key: f"value-{key}" for key in ROLE_CONTRACTS[role]})
    assert stale["status"] == "BLOCK"
    assert stale["blocker"] == "fresh_batch093_role_measurement_missing"
    raw = {key: f"value-{key}" for key in ROLE_CONTRACTS[role]}
    raw["fresh_batch093_measurement"] = True
    receipt = measure_role("candidate", role, raw)
    checked = verify_role_measurement(receipt)
    assert receipt["status"] == checked["status"] == "PASS"
    assert checked["producer_identity"] != checked["verifier_identity"]


def test_forbidden_outcome_evidence_blocks_role_measurement() -> None:
    role = "incident_snapshot"
    raw = {key: f"value-{key}" for key in ROLE_CONTRACTS[role]}
    raw.update({"fresh_batch093_measurement": True, "post_repair": True})
    receipt = measure_role("candidate", role, raw)
    assert receipt["status"] == "BLOCK"
    assert receipt["blocker"] == "future_or_outcome_evidence_detected"


def test_frozen_cohort_blocks_before_probes_without_fabrication() -> None:
    gate = _json("role_measurement_quality_gate.json")
    quality = _json("amds_historical_quality_gate_v2.json")
    downstream = _json("batch093_downstream_gate_status.json")
    assert gate["status"] == "BLOCK"
    assert gate["blocker"] == "BLOCK_MINIMUM_COHORT_NOT_MET"
    assert gate["frozen_candidate_count"] == 8
    assert gate["probe_execution_count"] == 0
    assert quality["executed_episode_count"] == 0
    assert downstream["historical_count_increment"] == 0
    assert downstream["patch_operation_count"] == 0


def test_external_human_authorization_is_not_synthesized() -> None:
    result = _json("external_human_authorization_receipt.json")
    assert result["status"] == "HUMAN_AUTHORIZATION_BLOCKED_EXACT"
    assert result["repository_generated_approval"] is False
    assert result["patch_actuation_allowed"] is False
