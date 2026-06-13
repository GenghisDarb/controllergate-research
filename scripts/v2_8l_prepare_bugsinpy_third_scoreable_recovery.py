#!/usr/bin/env python3
"""Prepare local v2.8l BugsInPy third scoreable recovery outputs."""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = REPO_ROOT / "outputs" / "v2_8l_bugsinpy_third_scoreable_recovery"
SUMMARY = REPO_ROOT / "controllergate_v1_7_beta" / "reports" / "critic_review_package" / "shareable_summary.md"
V28K_RESULTS = REPO_ROOT / "outputs" / "v2_8k_bugsinpy_third_scoreable_recovery" / "campaign_results.json"

CANDIDATES = [
    {"episode_id": "episode_001", "candidate": "youtube-dl:1", "v2_8k_classification": "inconclusive_equal_performance", "v2_8k_scoreable": True},
    {"episode_id": "episode_002", "candidate": "black:8", "v2_8k_classification": "blocked_no_safe_patch_candidate_generated", "v2_8k_scoreable": False},
    {"episode_id": "episode_003", "candidate": "black:4", "v2_8k_classification": "inconclusive_equal_performance", "v2_8k_scoreable": True},
]


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
    v28k = load_json(V28K_RESULTS)
    section = f"""## v2.8l BugsInPy Third Scoreable Episode Recovery

v2.8l follows the official v2.8k Linux result, where `black:8` remained blocked because the source-only candidate exceeded the repair budget. v2.8l keeps `black:8` as the target and replaces the oversized generator with a compact source-only comment/comma relocation guard.

- v2.8k official scoreable episodes: {v28k.get("scoreable_episode_count", 2)}.
- v2.8k official positive memory episodes: {v28k.get("positive_memory_episode_count", 0)}.
- v2.8k black:8 result: `blocked_no_safe_patch_candidate_generated`.
- v2.8l local workflow status: pending GitHub Actions artifact.
- Candidate set remains: `youtube-dl:1`, `black:8`, `black:4`.
- Full scoring: NOT_RUN / disallowed.
- Memory lift: not demonstrated.
- Self-maintaining software: not demonstrated.

v2.8l does not count candidate construction as repair success. Scoreable evidence still requires post-repair target validation logs under the same anti-leakage rules.
"""
    marker = "## v2.8l BugsInPy Third Scoreable Episode Recovery"
    text = SUMMARY.read_text(encoding="utf-8") if SUMMARY.exists() else ""
    if marker in text:
        start = text.index(marker)
        next_start = text.find("\n## ", start + 1)
        tail = text[next_start:].lstrip() if next_start != -1 else ""
        text = text[:start].rstrip() + "\n\n" + section + ("\n\n" + tail if tail else "")
    else:
        text = text.rstrip() + "\n\n" + section
    write_text(SUMMARY, text)


