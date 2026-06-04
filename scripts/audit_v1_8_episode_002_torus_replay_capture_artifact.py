#!/usr/bin/env python3
"""Audit the v1.8 Episode 002 TORUS replay-capture artifact bundle."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_DIR = REPO_ROOT / "outputs" / "v1_8_episode_002_torus_replay_capture"
EPISODE_001_ARTIFACT_METADATA_PATH = (
    REPO_ROOT / "outputs" / "v1_8_episode_001_torus_replay_capture" / "episode_001_metadata.json"
)
SUMMARY_PATH = (
    REPO_ROOT / "controllergate_v1_7_beta" / "reports" / "critic_review_package" / "shareable_summary.md"
)

REQUIRED_FILES = [
    "episode_002_metadata.json",
    "target_repo_baseline_snapshot.json",
    "pre_repair_changed_files_snapshot.txt",
    "environment_snapshot.txt",
    "failing_command.txt",
    "failing_log_raw.txt",
    "failure_signature.txt",
    "pre_repair_replay_transcript.txt",
    "repair_patch.diff",
    "post_repair_command.txt",
    "post_repair_log_raw.txt",
    "post_repair_outcome.json",
    "decision_time_inputs_manifest.json",
    "decision_time_outcome_overlap_check.json",
    "proof_obligations_ledger.json",
    "SHA256SUMS.txt",
]

BOUNDARY_FALSE_FIELDS = [
    "full_scoring_allowed",
    "memory_lift_claim_allowed",
    "self_maintaining_software_claim_allowed",
    "organic_external_evidence_claim_allowed",
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

    metadata, metadata_errors = load_json(ARTIFACT_DIR / "episode_002_metadata.json")
    ledger, ledger_errors = load_json(ARTIFACT_DIR / "proof_obligations_ledger.json")
    overlap, overlap_errors = load_json(ARTIFACT_DIR / "decision_time_outcome_overlap_check.json")
    outcome, outcome_errors = load_json(ARTIFACT_DIR / "post_repair_outcome.json")
    baseline, baseline_errors = load_json(ARTIFACT_DIR / "target_repo_baseline_snapshot.json")
    episode_001, episode_001_errors = load_json(EPISODE_001_ARTIFACT_METADATA_PATH)
    errors.extend(
        metadata_errors
        + ledger_errors
        + overlap_errors
        + outcome_errors
        + baseline_errors
        + episode_001_errors
    )

    if metadata.get("episode_id") != "v1_8_episode_002":
        errors.append("metadata episode_id must be v1_8_episode_002")
    if metadata.get("target_repo_class") != "user_owned_public_repo":
        errors.append("target_repo_class must be user_owned_public_repo")
    if metadata.get("target_repo_name") != "TORUS Theory":
        errors.append("target_repo_name must be TORUS Theory")
    if metadata.get("episode_label") != "seeded_controlled_real_repo_episode":
        errors.append("episode_label must be seeded_controlled_real_repo_episode")
    if metadata.get("allowed_scoring_mode") != "not_scoreable":
        errors.append("allowed_scoring_mode must be not_scoreable")
    if metadata.get("controllergate_full_scoring") != "NOT_RUN":
        errors.append("controllergate_full_scoring must be NOT_RUN")
    for field in BOUNDARY_FALSE_FIELDS:
        if metadata.get(field) is not False:
            errors.append(f"{field} must be false")
    for field in ["baseline_sha", "failing_sha", "post_repair_sha"]:
        value = metadata.get(field)
        if not isinstance(value, str) or len(value) != 40:
            errors.append(f"{field} must be a 40-character git SHA")
    if metadata.get("failing_command") != "python tools/validate_metadata_manifest.py metadata_manifest.json":
        errors.append("failing_command does not match preregistered command")
    if metadata.get("post_repair_command") != "python tools/validate_metadata_manifest.py metadata_manifest.json":
        errors.append("post_repair_command does not match preregistered command")
    if metadata.get("failure_signature") != "TYPE_MISMATCH: version":
        errors.append("failure_signature must be TYPE_MISMATCH: version")
    if metadata.get("replay_gate_status") != "capture_complete_not_scoreable":
        errors.append("replay_gate_status must be capture_complete_not_scoreable")
    if metadata.get("replay_gate_failures") != []:
        errors.append("replay_gate_failures must be empty for capture_complete_not_scoreable")

    if episode_001.get("replay_gate_status") != "capture_complete_not_scoreable":
        errors.append("Episode 001 must remain capture_complete_not_scoreable")
    if episode_001.get("allowed_scoring_mode") != "not_scoreable":
        errors.append("Episode 001 must remain not_scoreable")

    if ledger.get("proof_status") != "complete_not_scoreable":
        errors.append("proof ledger status must be complete_not_scoreable")
    if ledger.get("missing_obligations") != []:
        errors.append("proof ledger missing_obligations must be empty")
    ledger_boundaries = ledger.get("scoring_boundaries")
    if not isinstance(ledger_boundaries, dict):
        errors.append("proof ledger scoring_boundaries must be an object")
        ledger_boundaries = {}
    if ledger_boundaries.get("allowed_scoring_mode") != "not_scoreable":
        errors.append("proof ledger allowed_scoring_mode must be not_scoreable")
    for field in BOUNDARY_FALSE_FIELDS:
        if ledger_boundaries.get(field) is not False:
            errors.append(f"proof ledger {field} must be false")

    if overlap.get("overlap_detected") is not False:
        errors.append("decision-time/outcome overlap must be false")
    if overlap.get("decision_time_outcome_overlap_episode_count") != 0:
        errors.append("decision_time_outcome_overlap_episode_count must be 0")
    if overlap.get("status") != "PASS":
        errors.append("decision-time/outcome overlap status must be PASS")

    if outcome.get("post_repair_result") != "passed":
        errors.append("post_repair_result must be passed")
    if outcome.get("post_repair_exit_code") != 0:
        errors.append("post_repair_exit_code must be 0")
    if baseline.get("target_repo_url") != "https://github.com/GenghisDarb/TORUS-Theory":
        errors.append("baseline target repo URL must be GenghisDarb/TORUS-Theory")
    if baseline.get("modification_boundary") is None:
        errors.append("baseline snapshot must document modification boundary")

    errors.extend(
        require_text(
            ARTIFACT_DIR / "failing_log_raw.txt",
            ["metadata manifest validation failed", "TYPE_MISMATCH: version"],
        )
    )
    errors.extend(
        require_text(
            ARTIFACT_DIR / "post_repair_log_raw.txt",
            ["metadata manifest validation passed", "required_files_checked: 2"],
        )
    )
    errors.extend(
        require_text(
            ARTIFACT_DIR / "clean_checkout_replay_transcript.txt",
            ["failing_exit_code: 1", "post_repair_exit_code: 0"],
        )
    )
    errors.extend(
        require_text(
            ARTIFACT_DIR / "repair_patch.diff",
            ['+  "version": "episode-002-dry-run",'],
        )
    )
    errors.extend(
        require_text(
            SUMMARY_PATH,
            [
                "## v1.8 Episode 002 artifact dry-run result",
                "Episode 002 validates replay-capture artifact generation for a second deterministic failure class.",
                "Episode 002 remains `not_scoreable`.",
                "The TORUS repo was used as a controlled user-owned testbed.",
                "This is seeded controlled evidence, not organic external evidence.",
                "ControllerGate has not repaired TORUS.",
                "Memory lift is not demonstrated.",
                "Self-maintaining software is not demonstrated.",
                "Full scoring is not allowed.",
            ],
        )
    )
    errors.extend(verify_sha256_manifest())

    if errors:
        print("v1.8 Episode 002 TORUS replay-capture artifact audit: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1

    print("v1.8 Episode 002 TORUS replay-capture artifact audit: PASS")
    print("episode_id: v1_8_episode_002")
    print("episode label: seeded_controlled_real_repo_episode")
    print("failure signature: TYPE_MISMATCH: version")
    print("replay_gate_status: capture_complete_not_scoreable")
    print("allowed scoring mode: not_scoreable")
    print("full scoring allowed: false")
    print("memory lift claim allowed: false")
    print("self-maintaining software claim allowed: false")
    return 0


if __name__ == "__main__":
    sys.exit(main())
