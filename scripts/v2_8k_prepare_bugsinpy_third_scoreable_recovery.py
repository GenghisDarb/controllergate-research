#!/usr/bin/env python3
"""Prepare local v2.8k BugsInPy third scoreable recovery outputs."""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = REPO_ROOT / "outputs" / "v2_8k_bugsinpy_third_scoreable_recovery"
SUMMARY = REPO_ROOT / "controllergate_v1_7_beta" / "reports" / "critic_review_package" / "shareable_summary.md"
V28J_RESULTS = REPO_ROOT / "outputs" / "v2_8j_bugsinpy_scoreable_episode_expansion" / "campaign_results.json"

CANDIDATES = [
    {"episode_id": "episode_001", "candidate": "youtube-dl:1", "v2_8j_classification": "inconclusive_equal_performance", "v2_8j_scoreable": True},
    {"episode_id": "episode_002", "candidate": "black:8", "v2_8j_classification": "failed_both", "v2_8j_scoreable": False},
    {"episode_id": "episode_003", "candidate": "black:4", "v2_8j_classification": "inconclusive_equal_performance", "v2_8j_scoreable": True},
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
    v28j = load_json(V28J_RESULTS)
    section = f"""## v2.8k BugsInPy Third Scoreable Episode Recovery

v2.8k is a bounded Linux runner continuation after the official v2.8j result reached two scoreable BugsInPy episodes but remained below the aggregate threshold. The runner targets the missing third scoreable episode by refining the `black:8` source-only comma relocation patch construction path.

- v2.8j official executed episodes: {v28j.get("executed_episode_count", 3)}.
- v2.8j official scoreable episodes: {v28j.get("scoreable_episode_count", 2)}.
- v2.8j official positive memory episodes: {v28j.get("positive_memory_episode_count", 0)}.
- v2.8k local workflow status: pending GitHub Actions artifact.
- Targeted recovery candidate: `black:8`.
- Candidate set remains: `youtube-dl:1`, `black:8`, `black:4`.
- Full scoring: NOT_RUN / disallowed.
- Memory lift: not demonstrated.
- Self-maintaining software: not demonstrated.

v2.8k does not treat candidate promotion, patch construction, or missing logs as repair success. Scoreable evidence still requires Linux post-repair target validation logs under the same anti-leakage rules.
"""
    marker = "## v2.8k BugsInPy Third Scoreable Episode Recovery"
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
            "campaign_id": "v2_8k_bugsinpy_third_scoreable_recovery",
            "workflow": ".github/workflows/v2_8k_bugsinpy_third_scoreable_recovery.yml",
            "runner": "scripts/v2_8k_bugsinpy_third_scoreable_recovery_runner.py",
            "candidate_ids": [item["candidate"] for item in CANDIDATES],
            "targeted_candidate": "black:8",
            "goal": "recover the missing third scoreable BugsInPy episode without weakening anti-leakage or target-validation gates",
            "local_status": "pending_linux_runner_artifact",
            "full_scoring_allowed": False,
            "controllergate_full_scoring": "NOT_RUN",
            "self_maintaining_software_demonstrated": False,
        },
    )
    write_json(OUTPUT_DIR / "candidate_pool.json", {"records": CANDIDATES})
    write_json(
        OUTPUT_DIR / "previous_v2_8j_official_result.json",
        {
            "executed_episode_count": 3,
            "scoreable_episode_count": 2,
            "positive_memory_episode_count": 0,
            "aggregate_result": "insufficient_episode_count_for_bugsinpy_real_bug_memory_lift",
            "black_8_prior_classification": "failed_both",
            "interpretation": "official v2.8j Linux result; not memory lift",
        },
    )
    write_json(
        OUTPUT_DIR / "third_scoreable_recovery_policy.json",
        {
            "target": "black:8",
            "recovery_heuristic": "black8_comment_comma_relocation_guard_v2_8k",
            "source_only_repair_patch": True,
            "tests_may_be_modified": False,
            "dependency_runtime_setup_is_not_code_repair": True,
            "fixed_or_gold_patch_used": False,
            "future_outcome_evidence_used": False,
            "scoreable_requires_post_repair_target_validation_pass": True,
        },
    )
    write_json(
        OUTPUT_DIR / "anti_leakage_policy.json",
        {
            "no_fixed_or_gold_patch": True,
            "no_future_outcome_evidence": True,
            "no_fixed_state_diagnostic_hints": True,
            "tests_may_be_modified": False,
            "source_only_repair_patch": True,
            "prior_failed_replay_logs_allowed_as_controllergate_memory": True,
        },
    )
    write_json(
        OUTPUT_DIR / "campaign_results.json",
        {
            "workflow_executed": False,
            "executed_episode_count": 0,
            "scoreable_episode_count": 0,
            "positive_memory_episode_count": 0,
            "aggregate_result": "blocked_pending_v2_8k_third_scoreable_recovery_artifact",
            "limited_bugsinpy_real_bug_memory_lift_criteria_met": False,
            "full_scoring_allowed": False,
            "controllergate_full_scoring": "NOT_RUN",
            "self_maintaining_software_demonstrated": False,
        },
    )
    write_json(
        OUTPUT_DIR / "aggregate_bugsinpy_real_bug_memory_lift_assessment.json",
        {
            "aggregate_result": "blocked_pending_v2_8k_third_scoreable_recovery_artifact",
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
        OUTPUT_DIR / "github_actions_usage_instructions.md",
        "# v2.8k GitHub Actions Usage\n\n"
        "Run workflow `v2_8k_bugsinpy_third_scoreable_recovery` on branch `controllergate-v1.7-alpha-real-trace-pilot`.\n\n"
        "Expected artifact: `v2_8k_bugsinpy_third_scoreable_recovery_artifacts`.\n",
    )
    write_text(
        OUTPUT_DIR / "campaign_summary.md",
        "# v2.8k BugsInPy Third Scoreable Episode Recovery\n\n"
        "Local checkpoint status: `blocked_pending_v2_8k_third_scoreable_recovery_artifact`.\n\n"
        "The Linux runner is implemented and targets `black:8` as the missing third scoreable BugsInPy episode. Full scoring remains disallowed, memory lift is not demonstrated, and self-maintaining software remains undemonstrated.\n",
    )
    update_summary()
    write_manifest(OUTPUT_DIR)


def main() -> int:
    prepare()
    print("v2.8k BugsInPy third scoreable recovery outputs prepared")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
