#!/usr/bin/env python3
"""Audit v2.7e third-candidate ingestion and v2.8 limited replay gate."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = REPO_ROOT / "outputs" / "v2_7e_bugsinpy_third_candidate_artifact_ingestion"
V28_DIR = REPO_ROOT / "outputs" / "v2_8_bugsinpy_real_bug_limited_replay_execution"
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
SHAREABLE_SUMMARY = REPO_ROOT / "controllergate_v1_7_beta" / "reports" / "critic_review_package" / "shareable_summary.md"

REQUIRED_V27E_FILES = [
    "artifact_ingestion_summary.json",
    "artifact_sha256_verification.json",
    "candidate_reclassification_table.json",
    "black_4_promotion_record.json",
    "blocked_candidate_records.json",
    "target_failure_matching_summary.json",
    "promoted_bugsinpy_real_bug_candidate_pool.json",
    "v2_8_execution_gate_decision.json",
    "SHA256SUMS.txt",
]

REQUIRED_V28_CAMPAIGN_FILES = [
    "campaign_plan.json",
    "campaign_results.json",
    "aggregate_bugsinpy_real_bug_memory_lift_assessment.json",
    "campaign_summary.md",
    "candidate_source_integrity_check.json",
    "SHA256SUMS.txt",
]

REQUIRED_EPISODE_FILES = [
    "episode_metadata.json",
    "source_repo_metadata.json",
    "license_summary.txt",
    "candidate_selection_record.json",
    "bugsinpy_bug_reference.json",
    "target_repo_snapshot.json",
    "environment_snapshot.txt",
    "decision_time_input_manifest.json",
    "gold_patch_exclusion_check.json",
    "failing_command.txt",
    "failing_log_raw.txt",
    "failure_signature.txt",
    "pre_repair_replay_transcript.txt",
    "no_memory_decision_time_inputs.json",
    "no_memory_action_trace.json",
    "no_memory_repair_patch.diff",
    "no_memory_post_repair_log_raw.txt",
    "no_memory_outcome.json",
    "memory_enabled_decision_time_inputs.json",
    "memory_enabled_action_trace.json",
    "memory_evidence_used.json",
    "memory_enabled_repair_patch.diff",
    "memory_enabled_post_repair_log_raw.txt",
    "memory_enabled_outcome.json",
    "post_repair_comparison.json",
    "corruption_check_result.json",
    "decision_time_outcome_overlap_check.json",
    "limited_scoring_result.json",
    "proof_obligations_ledger.json",
    "apoptosis_watchdog_result.json",
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
    metadata, metadata_errors = load_json(directory / "episode_metadata.json")
    scoring, scoring_errors = load_json(directory / "limited_scoring_result.json")
    overlap, overlap_errors = load_json(directory / "decision_time_outcome_overlap_check.json")
    gold, gold_errors = load_json(directory / "gold_patch_exclusion_check.json")
    watchdog, watchdog_errors = load_json(directory / "apoptosis_watchdog_result.json")
    proof, proof_errors = load_json(directory / "proof_obligations_ledger.json")
    corruption, corruption_errors = load_json(directory / "corruption_check_result.json")
    decision_inputs, decision_errors = load_json(directory / "decision_time_input_manifest.json")
    errors.extend(
        metadata_errors
        + scoring_errors
        + overlap_errors
        + gold_errors
        + watchdog_errors
        + proof_errors
        + corruption_errors
        + decision_errors
    )
    if metadata.get("classification") != "blocked_runtime_replay_failure":
        errors.append(f"{directory.name}: expected blocked runtime classification")
    if scoring.get("result_classification") != "blocked_runtime_replay_failure":
        errors.append(f"{directory.name}: scoring result should be blocked runtime")
    if scoring.get("scoreable") is not False:
        errors.append(f"{directory.name}: blocked runtime episode must not be scoreable")
    if scoring.get("memory_enabled_outperformed_no_memory") is not False:
        errors.append(f"{directory.name}: memory cannot outperform no-memory in blocked runtime episode")
    if overlap.get("overlap_detected") is not False:
        errors.append(f"{directory.name}: decision-time/outcome overlap must be false")
    for key in [
        "fixed_revision_used_at_decision_time",
        "gold_patch_used_at_decision_time",
        "gold_patch_present_in_no_memory_inputs",
        "gold_patch_present_in_memory_enabled_inputs",
        "corrected_files_used_as_repair_hints",
    ]:
        if gold.get(key) is not False:
            errors.append(f"{directory.name}: gold/fixed exclusion failed for {key}")
    if decision_inputs.get("label_leakage_detected") is not False:
        errors.append(f"{directory.name}: label leakage must remain false")
    if proof.get("scoreable") is not False or proof.get("gold_patch_excluded") is not True:
        errors.append(f"{directory.name}: proof obligations must block scoring and exclude gold patch")
    if watchdog.get("flatline_or_no_op_counted_as_success") is not False:
        errors.append(f"{directory.name}: flatline/no-op must not count as success")
    if corruption.get("corruption_detected") is not False:
        errors.append(f"{directory.name}: corruption must not be counted in blocked runtime shell")
    errors.extend(verify_manifest(directory))
    return errors


def main() -> int:
    errors: list[str] = []
    if not OUTPUT_DIR.exists():
        errors.append(f"missing output directory: {OUTPUT_DIR}")
    for name in REQUIRED_V27E_FILES:
        path = OUTPUT_DIR / name
        if not path.exists():
            errors.append(f"missing v2.7e output {name}")
        elif path.stat().st_size == 0:
            errors.append(f"empty v2.7e output {name}")
    ingestion, ingestion_errors = load_json(OUTPUT_DIR / "artifact_ingestion_summary.json")
    verification, verification_errors = load_json(OUTPUT_DIR / "artifact_sha256_verification.json")
    black4, black4_errors = load_json(OUTPUT_DIR / "black_4_promotion_record.json")
    blocked, blocked_errors = load_json(OUTPUT_DIR / "blocked_candidate_records.json")
    matching, matching_errors = load_json(OUTPUT_DIR / "target_failure_matching_summary.json")
    pool, pool_errors = load_json(OUTPUT_DIR / "promoted_bugsinpy_real_bug_candidate_pool.json")
    gate, gate_errors = load_json(OUTPUT_DIR / "v2_8_execution_gate_decision.json")
    v27d_gate, v27d_errors = load_json(V27D_GATE)
    v27c_pool, v27c_errors = load_json(V27C_POOL)
    v27b_gate, v27b_errors = load_json(V27B_GATE)
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
        + black4_errors
        + blocked_errors
        + matching_errors
        + pool_errors
        + gate_errors
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
    if verification.get("verification_clean") is not True:
        errors.append("artifact SHA256 verification must be clean")
    if verification.get("hash_failure_count") != 0:
        errors.append("artifact hash failures must be 0")
    if black4.get("candidate") != "black:4":
        errors.append("black:4 promotion record missing")
    if black4.get("promotion_status") != "promoted_ready_for_v2_8_bugsinpy_real_bug":
        errors.append("black:4 must be promoted")
    if black4.get("target_failure_matched") is not True:
        errors.append("black:4 target failure must be matched")
    if black4.get("wrapper_contaminated") is not False:
        errors.append("black:4 wrapper contamination must be false")
    if black4.get("dependency_or_runtime_blocked") is not False:
        errors.append("black:4 dependency/runtime blocker must be false")
    if black4.get("fixed_or_gold_patch_used_at_decision_time") is not False:
        errors.append("black:4 must not use gold/fixed patch at decision time")
    blocked_candidates = {record.get("candidate"): record for record in blocked.get("records", [])}
    for candidate in ["black:1", "black:3"]:
        record = blocked_candidates.get(candidate)
        if not record:
            errors.append(f"{candidate} blocked record missing")
        elif record.get("promotion_status") == "promoted_ready_for_v2_8_bugsinpy_real_bug":
            errors.append(f"{candidate} must not be promoted")
    if matching.get("final_clean_target_matched_count") != 3:
        errors.append("final clean target-matched count must be 3")
    required = {"youtube-dl:1", "black:8", "black:4"}
    pool_candidates = {record.get("candidate") for record in pool.get("records", [])}
    if pool.get("count") != 3 or pool_candidates != required:
        errors.append("promoted pool must contain youtube-dl:1, black:8, and black:4")
    if gate.get("target_matched_candidate_count") != 3 or gate.get("execute_v2_8") is not True:
        errors.append("v2.8 gate must execute after three clean candidates")
    if gate.get("repair_scoring_run") is not False:
        errors.append("repair scoring should remain false until post-repair validation exists")
    if not V28_DIR.exists():
        errors.append("v2.8 output directory must exist after gate opens")
    for name in REQUIRED_V28_CAMPAIGN_FILES:
        path = V28_DIR / name
        if not path.exists():
            errors.append(f"missing v2.8 campaign artifact {name}")
        elif path.stat().st_size == 0:
            errors.append(f"empty v2.8 campaign artifact {name}")
    campaign, campaign_errors = load_json(V28_DIR / "campaign_results.json")
    aggregate, aggregate_errors = load_json(V28_DIR / "aggregate_bugsinpy_real_bug_memory_lift_assessment.json")
    integrity, integrity_errors = load_json(V28_DIR / "candidate_source_integrity_check.json")
    errors.extend(campaign_errors + aggregate_errors + integrity_errors)
    if integrity.get("required_candidates_present") is not True:
        errors.append("v2.8 source integrity check must include the three required candidates")
    if campaign.get("executed_episode_count") != 3:
        errors.append("v2.8 must create three candidate execution shells")
    if campaign.get("scoreable_episode_count") != 0:
        errors.append("v2.8 should have zero scoreable episodes without post-repair validation logs")
    if campaign.get("aggregate_result") != "blocked_bugsinpy_real_bug_replay_runtime_failure":
        errors.append("v2.8 aggregate should be blocked runtime failure")
    if campaign.get("limited_bugsinpy_real_bug_memory_lift_criteria_met") is not False:
        errors.append("limited BugsInPy memory lift must not be claimed")
    if campaign.get("full_scoring_allowed") is not False or campaign.get("controllergate_full_scoring") != "NOT_RUN":
        errors.append("full scoring must remain disallowed / NOT_RUN")
    if campaign.get("self_maintaining_software_demonstrated") is not False:
        errors.append("self-maintaining software must remain not demonstrated")
    if campaign.get("decision_time_outcome_overlap_count") != 0:
        errors.append("decision-time/outcome overlap count must remain 0")
    if campaign.get("label_leakage_count") != 0:
        errors.append("label leakage count must remain 0")
    if campaign.get("apoptosis_watchdog_triggered_count") != 0:
        errors.append("apoptosis watchdog count must remain 0")
    if campaign.get("corruption_count") != 0:
        errors.append("corruption count must remain 0")
    if aggregate.get("limited_bugsinpy_real_bug_memory_lift_criteria_met") is not False:
        errors.append("aggregate must not claim BugsInPy memory lift")
    for episode in sorted((V28_DIR).glob("episode_*")):
        if episode.is_dir():
            errors.extend(audit_episode(episode))
    if len([path for path in V28_DIR.glob("episode_*") if path.is_dir()]) != 3:
        errors.append("v2.8 must contain exactly three episode directories")
    if v27d_gate.get("target_matched_candidate_count") != 2:
        errors.append("v2.7d pending-artifact result must remain preserved")
    if v27c_pool.get("count") != 2:
        errors.append("v2.7c promoted pool must remain preserved at two")
    if v27b_gate.get("target_matched_candidate_count") != 1:
        errors.append("v2.7b pre-artifact result must remain preserved")
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
        errors.append("v2.3 QuixBugs result must remain preserved")
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
    errors.extend(verify_manifest(V28_DIR))
    errors.extend(
        require_text(
            SHAREABLE_SUMMARY,
            [
                "v2.7e/v2.8 BugsInPy Third-Candidate Ingestion and Limited Replay Execution",
                "v2.7e promotes black:4 from clean direct target replay.",
                "The clean BugsInPy target-matched pool reached 3 candidates",
                "Candidate promotion is not repair success.",
                "Limited BugsInPy memory lift is not demonstrated.",
                "Full scoring remains disallowed.",
                "Self-maintaining software remains undemonstrated.",
            ],
        )
    )
    if errors:
        print("v2.7e/v2.8 BugsInPy third-candidate ingestion and replay audit: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("v2.7e/v2.8 BugsInPy third-candidate ingestion and replay audit: PASS")
    print("final clean target-matched candidates: 3")
    print("v2.8 gate opened: true")
    print("scoreable episodes: 0")
    print("aggregate: blocked_bugsinpy_real_bug_replay_runtime_failure")
    print("full scoring allowed: false")
    print("self-maintaining software demonstrated: false")
    return 0


if __name__ == "__main__":
    sys.exit(main())
