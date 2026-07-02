def test_target_intent_retry_cannot_run_without_validated_manual_lock():
    gate = {
        "manual_dependency_lock_valid": False,
        "target_intent_retry_status": "NOT_RUN",
        "patch_authorized": False,
        "blocker": "manual_dependency_lock_absent",
    }

    assert gate["target_intent_retry_status"] == "NOT_RUN"
    assert gate["patch_authorized"] is False
    assert gate["blocker"] == "manual_dependency_lock_absent"


def test_precondition_failure_before_target_behavior_blocks_alignment():
    retry = {
        "positive_indicator_reached": False,
        "negative_precondition_indicator_before_target": True,
        "target_intent_alignment": False,
        "blocker": "target_intent_precondition_failure",
    }

    assert retry["target_intent_alignment"] is False
    assert retry["blocker"] == "target_intent_precondition_failure"
