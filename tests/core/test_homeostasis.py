from __future__ import annotations

from controllergate.core.homeostasis import evaluate_homeostasis_state, evaluate_risk_channel


def test_homeostasis_pass_and_block():
    assert evaluate_risk_channel("candidate_starvation_pressure", 0)["status"] == "PASS"
    assert evaluate_risk_channel("candidate_starvation_pressure", 10)["blocker"] == "candidate_starvation_threshold_reached"

    state = evaluate_homeostasis_state({"evidence_contamination_pressure": 1})
    assert state["status"] == "BLOCK"
    assert "evidence_contamination_pressure_exceeded" in state["blockers"]
