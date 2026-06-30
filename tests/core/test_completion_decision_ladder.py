from controllergate.core.target_reachability import EXPLICIT_COMPLETION_OUTCOMES, completion_decision


def test_every_run_ends_in_explicit_completion_outcome() -> None:
    decision = completion_decision(
        target_behavior_reached=False,
        target_passed_after_normalization=False,
        precondition_unresolved=True,
        patch_generated=False,
        target_validation_passed=False,
        duplicate_replay_passed=False,
    )
    assert decision in EXPLICIT_COMPLETION_OUTCOMES


def test_forbidden_evidence_has_explicit_outcome() -> None:
    decision = completion_decision(
        target_behavior_reached=True,
        target_passed_after_normalization=False,
        precondition_unresolved=False,
        patch_generated=False,
        target_validation_passed=False,
        duplicate_replay_passed=False,
        forbidden_evidence_or_file=True,
    )
    assert decision == "blocked_forbidden_evidence_or_file"
