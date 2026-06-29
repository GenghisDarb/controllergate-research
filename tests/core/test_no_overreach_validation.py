from __future__ import annotations

from controllergate.core.clean_repair import no_overreach_validation


def test_no_overreach_requires_target_and_duplicate_pass():
    result = no_overreach_validation(
        {"candidate_id": "darker_stdin_filename"},
        {"status": "PASS"},
        {"status": "PASS"},
    )

    assert result["status"] == "PASS"
    assert result["duplicate_clean_replay_3_of_3"] is True
    assert result["stronger_robustness_claim_allowed"] is False
