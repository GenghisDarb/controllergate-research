from __future__ import annotations

import json
from pathlib import Path


def test_repair_episode_registry_requires_validation_and_duplicate_replay_for_darker_stdin():
    registry = json.loads(Path("configs/external_repair_episode_registry.json").read_text(encoding="utf-8"))
    episode = next(
        item
        for item in registry["episodes"]
        if item["candidate_id"] == "darker_stdin_filename"
    )

    assert episode["scoreable"] is True
    assert episode["target_validation_status"] == "PASS"
    assert episode["duplicate_replay_status"] == "PASS"
    assert episode["full_scoring"] == "NOT_RUN/disallowed"
    assert episode["self_maintaining_software"] == "false/not_demonstrated"
