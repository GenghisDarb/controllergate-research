from __future__ import annotations

import json
from pathlib import Path

from controllergate.core.batch075_provider_harness_amds_memory_wave1a import BATCH, REVIEW, REJECTED

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs" / BATCH


def load(name: str) -> dict:
    return json.loads((OUT / name).read_text(encoding="utf-8"))


def test_manual_frame_order_and_exclusion_are_frozen() -> None:
    review = load("batch075_manual_review_decisions.json")
    assert review["candidate_order"] == [item["candidate_id"] for item in REVIEW]
    assert review["rejected"]["candidate_id"] == REJECTED["candidate_id"]
    assert review["rejected"]["executed"] is False
    assert load("batch075_candidate_evidence_firewall.json")["issue_comments_consumed"] is False


def test_duplicate_admission_precedes_cohort_and_arms() -> None:
    admitted = []
    for slug in ("cognicore", "hordeforge"):
        decision = load(f"{slug}_admission_decision.json")
        assert decision["status"] in {
            "ADMITTED_DUPLICATE_FAILURE", "FAILURE_NOT_REPRODUCED", "PROVIDER_BLOCKED",
            "TARGET_BLOCKED", "COMMAND_BLOCKED", "ENVIRONMENT_ONLY_TERMINAL", "CONTAMINATION_BLOCKED",
        }
        if decision["status"] == "ADMITTED_DUPLICATE_FAILURE":
            assert decision["duplicate_collection"] and decision["duplicate_failure"]
            admitted.append(decision["candidate_id"])
    cohort = load("batch075_admitted_cohort_freeze.json")
    assert cohort["frozen_after_all_dispositions"] and cohort["diagnostics_started_after_freeze"]
    assert cohort["candidate_count"] == len(admitted)
    assert cohort["candidates"] == admitted


def test_diagnostic_arms_are_isolated_and_patch_free() -> None:
    diagnostics = load("batch075_diagnostic_arm_summary.json")
    arms = [arm for record in diagnostics["records"] for arm in record["arm_outputs"].values()]
    assert len(arms) == diagnostics["candidate_count"] * 4
    assert len({arm["authorization_store_path"] for arm in arms}) == len(arms)
    assert len({arm["checkpoint_path"] for arm in arms}) == len(arms)
    assert len({arm["posterior_store"] for arm in arms}) == len(arms)
    assert all(not arm["observation_sharing"] and not arm["patch_authority"] for arm in arms)
    assert all(arm["canonical_run_amds_active_loop"] for arm in arms if arm["strategy"] == "AMDS_ACTIVE")
    assert all(not arm["canonical_run_amds_active_loop"] for arm in arms if arm["strategy"] == "FIXED_LEGAL_ORDER")


def test_memory_contract_changes_routing_only_and_claims_remain_bounded() -> None:
    diagnostics = load("batch075_diagnostic_arm_summary.json")
    for record in diagnostics["records"]:
        enabled = record["arm_outputs"]["amds_active_memory_enabled"]
        disabled = record["arm_outputs"]["amds_active_memory_disabled"]
        assert enabled["memory_influence"] == "MEMORY_CHANGED_PROBE_ORDER"
        assert disabled["memory_influence"] == "NO_OBSERVED_MEMORY_INFLUENCE"
        assert set(enabled["probe_order"]) == set(disabled["probe_order"])
    final = load("batch075_final_decision.json")
    assert final["AMDS_PROSPECTIVE_EFFECTIVENESS"] == "NOT_ESTABLISHED"
    assert final["memory_lift"] == "not_demonstrated"
    assert final["issue_derived_repair_count"] == 5
    assert final["native_external_repair_count"] == 4


def test_fourteen_contacts_are_real_record_hashes() -> None:
    evidence = load("batch075_fourteen_contact_evidence.json")
    admitted_count = load("batch075_admitted_cohort_freeze.json")["candidate_count"]
    assert evidence["status"] == ("PASS" if admitted_count else "NOT_RUN_EXECUTED_EMPTY_COHORT")
    assert len(evidence["records"]) == admitted_count
    for record in evidence["records"]:
        assert len(record["contacts"]) == 14
        assert all(item["record_present"] and not item["boolean_only_hash"] and len(item["evidence_record_hash"]) == 64 for item in record["contacts"])


def test_ground_truth_is_blinded_before_repair_decision() -> None:
    ground = load("batch075_blinded_ground_truth.json")
    assert ground["arm_outputs_sealed_first"] and ground["adjudicator_blinded"]
    assert all(item["strategy_identity_available"] is False for item in ground["records"])
    repair = load("batch075_authoritative_repair_decision.json")
    assert repair["attempts"] == 0 and repair["successes"] == 0
    assert repair["memory_disabled_lane"] is True
