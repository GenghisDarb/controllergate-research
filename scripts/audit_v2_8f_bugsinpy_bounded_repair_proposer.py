#!/usr/bin/env python3
"""Audit v2.8f BugsInPy bounded repair proposer campaign."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = REPO_ROOT / "outputs" / "v2_8f_bugsinpy_bounded_repair_proposer"
RERUN_DIR = REPO_ROOT / "outputs" / "v2_8f_bugsinpy_real_bug_bounded_repair_comparison"
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "v2_8f_bugsinpy_bounded_repair_proposer.yml"
RUNNER = REPO_ROOT / "scripts" / "v2_8f_bugsinpy_bounded_repair_proposer_runner.py"
PREP = REPO_ROOT / "scripts" / "v2_8f_prepare_bugsinpy_bounded_repair_proposer.py"
V28E_OUTPUT = REPO_ROOT / "outputs" / "v2_8e_bugsinpy_repair_workspace_preservation" / "campaign_results.json"
V28D_OUTPUT = REPO_ROOT / "outputs" / "v2_8d_bugsinpy_git_workspace_repair_comparison" / "campaign_results.json"
SUMMARY = REPO_ROOT / "controllergate_v1_7_beta" / "reports" / "critic_review_package" / "shareable_summary.md"

PRESERVED_RESULTS = [
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
    REPO_ROOT / "controllergate_v1_7_beta" / "outputs" / "v1_7_beta_replay_eligibility_plan.json",
    REPO_ROOT / "controllergate_v1_7_alpha" / "traces" / "audits" / "episode_review_classification.json",
]

REQUIRED_PHASE_A = [
    "v2_8e_artifact_ingestion_summary.json",
    "v2_8e_artifact_sha256_verification.json",
    "v2_8e_result_preservation.json",
    "v2_8e_workspace_preservation_success_report.md",
    "v2_8e_blocked_candidate_generation_report.md",
    "episode_prior_status_table.json",
    "bounded_repair_proposer_design.json",
    "repair_budget_policy.json",
    "decision_time_allowed_inputs_policy.json",
    "forbidden_inputs_policy.json",
    "memory_evidence_policy.json",
    "repair_candidate_generation_policy.json",
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
    "bounded_repair_proposer_summary.json",
    "SHA256SUMS.txt",
]


def load_json(path: Path) -> tuple[dict[str, Any], list[str]]:
    if not path.exists():
        return {}, [f"missing JSON file: {path}"]
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {}, [f"{path}: invalid JSON: {exc.msg}"]
    if not isinstance(data, dict):
        return {}, [f"{path}: expected object"]
    return data, []


def verify_manifest(directory: Path, recursive: bool = True) -> list[str]:
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
    if recursive:
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
            errors.append(f"missing v2.8f implementation file: {path}")
    for directory, required in [(OUTPUT_DIR, REQUIRED_PHASE_A), (RERUN_DIR, REQUIRED_RERUN)]:
        if not directory.exists():
            errors.append(f"missing v2.8f output directory: {directory}")
        for name in required:
            path = directory / name
            if not path.exists():
                errors.append(f"missing v2.8f artifact {path}")
            elif path.stat().st_size == 0:
                errors.append(f"empty v2.8f artifact {path}")
        if directory.exists():
            errors.extend(verify_manifest(directory))

    v28e_preservation, preservation_errors = load_json(OUTPUT_DIR / "v2_8e_result_preservation.json")
    design, design_errors = load_json(OUTPUT_DIR / "bounded_repair_proposer_design.json")
    budget, budget_errors = load_json(OUTPUT_DIR / "repair_budget_policy.json")
    forbidden, forbidden_errors = load_json(OUTPUT_DIR / "forbidden_inputs_policy.json")
    campaign, campaign_errors = load_json(RERUN_DIR / "campaign_results.json")
    aggregate, aggregate_errors = load_json(RERUN_DIR / "aggregate_bugsinpy_real_bug_memory_lift_assessment.json")
    errors.extend(preservation_errors + design_errors + budget_errors + forbidden_errors + campaign_errors + aggregate_errors)

    if v28e_preservation.get("workspace_preservation_success") is not True:
        errors.append("v2.8f must preserve v2.8e workspace preservation success")
    if v28e_preservation.get("preserved_aggregate_result") != "blocked_no_repair_candidate_generated":
        errors.append("v2.8f must preserve v2.8e no-candidate block")
    if design.get("uses_fixed_or_gold_patch") is not False or design.get("uses_future_outcome_evidence") is not False:
        errors.append("v2.8f proposer design must forbid fixed/gold and future outcome evidence")
    if budget.get("same_budget_for_no_memory_and_memory_enabled") is not True:
        errors.append("v2.8f budget must be identical except allowed memory evidence")
    forbidden_inputs = set(forbidden.get("forbidden_inputs", []))
    for item in ["BugsInPy fixed revision", "BugsInPy gold patch", "known repair diff", "future passing logs"]:
        if item not in forbidden_inputs:
            errors.append(f"v2.8f forbidden input policy missing {item}")
    if campaign.get("workflow_executed") is not False:
        errors.append("local v2.8f checkpoint must remain pending workflow execution")
    if campaign.get("scoreable_episode_count") != 0:
        errors.append("pending v2.8f checkpoint must have zero scoreable episodes")
    if campaign.get("full_scoring_allowed") is not False or campaign.get("controllergate_full_scoring") != "NOT_RUN":
        errors.append("full scoring must remain NOT_RUN / disallowed")
    if campaign.get("self_maintaining_software_demonstrated") is not False:
        errors.append("self-maintaining software must remain not demonstrated")
    if aggregate.get("limited_bugsinpy_real_bug_memory_lift_criteria_met") is not False:
        errors.append("memory lift must not be claimed before v2.8f aggregate criteria are met")

    if RUNNER.exists():
        runner_text = RUNNER.read_text(encoding="utf-8")
        for snippet in [
            "propose_patch",
            "forbidden_inputs_used",
            "fixed_or_gold_patch_used",
            "future_outcome_evidence_used",
            "blocked_no_safe_patch_candidate_generated",
            "workspace_equivalence_check.json",
            "no_memory_prerepair_replay_log_raw.txt",
            "memory_enabled_prerepair_replay_log_raw.txt",
            "NO PATCH CANDIDATE GENERATED",
        ]:
            if snippet not in runner_text:
                errors.append(f"v2.8f runner missing required bounded proposer snippet: {snippet}")
    if WORKFLOW.exists():
        workflow_text = WORKFLOW.read_text(encoding="utf-8")
        for snippet in ["v2_8f_bugsinpy_bounded_repair_proposer", "bounded decision-time-only repair proposer present", "v2_8f_bugsinpy_bounded_repair_proposer_artifacts"]:
            if snippet not in workflow_text:
                errors.append(f"v2.8f workflow missing required snippet: {snippet}")
    for path in [V28E_OUTPUT, V28D_OUTPUT, *PRESERVED_RESULTS]:
        if not path.exists():
            errors.append(f"missing preserved prior result: {path}")
    errors.extend(
        require_text(
            SUMMARY,
            [
                "v2.8f BugsInPy Bounded Repair Proposer",
                "v2.8e fixed workspace preservation",
                "v2.8e blocked reason: `blocked_no_repair_candidate_generated`",
                "workflow ready, pending GitHub Actions execution",
                "Full scoring: NOT_RUN / disallowed.",
                "Self-maintaining software: not demonstrated.",
            ],
        )
    )
    if errors:
        print("v2.8f BugsInPy bounded repair proposer audit: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("v2.8f BugsInPy bounded repair proposer audit: PASS")
    print("v2.8e workspace preservation preserved: true")
    print("v2.8f workflow status: pending GitHub Actions artifact")
    print("scoreable episodes: 0")
    print("full scoring allowed: false")
    print("self-maintaining software demonstrated: false")
    return 0


if __name__ == "__main__":
    sys.exit(main())
