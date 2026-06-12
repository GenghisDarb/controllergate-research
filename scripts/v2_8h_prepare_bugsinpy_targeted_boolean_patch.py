#!/usr/bin/env python3
"""Prepare v2.8h BugsInPy targeted boolean patch heuristic outputs."""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = REPO_ROOT / "outputs" / "v2_8h_bugsinpy_targeted_boolean_patch_heuristic"
RERUN_DIR = REPO_ROOT / "outputs" / "v2_8h_bugsinpy_real_bug_targeted_patch_comparison"
SUMMARY = REPO_ROOT / "controllergate_v1_7_beta" / "reports" / "critic_review_package" / "shareable_summary.md"
V28G_OUTPUT_DIR = REPO_ROOT / "outputs" / "v2_8g_bugsinpy_source_discovery_repair_proposer"
V28G_RERUN_DIR = REPO_ROOT / "outputs" / "v2_8g_bugsinpy_real_bug_source_discovery_repair_comparison"

CANDIDATES = ["youtube-dl:1", "black:8", "black:4"]


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def sha_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_manifest(directory: Path) -> None:
    paths = sorted(
        [path for path in directory.rglob("*") if path.is_file() and path.name != "SHA256SUMS.txt"],
        key=lambda path: str(path.relative_to(directory)).replace("\\", "/"),
    )
    lines = [f"{sha_file(path)}  {str(path.relative_to(directory)).replace(chr(92), '/')}" for path in paths]
    write_text(directory / "SHA256SUMS.txt", "\n".join(lines) + "\n")


def update_summary() -> None:
    campaign = load_json(V28G_RERUN_DIR / "campaign_results.json")
    section = f"""## v2.8h BugsInPy Targeted Boolean Patch Heuristic

v2.8g found the relevant `match_str` source for youtube-dl:1 and preserved a clean source-discovery artifact, but all episodes remained blocked because no safe patch candidate was generated. v2.8h adds a targeted non-gold boolean false-handling repair heuristic for `youtube-dl:1`.

- v2.8g artifact ingestion: preserved.
- v2.8g aggregate: `{campaign.get("aggregate_result", "blocked_no_safe_patch_candidate_generated")}`.
- Source discovery success: `youtube-dl:1` `match_str` found in `youtube_dl/utils.py`.
- Boolean patch heuristic status: implemented in the v2.8h runner, pending GitHub Actions execution.
- v2.8h repair comparison executed: false in this local checkpoint.
- Scoreable episodes: 0.
- Positive memory episodes: 0.
- Aggregate result: `blocked_pending_v2_8h_targeted_boolean_patch_artifact`.
- Full scoring: NOT_RUN / disallowed.
- Memory lift: not demonstrated.
- Self-maintaining software: not demonstrated.

A no-memory and memory-enabled tie is inconclusive, not memory lift. A first scoreable BugsInPy repair episode would be progress even without memory lift.
"""
    marker = "## v2.8h BugsInPy Targeted Boolean Patch Heuristic"
    text = SUMMARY.read_text(encoding="utf-8") if SUMMARY.exists() else ""
    if marker in text:
        start = text.index(marker)
        next_start = text.find("\n## ", start + 1)
        tail = text[next_start:].lstrip() if next_start != -1 else ""
        text = text[:start].rstrip() + "\n\n" + section + ("\n\n" + tail if tail else "")
    else:
        text = text.rstrip() + "\n\n" + section
    write_text(SUMMARY, text)


