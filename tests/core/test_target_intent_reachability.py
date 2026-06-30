from controllergate.core.target_reachability import classify_runtime_path, fragment_generation_authorized


def test_fragment_generation_cannot_run_when_target_intent_not_reached() -> None:
    runtime = classify_runtime_path("create_formatter(args.formatter)\nStopIteration", returncode=1)
    assert runtime["classification"] == "precondition_before_target_behavior"
    assert runtime["target_behavior_reached"] is False
    assert fragment_generation_authorized(runtime["classification"], "PASS") is False


def test_fragment_generation_may_run_after_aligned_target_behavior() -> None:
    runtime = classify_runtime_path("isort skip_glob conf/settings test_isort_respects_skip_glob AssertionError", returncode=1)
    assert runtime["classification"] == "aligned_target_behavior_reached"
    assert fragment_generation_authorized(runtime["classification"], "PASS") is True
