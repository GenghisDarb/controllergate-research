from __future__ import annotations

import json
from pathlib import Path


BATCH005 = Path("outputs/clean_replication_batch_005")


def _read(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_source_materialization_precedes_ast_node_discovery():
    materialization = _read(BATCH005 / "source_materialization_log.json")
    nodes = _read(BATCH005 / "native_challenge_node_discovery.json")
    attempts = _read(BATCH005 / "native_challenge_retry_attempts.json")

    assert materialization["source_materialized"] is True
    assert materialization["workspace_path"] == "<ephemeral_root>"
    assert materialization["runtime_workspace_outside_repo"] is True
    assert materialization["runtime_workspace_outside_onedrive"] is True
    assert nodes["status"] == "PASS"
    assert attempts[0]["ast_node_discovery_attempted_from_materialized_source"] is True


def test_command_cannot_collect_requires_materialized_retry():
    attempts = _read(BATCH005 / "native_challenge_retry_attempts.json")
    attempt = attempts[0]

    assert attempt["source_materialized"] is True
    if attempt["collection_attempted_from_materialized_source"] is False:
        assert attempt["blocker"] in {
            "native_challenge_command_cannot_collect_target_after_materialization",
            "environment_dependency_install_failed",
        }
        assert attempt["node_level_command_blocked_reason"]
    if attempt["collection_attempted_from_materialized_source"] is True and attempt["blocker"] == "native_challenge_command_cannot_collect_target_after_materialization":
        assert attempt["node_level_command_attempted_count"] >= 0


def test_target_test_and_environment_metadata_verified_from_checkout():
    materialization = _read(BATCH005 / "source_materialization_log.json")

    assert materialization["commit_sha"] == "bd28cdc3e1a56f2d2a6e25d6ca75a7cc41e71f75"
    assert materialization["git_object_type_commit"] is True
    assert materialization["target_test_path_exists"] is True
    assert materialization["target_test_sha256"]
    assert materialization["environment_file_present"] is True