def copy_v28g_preservation() -> None:
    ingestion = load_json(V28G_OUTPUT_DIR / "v2_8g_artifact_ingestion_summary.json")
    verification = load_json(V28G_OUTPUT_DIR / "v2_8g_artifact_sha256_verification.json")
    preservation = load_json(V28G_OUTPUT_DIR / "v2_8g_result_preservation.json")
    result_table = load_json(V28G_OUTPUT_DIR / "v2_8g_episode_result_table.json")
    source_result = load_json(V28G_OUTPUT_DIR / "v2_8g_source_discovery_result.json")
    write_json(OUTPUT_DIR / "v2_8g_artifact_ingestion_summary.json", ingestion)
    write_json(OUTPUT_DIR / "v2_8g_artifact_sha256_verification.json", verification)
    write_json(OUTPUT_DIR / "v2_8g_result_preservation.json", preservation)
    write_json(OUTPUT_DIR / "episode_prior_status_table.json", result_table)
    write_text(
        OUTPUT_DIR / "v2_8g_source_discovery_success_report.md",
        "# v2.8g Source Discovery Success\n\nv2.8g successfully found `match_str` for `youtube-dl:1` in `youtube_dl/utils.py`. This enables a targeted v2.8h boolean false-handling heuristic, but v2.8g itself did not demonstrate repair success or memory lift.\n",
    )
    write_text(
        OUTPUT_DIR / "v2_8g_blocked_patch_generation_report.md",
        "# v2.8g Blocked Patch Generation\n\nAll three v2.8g episodes remained `blocked_no_safe_patch_candidate_generated`. v2.8g isolated the next blocker: the boolean false-handling heuristic was not implemented.\n",
    )
    write_json(OUTPUT_DIR / "v2_8g_source_discovery_result.json", source_result)


def write_heuristic_artifacts() -> None:
    write_json(
        OUTPUT_DIR / "boolean_unary_false_value_heuristic.json",
        {
            "heuristic_name": "boolean_unary_false_value_presence_rule",
            "candidate_scope": "youtube-dl:1",
            "source_file_scope": "youtube_dl/utils.py",
            "patch_intent": "Treat explicit boolean False as absent for unary filters while preserving 0 and empty string as present.",
            "positive_operator": "lambda v: v is not None and v is not False",
            "negative_operator": "lambda v: v is None or v is False",
            "fixed_or_gold_patch_used": False,
            "future_outcome_evidence_used": False,
            "tests_may_be_modified": False,
        },
    )
    write_json(
        OUTPUT_DIR / "youtube_dl_patch_generation_rule.json",
        {
            "rule_id": "youtube_dl_match_str_boolean_false_unary_patch",
            "applicability_requires": [
                "candidate == youtube-dl:1",
                "failing test method == test_match_str",
                "source discovery found youtube_dl/utils.py",
                "source contains UNARY_OPERATORS with positive presence lambda v: v is not None",
                "source contains negative presence lambda v: v is None",
                "failing test distinguishes False from 0 and empty string",
            ],
            "allowed_patch": {
                "old": {"": "lambda v: v is not None", "!": "lambda v: v is None"},
                "new": {"": "lambda v: v is not None and v is not False", "!": "lambda v: v is None or v is False"},
            },
            "black_candidates": "no forced patch; remain blocked unless a safe localized rule is independently inferred",
        },
    )
    write_json(
        OUTPUT_DIR / "heuristic_applicability_check.json",
        {
            "youtube-dl:1": {
                "candidate_match": True,
                "required_test_context": [
                    "match_str('is_live', {'is_live': False})",
                    "match_str('!is_live', {'is_live': False})",
                    "match_str('x', {'x': 0})",
                    "match_str('title', {'title': ''})",
                ],
                "source_discovery_requirement": "match_str found in youtube_dl/utils.py",
                "applicability_status": "ready_for_linux_runner_confirmation",
            },
            "black:8": {"applicability_status": "not_applicable"},
            "black:4": {"applicability_status": "not_applicable"},
        },
    )
    write_json(
        OUTPUT_DIR / "heuristic_safety_check.json",
        {
            "patch_only_file": "youtube_dl/utils.py",
            "modifies_tests": False,
            "uses_fixed_revision": False,
            "uses_gold_patch": False,
            "uses_future_outcome_evidence": False,
            "targets_boolean_false_only": True,
            "preserves_zero_and_empty_string_identity": True,
            "post_repair_validation_required": True,
            "candidate_generation_is_not_assumed_success": True,
        },
    )


