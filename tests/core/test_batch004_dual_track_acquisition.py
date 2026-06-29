from __future__ import annotations

import json
from pathlib import Path


BATCH004 = Path("outputs/clean_replication_batch_004")


def _read(path: Path) -> dict[str, object] | list[dict[str, object]]:
    return json.loads(path.read_text(encoding="utf-8"))


def test_native_acquisition_runs_before_issue_derived_fallback():
    policy = _read(BATCH004 / "batch004_dual_track_acquisition_policy.json")
    state = _read(BATCH004 / "consolidated_state_clean_replication_batch_004.json")

    assert policy["track_order"] == [
        "native_challenge_acquisition",
        "issue_derived_ephemeral_reproduction_harness_fallback",
    ]
    assert policy["issue_derived_fallback_only_after_native_failure"] is True
    assert state["native_track_attempted_first"] is True
    assert state["issue_derived_fallback_activated"] is True


def test_issue_derived_fallback_cannot_increment_native_counts():
    separation = _read(BATCH004 / "native_issue_derived_count_separation.json")

    assert separation["issue_derived_repairs_count_as_native"] is False
    assert separation["native_candidates_verified_count"] == 0
    assert separation["issue_derived_candidates_verified_count"] == 0


def test_batch004_blocks_with_expected_no_candidate_blocker():
    state = _read(BATCH004 / "consolidated_state_clean_replication_batch_004.json")

    assert state["status"] == "BLOCKED"
    assert state["exact_blocker"] == "batch004_no_native_or_issue_derived_challenge_candidate_verified"
