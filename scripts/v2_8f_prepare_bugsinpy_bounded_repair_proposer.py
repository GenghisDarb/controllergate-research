#!/usr/bin/env python3
"""Prepare v2.8f BugsInPy bounded repair proposer outputs."""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
INPUT_DIR = REPO_ROOT / "outputs" / "v2_8e_bugsinpy_repair_workspace_preservation"
OUTPUT_DIR = REPO_ROOT / "outputs" / "v2_8f_bugsinpy_bounded_repair_proposer"
RERUN_DIR = REPO_ROOT / "outputs" / "v2_8f_bugsinpy_real_bug_bounded_repair_comparison"
SUMMARY = REPO_ROOT / "controllergate_v1_7_beta" / "reports" / "critic_review_package" / "shareable_summary.md"


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
    section = """## v2.8f BugsInPy Bounded Repair Proposer

v2.8e fixed workspace preservation and confirmed prerepair target failures in both no-memory and memory-enabled repair workspaces. v2.8e still produced 0 scoreable episodes because no safe repair candidate was generated.

v2.8f adds a bounded decision-time-only repair proposer workflow. The proposer may inspect only buggy checkout files, failing logs, failing tests, local project context, and allowed ControllerGate memory evidence for the memory-enabled path. BugsInPy fixed revisions, gold patches, known repair diffs, and future outcome evidence remain forbidden.

- v2.8e artifact ingestion: preserved.
- v2.8e workspace preservation success: preserved.
- v2.8e blocked reason: `blocked_no_repair_candidate_generated`.
- v2.8f bounded repair proposer status: workflow ready, pending GitHub Actions execution.
- v2.8f repair scoring: NOT RUN in this local checkpoint.
- Full scoring: NOT_RUN / disallowed.
- Memory lift: not demonstrated.
- Self-maintaining software: not demonstrated.

No-patch/no-action outcomes are not scoreable repair evidence. Candidate generation may not use fixed/gold patches.
"""
    marker = "## v2.8f BugsInPy Bounded Repair Proposer"
    text = SUMMARY.read_text(encoding="utf-8") if SUMMARY.exists() else ""
    if marker in text:
        text = text[: text.index(marker)].rstrip() + "\n\n" + section
    else:
        text = text.rstrip() + "\n\n" + section
    write_text(SUMMARY, text)


def prepare_phase_a() -> None:
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    v28e_ingestion = load_json(INPUT_DIR / "v2_8e_artifact_ingestion_summary.json")
    v28e_verification = load_json(INPUT_DIR / "v2_8e_artifact_sha256_verification.json")
    v28e_campaign = load_json(INPUT_DIR / "campaign_results.json")
    v28e_workspace = load_json(INPUT_DIR / "v2_8e_workspace_preservation_result.json")
    v28e_episode_table = load_json(INPUT_DIR / "v2_8e_episode_result_table.json")
    write_json(OUTPUT_DIR / "v2_8e_artifact_ingestion_summary.json", v28e_ingestion)
    write_json(OUTPUT_DIR / "v2_8e_artifact_sha256_verification.json", v28e_verification)
    write_json(
        OUTPUT_DIR / "v2_8e_result_preservation.json",
        {
            "preserved_aggregate_result": v28e_campaign.get("aggregate_result"),
            "preserved_scoreable_episode_count": v28e_campaign.get("scoreable_episode_count"),
            "preserved_positive_memory_episode_count": v28e_campaign.get("positive_memory_episode_count"),
            "workspace_preservation_success": v28e_workspace.get("all_repair_workspaces_preserved_target_failure"),
            "repair_success_demonstrated": False,
            "memory_lift_demonstrated": False,
            "self_maintaining_software_demonstrated": False,
            "full_scoring_allowed": False,
            "controllergate_full_scoring": "NOT_RUN",
        },
    )
    write_text(
        OUTPUT_DIR / "v2_8e_workspace_preservation_success_report.md",
        "# v2.8e Workspace Preservation Success\n\nv2.8e fixed checkout, target replay, and repair workspace preservation. Baseline, no-memory, and memory-enabled workspace manifests matched, and both repair workspaces reproduced the target failure before repair for all three promoted BugsInPy candidates.\n",
    )
    write_text(
        OUTPUT_DIR / "v2_8e_blocked_candidate_generation_report.md",
        "# v2.8e Blocked Candidate Generation\n\nv2.8e did not demonstrate repair success or memory lift. The isolated blocker is that neither no-memory nor memory-enabled paths generated safe bounded repair candidates, so all episodes remained `blocked_no_repair_candidate_generated` and not scoreable.\n",
    )
    write_json(OUTPUT_DIR / "episode_prior_status_table.json", v28e_episode_table)
    write_json(
        OUTPUT_DIR / "bounded_repair_proposer_design.json",
        {
            "proposer_id": "v2_8f_bounded_decision_time_repair_proposer",
            "purpose": "generate minimal candidate patches from allowed decision-time inputs when a safe heuristic applies",
            "uses_fixed_or_gold_patch": False,
            "uses_future_outcome_evidence": False,
            "candidate_specific_hints": {
                "youtube-dl:1": "inspect def match_str and false boolean handling only in buggy checkout",
                "black:8": "inspect test_comments7 and local parser/formatting functions only in buggy checkout",
                "black:4": "inspect test_beginning_backslash and local newline/backslash formatting only in buggy checkout",
            },
            "fallback_when_unclear": "blocked_no_safe_patch_candidate_generated",
        },
    )
    write_json(
        OUTPUT_DIR / "repair_budget_policy.json",
        {
            "max_inspected_files": 25,
            "max_candidate_patches": 2,
            "max_changed_files": 1,
            "max_changed_lines": 8,
            "max_repair_actions": 8,
            "same_budget_for_no_memory_and_memory_enabled": True,
        },
    )
    write_json(
        OUTPUT_DIR / "decision_time_allowed_inputs_policy.json",
        {
            "allowed_inputs": [
                "buggy checkout source files",
                "failing command",
                "raw failing log",
                "failing test file content from buggy workspace",
                "source file content from buggy workspace",
                "local project context available in buggy checkout",
                "allowed ControllerGate memory evidence for memory-enabled path only",
            ]
        },
    )
    write_json(
        OUTPUT_DIR / "forbidden_inputs_policy.json",
        {
            "forbidden_inputs": [
                "BugsInPy fixed revision",
                "BugsInPy gold patch",
                "known repair diff",
                "future passing logs",
                "manually copied fixes",
                "fixed-state diagnostic hints",
                "outcome-only evidence",
            ]
        },
    )
    write_json(
        OUTPUT_DIR / "memory_evidence_policy.json",
        {
            "no_memory_path_uses_memory": False,
            "memory_enabled_path_may_use_controllergate_memory": True,
            "memory_enabled_path_may_use_bugsinpy_fixed_patch": False,
        },
    )
    write_json(
        OUTPUT_DIR / "repair_candidate_generation_policy.json",
        {
            "candidate_generated_only_when_safe_heuristic_applies": True,
            "record_every_inspected_file": True,
            "record_every_generated_candidate": True,
            "no_patch_generated_is_not_scoreable": True,
            "no_patch_classifications": ["blocked_no_repair_candidate_generated", "blocked_no_safe_patch_candidate_generated"],
        },
    )
    write_manifest(OUTPUT_DIR)


