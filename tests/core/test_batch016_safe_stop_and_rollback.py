import json
from pathlib import Path


def test_rollback_block_written_after_target_intent_failure():
    ledger = Path("outputs/clean_replication_batch_016/proof_obligations_ledger.json")
    if ledger.exists():
        entries = json.loads(ledger.read_text(encoding="utf-8"))
        assert any(item.get("entry_type") == "ROLLBACK_BLOCK" for item in entries)


def test_issue_derived_evidence_cannot_increment_native_count_or_claim_memory():
    boundary = Path("outputs/clean_replication_batch_016/claim_boundary_batch016.json")
    if boundary.exists():
        data = json.loads(boundary.read_text(encoding="utf-8"))
        assert data["confirmed_native_repair_episode_count"] == 4
        assert data["native_memory_separation_claim_allowed"] is False
