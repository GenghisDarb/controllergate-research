from controllergate.runtime.dependency_drift_chaperone import classify_dependency_drift


def test_dependency_drift_is_classified_before_code_repair():
    result = classify_dependency_drift({"pytest": "8.0"}, {"pytest": "7.4"})
    assert result["classification"] == "likely_environment_drift"
    assert result["restore_environment_before_code_repair"] is True
    assert result["undeclared_dependency_install_allowed"] is False
