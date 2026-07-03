from controllergate.core.containerized_era_runtime import containerized_era_runtime_policy, containerized_workflow_plan


def test_containerized_policy_requires_digest_and_runtime_probe():
    policy = containerized_era_runtime_policy("3.7")
    plan = containerized_workflow_plan("3.7")
    assert policy["container_digest_required"] is True
    assert policy["in_container_python_version_probe_required"] is True
    assert plan["status"] == "PLAN_ONLY"
    assert plan["target_replay_in_current_workflow"] is False