def prepare() -> None:
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    write_json(
        OUTPUT_DIR / "campaign_plan.json",
        {
            "campaign_id": "v2_8l_bugsinpy_third_scoreable_recovery",
            "workflow": ".github/workflows/v2_8l_bugsinpy_third_scoreable_recovery.yml",
            "runner": "scripts/v2_8l_bugsinpy_third_scoreable_recovery_runner.py",
            "candidate_ids": [item["candidate"] for item in CANDIDATES],
            "targeted_candidate": "black:8",
            "goal": "recover third scoreable BugsInPy episode after v2.8k black:8 safety-budget block",
            "local_status": "pending_linux_runner_artifact",
            "full_scoring_allowed": False,
            "controllergate_full_scoring": "NOT_RUN",
            "self_maintaining_software_demonstrated": False,
        },
    )
    write_json(OUTPUT_DIR / "candidate_pool.json", {"records": CANDIDATES})
    write_json(
        OUTPUT_DIR / "v2_8k_black8_block_diagnosis.json",
        {
            "candidate": "black:8",
            "v2_8k_classification": "blocked_no_safe_patch_candidate_generated",
            "exact_blocker": "source-only safety budget rejected candidate",
            "v2_8k_changed_lines": 16,
            "max_changed_lines": 12,
            "target_failure_matched": True,
            "fixed_or_gold_patch_used": False,
            "future_outcome_evidence_used": False,
            "decision": "black:8 remains valid; use compact source-only patch generator instead of replacement candidate",
        },
    )
    write_json(
        OUTPUT_DIR / "black_or_replacement_candidate_policy.json",
        {
            "primary_candidate": "black:8",
            "black8_valid_target": True,
            "black8_recovery_heuristic": "black8_compact_comment_comma_guard_v2_8l",
            "replacement_candidate_used": False,
            "replacement_allowed_only_if_black8_cannot_be_repaired_without_forbidden_evidence": True,
            "selection_basis": "decision-time target failure context and v2.8k budget-block diagnosis only",
            "source_only_repair_patch": True,
            "tests_may_be_modified": False,
            "fixed_or_gold_patch_used": False,
            "future_outcome_evidence_used": False,
        },
    )
    write_json(
        OUTPUT_DIR / "decision_time_policy.json",
        {"fixed_or_gold_patch_forbidden": True, "future_outcome_evidence_forbidden": True, "test_edits_forbidden": True, "source_only_repair_required": True},
    )
    write_json(
        OUTPUT_DIR / "anti_leakage_policy.json",
        {"no_fixed_or_gold_patch": True, "no_future_outcome_evidence": True, "no_fixed_state_diagnostic_hints": True, "tests_may_be_modified": False, "source_only_repair_patch": True},
    )
    write_json(
        OUTPUT_DIR / "campaign_results.json",
        {
            "workflow_executed": False,
            "executed_episode_count": 0,
            "scoreable_episode_count": 0,
            "positive_memory_episode_count": 0,
            "aggregate_result": "blocked_pending_v2_8l_third_scoreable_recovery_artifact",
            "limited_bugsinpy_real_bug_memory_lift_criteria_met": False,
            "full_scoring_allowed": False,
            "controllergate_full_scoring": "NOT_RUN",
            "self_maintaining_software_demonstrated": False,
        },
    )
    write_json(
        OUTPUT_DIR / "aggregate_bugsinpy_real_bug_memory_lift_assessment.json",
        {
            "aggregate_result": "blocked_pending_v2_8l_third_scoreable_recovery_artifact",
            "scoreable_episode_count": 0,
            "positive_memory_episode_count": 0,
            "minimum_required_scoreable_episodes": 3,
            "limited_bugsinpy_real_bug_memory_lift_criteria_met": False,
            "full_scoring_allowed": False,
            "controllergate_full_scoring": "NOT_RUN",
            "self_maintaining_software_demonstrated": False,
        },
    )
    for name in [
        "decision_report.json",
        "aggregate_report.json",
        "bounded_repair_proposer_summary.json",
        "candidate_source_integrity_check.json",
        "source_discovery_summary.json",
        "pre_repair_replay_gate_summary.json",
        "workspace_equivalence_summary.json",
        "audit.json",
    ]:
        write_json(OUTPUT_DIR / name, {"local_status": "pending_linux_runner_artifact", "campaign_id": "v2_8l_bugsinpy_third_scoreable_recovery"})
    write_text(
        OUTPUT_DIR / "campaign_summary.md",
        "# v2.8l BugsInPy Third Scoreable Episode Recovery\n\n"
        "Local checkpoint status: `blocked_pending_v2_8l_third_scoreable_recovery_artifact`.\n\n"
        "v2.8l targets `black:8` with a compact source-only generator after v2.8k was blocked by the changed-line budget. Full scoring remains disallowed, memory lift is not demonstrated, and self-maintaining software remains undemonstrated.\n",
    )
    write_text(
        OUTPUT_DIR / "github_actions_usage_instructions.md",
        "# v2.8l GitHub Actions Usage\n\n"
        "Run workflow `v2_8l_bugsinpy_third_scoreable_recovery` on branch `controllergate-v1.7-alpha-real-trace-pilot`.\n\n"
        "Expected artifact: `v2_8l_bugsinpy_third_scoreable_recovery_artifacts`.\n",
    )
    update_summary()
    write_manifest(OUTPUT_DIR)


def main() -> int:
    prepare()
    print("v2.8l BugsInPy third scoreable recovery outputs prepared")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
