from controllergate.core.environment_lock import source_acquisition_allowed, summarize_source_commit_environment_lock


def test_environment_lock_ready_without_seed_but_does_not_allow_acquisition():
    result = summarize_source_commit_environment_lock(
        source_commit_sha=None,
        environment_lock_source_paths=[],
        seed_present=False,
    )

    assert result["status"] == "PASS"
    assert result["lock_to_source_commit_status"] == "READY_NO_SEED"
    assert source_acquisition_allowed(result) is False


def test_environment_lock_blocks_missing_metadata_after_seed():
    result = summarize_source_commit_environment_lock(
        source_commit_sha="0" * 40,
        environment_lock_source_paths=[],
        seed_present=True,
    )

    assert result["status"] == "BLOCK"
    assert result["blocker"] == "source_commit_environment_lock_missing"
