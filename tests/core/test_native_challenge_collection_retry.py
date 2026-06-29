from __future__ import annotations

import json
from pathlib import Path


BATCH004 = Path("outputs/clean_replication_batch_004")


def _read(path: Path) -> dict[str, object] | list[dict[str, object]]:
    return json.loads(path.read_text(encoding="utf-8"))


def test_command_collection_block_requires_improved_collection_steps():
    attempts = _read(BATCH004 / "native_challenge_attempts.json")
    attempt = attempts[0]

    assert attempt["candidate_id"] == "darker_skip_glob_failing_test"
    assert attempt["prior_blocker"] == "command_cannot_collect_target"
    assert attempt["environment_resolution_attempted_in_prior_evidence"] is True
    assert attempt["target_test_file_exists_in_prior_evidence"] is True
    assert attempt["file_collection_attempted"] is True
    assert attempt["project_pytest_invocation_considered"] is True
    assert attempt["safe_pythonpath_layout_considered"] is True
    assert attempt["ast_node_discovery_attempted"] is True
    assert attempt["node_level_command_attempted_count"] >= 1 or attempt["node_level_command_safely_blocked"] is True
    assert attempt["command_cannot_collect_target_finalized_after_improved_collection"] is True


def test_native_rejection_records_no_forbidden_evidence():
    attempts = _read(BATCH004 / "native_challenge_attempts.json")
    attempt = attempts[0]

    assert attempt["forbidden_evidence_used"] is False
    assert attempt["fixed_later_gold_pr_patch_content_used"] is False
