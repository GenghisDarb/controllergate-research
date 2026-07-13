from __future__ import annotations

from controllergate.core.maintenance_graph_v2 import STATE_ORDER, evaluate_pathway, graph_contract


def test_maintenance_graph_declares_full_order() -> None:
    contract = graph_contract()
    assert [row["state"] for row in contract["states"]] == list(STATE_ORDER)
    assert all(row["state_hash"] for row in contract["states"])


def test_repair_license_cannot_precede_materialization() -> None:
    result = evaluate_pathway("candidate", [STATE_ORDER[0], STATE_ORDER[4]])
    assert result["status"] == "BLOCK"


def test_prefix_pathway_has_exact_next_state() -> None:
    result = evaluate_pathway("candidate", list(STATE_ORDER[:4]))
    assert result["status"] == "PASS"
    assert result["next_legal_state"] == "REPAIR_LICENSE_GRANTED"

