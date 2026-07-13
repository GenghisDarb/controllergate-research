from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs" / "post_v2_37_hardening_batch080_executed_preflight_provider_memory_wave1d"


def load(name: str):
    return json.loads((OUT / name).read_text(encoding="utf-8"))


def jsonl(name: str) -> list[dict]:
    return [json.loads(line) for line in (OUT / name).read_text(encoding="utf-8").splitlines() if line.strip()]


def test_batch080_executed_preflight_funnel_and_freeze_order() -> None:
    rows = jsonl("batch080_static_preflight_records.jsonl")
    funnel = load("batch080_preflight_funnel.json")
    frame = load("batch080_execution_frame_freeze.json")
    assert len(rows) == funnel["registered_leads"] == 20
    assert funnel["source_verification_attempts"] == funnel["source_verification_passes"] == 20
    assert funnel["target_resolution_passes"] == 2
    assert funnel["command_resolution_passes"] == 2
    assert funnel["target_execution_before_frame_freeze"] == 0
    assert funnel["every_lead_has_terminal_record"] is True
    assert frame["frozen_before_target_execution"] is True
    assert frame["adaptive_replenishment"] is False
    assert frame["candidate_count"] == 1
    assert frame["status"] == "BLOCK_MINIMUM_PARTIAL_FRAME_NOT_MET"


def test_batch080_lane_separation_contamination_and_provider_boundary() -> None:
    native = jsonl("batch080_native_target_registry.jsonl")
    issue = jsonl("batch080_issue_reproducer_registry.jsonl")
    preflight = {row["candidate_id"]: row for row in jsonl("batch080_static_preflight_records.jsonl")}
    assert native and all(row.get("lane") == "NATIVE_TARGET_LANE" for row in native)
    assert issue and all(row.get("lane") == "ISSUE_DERIVED_REPRODUCER_LANE" for row in issue)
    contaminated = preflight["incident_pytest_asyncio_1501"]
    assert contaminated["stages"]["contamination"]["status"] == "BLOCK"
    assert contaminated["terminal"]["admitted_to_execution_frame"] is False
    capsules = jsonl("batch080_provider_capsule_registry.jsonl")
    assert all(row["provider_lock_version"] == 3 for row in capsules)
    assert all(row["provider_bytes_committed"] is False for row in capsules)
    assert load("batch080_provider_capsule_sbom.json")["provider_bytes_stored_in_main_artifact"] is False


def test_batch080_historical_diagnostics_and_hordeforge_sentinels() -> None:
    recovery = load("batch080_batch078_recovery_decision.json")
    assert len(recovery["records"]) == 4
    assert recovery["classification"] == "HISTORICAL_RECOVERY_DIAGNOSTICS_ONLY"
    horde = load("batch080_hordeforge_execution_proof.json")
    assert horde["sentinels"]["TARGET_STARTED"] is False
    assert horde["sentinels"]["TARGET_COMPLETED"] is False
    assert horde["result"] in {"CANDIDATE_HARNESS_DEFECT_CONFIRMED", "INFRASTRUCTURE_EXECUTION_FAILED"}
    assert horde["result"] != "CONTROLLERGATE_ADAPTER_DEFECT_FIXED"
    assert load("batch080_hordeforge_execution_decision.json")["target_execution_proven"] is False


def test_batch080_memory_v3_is_historical_and_controls_are_executed() -> None:
    identities = jsonl("pathway_memory_v3_identity_registry.jsonl")
    assert identities
    assert all(row["repository_identity"].startswith("https://github.com/") for row in identities)
    assert all(row["repository_identity"] != row["episode_id"] for row in identities)
    methods = {row["method"] for row in jsonl("pathway_memory_v3_baseline_rankings.jsonl")}
    assert {"real_memory", "no_memory", "uniform_random", "seeded_random", "frequency_only", "shuffled_memory"} <= methods
    shuffled = jsonl("pathway_memory_v3_shuffled_corpus.jsonl")
    assert any(
        row["original_terminal_class_hash"]
        != __import__("hashlib").sha256(row["shuffled_terminal_class"].encode()).hexdigest()
        for row in shuffled
    )
    decision = load("pathway_memory_v3_decision.json")
    assert decision["decision"] == "CALIBRATED_FOR_EXPERIMENTAL_ROUTING"
    assert decision["prospective_memory_outcomes_used"] is False
    assert decision["MEMORY_LIFT_PROVED"] is False


def test_batch080_safe_stop_keeps_downstream_zero_and_claims_bounded() -> None:
    assert load("batch080_admitted_cohort_freeze.json")["candidate_count"] == 0
    assert load("batch080_comparative_arm_execution_summary.json")["executed_arm_count"] == 0
    assert load("batch080_matched_null_results.json")["executed_replicates"] == 0
    assert load("batch080_authoritative_repair_decision.json")["attempts"] == 0
    final = load("batch080_final_decision.json")
    assert final["issue_derived_repair_count"] == 6
    assert final["native_external_repair_count"] == 4
    assert final["AMDS_PROSPECTIVE_EFFECTIVENESS"] == "NOT_ESTABLISHED"
    assert final["memory_lift"] == "not demonstrated"
    assert final["self_maintaining_software"] == "false/not demonstrated"
