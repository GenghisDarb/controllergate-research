#!/usr/bin/env python3
"""Audit v2.8b BugsInPy repair-comparison runner artifacts."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = REPO_ROOT / "outputs" / "v2_8b_bugsinpy_repair_comparison"
V27E_POOL = REPO_ROOT / "outputs" / "v2_7e_bugsinpy_third_candidate_artifact_ingestion" / "promoted_bugsinpy_real_bug_candidate_pool.json"
V27E_GATE = REPO_ROOT / "outputs" / "v2_7e_bugsinpy_third_candidate_artifact_ingestion" / "v2_8_execution_gate_decision.json"
V28_AGG = REPO_ROOT / "outputs" / "v2_8_bugsinpy_real_bug_limited_replay_execution" / "aggregate_bugsinpy_real_bug_memory_lift_assessment.json"
V27D_GATE = REPO_ROOT / "outputs" / "v2_7d_bugsinpy_third_candidate_direct_runner_expansion" / "v2_8_execution_gate_decision.json"
V27C_POOL = REPO_ROOT / "outputs" / "v2_7c_bugsinpy_direct_runner_artifact_ingestion" / "promoted_bugsinpy_real_bug_candidate_pool.json"
V27B_GATE = REPO_ROOT / "outputs" / "v2_7b_bugsinpy_direct_target_runner_fix" / "v2_8_execution_gate_decision.json"
V27_INGEST = REPO_ROOT / "outputs" / "v2_7_bugsinpy_target_replay_promotion_recovery" / "runtime_artifact_ingestion_result.json"
V26_RESULTS = REPO_ROOT / "outputs" / "v2_6_bugsinpy_real_bug_limited_replay" / "campaign_results.json"
V25_STATUS = REPO_ROOT / "outputs" / "v2_5_bugsinpy_runtime_runner" / "runner_status.json"
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
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "v2_8b_bugsinpy_repair_comparison.yml"
RUNNER = REPO_ROOT / "scripts" / "v2_8b_bugsinpy_repair_comparison_runner.py"
PARSER = REPO_ROOT / "scripts" / "v2_8b_parse_repair_comparison_artifacts.py"
SHAREABLE_SUMMARY = REPO_ROOT / "controllergate_v1_7_beta" / "reports" / "critic_review_package" / "shareable_summary.md"

REQUIRED_CAMPAIGN_FILES = [
    "campaign_plan.json",
    "candidate_pool.json",
    "linux_runner_environment_snapshot.txt",
    "repair_comparison_runner_policy.json",
    "decision_time_policy.json",
    "gold_patch_exclusion_policy.json",
    "label_blindness_policy.json",
    "apoptosis_watchdog_policy.json",
    "campaign_results.json",
    "aggregate_bugsinpy_real_bug_memory_lift_assessment.json",
    "campaign_summary.md",
    "SHA256SUMS.txt",
]

REQUIRED_EPISODE_FILES = [
    "episode_metadata.json",
    "candidate_selection_record.json",
    "bugsinpy_bug_reference.json",
    "source_repo_metadata.json",
    "license_summary.txt",
    "target_repo_snapshot.json",
    "environment_snapshot.txt",
    "baseline_checkout_command.txt",
    "baseline_checkout_log_raw.txt",
    "dependency_install_plan.json",
    "dependency_install_commands.txt",
    "dependency_install_log_raw.txt",
    "compile_command.txt",
    "compile_log_raw.txt",
    "failing_command.txt",
    "failing_log_raw.txt",
    "failure_signature.txt",
    "target_failure_match_check.json",
    "pre_repair_replay_transcript.txt",
    "decision_time_input_manifest.json",
    "gold_patch_exclusion_check.json",
    "label_blindness_check.json",
    "proof_obligations_ledger.json",
    "apoptosis_watchdog_result.json",
    "no_memory_decision_time_inputs.json",
    "no_memory_action_trace.json",
    "no_memory_repair_patch.diff",
    "no_memory_post_repair_command.txt",
    "no_memory_post_repair_log_raw.txt",
    "no_memory_outcome.json",
    "memory_enabled_decision_time_inputs.json",
    "memory_evidence_used.json",
    "memory_enabled_action_trace.json",
    "memory_enabled_repair_patch.diff",
    "memory_enabled_post_repair_command.txt",
    "memory_enabled_post_repair_log_raw.txt",
    "memory_enabled_outcome.json",
    "post_repair_comparison.json",
    "corruption_check_result.json",
    "decision_time_outcome_overlap_check.json",
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


def require_text(path: Path, required: list[str]) -> list[str]:
    if not path.exists():
        return [f"missing text file: {path}"]
    text = path.read_text(encoding="utf-8")
    return [f"{path}: missing required text {item!r}" for item in required if item not in text]


def audit_episode(directory: Path) -> list[str]:
    errors: list[str] = []
    for name in REQUIRED_EPISODE_FILES:
        path = directory / name
        if not path.exists():
            errors.append(f"{directory.name}: missing {name}")
        elif path.stat().st_size == 0:
            errors.append(f"{directory.name}: empty {name}")
    no_command = (directory / "no_memory_post_repair_command.txt").read_text(encoding="utf-8", errors="replace").strip() if (directory / "no_memory_post_repair_command.txt").exists() else ""
    mem_command = (directory / "memory_enabled_post_repair_command.txt").read_text(encoding="utf-8", errors="replace").strip() if (directory / "memory_enabled_post_repair_command.txt").exists() else ""
    if no_command != mem_command:
        errors.append(f"{directory.name}: no-memory and memory-enabled validation commands must match")
    decision, decision_errors = load_json(directory / "decision_time_input_manifest.json")
    gold, gold_errors = load_json(directory / "gold_patch_exclusion_check.json")
    label, label_errors = load_json(directory / "label_blindness_check.json")
    proof, proof_errors = load_json(directory / "proof_obligations_ledger.json")
    watchdog, watchdog_errors = load_json(directory / "apoptosis_watchdog_result.json")
    overlap, overlap_errors = load_json(directory / "decision_time_outcome_overlap_check.json")
    corruption, corruption_errors = load_json(directory / "corruption_check_result.json")
    scoring, scoring_errors = load_json(directory / "limited_scoring_result.json")
    errors.extend(decision_errors + gold_errors + label_errors + proof_errors + watchdog_errors + overlap_errors + corruption_errors + scoring_errors)
    if decision.get("fixed_or_gold_patch_used_at_decision_time") is True:
        errors.append(f"{directory.name}: decision-time input manifest indicates gold/fixed patch leakage")
    for key in ["fixed_revision_used_at_decision_time", "gold_patch_used_at_decision_time", "corrected_files_used_as_repair_hints"]:
        if gold.get(key) is not False:
            errors.append(f"{directory.name}: gold patch exclusion check failed for {key}")
    if label.get("label_leakage_detected") is True:
        errors.append(f"{directory.name}: label leakage detected")
    if overlap.get("overlap_detected") is True:
        errors.append(f"{directory.name}: decision-time/outcome overlap detected")
    if corruption.get("corruption_detected") is True and str(scoring.get("result_classification", "")).startswith("positive"):
        errors.append(f"{directory.name}: positive episode cannot have corruption")
    if scoring.get("memory_enabled_outperformed_no_memory") is True and watchdog.get("watchdog_triggered") is True:
        errors.append(f"{directory.name}: watchdog-triggered path cannot count as memory outperformance")
    if proof.get("gold_patch_excluded") is False:
        errors.append(f"{directory.name}: proof ledger must exclude gold patch")
    errors.extend(verify_manifest(directory))
    return errors


def main() -> int:
    errors: list[str] = []
    for path in [WORKFLOW, RUNNER, PARSER]:
        if not path.exists():
            errors.append(f"missing v2.8b implementation file: {path}")
    if not OUTPUT_DIR.exists():
        errors.append(f"missing v2.8b output directory: {OUTPUT_DIR}")
    for name in REQUIRED_CAMPAIGN_FILES:
        path = OUTPUT_DIR / name
        if not path.exists():
            errors.append(f"missing v2.8b campaign artifact {name}")
        elif path.stat().st_size == 0:
            errors.append(f"empty v2.8b campaign artifact {name}")
    pool, pool_errors = load_json(OUTPUT_DIR / "candidate_pool.json")
    results, results_errors = load_json(OUTPUT_DIR / "campaign_results.json")
    aggregate, aggregate_errors = load_json(OUTPUT_DIR / "aggregate_bugsinpy_real_bug_memory_lift_assessment.json")
    policy, policy_errors = load_json(OUTPUT_DIR / "repair_comparison_runner_policy.json")
    v27e_pool, v27e_pool_errors = load_json(V27E_POOL)
    v27e_gate, v27e_gate_errors = load_json(V27E_GATE)
    v28, v28_errors = load_json(V28_AGG)
    v27d, v27d_errors = load_json(V27D_GATE)
    v27c, v27c_errors = load_json(V27C_POOL)
    v27b, v27b_errors = load_json(V27B_GATE)
    v27_ingest, v27_ingest_errors = load_json(V27_INGEST)
    v26, v26_errors = load_json(V26_RESULTS)
    v25, v25_errors = load_json(V25_STATUS)
    v24b, v24b_errors = load_json(V24B_AGG)
    v24, v24_errors = load_json(V24_AGG)
    v23, v23_errors = load_json(V23_AGG)
    v22, v22_errors = load_json(V22_AGG)
    v19, v19_errors = load_json(V19_AGG)
    v18, v18_errors = load_json(V18_AGG)
    e003, e003_errors = load_json(E003_RESULT)
    beta_replay, beta_replay_errors = load_json(BETA_REPLAY)
    beta_scoring, beta_scoring_errors = load_json(BETA_SCORING)
    alpha, alpha_errors = load_json(ALPHA_CLASSIFICATION)
    errors.extend(
        pool_errors
        + results_errors
        + aggregate_errors
        + policy_errors
        + v27e_pool_errors
        + v27e_gate_errors
        + v28_errors
        + v27d_errors
        + v27c_errors
        + v27b_errors
        + v27_ingest_errors
        + v26_errors
        + v25_errors
        + v24b_errors
        + v24_errors
        + v23_errors
        + v22_errors
        + v19_errors
        + v18_errors
        + e003_errors
        + beta_replay_errors
        + beta_scoring_errors
        + alpha_errors
    )
    candidates = {record.get("candidate") for record in pool.get("records", [])}
    required = {"youtube-dl:1", "black:8", "black:4"}
    if pool.get("count") != 3 or candidates != required:
        errors.append("candidate pool must contain exactly youtube-dl:1, black:8, and black:4")
    if policy.get("candidate_promotion_is_repair_success") is not False:
        errors.append("candidate promotion must not be treated as repair success")
    if policy.get("missing_logs_count_as_pass") is not False:
        errors.append("missing logs must not count as pass")
    if policy.get("no_op_flatline_success_allowed") is not False:
        errors.append("no-op/flatline behavior must not count as success")
    if results.get("full_scoring_allowed") is not False or results.get("controllergate_full_scoring") != "NOT_RUN":
        errors.append("full scoring must remain disallowed / NOT_RUN")
    if results.get("self_maintaining_software_demonstrated") is not False:
        errors.append("self-maintaining software must remain not demonstrated")
    if aggregate.get("limited_bugsinpy_real_bug_memory_lift_criteria_met") is True:
        scoreable = int(aggregate.get("scoreable_episode_count") or 0)
        positives = int(aggregate.get("positive_memory_episode_count") or 0)
        if scoreable < 3 or positives < 2:
            errors.append("memory lift can be claimed only if aggregate criteria are met")
    workflow_executed = results.get("workflow_executed") is True
    episode_dirs = sorted(path for path in OUTPUT_DIR.glob("episode_*") if path.is_dir())
    if workflow_executed:
        if len(episode_dirs) != 3:
            errors.append("executed v2.8b workflow must produce exactly three episode directories")
        for episode in episode_dirs:
            errors.extend(audit_episode(episode))
    else:
        if not (OUTPUT_DIR / "v2_8b_repair_comparison_not_executed_blocker_report.md").exists():
            errors.append("pending v2.8b workflow must include a blocker report")
        if results.get("scoreable_episode_count") != 0:
            errors.append("pending v2.8b workflow cannot have scoreable episodes")
    if v27e_pool.get("count") != 3:
        errors.append("v2.7e candidate promotion result must remain preserved")
    if v27e_gate.get("execute_v2_8") is not True or v27e_gate.get("target_matched_candidate_count") != 3:
        errors.append("v2.7e gate-open result must remain preserved")
    if v28.get("aggregate_result") != "blocked_bugsinpy_real_bug_replay_runtime_failure":
        errors.append("v2.8 blocked runtime result must remain preserved")
    if v27d.get("target_matched_candidate_count") != 2:
        errors.append("v2.7d pending-artifact lineage must remain preserved")
    if v27c.get("count") != 2:
        errors.append("v2.7c lineage must remain preserved")
    if v27b.get("target_matched_candidate_count") != 1:
        errors.append("v2.7b lineage must remain preserved")
    if v27_ingest.get("final_target_matched_candidate_count") != 1:
        errors.append("v2.7 artifact ingestion result must remain preserved")
    if v26.get("aggregate_result") != "insufficient_episode_count_for_bugsinpy_real_bug_memory_lift":
        errors.append("v2.6 insufficient-count result must remain preserved")
    if v25.get("promoted_candidate_count") != 1:
        errors.append("corrected v2.5 result must remain preserved")
    if v24b.get("aggregate_result") != "blocked_real_bug_runtime_unavailable":
        errors.append("v2.4b blocked runtime result must remain preserved")
    if v24.get("aggregate_result") != "blocked_real_external_bug_candidate_acquisition_failure":
        errors.append("v2.4 blocked acquisition result must remain preserved")
    if v23.get("aggregate_result") != "limited_known_external_or_benchmark_memory_lift_criteria_met":
        errors.append("v2.3 benchmark result must remain preserved")
    if v22.get("aggregate_result") != "limited_external_fork_controlled_fixture_memory_lift_criteria_met":
        errors.append("v2.2 controlled fixture result must remain preserved")
    if v19.get("aggregate_classification") != "limited_user_owned_organic_style_memory_lift_criteria_met":
        errors.append("v1.9 result must remain preserved")
    if v18.get("aggregate_classification") != "limited_seeded_controlled_memory_lift_criteria_met":
        errors.append("v1.8 result must remain preserved")
    if e003.get("result_classification") != "negative_evidence_no_memory_lift_on_seeded_controlled_episode":
        errors.append("Episode 003 negative result must remain preserved")
    if beta_replay.get("deterministic_replay_ready_count") != 0:
        errors.append("TatMapper quarantine must remain unchanged")
    if beta_scoring.get("full_scoring_allowed") is not False:
        errors.append("beta full scoring must remain false")
    alpha_summary = alpha.get("summary") if isinstance(alpha.get("summary"), dict) else {}
    if alpha_summary.get("full_scoring_allowed") is not False:
        errors.append("alpha full scoring must remain false")
    errors.extend(verify_manifest(OUTPUT_DIR))
    errors.extend(
        require_text(
            SHAREABLE_SUMMARY,
            [
                "v2.8b BugsInPy Linux Repair-Comparison Runner",
                "candidate promotion alone was not repair success",
                "No-memory and memory-enabled paths are compared under identical BugsInPy replay conditions",
                "Full scoring remains disallowed.",
                "Self-maintaining software remains undemonstrated.",
            ],
        )
    )
    if errors:
        print("v2.8b BugsInPy repair-comparison audit: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("v2.8b BugsInPy repair-comparison audit: PASS")
    print(f"workflow executed: {str(workflow_executed).lower()}")
    print(f"scoreable episodes: {results.get('scoreable_episode_count')}")
    print(f"aggregate: {aggregate.get('aggregate_result')}")
    print("full scoring allowed: false")
    print("self-maintaining software demonstrated: false")
    return 0


if __name__ == "__main__":
    sys.exit(main())
