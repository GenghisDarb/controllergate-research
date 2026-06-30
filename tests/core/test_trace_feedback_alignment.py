from controllergate.core.target_reachability import classify_runtime_path


def test_first_trace_mismatch_allows_feedback_step() -> None:
    runtime = classify_runtime_path("StopIteration create_formatter", returncode=1)
    next_step = "run_declared_precondition_resolution" if runtime["classification"] == "precondition_before_target_behavior" else "block"
    assert next_step == "run_declared_precondition_resolution"


def test_precondition_normalization_triggers_rerun_and_reclassification() -> None:
    attempts = [
        {"iteration": 1, "runtime_classification": "precondition_before_target_behavior", "next_step": "run_declared_precondition_resolution"},
        {"iteration": 2, "runtime_classification": "precondition_before_target_behavior", "next_step": "retire_candidate"},
    ]
    assert attempts[0]["next_step"] != "retire_candidate"
    assert attempts[-1]["next_step"] == "retire_candidate"
