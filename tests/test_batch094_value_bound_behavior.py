from __future__ import annotations

from controllergate.isomorphism.behavior import CONFUSION_PAIRS, behavioral_evidence, execute_behavior, typed_contract
from controllergate.isomorphism.primitives import GENERIC_PRIMITIVES
from controllergate.isomorphism.runtime import execute_structured_scenario


def test_all_primitives_have_typed_behavioral_contracts() -> None:
    evidence = behavioral_evidence()
    assert len(evidence["contracts"]) == len(GENERIC_PRIMITIVES) == 46
    assert evidence["coverage"]["status"] == "PASS"
    assert evidence["coverage"]["effect_key_only_authority_count"] == 0
    for row in evidence["contracts"]:
        assert row["typed_state_schema"]
        assert row["typed_event_schema"]
        assert row["transition_relation"]
        assert row["positive_test_vectors"]
        assert row["negative_test_vectors"]
        assert row["adversarial_test_vectors"]


def test_confusion_pairs_use_shared_domain_semantics() -> None:
    evidence = behavioral_evidence()
    assert len(evidence["confusion_pairs"]) == len(CONFUSION_PAIRS) == 16
    assert all(row["status"] == "PASS" for row in evidence["confusion_pairs"])
    assert all(row["effect_key_used_as_decision_basis"] is False for row in evidence["confusion_pairs"])


def test_adversarial_authority_escalation_blocks() -> None:
    contract = typed_contract("ACTUATOR")
    event = contract["adversarial_test_vectors"][0]
    result = execute_behavior("ACTUATOR", {"primitive_trace": [], "authority": "shadow_non_authorizing"}, event)
    assert result["status"] == "BLOCK"
    assert result["blocker"] == "unauthorized_authority_escalation"


def test_canonical_executor_and_independent_verifier_both_execute(tmp_path) -> None:
    source_event = {
        "source_occurrence_identity": "unit-source-bound",
        "event_type": "Reaction",
        "entity_state": [{"database_id": 1, "role": "input"}],
    }
    scenario = {
        "scenario_id": "unit-value-bound",
        "source_stable_id": "R-HSA-1",
        "source_occurrence_identity": "unit-source-bound",
        "source_graph_hash": "a" * 64,
        "primitive_ids": ["EVENT_CONTRACT", "ENTITY_STATE"],
        "source_event": source_event,
    }
    result = execute_structured_scenario(scenario, tmp_path / "state.sqlite3", platform="unit")
    assert result["status"] == "PASS"
    assert result["stage_execution_receipt"]["producer_executed"] is True
    assert result["stage_verification_receipt"]["verifier_executed"] is True
    assert result["canonical_stage_shortcut_negative_control"]["status"] == "PASS"
