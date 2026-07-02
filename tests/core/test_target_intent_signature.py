from controllergate.core.target_intent_signature import evaluate_target_intent, issue112_target_signature


def test_any_failure_is_not_sufficient_for_issue_derived_verification():
    result = evaluate_target_intent("GIT_DIR=.git python -m darker --check src", "Traceback\nValueError: unrelated")
    assert result["status"] == "BLOCK"
    assert result["target_intent_alignment"] is False
    assert issue112_target_signature()["any_failure_sufficient"] is False


def test_expected_positive_issue112_indicators_are_required():
    result = evaluate_target_intent(
        "GIT_DIR=.git python -m darker --check src",
        "Not a git repository\n_git_check_output_lines",
    )
    assert result["status"] == "PASS"
    assert result["target_intent_alignment"] is True


def test_config_loading_typeerror_is_pre_target_failure():
    result = evaluate_target_intent(
        "GIT_DIR=.git python -m darker --check src",
        "TypeError: unsupported operand type(s) for /: 'tuple' and 'str'",
    )
    assert result["blocker"] == "target_intent_precondition_failure"
    assert result["patch_authorized"] is False
