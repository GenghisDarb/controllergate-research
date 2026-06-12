#!/usr/bin/env python3
"""Audit v2.8g BugsInPy source-discovery repair proposer campaign."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = REPO_ROOT / "outputs" / "v2_8g_bugsinpy_source_discovery_repair_proposer"
RERUN_DIR = REPO_ROOT / "outputs" / "v2_8g_bugsinpy_real_bug_source_discovery_repair_comparison"
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "v2_8g_bugsinpy_source_discovery_repair_proposer.yml"
RUNNER = REPO_ROOT / "scripts" / "v2_8g_bugsinpy_source_discovery_repair_proposer_runner.py"
PREP = REPO_ROOT / "scripts" / "v2_8g_prepare_bugsinpy_source_discovery_repair_proposer.py"
SUMMARY = REPO_ROOT / "controllergate_v1_7_beta" / "reports" / "critic_review_package" / "shareable_summary.md"

REQUIRED_PHASE_A = [
    "v2_8f_artifact_ingestion_summary.json",
    "v2_8f_artifact_sha256_verification.json",
    "v2_8f_result_preservation.json",
    "v2_8f_bounded_proposer_success_report.md",
    "v2_8f_blocked_patch_generation_report.md",
    "episode_prior_status_table.json",
    "source_discovery_design.json",
    "symbol_index_policy.json",
    "source_ranking_policy.json",
    "source_discovery_budget.json",
    "repair_heuristic_registry.json",
    "repair_heuristic_safety_policy.json",
    "patch_candidate_ranking_policy.json",
    "SHA256SUMS.txt",
]

REQUIRED_RERUN = [
    "campaign_plan.json",
    "campaign_results.json",
    "aggregate_bugsinpy_real_bug_memory_lift_assessment.json",
    "campaign_summary.md",
    "candidate_source_integrity_check.json",
    "pre_repair_replay_gate_summary.json",
    "workspace_equivalence_summary.json",
    "repair_attempt_summary.json",
    "source_discovery_summary.json",
    "bounded_repair_proposer_summary.json",
    "SHA256SUMS.txt",
]

PRESERVED_RESULTS = [
    REPO_ROOT / "outputs" / "v2_8f_bugsinpy_real_bug_bounded_repair_comparison" / "campaign_results.json",
    REPO_ROOT / "outputs" / "v2_8e_bugsinpy_repair_workspace_preservation" / "campaign_results.json",
    REPO_ROOT / "outputs" / "v2_8d_bugsinpy_git_workspace_repair_comparison" / "campaign_results.json",
    REPO_ROOT / "outputs" / "v2_8c_bugsinpy_real_bug_repair_comparison_rerun" / "campaign_results.json",
    REPO_ROOT / "outputs" / "v2_8b_bugsinpy_repair_comparison" / "campaign_results.json",
    REPO_ROOT / "outputs" / "v2_7e_bugsinpy_third_candidate_artifact_ingestion" / "v2_8_execution_gate_decision.json",
    REPO_ROOT / "outputs" / "v2_7d_bugsinpy_third_candidate_direct_runner_expansion" / "v2_8_execution_gate_decision.json",
    REPO_ROOT / "outputs" / "v2_7b_bugsinpy_direct_target_runner_fix" / "v2_8_execution_gate_decision.json",
    REPO_ROOT / "outputs" / "v2_7_bugsinpy_target_replay_promotion_recovery" / "runtime_artifact_ingestion_result.json",
    REPO_ROOT / "outputs" / "v2_5_bugsinpy_runtime_runner" / "runner_status.json",
    REPO_ROOT / "outputs" / "v2_6_bugsinpy_real_bug_limited_replay" / "campaign_results.json",
    REPO_ROOT / "outputs" / "v2_4b_real_bug_runtime_unblock" / "aggregate_real_bug_memory_lift_assessment.json",
    REPO_ROOT / "outputs" / "v2_4_real_external_bug_replay_campaign" / "aggregate_real_external_bug_memory_lift_assessment.json",
    REPO_ROOT / "outputs" / "v2_3_known_external_bug_replay_campaign" / "aggregate_known_external_bug_memory_lift_assessment.json",
    REPO_ROOT / "outputs" / "v2_2_external_fork_controlled_fixture_replay_pilot" / "aggregate_external_fork_controlled_fixture_memory_lift_assessment.json",
    REPO_ROOT / "outputs" / "v1_9_organic_style_replay_pilot_completion_pass" / "aggregate_v1_9_updated_memory_lift_assessment.json",
    REPO_ROOT / "outputs" / "v1_8_episodes_004_010_memory_relevance_campaign" / "aggregate_memory_lift_assessment.json",
    REPO_ROOT / "outputs" / "v1_8_episode_003_torus_limited_replay_scoring" / "limited_scoring_result.json",
]


def load_json(path: Path) -> tuple[dict[str, Any], list[str]]:
    if not path.exists():
        return {}, [f"missing JSON file: {path}"]
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {}, [f"{path}: invalid JSON: {exc.msg}"]
    if not isinstance(data, dict):
        return {}, [f"{path}: expected JSON object"]
    return data, []


def verify_manifest(directory: Path) -> list[str]:
    manifest = directory / "SHA256SUMS.txt"
    if not manifest.exists():
        return [f"missing SHA256SUMS.txt in {directory}"]
    errors: list[str] = []
    seen: set[str] = set()
    for line_no, line in enumerate(manifest.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        parts = line.split()
        if len(parts) != 2:
            errors.append(f"{manifest}:{line_no}: expected '<sha256>  <path>'")
            continue
        expected, rel = parts
        seen.add(rel)
        path = directory / rel
        if not path.exists():
            errors.append(f"{manifest}:{line_no}: missing artifact {rel}")
            continue
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != expected:
            errors.append(f"{manifest}:{line_no}: hash mismatch for {rel}")
    for path in directory.rglob("*"):
        if path.is_file() and path.name != "SHA256SUMS.txt":
            rel = str(path.relative_to(directory)).replace("\\", "/")
            if rel not in seen:
                errors.append(f"SHA256SUMS missing artifact entry {rel}")
    return errors


def require_text(path: Path, snippets: list[str]) -> list[str]:
    if not path.exists():
        return [f"missing text file: {path}"]
    text = path.read_text(encoding="utf-8", errors="replace")
    return [f"{path}: missing required text {snippet!r}" for snippet in snippets if snippet not in text]


def main() -> int:
    errors: list[str] = []
    for path in [WORKFLOW, RUNNER, PREP]:
        if not path.exists():
            errors.append(f"missing v2.8g implementation file: {path}")
    for directory, required in [(OUTPUT_DIR, REQUIRED_PHASE_A), (RERUN_DIR, REQUIRED_RERUN)]:
        if not directory.exists():
            errors.append(f"missing v2.8g output directory: {directory}")
            continue
        for name in required:
            path = directory / name
            if not path.exists():
                errors.append(f"missing v2.8g artifact: {path}")
            elif path.stat().st_size == 0:
                errors.append(f"empty v2.8g artifact: {path}")
        errors.extend(verify_manifest(directory))

    preservation, preservation_errors = load_json(OUTPUT_DIR / "v2_8f_result_preservation.json")
    sha_record, sha_errors = load_json(OUTPUT_DIR / "v2_8f_artifact_sha256_verification.json")
    design, design_errors = load_json(OUTPUT_DIR / "source_discovery_design.json")
    registry, registry_errors = load_json(OUTPUT_DIR / "repair_heuristic_registry.json")
    campaign, campaign_errors = load_json(RERUN_DIR / "campaign_results.json")
    aggregate, aggregate_errors = load_json(RERUN_DIR / "aggregate_bugsinpy_real_bug_memory_lift_assessment.json")
    errors.extend(preservation_errors + sha_errors + design_errors + registry_errors + campaign_errors + aggregate_errors)

    verification_clean = sha_record.get("verification_clean", sha_record.get("sha256_manifest_clean"))
    if verification_clean is not True or sha_record.get("hash_failures"):
        errors.append("v2.8g must preserve clean v2.8f SHA256 inspection record")
    allowed_v28f_aggregates = {
        "blocked_no_safe_patch_candidate_generated",
        "insufficient_episode_count_for_bugsinpy_real_bug_memory_lift",
    }
    if preservation.get("aggregate_result") not in allowed_v28f_aggregates:
        errors.append("v2.8g must preserve v2.8f no-safe-patch / insufficient-count result")
    if preservation.get("episode_classification") != "blocked_no_safe_patch_candidate_generated":
        errors.append("v2.8g must preserve v2.8f episode-level no-safe-patch classification")
    if preservation.get("scoreable_episode_count") != 0:
        errors.append("v2.8g must preserve v2.8f zero-scoreable result")
    if design.get("inputs_forbidden") is None or "gold patch" not in design.get("inputs_forbidden", []):
        errors.append("source-discovery design must forbid gold patch inputs")
    if "boolean_value_matching_failure" not in registry or "parser_formatter_localized_failure" not in registry or "leading_newline_backslash_formatting_failure" not in registry:
        errors.append("repair heuristic registry must include all three required families")
    if campaign.get("workflow_executed") is not False:
        errors.append("local v2.8g checkpoint must remain pending workflow execution")
    if campaign.get("scoreable_episode_count") != 0:
        errors.append("pending v2.8g checkpoint must have zero scoreable episodes")
    if campaign.get("full_scoring_allowed") is not False or campaign.get("controllergate_full_scoring") != "NOT_RUN":
        errors.append("full scoring must remain NOT_RUN / disallowed")
    if campaign.get("self_maintaining_software_demonstrated") is not False:
        errors.append("self-maintaining software must remain not demonstrated")
    if aggregate.get("limited_bugsinpy_real_bug_memory_lift_criteria_met") is not False:
        errors.append("memory lift must not be claimed before v2.8g aggregate criteria are met")

    if RUNNER.exists():
        runner_text = RUNNER.read_text(encoding="utf-8")
        for snippet in [
            "build_symbol_index",
            "rank_source_files",
            "match_str",
            "source_discovery_report.json",
            "symbol_index_summary.json",
            "ranked_candidate_source_files.json",
            "repair_heuristic_selection.json",
            "patch_candidate_safety_check.json",
            "fixed_or_gold_patch_used",
            "future_outcome_evidence_used",
            "blocked_no_safe_patch_candidate_generated",
        ]:
            if snippet not in runner_text:
                errors.append(f"v2.8g runner missing required source-discovery snippet: {snippet}")
    if WORKFLOW.exists():
        workflow_text = WORKFLOW.read_text(encoding="utf-8")
        for snippet in ["v2_8g_bugsinpy_source_discovery_repair_proposer", "source discovery repair proposer present", "v2_8g_bugsinpy_source_discovery_repair_proposer_artifacts"]:
            if snippet not in workflow_text:
                errors.append(f"v2.8g workflow missing required snippet: {snippet}")
    for path in PRESERVED_RESULTS:
        if not path.exists():
            errors.append(f"missing preserved prior result: {path}")
    errors.extend(
        require_text(
            SUMMARY,
            [
                "v2.8g BugsInPy Source-Discovery Repair Proposer",
                "v2.8f proved the bounded proposer ran",
                "v2.8g adds decision-time symbol/source discovery",
                "No-patch/no-action outcomes are not scoreable repair evidence.",
                "Full scoring: NOT_RUN / disallowed.",
                "Self-maintaining software: not demonstrated.",
            ],
        )
    )
    if errors:
        print("v2.8g BugsInPy source-discovery repair proposer audit: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("v2.8g BugsInPy source-discovery repair proposer audit: PASS")
    print("v2.8f no-safe-patch result preserved: true")
    print("v2.8g workflow status: pending GitHub Actions artifact")
    print("scoreable episodes: 0")
    print("full scoring allowed: false")
    print("self-maintaining software demonstrated: false")
    return 0


if __name__ == "__main__":
    sys.exit(main())
