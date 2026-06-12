#!/usr/bin/env python3
"""Prepare v2.8i BugsInPy boolean patch construction fix outputs."""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = REPO_ROOT / "outputs" / "v2_8i_bugsinpy_boolean_patch_construction_fix"
RERUN_DIR = REPO_ROOT / "outputs" / "v2_8i_bugsinpy_real_bug_boolean_patch_comparison"
SUMMARY = REPO_ROOT / "controllergate_v1_7_beta" / "reports" / "critic_review_package" / "shareable_summary.md"
V28H_OUTPUT_DIR = REPO_ROOT / "outputs" / "v2_8h_bugsinpy_targeted_boolean_patch_heuristic"
V28H_RERUN_DIR = REPO_ROOT / "outputs" / "v2_8h_bugsinpy_real_bug_targeted_patch_comparison"

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
    h_campaign = load_json(V28H_RERUN_DIR / "campaign_results.json")
    h_inconsistency = load_json(V28H_OUTPUT_DIR / "v2_8h_boolean_heuristic_inconsistency.json")
    section = f"""## v2.8i BugsInPy Boolean Patch Construction Fix

v2.8h registered the boolean heuristic but failed patch construction despite detecting the unary operator block. v2.8i fixes the boolean patch construction path. The fix searches the full `youtube_dl/utils.py` file and patches the bounded `UNARY_OPERATORS` region.

- v2.8h artifact ingestion: preserved.
- v2.8h aggregate: `{h_campaign.get("aggregate_result", "blocked_no_safe_patch_candidate_generated")}`.
- Boolean heuristic registration: {str(h_inconsistency.get("heuristic_registered", True)).lower()}.
- Unary block detection: {str(h_inconsistency.get("unary_operator_block_found", True)).lower()}.
- Patch-construction fix status: implemented in the v2.8i runner, pending GitHub Actions execution.
- v2.8i repair comparison executed: false in this local checkpoint.
- Scoreable episodes: 0.
- Positive memory episodes: 0.
- Aggregate result: `blocked_pending_v2_8i_boolean_patch_construction_fix_artifact`.
- Full scoring: NOT_RUN / disallowed.
- Memory lift: not demonstrated.
- Self-maintaining software: not demonstrated.

A no-memory and memory-enabled tie is inconclusive, not memory lift. A first scoreable BugsInPy repair episode would be progress even without memory lift.
"""
    marker = "## v2.8i BugsInPy Boolean Patch Construction Fix"
    text = SUMMARY.read_text(encoding="utf-8") if SUMMARY.exists() else ""
    if marker in text:
        start = text.index(marker)
        next_start = text.find("\n## ", start + 1)
        tail = text[next_start:].lstrip() if next_start != -1 else ""
        text = text[:start].rstrip() + "\n\n" + section + ("\n\n" + tail if tail else "")
    else:
        text = text.rstrip() + "\n\n" + section
    write_text(SUMMARY, text)


def copy_v28h_preservation() -> None:
    write_json(OUTPUT_DIR / "v2_8h_artifact_ingestion_summary.json", load_json(V28H_OUTPUT_DIR / "v2_8h_artifact_ingestion_summary.json"))
    write_json(OUTPUT_DIR / "v2_8h_artifact_sha256_verification.json", load_json(V28H_OUTPUT_DIR / "v2_8h_artifact_sha256_verification.json"))
    write_json(OUTPUT_DIR / "v2_8h_result_preservation.json", load_json(V28H_OUTPUT_DIR / "v2_8h_result_preservation.json"))
    write_json(OUTPUT_DIR / "episode_prior_status_table.json", load_json(V28H_OUTPUT_DIR / "v2_8h_episode_result_table.json"))
    write_json(OUTPUT_DIR / "v2_8h_boolean_heuristic_inconsistency.json", load_json(V28H_OUTPUT_DIR / "v2_8h_boolean_heuristic_inconsistency.json"))
    write_text(
        OUTPUT_DIR / "v2_8h_boolean_heuristic_inconsistency_report.md",
        "# v2.8h Boolean Heuristic Inconsistency\n\nv2.8h successfully registered the boolean heuristic and detected that the unary operator block exists, but both no-memory and memory-enabled candidate generation failed with `expected UNARY_OPERATORS block not found`. v2.8i fixes this patch-construction mismatch by searching the full `youtube_dl/utils.py` file and patching the bounded unary-operator region.\n",
    )


