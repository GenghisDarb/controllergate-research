#!/usr/bin/env python3
"""Audit v2.8e BugsInPy repair workspace-preservation campaign."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = REPO_ROOT / "outputs" / "v2_8e_bugsinpy_repair_workspace_preservation"
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "v2_8e_bugsinpy_repair_workspace_preservation.yml"
RUNNER = REPO_ROOT / "scripts" / "v2_8e_bugsinpy_repair_workspace_preservation_runner.py"
PREP = REPO_ROOT / "scripts" / "v2_8e_prepare_bugsinpy_repair_workspace_preservation.py"
SUMMARY = REPO_ROOT / "controllergate_v1_7_beta" / "reports" / "critic_review_package" / "shareable_summary.md"

V28D_OUTPUT = REPO_ROOT / "outputs" / "v2_8d_bugsinpy_git_workspace_repair_comparison" / "campaign_results.json"
V27E_OUTPUT = REPO_ROOT / "outputs" / "v2_7e_bugsinpy_third_candidate_artifact_ingestion" / "v2_8_execution_gate_decision.json"
V27_OUTPUT = REPO_ROOT / "outputs" / "v2_7_bugsinpy_target_replay_promotion_recovery" / "runtime_artifact_ingestion_result.json"
V25_STATUS = REPO_ROOT / "outputs" / "v2_5_bugsinpy_runtime_runner" / "runner_status.json"
V26_RESULTS = REPO_ROOT / "outputs" / "v2_6_bugsinpy_real_bug_limited_replay" / "campaign_results.json"
V24B_AGG = REPO_ROOT / "outputs" / "v2_4b_real_bug_runtime_unblock" / "aggregate_real_bug_memory_lift_assessment.json"
V24_AGG = REPO_ROOT / "outputs" / "v2_4_real_external_bug_replay_campaign" / "aggregate_real_external_bug_memory_lift_assessment.json"
V23_AGG = REPO_ROOT / "outputs" / "v2_3_known_external_bug_replay_campaign" / "aggregate_known_external_bug_memory_lift_assessment.json"
V22_AGG = REPO_ROOT / "outputs" / "v2_2_external_fork_controlled_fixture_replay_pilot" / "aggregate_external_fork_controlled_fixture_memory_lift_assessment.json"
V19_AGG = REPO_ROOT / "outputs" / "v1_9_organic_style_replay_pilot_completion_pass" / "aggregate_v1_9_updated_memory_lift_assessment.json"
V18_AGG = REPO_ROOT / "outputs" / "v1_8_episodes_004_010_memory_relevance_campaign" / "aggregate_memory_lift_assessment.json"
E003_RESULT = REPO_ROOT / "outputs" / "v1_8_episode_003_torus_limited_replay_scoring" / "limited_scoring_result.json"
BETA_REPLAY = REPO_ROOT / "controllergate_v1_7_beta" / "outputs" / "v1_7_beta_replay_eligibility_plan.json"
BETA_SCORING = REPO_ROOT / "controllergate_v1_7_beta" / "traces" / "audits" / "limited_pilot_scoring" / "limited_pilot_scoring.json"
ALPHA_CLASSIFICATION = REPO_ROOT / "controllergate_v1_7_alpha" / "traces" / "audits" / "episode_review_classification.json"

REQUIRED_OUTPUTS = [
    "v2_8d_artifact_ingestion_summary.json",
    "v2_8d_artifact_sha256_verification.json",
    "v2_8d_result_preservation.json",
    "v2_8d_apoptosis_context_report.md",
    "repair_noop_root_cause_report.md",
    "post_repair_workspace_divergence_report.md",
    "episode_blocker_table.json",
    "runner_status.json",
    "campaign_plan.json",
    "github_actions_usage_instructions.md",
    "SHA256SUMS.txt",
]

REQUIRED_EPISODE_ARTIFACTS_IF_EXECUTED = [
    "workspace_preservation_strategy.json",
    "baseline_workspace_manifest.json",
    "no_memory_prerepair_workspace_manifest.json",
    "memory_enabled_prerepair_workspace_manifest.json",
    "workspace_equivalence_check.json",
    "no_memory_prerepair_replay_log_raw.txt",
    "memory_enabled_prerepair_replay_log_raw.txt",
    "repair_workspace_preservation_result.json",
    "repair_attempt_budget.json",
    "no_memory_repair_candidate_generation.json",
    "memory_enabled_repair_candidate_generation.json",
    "no_memory_action_trace.json",
    "memory_enabled_action_trace.json",
    "no_memory_repair_patch.diff",
    "memory_enabled_repair_patch.diff",
    "no_memory_patch_application_result.json",
    "memory_enabled_patch_application_result.json",
    "limited_scoring_result.json",
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
            if path.is_file() and path.name != "SHA256SUMS.txt" and path.suffix.lower() != ".zip":
                rel = str(path.relative_to(directory)).replace("\\", "/")
                if rel not in seen:
                    errors.append(f"SHA256SUMS missing artifact entry {rel}")
    return errors


def require_text(path: Path, snippets: list[str]) -> list[str]:
    if not path.exists():
        return [f"missing text file: {path}"]
    text = path.read_text(encoding="utf-8", errors="replace")
    return [f"{path}: missing required text {snippet!r}" for snippet in snippets if snippet not in text]


def audit_executed_artifact_dir(path: Path) -> list[str]:
    errors: list[str] = []
    campaign, campaign_errors = load_json(path / "campaign_results.json")
    errors.extend(campaign_errors)
    for episode in ["episode_001", "episode_002", "episode_003"]:
        episode_dir = path / episode
        if not episode_dir.exists():
            errors.append(f"executed v2.8e artifact missing {episode}")
            continue
        for name in REQUIRED_EPISODE_ARTIFACTS_IF_EXECUTED:
            file = episode_dir / name
            if not file.exists():
                errors.append(f"{episode}: missing {name}")
            elif file.stat().st_size == 0:
                errors.append(f"{episode}: empty {name}")
        equivalence, equivalence_errors = load_json(episode_dir / "workspace_equivalence_check.json")
        no_gen, no_errors = load_json(episode_dir / "no_memory_repair_candidate_generation.json")
        mem_gen, mem_errors = load_json(episode_dir / "memory_enabled_repair_candidate_generation.json")
        scoring, scoring_errors = load_json(episode_dir / "limited_scoring_result.json")
        errors.extend(equivalence_errors + no_errors + mem_errors + scoring_errors)
        if equivalence.get("workspace_equivalence_passed") is not True:
            errors.append(f"{episode}: workspace equivalence must pass before repair attempt")
        if no_gen.get("candidate_generated") is False and scoring.get("scoreable") is True:
            errors.append(f"{episode}: no patch candidate cannot be scoreable")
        if mem_gen.get("candidate_generated") is False and scoring.get("scoreable") is True:
            errors.append(f"{episode}: no memory patch candidate cannot be scoreable")
        errors.extend(verify_manifest(episode_dir))
    if campaign.get("full_scoring_allowed") is not False or campaign.get("controllergate_full_scoring") != "NOT_RUN":
        errors.append("v2.8e executed artifact must keep full scoring NOT_RUN / disallowed")
    if campaign.get("self_maintaining_software_demonstrated") is not False:
        errors.append("v2.8e executed artifact must not demonstrate self-maintaining software")
    errors.extend(verify_manifest(path))
    return errors


def main() -> int:
    errors: list[str] = []
    for path in [WORKFLOW, RUNNER, PREP]:
        if not path.exists():
            errors.append(f"missing v2.8e implementation file: {path}")
    if not OUTPUT_DIR.exists():
        errors.append(f"missing v2.8e output directory: {OUTPUT_DIR}")
    for name in REQUIRED_OUTPUTS:
        path = OUTPUT_DIR / name
        if not path.exists():
            errors.append(f"missing v2.8e output {name}")
        elif path.stat().st_size == 0:
            errors.append(f"empty v2.8e output {name}")

    verification, verification_errors = load_json(OUTPUT_DIR / "v2_8d_artifact_sha256_verification.json")
    preservation, preservation_errors = load_json(OUTPUT_DIR / "v2_8d_result_preservation.json")
    blockers, blocker_errors = load_json(OUTPUT_DIR / "episode_blocker_table.json")
    runner_status, runner_errors = load_json(OUTPUT_DIR / "runner_status.json")
    plan, plan_errors = load_json(OUTPUT_DIR / "campaign_plan.json")
    errors.extend(verification_errors + preservation_errors + blocker_errors + runner_errors + plan_errors)

    if verification.get("verification_clean") is not True:
        errors.append("v2.8d artifact SHA256 verification must be clean")
    if preservation.get("preserved_aggregate_result") != "blocked_apoptosis_watchdog_triggered":
        errors.append("v2.8e must preserve v2.8d blocked_apoptosis_watchdog_triggered result")
    if preservation.get("memory_lift_demonstrated") is not False:
        errors.append("v2.8e must not claim memory lift from v2.8d preservation")
    records = blockers.get("records", [])
    if len(records) != 3:
        errors.append("episode blocker table must contain three v2.8d episodes")
    required_candidates = {"youtube-dl:1", "black:8", "black:4"}
    if {item.get("candidate") for item in records} != required_candidates:
        errors.append("episode blocker table must preserve youtube-dl:1, black:8, and black:4")
    for item in records:
        if item.get("v2_8e_preserved_classification") != "blocked_repair_runner_noop_or_workspace_divergence":
            errors.append(f"{item.get('candidate')}: expected blocked repair runner/noop/workspace divergence classification")
        if item.get("scoreable_repair_evidence") is not False:
            errors.append(f"{item.get('candidate')}: v2.8d blocked artifact cannot become scoreable")
    if runner_status.get("workflow_executed") is not False:
        errors.append("local v2.8e checkpoint should be pending workflow execution")
    if runner_status.get("repair_scoring") != "NOT_RUN":
        errors.append("repair scoring must remain NOT_RUN until v2.8e artifact is ingested")
    if runner_status.get("full_scoring_allowed") is not False:
        errors.append("full scoring must remain disallowed")
    if runner_status.get("self_maintaining_software_demonstrated") is not False:
        errors.append("self-maintaining software must remain not demonstrated")
    if plan.get("workspace_preservation_strategy") != "archive validated baseline workspace and extract exact copies for repair paths":
        errors.append("v2.8e plan must require archive-restored exact repair workspaces")

    if WORKFLOW.exists():
        workflow_text = WORKFLOW.read_text(encoding="utf-8")
        for snippet in [
            "v2_8e_bugsinpy_repair_workspace_preservation",
            "Verify v2.8e runner revision",
            "archive-preserved repair workspaces present",
            "v2_8e_bugsinpy_repair_workspace_preservation_artifacts",
        ]:
            if snippet not in workflow_text:
                errors.append(f"v2.8e workflow missing required snippet: {snippet}")
    if RUNNER.exists():
        runner_text = RUNNER.read_text(encoding="utf-8")
        for snippet in [
            "tarfile.open",
            "dereference=False",
            "workspace_equivalence_check.json",
            "baseline_workspace_manifest.json",
            "no_memory_prerepair_workspace_manifest.json",
            "memory_enabled_prerepair_workspace_manifest.json",
            "no_memory_prerepair_replay_log_raw.txt",
            "memory_enabled_prerepair_replay_log_raw.txt",
            "repair_workspace_preservation_result.json",
            "repair_attempt_budget.json",
            "blocked_no_repair_candidate_generated",
            "candidate_generated\": False",
        ]:
            if snippet not in runner_text:
                errors.append(f"v2.8e runner missing required workspace/attempt snippet: {snippet}")
        if "git_clone_no_local" in runner_text:
            errors.append("v2.8e runner must not use git_clone_no_local as repair workspace preservation")

    executed_artifact = REPO_ROOT / "v2_8e_bugsinpy_repair_workspace_preservation_artifacts"
    if executed_artifact.exists():
        errors.extend(audit_executed_artifact_dir(executed_artifact))

    errors.extend(verify_manifest(OUTPUT_DIR))
    for path in [
        V28D_OUTPUT,
        V27E_OUTPUT,
        V27_OUTPUT,
        V25_STATUS,
        V26_RESULTS,
        V24B_AGG,
        V24_AGG,
        V23_AGG,
        V22_AGG,
        V19_AGG,
        V18_AGG,
        E003_RESULT,
        BETA_REPLAY,
        BETA_SCORING,
        ALPHA_CLASSIFICATION,
    ]:
        if not path.exists():
            errors.append(f"missing preserved prior result: {path}")
    errors.extend(
        require_text(
            SUMMARY,
            [
                "v2.8e BugsInPy Repair Workspace Preservation",
                "v2.8d artifact ingestion: SHA256 verification clean.",
                "repair workspaces must be exact preserved copies",
                "v2.8e repair scoring: NOT RUN.",
                "Full scoring: NOT_RUN / disallowed.",
                "Memory lift: not demonstrated.",
                "Self-maintaining software: not demonstrated.",
            ],
        )
    )
    if errors:
        print("v2.8e BugsInPy repair workspace-preservation audit: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("v2.8e BugsInPy repair workspace-preservation audit: PASS")
    print("v2.8d artifact preserved: blocked_apoptosis_watchdog_triggered")
    print("v2.8e workflow status: pending GitHub Actions artifact")
    print("repair scoring: NOT_RUN")
    print("full scoring allowed: false")
    print("self-maintaining software demonstrated: false")
    return 0


if __name__ == "__main__":
    sys.exit(main())
