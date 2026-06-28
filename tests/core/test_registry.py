from __future__ import annotations

from controllergate.core.registry import (
    add_candidate_entry,
    count_reviewed_issue_derived_candidates,
    count_reviewed_native_candidates,
    reject_duplicate_candidate_id,
    validate_external_candidate_registry,
)


def test_registry_counts_and_duplicate_guard():
    registry = {
        "candidates": [
            {
                "candidate_id": "native_1",
                "registry_review_status": "reviewed",
                "candidate_class": "native_buggy_tree_test_candidate",
            },
            {
                "candidate_id": "issue_1",
                "registry_review_status": "reviewed",
                "candidate_class": "issue_derived_reproduction_candidate",
            },
        ]
    }

    assert count_reviewed_native_candidates(registry) == 1
    assert count_reviewed_issue_derived_candidates(registry) == 1
    assert validate_external_candidate_registry(registry)["registry_validation_status"] == "PASS"
    assert reject_duplicate_candidate_id(registry, "native_1") is True

    add_candidate_entry(registry, {"candidate_id": "native_2"})
    assert reject_duplicate_candidate_id(registry, "native_2") is True
