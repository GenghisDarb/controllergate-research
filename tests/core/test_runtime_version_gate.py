from controllergate.core.dynamic_era_materialization import runtime_version_gate_audit, runtime_version_gate_policy


def test_runtime_version_gate_blocks_host_mismatch():
    policy = runtime_version_gate_policy("3.7")
    assert policy["exact_family_match_required"] is True
    audit = runtime_version_gate_audit(
        {
            "status": "BLOCK",
            "selected_provider_id": "self_hosted_python37_plan",
            "blocker": "runtime_provider_exact_version_unavailable",
            "target_replay_allowed": False,
        },
        "3.10.14",
        "3.7",
    )
    assert audit["status"] == "BLOCK"
    assert audit["host_matches_required_family"] is False
    assert audit["target_replay_allowed"] is False

