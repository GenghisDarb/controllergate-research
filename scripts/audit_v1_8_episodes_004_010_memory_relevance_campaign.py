#!/usr/bin/env python3
"""Audit the v1.8 Episodes 004-010 memory-relevance replay campaign."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
CAMPAIGN_DIR = REPO_ROOT / "outputs" / "v1_8_episodes_004_010_memory_relevance_campaign"
SUMMARY_PATH = (
    REPO_ROOT / "controllergate_v1_7_beta" / "reports" / "critic_review_package" / "shareable_summary.md"
)
EPISODE_001_METADATA_PATH = (
    REPO_ROOT / "outputs" / "v1_8_episode_001_torus_replay_capture" / "episode_001_metadata.json"
)
EPISODE_002_METADATA_PATH = (
    REPO_ROOT / "outputs" / "v1_8_episode_002_torus_replay_capture" / "episode_002_metadata.json"
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
    "campaign_plan.json",
    "campaign_results.json",
    "campaign_summary.md",
    "aggregate_limited_scoring_result.json",
    "aggregate_memory_lift_assessment.json",
    "falsification_and_stop_conditions.md",
    "SHA256SUMS.txt",
]

REQUIRED_EPISODE_FILES = [
    "episode_metadata.json",
    "target_repo_baseline_snapshot.json",
    "environment_snapshot.txt",
    "seeded_or_discovered_failure_snapshot.json",
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
    "positive_evidence_memory_lift_seeded_controlled_episode",
    "negative_evidence_no_memory_lift_seeded_controlled_episode",
    "negative_evidence_memory_harm_or_corruption_seeded_controlled_episode",
    "blocked_replay_gate_failed",
    "blocked_missing_baseline",
    "blocked_artifact_custody_failure",
    "blocked_decision_time_outcome_overlap",
    "inconclusive_equal_performance",
    "capture_complete_not_scoreable",
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
                    errors.append(f"campaign SHA256SUMS missing artifact entry {rel}")
    return errors


def audit_episode(episode_id: str) -> tuple[dict[str, Any], list[str]]:
    errors: list[str] = []
    directory = CAMPAIGN_DIR / episode_id
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
    errors.extend(metadata_errors + scoring_errors + comparison_errors + corruption_errors + overlap_errors + ledger_errors)

    classification = metadata.get("classification")
    if classification not in VALID_CLASSIFICATIONS:
        errors.append(f"{episode_id}: invalid classification {classification!r}")
    if metadata.get("episode_id") != episode_id:
        errors.append(f"{episode_id}: metadata episode_id mismatch")
    if metadata.get("episode_label") != "seeded_controlled_real_repo_episode":
        errors.append(f"{episode_id}: episode label must be seeded_controlled_real_repo_episode")
    if metadata.get("allowed_scoring_mode") != "limited_replay_scoring_only":
        errors.append(f"{episode_id}: allowed scoring mode must be limited_replay_scoring_only")
    if metadata.get("replay_gate_status") != "deterministic_replay_ready_limited_scoring":
        errors.append(f"{episode_id}: replay gate status must be deterministic_replay_ready_limited_scoring")
    if metadata.get("full_scoring_allowed") is not False:
        errors.append(f"{episode_id}: full_scoring_allowed must be false")
    if metadata.get("self_maintaining_software_claim_allowed") is not False:
        errors.append(f"{episode_id}: self-maintaining claim must be false")
    if scoring.get("controllergate_full_scoring") != "NOT_RUN":
        errors.append(f"{episode_id}: ControllerGate full scoring must be NOT_RUN")
    if scoring.get("full_scoring_allowed") is not False:
        errors.append(f"{episode_id}: limited scoring full scoring must remain false")
    if scoring.get("classification") != classification:
        errors.append(f"{episode_id}: scoring classification must match metadata")
    if comparison.get("classification") != classification:
        errors.append(f"{episode_id}: comparison classification must match metadata")
    if corruption.get("corruption_detected") is not False:
        errors.append(f"{episode_id}: corruption must be false")
    if overlap.get("overlap_detected") is not False:
        errors.append(f"{episode_id}: decision-time/outcome overlap must be false")
    if overlap.get("decision_time_outcome_overlap_episode_count") != 0:
        errors.append(f"{episode_id}: overlap count must be 0")
    if ledger.get("proof_status") != "complete_limited_replay_scoring_only":
        errors.append(f"{episode_id}: proof status must be complete_limited_replay_scoring_only")
    if ledger.get("missing_obligations") != []:
        errors.append(f"{episode_id}: proof ledger missing_obligations must be empty")
    if classification == "positive_evidence_memory_lift_seeded_controlled_episode":
        if scoring.get("memory_enabled_outperformed_no_memory") is not True:
            errors.append(f"{episode_id}: positive episode must mark memory outperformance")
        if not scoring.get("positive_dimensions"):
            errors.append(f"{episode_id}: positive episode must list positive dimensions")
    if "HASH_MISMATCH" in str(metadata.get("failure_signature")) and classification == "blocked_artifact_custody_failure":
        errors.append(f"{episode_id}: validator-level hash mismatch must not be treated as artifact-custody failure")
    errors.extend(verify_sha256_manifest(directory))
    return metadata, errors


def main() -> int:
    errors: list[str] = []
    if not CAMPAIGN_DIR.exists():
        errors.append(f"campaign directory missing: {CAMPAIGN_DIR}")
    for name in REQUIRED_CAMPAIGN_FILES:
        path = CAMPAIGN_DIR / name
        if not path.exists():
            errors.append(f"missing campaign artifact: {name}")
        elif path.stat().st_size == 0:
            errors.append(f"campaign artifact is empty: {name}")

    plan, plan_errors = load_json(CAMPAIGN_DIR / "campaign_plan.json")
    results, results_errors = load_json(CAMPAIGN_DIR / "campaign_results.json")
    aggregate, aggregate_errors = load_json(CAMPAIGN_DIR / "aggregate_memory_lift_assessment.json")
    episode_001, episode_001_errors = load_json(EPISODE_001_METADATA_PATH)
    episode_002, episode_002_errors = load_json(EPISODE_002_METADATA_PATH)
    episode_003, episode_003_errors = load_json(EPISODE_003_RESULT_PATH)
    beta_replay, beta_replay_errors = load_json(BETA_REPLAY_PLAN_PATH)
    beta_scoring, beta_scoring_errors = load_json(BETA_SCORING_PATH)
    alpha_classification, alpha_classification_errors = load_json(ALPHA_CLASSIFICATION_PATH)
    errors.extend(
        plan_errors
        + results_errors
        + aggregate_errors
        + episode_001_errors
        + episode_002_errors
        + episode_003_errors
        + beta_replay_errors
        + beta_scoring_errors
        + alpha_classification_errors
    )

    if plan.get("campaign_id") != "v1_8_episodes_004_010_memory_relevance_campaign":
        errors.append("campaign_id mismatch")
    if plan.get("full_scoring_allowed") is not False:
        errors.append("campaign plan full_scoring_allowed must be false")
    if plan.get("controllergate_full_scoring") != "NOT_RUN":
        errors.append("campaign plan ControllerGate full scoring must be NOT_RUN")
    if plan.get("self_maintaining_software_claim_allowed") is not False:
        errors.append("campaign plan self-maintaining software claim must be false")
    if "Validator-level hash mismatch may be a valid deterministic failure target" not in str(
        plan.get("validator_level_hash_mismatch_rule")
    ):
        errors.append("campaign plan must distinguish validator-level hash mismatch as potentially valid")
    if "blocks or quarantines" not in str(plan.get("artifact_custody_hash_mismatch_rule")):
        errors.append("campaign plan must block/quarantine artifact-custody hash mismatch")

    episode_metadata: list[dict[str, Any]] = []
    for number in range(4, 11):
        metadata, episode_errors = audit_episode(f"episode_{number:03d}")
        episode_metadata.append(metadata)
        errors.extend(episode_errors)

    if results.get("executed_episode_count") != 7:
        errors.append("campaign must execute 7 episodes")
    if results.get("scoreable_episode_count") != 7:
        errors.append("campaign must have 7 deterministic replay-ready limited scoring episodes")
    if results.get("positive_episode_count") != 6:
        errors.append("campaign positive episode count must be 6")
    if results.get("inconclusive_episode_count") != 1:
        errors.append("campaign inconclusive episode count must be 1")
    if results.get("blocked_episode_count") != 0:
        errors.append("campaign blocked episode count must be 0")
    if results.get("decision_time_outcome_overlap_count") != 0:
        errors.append("campaign decision-time/outcome overlap count must be 0")
    if results.get("corruption_episode_count") != 0:
        errors.append("campaign corruption count must be 0")
    if results.get("full_scoring_allowed") is not False:
        errors.append("campaign results full scoring must remain false")
    if results.get("controllergate_full_scoring") != "NOT_RUN":
        errors.append("campaign results ControllerGate full scoring must be NOT_RUN")
    if results.get("self_maintaining_software_demonstrated") is not False:
        errors.append("campaign must not demonstrate self-maintaining software")

    observed = aggregate.get("criteria_observed")
    if not isinstance(observed, dict):
        errors.append("aggregate criteria_observed must be an object")
        observed = {}
    criteria_met = (
        observed.get("scoreable_episode_count", 0) >= 3
        and observed.get("positive_memory_outperformance_episodes", 0) >= 2
        and observed.get("positive_episode_corruption_count") == 0
        and observed.get("decision_time_outcome_overlap_count") == 0
        and observed.get("positive_episodes_identical_replay_conditions") is True
    )
    if aggregate.get("limited_seeded_controlled_memory_lift_criteria_met") is True and not criteria_met:
        errors.append("aggregate memory lift criteria marked true without preregistered criteria")
    if aggregate.get("aggregate_classification") != "limited_seeded_controlled_memory_lift_criteria_met":
        errors.append("aggregate classification must be limited_seeded_controlled_memory_lift_criteria_met")
    if aggregate.get("memory_lift_scope") != "seeded_controlled_replay_campaign_only":
        errors.append("aggregate memory lift scope must remain seeded-controlled only")
    if aggregate.get("real_repo_memory_lift_generalized") is not False:
        errors.append("real repo memory lift must not be generalized")
    if aggregate.get("organic_external_memory_lift_demonstrated") is not False:
        errors.append("organic external memory lift must remain false")
    if aggregate.get("self_maintaining_software_demonstrated") is not False:
        errors.append("self-maintaining software must remain undemonstrated")

    if episode_001.get("replay_gate_status") != "capture_complete_not_scoreable":
        errors.append("Episode 001 must remain capture_complete_not_scoreable")
    if episode_002.get("replay_gate_status") != "capture_complete_not_scoreable":
        errors.append("Episode 002 must remain capture_complete_not_scoreable")
    if episode_003.get("result_classification") != "negative_evidence_no_memory_lift_on_seeded_controlled_episode":
        errors.append("Episode 003 no-memory-lift result must remain preserved")
    if beta_replay.get("deterministic_replay_ready_count") != 0:
        errors.append("TatMapper deterministic replay-ready count must remain 0")
    if beta_scoring.get("full_scoring_allowed") is not False:
        errors.append("beta full scoring must remain false")
    if beta_scoring.get("scoring_mode") != "limited_pilot_only":
        errors.append("beta must remain limited-pilot only")
    alpha_summary = alpha_classification.get("summary") if isinstance(alpha_classification.get("summary"), dict) else {}
    if alpha_summary.get("full_scoring_allowed") is not False:
        errors.append("alpha full scoring must remain false")

    errors.extend(verify_sha256_manifest(CAMPAIGN_DIR, recursive=True))
    errors.extend(
        require_text(
            SUMMARY_PATH,
            [
                "## v1.8 Episodes 004-010 memory-relevance campaign",
                "This campaign tests whether memory helps under replay-ready seeded controlled conditions.",
                "Negative results are valid evidence against this memory design for these task classes.",
                "Blocked results reflect missing artifacts or replay failure, not capability failure.",
                "Validator-level hash mismatch is a valid deterministic target when replay/custody passes.",
                "Artifact-custody hash mismatch blocks scoring.",
                "Full scoring remains disallowed.",
                "Self-maintaining software remains undemonstrated.",
                "Aggregate memory-lift assessment: `limited_seeded_controlled_memory_lift_criteria_met`.",
            ],
        )
    )

    if errors:
        print("v1.8 Episodes 004-010 memory-relevance campaign audit: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1

    print("v1.8 Episodes 004-010 memory-relevance campaign audit: PASS")
    print("executed episodes: 7")
    print("scoreable episodes: 7")
    print("positive seeded memory-lift episodes: 6")
    print("inconclusive episodes: 1")
    print("blocked episodes: 0")
    print("aggregate: limited_seeded_controlled_memory_lift_criteria_met")
    print("full scoring allowed: false")
    print("self-maintaining software demonstrated: false")
    return 0


if __name__ == "__main__":
    sys.exit(main())
