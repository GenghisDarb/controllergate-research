import json
from pathlib import Path


def test_provider_source_materialization_uses_lock_and_no_undeclared_resolution():
    batch = Path("outputs/clean_replication_batch_024")
    policy = json.loads((batch / "manual_lock_environment_materialization_policy.json").read_text(encoding="utf-8"))
    materialization = json.loads((batch / "manual_lock_environment_materialization_log.json").read_text(encoding="utf-8"))
    assert policy["requires_provider_workspace_bridge"] is True
    assert policy["install_source_with_no_deps"] is True
    assert policy["undeclared_dependency_install_allowed"] is False
    if materialization["status"] == "PASS":
        assert materialization["source_install_returncode"] == 0
    else:
        assert materialization["blocker"] is not None
