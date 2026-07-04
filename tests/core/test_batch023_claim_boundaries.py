import json
from pathlib import Path


def test_batch023_claim_boundaries_do_not_advance():
    claim = json.loads(Path("outputs/clean_replication_batch_023/claim_boundary_batch023.json").read_text(encoding="utf-8"))
    assert claim["native_repair_episode_count"] == 4
    assert claim["issue_derived_repair_episode_count"] == 0
    assert claim["matched_null_diagnostic_run_count"] == 0
    assert claim["full_scoring"] == "NOT_RUN/disallowed"
    assert claim["memory_lift"] == "not_demonstrated"
    assert claim["self_maintaining_software"] == "false/not_demonstrated"
