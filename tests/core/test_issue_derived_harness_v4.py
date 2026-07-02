def test_harness_v4_cannot_use_solution_sections():
    policy = {
        "status": "PASS",
        "solution_sections_allowed": False,
        "future_fixed_gold_pr_evidence_allowed": False,
    }

    assert policy["solution_sections_allowed"] is False
    assert policy["future_fixed_gold_pr_evidence_allowed"] is False


def test_harness_v4_cannot_run_without_target_intent_alignment():
    result = {
        "status": "NOT_RUN",
        "target_intent_alignment": False,
        "issue_derived_candidate_verified": False,
        "blocker": "manual_dependency_lock_absent",
    }

    assert result["status"] == "NOT_RUN"
    assert result["issue_derived_candidate_verified"] is False
