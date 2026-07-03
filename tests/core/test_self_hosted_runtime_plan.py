from controllergate.core.self_hosted_runtime_plan import self_hosted_runtime_plan


def test_self_hosted_runtime_plan_is_next_safe_action():
    plan = self_hosted_runtime_plan("3.7")
    assert plan["status"] == "PLAN_READY"
    assert plan["next_allowed_action"] == "provide_verified_python37_runtime_provider_or_self_hosted_runner"
    assert any("Python 3.7" in item for item in plan["requirements"])

