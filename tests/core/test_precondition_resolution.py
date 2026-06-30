from controllergate.core.target_reachability import classify_runtime_path


def test_formatter_precondition_is_separate_from_source_bug() -> None:
    result = classify_runtime_path("src/darker/formatters/__init__.py:37 StopIteration create_formatter", returncode=1)
    assert result["classification"] == "precondition_before_target_behavior"
    assert result["failure_before_target_behavior"] is True


def test_dependency_precondition_is_classified_separately() -> None:
    result = classify_runtime_path("ModuleNotFoundError: No module named 'black'", returncode=1)
    assert result["classification"] in {"precondition_before_target_behavior", "environment_dependency_block"}
