def test_harness_v3_policy_forbids_solution_and_future_sources():
    policy = {
        "solution_sections_allowed": False,
        "fixed_later_gold_pr_evidence_allowed": False,
        "hidden_benchmark_state_allowed": False,
        "requires_target_intent_alignment": True,
    }
    assert policy["solution_sections_allowed"] is False
    assert policy["fixed_later_gold_pr_evidence_allowed"] is False
    assert policy["requires_target_intent_alignment"] is True


def test_harness_v3_not_generated_when_target_intent_blocked():
    result = {"harness_v3_generated": False, "target_intent_alignment": False, "repair_allowed": False}
    assert result["harness_v3_generated"] is False
    assert result["repair_allowed"] is False
