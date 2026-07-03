import json
from pathlib import Path


def test_batch022_claim_boundaries_do_not_overclaim():
    path = Path("outputs/clean_replication_batch_022/claim_boundary_batch022.json")
    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data["native_repair_episode_count"] == 4
        assert data["issue_derived_repair_episode_count"] == 0
        assert data["full_scoring"] == "NOT_RUN/disallowed"
        assert data["self_maintaining_software"] == "false/not_demonstrated"
        assert data["hallucination_elimination"] == "false/not_claimed"
        assert data["absolute_uncrashability"] == "false/not_claimed"
