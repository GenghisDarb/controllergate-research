from __future__ import annotations

from controllergate.evaluation.agreement_adjudicator import adjudicate
from controllergate.evaluation.builder_report import build_report
from controllergate.evaluation.independent_critic import recompute_from_raw


def test_builder_and_critic_recompute_matching_coordinates() -> None:
    builder = build_report([{"candidate_id": "c", "provider_verified": True, "duplicate_failure_admitted": False, "repair_counted": False, "exact_blocker": "not_reproduced"}])
    critic = recompute_from_raw([{"candidate_id": "c", "provider_manifest": {"verification_status": "PASS"}, "duplicate_replay": {"status": "BLOCK"}, "count_gate": {"status": "NOT_RUN"}, "exact_blocker": "not_reproduced"}])
    result = adjudicate(builder, critic, builder_source_hash="a", critic_source_hash="b")
    assert result["status"] == "PASS"


def test_same_source_or_hardcoded_coordinates_are_rejected() -> None:
    builder = {"evaluator": "builder", "coordinates": [], "hardcoded_all_pass": True, "report_hash": "x"}
    critic = {"evaluator": "critic", "coordinates": [], "hardcoded_all_pass": False, "report_hash": "y"}
    assert adjudicate(builder, critic, builder_source_hash="same", critic_source_hash="same")["status"] == "BLOCK"


def test_critic_does_not_conflate_reproduction_with_admission() -> None:
    critic = recompute_from_raw([{
        "candidate_id": "c",
        "provider_manifest": {"verification_status": "PASS"},
        "duplicate_replay": {"status": "CANDIDATE_FAILURE_REPRODUCED", "network_denial_verified": False},
        "count_gate": {"status": "NOT_RUN"},
        "exact_blocker": "network_boundary_not_verified",
    }])
    assert critic["coordinates"][0]["duplicate_failure_admitted"] is False
