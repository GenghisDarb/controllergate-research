from controllergate.core.matched_null import null_ensemble_success_rate, retrospective_matched_null_calibration_score


def test_score_is_zero_when_null_ensemble_success_rate_is_one():
    result = retrospective_matched_null_calibration_score(
        quarantine_passed=True,
        arms_comparable=True,
        arm_a_succeeded=True,
        null_success_rate=1.0,
        routing_delta_detected=True,
    )
    assert result["matched_null_ensemble_separation_score"] == 0.0


def test_score_is_zero_when_memory_routing_delta_is_passive():
    result = retrospective_matched_null_calibration_score(
        quarantine_passed=True,
        arms_comparable=True,
        arm_a_succeeded=True,
        null_success_rate=0.0,
        routing_delta_detected=False,
    )
    assert result["matched_null_ensemble_separation_score"] == 0.0
    assert result["retrospective_single_candidate_memory_separation_diagnostic"] is False


def test_patch_quarantine_failure_prevents_score_computation():
    result = retrospective_matched_null_calibration_score(
        quarantine_passed=False,
        arms_comparable=True,
        arm_a_succeeded=True,
        null_success_rate=0.0,
        routing_delta_detected=True,
    )
    assert result["score_computed"] is False
    assert result["blocker"] == "matched_null_patch_quarantine_failed"


def test_null_success_rate_uses_validation_and_duplicate_replay():
    assert null_ensemble_success_rate([
        {"target_validation_status": "PASS", "duplicate_replay_status": "PASS"},
        {"target_validation_status": "PASS", "duplicate_replay_status": "FAIL"},
    ]) == 0.5
