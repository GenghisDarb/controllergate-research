#!/usr/bin/env python3
"""Audit the v1.8 Episode 003 limited replay-scoring artifact bundle."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_DIR = REPO_ROOT / "outputs" / "v1_8_episode_003_torus_limited_replay_scoring"
EPISODE_001_METADATA_PATH = (
    REPO_ROOT / "outputs" / "v1_8_episode_001_torus_replay_capture" / "episode_001_metadata.json"
)
EPISODE_002_METADATA_PATH = (
    REPO_ROOT / "outputs" / "v1_8_episode_002_torus_replay_capture" / "episode_002_metadata.json"
)
BETA_REPLAY_PLAN_PATH = REPO_ROOT / "controllergate_v1_7_beta" / "outputs" / "v1_7_beta_replay_eligibility_plan.json"
SUMMARY_PATH = (
    REPO_ROOT / "controllergate_v1_7_beta" / "reports" / "critic_review_package" / "shareable_summary.md"
)

REQUIRED_FILES = [
    "episode_003_metadata.json",
    "target_repo_baseline_snapshot.json",
    "environment_snapshot.txt",
    "seeded_failure_snapshot.json",
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

BOUNDARY_FALSE_FIELDS = [
    "full_scoring_allowed",
    "memory_lift_claim_allowed",
    "self_maintaining_software_claim_allowed",
    "organic_external_evidence_claim_allowed",
    "controllergate_repair_claim_allowed",
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


def verify_sha256_manifest() -> list[str]:
    manifest_path = ARTIFACT_DIR / "SHA256SUMS.txt"
    if not manifest_path.exists():
        return ["missing SHA256SUMS.txt"]
    errors: list[str] = []
    seen: set[str] = set()
    for line_no, line in enumerate(manifest_path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        parts = line.split()
        if len(parts) != 2:
            errors.append(f"SHA256SUMS.txt:{line_no}: expected '<sha256>  <filename>'")
            continue
        expected, name = parts
        seen.add(name)
        path = ARTIFACT_DIR / name
        if not path.exists():
            errors.append(f"SHA256SUMS.txt:{line_no}: missing artifact {name}")
            continue
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != expected:
            errors.append(f"SHA256SUMS.txt:{line_no}: hash mismatch for {name}")
    for required in REQUIRED_FILES:
        if required == "SHA256SUMS.txt":
            continue
        if required not in seen:
            errors.append(f"SHA256SUMS.txt missing required artifact entry {required}")
    return errors


def main() -> int:
    errors: list[str] = []
    if not ARTIFACT_DIR.exists():
        errors.append(f"artifact directory missing: {ARTIFACT_DIR}")
    for name in REQUIRED_FILES:
        path = ARTIFACT_DIR / name
        if not path.exists():
            errors.append(f"required artifact missing: {name}")
        elif path.is_file() and path.stat().st_size == 0:
            errors.append(f"required artifact is empty: {name}")

    metadata, metadata_errors = load_json(ARTIFACT_DIR / "episode_003_metadata.json")
    scoring, scoring_errors = load_json(ARTIFACT_DIR / "limited_scoring_result.json")
    comparison, comparison_errors = load_json(ARTIFACT_DIR / "post_repair_comparison.json")
    corruption, corruption_errors = load_json(ARTIFACT_DIR / "corruption_check_result.json")
    overlap, overlap_errors = load_json(ARTIFACT_DIR / "decision_time_outcome_overlap_check.json")
    ledger, ledger_errors = load_json(ARTIFACT_DIR / "proof_obligations_ledger.json")
    no_memory, no_memory_errors = load_json(ARTIFACT_DIR / "no_memory_outcome.json")
    memory_enabled, memory_enabled_errors = load_json(ARTIFACT_DIR / "memory_enabled_outcome.json")
    episode_001, episode_001_errors = load_json(EPISODE_001_METADATA_PATH)
    episode_002, episode_002_errors = load_json(EPISODE_002_METADATA_PATH)
    beta_replay, beta_replay_errors = load_json(BETA_REPLAY_PLAN_PATH)
    errors.extend(
        metadata_errors
        + scoring_errors
        + comparison_errors
        + corruption_errors
        + overlap_errors
        + ledger_errors
        + no_memory_errors
        + memory_enabled_errors
        + episode_001_errors
        + episode_002_errors
        + beta_replay_errors
    )

    if metadata.get("episode_id") != "v1_8_episode_003":
        errors.append("metadata episode_id must be v1_8_episode_003")
    if metadata.get("target_repo_class") != "user_owned_public_repo":
        errors.append("target_repo_class must be user_owned_public_repo")
    if metadata.get("target_repo_name") != "TORUS Theory":
        errors.append("target_repo_name must be TORUS Theory")
    if metadata.get("episode_label") != "seeded_controlled_real_repo_episode":
        errors.append("episode_label must be seeded_controlled_real_repo_episode")
    if metadata.get("failure_signature") != "HASH_MISMATCH: README.md":
        errors.append("failure signature must be HASH_MISMATCH: README.md")
    if metadata.get("replay_gate_status") != "deterministic_replay_ready_limited_scoring":
        errors.append("replay_gate_status must be deterministic_replay_ready_limited_scoring")
    if metadata.get("allowed_scoring_mode") != "limited_replay_scoring_only":
        errors.append("allowed_scoring_mode must be limited_replay_scoring_only")
    if metadata.get("controllergate_full_scoring") != "NOT_RUN":
        errors.append("controllergate_full_scoring must be NOT_RUN")
    for field in BOUNDARY_FALSE_FIELDS:
        if metadata.get(field) is not False:
            errors.append(f"{field} must be false")
    for field in ["baseline_sha", "failing_sha", "no_memory_post_repair_sha", "memory_enabled_post_repair_sha"]:
        value = metadata.get(field)
        if not isinstance(value, str) or len(value) != 40:
            errors.append(f"{field} must be a 40-character git SHA")

    if ledger.get("proof_status") != "complete_limited_replay_scoring_only":
        errors.append("proof ledger status must be complete_limited_replay_scoring_only")
    if ledger.get("replay_gate_status") != "deterministic_replay_ready_limited_scoring":
        errors.append("proof ledger replay gate status mismatch")
    if ledger.get("missing_obligations") != []:
        errors.append("proof ledger missing_obligations must be empty")
    ledger_boundaries = ledger.get("scoring_boundaries") if isinstance(ledger.get("scoring_boundaries"), dict) else {}
    if ledger_boundaries.get("allowed_scoring_mode") != "limited_replay_scoring_only":
        errors.append("proof ledger allowed scoring mode must be limited_replay_scoring_only")
    if ledger_boundaries.get("full_scoring_allowed") is not False:
        errors.append("proof ledger full scoring must remain false")
    if ledger_boundaries.get("memory_lift_claim_allowed") is not False:
        errors.append("proof ledger memory lift claim must remain false")
    if ledger_boundaries.get("self_maintaining_software_claim_allowed") is not False:
        errors.append("proof ledger self-maintaining software claim must remain false")

    if no_memory.get("post_repair_result") != "passed" or no_memory.get("post_repair_exit_code") != 0:
        errors.append("no-memory baseline must have passed with exit code 0")
    if memory_enabled.get("post_repair_result") != "passed" or memory_enabled.get("post_repair_exit_code") != 0:
        errors.append("memory-enabled path must have passed with exit code 0")
    if comparison.get("memory_enabled_outperformed_no_memory") is not False:
        errors.append("memory-enabled path must not be marked as outperforming no-memory")
    if comparison.get("memory_lift_demonstrated") is not False:
        errors.append("memory lift must not be demonstrated by Episode 003")
    if scoring.get("memory_lift_demonstrated") is not False:
        errors.append("limited scoring result must not demonstrate memory lift")
    if scoring.get("result_classification") != "negative_evidence_no_memory_lift_on_seeded_controlled_episode":
        errors.append("limited scoring result classification must preserve no-memory-lift finding")
    if scoring.get("full_scoring_allowed") is not False:
        errors.append("limited scoring full_scoring_allowed must be false")
    if scoring.get("controllergate_full_scoring") != "NOT_RUN":
        errors.append("limited scoring must say ControllerGate full scoring was NOT_RUN")

    if overlap.get("status") != "PASS" or overlap.get("overlap_detected") is not False:
        errors.append("decision-time/outcome overlap check must pass with no overlap")
    if overlap.get("decision_time_outcome_overlap_episode_count") != 0:
        errors.append("decision-time/outcome overlap episode count must be 0")
    if corruption.get("status") != "PASS" or corruption.get("corruption_detected") is not False:
        errors.append("corruption check must pass with no corruption")

    if episode_001.get("replay_gate_status") != "capture_complete_not_scoreable":
        errors.append("Episode 001 must remain capture_complete_not_scoreable")
    if episode_001.get("allowed_scoring_mode") != "not_scoreable":
        errors.append("Episode 001 must remain not_scoreable")
    if episode_002.get("replay_gate_status") != "capture_complete_not_scoreable":
        errors.append("Episode 002 must remain capture_complete_not_scoreable")
    if episode_002.get("allowed_scoring_mode") != "not_scoreable":
        errors.append("Episode 002 must remain not_scoreable")
    if beta_replay.get("summary", {}).get("eligible_now_count") != 0:
        errors.append("TatMapper replay-ready eligibility count must remain 0")

    errors.extend(
        require_text(
            ARTIFACT_DIR / "failing_log_raw.txt",
            ["metadata manifest validation failed", "HASH_MISMATCH: README.md"],
        )
    )
    errors.extend(
        require_text(
            ARTIFACT_DIR / "no_memory_post_repair_log_raw.txt",
            ["metadata manifest validation passed", "required_files_checked: 1"],
        )
    )
    errors.extend(
        require_text(
            ARTIFACT_DIR / "memory_enabled_post_repair_log_raw.txt",
            ["metadata manifest validation passed", "required_files_checked: 1"],
        )
    )
    errors.extend(
        require_text(
            ARTIFACT_DIR / "clean_checkout_replay_transcript.txt",
            [
                "clean_checkout_failing_exit_code: 1",
                "no_memory_post_repair_exit_code: 0",
                "memory_enabled_post_repair_exit_code: 0",
            ],
        )
    )
    errors.extend(
        require_text(
            ARTIFACT_DIR / "no_memory_repair_patch.diff",
            ["bafd986922ca464dddf9cbc3eb7ace716272dbb9571b65694dc57059fc16128f"],
        )
    )
    errors.extend(
        require_text(
            ARTIFACT_DIR / "memory_enabled_repair_patch.diff",
            ["bafd986922ca464dddf9cbc3eb7ace716272dbb9571b65694dc57059fc16128f"],
        )
    )
    errors.extend(
        require_text(
            SUMMARY_PATH,
            [
                "## v1.8 Episode 003 limited replay-scoring execution result",
                "Episode 003 is the first controlled limited replay-scoring attempt.",
                "Result classification: `negative_evidence_no_memory_lift_on_seeded_controlled_episode`.",
                "Replay gate status: `deterministic_replay_ready_limited_scoring`.",
                "No-memory baseline result: `passed`.",
                "Memory-enabled path result: `passed`.",
                "Memory-enabled outperformed no-memory: `false`.",
                "Memory lift is only evaluated against no-memory baseline.",
                "Full scoring remains disallowed.",
                "Self-maintaining software remains undemonstrated.",
                "This is seeded controlled evidence, not organic external evidence.",
            ],
        )
    )
    errors.extend(verify_sha256_manifest())

    if errors:
        print("v1.8 Episode 003 limited replay-scoring artifact audit: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1

    print("v1.8 Episode 003 limited replay-scoring artifact audit: PASS")
    print("episode_id: v1_8_episode_003")
    print("failure signature: HASH_MISMATCH: README.md")
    print("replay_gate_status: deterministic_replay_ready_limited_scoring")
    print("allowed scoring mode: limited_replay_scoring_only")
    print("no-memory baseline result: passed")
    print("memory-enabled path result: passed")
    print("memory-enabled outperformed no-memory: false")
    print("memory lift demonstrated: false")
    print("full scoring allowed: false")
    print("self-maintaining software demonstrated: false")
    return 0


if __name__ == "__main__":
    sys.exit(main())
