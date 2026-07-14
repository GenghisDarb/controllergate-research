from pathlib import Path

from controllergate.connectors.local_write_sandbox import execute_local_write_sandbox


def test_controlled_write_connector_never_mutates_public_remote(tmp_path: Path):
    result = execute_local_write_sandbox(tmp_path)
    assert result["status"] == "CONTROLLED_WRITE_CONNECTOR_FIXTURE_PASS"
    assert result["public_remote_mutation"] is False
    assert result["credentials_used"] is False
    assert result["live_write_connector_active"] is False
    assert {row["operation"] for row in result["operations"]} >= {"reject_unauthorized_branch", "reject_unapproved_path", "rollback_branch"}
