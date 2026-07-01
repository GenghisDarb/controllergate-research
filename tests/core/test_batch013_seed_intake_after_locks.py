import json
from pathlib import Path


def test_batch013_blocks_after_locks_ready_when_seed_missing():
    state_path = Path("outputs/clean_replication_batch_013/consolidated_state_clean_replication_batch_013.json")
    if not state_path.is_file():
        return
    state = json.loads(state_path.read_text(encoding="utf-8"))

    assert state["status"] == "BLOCK"
    assert state["exact_blocker"] == "targeted_prospective_seed_missing_or_invalid_after_locks_ready"
    assert state["acquisition_lock_stack_status"] == "PASS_WITH_SEED_BLOCKED"
