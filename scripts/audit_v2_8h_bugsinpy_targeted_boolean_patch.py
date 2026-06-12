#!/usr/bin/env python3
"""Audit v2.8h BugsInPy targeted boolean patch heuristic."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = REPO_ROOT / "outputs" / "v2_8h_bugsinpy_targeted_boolean_patch_heuristic"
RERUN_DIR = REPO_ROOT / "outputs" / "v2_8h_bugsinpy_real_bug_targeted_patch_comparison"
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "v2_8h_bugsinpy_targeted_boolean_patch.yml"
RUNNER = REPO_ROOT / "scripts" / "v2_8h_bugsinpy_targeted_boolean_patch_runner.py"
PREP = REPO_ROOT / "scripts" / "v2_8h_prepare_bugsinpy_targeted_boolean_patch.py"
SUMMARY = REPO_ROOT / "controllergate_v1_7_beta" / "reports" / "critic_review_package" / "shareable_summary.md"

REQUIRED_PHASE_A = [
    "v2_8g_artifact_ingestion_summary.json",
    "v2_8g_artifact_sha256_verification.json",
    "v2_8g_result_preservation.json",
    "v2_8g_source_discovery_success_report.md",
    "v2_8g_blocked_patch_generation_report.md",
    "episode_prior_status_table.json",
    "boolean_unary_false_value_heuristic.json",
    "youtube_dl_patch_generation_rule.json",
    "heuristic_applicability_check.json",
    "heuristic_safety_check.json",
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
    "targeted_boolean_patch_summary.json",
    "SHA256SUMS.txt",
]

PRESERVED_RESULTS = [
    REPO_ROOT / "outputs" / "v2_8g_bugsinpy_real_bug_source_discovery_repair_comparison" / "campaign_results.json",
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
            errors.append(f"missing v2.8h implementation file: {path}")
    for directory, required in [(OUTPUT_DIR, REQUIRED_PHASE_A), (RERUN_DIR, REQUIRED_RERUN)]:
        if not directory.exists():
            errors.append(f"missing v2.8h output directory: {directory}")
            continue
        for name in required:
            path = directory / name
            if not path.exists():
                errors.append(f"missing v2.8h artifact: {path}")
            elif path.stat().st_size == 0:
                errors.append(f"empty v2.8h artifact: {path}")
        errors.extend(verify_manifest(directory))

    verification, verification_errors = load_json(OUTPUT_DIR / "v2_8g_artifact_sha256_verification.json")
    preservation, preservation_errors = load_json(OUTPUT_DIR / "v2_8g_result_preservation.json")
    heuristic, heuristic_errors = load_json(OUTPUT_DIR / "boolean_unary_false_value_heuristic.json")
    rule, rule_errors = load_json(OUTPUT_DIR / "youtube_dl_patch_generation_rule.json")
    applicability, applicability_errors = load_json(OUTPUT_DIR / "heuristic_applicability_check.json")
    safety, safety_errors = load_json(OUTPUT_DIR / "heuristic_safety_check.json")
    campaign, campaign_errors = load_json(RERUN_DIR / "campaign_results.json")
    aggregate, aggregate_errors = load_json(RERUN_DIR / "aggregate_bugsinpy_real_bug_memory_lift_assessment.json")
    errors.extend(
        verification_errors
        + preservation_errors
        + heuristic_errors
        + rule_errors
        + applicability_errors
        + safety_errors
        + campaign_errors
        + aggregate_errors
    )

    if verification.get("verification_clean") is not True:
        errors.append("v2.8h must preserve clean v2.8g artifact SHA256 verification")
    if preservation.get("aggregate_result") != "blocked_no_safe_patch_candidate_generated":
        errors.append("v2.8h must preserve v2.8g blocked_no_safe_patch_candidate_generated result")
    if preservation.get("scoreable_episode_count") != 0:
        errors.append("v2.8h must preserve v2.8g zero-scoreable result")
    if heuristic.get("heuristic_name") != "boolean_unary_false_value_presence_rule":
        errors.append("v2.8h boolean-unary heuristic missing expected name")
    if heuristic.get("candidate_scope") != "youtube-dl:1":
        errors.append("v2.8h heuristic must be scoped to youtube-dl:1")
    if heuristic.get("source_file_scope") != "youtube_dl/utils.py":
        errors.append("v2.8h heuristic must be scoped to youtube_dl/utils.py")
    if heuristic.get("fixed_or_gold_patch_used") is not False or heuristic.get("future_outcome_evidence_used") is not False:
        errors.append("v2.8h heuristic must forbid fixed/gold and future outcome evidence")
    if rule.get("black_candidates") is None:
        errors.append("v2.8h rule must explicitly avoid forced Black patches")
    youtube_applicability = applicability.get("youtube-dl:1", {})
    if youtube_applicability.get("applicability_status") != "ready_for_linux_runner_confirmation":
        errors.append("youtube-dl applicability must be ready for Linux runner confirmation")
    if safety.get("patch_only_file") != "youtube_dl/utils.py" or safety.get("modifies_tests") is not False:
        errors.append("v2.8h safety check must restrict patch to youtube_dl/utils.py and forbid test edits")
    if safety.get("uses_fixed_revision") is not False or safety.get("uses_gold_patch") is not False or safety.get("uses_future_outcome_evidence") is not False:
        errors.append("v2.8h safety check must forbid fixed/gold/future inputs")
    if campaign.get("workflow_executed") is not False:
        errors.append("local v2.8h checkpoint must remain pending workflow execution")
    if campaign.get("scoreable_episode_count") != 0:
        errors.append("pending v2.8h checkpoint must have zero scoreable episodes")
    if campaign.get("aggregate_result") != "blocked_pending_v2_8h_targeted_boolean_patch_artifact":
        errors.append("pending v2.8h aggregate must require GitHub Actions artifact")
    if campaign.get("full_scoring_allowed") is not False or campaign.get("controllergate_full_scoring") != "NOT_RUN":
        errors.append("full scoring must remain NOT_RUN / disallowed")
    if campaign.get("self_maintaining_software_demonstrated") is not False:
        errors.append("self-maintaining software must remain not demonstrated")
    if aggregate.get("limited_bugsinpy_real_bug_memory_lift_criteria_met") is not False:
        errors.append("memory lift must not be claimed before v2.8h aggregate criteria are met")

    if RUNNER.exists():
        runner_text = RUNNER.read_text(encoding="utf-8")
        for snippet in [
            "boolean_unary_false_value_presence_rule",
            "v is not None and v is not False",
            "v is None or v is False",
            "youtube_dl/utils.py",
            "boolean_patch_candidate.diff",
            "boolean_patch_candidate_explanation.json",
            "fixed_or_gold_patch_used",
            "future_outcome_evidence_used",
            "insufficient_episode_count_for_bugsinpy_real_bug_memory_lift",
        ]:
            if snippet not in runner_text:
                errors.append(f"v2.8h runner missing required heuristic snippet: {snippet}")
    if WORKFLOW.exists():
        workflow_text = WORKFLOW.read_text(encoding="utf-8")
        for snippet in [
            "v2_8h_bugsinpy_targeted_boolean_patch",
            "targeted boolean patch heuristic present",
            "v2_8h_bugsinpy_targeted_boolean_patch_artifacts",
        ]:
            if snippet not in workflow_text:
                errors.append(f"v2.8h workflow missing required snippet: {snippet}")
    for path in PRESERVED_RESULTS:
        if not path.exists():
            errors.append(f"missing preserved prior result: {path}")
    errors.extend(
        require_text(
            SUMMARY,
            [
                "v2.8h BugsInPy Targeted Boolean Patch Heuristic",
                "v2.8g found the relevant `match_str` source for youtube-dl:1",
                "targeted non-gold boolean false-handling repair heuristic",
                "A no-memory and memory-enabled tie is inconclusive, not memory lift.",
                "Full scoring: NOT_RUN / disallowed.",
                "Self-maintaining software: not demonstrated.",
            ],
        )
    )
    if errors:
        print("v2.8h BugsInPy targeted boolean patch audit: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("v2.8h BugsInPy targeted boolean patch audit: PASS")
    print("v2.8g source discovery preserved: true")
    print("v2.8h workflow status: pending GitHub Actions artifact")
    print("scoreable episodes: 0")
    print("full scoring allowed: false")
    print("self-maintaining software demonstrated: false")
    return 0


if __name__ == "__main__":
    sys.exit(main())
