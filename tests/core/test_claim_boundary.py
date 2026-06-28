from __future__ import annotations

from controllergate.core.claim_boundary import (
    classify_evidence_level,
    enforce_no_full_scoring,
    enforce_no_memory_lift_without_matched_null,
    enforce_no_self_maintaining_claim,
)


def test_claim_boundary_guards():
    boundary = {
        "full_scoring": "NOT_RUN/disallowed",
        "self_maintaining_software": "false/not_demonstrated",
        "memory_lift": "undemonstrated",
    }

    assert enforce_no_full_scoring(boundary)
    assert enforce_no_self_maintaining_claim(boundary)
    assert enforce_no_memory_lift_without_matched_null(boundary)
    assert classify_evidence_level(boundary) == "bounded_research_evidence"
