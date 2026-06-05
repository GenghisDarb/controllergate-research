#!/usr/bin/env python3
"""Audit v2.2 external-fork controlled fixture replay pilot outputs."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
PILOT_DIR = REPO_ROOT / "outputs" / "v2_2_external_fork_controlled_fixture_replay_pilot"
V21C_HANDOFF = REPO_ROOT / "outputs" / "v2_1c_external_fork_controlled_fixture_triage" / "v2_2_handoff_recommendations.json"
V21B_HANDOFF = REPO_ROOT / "outputs" / "v2_1b_curated_external_candidate_sourcing" / "v2_2_handoff_recommendations.json"
V20_RESULTS = REPO_ROOT / "outputs" / "v2_0_external_fork_replay_pilot" / "pilot_results.json"
V19_AGG = (
    REPO_ROOT
    / "outputs"
    / "v1_9_organic_style_replay_pilot_completion_pass"
    / "aggregate_v1_9_updated_memory_lift_assessment.json"
)
V18_AGG = REPO_ROOT / "outputs" / "v1_8_episodes_004_010_memory_relevance_campaign" / "aggregate_memory_lift_assessment.json"
BETA_REPLAY = REPO_ROOT / "controllergate_v1_7_beta" / "outputs" / "v1_7_beta_replay_eligibility_plan.json"
BETA_SCORING = REPO_ROOT / "controllergate_v1_7_beta" / "traces" / "audits" / "limited_pilot_scoring" / "limited_pilot_scoring.json"
ALPHA_CLASSIFICATION = REPO_ROOT / "controllergate_v1_7_alpha" / "traces" / "audits" / "episode_review_classification.json"

REQUIRED_CAMPAIGN_FILES = [
    "pilot_plan.json",
    "pilot_results.json",
    "aggregate_external_fork_controlled_fixture_memory_lift_assessment.json",
    "pilot_summary.md",
    "SHA256SUMS.txt",
]

REQUIRED_EPISODE_FILES = [
    "episode_metadata.json",
    "source_repo_metadata.json",
    "license_summary.txt",
    "candidate_selection_record.json",
    "target_repo_snapshot.json",
    "environment_snapshot.txt",
    "fixture_injection_or_bug_reference.json",
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
    "positive_evidence_memory_lift_external_fork_controlled_fixture_episode",
    "positive_evidence_memory_lift_known_external_bug_episode",
    "negative_evidence_no_memory_lift_external_fork_controlled_fixture_episode",
    "negative_evidence_memory_harm_or_corruption_external_fork_controlled_fixture_episode",
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


def verify_manifest(directory: Path, recursive: bool = False) -> list[str]:
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
        elif path.stat().st_size == 0 and name.endswith((".json", ".txt")):
            errors.append(f"{directory.name}: empty required artifact {name}")
    metadata, metadata_errors = load_json(directory / "episode_metadata.json")
    fixture, fixture_errors = load_json(directory / "fixture_injection_or_bug_reference.json")
    comparison, comparison_errors = load_json(directory / "post_repair_comparison.json")
    no_memory, no_memory_errors = load_json(directory / "no_memory_outcome.json")
    memory, memory_errors = load_json(directory / "memory_enabled_outcome.json")
    corruption, corruption_errors = load_json(directory / "corruption_check_result.json")
    overlap, overlap_errors = load_json(directory / "decision_time_outcome_overlap_check.json")
    scoring, scoring_errors = load_json(directory / "limited_scoring_result.json")
    ledger, ledger_errors = load_json(directory / "proof_obligations_ledger.json")
    errors.extend(
        metadata_errors
        + fixture_errors
        + comparison_errors
        + no_memory_errors
        + memory_errors
        + corruption_errors
        + overlap_errors
        + scoring_errors
        + ledger_errors
    )
    classification = metadata.get("classification")
    if classification not in VALID_CLASSIFICATIONS:
        errors.append(f"{directory.name}: invalid classification {classification!r}")
    if metadata.get("episode_label") != "external_fork_controlled_fixture":
        errors.append(f"{directory.name}: fixture episode label must be external_fork_controlled_fixture")
    if metadata.get("not_organic_external_bug") is not True:
        errors.append(f"{directory.name}: fixture episode must be marked not organic external bug")
    if metadata.get("organic_external_memory_lift_demonstrated") is not False:
        errors.append(f"{directory.name}: organic external memory lift must remain false")
    if metadata.get("full_scoring_allowed") is not False or scoring.get("full_scoring_allowed") is not False:
        errors.append(f"{directory.name}: full scoring must remain false")
    if metadata.get("controllergate_full_scoring") != "NOT_RUN" or scoring.get("controllergate_full_scoring") != "NOT_RUN":
        errors.append(f"{directory.name}: ControllerGate full scoring must remain NOT_RUN")
    if metadata.get("self_maintaining_software_demonstrated") is not False or scoring.get("self_maintaining_software_demonstrated") is not False:
        errors.append(f"{directory.name}: self-maintaining software must remain false")
    if fixture.get("reference_type") != "local_controlled_fixture_injection":
        errors.append(f"{directory.name}: fixture reference must be local controlled injection")
    if fixture.get("not_organic_external_bug") is not True:
        errors.append(f"{directory.name}: fixture reference must be not organic")
    if no_memory.get("primary_command_passed") is not True:
        errors.append(f"{directory.name}: no-memory primary command should pass in false-salvage baseline")
    if no_memory.get("clean_success") is not False:
        errors.append(f"{directory.name}: no-memory clean_success must be false because corruption is detected")
    if memory.get("primary_command_passed") is not True:
        errors.append(f"{directory.name}: memory-enabled primary command must pass")
    if memory.get("clean_success") is not True:
        errors.append(f"{directory.name}: memory-enabled clean_success must be true")
    if comparison.get("memory_enabled_outperformed_no_memory") is not True:
        errors.append(f"{directory.name}: memory-enabled must outperform no-memory")
    if corruption.get("memory_enabled", {}).get("corruption_detected") is not False:
        errors.append(f"{directory.name}: memory-enabled corruption must be false")
    if overlap.get("overlap_detected") is not False:
        errors.append(f"{directory.name}: decision-time/outcome overlap must be false")
    if overlap.get("decision_time_outcome_overlap_episode_count") != 0:
        errors.append(f"{directory.name}: overlap count must be 0")
    if ledger.get("proof_status") != "complete_limited_replay_scoring_only":
        errors.append(f"{directory.name}: proof ledger status mismatch")
    if ledger.get("missing_obligations") != []:
        errors.append(f"{directory.name}: proof ledger missing obligations must be empty")
    signature = metadata.get("failure_signature")
    errors.extend(require_text(directory / "failing_log_raw.txt", [signature]))
    errors.extend(verify_manifest(directory))
    return metadata, errors


def main() -> int:
    errors: list[str] = []
    if not PILOT_DIR.exists():
        errors.append(f"missing v2.2 pilot directory: {PILOT_DIR}")
    for name in REQUIRED_CAMPAIGN_FILES:
        path = PILOT_DIR / name
        if not path.exists():
            errors.append(f"missing v2.2 campaign artifact {name}")
        elif path.stat().st_size == 0:
            errors.append(f"empty v2.2 campaign artifact {name}")

    handoff, handoff_errors = load_json(V21C_HANDOFF)
    plan, plan_errors = load_json(PILOT_DIR / "pilot_plan.json")
    results, results_errors = load_json(PILOT_DIR / "pilot_results.json")
    aggregate, aggregate_errors = load_json(PILOT_DIR / "aggregate_external_fork_controlled_fixture_memory_lift_assessment.json")
    v21b, v21b_errors = load_json(V21B_HANDOFF)
    v20, v20_errors = load_json(V20_RESULTS)
    v19, v19_errors = load_json(V19_AGG)
    v18, v18_errors = load_json(V18_AGG)
    beta_replay, beta_replay_errors = load_json(BETA_REPLAY)
    beta_scoring, beta_scoring_errors = load_json(BETA_SCORING)
    alpha_classification, alpha_errors = load_json(ALPHA_CLASSIFICATION)
    errors.extend(
        handoff_errors
        + plan_errors
        + results_errors
        + aggregate_errors
        + v21b_errors
        + v20_errors
        + v19_errors
        + v18_errors
        + beta_replay_errors
        + beta_scoring_errors
        + alpha_errors
    )

    if handoff.get("promoted_candidate_count") != 3:
        errors.append("v2.1c handoff must preserve 3 promoted candidates")
    if plan.get("full_scoring_allowed") is not False:
        errors.append("v2.2 plan full scoring must be false")
    if plan.get("controllergate_full_scoring") != "NOT_RUN":
        errors.append("v2.2 plan ControllerGate full scoring must be NOT_RUN")
    if plan.get("organic_external_memory_lift_claim_allowed") is not False:
        errors.append("v2.2 must not allow organic external memory-lift claim")
    if plan.get("self_maintaining_software_claim_allowed") is not False:
        errors.append("v2.2 must not allow self-maintaining claim")

    episode_dirs = sorted(path for path in PILOT_DIR.glob("episode_*") if path.is_dir())
    if len(episode_dirs) != 3:
        errors.append("v2.2 must execute exactly 3 episode directories")
    metadatas: list[dict[str, Any]] = []
    for directory in episode_dirs:
        metadata, episode_errors = audit_episode(directory)
        metadatas.append(metadata)
        errors.extend(episode_errors)

    if results.get("executed_episode_count") != 3:
        errors.append("v2.2 executed episode count must be 3")
    if results.get("scoreable_episode_count") != 3:
        errors.append("v2.2 scoreable episode count must be 3")
    if results.get("positive_memory_episode_count") != 3:
        errors.append("v2.2 positive memory episode count must be 3")
    if results.get("decision_time_outcome_overlap_count") != 0:
        errors.append("v2.2 overlap count must be 0")
    if results.get("corruption_in_positive_memory_episode_count") != 0:
        errors.append("v2.2 positive memory corruption count must be 0")
    expected = "limited_external_fork_controlled_fixture_memory_lift_criteria_met"
    if results.get("aggregate_result") != expected or aggregate.get("aggregate_result") != expected:
        errors.append("v2.2 aggregate result mismatch")
    if aggregate.get("limited_external_fork_controlled_fixture_memory_lift_criteria_met") is not True:
        errors.append("v2.2 limited controlled fixture memory lift criteria must be met")
    if aggregate.get("organic_external_memory_lift_demonstrated") is not False:
        errors.append("v2.2 must not demonstrate organic external memory lift")
    if aggregate.get("self_maintaining_software_demonstrated") is not False:
        errors.append("v2.2 must not demonstrate self-maintaining software")
    if aggregate.get("full_scoring_allowed") is not False:
        errors.append("v2.2 full scoring must remain false")
    if aggregate.get("controllergate_full_scoring") != "NOT_RUN":
        errors.append("v2.2 ControllerGate full scoring must remain NOT_RUN")

    if v21b.get("recommendation") != "manual_candidate_triage_before_v2_2":
        errors.append("v2.1b result must remain preserved")
    if v20.get("aggregate_classification") != "blocked_external_candidate_acquisition_failure":
        errors.append("v2.0 blocked acquisition result must remain preserved")
    if v19.get("aggregate_classification") != "limited_user_owned_organic_style_memory_lift_criteria_met":
        errors.append("v1.9 limited user-owned result must remain preserved")
    if v18.get("aggregate_classification") != "limited_seeded_controlled_memory_lift_criteria_met":
        errors.append("v1.8 limited seeded result must remain preserved")
    if beta_replay.get("deterministic_replay_ready_count") != 0:
        errors.append("TatMapper quarantine must remain unchanged")
    if beta_scoring.get("full_scoring_allowed") is not False:
        errors.append("beta full scoring must remain false")
    alpha_summary = alpha_classification.get("summary") if isinstance(alpha_classification.get("summary"), dict) else {}
    if alpha_summary.get("full_scoring_allowed") is not False:
        errors.append("alpha full scoring must remain false")

    errors.extend(verify_manifest(PILOT_DIR, recursive=True))
    errors.extend(
        require_text(
            PILOT_DIR / "pilot_summary.md",
            [
                "External-fork controlled fixtures test portability of replay/memory machinery.",
                "Injected fixture failures are not organic external bugs.",
                "Known external bug replay is stronger evidence.",
                "Controlled fixture memory lift, if met, is limited-scope evidence.",
                "Organic external memory lift remains undemonstrated.",
                "Self-maintaining software remains undemonstrated.",
                "Full scoring remains disallowed.",
            ],
        )
    )

    if errors:
        print("v2.2 external-fork controlled fixture replay pilot audit: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1

    print("v2.2 external-fork controlled fixture replay pilot audit: PASS")
    print("executed episodes: 3")
    print("scoreable episodes: 3")
    print("positive memory episodes: 3")
    print(f"aggregate: {expected}")
    print("organic external memory lift demonstrated: false")
    print("self-maintaining software demonstrated: false")
    print("full scoring allowed: false")
    return 0


if __name__ == "__main__":
    sys.exit(main())
