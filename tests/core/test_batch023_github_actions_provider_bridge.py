import json
from pathlib import Path


def test_batch023_github_actions_provider_bridge_is_bounded():
    base = Path("outputs/clean_replication_batch_023")
    policy = json.loads((base / "github_actions_provider_bridge_policy.json").read_text(encoding="utf-8"))
    audit = json.loads((base / "github_actions_provider_bridge_audit.json").read_text(encoding="utf-8"))
    assert policy["checkout_persist_credentials_required_false"] is True
    assert policy["provider_workspace_transport_sha256_required"] is True
    assert audit["workflow_provider_bridge_present"] is True
    assert audit["actual_runtime_probe_required"] is True
