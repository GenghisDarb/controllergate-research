#!/usr/bin/env python3
"""Prepare v2.8g BugsInPy source-discovery repair proposer outputs."""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = REPO_ROOT / "outputs" / "v2_8g_bugsinpy_source_discovery_repair_proposer"
RERUN_DIR = REPO_ROOT / "outputs" / "v2_8g_bugsinpy_real_bug_source_discovery_repair_comparison"
SUMMARY = REPO_ROOT / "controllergate_v1_7_beta" / "reports" / "critic_review_package" / "shareable_summary.md"
V28F_OUTPUT_DIR = REPO_ROOT / "outputs" / "v2_8f_bugsinpy_bounded_repair_proposer"
V28F_RERUN_DIR = REPO_ROOT / "outputs" / "v2_8f_bugsinpy_real_bug_bounded_repair_comparison"

CANDIDATES = ["youtube-dl:1", "black:8", "black:4"]
V28F_REPORTED_ARTIFACT_SHA256 = "0b0e88577d872443dc0bec734f21d1da2c4ac12fc71c161a00534f96ab59aece"


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
    v28f_campaign = load_json(V28F_RERUN_DIR / "campaign_results.json")
    v28f_aggregate = v28f_campaign.get("aggregate_result", "blocked_no_safe_patch_candidate_generated")
    section = f"""## v2.8g BugsInPy Source-Discovery Repair Proposer

v2.8f proved the bounded proposer ran under valid replay/workspace gates, but it produced 0 scoreable episodes because no safe patch candidate was generated. That is a source-discovery and heuristic-coverage gap, not negative ControllerGate repair evidence.

v2.8g adds decision-time symbol/source discovery and targeted safe heuristics for the same three BugsInPy real-bug candidates:

- `youtube-dl:1`
- `black:8`
- `black:4`

Current v2.8g status: workflow ready, pending GitHub Actions execution.

- v2.8f artifact inspection: preserved.
- v2.8f aggregate: `{v28f_aggregate}`.
- v2.8f episode classification: `blocked_no_safe_patch_candidate_generated`.
- v2.8g source-discovery repair proposer: implemented.
- v2.8g repair comparison: pending Linux runner artifact.
- Scoreable v2.8g episodes: 0 at this checkpoint.
- Full scoring: NOT_RUN / disallowed.
- Memory lift: not demonstrated.
- Self-maintaining software: not demonstrated.

No-patch/no-action outcomes are not scoreable repair evidence. Candidate generation may not use fixed/gold patches, future outcome evidence, or fixed-state diagnostic hints.
"""
    marker = "## v2.8g BugsInPy Source-Discovery Repair Proposer"
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
    v28f_ingestion = load_json(V28F_OUTPUT_DIR / "v2_8f_artifact_ingestion_summary.json")
    v28f_verification = load_json(V28F_OUTPUT_DIR / "v2_8f_artifact_sha256_verification.json")
    v28f_campaign = load_json(V28F_RERUN_DIR / "campaign_results.json")
    v28f_table = load_json(V28F_OUTPUT_DIR / "v2_8f_episode_result_table.json")
    write_json(
        OUTPUT_DIR / "v2_8f_artifact_ingestion_summary.json",
        v28f_ingestion
        or {
            "artifact_name": "v2_8f_bugsinpy_bounded_repair_proposer_artifacts",
            "reported_artifact_sha256": V28F_REPORTED_ARTIFACT_SHA256,
            "local_zip_available_for_reverification": False,
            "preservation_source": "user_provided_manual_artifact_inspection_record",
            "files_ok_reported": 199,
            "hash_failures_reported": 0,
            "workflow_executed_reported": True,
            "note": "The v2.8f artifact zip was not locally available in this checkpoint; v2.8g preserves the supplied inspection record without claiming local zip re-verification.",
        },
    )
    write_json(
        OUTPUT_DIR / "v2_8f_artifact_sha256_verification.json",
        v28f_verification
        or {
            "verification_recorded": True,
            "verification_source": "manual_inspection_record_from_user",
            "files_ok": 199,
            "hash_failures": 0,
            "sha256_manifest_clean": True,
            "local_reverification_performed": False,
            "reported_artifact_sha256": V28F_REPORTED_ARTIFACT_SHA256,
        },
    )
    write_json(
        OUTPUT_DIR / "v2_8f_result_preservation.json",
        {
            "workflow_executed": v28f_campaign.get("workflow_executed", True),
            "executed_episode_count": v28f_campaign.get("executed_episode_count", 3),
            "scoreable_episode_count": v28f_campaign.get("scoreable_episode_count", 0),
            "blocked_episode_count": v28f_campaign.get("blocked_episode_count", 3),
            "aggregate_result": v28f_campaign.get("aggregate_result", "blocked_no_safe_patch_candidate_generated"),
            "episode_classification": "blocked_no_safe_patch_candidate_generated",
            "positive_memory_episode_count": v28f_campaign.get("positive_memory_episode_count", 0),
            "corruption_count": v28f_campaign.get("corruption_count", 0),
            "decision_time_outcome_overlap_count": v28f_campaign.get("decision_time_outcome_overlap_count", 0),
            "label_leakage_count": v28f_campaign.get("label_leakage_count", 0),
            "full_scoring_allowed": False,
            "controllergate_full_scoring": "NOT_RUN",
            "self_maintaining_software_demonstrated": False,
            "memory_lift_demonstrated": False,
        },
    )
    write_text(
        OUTPUT_DIR / "v2_8f_bounded_proposer_success_report.md",
        "# v2.8f Bounded Proposer Success\n\nv2.8f successfully ran the bounded repair proposer under valid replay/workspace gates. Candidate promotion, checkout/runtime, target replay, exact workspace preservation, no-memory prerepair replay, and memory-enabled prerepair replay were preserved.\n",
    )
    write_text(
        OUTPUT_DIR / "v2_8f_blocked_patch_generation_report.md",
        "# v2.8f Blocked Patch Generation\n\nv2.8f did not demonstrate repair success or memory lift. All three episodes remained `blocked_no_safe_patch_candidate_generated`; this isolates insufficient source-discovery and repair-heuristic coverage as the next blocker.\n",
    )
    write_json(
        OUTPUT_DIR / "episode_prior_status_table.json",
        v28f_table
        or {
            "youtube-dl:1": {
                "classification": "blocked_no_safe_patch_candidate_generated",
                "blocker": "def match_str not found in inspected buggy files",
                "next_fix": "source definition discovery from failing test imports and workspace symbol index",
            },
            "black:8": {
                "classification": "blocked_no_safe_patch_candidate_generated",
                "blocker": "no safe localized parser/formatter patch heuristic registered",
                "next_fix": "decision-time source ranking and conservative parser/formatter heuristic gate",
            },
            "black:4": {
                "classification": "blocked_no_safe_patch_candidate_generated",
                "blocker": "no safe localized newline/backslash formatting heuristic registered",
                "next_fix": "decision-time source ranking and conservative leading-newline heuristic gate",
            },
        },
    )
    write_json(
        OUTPUT_DIR / "source_discovery_design.json",
        {
            "inputs_allowed": [
                "failing command",
                "raw failing log",
                "stack traces from failing log",
                "failing test file content in buggy workspace",
                "source files in buggy workspace",
                "project imports from buggy workspace",
                "allowed memory evidence for memory-enabled prioritization",
            ],
            "inputs_forbidden": [
                "fixed revision",
                "gold patch",
                "known repair diff",
                "future passing logs",
                "fixed-state diagnostic hints",
            ],
            "steps": [
                "parse failing command",
                "locate failing test file",
                "extract test method symbols and call targets",
                "parse traceback frames",
                "build symbol index over buggy workspace",
                "rank local source files",
                "record inspected files and ranking reasons",
            ],
        },
    )
    write_json(
        OUTPUT_DIR / "symbol_index_policy.json",
        {
            "indexed_entities": ["python_function_definitions", "class_definitions", "method_definitions", "imported_names", "assignment_targets"],
            "workspace_scope": "buggy_checkout_only",
            "fixed_or_gold_patch_allowed": False,
        },
    )
    write_json(
        OUTPUT_DIR / "source_ranking_policy.json",
        {
            "ranking_signals": [
                "traceback_frame_occurrence",
                "imported_symbol_relation",
                "function_or_method_name_match",
                "assertion_or_call_target_relation",
                "proximity_to_failing_test",
                "project_source_priority_over_tests",
            ],
        },
    )
    write_json(
        OUTPUT_DIR / "source_discovery_budget.json",
        {
            "max_indexed_files": 1200,
            "max_inspected_candidate_source_files": 40,
            "max_candidate_functions": 20,
            "max_patch_candidates": 2,
        },
    )
    write_json(
        OUTPUT_DIR / "repair_heuristic_registry.json",
        {
            "boolean_value_matching_failure": {"candidate": "youtube-dl:1", "requires_symbol": "match_str"},
            "parser_formatter_localized_failure": {"candidate": "black:8", "safe_patch_required": True},
            "leading_newline_backslash_formatting_failure": {"candidate": "black:4", "safe_patch_required": True},
        },
    )
    write_json(
        OUTPUT_DIR / "repair_heuristic_safety_policy.json",
        {
            "max_changed_source_files": 1,
            "max_changed_lines": 12,
            "tests_may_be_modified": False,
            "generated_artifacts_may_be_modified": False,
            "fixed_or_gold_patch_allowed": False,
            "future_outcome_evidence_allowed": False,
            "patch_must_be_reversible": True,
        },
    )
    write_json(
        OUTPUT_DIR / "patch_candidate_ranking_policy.json",
        {
            "prefer_minimal_local_patch": True,
            "prefer_target_source_file": True,
            "prefer_low_changed_line_count": True,
            "prefer_no_corruption_risk": True,
            "no_patch_when_uncertain": True,
        },
    )
    write_manifest(OUTPUT_DIR)


