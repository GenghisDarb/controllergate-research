from __future__ import annotations

from controllergate.amds.causal_closure_contract import evaluate_causal_closure
from controllergate.amds.early_stop_verifier import verify_early_stop
from controllergate.amds.mandatory_invariant_interlock import MANDATORY_INVARIANTS
from controllergate.amds.probe_cost_model import calculate_probe_cost, select_cost_sensitive_probe


def invariant_states() -> dict[str, str]:
    return {name: "PASS" for name in MANDATORY_INVARIANTS}


def test_memory_cannot_waive_mandatory_invariant() -> None:
    states = invariant_states()
    states.pop("source_identity")
    closure = evaluate_causal_closure(
        "insufficient_evidence",
        invariant_states=states,
        resolved_edges={"unresolved_edges_can_change_legal_action"},
        memory_condition="REAL_MEMORY",
    )
    assert closure["status"] == "OPEN"
    assert closure["mandatory_invariant_interlock"]["memory_can_waive"] is False
    assert "source_identity" in closure["mandatory_invariant_interlock"]["missing"]


def test_source_ownership_requires_every_specific_edge() -> None:
    closure = evaluate_causal_closure(
        "source_owned_behavior_defect",
        invariant_states=invariant_states(),
        resolved_edges={
            "candidate_failure_reproduced",
            "candidate_source_causal_frame_or_output_divergence",
            "provider_environment_alternative_excluded",
            "test_expectation_checked",
        },
        excluded_alternatives={"environment_owned", "provider_owned", "harness_owned"},
    )
    assert closure["status"] == "OPEN"
    assert closure["missing_required_edges"] == ["source_locality_established"]


def test_safe_abstention_can_close_with_optional_edges_unresolved() -> None:
    closure = evaluate_causal_closure(
        "insufficient_evidence",
        invariant_states=invariant_states(),
        resolved_edges={"unresolved_edges_can_change_legal_action"},
        optional_edges={"provider_rebuild", "source_locality"},
        memory_condition="NO_MEMORY",
    )
    verifier = verify_early_stop(closure, verifier_identity="independent-test-verifier")
    assert closure["status"] == "PASS"
    assert closure["terminal_action"] == "safe_abstention"
    assert closure["optional_edges_unresolved"] == ["provider_rebuild", "source_locality"]
    assert verifier["status"] == "PASS"


def test_cost_sensitive_probe_selection_uses_gain_per_cost() -> None:
    cheap = calculate_probe_cost({"wall_time": 0.1}, evidence_value=0.8)
    expensive = calculate_probe_cost({"wall_time": 1.0, "provider_rebuild_requirement": 1}, evidence_value=1.0)
    result = select_cost_sensitive_probe(
        [
            {"probe_id": "expensive", "cost_dimensions": {"wall_time": 1.0, "provider_rebuild_requirement": 1}, "evidence_value": 1.0},
            {"probe_id": "cheap", "cost_dimensions": {"wall_time": 0.1}, "evidence_value": 0.8},
        ]
    )
    assert cheap["expected_causal_closure_gain_per_unit_cost"] > expensive["expected_causal_closure_gain_per_unit_cost"]
    assert result["selected_probe"]["probe_id"] == "cheap"
    assert result["probe_count_is_not_sole_objective"] is True
