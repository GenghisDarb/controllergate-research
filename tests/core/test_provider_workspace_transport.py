from pathlib import Path

from controllergate.core.provider_workspace_transport import cleanup_provider_workspace, create_provider_workspace


def test_provider_workspace_transport_records_cleanup_requirement():
    workspace = create_provider_workspace(Path.cwd())
    try:
        assert workspace["status"] == "PASS"
        assert workspace["outside_live_repo"] is True
        assert "OneDrive".lower() not in workspace["workspace_path"].lower()
    finally:
        cleanup = cleanup_provider_workspace(workspace["workspace_path"])
    assert cleanup["status"] == "PASS"
    assert cleanup["removed"] is True
