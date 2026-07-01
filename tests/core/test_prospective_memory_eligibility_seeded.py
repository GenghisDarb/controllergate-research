from __future__ import annotations

from controllergate.core.prospective_memory_challenge import evaluate_prospective_memory_eligibility


def _candidate(**overrides: object) -> dict[str, object]:
    candidate: dict[str, object] = {
        "candidate_id": "fresh_targeted_candidate",
        "native_candidate": True,
        "pre_repair_failure_reproduced": True,
        "source_file_count": 2,
        "function_or_class_count": 1,
        "distinct_strategy_count": 0,
        "status_features": [
            {
                "decision_time_safe": True,
                "uses_patch_bytes_or_rationale": False,
                "source_path": "pkg/module.py",
            }
        ],
    }
    candidate.update(overrides)
    return candidate


def test_prospective_memory_eligibility_requires_route_diversity():
    result = evaluate_prospective_memory_eligibility(_candidate(source_file_count=1, function_or_class_count=1))

    assert result["status"] == "BLOCK"
    assert result["blocker"] == "prospective_memory_no_patchable_alternatives"


def test_prospective_memory_eligibility_requires_mappable_status_features():
    result = evaluate_prospective_memory_eligibility(_candidate(status_features=[]))

    assert result["status"] == "BLOCK"
    assert result["blocker"] == "prospective_memory_no_mappable_status_features"


def test_seeded_fresh_native_candidate_can_pass_eligibility_shape():
    result = evaluate_prospective_memory_eligibility(_candidate())

    assert result["status"] == "PASS"
    assert result["eligible"] is True
