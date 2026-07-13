from __future__ import annotations

from controllergate.intake.issue_reproducer_lane import assess_issue_reproducer, verify_duplicate_reproducer


def test_issue_reproducer_lane_is_distinct_and_requires_complete_safe_evidence() -> None:
    record = assess_issue_reproducer(candidate_id="x", sanitized_text="Command: poetry init -n\nObserved error: bad name\nExpected: normalized name", platform="windows", runtime="3.13", source_sha="a" * 40)
    assert record["status"] == "ELIGIBLE_FOR_CONSTRUCTION"
    assert record["lane"] == "ISSUE_DERIVED_REPRODUCER_LANE"
    assert record["committed_into_candidate_repository"] is False


def test_solution_contamination_and_duplicate_execution() -> None:
    blocked = assess_issue_reproducer(candidate_id="x", sanitized_text="Command: python -m x\nObserved error\nExpected result\nSuggested fix: replace the function", platform="linux", runtime="3.13", source_sha="a" * 40)
    assert blocked["status"] == "BLOCK"
    assert verify_duplicate_reproducer(["abc", "abc"], ["fresh-1", "fresh-2"])["status"] == "PASS"
    assert verify_duplicate_reproducer(["abc", "def"], ["fresh-1", "fresh-2"])["status"] == "BLOCK"
