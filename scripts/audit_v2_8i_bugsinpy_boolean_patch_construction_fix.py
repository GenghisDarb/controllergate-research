#!/usr/bin/env python3
"""Audit v2.8i BugsInPy boolean patch construction fix."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = REPO_ROOT / "outputs" / "v2_8i_bugsinpy_boolean_patch_construction_fix"
RERUN_DIR = REPO_ROOT / "outputs" / "v2_8i_bugsinpy_real_bug_boolean_patch_comparison"
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "v2_8i_bugsinpy_boolean_patch_construction_fix.yml"
RUNNER = REPO_ROOT / "scripts" / "v2_8i_bugsinpy_boolean_patch_construction_fix_runner.py"
PREP = REPO_ROOT / "scripts" / "v2_8i_prepare_bugsinpy_boolean_patch_construction_fix.py"
H_INGESTER = REPO_ROOT / "scripts" / "v2_8h_ingest_targeted_boolean_patch_artifact.py"
INGESTER = REPO_ROOT / "scripts" / "v2_8i_ingest_boolean_patch_construction_fix_artifact.py"
SUMMARY = REPO_ROOT / "controllergate_v1_7_beta" / "reports" / "critic_review_package" / "shareable_summary.md"

REQUIRED_PHASE_A = [
    "v2_8h_artifact_ingestion_summary.json",
    "v2_8h_artifact_sha256_verification.json",
    "v2_8h_result_preservation.json",
    "v2_8h_boolean_heuristic_inconsistency.json",
    "v2_8h_boolean_heuristic_inconsistency_report.md",
    "episode_prior_status_table.json",
    "boolean_patch_construction_fix_design.json",
    "full_source_patch_search_policy.json",
    "unary_operator_region_extract.txt",
    "unary_operator_region_match_check.json",
    "boolean_patch_generation_result.json",
    "boolean_patch_safety_check.json",
    "no_memory_boolean_patch_generation_result.json",
    "memory_enabled_boolean_patch_generation_result.json",
    "no_memory_boolean_patch_safety_check.json",
    "memory_enabled_boolean_patch_safety_check.json",
    "no_memory_boolean_patch_candidate.diff",
    "memory_enabled_boolean_patch_candidate.diff",
    "v2_8i_artifact_ingestion_summary.json",
    "v2_8i_artifact_sha256_verification.json",
    "large_workspace_snapshots_index.json",
    "v2_8i_episode_result_table.json",
    "v2_8i_result_preservation.json",
    "v2_8i_boolean_patch_construction_result.json",
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
    "boolean_patch_construction_fix_design.json",
    "full_source_patch_search_policy.json",
    "boolean_patch_generation_result.json",
    "boolean_patch_safety_check.json",
    "unary_operator_region_extract.txt",
    "unary_operator_region_match_check.json",
    "runner_status.json",
    "SHA256SUMS.txt",
]

PRESERVED_RESULTS = [
    REPO_ROOT / "outputs" / "v2_8h_bugsinpy_real_bug_targeted_patch_comparison" / "campaign_results.json",
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
    for path in [WORKFLOW, RUNNER, PREP, H_INGESTER, INGESTER]:
        if not path.exists():
            errors.append(f"missing v2.8i implementation file: {path}")
    for directory, required in [(OUTPUT_DIR, REQUIRED_PHASE_A), (RERUN_DIR, REQUIRED_RERUN)]:
        if not directory.exists():
            errors.append(f"missing v2.8i output directory: {directory}")
            continue
        for name in required:
            path = directory / name
            if not path.exists():
                errors.append(f"missing v2.8i artifact: {path}")
            elif path.stat().st_size == 0:
                errors.append(f"empty v2.8i artifact: {path}")
        errors.extend(verify_manifest(directory))

    h_verification, h_verification_errors = load_json(OUTPUT_DIR / "v2_8h_artifact_sha256_verification.json")
    h_preservation, h_preservation_errors = load_json(OUTPUT_DIR / "v2_8h_result_preservation.json")
    h_inconsistency, h_inconsistency_errors = load_json(OUTPUT_DIR / "v2_8h_boolean_heuristic_inconsistency.json")
    prior_table, prior_table_errors = load_json(OUTPUT_DIR / "episode_prior_status_table.json")
    design, design_errors = load_json(OUTPUT_DIR / "boolean_patch_construction_fix_design.json")
    policy, policy_errors = load_json(OUTPUT_DIR / "full_source_patch_search_policy.json")
    region_check, region_check_errors = load_json(OUTPUT_DIR / "unary_operator_region_match_check.json")
    generation, generation_errors = load_json(OUTPUT_DIR / "boolean_patch_generation_result.json")
    safety, safety_errors = load_json(OUTPUT_DIR / "boolean_patch_safety_check.json")
    campaign, campaign_errors = load_json(RERUN_DIR / "campaign_results.json")
    aggregate, aggregate_errors = load_json(RERUN_DIR / "aggregate_bugsinpy_real_bug_memory_lift_assessment.json")
    i_verification, i_verification_errors = load_json(OUTPUT_DIR / "v2_8i_artifact_sha256_verification.json")
    i_preservation, i_preservation_errors = load_json(OUTPUT_DIR / "v2_8i_result_preservation.json")
    i_table, i_table_errors = load_json(OUTPUT_DIR / "v2_8i_episode_result_table.json")
    i_boolean_result, i_boolean_result_errors = load_json(OUTPUT_DIR / "v2_8i_boolean_patch_construction_result.json")
    errors.extend(
        h_verification_errors
        + h_preservation_errors
        + h_inconsistency_errors
        + prior_table_errors
        + design_errors
        + policy_errors
        + region_check_errors
        + generation_errors
        + safety_errors
        + campaign_errors
        + aggregate_errors
        + i_verification_errors
        + i_preservation_errors
        + i_table_errors
        + i_boolean_result_errors
    )

    if h_verification.get("verification_clean") is not True or h_verification.get("hash_failures"):
        errors.append("v2.8h artifact verification must be preserved as clean")
    if h_preservation.get("aggregate_result") != "blocked_no_safe_patch_candidate_generated":
        errors.append("v2.8i must preserve v2.8h blocked_no_safe_patch_candidate_generated result")
    if h_preservation.get("scoreable_episode_count") != 0:
        errors.append("v2.8i must preserve v2.8h zero-scoreable result")
    if h_inconsistency.get("heuristic_registered") is not True:
        errors.append("v2.8i must preserve v2.8h boolean heuristic registration")
    if h_inconsistency.get("unary_operator_block_found") is not True:
        errors.append("v2.8i must preserve v2.8h unary block detection")
    if h_inconsistency.get("patch_construction_mismatch_detected") is not True:
        errors.append("v2.8i must record v2.8h patch-construction mismatch")
    if h_inconsistency.get("no_memory_reason") != "expected UNARY_OPERATORS block not found":
        errors.append("v2.8i must preserve v2.8h no-memory patch-construction blocker")
    if h_inconsistency.get("memory_enabled_reason") != "expected UNARY_OPERATORS block not found":
        errors.append("v2.8i must preserve v2.8h memory-enabled patch-construction blocker")
    records = prior_table.get("records", [])
    if len(records) != 3:
        errors.append("v2.8i prior episode table must include three records")
    for record in records:
        if record.get("classification") != "blocked_no_safe_patch_candidate_generated":
            errors.append(f"v2.8i prior episode {record.get('episode_id')} has unexpected classification {record.get('classification')}")

    if design.get("source_file") != "youtube_dl/utils.py":
        errors.append("v2.8i fix design must target youtube_dl/utils.py")
    if "full source" not in str(design.get("fix", "")).lower():
        errors.append("v2.8i fix design must describe full source patch construction")
    if design.get("fixed_or_gold_patch_allowed") is not False or design.get("future_outcome_evidence_allowed") is not False:
        errors.append("v2.8i fix design must forbid fixed/gold and future outcome evidence")
    if policy.get("search_scope") != "full buggy youtube_dl/utils.py source file":
        errors.append("v2.8i full-source search policy must use full buggy youtube_dl/utils.py")
    workflow_executed = campaign.get("workflow_executed") is True
    if workflow_executed:
        if region_check.get("unary_operator_block_found") is not True:
            errors.append("executed v2.8i region check must find the unary operator block")
        if region_check.get("full_source_search_used") is not True:
            errors.append("executed v2.8i region check must record full-source search")
        if generation.get("candidate_generated") is not True:
            errors.append("executed v2.8i must generate the youtube-dl boolean patch")
        if generation.get("patched_file") != "youtube_dl/utils.py":
            errors.append("executed v2.8i generated patch must touch youtube_dl/utils.py")
    else:
        if region_check.get("full_source_search_policy_defined") is not True:
            errors.append("v2.8i region check must record full-source policy")
        if generation.get("patch_generation_pending_linux_runner") is not True:
            errors.append("local v2.8i patch generation must remain pending Linux runner")
    if safety.get("patch_only_file") != "youtube_dl/utils.py" or safety.get("modifies_tests") is not False:
        errors.append("v2.8i safety check must restrict patch to youtube_dl/utils.py and forbid test edits")
    if safety.get("uses_fixed_revision") is not False or safety.get("uses_gold_patch") is not False:
        errors.append("v2.8i safety check must forbid fixed/gold inputs")

    if workflow_executed:
        if i_verification.get("verification_clean") is not True or i_verification.get("hash_failures"):
            errors.append("v2.8i artifact SHA256 verification must be clean")
        if i_preservation.get("aggregate_result") != "insufficient_episode_count_for_bugsinpy_real_bug_memory_lift":
            errors.append("v2.8i executed aggregate must remain insufficient episode count")
        if campaign.get("executed_episode_count") != 3:
            errors.append("executed v2.8i campaign must include three executed episodes")
        if campaign.get("scoreable_episode_count") != 1:
            errors.append("executed v2.8i campaign must have exactly one scoreable episode")
        if campaign.get("positive_memory_episode_count") != 0:
            errors.append("executed v2.8i campaign must have zero positive memory episodes")
        if campaign.get("aggregate_result") != "insufficient_episode_count_for_bugsinpy_real_bug_memory_lift":
            errors.append("executed v2.8i aggregate must be insufficient episode count")
        records_after = i_table.get("records", [])
        if len(records_after) != 3:
            errors.append("v2.8i executed episode table must include three records")
        by_candidate = {record.get("candidate"): record for record in records_after}
        youtube = by_candidate.get("youtube-dl:1", {})
        if youtube.get("classification") != "inconclusive_equal_performance" or youtube.get("scoreable") is not True:
            errors.append("youtube-dl:1 must be scoreable inconclusive_equal_performance")
        if youtube.get("no_memory_patch_candidate_generated") is not True or youtube.get("memory_enabled_patch_candidate_generated") is not True:
            errors.append("youtube-dl:1 must generate both no-memory and memory-enabled patch candidates")
        if youtube.get("no_memory_primary_command_passed") is not True or youtube.get("memory_enabled_primary_command_passed") is not True:
            errors.append("youtube-dl:1 post-repair target command must pass for both paths")
        for candidate in ["black:8", "black:4"]:
            record = by_candidate.get(candidate, {})
            if record.get("classification") != "blocked_no_safe_patch_candidate_generated" or record.get("scoreable") is not False:
                errors.append(f"{candidate} must remain blocked_no_safe_patch_candidate_generated")
        if i_boolean_result.get("result_interpretation") != "scoreable_inconclusive_equal_performance_not_memory_lift":
            errors.append("v2.8i boolean result must classify the tie as inconclusive, not memory lift")
        if i_boolean_result.get("memory_enabled_outperformed_no_memory") is not False:
            errors.append("v2.8i must not mark memory-enabled outperformance for tied youtube-dl repair")
        if i_boolean_result.get("fixed_or_gold_patch_used") is not False or i_boolean_result.get("future_outcome_evidence_used") is not False:
            errors.append("v2.8i boolean result must forbid fixed/gold/future evidence")
    else:
        if campaign.get("scoreable_episode_count") != 0 or campaign.get("positive_memory_episode_count") != 0:
            errors.append("local v2.8i campaign must have zero scoreable and zero positive memory episodes")
        if campaign.get("aggregate_result") != "blocked_pending_v2_8i_boolean_patch_construction_fix_artifact":
            errors.append("local v2.8i aggregate must be pending runner artifact")
    if campaign.get("full_scoring_allowed") is not False or campaign.get("controllergate_full_scoring") != "NOT_RUN":
        errors.append("full scoring must remain NOT_RUN / disallowed")
    if campaign.get("self_maintaining_software_demonstrated") is not False:
        errors.append("self-maintaining software must remain not demonstrated")
    if aggregate.get("limited_bugsinpy_real_bug_memory_lift_criteria_met") is not False:
        errors.append("memory lift must not be claimed before v2.8i aggregate criteria are met")

    if RUNNER.exists():
        runner_text = RUNNER.read_text(encoding="utf-8")
        for snippet in [
            "locate_unary_operator_region",
            "full_source_patch_search_policy",
            "v is not None and v is not False",
            "v is None or v is False",
            "blocked_boolean_patch_construction_failed",
            "unary_operator_region_match_check.json",
            "no_memory_boolean_patch_candidate.diff",
            "memory_enabled_boolean_patch_candidate.diff",
            "fixed_or_gold_patch_used",
            "future_outcome_evidence_used",
            "inconclusive_equal_performance",
        ]:
            if snippet not in runner_text:
                errors.append(f"v2.8i runner missing required construction-fix snippet: {snippet}")
    if WORKFLOW.exists():
        workflow_text = WORKFLOW.read_text(encoding="utf-8")
        for snippet in [
            "v2_8i_bugsinpy_boolean_patch_construction_fix",
            "runner revision guard: boolean patch construction fix present",
            "v2_8i_bugsinpy_boolean_patch_construction_fix_artifacts",
        ]:
            if snippet not in workflow_text:
                errors.append(f"v2.8i workflow missing required snippet: {snippet}")

    for path in PRESERVED_RESULTS:
        if not path.exists():
            errors.append(f"missing preserved prior result: {path}")
    errors.extend(
        require_text(
            SUMMARY,
            [
                "v2.8i BugsInPy Boolean Patch Construction Fix",
                "v2.8h registered the boolean heuristic but failed patch construction despite detecting the unary operator block.",
                "v2.8i fixes the boolean patch construction path.",
                "A no-memory and memory-enabled tie is inconclusive, not memory lift.",
                "Full scoring: NOT_RUN / disallowed.",
                "Self-maintaining software: not demonstrated.",
            ],
        )
    )
    if errors:
        print("v2.8i BugsInPy boolean patch construction fix audit: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("v2.8i BugsInPy boolean patch construction fix audit: PASS")
    print("v2.8h artifact preserved: true")
    if workflow_executed:
        print("v2.8i workflow status: executed artifact ingested")
        print(f"scoreable episodes: {campaign.get('scoreable_episode_count')}")
        print("youtube-dl:1 classification: inconclusive_equal_performance")
    else:
        print("v2.8i workflow status: ready, pending GitHub Actions artifact")
        print("scoreable episodes: 0")
    print("full scoring allowed: false")
    print("self-maintaining software demonstrated: false")
    return 0


if __name__ == "__main__":
    sys.exit(main())
