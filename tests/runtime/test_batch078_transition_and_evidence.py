from __future__ import annotations

import json
from pathlib import Path

from controllergate.core.batch078_count6_minimal_closure_memory_wave1b import ARM_CONDITIONS, BATCH, EXPECTED_PATCH_SHA
from controllergate.runtime.transition_closure_audit import audit_transition_closure


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs" / BATCH


def load(name: str) -> dict:
    return json.loads((OUT / name).read_text(encoding="utf-8"))


def rows(name: str) -> list[dict]:
    return [json.loads(line) for line in (OUT / name).read_text(encoding="utf-8").splitlines() if line]


def test_transition_closure_requires_rollback_inverse() -> None:
    result = audit_transition_closure(
        before={"state": "before", "source": "fixed"},
        after={"state": "after", "source": "fixed"},
        rollback={"state": "wrong", "source": "fixed"},
        expected_changed={"state"},
        expected_unchanged={"source"},
        authorized=True,
        proof_ledger_bound=True,
        compartment_escape=False,
    )
    assert result["status"] == "BLOCK"
    assert result["rollback_inverse"] is False


def test_count_six_identity_is_preserved_without_recount() -> None:
    identity = load("batch077_count6_identity_preservation.json")
    gate = load("cognicore_count6_existing_count_gate.json")
    assert identity["patch_sha256"] == EXPECTED_PATCH_SHA
    assert identity["historical_count"] == 6
    assert gate["existing_count_records"] == 1
    assert gate["count_increment"] == 0


def test_hordeforge_reproduction_and_ownership_are_separate() -> None:
    decision = load("hordeforge_causal_ownership_decision.json")
    assert decision["preserved_reproduction"] == "ORIGINAL_ASSERTION_REPRODUCED"
    assert decision["causal_ownership"] == "fixture_or_harness_owned"
    assert decision["patch_authority"] is False


def test_complete_traversal_is_an_efficiency_confound() -> None:
    reconciliation = load("batch077_complete_traversal_reconciliation.json")
    identifiability = load("batch077_memory_effect_identifiability_audit.json")
    assert reconciliation["arm_count"] == 12
    assert reconciliation["raw_probe_count"] == 96
    assert reconciliation["any_arm_stopped_before_complete_traversal"] is False
    assert set(identifiability["endpoints"].values()) == {"NOT_IDENTIFIABLE_UNDER_COMPLETE_TRAVERSAL"}


def test_calibration_is_leave_one_out_and_real_shuffled_distinct() -> None:
    prereg = load("pathway_memory_calibration_preregistration.json")
    calibration = load("pathway_memory_calibration_metrics.json")
    assert prereg["evaluation"] == "leave_one_episode_out"
    assert prereg["prospective_outcomes_used_for_tuning"] is False
    assert "mean_reciprocal_rank" in calibration
    assert "shuffled_mean_reciprocal_rank" in calibration


def test_proof_hashes_have_one_independence_group() -> None:
    corpus = rows("routing_event_pathway_corpus_v2_1.jsonl")
    groups: dict[str, set[str]] = {}
    for row in corpus:
        groups.setdefault(row["proof_hash"], set()).add(row["episode_independence_group"])
    assert all(len(value) == 1 for value in groups.values())


def test_frame_is_frozen_and_not_replenished() -> None:
    frame = load("batch078_candidate_frame.json")
    freeze = load("batch078_candidate_frame_freeze.json")
    cohort = load("batch078_admitted_cohort_freeze.json")
    assert frame["candidate_count"] == 4
    assert freeze["arm_conditions"] == list(ARM_CONDITIONS)
    assert freeze["no_adaptive_replenishment"] is True
    assert cohort["adaptive_replenishment"] is False


def test_shadow_metric_never_controls_repair_or_count() -> None:
    nss = load("controllergate_nss_nonconflation_statement.json")
    shadow = load("batch078_tld_shadow_nonblocking_audit.json")
    repair = load("batch078_authoritative_repair_decision.json")
    assert nss["same_name_reused"] is False
    assert shadow["patch_authorization_influence"] is False
    assert shadow["repair_count_influence"] is False
    assert repair["memory_repair_content_used"] is False
