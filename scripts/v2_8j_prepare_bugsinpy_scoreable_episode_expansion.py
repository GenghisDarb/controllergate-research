#!/usr/bin/env python3
"""Prepare local v2.8j BugsInPy scoreable episode expansion outputs."""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = REPO_ROOT / "outputs" / "v2_8j_bugsinpy_scoreable_episode_expansion"
SUMMARY = REPO_ROOT / "controllergate_v1_7_beta" / "reports" / "critic_review_package" / "shareable_summary.md"
V28I_DIR = REPO_ROOT / "outputs" / "v2_8i_bugsinpy_real_bug_boolean_patch_comparison"

CANDIDATES = [
    {"episode_id": "episode_001", "candidate": "youtube-dl:1", "prior_v2_8i_classification": "inconclusive_equal_performance", "prior_v2_8i_scoreable": True},
    {"episode_id": "episode_002", "candidate": "black:8", "prior_v2_8i_classification": "blocked_no_safe_patch_candidate_generated", "prior_v2_8i_scoreable": False},
    {"episode_id": "episode_003", "candidate": "black:4", "prior_v2_8i_classification": "blocked_no_safe_patch_candidate_generated", "prior_v2_8i_scoreable": False},
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
    prior = load_json(V28I_DIR / "campaign_results.json")
    section = f"""## v2.8j BugsInPy Scoreable Episode Expansion

v2.8j adds a Linux runner for scoreable BugsInPy episode expansion after the v2.8i boolean patch construction fix. The runner preserves `youtube-dl:1` as the first scoreable reference episode and attempts bounded source-only candidate generation for `black:8` and `black:4`.

- v2.8i scoreable reference episodes: {prior.get("scoreable_episode_count", 1)}.
- v2.8j local workflow status: pending GitHub Actions artifact.
- Candidate set: `youtube-dl:1`, `black:8`, `black:4`.
- Black candidate generators: source-only, bounded, buggy-source/failing-context only.
- Test edits as repair candidates: disallowed.
- Full scoring: NOT_RUN / disallowed.
- Memory lift: not demonstrated.
- Self-maintaining software: not demonstrated.

Candidate promotion or patch generation is not repair success. Scoreable evidence requires post-repair target validation logs from the Linux runner.
"""
    marker = "## v2.8j BugsInPy Scoreable Episode Expansion"
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
            "campaign_id": "v2_8j_bugsinpy_scoreable_episode_expansion",
            "workflow": ".github/workflows/v2_8j_bugsinpy_scoreable_episode_expansion.yml",
            "runner": "scripts/v2_8j_bugsinpy_scoreable_episode_expansion_runner.py",
            "candidate_ids": [item["candidate"] for item in CANDIDATES],
            "goal": "expand BugsInPy limited pilot from one scoreable episode toward at least three scoreable episodes",
            "local_status": "pending_linux_runner_artifact",
            "full_scoring_allowed": False,
            "controllergate_full_scoring": "NOT_RUN",
            "self_maintaining_software_demonstrated": False,
        },
    )
    write_json(OUTPUT_DIR / "candidate_pool.json", {"records": CANDIDATES})
    write_json(
        OUTPUT_DIR / "previous_v2_8i_scoreable_reference.json",
        {
            "candidate": "youtube-dl:1",
            "classification": "inconclusive_equal_performance",
            "scoreable": True,
            "memory_enabled_outperformed_no_memory": False,
            "interpretation": "scoreable reference episode, not memory lift",
        },
    )
    write_json(
        OUTPUT_DIR / "source_repair_vs_harness_separation.json",
        {
            "source_repair_candidate_patch_files": ["*_source_only_repair_patch.diff", "*_repair_patch.diff"],
            "failing_test_materialization_or_replay_harness_changes": "separate runtime setup/checkouts only; not repair candidates",
            "tests_may_be_modified_as_repair": False,
            "dependency_runtime_setup_is_not_code_repair": True,
        },
    )
    write_json(
        OUTPUT_DIR / "scoreable_episode_expansion_policy.json",
        {
            "scoreable_requires_patch_generated": True,
            "scoreable_requires_source_patch_applies": True,
            "scoreable_requires_target_test_executes": True,
            "scoreable_requires_target_test_passes_in_at_least_one_arm": True,
            "no_patch_or_no_op_is_scoreable": False,
            "classification_vocabulary": [
                "positive_memory_only",
                "no_memory_only",
                "inconclusive_equal_performance",
                "failed_both",
                "blocked_no_safe_patch_candidate_generated",
                "blocked_patch_did_not_apply",
                "blocked_target_test_failed",
                "blocked_replay_or_materialization_failure",
            ],
        },
    )
    write_json(
        OUTPUT_DIR / "black_candidate_generation_policy.json",
        {
            "black:8": "bounded black.py format_str post-format guard from comments7 parse/assertion context",
            "black:4": "bounded black.py format_str leading-backslash leading-newline guard",
            "source_only": True,
            "fixed_or_gold_patch_used": False,
            "future_outcome_evidence_used": False,
            "can_fail_safely_without_becoming_scoreable": True,
        },
    )
    write_json(
        OUTPUT_DIR / "decision_report.json",
        {
            "workflow_executed": False,
            "records": [
                {"episode_id": item["episode_id"], "candidate": item["candidate"], "classification": "pending_linux_runner_artifact", "scoreable": False}
                for item in CANDIDATES
            ],
        },
    )
    write_json(
        OUTPUT_DIR / "aggregate_report.json",
        {
            "workflow_executed": False,
            "aggregate_result": "blocked_pending_v2_8j_scoreable_episode_expansion_artifact",
            "executed_episode_count": 0,
            "scoreable_episode_count": 0,
            "positive_memory_only_episode_count": 0,
            "full_scoring_allowed": False,
            "controllergate_full_scoring": "NOT_RUN",
            "self_maintaining_software_demonstrated": False,
        },
    )
    write_json(
        OUTPUT_DIR / "campaign_results.json",
        {
            "workflow_executed": False,
            "executed_episode_count": 0,
            "scoreable_episode_count": 0,
            "positive_memory_episode_count": 0,
            "aggregate_result": "blocked_pending_v2_8j_scoreable_episode_expansion_artifact",
            "limited_bugsinpy_real_bug_memory_lift_criteria_met": False,
            "full_scoring_allowed": False,
            "controllergate_full_scoring": "NOT_RUN",
            "self_maintaining_software_demonstrated": False,
        },
    )
    write_json(
        OUTPUT_DIR / "aggregate_bugsinpy_real_bug_memory_lift_assessment.json",
        {
            "aggregate_result": "blocked_pending_v2_8j_scoreable_episode_expansion_artifact",
            "scoreable_episode_count": 0,
            "positive_memory_episode_count": 0,
            "minimum_required_scoreable_episodes": 3,
            "limited_bugsinpy_real_bug_memory_lift_criteria_met": False,
            "full_scoring_allowed": False,
            "controllergate_full_scoring": "NOT_RUN",
            "self_maintaining_software_demonstrated": False,
        },
    )
    write_json(OUTPUT_DIR / "label_hygiene_check.json", {"campaign_label": "v2.8j", "current_artifact_uses_v2_8j_names": True, "older_version_labels_allowed_only_as_history": True})
    write_json(OUTPUT_DIR / "audit.json", {"local_preparation_audit_equivalent": True, "pending_linux_runner_artifact": True})
    for item in CANDIDATES:
        episode_dir = OUTPUT_DIR / item["episode_id"]
        write_json(episode_dir / "episode_metadata.json", item | {"classification": "pending_linux_runner_artifact", "scoreable": False})
        write_text(episode_dir / "no_memory_source_only_repair_patch.diff", "# PENDING LINUX RUNNER\n")
        write_text(episode_dir / "memory_enabled_source_only_repair_patch.diff", "# PENDING LINUX RUNNER\n")
        write_json(episode_dir / "repair_materialization_separation.json", {"tests_may_be_modified_as_repair": False, "source_only_patch_required": True})
    write_text(
        OUTPUT_DIR / "verification_commands.md",
        "# v2.8j Verification\n\n"
        "- Run GitHub Actions workflow `v2_8j_bugsinpy_scoreable_episode_expansion`.\n"
        "- Download artifact `v2_8j_bugsinpy_scoreable_episode_expansion_artifacts`.\n"
        "- Verify `SHA256SUMS.txt` inside the artifact.\n"
        "- Confirm `decision_report.json` and `aggregate_report.json` reproduce campaign summary counts.\n"
        "- Confirm source-only repair patches are separate from replay/materialization artifacts.\n",
    )
    write_text(
        OUTPUT_DIR / "campaign_summary.md",
        "# v2.8j BugsInPy Scoreable Episode Expansion\n\n"
        "Local checkpoint status: `blocked_pending_v2_8j_scoreable_episode_expansion_artifact`.\n\n"
        "The v2.8j Linux runner is implemented and ready to run. It preserves `youtube-dl:1` as a scoreable reference from v2.8i, then attempts source-only bounded repair candidates for `black:8` and `black:4`. Full scoring remains disallowed, memory lift is not demonstrated, and self-maintaining software remains undemonstrated.\n",
    )
    update_summary()
    write_manifest(OUTPUT_DIR)


def main() -> int:
    prepare()
    print("v2.8j BugsInPy scoreable episode expansion outputs prepared")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
