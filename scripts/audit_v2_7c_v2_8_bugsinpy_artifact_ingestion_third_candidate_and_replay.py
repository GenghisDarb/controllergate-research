#!/usr/bin/env python3
"""Audit v2.7c/v2.8 BugsInPy artifact ingestion and conditional replay gate."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = REPO_ROOT / "outputs" / "v2_7c_bugsinpy_direct_runner_artifact_ingestion"
V28_DIR = REPO_ROOT / "outputs" / "v2_8_bugsinpy_real_bug_limited_replay_execution"
V27E_GATE = REPO_ROOT / "outputs" / "v2_7e_bugsinpy_third_candidate_artifact_ingestion" / "v2_8_execution_gate_decision.json"
V27B_GATE = REPO_ROOT / "outputs" / "v2_7b_bugsinpy_direct_target_runner_fix" / "v2_8_execution_gate_decision.json"
V27B_AUDIT_GATE = REPO_ROOT / "outputs" / "v2_7b_bugsinpy_direct_target_runner_fix" / "target_failure_matching_summary.json"
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
    "artifact_ingestion_summary.json",
    "artifact_sha256_verification.json",
    "candidate_reclassification_table.json",
    "black_8_promotion_record.json",
    "black_2_blocker_record.json",
    "target_failure_matching_summary.json",
    "v2_8_gate_status_after_artifact.json",
    "third_candidate_acquisition_plan.json",
    "third_candidate_acquisition_results.json",
    "third_candidate_attempt_matrix.json",
    "third_candidate_rejection_table.json",
    "third_candidate_selection_policy.json",
    "promoted_bugsinpy_real_bug_candidate_pool.json",
    "blocked_candidate_summary.json",
    "v2_8_execution_gate_decision.json",
    "campaign_summary.md",
    "v2_8_not_executed_blocker_report.md",
    "SHA256SUMS.txt",
]

REQUIRED_ATTEMPT_FILES = [
    "candidate_metadata.json",
    "selection_reason.json",
    "direct_command_source.json",
    "checkout_command.txt",
    "checkout_log_raw.txt",
    "dependency_install_plan.json",
    "dependency_install_commands.txt",
    "dependency_install_log_raw.txt",
    "compile_command.txt",
    "compile_log_raw.txt",
    "direct_test_command.txt",
    "direct_test_log_raw.txt",
    "failure_signature.txt",
    "target_failure_match_check.json",
    "wrapper_contamination_check.json",
    "gold_patch_exclusion_plan.json",
    "replay_feasibility_result.json",
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


def audit_attempt_dir(directory: Path) -> list[str]:
    errors: list[str] = []
    for name in REQUIRED_ATTEMPT_FILES:
        path = directory / name
        if not path.exists():
            errors.append(f"{directory.name}: missing {name}")
        elif path.stat().st_size == 0:
            errors.append(f"{directory.name}: empty {name}")
    match, match_errors = load_json(directory / "target_failure_match_check.json")
    wrapper, wrapper_errors = load_json(directory / "wrapper_contamination_check.json")
    exclusion, exclusion_errors = load_json(directory / "gold_patch_exclusion_plan.json")
    feasibility, feasibility_errors = load_json(directory / "replay_feasibility_result.json")
    errors.extend(match_errors + wrapper_errors + exclusion_errors + feasibility_errors)
    promoted = str(match.get("promotion_status", "")).startswith("promoted")
    if promoted:
        errors.append(f"{directory.name}: third-candidate attempt cannot be promoted in current artifact")
    if wrapper.get("wrapper_contamination_detected") is True:
        errors.append(f"{directory.name}: wrapper-contaminated third-candidate attempt must stay blocked")
    if exclusion.get("fixed_revision_used_at_decision_time") is not False:
        errors.append(f"{directory.name}: fixed revision cannot be decision-time input")
    if exclusion.get("gold_patch_used_at_decision_time") is not False:
        errors.append(f"{directory.name}: gold patch cannot be decision-time input")
    if feasibility.get("fixed_or_gold_patch_used_at_decision_time") is True:
        errors.append(f"{directory.name}: replay feasibility indicates gold/fixed patch leakage")
    errors.extend(verify_manifest(directory))
    return errors


def main() -> int:
    errors: list[str] = []
    if not OUTPUT_DIR.exists():
        errors.append(f"missing output directory: {OUTPUT_DIR}")
    for name in REQUIRED_FILES:
        path = OUTPUT_DIR / name
        if not path.exists():
            errors.append(f"missing v2.7c output artifact {name}")
        elif path.stat().st_size == 0:
            errors.append(f"empty v2.7c output artifact {name}")
    ingestion, ingestion_errors = load_json(OUTPUT_DIR / "artifact_ingestion_summary.json")
    verification, verification_errors = load_json(OUTPUT_DIR / "artifact_sha256_verification.json")
    black8, black8_errors = load_json(OUTPUT_DIR / "black_8_promotion_record.json")
    black2, black2_errors = load_json(OUTPUT_DIR / "black_2_blocker_record.json")
    matching, matching_errors = load_json(OUTPUT_DIR / "target_failure_matching_summary.json")
    gate, gate_errors = load_json(OUTPUT_DIR / "v2_8_execution_gate_decision.json")
    attempts, attempts_errors = load_json(OUTPUT_DIR / "third_candidate_attempt_matrix.json")
    promoted_pool, promoted_errors = load_json(OUTPUT_DIR / "promoted_bugsinpy_real_bug_candidate_pool.json")
    v27b_gate, v27b_gate_errors = load_json(V27B_GATE)
    v27b_matching, v27b_matching_errors = load_json(V27B_AUDIT_GATE)
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
        ingestion_errors
        + verification_errors
        + black8_errors
        + black2_errors
        + matching_errors
        + gate_errors
        + attempts_errors
        + promoted_errors
        + v27b_gate_errors
        + v27b_matching_errors
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
    if verification.get("verification_clean") is not True:
        errors.append("artifact SHA256 verification must be clean")
    if verification.get("hash_failure_count") != 0:
        errors.append("artifact hash failure count must be 0")
    if black8.get("candidate") != "black:8":
        errors.append("black:8 promotion record missing")
    if black8.get("promotion_status") != "promoted_ready_for_v2_8_bugsinpy_real_bug":
        errors.append("black:8 must be promoted after clean direct replay")
    if black8.get("target_failure_matched") is not True:
        errors.append("black:8 cannot be promoted without target_failure_matched true")
    if black8.get("wrapper_contaminated") is not False:
        errors.append("black:8 cannot be promoted with wrapper contamination")
    if black8.get("dependency_or_runtime_blocked") is not False:
        errors.append("black:8 cannot be promoted with dependency/runtime blocker")
    if black8.get("fixed_or_gold_patch_used_at_decision_time") is not False:
        errors.append("black:8 cannot be promoted with gold/fixed patch leakage")
    if black2.get("candidate") != "black:2":
        errors.append("black:2 blocker record missing")
    if black2.get("promotion_status") == "promoted_ready_for_v2_8_bugsinpy_real_bug":
        errors.append("black:2 must not promote unless clean direct target replay exists")
    if black2.get("dependency_or_runtime_blocked") is not True:
        errors.append("black:2 should remain runtime/environment blocked")
    if matching.get("final_clean_target_matched_count") != 2:
        errors.append("v2.7c final clean target-matched count must be 2")
    if gate.get("target_matched_candidate_count") != matching.get("final_clean_target_matched_count"):
        errors.append("v2.8 gate count must match target-failure summary")
    if gate.get("execute_v2_8") is not False or gate.get("repair_scoring_run") is not False:
        errors.append("v2.8 must not execute when only two clean candidates exist")
    if V28_DIR.exists() and not later_v28_gate_passed():
        errors.append("v2.8 output directory must not exist unless a later gate passes")
    if promoted_pool.get("count") != 2:
        errors.append("promoted candidate pool must contain exactly two clean target-matched candidates")
    attempt_count = attempts.get("attempted_count")
    if not isinstance(attempt_count, int) or attempt_count <= 0 or attempt_count > 12:
        errors.append("third-candidate attempt count must be between 1 and 12")
    for record in attempts.get("attempts", []):
        directory_name = record.get("directory")
        if directory_name:
            errors.extend(audit_attempt_dir(OUTPUT_DIR / directory_name))
    if v27b_gate.get("target_matched_candidate_count") != 1:
        errors.append("v2.7b pre-artifact gate must remain preserved at one target-matched candidate")
    if v27b_matching.get("final_clean_target_matched_count") != 1:
        errors.append("v2.7b pre-artifact matching summary must remain preserved at one target-matched candidate")
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
                "v2.7c/v2.8 BugsInPy Direct Runner Artifact Ingestion, Third-Candidate Recovery, and Conditional Replay",
                "v2.7c promotes black:8 from clean direct target replay.",
                "black:2 remains blocked by runtime/environment failure.",
                "Target-failure matching remains mandatory.",
                "Dependency/import/wrapper failures do not count as target bug replay.",
                "Full scoring remains disallowed.",
                "Self-maintaining software remains undemonstrated.",
            ],
        )
    )
    if errors:
        print("v2.7c/v2.8 BugsInPy artifact ingestion and conditional replay audit: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("v2.7c/v2.8 BugsInPy artifact ingestion and conditional replay audit: PASS")
    print("final clean target-matched candidates: 2")
    print("v2.8 executed: false")
    print("repair scoring run: false")
    print("full scoring allowed: false")
    print("self-maintaining software demonstrated: false")
    return 0


if __name__ == "__main__":
    sys.exit(main())
