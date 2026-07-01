from __future__ import annotations

from controllergate.core.issue_derived_harness import issue_derived_harness_policy, issue_derived_verification_not_run
from controllergate.core.targeted_seed import native_first_order


def test_native_path_runs_before_issue_derived_when_native_test_exists():
    result = native_first_order("issue_derived_reproduction_candidate", native_test_available=True)

    assert result["status"] == "PASS"
    assert result["native_verification_runs_first"] is True
    assert result["issue_derived_allowed_after_native_failure"] is True


def test_issue_derived_candidate_never_increments_native_count():
    policy = issue_derived_harness_policy()
    not_run = issue_derived_verification_not_run("targeted_prospective_seed_missing_or_invalid")

    assert policy["evidence_class"] == "issue_derived_reproduction_candidate"
    assert policy["increments_native_repair_count"] is False
    assert not_run["increments_native_repair_count"] is False
    assert not_run["status"] == "NOT_RUN"
