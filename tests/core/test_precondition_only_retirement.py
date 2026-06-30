from controllergate.core.precondition_resolution import retirement_decision_after_declared_extras


def test_precondition_only_pass_does_not_count_as_repair_success() -> None:
    result = retirement_decision_after_declared_extras(
        declared_extras_attempted=True,
        target_replay_status="target_passed_after_declared_precondition_resolution",
        repair_attempted=False,
        target_validation_status="NOT_RUN",
        duplicate_replay_status="NOT_RUN",
    )
    assert result["retired"] is True
    assert result["completion_decision"] == "candidate_retired_precondition_only"


def test_validation_and_duplicate_replay_can_record_success() -> None:
    result = retirement_decision_after_declared_extras(
        declared_extras_attempted=True,
        target_replay_status="target_behavior_reached_and_failed",
        repair_attempted=True,
        target_validation_status="PASS",
        duplicate_replay_status="PASS",
    )
    assert result["retired"] is False
    assert result["completion_decision"] == "repair_success"
