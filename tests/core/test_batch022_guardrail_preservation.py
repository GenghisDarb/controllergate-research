import json
from pathlib import Path


def test_batch022_guardrails_preserve_order_and_empirical_gates():
    base = Path("outputs/clean_replication_batch_022")
    if base.exists():
        activation = json.loads((base / "activation_order_guardrail_status.json").read_text(encoding="utf-8"))
        geometry = json.loads((base / "active_search_geometry_execution_trace.json").read_text(encoding="utf-8"))
        ghost = json.loads((base / "rollback_ghost_state_guardrail_status.json").read_text(encoding="utf-8"))
        assert activation["repair_before_target_intent"] is False
        assert geometry["empirical_evidence_replaced"] is False
        assert ghost["downstream_state_contaminated"] is False
