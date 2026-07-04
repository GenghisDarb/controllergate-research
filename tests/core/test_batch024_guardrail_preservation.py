import json
from pathlib import Path


def test_batch024_guardrails_preserved():
    batch = Path("outputs/clean_replication_batch_024")
    geometry = json.loads((batch / "active_search_geometry_execution_trace.json").read_text(encoding="utf-8"))
    curvature = json.loads((batch / "curvature_claim_boundary.json").read_text(encoding="utf-8"))
    interlock = json.loads((batch / "consolidated_state_clean_replication_batch_024.json").read_text(encoding="utf-8"))
    assert geometry["empirical_evidence_replaced"] is False
    assert curvature["curvature_can_replace_evidence"] is False
    assert interlock["coupled_interlock_extension_status"] == "BLOCK"