def prepare_rerun_bundle() -> None:
    if RERUN_DIR.exists():
        shutil.rmtree(RERUN_DIR)
    RERUN_DIR.mkdir(parents=True, exist_ok=True)
    candidate_ids = ["youtube-dl:1", "black:8", "black:4"]
    write_json(RERUN_DIR / "campaign_plan.json", {
        "campaign_id": "v2_8f_bugsinpy_real_bug_bounded_repair_comparison",
        "workflow": ".github/workflows/v2_8f_bugsinpy_bounded_repair_proposer.yml",
        "runner": "scripts/v2_8f_bugsinpy_bounded_repair_proposer_runner.py",
        "candidate_ids": candidate_ids,
        "bounded_repair_proposer_enabled": True,
        "full_scoring_allowed": False,
        "controllergate_full_scoring": "NOT_RUN",
        "self_maintaining_software_demonstrated": False,
    })
    write_json(RERUN_DIR / "candidate_source_integrity_check.json", {"candidate_count": 3, "candidate_ids": candidate_ids})
    write_json(RERUN_DIR / "pre_repair_replay_gate_summary.json", {"workflow_executed": False, "passed_count": 0})
    write_json(RERUN_DIR / "workspace_equivalence_summary.json", {"workflow_executed": False, "workspace_equivalence_passed_count": 0})
    write_json(RERUN_DIR / "repair_attempt_summary.json", {"workflow_executed": False, "patch_candidate_generated_count": 0, "post_repair_outcome_count": 0})
    write_json(RERUN_DIR / "bounded_repair_proposer_summary.json", {"workflow_executed": False, "proposer_ready": True, "pending_artifact": "v2_8f_bugsinpy_bounded_repair_proposer_artifacts"})
    write_json(RERUN_DIR / "campaign_results.json", {
        "workflow_executed": False,
        "executed_episode_count": 0,
        "scoreable_episode_count": 0,
        "positive_memory_episode_count": 0,
        "blocked_episode_count": 0,
        "aggregate_result": "blocked_pending_v2_8f_bounded_repair_proposer_artifact",
        "limited_bugsinpy_real_bug_memory_lift_criteria_met": False,
        "full_scoring_allowed": False,
        "controllergate_full_scoring": "NOT_RUN",
        "self_maintaining_software_demonstrated": False,
    })
    write_json(RERUN_DIR / "aggregate_bugsinpy_real_bug_memory_lift_assessment.json", {
        "aggregate_result": "blocked_pending_v2_8f_bounded_repair_proposer_artifact",
        "scoreable_episode_count": 0,
        "positive_memory_episode_count": 0,
        "minimum_required_scoreable_episodes": 3,
        "limited_bugsinpy_real_bug_memory_lift_criteria_met": False,
        "full_scoring_allowed": False,
        "controllergate_full_scoring": "NOT_RUN",
        "self_maintaining_software_demonstrated": False,
    })
    write_text(RERUN_DIR / "campaign_summary.md", "# v2.8f BugsInPy Bounded Repair Proposer\n\nThe bounded repair proposer workflow is ready but has not been executed in this local checkpoint.\n")
    write_manifest(RERUN_DIR)


def main() -> int:
    prepare_phase_a()
    prepare_rerun_bundle()
    update_summary()
    print("v2.8f BugsInPy bounded repair proposer bundle prepared")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
