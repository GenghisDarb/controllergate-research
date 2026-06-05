#!/usr/bin/env python3
"""Audit v2.3 known external / benchmark bug replay campaign outputs."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
INPUT_PATH = REPO_ROOT / "inputs" / "v2_3_known_external_bug_candidate_sources.json"
CAMPAIGN_DIR = REPO_ROOT / "outputs" / "v2_3_known_external_bug_replay_campaign"
V22_AGG = (
    REPO_ROOT
    / "outputs"
    / "v2_2_external_fork_controlled_fixture_replay_pilot"
    / "aggregate_external_fork_controlled_fixture_memory_lift_assessment.json"
)
V19_AGG = (
    REPO_ROOT
    / "outputs"
    / "v1_9_organic_style_replay_pilot_completion_pass"
    / "aggregate_v1_9_updated_memory_lift_assessment.json"
)
V18_AGG = REPO_ROOT / "outputs" / "v1_8_episodes_004_010_memory_relevance_campaign" / "aggregate_memory_lift_assessment.json"
E003_RESULT = REPO_ROOT / "outputs" / "v1_8_episode_003_torus_limited_replay_scoring" / "limited_scoring_result.json"
BETA_REPLAY = REPO_ROOT / "controllergate_v1_7_beta" / "outputs" / "v1_7_beta_replay_eligibility_plan.json"
BETA_SCORING = REPO_ROOT / "controllergate_v1_7_beta" / "traces" / "audits" / "limited_pilot_scoring" / "limited_pilot_scoring.json"
ALPHA_CLASSIFICATION = REPO_ROOT / "controllergate_v1_7_alpha" / "traces" / "audits" / "episode_review_classification.json"
SHAREABLE_SUMMARY = REPO_ROOT / "controllergate_v1_7_beta" / "reports" / "critic_review_package" / "shareable_summary.md"

REQUIRED_ACQUISITION_FILES = [
    "candidate_acquisition_plan.json",
    "candidate_triage_results.json",
    "candidate_promotion_table.json",
    "v2_3_ready_known_bug_candidate_pool.json",
    "v2_3_ready_benchmark_bug_candidate_pool.json",
    "v2_3_ready_dependency_drift_candidate_pool.json",
    "fallback_controlled_fixture_pool.json",
    "candidate_gap_report.md",
    "v2_3_handoff_recommendations.json",
    "campaign_results.json",
    "aggregate_known_external_bug_memory_lift_assessment.json",
    "campaign_summary.md",
    "SHA256SUMS.txt",
]

REQUIRED_EPISODE_FILES = [
    "episode_metadata.json",
    "source_repo_metadata.json",
    "license_summary.txt",
    "candidate_selection_record.json",
    "known_bug_reference.json",
    "target_repo_snapshot.json",
    "environment_snapshot.txt",
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
    "SHA256SUMS.txt",
]

VALID_CLASSIFICATIONS = {
    "positive_evidence_memory_lift_known_external_bug_episode",
    "positive_evidence_memory_lift_benchmark_bug_episode",
    "positive_evidence_memory_lift_dependency_drift_episode",
    "negative_evidence_no_memory_lift_known_external_bug_episode",
    "negative_evidence_memory_harm_or_corruption_known_external_bug_episode",
    "blocked_replay_gate_failed",
    "blocked_missing_baseline",
    "blocked_artifact_custody_failure",
    "blocked_decision_time_outcome_overlap",
    "inconclusive_equal_performance",
    "not_executed_resource_limit",
}


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


def require_text(path: Path, required: list[str]) -> list[str]:
    if not path.exists():
        return [f"missing text file: {path}"]
    text = path.read_text(encoding="utf-8")
    return [f"{path}: missing required text {item!r}" for item in required if item not in text]


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


def audit_episode(directory: Path) -> tuple[dict[str, Any], list[str]]:
    errors: list[str] = []
    for name in REQUIRED_EPISODE_FILES:
        path = directory / name
        if not path.exists():
            errors.append(f"{directory.name}: missing required artifact {name}")
        elif path.stat().st_size == 0:
            errors.append(f"{directory.name}: empty required artifact {name}")
    metadata, metadata_errors = load_json(directory / "episode_metadata.json")
    reference, reference_errors = load_json(directory / "known_bug_reference.json")
    no_memory, no_memory_errors = load_json(directory / "no_memory_outcome.json")
    memory, memory_errors = load_json(directory / "memory_enabled_outcome.json")
    comparison, comparison_errors = load_json(directory / "post_repair_comparison.json")
    corruption, corruption_errors = load_json(directory / "corruption_check_result.json")
    overlap, overlap_errors = load_json(directory / "decision_time_outcome_overlap_check.json")
    scoring, scoring_errors = load_json(directory / "limited_scoring_result.json")
    ledger, ledger_errors = load_json(directory / "proof_obligations_ledger.json")
    memory_inputs, memory_input_errors = load_json(directory / "memory_enabled_decision_time_inputs.json")
    errors.extend(
        metadata_errors
        + reference_errors
        + no_memory_errors
        + memory_errors
        + comparison_errors
        + corruption_errors
        + overlap_errors
        + scoring_errors
        + ledger_errors
        + memory_input_errors
    )

    classification = metadata.get("classification")
    if classification not in VALID_CLASSIFICATIONS:
        errors.append(f"{directory.name}: invalid classification {classification!r}")
    if metadata.get("episode_label") != "curated_benchmark_bug_entry":
        errors.append(f"{directory.name}: episode must be labeled curated_benchmark_bug_entry")
    if metadata.get("not_organic_external_bug") is not True:
        errors.append(f"{directory.name}: benchmark episode must be marked not organic external bug")
    if reference.get("reference_type") != "curated_benchmark_bug_entry":
        errors.append(f"{directory.name}: known_bug_reference must identify curated benchmark entry")
    if reference.get("not_organic_external_bug") is not True:
        errors.append(f"{directory.name}: reference must be marked not organic")
    if reference.get("corrected_version_available_but_excluded_from_decision_time") is not True:
        errors.append(f"{directory.name}: corrected benchmark files must be excluded from decision time")
    if "correct_python_programs" in json.dumps(memory_inputs.get("available_inputs", [])):
        errors.append(f"{directory.name}: corrected benchmark files leaked into decision-time inputs")
    if metadata.get("full_scoring_allowed") is not False or scoring.get("full_scoring_allowed") is not False:
        errors.append(f"{directory.name}: full scoring must remain false")
    if metadata.get("controllergate_full_scoring") != "NOT_RUN" or scoring.get("controllergate_full_scoring") != "NOT_RUN":
        errors.append(f"{directory.name}: ControllerGate full scoring must remain NOT_RUN")
    if metadata.get("self_maintaining_software_demonstrated") is not False or scoring.get("self_maintaining_software_demonstrated") is not False:
        errors.append(f"{directory.name}: self-maintaining software must remain false")
    if metadata.get("broad_organic_external_memory_lift_demonstrated") is not False:
        errors.append(f"{directory.name}: broad organic external memory lift must remain false")
    if no_memory.get("primary_command_passed") is not False:
        errors.append(f"{directory.name}: no-memory baseline should preserve failing benchmark result")
    if memory.get("primary_command_passed") is not True:
        errors.append(f"{directory.name}: memory-enabled command must pass")
    if comparison.get("memory_enabled_outperformed_no_memory") is not True:
        errors.append(f"{directory.name}: memory-enabled must outperform no-memory for positive benchmark episode")
    if corruption.get("memory_enabled", {}).get("corruption_detected") is not False:
        errors.append(f"{directory.name}: memory-enabled corruption must be false")
    if overlap.get("overlap_detected") is not False:
        errors.append(f"{directory.name}: decision-time/outcome overlap must be false")
    if overlap.get("decision_time_outcome_overlap_episode_count") != 0:
        errors.append(f"{directory.name}: overlap count must be 0")
    if ledger.get("proof_status") != "complete_limited_benchmark_replay_scoring_only":
        errors.append(f"{directory.name}: proof ledger status mismatch")
    if ledger.get("missing_obligations") != []:
        errors.append(f"{directory.name}: proof ledger missing obligations must be empty")
    signature = metadata.get("failure_signature")
    errors.extend(require_text(directory / "failing_log_raw.txt", [signature]))
    errors.extend(verify_manifest(directory))
    return metadata, errors


def main() -> int:
    errors: list[str] = []
    if not CAMPAIGN_DIR.exists():
        errors.append(f"missing v2.3 campaign directory: {CAMPAIGN_DIR}")
    if not INPUT_PATH.exists():
        errors.append(f"missing v2.3 input descriptor: {INPUT_PATH}")
    for name in REQUIRED_ACQUISITION_FILES:
        path = CAMPAIGN_DIR / name
        if not path.exists():
            errors.append(f"missing v2.3 acquisition/campaign artifact {name}")
        elif path.stat().st_size == 0:
            errors.append(f"empty v2.3 artifact {name}")

    inputs, input_errors = load_json(INPUT_PATH)
    plan, plan_errors = load_json(CAMPAIGN_DIR / "candidate_acquisition_plan.json")
    triage, triage_errors = load_json(CAMPAIGN_DIR / "candidate_triage_results.json")
    table, table_errors = load_json(CAMPAIGN_DIR / "candidate_promotion_table.json")
    known_pool, known_errors = load_json(CAMPAIGN_DIR / "v2_3_ready_known_bug_candidate_pool.json")
    benchmark_pool, benchmark_errors = load_json(CAMPAIGN_DIR / "v2_3_ready_benchmark_bug_candidate_pool.json")
    dependency_pool, dependency_errors = load_json(CAMPAIGN_DIR / "v2_3_ready_dependency_drift_candidate_pool.json")
    fallback_pool, fallback_errors = load_json(CAMPAIGN_DIR / "fallback_controlled_fixture_pool.json")
    handoff, handoff_errors = load_json(CAMPAIGN_DIR / "v2_3_handoff_recommendations.json")
    results, results_errors = load_json(CAMPAIGN_DIR / "campaign_results.json")
    aggregate, aggregate_errors = load_json(CAMPAIGN_DIR / "aggregate_known_external_bug_memory_lift_assessment.json")
    v22, v22_errors = load_json(V22_AGG)
    v19, v19_errors = load_json(V19_AGG)
    v18, v18_errors = load_json(V18_AGG)
    e003, e003_errors = load_json(E003_RESULT)
    beta_replay, beta_replay_errors = load_json(BETA_REPLAY)
    beta_scoring, beta_scoring_errors = load_json(BETA_SCORING)
    alpha_classification, alpha_errors = load_json(ALPHA_CLASSIFICATION)
    errors.extend(
        input_errors
        + plan_errors
        + triage_errors
        + table_errors
        + known_errors
        + benchmark_errors
        + dependency_errors
        + fallback_errors
        + handoff_errors
        + results_errors
        + aggregate_errors
        + v22_errors
        + v19_errors
        + v18_errors
        + e003_errors
        + beta_replay_errors
        + beta_scoring_errors
        + alpha_errors
    )

    if len(inputs.get("candidates", [])) < 6:
        errors.append("v2.3 input must contain benchmark and blocked source descriptors")
    if plan.get("full_scoring_allowed") is not False:
        errors.append("v2.3 plan full scoring must be false")
    if plan.get("controllergate_full_scoring") != "NOT_RUN":
        errors.append("v2.3 plan ControllerGate full scoring must be NOT_RUN")
    if plan.get("self_maintaining_software_claim_allowed") is not False:
        errors.append("v2.3 must not allow self-maintaining claim")
    if plan.get("broad_organic_external_memory_lift_claim_allowed") is not False:
        errors.append("v2.3 must not allow broad organic external memory-lift claim")
    if plan.get("corrected_benchmark_files_allowed_as_decision_time_input") is not False:
        errors.append("corrected benchmark files must be barred from decision time")

    records = triage.get("records") if isinstance(triage.get("records"), list) else []
    for record in records:
        status = record.get("promotion_status")
        if status in {
            "promoted_ready_for_v2_3_known_external_bug",
            "promoted_ready_for_v2_3_benchmark_bug",
            "promoted_ready_for_v2_3_dependency_drift",
        }:
            if record.get("readiness_score", 0) < 75:
                errors.append(f"{record.get('candidate_id')}: promoted readiness_score must be >= 75")
            if not record.get("failure_reference"):
                errors.append(f"{record.get('candidate_id')}: promoted candidate lacks real failure/reference")
            if status == "promoted_ready_for_v2_3_known_external_bug" and record.get("failure_reference_type") not in {
                "known_external_bug_reference",
                "known_issue_branch",
                "known_failing_test",
            }:
                errors.append(f"{record.get('candidate_id')}: known bug promotion lacks known external reference")
            if status == "promoted_ready_for_v2_3_benchmark_bug" and record.get("failure_reference_type") != "curated_benchmark_bug_entry":
                errors.append(f"{record.get('candidate_id')}: benchmark promotion lacks curated benchmark reference")

    known_records = known_pool.get("records") if isinstance(known_pool.get("records"), list) else []
    benchmark_records = benchmark_pool.get("records") if isinstance(benchmark_pool.get("records"), list) else []
    dependency_records = dependency_pool.get("records") if isinstance(dependency_pool.get("records"), list) else []
    fallback_records = fallback_pool.get("records") if isinstance(fallback_pool.get("records"), list) else []
    if len(known_records) != 0:
        errors.append("this v2.3 run should not have organic known external bug candidates")
    if len(benchmark_records) != 3:
        errors.append("expected 3 promoted benchmark bug candidates")
    if len(dependency_records) != 0:
        errors.append("expected 0 dependency-drift candidates")
    if len(fallback_records) != 3:
        errors.append("expected 3 fallback controlled fixture records preserved from v2.2")
    if fallback_pool.get("counts_toward_known_external_bug_aggregate") is not False:
        errors.append("fallback controlled fixtures must not count toward known external bug aggregate")
    if table.get("promotion_counts", {}).get("fallback_external_fork_controlled_fixture_only") != 3:
        errors.append("promotion table must preserve 3 fallback controlled fixtures")

    if handoff.get("promoted_known_or_benchmark_or_dependency_count") != 3:
        errors.append("handoff promoted known/benchmark/dependency count must be 3")
    if handoff.get("execute_v2_3_limited_replay") is not True:
        errors.append("handoff must execute v2.3 when 3 benchmark candidates promote")
    if handoff.get("fallback_fixtures_count_toward_known_external_bug_aggregate") is not False:
        errors.append("handoff must not count fallback fixtures")
    if handoff.get("full_scoring_allowed") is not False or handoff.get("controllergate_full_scoring") != "NOT_RUN":
        errors.append("handoff must keep full scoring NOT_RUN/disallowed")
    if handoff.get("self_maintaining_software_demonstrated") is not False:
        errors.append("handoff must keep self-maintaining software false")

    episode_dirs = sorted((CAMPAIGN_DIR / "episodes").glob("episode_*")) if (CAMPAIGN_DIR / "episodes").exists() else []
    if len(episode_dirs) != 3:
        errors.append("v2.3 must execute exactly 3 benchmark episode directories")
    metadatas: list[dict[str, Any]] = []
    for directory in episode_dirs:
        metadata, episode_errors = audit_episode(directory)
        metadatas.append(metadata)
        errors.extend(episode_errors)

    expected = "limited_known_external_or_benchmark_memory_lift_criteria_met"
    if results.get("executed_episode_count") != 3:
        errors.append("v2.3 executed episode count must be 3")
    if results.get("scoreable_episode_count") != 3:
        errors.append("v2.3 scoreable episode count must be 3")
    if results.get("positive_memory_episode_count") != 3:
        errors.append("v2.3 positive memory episode count must be 3")
    if results.get("decision_time_outcome_overlap_count") != 0:
        errors.append("v2.3 overlap count must be 0")
    if results.get("corruption_in_positive_memory_episode_count") != 0:
        errors.append("v2.3 positive corruption count must be 0")
    if results.get("aggregate_result") != expected or aggregate.get("aggregate_result") != expected:
        errors.append("v2.3 aggregate result mismatch")
    if aggregate.get("limited_known_external_or_benchmark_memory_lift_criteria_met") is not True:
        errors.append("v2.3 limited known/benchmark memory-lift criteria must be met")
    if aggregate.get("broad_organic_external_memory_lift_demonstrated") is not False:
        errors.append("broad organic external memory lift must remain false")
    if aggregate.get("self_maintaining_software_demonstrated") is not False:
        errors.append("self-maintaining software must remain false")
    if aggregate.get("full_scoring_allowed") is not False or aggregate.get("controllergate_full_scoring") != "NOT_RUN":
        errors.append("full scoring must remain NOT_RUN/disallowed")

    if v22.get("aggregate_result") != "limited_external_fork_controlled_fixture_memory_lift_criteria_met":
        errors.append("v2.2 controlled fixture result must remain preserved")
    if v19.get("aggregate_classification") != "limited_user_owned_organic_style_memory_lift_criteria_met":
        errors.append("v1.9 user-owned result must remain preserved")
    if v18.get("aggregate_classification") != "limited_seeded_controlled_memory_lift_criteria_met":
        errors.append("v1.8 seeded result must remain preserved")
    if e003.get("result_classification") != "negative_evidence_no_memory_lift_on_seeded_controlled_episode":
        errors.append("Episode 003 negative simple-task result must remain preserved")
    if beta_replay.get("deterministic_replay_ready_count") != 0:
        errors.append("TatMapper quarantine must remain unchanged")
    if beta_scoring.get("full_scoring_allowed") is not False:
        errors.append("beta full scoring must remain false")
    alpha_summary = alpha_classification.get("summary") if isinstance(alpha_classification.get("summary"), dict) else {}
    if alpha_summary.get("full_scoring_allowed") is not False:
        errors.append("alpha full scoring must remain false")

    errors.extend(verify_manifest(CAMPAIGN_DIR, recursive=True))
    errors.extend(
        require_text(
            CAMPAIGN_DIR / "campaign_summary.md",
            [
                "Known external bug replay is stronger than injected fixture evidence.",
                "Benchmark bugs must be labeled as benchmark evidence.",
                "Fallback controlled fixtures do not count as known external bug evidence.",
                "Broad organic external memory lift remains undemonstrated.",
                "Self-maintaining software remains undemonstrated.",
                "Full scoring remains disallowed.",
            ],
        )
    )
    errors.extend(
        require_text(
            SHAREABLE_SUMMARY,
            [
                "v2.3 Known External Bug Replay Campaign",
                "Fallback controlled fixtures do not count as known external bug evidence.",
                "Benchmark success does not prove arbitrary public repo performance.",
                "Self-maintaining software remains undemonstrated.",
                "Full scoring remains disallowed.",
            ],
        )
    )

    if errors:
        print("v2.3 known external bug replay campaign audit: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1

    print("v2.3 known external bug replay campaign audit: PASS")
    print("promoted benchmark candidates: 3")
    print("executed episodes: 3")
    print("scoreable episodes: 3")
    print("positive memory episodes: 3")
    print(f"aggregate: {expected}")
    print("broad organic external memory lift demonstrated: false")
    print("self-maintaining software demonstrated: false")
    print("full scoring allowed: false")
    return 0


if __name__ == "__main__":
    sys.exit(main())
