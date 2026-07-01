from controllergate.core.prospective_memory_challenge import evaluate_prospective_memory_eligibility, is_fresh_candidate


def test_prior_repaired_candidates_cannot_enter_prospective_memory_challenge():
    assert is_fresh_candidate("darker_skip_glob_failing_test") is False
    result = evaluate_prospective_memory_eligibility(
        {
            "candidate_id": "darker_skip_glob_failing_test",
            "native_candidate": True,
            "pre_repair_failure_reproduced": True,
            "source_file_count": 2,
            "function_or_class_count": 2,
            "status_features": [
                {
                    "decision_time_safe": True,
                    "source_path": "src/pkg/mod.py",
                    "uses_patch_bytes_or_rationale": False,
                }
            ],
        }
    )
    assert result["eligible"] is False
    assert result["blocker"] == "prospective_memory_candidate_not_fresh"


def test_issue_derived_candidate_cannot_count_as_native_prospective_memory_lift():
    result = evaluate_prospective_memory_eligibility(
        {
            "candidate_id": "fresh_issue_candidate",
            "native_candidate": False,
            "pre_repair_failure_reproduced": True,
            "source_file_count": 2,
            "function_or_class_count": 2,
            "status_features": [
                {
                    "decision_time_safe": True,
                    "source_path": "src/pkg/mod.py",
                    "uses_patch_bytes_or_rationale": False,
                }
            ],
        }
    )
    assert result["eligible"] is False
    assert result["blocker"] == "prospective_memory_eligibility_not_met"
