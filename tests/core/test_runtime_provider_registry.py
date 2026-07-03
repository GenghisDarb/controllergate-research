from controllergate.core.runtime_provider_registry import runtime_provider_registry


def test_registry_requires_exact_runtime_probe():
    registry = runtime_provider_registry("3.7")
    assert registry["status"] == "PASS"
    assert registry["label_only_provider_accepted"] is False
    providers = {item["provider_id"]: item for item in registry["providers"]}
    assert providers["github_actions_setup_python_37"]["exact_runtime_verified"] is False
    assert providers["container_python_37"]["exact_runtime_verified"] is False

