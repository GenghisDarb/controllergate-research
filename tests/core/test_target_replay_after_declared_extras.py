from controllergate.core.precondition_resolution import classify_target_replay_after_declared_extras


def test_target_pass_after_declared_extras_is_precondition_only() -> None:
    result = classify_target_replay_after_declared_extras(0, "1 passed in 1.0s")
    assert result["status"] == "target_passed_after_declared_precondition_resolution"
    assert result["target_passed_after_declared_precondition_resolution"] is True


def test_target_failure_after_declared_extras_can_authorize_repair() -> None:
    output = "src/darker/tests/test_main_isort.py::test_isort_respects_skip_glob AssertionError isort skip_glob"
    result = classify_target_replay_after_declared_extras(1, output)
    assert result["status"] == "target_behavior_reached_and_failed"
    assert result["target_behavior_reached"] is True


def test_formatter_import_failure_remains_precondition_block() -> None:
    result = classify_target_replay_after_declared_extras(1, "StopIteration in create_formatter")
    assert result["status"] == "target_precondition_unresolved_after_declared_extras"