def write_fix_design() -> None:
    write_json(
        OUTPUT_DIR / "boolean_patch_construction_fix_design.json",
        {
            "fix_id": "v2_8i_full_source_unary_operator_patch_construction",
            "candidate_scope": "youtube-dl:1",
            "source_file": "youtube_dl/utils.py",
            "problem": "v2.8h context detected the unary block, but candidate generation failed exact block lookup",
            "fix": "read full source file, locate UNARY_OPERATORS region, verify positive/negative lambdas, patch only those two lambdas",
            "fixed_or_gold_patch_allowed": False,
            "future_outcome_evidence_allowed": False,
            "tests_may_be_modified": False,
        },
    )
    write_json(
        OUTPUT_DIR / "full_source_patch_search_policy.json",
        {
            "search_scope": "full buggy youtube_dl/utils.py source file",
            "forbidden_scope": ["fixed revision", "gold patch", "test modifications", "future outcome logs"],
            "fallback_strategy": [
                "exact block match",
                "bounded UNARY_OPERATORS region search",
                "line-level lambda replacement after equivalence check",
            ],
        },
    )
    write_text(
        OUTPUT_DIR / "unary_operator_region_extract.txt",
        "Pending Linux runner execution. Expected source region:\nUNARY_OPERATORS = {\n    '': lambda v: v is not None,\n    '!': lambda v: v is None,\n}\n",
    )
    write_json(
        OUTPUT_DIR / "unary_operator_region_match_check.json",
        {
            "workflow_executed": False,
            "full_source_search_policy_defined": True,
            "region_match_pending_linux_runner": True,
        },
    )
    write_json(
        OUTPUT_DIR / "boolean_patch_generation_result.json",
        {
            "workflow_executed": False,
            "patch_generation_pending_linux_runner": True,
            "expected_patch_file": "youtube_dl/utils.py",
        },
    )
    write_json(
        OUTPUT_DIR / "boolean_patch_safety_check.json",
        {
            "workflow_executed": False,
            "patch_only_file": "youtube_dl/utils.py",
            "modifies_tests": False,
            "uses_fixed_revision": False,
            "uses_gold_patch": False,
            "uses_future_outcome_evidence": False,
        },
    )
    for prefix in ["no_memory", "memory_enabled"]:
        write_json(
            OUTPUT_DIR / f"{prefix}_boolean_patch_generation_result.json",
            {
                "workflow_executed": False,
                "patch_generation_pending_linux_runner": True,
                "expected_patch_file": "youtube_dl/utils.py",
                "full_source_search_required": True,
                "fixed_or_gold_patch_used": False,
                "future_outcome_evidence_used": False,
            },
        )
        write_json(
            OUTPUT_DIR / f"{prefix}_boolean_patch_safety_check.json",
            {
                "workflow_executed": False,
                "patch_only_file": "youtube_dl/utils.py",
                "modifies_tests": False,
                "uses_fixed_revision": False,
                "uses_gold_patch": False,
                "uses_future_outcome_evidence": False,
            },
        )
        write_text(OUTPUT_DIR / f"{prefix}_boolean_patch_candidate.diff", "# PENDING LINUX RUNNER PATCH CANDIDATE\n")


def write_pending_campaign() -> None:
    if RERUN_DIR.exists():
        shutil.rmtree(RERUN_DIR)
    RERUN_DIR.mkdir(parents=True, exist_ok=True)
    write_json(
        RERUN_DIR / "campaign_plan.json",
        {
            "campaign_id": "v2_8i_bugsinpy_boolean_patch_construction_fix",
            "workflow": ".github/workflows/v2_8i_bugsinpy_boolean_patch_construction_fix.yml",
            "runner": "scripts/v2_8i_bugsinpy_boolean_patch_construction_fix_runner.py",
            "candidate_ids": CANDIDATES,
            "full_source_boolean_patch_construction_fix_enabled": True,
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
    write_json(RERUN_DIR / "targeted_boolean_patch_summary.json", {"workflow_executed": False, "construction_fix_enabled": True, "youtube_dl_patch_attempted": False})
    write_json(
        RERUN_DIR / "campaign_results.json",
        {
            "workflow_executed": False,
            "executed_episode_count": 0,
            "scoreable_episode_count": 0,
            "positive_memory_episode_count": 0,
            "blocked_episode_count": 0,
            "aggregate_result": "blocked_pending_v2_8i_boolean_patch_construction_fix_artifact",
            "limited_bugsinpy_real_bug_memory_lift_criteria_met": False,
            "full_scoring_allowed": False,
            "controllergate_full_scoring": "NOT_RUN",
            "self_maintaining_software_demonstrated": False,
        },
    )
    write_json(
        RERUN_DIR / "aggregate_bugsinpy_real_bug_memory_lift_assessment.json",
        {
            "aggregate_result": "blocked_pending_v2_8i_boolean_patch_construction_fix_artifact",
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
        "# v2.8i BugsInPy Boolean Patch Construction Fix\n\nThe boolean patch construction fix workflow is ready but has not been executed in this local checkpoint. Run `v2_8i_bugsinpy_boolean_patch_construction_fix` in GitHub Actions and ingest the artifact before any memory-lift claim.\n",
    )


def prepare() -> None:
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    copy_v28h_preservation()
    write_fix_design()
    write_pending_campaign()
    update_summary()
    write_manifest(OUTPUT_DIR)
    write_manifest(RERUN_DIR)


def main() -> int:
    prepare()
    print("v2.8i BugsInPy boolean patch construction fix outputs prepared")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
