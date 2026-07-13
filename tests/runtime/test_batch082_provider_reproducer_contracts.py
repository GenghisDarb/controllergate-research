from __future__ import annotations

import json
from pathlib import Path


def test_frozen_frame_has_exact_platform_runtime_authority() -> None:
    root = Path(__file__).resolve().parents[2]
    frame = json.loads((root / "configs/batch082_candidate_frame.json").read_text(encoding="utf-8"))
    assert frame["candidate_order"] == [
        "incident_openbb_7585_modular_openapi_reproducer",
        "incident_poetry_10974_windows_name_normalization",
    ]
    openbb, poetry = frame["candidates"]
    assert (openbb["source_sha"], openbb["platform"], openbb["runtime"]) == ("1c74893140292944e71ff5cdd9536edf12f05483", "linux", "python3.11")
    assert (poetry["resolved_tag_sha"], poetry["platform"], poetry["runtime"]) == ("811a12dae0fe81f199e3f1b88b8b8be9eed543c2", "windows", "python3.13")


def test_issue_snapshots_exclude_comments_and_fix_material() -> None:
    root = Path(__file__).resolve().parents[2]
    snapshots = json.loads((root / "configs/batch082_issue_snapshots.json").read_text(encoding="utf-8"))
    assert snapshots["comments_included"] is False
    assert snapshots["fix_prs_included"] is False
    assert snapshots["later_commits_included"] is False


def test_preregistration_forbids_replacement_and_memory_patch_content() -> None:
    root = Path(__file__).resolve().parents[2]
    policy = json.loads((root / "configs/batch082_preregistration.json").read_text(encoding="utf-8"))
    assert policy["candidate_replacement_after_execution"] is False
    assert policy["authoritative_repair_memory"] == "NO_MEMORY"
    assert policy["maximum_authoritative_repairs"] == 2
