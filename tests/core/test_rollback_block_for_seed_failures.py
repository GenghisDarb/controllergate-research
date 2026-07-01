import json
from pathlib import Path


def test_batch013_proof_ledger_contains_seed_failure_rollback_block():
    path = Path("outputs/clean_replication_batch_013/proof_obligations_ledger.json")
    if not path.is_file():
        return
    proof = json.loads(path.read_text(encoding="utf-8"))

    rollback_entries = [entry for entry in proof["entries"] if entry.get("entry_type") == "ROLLBACK_BLOCK"]
    assert rollback_entries
    assert rollback_entries[0]["blocker"] == "targeted_prospective_seed_missing_or_invalid_after_locks_ready"
