#!/usr/bin/env python3
"""Audit v2.7d/v2.8 BugsInPy third-candidate direct runner expansion."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = REPO_ROOT / "outputs" / "v2_7d_bugsinpy_third_candidate_direct_runner_expansion"
V28_DIR = REPO_ROOT / "outputs" / "v2_8_bugsinpy_real_bug_limited_replay_execution"
V27E_GATE = REPO_ROOT / "outputs" / "v2_7e_bugsinpy_third_candidate_artifact_ingestion" / "v2_8_execution_gate_decision.json"
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "v2_7d_bugsinpy_third_candidate_direct_runner_expansion.yml"
RUNNER = REPO_ROOT / "scripts" / "v2_7d_bugsinpy_third_candidate_direct_runner_expansion.py"
V27C_GATE = REPO_ROOT / "outputs" / "v2_7c_bugsinpy_direct_runner_artifact_ingestion" / "v2_8_execution_gate_decision.json"
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
SHAREABLE_SUMMARY = REPO_ROOT / "controllergate_v1_7_beta" / "reports" / "critic_review_package" / "shareable_summary.md"

REQUIRED_FILES = [
    "third_candidate_direct_runner_plan.json",
    "candidate_selection_policy.json",
    "runner_status.json",
    "promoted_bugsinpy_real_bug_candidate_pool.json",
    "blocked_candidate_summary.json",
    "v2_8_execution_gate_decision.json",
    "v2_8_not_executed_blocker_report.md",
    "campaign_summary.md",
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


def later_v28_gate_passed() -> bool:
    if not V27E_GATE.exists():
        return False
    data, _ = load_json(V27E_GATE)
    return data.get("execute_v2_8") is True and data.get("target_matched_candidate_count") == 3


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


def require_text(path: Path, required: list[str]) -> list[str]:
    if not path.exists():
        return [f"missing text file: {path}"]
    text = path.read_text(encoding="utf-8")
    return [f"{path}: missing required text {item!r}" for item in required if item not in text]


def main() -> int:
    errors: list[str] = []
    if not WORKFLOW.exists():
        errors.append("missing v2.7d GitHub Actions workflow")
    if not RUNNER.exists():
        errors.append("missing v2.7d direct runner script")
    if not OUTPUT_DIR.exists():
        errors.append(f"missing output directory: {OUTPUT_DIR}")
    for name in REQUIRED_FILES:
        path = OUTPUT_DIR / name
        if not path.exists():
            errors.append(f"missing v2.7d output artifact {name}")
        elif path.stat().st_size == 0:
            errors.append(f"empty v2.7d output artifact {name}")
    plan, plan_errors = load_json(OUTPUT_DIR / "third_candidate_direct_runner_plan.json")
    policy, policy_errors = load_json(OUTPUT_DIR / "candidate_selection_policy.json")
    status, status_errors = load_json(OUTPUT_DIR / "runner_status.json")
    gate, gate_errors = load_json(OUTPUT_DIR / "v2_8_execution_gate_decision.json")
    pool, pool_errors = load_json(OUTPUT_DIR / "promoted_bugsinpy_real_bug_candidate_pool.json")
    v27c_gate, v27c_gate_errors = load_json(V27C_GATE)
    v27c_pool, v27c_pool_errors = load_json(V27C_POOL)
    v27b_gate, v27b_gate_errors = load_json(V27B_GATE)
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
        plan_errors
        + policy_errors
        + status_errors
        + gate_errors
        + pool_errors
        + v27c_gate_errors
        + v27c_pool_errors
        + v27b_gate_errors
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
    if plan.get("budget") != 12:
        errors.append("v2.7d runner budget must be 12")
    if policy.get("dependency_import_runtime_wrapper_failures_count_as_target_replay") is not False:
        errors.append("dependency/import/runtime/wrapper failures must not count as target replay")
    if policy.get("fixed_or_gold_patch_allowed_at_decision_time") is not False:
        errors.append("gold/fixed patch cannot be decision-time input")
    if status.get("artifact_ingested") is not False:
        errors.append("v2.7d local gate should not claim artifact ingestion")
    if gate.get("target_matched_candidate_count") != 2:
        errors.append("v2.7d gate must start from two clean target-matched candidates")
    if gate.get("execute_v2_8") is not False or gate.get("repair_scoring_run") is not False:
        errors.append("v2.8 must not execute before third candidate artifact is ingested")
    if V28_DIR.exists() and not later_v28_gate_passed():
        errors.append("v2.8 output directory must not exist unless a later gate passes")
    if pool.get("count") != 2:
        errors.append("v2.7d promoted pool must preserve two clean target-matched candidates")
    if v27c_gate.get("target_matched_candidate_count") != 2:
        errors.append("v2.7c target-matched count must remain 2")
    if v27c_pool.get("count") != 2:
        errors.append("v2.7c promoted pool must remain 2")
    if v27b_gate.get("target_matched_candidate_count") != 1:
        errors.append("v2.7b pre-artifact target count must remain 1")
    if v27_ingest.get("final_target_matched_candidate_count") != 1:
        errors.append("v2.7 artifact ingestion result must remain preserved")
    if v26.get("aggregate_result") != "insufficient_episode_count_for_bugsinpy_real_bug_memory_lift":
        errors.append("v2.6 insufficient-count result must remain preserved")
    if v25.get("promoted_candidate_count") != 1:
        errors.append("corrected v2.5 promoted count must remain 1")
    if v24b.get("aggregate_result") != "blocked_real_bug_runtime_unavailable":
        errors.append("v2.4b blocked runtime result must remain preserved")
    if v24.get("aggregate_result") != "blocked_real_external_bug_candidate_acquisition_failure":
        errors.append("v2.4 blocked acquisition result must remain preserved")
    if v23.get("aggregate_result") != "limited_known_external_or_benchmark_memory_lift_criteria_met":
        errors.append("v2.3 QuixBugs benchmark result must remain preserved")
    if v22.get("aggregate_result") != "limited_external_fork_controlled_fixture_memory_lift_criteria_met":
        errors.append("v2.2 controlled fixture result must remain preserved")
    if v19.get("aggregate_classification") != "limited_user_owned_organic_style_memory_lift_criteria_met":
        errors.append("v1.9 user-owned result must remain preserved")
    if v18.get("aggregate_classification") != "limited_seeded_controlled_memory_lift_criteria_met":
        errors.append("v1.8 seeded result must remain preserved")
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
                "v2.7d/v2.8 BugsInPy Third-Candidate Direct Runner Expansion",
                "rejects dependency/import/runtime/wrapper failures",
                "Candidate promotion is not repair success.",
                "Full scoring remains disallowed.",
                "Memory lift and self-maintaining software remain undemonstrated.",
            ],
        )
    )
    if errors:
        print("v2.7d/v2.8 BugsInPy third-candidate direct runner expansion audit: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("v2.7d/v2.8 BugsInPy third-candidate direct runner expansion audit: PASS")
    print("starting clean target-matched candidates: 2")
    print("v2.8 executed: false")
    print("repair scoring run: false")
    print("full scoring allowed: false")
    print("self-maintaining software demonstrated: false")
    return 0


if __name__ == "__main__":
    sys.exit(main())
