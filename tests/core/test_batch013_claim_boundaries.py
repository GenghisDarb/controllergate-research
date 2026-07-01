import json
from pathlib import Path


def test_batch013_claim_boundary_preserves_counts_and_limits():
    path = Path("outputs/clean_replication_batch_013/claim_boundary.json")
    if not path.is_file():
        return
    claim = json.loads(path.read_text(encoding="utf-8"))

    assert claim["full_scoring"] == "NOT_RUN/disallowed"
    assert claim["full_memory_lift_claimed"] is False
    assert claim["confirmed_native_repair_episode_count"] == 4
    assert claim["confirmed_issue_derived_repair_episode_count"] == 0
