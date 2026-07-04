import json
from pathlib import Path


def test_batch023_provider_output_transport_is_hashed_when_run():
    audit = json.loads(Path("outputs/clean_replication_batch_023/provider_workspace_transport_audit.json").read_text(encoding="utf-8"))
    if audit["status"] == "PASS":
        assert len(audit["output_sha256"]) == 64
        assert audit["provider_output_transport_verified"] is True
    else:
        assert audit["provider_output_transport_verified"] is False
