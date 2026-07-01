from controllergate.core.prospective_memory_challenge import evaluate_prospective_memory_eligibility


def test_candidate_with_one_obvious_source_route_fails_memory_eligibility():
    result = evaluate_prospective_memory_eligibility(
        {
            "candidate_id": "fresh_candidate",
            "native_candidate": True,
            "pre_repair_failure_reproduced": True,
            "source_file_count": 1,
            "function_or_class_count": 1,
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
    assert result["blocker"] == "prospective_memory_no_patchable_alternatives"


def test_candidate_with_no_mappable_status_feature_fails_memory_eligibility():
    result = evaluate_prospective_memory_eligibility(
        {
            "candidate_id": "fresh_candidate",
            "native_candidate": True,
            "pre_repair_failure_reproduced": True,
            "source_file_count": 2,
            "function_or_class_count": 2,
            "status_features": [{"decision_time_safe": True, "uses_patch_bytes_or_rationale": False}],
        }
    )
    assert result["eligible"] is False
    assert result["blocker"] == "prospective_memory_no_mappable_status_features"


def test_candidate_with_multiple_legal_routes_may_pass_route_diversity():
    result = evaluate_prospective_memory_eligibility(
        {
            "candidate_id": "fresh_candidate",
            "native_candidate": True,
            "pre_repair_failure_reproduced": True,
            "source_file_count": 2,
            "function_or_class_count": 1,
            "status_features": [
                {
                    "decision_time_safe": True,
                    "source_path": "src/pkg/mod.py",
                    "uses_patch_bytes_or_rationale": False,
                }
            ],
        }
    )
    assert result["eligible"] is True
    assert result["status"] == "PASS"
