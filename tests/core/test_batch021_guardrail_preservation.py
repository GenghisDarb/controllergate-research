import json
from pathlib import Path


def test_batch021_preserves_claim_boundaries_and_rolls_back_block():
    claim_path = Path("outputs/clean_replication_batch_021/claim_boundary_batch021.json")
    ledger_path = Path("outputs/clean_replication_batch_021/proof_obligations_ledger.json")
    if claim_path.exists() and ledger_path.exists():
        claim = json.loads(claim_path.read_text(encoding="utf-8"))
        ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
        assert claim["native_repair_episode_count"] == 4
        assert claim["issue_derived_repair_episode_count"] == 0
        assert claim["full_scoring"] == "NOT_RUN/disallowed"
        assert claim["memory_lift"] == "not_demonstrated"
        assert any(entry["entry_type"] == "ROLLBACK_BLOCK" for entry in ledger["entries"])