def prepare_rerun_bundle() -> None:
    if RERUN_DIR.exists():
        shutil.rmtree(RERUN_DIR)
    RERUN_DIR.mkdir(parents=True, exist_ok=True)
    write_json(
        RERUN_DIR / "campaign_plan.json",
        {
            "campaign_id": "v2_8g_bugsinpy_real_bug_source_discovery_repair_comparison",
            "workflow": ".github/workflows/v2_8g_bugsinpy_source_discovery_repair_proposer.yml",
            "runner": "scripts/v2_8g_bugsinpy_source_discovery_repair_proposer_runner.py",
            "candidate_ids": CANDIDATES,
            "source_discovery_enabled": True,
            "targeted_safe_heuristics_enabled": True,
            "full_scoring_allowed": False,
            "controllergate_full_scoring": "NOT_RUN",
            "self_maintaining_software_demonstrated": False,
        },
    )
    write_json(RERUN_DIR / "candidate_source_integrity_check.json", {"candidate_count": 3, "candidate_ids": CANDIDATES, "blocked_candidates_executed": False})
    write_json(RERUN_DIR / "pre_repair_replay_gate_summary.json", {"workflow_executed": False, "passed_count": 0})
    write_json(RERUN_DIR / "workspace_equivalence_summary.json", {"workflow_executed": False, "workspace_equivalence_passed_count": 0})
    write_json(RERUN_DIR / "repair_attempt_summary.json", {"workflow_executed": False, "patch_candidate_generated_count": 0, "post_repair_outcome_count": 0})
    write_json(RERUN_DIR / "source_discovery_summary.json", {"workflow_executed": False, "source_discovery_runner_ready": True, "match_str_required_for_youtube_dl": True})
    write_json(RERUN_DIR / "bounded_repair_proposer_summary.json", {"workflow_executed": False, "proposer_ready": True, "pending_artifact": "v2_8g_bugsinpy_source_discovery_repair_proposer_artifacts"})
    write_json(
        RERUN_DIR / "campaign_results.json",
        {
            "workflow_executed": False,
            "executed_episode_count": 0,
            "scoreable_episode_count": 0,
            "positive_memory_episode_count": 0,
            "blocked_episode_count": 0,
            "aggregate_result": "blocked_pending_v2_8g_source_discovery_repair_proposer_artifact",
            "limited_bugsinpy_real_bug_memory_lift_criteria_met": False,
            "full_scoring_allowed": False,
            "controllergate_full_scoring": "NOT_RUN",
            "self_maintaining_software_demonstrated": False,
        },
    )
    write_json(
        RERUN_DIR / "aggregate_bugsinpy_real_bug_memory_lift_assessment.json",
        {
            "aggregate_result": "blocked_pending_v2_8g_source_discovery_repair_proposer_artifact",
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
        "# v2.8g BugsInPy Source-Discovery Repair Proposer\n\nThe source-discovery repair proposer workflow is ready but has not been executed in this local checkpoint. Run `v2_8g_bugsinpy_source_discovery_repair_proposer` in GitHub Actions and ingest the artifact before making any memory-lift claim.\n",
    )
    write_manifest(RERUN_DIR)


def main() -> int:
    prepare_phase_a()
    prepare_rerun_bundle()
    update_summary()
    print("v2.8g BugsInPy source-discovery repair proposer bundle prepared")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
