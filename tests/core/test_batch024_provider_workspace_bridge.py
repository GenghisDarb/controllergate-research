import json
from pathlib import Path


BATCH024 = Path("outputs/clean_replication_batch_024")


def test_batch024_provider_workspace_bridge_boundary():
    state = json.loads((BATCH024 / "consolidated_state_clean_replication_batch_024.json").read_text(encoding="utf-8"))
    bridge = json.loads((BATCH024 / "provider_workspace_bridge_status.json").read_text(encoding="utf-8"))
    assert state["provider_workspace_bridge_status"] in {"PASS", "BLOCK"}
    assert bridge["input_bundle_status"] == "PASS"
    assert bridge["output_bundle_status"] == "PASS"
    assert state["full_scoring"] == "NOT_RUN/disallowed"
