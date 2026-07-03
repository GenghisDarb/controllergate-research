from controllergate.core.dynamic_era_materialization import (
    dynamic_era_materialization_policy,
    dynamic_era_materialization_status,
    runtime_version_gate_audit,
)


def test_dynamic_era_policy_does_not_loosen_lock():
    policy = dynamic_era_materialization_policy()
    assert policy["status"] == "PASS"
    assert policy["must_not_loosen_python_version"] is True
    assert policy["provider_verification_required_before_replay"] is True


def test_dynamic_era_blocks_when_provider_not_verified():
    selection = {
        "status": "BLOCK",
        "selected_provider_id": "self_hosted_python37_plan",
        "blocker": "runtime_provider_exact_version_unavailable",
        "target_replay_allowed": False,
    }
    version_gate = runtime_version_gate_audit(selection, "3.10.0", "3.7")
    status = dynamic_era_materialization_status(selection, version_gate)
    assert version_gate["status"] == "BLOCK"
    assert status["status"] == "BLOCK"
    assert status["target_replay_allowed"] is False

