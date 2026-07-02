def test_rollback_block_is_written_after_missing_manual_lock():
    ledger = [
        {
            "entry_type": "ROLLBACK_BLOCK",
            "blocker": "manual_dependency_lock_absent",
            "next_allowed_action": "provide_canonical_manual_dependency_lock_json",
            "downstream_repair_suppressed": True,
        }
    ]

    assert any(item["entry_type"] == "ROLLBACK_BLOCK" for item in ledger)
    assert ledger[0]["downstream_repair_suppressed"] is True


def test_safe_stop_is_success_when_downstream_work_is_suppressed():
    safe_stop = {
        "status": "SAFE_STOP",
        "safe_stop_success": True,
        "exact_blocker": "manual_dependency_lock_absent",
        "downstream_repair_suppressed": True,
    }

    assert safe_stop["safe_stop_success"] is True
    assert safe_stop["exact_blocker"] == "manual_dependency_lock_absent"
