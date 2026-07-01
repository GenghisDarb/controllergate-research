from controllergate.core.targeted_seed import seed_git_tracking_audit


def test_missing_seed_git_tracking_blocks(tmp_path):
    result = seed_git_tracking_audit(tmp_path / "missing.json", workflow_paths=[])

    assert result["status"] == "BLOCK"
    assert result["file_exists"] is False
    assert result["blocker"] == "targeted_prospective_seed_missing_or_invalid_after_locks_ready"
