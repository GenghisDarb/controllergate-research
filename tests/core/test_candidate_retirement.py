from controllergate.core.target_reachability import completion_decision


def test_target_passed_after_precondition_resolution_does_not_count_as_repair() -> None:
    decision = completion_decision(
        target_behavior_reached=True,
        target_passed_after_normalization=True,
        precondition_unresolved=False,
        patch_generated=False,
        target_validation_passed=False,
        duplicate_replay_passed=False,
    )
    assert decision == "candidate_retired_precondition_only"


def test_retired_candidate_records_precondition_unresolved() -> None:
    decision = completion_decision(
        target_behavior_reached=False,
        target_passed_after_normalization=False,
        precondition_unresolved=True,
        patch_generated=False,
        target_validation_passed=False,
        duplicate_replay_passed=False,
    )
    assert decision == "candidate_retired_precondition_unresolved"
