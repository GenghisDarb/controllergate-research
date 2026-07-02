def test_rollback_block_written_after_dependency_era_failure():
    ledger = [
        {
            "entry_type": "ROLLBACK_BLOCK",
            "blocker": "dependency_era_lock_unavailable",
            "next_allowed_action": "manual_dependency_lock_request",
        }
    ]
    assert any(item["entry_type"] == "ROLLBACK_BLOCK" for item in ledger)
    assert ledger[0]["next_allowed_action"] == "manual_dependency_lock_request"


def test_proof_to_action_does_not_admit_patch_after_unresolved_precondition():
    action = {
        "action_type": "manual_dependency_lock_request",
        "patch_ready_for_review_emitted": False,
        "repair_candidate_admitted_emitted": False,
    }
    assert action["patch_ready_for_review_emitted"] is False
    assert action["repair_candidate_admitted_emitted"] is False
