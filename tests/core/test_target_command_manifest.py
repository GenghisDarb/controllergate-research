from controllergate.core.command_manifest import build_target_command_manifest_summary


def test_command_manifest_ready_without_seed_but_replay_disallowed():
    result = build_target_command_manifest_summary(seed_present=False)

    assert result["status"] == "PASS"
    assert result["target_command_manifest_status"] == "READY_NO_SEED"
    assert result["target_replay_allowed"] is False


def test_command_manifest_requires_explicit_command_when_seed_present():
    result = build_target_command_manifest_summary(seed_present=True)

    assert result["status"] == "BLOCK"
    assert result["blocker"] == "target_command_manifest_malformed"
