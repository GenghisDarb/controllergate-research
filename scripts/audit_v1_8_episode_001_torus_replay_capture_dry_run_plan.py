#!/usr/bin/env python3
"""Audit the v1.8 Episode 001 TORUS replay-capture dry-run plan."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
EPISODE_JSON_PATH = REPO_ROOT / "outputs" / "v1_8_episode_001_torus_replay_capture_dry_run_plan.json"
EPISODE_MD_PATH = REPO_ROOT / "outputs" / "v1_8_episode_001_torus_replay_capture_dry_run_plan.md"
V18_PLAN_JSON_PATH = REPO_ROOT / "outputs" / "v1_8_controlled_repo_replay_capture_plan.json"
SHAREABLE_SUMMARY_PATH = (
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
    plan, plan_errors = load_json(EPISODE_JSON_PATH)
    v18, v18_errors = load_json(V18_PLAN_JSON_PATH)
    errors = plan_errors + v18_errors

    if plan.get("episode_id") != "v1_8_episode_001":
        errors.append("episode_id must be v1_8_episode_001")
    if plan.get("plan_status") != "dry_run_capture_design_only":
        errors.append("plan_status must be dry_run_capture_design_only")
    if plan.get("target_repo_class") != "user_owned_public_repo":
        errors.append("target_repo_class must be user_owned_public_repo")
    if plan.get("target_repo_full_name") != "GenghisDarb/TORUS-Theory":
        errors.append("target repo must be GenghisDarb/TORUS-Theory")
    if plan.get("episode_label") != "seeded_controlled_real_repo_episode":
        errors.append("episode_label must be seeded_controlled_real_repo_episode")
    if plan.get("purpose") != "validate replay capture harness before scoring":
        errors.append("purpose must validate replay capture harness before scoring")
    if plan.get("allowed_scoring_mode") != "not_scoreable":
        errors.append("allowed_scoring_mode must be not_scoreable")

    for field in [
        "full_scoring_allowed",
        "memory_lift_claim_allowed",
        "self_maintaining_software_claim_allowed",
        "organic_external_evidence_claim_allowed",
        "subjective_theory_correctness_claim_allowed",
    ]:
        if plan.get(field) is not False:
            errors.append(f"{field} must be false")

    if plan.get("proposed_failure_type") != "metadata_manifest_validation_failure":
        errors.append("proposed_failure_type must be metadata_manifest_validation_failure")
    if "validate_metadata_manifest.py" not in str(plan.get("proposed_validator_command")):
        errors.append("proposed_validator_command must use validate_metadata_manifest.py")

    seed = plan.get("proposed_seed_failure_method")
    if not isinstance(seed, dict):
        errors.append("proposed_seed_failure_method must be an object")
        seed = {}
    if seed.get("failure_is_seeded") is not True:
        errors.append("seeded failure must be explicit")
    if seed.get("not_theory_content") is not True:
        errors.append("seeded failure must avoid subjective theory content")

    required_pre = [
        "clean_clone_transcript",
        "baseline_sha",
        "original_repo_snapshot_manifest",
        "original_repo_sha256_manifest",
        "environment_snapshot",
        "setup_command_transcript",
        "changed_files_snapshot_before_seed",
    ]
    required_failure = [
        "failing_sha",
        "seed_patch_diff",
        "failing_command",
        "failing_log_raw",
        "failure_signature",
        "pre_repair_replay_transcript",
        "decision_time_inputs",
        "decision_time_outcome_overlap_check",
        "proof_obligations_ledger_pre_repair",
    ]
    required_repair = [
        "controllergate_action_trace",
        "human_required_flag",
        "repair_patch_diff",
        "post_repair_sha_if_repair_attempted",
        "corruption_check_result",
    ]
    required_post = [
        "post_repair_command",
        "post_repair_log_raw",
        "post_repair_outcome",
        "post_repair_replay_transcript",
        "clean_checkout_post_repair_replay_result",
        "proof_obligations_ledger_post_repair",
    ]
    required_hash = [
        "sha256_manifest_path",
        "sha256_manifest_for_original_snapshot",
        "sha256_manifest_for_failing_artifacts",
        "sha256_manifest_for_repair_artifacts",
        "sha256_manifest_for_post_repair_artifacts",
    ]

    require_list_contains(plan, "required_pre_capture_artifacts", required_pre, errors)
    require_list_contains(plan, "required_failure_capture_artifacts", required_failure, errors)
    require_list_contains(plan, "required_repair_capture_artifacts", required_repair, errors)
    require_list_contains(plan, "required_post_repair_artifacts", required_post, errors)
    require_list_contains(plan, "required_hash_artifacts", required_hash, errors)

    replay_checks = plan.get("replay_gate_checks")
    if not isinstance(replay_checks, list):
        errors.append("replay_gate_checks must be a list")
        replay_checks = []
    replay_text = "\n".join(str(item) for item in replay_checks)
    for required in [
        "clean checkout can reproduce pre-repair failure",
        "failing command is explicit",
        "raw failing log is captured",
        "failure signature is captured",
        "repair patch/action trace is captured if repair is attempted",
        "post-repair validation command is explicit",
        "raw post-repair log is captured",
        "SHA256 manifest covers all input/output artifacts",
        "proof obligations ledger exists",
    ]:
        if required not in replay_text:
            errors.append(f"replay_gate_checks missing {required!r}")

    discard = plan.get("discard_conditions")
    if not isinstance(discard, list):
        errors.append("discard_conditions must be a list")
        discard = []
    discard_set = set(discard)
    for required in [
        "discard_before_scoring_if_clean_checkout_cannot_reproduce_pre_repair_failure",
        "discard_before_scoring_if_failing_log_missing",
        "discard_before_scoring_if_failure_signature_missing",
        "discard_before_scoring_if_repair_patch_or_action_trace_missing",
        "discard_before_scoring_if_post_repair_validation_missing",
        "discard_before_scoring_if_decision_time_inputs_include_future_outcome_evidence",
    ]:
        if required not in discard_set:
            errors.append(f"discard_conditions missing {required!r}")

    excluded = set(plan.get("excluded_task_types") or [])
    for required in [
        "subjective_theory_content_correctness",
        "broad_documentation_improvement",
        "security_task",
        "private_credential_task",
        "network_only_validator",
        "non_deterministic_quality_judgment",
    ]:
        if required not in excluded:
            errors.append(f"excluded_task_types missing {required!r}")

    if plan.get("baseline_comparison_status") != "not_run_in_dry_run":
        errors.append("baseline_comparison_status must be not_run_in_dry_run")
    baseline = plan.get("baseline_comparison_boundary")
    if not isinstance(baseline, dict):
        errors.append("baseline_comparison_boundary must be an object")
        baseline = {}
    for field in ["memory_lift_claim_allowed", "controllergate_advantage_claim_allowed"]:
        if baseline.get(field) is not False:
            errors.append(f"baseline_comparison_boundary.{field} must be false")

    promotion = plan.get("episode_002_promotion_requirements")
    if not isinstance(promotion, list):
        errors.append("episode_002_promotion_requirements must be a list")
        promotion = []
    promotion_text = "\n".join(str(item) for item in promotion)
    for required in [
        "Episode 001 dry run produces complete artifact bundle",
        "Replay Gate passes on clean checkout for pre-repair failure",
        "SHA256 manifest validates with zero mismatches",
        "Decision-time/outcome overlap check remains zero",
        "Baseline comparison instrumentation is specified before any limited replay scoring",
    ]:
        if required not in promotion_text:
            errors.append(f"episode_002_promotion_requirements missing {required!r}")

    v18_target = (((v18.get("controlled_target_repo_policy") or {}).get("preferred_initial_target")) or {}).get(
        "repo_full_name"
    )
    if v18_target != plan.get("target_repo_full_name"):
        errors.append("Episode 001 target must match v1.8 preferred initial target")
    if v18.get("full_scoring_allowed") is not False:
        errors.append("v1.8 full scoring boundary must remain false")

    errors.extend(
        require_text(
            EPISODE_MD_PATH,
            [
                "Status: dry-run capture design only. Do not score.",
                "Episode 001 is therefore `not_scoreable`.",
                "metadata manifest validation",
                "It does not judge TORUS theory content or scientific correctness.",
                "Replay Gate",
                "Allowed scoring mode: `not_scoreable`.",
                "Memory-lift claims remain false.",
                "Self-maintaining software claims remain false.",
                "What Would Allow Episode 002 To Advance",
            ],
        )
    )
    errors.extend(
        require_text(
            SHAREABLE_SUMMARY_PATH,
            [
                "## v1.8 Episode 001 dry-run capture plan",
                "Episode 001 is a dry-run capture plan.",
                "The TORUS repo is a controlled testbed.",
                "The purpose is to validate replay capture, not repair capability.",
                "No scoring is allowed yet.",
                "ControllerGate has not repaired TORUS.",
            ],
        )
    )

    if errors:
        print("v1.8 Episode 001 TORUS replay-capture dry-run plan audit: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1

    print("v1.8 Episode 001 TORUS replay-capture dry-run plan audit: PASS")
    print("episode_id: v1_8_episode_001")
    print("episode label: seeded_controlled_real_repo_episode")
    print("allowed scoring mode: not_scoreable")
    print("full scoring allowed: false")
    print("self-maintaining claim: NOT ALLOWED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
