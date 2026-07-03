from controllergate.core.docker_runtime_provider import container_security_policy, docker_runtime_provider_policy


def test_docker_runtime_provider_policy_requires_actual_python_probe():
    policy = docker_runtime_provider_policy("3.7")
    assert policy["status"] == "PASS"
    assert policy["actual_python_version_probe_required"] is True
    assert policy["image_label_only_allowed"] is False
    assert policy["external_source_write_credentials_allowed"] is False
    assert container_security_policy()["secrets_exposed_to_external_source"] is False
