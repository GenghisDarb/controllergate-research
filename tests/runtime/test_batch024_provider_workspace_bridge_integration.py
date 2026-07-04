import json
from pathlib import Path


def test_batch024_runtime_boundary_records_provider_cleanup():
    state = json.loads(Path("outputs/clean_replication_batch_024/consolidated_state_clean_replication_batch_024.json").read_text(encoding="utf-8"))
    cleanup = json.loads(Path("outputs/clean_replication_batch_024/provider_workspace_cleanup_audit.json").read_text(encoding="utf-8"))
    assert state["provider_workspace_cleanup_status"] == "PASS"
    assert cleanup["removed"] is True