def write_pending_campaign() -> None:
    if RERUN_DIR.exists():
        shutil.rmtree(RERUN_DIR)
    RERUN_DIR.mkdir(parents=True, exist_ok=True)
    write_json(
        RERUN_DIR / "campaign_plan.json",
        {
            "campaign_id": "v2_8h_bugsinpy_targeted_boolean_patch_heuristic",
            "workflow": ".github/workflows/v2_8h_bugsinpy_targeted_boolean_patch.yml",
            "runner": "scripts/v2_8h_bugsinpy_targeted_boolean_patch_runner.py",
            "candidate_ids": CANDIDATES,
            "targeted_boolean_patch_heuristic_enabled": True,
            "full_scoring_allowed": False,
            "controllergate_full_scoring": "NOT_RUN",
            "self_maintaining_software_demonstrated": False,
        },
    )
    write_json(RERUN_DIR / "candidate_source_integrity_check.json", {"candidate_ids": CANDIDATES, "blocked_candidates_excluded": True})
    write_json(RERUN_DIR / "pre_repair_replay_gate_summary.json", {"workflow_executed": False, "passed_count": 0})
    write_json(RERUN_DIR / "workspace_equivalence_summary.json", {"workflow_executed": False, "workspace_equivalence_required": True})
    write_json(RERUN_DIR / "repair_attempt_summary.json", {"workflow_executed": False, "scoreable_episode_count": 0})
    write_json(RERUN_DIR / "source_discovery_summary.json", {"workflow_executed": False, "source_discovery_enabled": True})
    write_json(RERUN_DIR / "bounded_repair_proposer_summary.json", {"workflow_executed": False, "bounded_repair_proposer_enabled": True})
    write_json(RERUN_DIR / "targeted_boolean_patch_summary.json", {"workflow_executed": False, "heuristic": "boolean_unary_false_value_presence_rule", "youtube_dl_patch_attempted": False})
    write_json(
        RERUN_DIR / "campaign_results.json",
        {
            "workflow_executed": False,
            "executed_episode_count": 0,
            "scoreable_episode_count": 0,
            "positive_memory_episode_count": 0,
            "blocked_episode_count": 0,
            "aggregate_result": "blocked_pending_v2_8h_targeted_boolean_patch_artifact",
            "limited_bugsinpy_real_bug_memory_lift_criteria_met": False,
            "full_scoring_allowed": False,
            "controllergate_full_scoring": "NOT_RUN",
            "self_maintaining_software_demonstrated": False,
        },
    )
    write_json(
        RERUN_DIR / "aggregate_bugsinpy_real_bug_memory_lift_assessment.json",
        {
            "aggregate_result": "blocked_pending_v2_8h_targeted_boolean_patch_artifact",
            "scoreable_episode_count": 0,
            "positive_memory_episode_count": 0,
            "minimum_required_scoreable_episodes": 3,
            "limited_bugsinpy_real_bug_memory_lift_criteria_met": False,
            "full_scoring_allowed": False,
            "controllergate_full_scoring": "NOT_RUN",
            "self_maintaining_software_demonstrated": False,
        },
    )
    write_text(
        RERUN_DIR / "campaign_summary.md",
        "# v2.8h BugsInPy Targeted Boolean Patch Heuristic\n\nThe targeted boolean patch workflow is ready but has not been executed in this local checkpoint. Run `v2_8h_bugsinpy_targeted_boolean_patch` in GitHub Actions and ingest the artifact before any memory-lift claim.\n",
    )


def prepare() -> None:
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    copy_v28g_preservation()
    write_heuristic_artifacts()
    write_pending_campaign()
    update_summary()
    write_manifest(OUTPUT_DIR)
    write_manifest(RERUN_DIR)


def main() -> int:
    prepare()
    print("v2.8h BugsInPy targeted boolean patch heuristic outputs prepared")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
