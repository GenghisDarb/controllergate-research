from controllergate.core.memory_policy import evaluate_retrospective_memory_claim, prospective_memory_lift_requirement


def test_retrospective_calibration_cannot_claim_prospective_memory_lift():
    result = evaluate_retrospective_memory_claim(score=1.0, routing_delta_detected=True, retrospective=True)
    assert result["retrospective_single_candidate_memory_separation_diagnostic"] is True
    assert result["prospective_memory_lift_status"] == "not_demonstrated"
    assert result["full_memory_lift_claimed"] is False


def test_retrospective_calibration_cannot_increment_repair_episode_count():
    requirement = prospective_memory_lift_requirement()
    assert requirement["fresh_candidate_required"] is True
    assert requirement["matched_null_rules_pre_registered_before_successful_patch"] is True
    assert requirement["full_memory_lift_claim_allowed"] is False
