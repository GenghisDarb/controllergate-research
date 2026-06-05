#!/usr/bin/env python3
"""Audit the v1.9 Episodes 011-013 organic-style replay pilot."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
PILOT_DIR = REPO_ROOT / "outputs" / "v1_9_episodes_011_013_organic_style_replay_pilot"
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

REQUIRED_CAMPAIGN_FILES = [
    "pilot_plan.json",
    "candidate_search_log.json",
    "pilot_results.json",
    "pilot_summary.md",
    "aggregate_organic_style_memory_lift_assessment.json",
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

VALID_CLASSIFICATIONS = {
    "positive_evidence_memory_lift_organic_style_episode",
    "negative_evidence_no_memory_lift_organic_style_episode",
    "negative_evidence_memory_harm_or_corruption_organic_style_episode",
    "blocked_replay_gate_failed",
    "blocked_missing_baseline",
    "blocked_artifact_custody_failure",
    "blocked_decision_time_outcome_overlap",
    "inconclusive_equal_performance",
    "not_executed_candidate_acquisition_failed",
    "not_executed_resource_limit",
    "seeded_fallback_not_organic_style",
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


def audit_episode(episode_id: str) -> tuple[dict[str, Any], list[str]]:
    errors: list[str] = []
    directory = PILOT_DIR / episode_id
    if not directory.exists():
        return {}, [f"missing episode directory: {episode_id}"]
    for name in REQUIRED_EPISODE_FILES:
        path = directory / name
        if not path.exists():
            errors.append(f"{episode_id}: missing required artifact {name}")
        elif path.is_file() and path.stat().st_size == 0:
            errors.append(f"{episode_id}: required artifact is empty {name}")

    metadata, metadata_errors = load_json(directory / "episode_metadata.json")
    scoring, scoring_errors = load_json(directory / "limited_scoring_result.json")
    comparison, comparison_errors = load_json(directory / "post_repair_comparison.json")
    corruption, corruption_errors = load_json(directory / "corruption_check_result.json")
    overlap, overlap_errors = load_json(directory / "decision_time_outcome_overlap_check.json")
    ledger, ledger_errors = load_json(directory / "proof_obligations_ledger.json")
    no_memory, no_memory_errors = load_json(directory / "no_memory_outcome.json")
    memory_enabled, memory_enabled_errors = load_json(directory / "memory_enabled_outcome.json")
    errors.extend(
        metadata_errors
        + scoring_errors
        + comparison_errors
        + corruption_errors
        + overlap_errors
        + ledger_errors
        + no_memory_errors
        + memory_enabled_errors
    )

    classification = metadata.get("classification")
    if classification not in VALID_CLASSIFICATIONS:
        errors.append(f"{episode_id}: invalid classification {classification!r}")
    if metadata.get("episode_id") != episode_id:
        errors.append(f"{episode_id}: metadata episode_id mismatch")
    if scoring.get("classification") != classification:
        errors.append(f"{episode_id}: scoring classification must match metadata")
    if comparison.get("classification") != classification:
        errors.append(f"{episode_id}: comparison classification must match metadata")
    if metadata.get("full_scoring_allowed") is not False:
        errors.append(f"{episode_id}: full_scoring_allowed must be false")
    if metadata.get("controllergate_full_scoring") != "NOT_RUN":
        errors.append(f"{episode_id}: ControllerGate full scoring must be NOT_RUN")
    if metadata.get("self_maintaining_software_claim_allowed") is not False:
        errors.append(f"{episode_id}: self-maintaining claim must be false")
    if scoring.get("full_scoring_allowed") is not False:
        errors.append(f"{episode_id}: limited scoring full scoring must remain false")
    if scoring.get("controllergate_full_scoring") != "NOT_RUN":
        errors.append(f"{episode_id}: limited scoring must keep ControllerGate full scoring NOT_RUN")
    if corruption.get("corruption_detected") is not False:
        errors.append(f"{episode_id}: corruption must be false")
    if overlap.get("overlap_detected") is not False:
        errors.append(f"{episode_id}: decision-time/outcome overlap must be false")
    if overlap.get("decision_time_outcome_overlap_episode_count") != 0:
        errors.append(f"{episode_id}: decision-time/outcome overlap count must be 0")

    if episode_id in {"episode_011", "episode_013"}:
        if metadata.get("target_class") != "user_owned_repo_semi_organic_failure":
            errors.append(f"{episode_id}: target class must be user_owned_repo_semi_organic_failure")
        if metadata.get("seeded_fallback") is not False:
            errors.append(f"{episode_id}: must not be marked as seeded fallback")
        if metadata.get("replay_gate_status") != "deterministic_replay_ready_limited_scoring":
            errors.append(f"{episode_id}: replay gate must be deterministic_replay_ready_limited_scoring")
        if metadata.get("allowed_scoring_mode") != "limited_replay_scoring_only":
            errors.append(f"{episode_id}: allowed scoring mode must be limited_replay_scoring_only")
        if classification != "positive_evidence_memory_lift_organic_style_episode":
            errors.append(f"{episode_id}: expected positive organic-style evidence classification")
        if no_memory.get("post_repair_result") != "failed":
            errors.append(f"{episode_id}: no-memory baseline must fail")
        if memory_enabled.get("post_repair_result") != "passed":
            errors.append(f"{episode_id}: memory-enabled path must pass")
        if scoring.get("memory_enabled_outperformed_no_memory") is not True:
            errors.append(f"{episode_id}: memory-enabled outperformance must be true")
        if scoring.get("organic_external_memory_lift_demonstrated") is not False:
            errors.append(f"{episode_id}: single episode must not demonstrate organic external memory lift")
        if ledger.get("proof_status") != "complete_limited_replay_scoring_only":
            errors.append(f"{episode_id}: proof ledger status must be complete_limited_replay_scoring_only")
        if ledger.get("missing_obligations") != []:
            errors.append(f"{episode_id}: proof ledger missing_obligations must be empty")
    elif episode_id == "episode_012":
        if classification != "not_executed_candidate_acquisition_failed":
            errors.append("episode_012: expected not_executed_candidate_acquisition_failed")
        if metadata.get("allowed_scoring_mode") != "not_scoreable":
            errors.append("episode_012: allowed scoring mode must be not_scoreable")
        if scoring.get("scoreable") is not False:
            errors.append("episode_012: scoring must be false")
        if metadata.get("replay_gate_status") != "not_executed_candidate_acquisition_failed":
            errors.append("episode_012: replay gate must record candidate acquisition failure")
        if ledger.get("proof_status") != "not_executed_candidate_acquisition_failed":
            errors.append("episode_012: proof ledger status must record candidate acquisition failure")
    else:
        errors.append(f"unexpected episode id {episode_id}")

    errors.extend(verify_sha256_manifest(directory))
    return metadata, errors


def main() -> int:
    errors: list[str] = []
    if not PILOT_DIR.exists():
        errors.append(f"pilot directory missing: {PILOT_DIR}")
    for name in REQUIRED_CAMPAIGN_FILES:
        path = PILOT_DIR / name
        if not path.exists():
            errors.append(f"missing campaign artifact: {name}")
        elif path.stat().st_size == 0:
            errors.append(f"campaign artifact is empty: {name}")

    plan, plan_errors = load_json(PILOT_DIR / "pilot_plan.json")
    candidate_search, search_errors = load_json(PILOT_DIR / "candidate_search_log.json")
    results, results_errors = load_json(PILOT_DIR / "pilot_results.json")
    aggregate, aggregate_errors = load_json(PILOT_DIR / "aggregate_organic_style_memory_lift_assessment.json")
    v18_assessment, v18_errors = load_json(V18_CAMPAIGN_ASSESSMENT_PATH)
    episode_003, episode_003_errors = load_json(EPISODE_003_RESULT_PATH)
    beta_replay, beta_replay_errors = load_json(BETA_REPLAY_PLAN_PATH)
    beta_scoring, beta_scoring_errors = load_json(BETA_SCORING_PATH)
    alpha_classification, alpha_errors = load_json(ALPHA_CLASSIFICATION_PATH)
    errors.extend(
        plan_errors
        + search_errors
        + results_errors
        + aggregate_errors
        + v18_errors
        + episode_003_errors
        + beta_replay_errors
        + beta_scoring_errors
        + alpha_errors
    )

    if plan.get("pilot_id") != "v1_9_episodes_011_013_organic_style_replay_pilot":
        errors.append("pilot_id mismatch")
    if plan.get("full_scoring_allowed") is not False:
        errors.append("pilot full_scoring_allowed must be false")
    if plan.get("controllergate_full_scoring") != "NOT_RUN":
        errors.append("pilot ControllerGate full scoring must be NOT_RUN")
    if plan.get("self_maintaining_software_claim_allowed") is not False:
        errors.append("pilot self-maintaining software claim must be false")
    if plan.get("organic_external_memory_lift_claim_allowed") is not False:
        errors.append("pilot organic external memory-lift claim must be false")
    if plan.get("episode_ids") != ["episode_011", "episode_012", "episode_013"]:
        errors.append("pilot episode ids must be 011-013")

    findings = candidate_search.get("findings")
    if not isinstance(findings, list) or len(findings) != 3:
        errors.append("candidate search must record three findings")
    if candidate_search.get("network_candidate_acquisition") != "not_used_restricted":
        errors.append("candidate search must record restricted/no network acquisition")

    episode_metadata: list[dict[str, Any]] = []
    for episode_id in ["episode_011", "episode_012", "episode_013"]:
        metadata, episode_errors = audit_episode(episode_id)
        episode_metadata.append(metadata)
        errors.extend(episode_errors)

    if results.get("executed_or_recorded_episode_count") != 3:
        errors.append("pilot must record three episodes")
    if results.get("scoreable_episode_count") != 2:
        errors.append("pilot scoreable episode count must be 2")
    if results.get("positive_episode_count") != 2:
        errors.append("pilot positive episode count must be 2")
    if results.get("not_executed_episode_count") != 1:
        errors.append("pilot not-executed episode count must be 1")
    if results.get("blocked_episode_count") != 0:
        errors.append("pilot blocked episode count must be 0")
    if results.get("decision_time_outcome_overlap_count") != 0:
        errors.append("pilot decision-time/outcome overlap count must be 0")
    if results.get("corruption_episode_count") != 0:
        errors.append("pilot corruption count must be 0")
    if results.get("aggregate_classification") != "insufficient_episode_count_for_organic_style_memory_lift":
        errors.append("pilot aggregate classification must be insufficient episode count")
    if results.get("organic_style_memory_lift_demonstrated") is not False:
        errors.append("organic-style memory lift must remain undemonstrated")
    if results.get("organic_external_memory_lift_demonstrated") is not False:
        errors.append("organic external memory lift must remain undemonstrated")
    if results.get("self_maintaining_software_demonstrated") is not False:
        errors.append("self-maintaining software must remain undemonstrated")
    if results.get("full_scoring_allowed") is not False:
        errors.append("full scoring must remain false")
    if results.get("controllergate_full_scoring") != "NOT_RUN":
        errors.append("ControllerGate full scoring must remain NOT_RUN")

    criteria = aggregate.get("criteria_observed") if isinstance(aggregate.get("criteria_observed"), dict) else {}
    if criteria.get("scoreable_episode_count") != 2:
        errors.append("aggregate scoreable episode count must be 2")
    if criteria.get("positive_memory_outperformance_episodes") != 2:
        errors.append("aggregate positive outperformance count must be 2")
    if criteria.get("decision_time_outcome_overlap_count") != 0:
        errors.append("aggregate overlap count must be 0")
    if criteria.get("corruption_episode_count") != 0:
        errors.append("aggregate corruption count must be 0")
    if aggregate.get("aggregate_classification") != "insufficient_episode_count_for_organic_style_memory_lift":
        errors.append("aggregate assessment must preserve insufficient-count classification")
    if aggregate.get("organic_style_memory_lift_demonstrated") is not False:
        errors.append("aggregate must not demonstrate organic-style memory lift")
    if aggregate.get("organic_external_memory_lift_demonstrated") is not False:
        errors.append("aggregate must not demonstrate organic external memory lift")
    if aggregate.get("self_maintaining_software_demonstrated") is not False:
        errors.append("aggregate must not demonstrate self-maintaining software")

    if v18_assessment.get("aggregate_classification") != "limited_seeded_controlled_memory_lift_criteria_met":
        errors.append("v1.8 seeded campaign aggregate must remain preserved")
    if v18_assessment.get("organic_external_memory_lift_demonstrated") is not False:
        errors.append("v1.8 must not demonstrate organic external memory lift")
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

    errors.extend(verify_sha256_manifest(PILOT_DIR, recursive=True))
    errors.extend(
        require_text(
            SUMMARY_PATH,
            [
                "## v1.9 Episodes 011-013 organic-style replay pilot",
                "v1.9 tests generalization beyond seeded controlled memory-relevance tasks.",
                "Episode 011",
                "Episode 012",
                "Episode 013",
                "Aggregate assessment: `insufficient_episode_count_for_organic_style_memory_lift`.",
                "Organic-style memory lift remains undemonstrated.",
                "Organic external memory lift remains undemonstrated.",
                "Self-maintaining software remains undemonstrated.",
                "Full scoring remains disallowed.",
            ],
        )
    )

    if errors:
        print("v1.9 Episodes 011-013 organic-style replay pilot audit: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1

    print("v1.9 Episodes 011-013 organic-style replay pilot audit: PASS")
    print("scoreable episodes: 2")
    print("positive user-owned semi-organic episodes: 2")
    print("not executed candidate acquisition failures: 1")
    print("aggregate: insufficient_episode_count_for_organic_style_memory_lift")
    print("organic-style memory lift demonstrated: false")
    print("organic external memory lift demonstrated: false")
    print("self-maintaining software demonstrated: false")
    print("full scoring allowed: false")
    return 0


if __name__ == "__main__":
    sys.exit(main())
