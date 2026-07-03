from controllergate.core.hosted_runtime_adapter import hosted_runtime_adapter_status


def test_hosted_runtime_adapter_label_alone_is_not_evidence():
    status = hosted_runtime_adapter_status("3.7")
    assert status["status"] == "UNVERIFIED"
    assert status["hosted_runtime_label_allowed_as_evidence"] is False
    assert status["target_replay_allowed"] is False

