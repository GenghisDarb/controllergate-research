from __future__ import annotations

from controllergate.core.targeted_seed import issue112_claim_boundary


def test_issue112_claim_boundary_keeps_global_claims_closed():
    result = issue112_claim_boundary(issue_derived=True, repair_succeeded=False)

    assert result["full_scoring"] == "NOT_RUN/disallowed"
    assert result["self_maintaining_software"] == "false/not_demonstrated"
    assert result["native_memory_separation_claim_allowed"] is False
