#!/usr/bin/env python3
"""Audit the v1.8 Episode 003 limited replay-scoring candidate plan."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
PLAN_JSON_PATH = REPO_ROOT / "outputs" / "v1_8_episode_003_limited_replay_scoring_candidate_plan.json"
PLAN_MD_PATH = REPO_ROOT / "outputs" / "v1_8_episode_003_limited_replay_scoring_candidate_plan.md"
EPISODE_001_METADATA_PATH = (
    REPO_ROOT / "outputs" / "v1_8_episode_001_torus_replay_capture" / "episode_001_metadata.json"
)
EPISODE_002_METADATA_PATH = (
    REPO_ROOT / "outputs" / "v1_8_episode_002_torus_replay_capture" / "episode_002_metadata.json"
)
V18_PLAN_JSON_PATH = REPO_ROOT / "outputs" / "v1_8_controlled_repo_replay_capture_plan.json"
BETA_REPLAY_PLAN_PATH = REPO_ROOT / "controllergate_v1_7_beta" / "outputs" / "v1_7_beta_replay_eligibility_plan.json"
SUMMARY_PATH = (
    REPO_ROOT / "controllergate_v1_7_beta" / "reports" / "critic_review_package" / "shareable_summary.md"
)


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


def require_list_contains(data: dict[str, Any], field: str, required: list[str], errors: list[str]) -> None:
    values = data.get(field)
    if not isinstance(values, list):
        errors.append(f"{field} must be a list")
        return
    value_set = set(values)
    for item in required:
        if item not in value_set:
            errors.append(f"{field} missing {item!r}")


def main() -> int:
    plan, plan_errors = load_json(PLAN_JSON_PATH)
    v18, v18_errors = load_json(V18_PLAN_JSON_PATH)
    episode_001, episode_001_errors = load_json(EPISODE_001_METADATA_PATH)
    episode_002, episode_002_errors = load_json(EPISODE_002_METADATA_PATH)
    beta_replay, beta_replay_errors = load_json(BETA_REPLAY_PLAN_PATH)
    errors = plan_errors + v18_errors + episode_001_errors + episode_002_errors + beta_replay_errors

    if plan.get("episode_id") != "v1_8_episode_003":
        errors.append("episode_id must be v1_8_episode_003")
    if plan.get("plan_status") != "limited_replay_scoring_candidate_design_only":
        errors.append("plan_status must be limited_replay_scoring_candidate_design_only")
    if plan.get("execution_status") != "not_executed":
        errors.append("execution_status must be not_executed")
    if plan.get("target_repo_class") != "user_owned_public_repo":
        errors.append("target_repo_class must be user_owned_public_repo")
    if plan.get("target_repo_full_name") != "GenghisDarb/TORUS-Theory":
        errors.append("target repo must be GenghisDarb/TORUS-Theory")
    if plan.get("episode_label") != "seeded_controlled_real_repo_episode":
        errors.append("episode_label must be seeded_controlled_real_repo_episode")
    if plan.get("purpose") != "first limited replay-scoring candidate design":
        errors.append("purpose must be first limited replay-scoring candidate design")
    if plan.get("allowed_scoring_mode") != "limited_replay_scoring_candidate_not_executed":
        errors.append("allowed_scoring_mode must be limited_replay_scoring_candidate_not_executed")

    for field in [
        "full_scoring_allowed",
        "memory_lift_claim_allowed",
        "self_maintaining_software_claim_allowed",
        "organic_external_evidence_claim_allowed",
        "controllergate_repair_claim_allowed",
    ]:
        if plan.get(field) is not False:
            errors.append(f"{field} must be false")

    if plan.get("expected_failure_type") != "metadata_manifest_hash_mismatch":
        errors.append("expected_failure_type must be metadata_manifest_hash_mismatch")
    if plan.get("expected_failure_signature") != "HASH_MISMATCH: README.md":
        errors.append("expected_failure_signature must be HASH_MISMATCH: README.md")
    if "validate_metadata_manifest.py" not in str(plan.get("proposed_validator_command")):
        errors.append("proposed_validator_command must use validate_metadata_manifest.py")

    seed = plan.get("proposed_seed_failure_method")
    if not isinstance(seed, dict):
        errors.append("proposed_seed_failure_method must be an object")
        seed = {}
    for field in [
        "failure_is_seeded",
        "failure_class_differs_from_episode_001",
        "failure_class_differs_from_episode_002",
        "not_theory_content",
    ]:
        if seed.get(field) is not True:
            errors.append(f"proposed_seed_failure_method.{field} must be true")

    require_list_contains(
        plan,
        "required_replay_gate_artifacts",
        [
            "clean_clone_transcript",
            "baseline_sha",
            "failing_sha",
            "failing_command",
            "failing_log_raw",
            "failure_signature",
            "post_repair_log_raw",
            "clean_checkout_pre_repair_replay_result",
            "clean_checkout_post_repair_replay_result",
        ],
        errors,
    )
    require_list_contains(
        plan,
        "required_memory_enabled_artifacts",
        [
            "memory_enabled_protocol",
            "memory_enabled_decision_time_inputs",
            "memory_enabled_controllergate_action_trace",
            "memory_enabled_memory_lookup_trace",
            "memory_enabled_memory_use_or_abstention_decision",
            "memory_enabled_patch_diff",
            "memory_enabled_post_repair_log_raw",
            "memory_enabled_outcome",
            "memory_enabled_corruption_check",
        ],
        errors,
    )
    require_list_contains(
        plan,
        "required_corruption_check_artifacts",
        [
            "modified_paths_scope_check",
            "theory_content_unchanged_check",
            "downstream_validator_replay_result",
            "unexpected_file_change_scan",
        ],
        errors,
    )
    require_list_contains(
        plan,
        "required_decision_time_outcome_separation_artifacts",
        [
            "decision_time_inputs_manifest",
            "outcome_only_evidence_manifest",
            "decision_time_outcome_overlap_check",
            "future_leakage_risk_assessment",
        ],
        errors,
    )
    require_list_contains(
        plan,
        "required_sha256_manifest",
        ["SHA256SUMS.txt", "sha256_manifest_verification_transcript", "zero_mismatch_requirement"],
        errors,
    )
    require_list_contains(
        plan,
        "required_proof_obligations_ledger",
        [
            "proof_obligations_ledger.json",
            "replay_gate_obligations",
            "baseline_obligations",
            "memory_enabled_obligations",
            "claim_boundary_obligations",
        ],
        errors,
    )

    baselines = plan.get("required_baseline_artifacts")
    if not isinstance(baselines, dict):
        errors.append("required_baseline_artifacts must be an object")
        baselines = {}
    no_memory = baselines.get("no_memory_baseline")
    if not isinstance(no_memory, dict):
        errors.append("no_memory_baseline must be an object")
        no_memory = {}
    if no_memory.get("required") is not True:
        errors.append("no_memory_baseline.required must be true")
    no_memory_required = set(no_memory.get("required_artifacts") or [])
    for required in [
        "no_memory_baseline_protocol",
        "no_memory_baseline_decision_time_inputs",
        "no_memory_baseline_action_trace",
        "no_memory_baseline_patch_diff",
        "no_memory_baseline_post_repair_log_raw",
        "no_memory_baseline_outcome",
        "no_memory_baseline_corruption_check",
    ]:
        if required not in no_memory_required:
            errors.append(f"no_memory_baseline missing {required!r}")
    for optional_baseline in ["always_rebuild_baseline", "simple_rule_baseline"]:
        baseline = baselines.get(optional_baseline)
        if not isinstance(baseline, dict):
            errors.append(f"{optional_baseline} must be an object")
        elif baseline.get("preferred") is not True:
            errors.append(f"{optional_baseline}.preferred must be true")

    if plan.get("identical_replay_conditions_required") is not True:
        errors.append("identical_replay_conditions_required must be true")
    identical = "\n".join(str(item) for item in plan.get("identical_replay_conditions_definition") or [])
    for required in [
        "same baseline SHA",
        "same failing SHA",
        "same validator command",
        "same decision-time evidence boundary",
        "same post-repair validation command",
        "same corruption/downstream check",
    ]:
        if required not in identical:
            errors.append(f"identical replay conditions missing {required!r}")

    preconditions = "\n".join(str(item) for item in plan.get("scoring_preconditions") or [])
    for required in [
        "Replay Gate passes before any limited scoring",
        "no_memory_baseline artifacts are complete",
        "memory_enabled artifacts are complete",
        "baseline and memory-enabled paths use identical replay conditions",
        "decision-time/outcome overlap check is PASS with zero overlap",
        "corruption/downstream check is PASS",
        "SHA256 manifest verifies with zero mismatches",
    ]:
        if required not in preconditions:
            errors.append(f"scoring_preconditions missing {required!r}")

    disallowed = "\n".join(str(item) for item in plan.get("scoring_disallowed_conditions") or [])
    for required in [
        "full scoring is disallowed",
        "scoring disallowed if Replay Gate fails",
        "scoring disallowed if no_memory_baseline is absent",
        "memory lift claim disallowed if memory_enabled path is absent",
        "memory lift claim disallowed if memory-enabled result does not outperform no-memory under identical replay conditions",
        "self-maintaining software claim disallowed for one seeded controlled episode",
        "organic external repo claim disallowed for seeded controlled evidence",
    ]:
        if required not in disallowed:
            errors.append(f"scoring_disallowed_conditions missing {required!r}")

    result_language = plan.get("result_classification_language")
    if not isinstance(result_language, dict):
        errors.append("result_classification_language must be an object")
        result_language = {}
    for key in ["positive_evidence", "negative_evidence", "blocked_evidence"]:
        if key not in result_language:
            errors.append(f"result_classification_language missing {key}")
    if "memory-enabled result outperforms no-memory without corruption" not in str(
        result_language.get("positive_evidence")
    ):
        errors.append("positive evidence must require memory-enabled outperforming no-memory without corruption")
    if "does not outperform baselines or causes corruption" not in str(result_language.get("negative_evidence")):
        errors.append("negative evidence must include no outperformance or corruption")
    if "baselines are absent" not in str(result_language.get("blocked_evidence")):
        errors.append("blocked evidence must include absent baselines")

    boundaries = plan.get("claim_boundaries")
    if not isinstance(boundaries, dict):
        errors.append("claim_boundaries must be an object")
        boundaries = {}
    for field in [
        "episodes_001_and_002_are_repair_performance_evidence",
        "episode_003_executed",
        "full_scoring_allowed",
        "memory_lift_demonstrated",
        "self_maintaining_software_demonstrated",
        "seeded_controlled_success_equals_organic_external_evidence",
        "one_seeded_episode_can_demonstrate_self_maintaining_software",
    ]:
        if boundaries.get(field) is not False:
            errors.append(f"claim_boundaries.{field} must be false")
    if boundaries.get(
        "memory_lift_requires_memory_enabled_outperforms_no_memory_under_same_replay_protocol"
    ) is not True:
        errors.append("claim boundaries must require memory-enabled outperformance under same replay protocol")

    tatmapper = plan.get("historical_tatmapper_boundary")
    if not isinstance(tatmapper, dict):
        errors.append("historical_tatmapper_boundary must be an object")
        tatmapper = {}
    if tatmapper.get("tatmapper_historical_episodes_remain_review_required") is not True:
        errors.append("TatMapper historical episodes must remain review_required")
    if tatmapper.get("tatmapper_deterministic_replay_ready_count") != 0:
        errors.append("TatMapper deterministic replay-ready count must remain 0")
    if tatmapper.get("do_not_mark_tatmapper_scoreable") is not True:
        errors.append("TatMapper must not be marked scoreable")
    if beta_replay.get("summary", {}).get("eligible_now_count") != 0:
        errors.append("beta replay eligibility count must remain 0")

    if episode_001.get("replay_gate_status") != "capture_complete_not_scoreable":
        errors.append("Episode 001 artifact audit boundary must remain capture_complete_not_scoreable")
    if episode_001.get("allowed_scoring_mode") != "not_scoreable":
        errors.append("Episode 001 must remain not_scoreable")
    if episode_002.get("replay_gate_status") != "capture_complete_not_scoreable":
        errors.append("Episode 002 artifact audit boundary must remain capture_complete_not_scoreable")
    if episode_002.get("allowed_scoring_mode") != "not_scoreable":
        errors.append("Episode 002 must remain not_scoreable")
    if v18.get("full_scoring_allowed") is not False:
        errors.append("v1.8 full scoring boundary must remain false")

    errors.extend(
        require_text(
            PLAN_MD_PATH,
            [
                "Status: preregistered limited replay-scoring candidate design only. Do not execute. Do not score.",
                "Episode 003 is the first possible bridge",
                "They were intentionally `not_scoreable`",
                "limited_replay_scoring_candidate_not_executed",
                "HASH_MISMATCH: README.md",
                "Replay Gate success before any limited scoring",
                "no-memory baseline",
                "memory-enabled ControllerGate path",
                "identical replay conditions",
                "Memory lift remains undemonstrated unless memory-enabled ControllerGate outperforms the no-memory baseline",
                "Positive evidence would be:",
                "Negative evidence would be:",
                "Blocked evidence would be:",
                "One seeded controlled episode cannot demonstrate self-maintaining software.",
            ],
        )
    )
    errors.extend(
        require_text(
            SUMMARY_PATH,
            [
                "## v1.8 Episode 003 limited replay-scoring candidate design",
                "Episode 003 is a preregistered limited replay-scoring candidate design.",
                "Episode 003 is not executed yet.",
                "Baselines are mandatory before memory lift can be evaluated.",
                "Replay Gate must pass before any limited scoring.",
                "Allowed scoring mode: `limited_replay_scoring_candidate_not_executed`.",
                "Expected failure signature: `HASH_MISMATCH: README.md`.",
                "ControllerGate has not demonstrated memory lift.",
                "ControllerGate has not demonstrated self-maintaining software.",
                "Full scoring is not allowed.",
                "Episodes 001/002 were capture evidence, not repair-performance evidence.",
            ],
        )
    )

    if errors:
        print("v1.8 Episode 003 limited replay-scoring candidate plan audit: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1

    print("v1.8 Episode 003 limited replay-scoring candidate plan audit: PASS")
    print("episode_id: v1_8_episode_003")
    print("allowed scoring mode: limited_replay_scoring_candidate_not_executed")
    print("execution status: not_executed")
    print("required baseline: no_memory_baseline")
    print("memory lift claim allowed: false")
    print("self-maintaining software claim allowed: false")
    return 0


if __name__ == "__main__":
    sys.exit(main())
