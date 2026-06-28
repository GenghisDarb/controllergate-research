from __future__ import annotations

from controllergate.core.evidence_classes import classify_candidate_evidence, temporal_guard_policy


def test_issue_derived_class_separate_from_native():
    issue = classify_candidate_evidence("issue_derived_reproduction_candidate")
    native = classify_candidate_evidence("native_buggy_tree_test_candidate")

    assert issue["increments_native_count"] is False
    assert issue["increments_issue_derived_count"] is True
    assert native["increments_native_count"] is True
    assert "issue_text_temporal_guard_failed" in temporal_guard_policy()["blockers"]
