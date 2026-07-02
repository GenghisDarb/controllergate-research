from controllergate.core.target_intent_signature import evaluate_target_intent


def test_precondition_failure_before_target_behavior_blocks_retry():
    result = evaluate_target_intent(
        "GIT_DIR=.git darker --check src",
        "TypeError: unsupported operand type(s) for /: 'tuple' and 'str'\nNot a git repository",
    )
    assert result["status"] == "BLOCK"
    assert result["patch_authorized"] is False


def test_positive_issue112_indicator_is_required_for_retry():
    result = evaluate_target_intent("GIT_DIR=.git darker --check src", "ValueError: unrelated")
    assert result["status"] == "BLOCK"
    assert result["target_intent_alignment"] is False
