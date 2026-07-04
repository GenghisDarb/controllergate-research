import json
from pathlib import Path


def test_batch024_issue_derived_evidence_does_not_overclaim():
    state = json.loads(Path("outputs/clean_replication_batch_024/consolidated_state_clean_replication_batch_024.json").read_text(encoding="utf-8"))
    assert state["native_repair_episode_count"] == 4
    assert state["issue_derived_repair_episode_count"] == 0
    assert state["memory_separation_claim_status"] == "not_demonstrated"
    assert state["self_maintaining_software"] == "false/not_demonstrated"
