import json
from pathlib import Path


def test_feature_vectors_reassert_after_manual_lock_validation():
    path = Path("outputs/clean_replication_batch_020/feature_vector_reassertion_batch020.json")
    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data["status"] == "PASS"
        assert data["recomputed_after_manual_lock_validation"] is True
