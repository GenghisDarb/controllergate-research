import json
from pathlib import Path


def test_materialization_block_writes_rollback_block():
    ledger = Path("outputs/clean_replication_batch_020/proof_obligations_ledger.json")
    if ledger.exists():
        data = json.loads(ledger.read_text(encoding="utf-8"))
        entries = data["entries"]
        assert entries
        entry = entries[0]
        assert entry["entry_type"] == "ROLLBACK_BLOCK"
        for key in ["previous_state_hash", "attempted_action_hash", "rollback_target_entry_index", "rollback_hash", "blocker", "next_allowed_action"]:
            assert key in entry
