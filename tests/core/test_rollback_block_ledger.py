from controllergate.core.rollback_ledger import audit_rollback_block_ledger, rollback_block_entry


def test_rollback_block_entry_records_previous_state_hash():
    entry = rollback_block_entry(
        entry_index=1,
        action="seed_gate",
        blocker="targeted_prospective_seed_missing_or_invalid_after_locks_ready",
        next_allowed_action="commit_reviewed_seed",
        rollback_target_entry_index=0,
        pre_action_state={"locks": "ready"},
        attempted_action_state={"seed_present": False},
    )

    assert entry["entry_type"] == "ROLLBACK_BLOCK"
    assert entry["previous_state_hash"] == entry["pre_action_hash"]
    assert entry["chain_status"] == "PASS"


def test_rollback_block_ledger_audit_requires_block_entry():
    assert audit_rollback_block_ledger([])["status"] == "BLOCK"
