from controllergate.amds.alternative_exclusion_v2 import ALTERNATIVES, evaluate_alternatives, ownership_support
from controllergate.amds.causal_intervention_v12 import interaction_receipt, necessity_receipt, sufficiency_receipt


def evidence() -> dict:
    return {"incident_materialized": True, "factor_removed": True, "incident_disappeared": True,
            "control_materialized": True, "factor_introduced": True, "incident_appeared": True,
            "held_invariants_stable": True, "semantic_reproducibility": True, "direct_causal_contact": True,
            "independent_verifier": "independent", "fresh_execution": True}


def test_necessity_and_sufficiency_require_all_checks() -> None:
    assert necessity_receipt("p", evidence())["supported"] is True
    assert sufficiency_receipt("p", evidence())["supported"] is True
    broken = evidence(); broken["fresh_execution"] = False
    assert necessity_receipt("p", broken)["supported"] is False
    assert sufficiency_receipt("p", broken)["supported"] is False


def test_interaction_requires_complete_executed_factorial() -> None:
    corners = [{"corner_id": str(i), "executed": True, "reproducible": True, "held_invariants": True} for i in range(4)]
    assert interaction_receipt("p", corners, {"predeclared": True, "non_additive": True})["supported"] is True
    assert interaction_receipt("p", corners[:3], {"predeclared": True, "non_additive": True})["supported"] is False


def test_ownership_is_blocked_until_every_alternative_is_resolved() -> None:
    resolved = evaluate_alternatives([{"alternative": name, "excluded": True, "evidence": ["receipt"]} for name in ALTERNATIVES])
    n, s = necessity_receipt("p", evidence()), sufficiency_receipt("p", evidence())
    assert ownership_support(necessity=n, sufficiency=s, alternatives=resolved, direct_contact=True, fresh_reproducible=True, truth_access_count=0, patch_operation_count=0)["ownership_supported"] is True
    open_set = evaluate_alternatives([])
    assert ownership_support(necessity=n, sufficiency=s, alternatives=open_set, direct_contact=True, fresh_reproducible=True, truth_access_count=0, patch_operation_count=0)["ownership_supported"] is False
