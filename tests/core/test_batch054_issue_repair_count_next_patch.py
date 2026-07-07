from __future__ import annotations

from controllergate.core.batch054_issue_repair_count_next_patch import _next_seed_records
from controllergate.core.public_status_writer import append_batch054_public_status


def test_batch054_public_status_writer_replaces_stale_batch054_section(tmp_path) -> None:
    for rel in [
        "README.md",
        "docs/current_status.md",
        "docs/capability_inventory.md",
        "docs/technical_validation_gap_report.md",
        "controllergate_v1_7_beta/reports/critic_review_package/shareable_summary.md",
    ]:
        path = tmp_path / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            "Existing text\n\n"
            "### Batch054 issue-derived repair count gate and next patch preparation\n\n"
            "- Batch054 status: `STALE`.\n",
            encoding="utf-8",
        )

    result = append_batch054_public_status(
        tmp_path,
        {
            "status": "PASS_WITH_BATCH054_ISSUE_DERIVED_REPAIR_COUNT_LOCKED",
            "current_protocol": "v2.14",
            "issue_derived_repair_episode_count_after": 2,
            "native_external_repair_episode_count": 4,
            "exact_blocker": None,
            "next_allowed_action": "batch055_next_patch_seed_gate",
            "next_seed_intake_status": "WAITING_FOR_FRESH_SEED",
        },
    )

    text = (tmp_path / "README.md").read_text(encoding="utf-8")
    assert result["status"] == "PASS"
    assert "STALE" not in text
    assert "PASS_WITH_BATCH054_ISSUE_DERIVED_REPAIR_COUNT_LOCKED" in text
    assert "Issue-derived repair episodes after Batch054: `2`" in text
    assert "self-maintaining software remains `false/not_demonstrated`" in text


def test_batch054_next_seed_fastlane_waits_without_running_patch_or_replay(tmp_path) -> None:
    count_gate = {
        "status": "PASS_WITH_BATCH054_ISSUE_DERIVED_REPAIR_COUNT_LOCKED",
        "next_allowed_action": "batch055_next_patch_seed_gate",
    }

    prep, fastlane, handoff = _next_seed_records(tmp_path, count_gate)

    template = tmp_path / "docs/templates/next_manual_issue_seed_manifest.template.json"
    assert template.is_file()
    assert fastlane["next_seed_intake_status"] == "WAITING_FOR_FRESH_SEED"
    assert fastlane["patch_generation_run"] is False
    assert fastlane["target_replay_run"] is False
    assert fastlane["raw_next_seed_manifest_committed"] is False
    assert prep["next_allowed_action_after_count_gate"] == "provide_next_manual_seed_package"
    assert handoff["next_allowed_action"] == "provide_next_manual_seed_package"
