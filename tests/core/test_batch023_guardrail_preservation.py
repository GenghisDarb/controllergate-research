import json
from pathlib import Path


def test_batch023_guardrails_preserve_order_and_empirical_gates():
    base = Path("outputs/clean_replication_batch_023")
    activation = json.loads((base / "activation_order_guardrail_status.json").read_text(encoding="utf-8"))
    geometry = json.loads((base / "active_search_geometry_execution_trace.json").read_text(encoding="utf-8"))
    coupling = json.loads((base / "claim_boundary_batch023.json").read_text(encoding="utf-8"))
    assert activation["order_preserved"] is True
    assert activation["repair_before_target_intent"] is False
    assert geometry["empirical_evidence_replaced"] is False
    assert coupling["current_protocol"] == "v2.13"
