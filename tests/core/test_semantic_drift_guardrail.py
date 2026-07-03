import json
from pathlib import Path


def test_batch020_public_language_audit_passes():
    path = Path("outputs/clean_replication_batch_020/public_language_audit_batch020.json")
    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data["status"] == "PASS"
        assert data["hits"] == []
