from __future__ import annotations

from controllergate.core.targeted_seed import issue112_claim_boundary


def test_issue_derived_candidate_cannot_increment_native_count():
    result = issue112_claim_boundary(issue_derived=True, repair_succeeded=True)

    assert result["native_repair_count_increment_allowed"] is False
    assert result["issue_derived_feasibility_increment_allowed"] is True


def test_issue_derived_candidate_cannot_claim_native_memory_separation():
    result = issue112_claim_boundary(issue_derived=True, repair_succeeded=False)

    assert result["native_memory_separation_claim_allowed"] is False
    assert result["prospective_native_memory_lift"] == "not_demonstrated"
