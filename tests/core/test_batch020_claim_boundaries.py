import json
from pathlib import Path


def test_issue_derived_evidence_does_not_change_native_or_memory_claims():
    path = Path("outputs/clean_replication_batch_020/claim_boundary_batch020.json")
    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data["native_repair_episode_count"] == 4
        assert data["issue_derived_repair_episode_count"] == 0
        assert data["full_scoring"] == "NOT_RUN/disallowed"
        assert data["memory_lift"] == "not_demonstrated"
        assert data["self_maintaining_software"] == "false/not_demonstrated"
