import json
from pathlib import Path


def test_batch023_provider_credentials_are_not_exposed():
    audit = json.loads(Path("outputs/clean_replication_batch_023/provider_credentials_isolation_audit.json").read_text(encoding="utf-8"))
    assert audit["github_token_passed_to_provider"] is False
    assert audit["write_credentials_passed_to_provider"] is False
    assert audit["secrets_exposed_to_external_source"] is False
