#!/usr/bin/env python3
"""Audit the v1.9 organic-style replay pilot completion pass."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
COMPLETION_DIR = REPO_ROOT / "outputs" / "v1_9_organic_style_replay_pilot_completion_pass"
PRIOR_PILOT_DIR = REPO_ROOT / "outputs" / "v1_9_episodes_011_013_organic_style_replay_pilot"
SUMMARY_PATH = (
    REPO_ROOT / "controllergate_v1_7_beta" / "reports" / "critic_review_package" / "shareable_summary.md"
)
V18_CAMPAIGN_ASSESSMENT_PATH = (
    REPO_ROOT / "outputs" / "v1_8_episodes_004_010_memory_relevance_campaign" / "aggregate_memory_lift_assessment.json"
)
EPISODE_003_RESULT_PATH = (
    REPO_ROOT / "outputs" / "v1_8_episode_003_torus_limited_replay_scoring" / "limited_scoring_result.json"
)
BETA_REPLAY_PLAN_PATH = REPO_ROOT / "controllergate_v1_7_beta" / "outputs" / "v1_7_beta_replay_eligibility_plan.json"
BETA_SCORING_PATH = (
    REPO_ROOT / "controllergate_v1_7_beta" / "traces" / "audits" / "limited_pilot_scoring" / "limited_pilot_scoring.json"
)
ALPHA_CLASSIFICATION_PATH = (
    REPO_ROOT / "controllergate_v1_7_alpha" / "traces" / "audits" / "episode_review_classification.json"
)

REQUIRED_COMPLETION_FILES = [
    "completion_pass_plan.json",
    "candidate_search_log.json",
    "completion_pass_results.json",
    "completion_pass_summary.md",
    "aggregate_v1_9_updated_memory_lift_assessment.json",
    "falsification_and_stop_conditions.md",
    "SHA256SUMS.txt",
]

REQUIRED_EPISODE_FILES = [
    "episode_metadata.json",
    "target_repo_snapshot.json",
    "candidate_selection_record.json",
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


def verify_sha256_manifest(base_dir: Path, recursive: bool = False) -> list[str]:
    manifest_path = base_dir / "SHA256SUMS.txt"
    if not manifest_path.exists():
        return [f"missing SHA256SUMS.txt in {base_dir}"]
    errors: list[str] = []
    seen: set[str] = set()
    for line_no, line in enumerate(manifest_path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        parts = line.split()
        if len(parts) != 2:
            errors.append(f"{manifest_path}:{line_no}: expected '<sha256>  <path>'")
            continue
        expected, rel = parts
        seen.add(rel)
        path = base_dir / rel
        if not path.exists():
            errors.append(f"{manifest_path}:{line_no}: missing artifact {rel}")
            continue
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != expected:
            errors.append(f"{manifest_path}:{line_no}: hash mismatch for {rel}")
    if recursive:
        for path in base_dir.rglob("*"):
            if path.is_file() and path.name != "SHA256SUMS.txt":
                rel = str(path.relative_to(base_dir)).replace("\\", "/")
                if rel not in seen:
                    errors.append(f"top-level SHA256SUMS missing artifact entry {rel}")
    return errors


def audit_episode_014() -> list[str]:
    errors: list[str] = []
    directory = COMPLETION_DIR / "episode_014"
    if not directory.exists():
        return ["missing episode_014 artifact directory"]
    for name in REQUIRED_EPISODE_FILES:
        path = directory / name
        if not path.exists():
            errors.append(f"episode_014: missing required artifact {name}")
        elif path.stat().st_size == 0:
            errors.append(f"episode_014: required artifact is empty {name}")

    metadata, metadata_errors = load_json(directory / "episode_metadata.json")
    scoring, scoring_errors = load_json(directory / "limited_scoring_result.json")
    comparison, comparison_errors = load_json(directory / "post_repair_comparison.json")
    no_memory, no_memory_errors = load_json(directory / "no_memory_outcome.json")
    memory_enabled, memory_enabled_errors = load_json(directory / "memory_enabled_outcome.json")
    corruption, corruption_errors = load_json(directory / "corruption_check_result.json")
    overlap, overlap_errors = load_json(directory / "decision_time_outcome_overlap_check.json")
    ledger, ledger_errors = load_json(directory / "proof_obligations_ledger.json")
    errors.extend(
        metadata_errors
        + scoring_errors
        + comparison_errors
        + no_memory_errors
        + memory_enabled_errors
        + corruption_errors
        + overlap_errors
        + ledger_errors
    )

    expected_classification = "positive_evidence_memory_lift_user_owned_organic_style_episode"
    if metadata.get("episode_id") != "episode_014":
        errors.append("episode_014 metadata episode_id mismatch")
    if metadata.get("target_class") != "user_owned_repo_semi_organic_failure":
        errors.append("episode_014 target_class must be user_owned_repo_semi_organic_failure")
    if metadata.get("classification") != expected_classification:
        errors.append("episode_014 expected positive user-owned organic-style classification")
    if scoring.get("classification") != expected_classification:
        errors.append("episode_014 scoring classification mismatch")
    if comparison.get("classification") != expected_classification:
        errors.append("episode_014 comparison classification mismatch")
    if metadata.get("replay_gate_status") != "deterministic_replay_ready_limited_scoring":
        errors.append("episode_014 replay gate must be deterministic_replay_ready_limited_scoring")
    if metadata.get("allowed_scoring_mode") != "limited_replay_scoring_only":
        errors.append("episode_014 scoring mode must be limited_replay_scoring_only")
    if metadata.get("failure_signature") != "README_LOCAL_TARGET_MISSING: key_repo_entrypoints":
        errors.append("episode_014 failure signature mismatch")
    if metadata.get("seeded_fallback") is not False:
        errors.append("episode_014 must not be seeded fallback")
    if metadata.get("full_scoring_allowed") is not False or scoring.get("full_scoring_allowed") is not False:
        errors.append("episode_014 full scoring must remain false")
    if metadata.get("controllergate_full_scoring") != "NOT_RUN" or scoring.get("controllergate_full_scoring") != "NOT_RUN":
        errors.append("episode_014 ControllerGate full scoring must remain NOT_RUN")
    if metadata.get("self_maintaining_software_claim_allowed") is not False:
        errors.append("episode_014 self-maintaining claim must be false")
    if no_memory.get("post_repair_result") != "failed":
        errors.append("episode_014 no-memory baseline must fail")
    if memory_enabled.get("post_repair_result") != "passed":
        errors.append("episode_014 memory-enabled path must pass")
    if scoring.get("memory_enabled_outperformed_no_memory") is not True:
        errors.append("episode_014 must mark memory-enabled outperformance")
    if scoring.get("organic_external_memory_lift_demonstrated") is not False:
        errors.append("episode_014 must not demonstrate organic external memory lift")
    if corruption.get("corruption_detected") is not False:
        errors.append("episode_014 corruption must be false")
    if overlap.get("overlap_detected") is not False:
        errors.append("episode_014 decision-time/outcome overlap must be false")
    if overlap.get("decision_time_outcome_overlap_episode_count") != 0:
        errors.append("episode_014 overlap count must be 0")
    if ledger.get("proof_status") != "complete_limited_replay_scoring_only":
        errors.append("episode_014 proof ledger status mismatch")
    if ledger.get("missing_obligations") != []:
        errors.append("episode_014 proof ledger missing obligations must be empty")
    errors.extend(verify_sha256_manifest(directory))
    errors.extend(require_text(directory / "failing_log_raw.txt", ["README_LOCAL_TARGET_MISSING: key_repo_entrypoints"]))
    errors.extend(require_text(directory / "memory_enabled_post_repair_log_raw.txt", ["v1.9 completion validation passed"]))
    return errors


def main() -> int:
    errors: list[str] = []
    if not COMPLETION_DIR.exists():
        errors.append(f"completion pass directory missing: {COMPLETION_DIR}")
    for name in REQUIRED_COMPLETION_FILES:
        path = COMPLETION_DIR / name
        if not path.exists():
            errors.append(f"missing completion pass artifact: {name}")
        elif path.stat().st_size == 0:
            errors.append(f"completion pass artifact is empty: {name}")

    prior, prior_errors = load_json(PRIOR_PILOT_DIR / "pilot_results.json")
    plan, plan_errors = load_json(COMPLETION_DIR / "completion_pass_plan.json")
    results, results_errors = load_json(COMPLETION_DIR / "completion_pass_results.json")
    aggregate, aggregate_errors = load_json(COMPLETION_DIR / "aggregate_v1_9_updated_memory_lift_assessment.json")
    v18_assessment, v18_errors = load_json(V18_CAMPAIGN_ASSESSMENT_PATH)
    episode_003, episode_003_errors = load_json(EPISODE_003_RESULT_PATH)
    beta_replay, beta_replay_errors = load_json(BETA_REPLAY_PLAN_PATH)
    beta_scoring, beta_scoring_errors = load_json(BETA_SCORING_PATH)
    alpha_classification, alpha_errors = load_json(ALPHA_CLASSIFICATION_PATH)
    errors.extend(
        prior_errors
        + plan_errors
        + results_errors
        + aggregate_errors
        + v18_errors
        + episode_003_errors
        + beta_replay_errors
        + beta_scoring_errors
        + alpha_errors
    )

    if prior.get("scoreable_episode_count") != 2:
        errors.append("existing v1.9 pilot must preserve 2 scoreable episodes")
    if prior.get("positive_episode_count") != 2:
        errors.append("existing v1.9 pilot must preserve 2 positive episodes")
    if prior.get("not_executed_episode_count") != 1:
        errors.append("existing v1.9 candidate acquisition miss must remain recorded")
    if prior.get("aggregate_classification") != "insufficient_episode_count_for_organic_style_memory_lift":
        errors.append("existing v1.9 pilot aggregate must remain insufficient-count")
    if prior.get("organic_external_memory_lift_demonstrated") is not False:
        errors.append("existing v1.9 pilot must not demonstrate organic external memory lift")

    if plan.get("full_scoring_allowed") is not False:
        errors.append("completion plan full scoring must be false")
    if plan.get("controllergate_full_scoring") != "NOT_RUN":
        errors.append("completion plan ControllerGate full scoring must be NOT_RUN")
    if plan.get("self_maintaining_software_claim_allowed") is not False:
        errors.append("completion plan self-maintaining claim must be false")
    if plan.get("organic_external_memory_lift_claim_allowed") is not False:
        errors.append("completion plan organic external lift claim must be false")

    if results.get("new_scoreable_episode_count") != 1:
        errors.append("completion pass must add 1 scoreable episode")
    if results.get("new_positive_episode_count") != 1:
        errors.append("completion pass must add 1 positive episode")
    if results.get("stopped_early") is not True:
        errors.append("completion pass must stop early after threshold evaluation")
    if results.get("full_scoring_allowed") is not False:
        errors.append("completion results full scoring must remain false")
    if results.get("controllergate_full_scoring") != "NOT_RUN":
        errors.append("completion results ControllerGate full scoring must be NOT_RUN")
    if results.get("organic_external_memory_lift_demonstrated") is not False:
        errors.append("completion results organic external memory lift must remain false")
    if results.get("self_maintaining_software_demonstrated") is not False:
        errors.append("completion results self-maintaining software must remain false")

    criteria = aggregate.get("criteria_observed") if isinstance(aggregate.get("criteria_observed"), dict) else {}
    if aggregate.get("aggregate_classification") != "limited_user_owned_organic_style_memory_lift_criteria_met":
        errors.append("updated aggregate classification mismatch")
    if aggregate.get("limited_user_owned_organic_style_memory_lift_criteria_met") is not True:
        errors.append("updated aggregate must mark limited user-owned criteria met")
    if aggregate.get("memory_lift_scope") != "limited_user_owned_organic_style_replay_only":
        errors.append("updated aggregate memory lift scope must be limited user-owned organic-style replay only")
    if aggregate.get("organic_style_memory_lift_demonstrated") is not True:
        errors.append("updated aggregate should demonstrate limited organic-style memory lift")
    if aggregate.get("organic_external_memory_lift_demonstrated") is not False:
        errors.append("updated aggregate must not demonstrate organic external memory lift")
    if aggregate.get("self_maintaining_software_demonstrated") is not False:
        errors.append("updated aggregate must not demonstrate self-maintaining software")
    if aggregate.get("full_scoring_allowed") is not False:
        errors.append("updated aggregate full scoring must remain false")
    if aggregate.get("controllergate_full_scoring") != "NOT_RUN":
        errors.append("updated aggregate ControllerGate full scoring must remain NOT_RUN")
    if criteria.get("total_v1_9_scoreable_episode_count") != 3:
        errors.append("updated aggregate total scoreable count must be 3")
    if criteria.get("total_v1_9_positive_memory_outperformance_episodes") != 3:
        errors.append("updated aggregate positive outperformance count must be 3")
    if criteria.get("total_v1_9_not_executed_candidate_acquisition_episodes") != 1:
        errors.append("updated aggregate not-executed candidate count must be 1")
    if criteria.get("decision_time_outcome_overlap_count") != 0:
        errors.append("updated aggregate overlap count must be 0")
    if criteria.get("corruption_episode_count") != 0:
        errors.append("updated aggregate corruption count must be 0")
    if criteria.get("positive_episodes_identical_replay_conditions") is not True:
        errors.append("updated aggregate identical replay condition flag must be true")
    if criteria.get("replay_custody_passes_for_positive_episodes") is not True:
        errors.append("updated aggregate replay/custody positive flag must be true")

    errors.extend(audit_episode_014())
    errors.extend(verify_sha256_manifest(COMPLETION_DIR, recursive=True))

    if v18_assessment.get("aggregate_classification") != "limited_seeded_controlled_memory_lift_criteria_met":
        errors.append("v1.8 seeded campaign aggregate must remain preserved")
    if episode_003.get("result_classification") != "negative_evidence_no_memory_lift_on_seeded_controlled_episode":
        errors.append("Episode 003 negative result must remain preserved")
    if episode_003.get("memory_lift_demonstrated") is not False:
        errors.append("Episode 003 memory lift must remain false")
    if beta_replay.get("deterministic_replay_ready_count") != 0:
        errors.append("TatMapper deterministic replay-ready count must remain 0")
    if beta_scoring.get("full_scoring_allowed") is not False:
        errors.append("beta full scoring must remain false")
    if beta_scoring.get("scoring_mode") != "limited_pilot_only":
        errors.append("beta must remain limited-pilot only")
    alpha_summary = alpha_classification.get("summary") if isinstance(alpha_classification.get("summary"), dict) else {}
    if alpha_summary.get("full_scoring_allowed") is not False:
        errors.append("alpha full scoring must remain false")

    errors.extend(
        require_text(
            SUMMARY_PATH,
            [
                "## v1.9 Organic-Style Replay Pilot Completion Pass",
                "v1.9 was previously positive but underpowered.",
                "Completion pass attempts to reach the minimum scoreable episode count.",
                "Aggregate assessment: `limited_user_owned_organic_style_memory_lift_criteria_met`.",
                "Organic-style memory lift is now supported only within the limited user-owned replay scope.",
                "Organic external memory lift remains undemonstrated.",
                "Self-maintaining software remains undemonstrated.",
                "Full scoring remains disallowed.",
            ],
        )
    )

    if errors:
        print("v1.9 organic-style replay pilot completion pass audit: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1

    print("v1.9 organic-style replay pilot completion pass audit: PASS")
    print("new scoreable episodes: 1")
    print("total v1.9 scoreable episodes: 3")
    print("total v1.9 positive memory-outperformance episodes: 3")
    print("aggregate: limited_user_owned_organic_style_memory_lift_criteria_met")
    print("organic external memory lift demonstrated: false")
    print("self-maintaining software demonstrated: false")
    print("full scoring allowed: false")
    return 0


if __name__ == "__main__":
    sys.exit(main())
