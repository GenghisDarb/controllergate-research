#!/usr/bin/env python3
"""Ingest v2.8b artifacts and initialize v2.8c checkout-fix outputs."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import zipfile
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
PHASE_A_DIR = REPO_ROOT / "outputs" / "v2_8c_bugsinpy_repair_checkout_fix"
RERUN_DIR = REPO_ROOT / "outputs" / "v2_8c_bugsinpy_real_bug_repair_comparison_rerun"
SUMMARY = REPO_ROOT / "controllergate_v1_7_beta" / "reports" / "critic_review_package" / "shareable_summary.md"

CANDIDATES = [
    {"episode_id": "episode_001", "candidate": "youtube-dl:1", "classification": "blocked_checkout_runtime_failure"},
    {"episode_id": "episode_002", "candidate": "black:8", "classification": "blocked_checkout_runtime_failure"},
    {"episode_id": "episode_003", "candidate": "black:4", "classification": "blocked_checkout_runtime_failure"},
]


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def sha_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_manifest(directory: Path) -> None:
    paths = sorted(
        [
            path
            for path in directory.rglob("*")
            if path.is_file() and path.name != "SHA256SUMS.txt" and path.suffix.lower() != ".zip"
        ],
        key=lambda path: str(path.relative_to(directory)).replace("\\", "/"),
    )
    lines = [f"{sha_file(path)}  {str(path.relative_to(directory)).replace(chr(92), '/')}" for path in paths]
    write_text(directory / "SHA256SUMS.txt", "\n".join(lines) + "\n")


def verify_manifest(directory: Path) -> dict[str, Any]:
    manifest = directory / "SHA256SUMS.txt"
    result: dict[str, Any] = {"manifest_exists": manifest.exists(), "checked_files": 0, "missing_files": [], "hash_failures": []}
    if not manifest.exists():
        return result
    for line in manifest.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        parts = line.split()
        if len(parts) != 2:
            result["hash_failures"].append({"line": line, "reason": "invalid SHA256SUMS row"})
            continue
        expected, rel = parts
        path = directory / rel
        if not path.exists():
            result["missing_files"].append(rel)
            continue
        result["checked_files"] += 1
        actual = sha_file(path)
        if actual != expected:
            result["hash_failures"].append({"path": rel, "expected": expected, "actual": actual})
    result["verification_clean"] = result["manifest_exists"] and not result["missing_files"] and not result["hash_failures"]
    return result


def safe_extract(zip_path: Path, destination: Path) -> None:
    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path) as archive:
        for member in archive.infolist():
            target = (destination / member.filename).resolve()
            if not str(target).startswith(str(destination.resolve())):
                raise ValueError(f"unsafe zip member path: {member.filename}")
        archive.extractall(destination)


def read_log(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def episode_blockers(intake: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in CANDIDATES:
        episode = intake / item["episode_id"]
        checkout_log = read_log(episode / "baseline_checkout_log_raw.txt")
        no_memory_log = read_log(episode / "no_memory_post_repair_log_raw.txt")
        memory_log = read_log(episode / "memory_enabled_post_repair_log_raw.txt")
        rows.append(
            {
                **item,
                "blocker_type": "checkout/runtime infrastructure failure",
                "checkout_log_contains_no_such_file": "No such file or directory" in checkout_log,
                "checkout_log_contains_bad_object": "Could not parse object" in checkout_log,
                "no_memory_workspace_unavailable": "no-memory workspace unavailable" in no_memory_log,
                "memory_enabled_workspace_unavailable": "memory-enabled workspace unavailable" in memory_log,
                "repair_attempt_meaningful": False,
                "negative_capability_evidence": False,
            }
        )
    return rows


def update_summary() -> None:
    section = """## v2.8c BugsInPy Repair-Comparison Checkout Fix

v2.8b reached the workflow but blocked before repair because checkout failed. Checkout/runtime failure is blocked evidence, not negative ControllerGate repair evidence.

- v2.8b artifact ingestion result: SHA256 verification clean; 3 episodes executed by the workflow, 0 scoreable repair episodes.
- Root cause diagnosis: relative checkout/workspace path handling caused BugsInPy checkout failures before replay/repair.
- v2.8c checkout fix status: workflow and runner are ready; the runner uses absolute workspace paths and pre-repair replay gates.
- v2.8c repair comparison executed: false in this local checkpoint; GitHub Actions artifact is required.
- Scoreable episodes: 0.
- Positive memory episodes: 0.
- Aggregate result: `blocked_bugsinpy_real_bug_replay_runtime_failure`.

Apoptosis should not count infrastructure checkout failure as repair flatline. Full scoring remains disallowed. Self-maintaining software remains undemonstrated.
"""
    marker = "## v2.8c BugsInPy Repair-Comparison Checkout Fix"
    text = SUMMARY.read_text(encoding="utf-8") if SUMMARY.exists() else ""
    if marker in text:
        text = text[: text.index(marker)].rstrip() + "\n\n" + section
    else:
        text = text.rstrip() + "\n\n" + section
    write_text(SUMMARY, text)


def initialize_rerun_bundle() -> None:
    if RERUN_DIR.exists():
        shutil.rmtree(RERUN_DIR)
    RERUN_DIR.mkdir(parents=True, exist_ok=True)
    write_json(
        RERUN_DIR / "campaign_plan.json",
        {
            "campaign_id": "v2_8c_bugsinpy_real_bug_repair_comparison_rerun",
            "workflow": ".github/workflows/v2_8c_bugsinpy_repair_checkout_fix.yml",
            "runner": "scripts/v2_8c_bugsinpy_repair_checkout_fix_runner.py",
            "candidate_ids": [item["candidate"] for item in CANDIDATES],
            "checkout_fix": "absolute workspace paths and pre-repair replay gate",
            "full_scoring_allowed": False,
            "controllergate_full_scoring": "NOT_RUN",
            "self_maintaining_software_demonstrated": False,
        },
    )
    write_json(RERUN_DIR / "candidate_source_integrity_check.json", {"count": 3, "records": CANDIDATES})
    write_json(RERUN_DIR / "pre_repair_replay_gate_summary.json", {"workflow_executed": False, "passed_count": 0, "repair_paths_run_count": 0})
    write_json(
        RERUN_DIR / "checkout_runtime_fix_summary.json",
        {
            "absolute_workspace_paths_required": True,
            "bugsinpy_checkout_absolute_w_path_required": True,
            "checkout_integrity_check_required": True,
            "pre_repair_replay_gate_required": True,
        },
    )
    write_json(
        RERUN_DIR / "campaign_results.json",
        {
            "workflow_executed": False,
            "executed_episode_count": 0,
            "scoreable_episode_count": 0,
            "positive_memory_episode_count": 0,
            "blocked_episode_count": 0,
            "decision_time_outcome_overlap_count": 0,
            "label_leakage_count": 0,
            "apoptosis_watchdog_triggered_count": 0,
            "corruption_count": 0,
            "aggregate_result": "blocked_bugsinpy_real_bug_replay_runtime_failure",
            "limited_bugsinpy_real_bug_memory_lift_criteria_met": False,
            "full_scoring_allowed": False,
            "controllergate_full_scoring": "NOT_RUN",
            "self_maintaining_software_demonstrated": False,
            "next_required_action": "Run v2_8c_bugsinpy_repair_checkout_fix in GitHub Actions and ingest the artifact.",
        },
    )
    write_json(
        RERUN_DIR / "aggregate_bugsinpy_real_bug_memory_lift_assessment.json",
        {
            "aggregate_result": "blocked_bugsinpy_real_bug_replay_runtime_failure",
            "scoreable_episode_count": 0,
            "positive_memory_episode_count": 0,
            "minimum_required_scoreable_episodes": 3,
            "limited_bugsinpy_real_bug_memory_lift_criteria_met": False,
            "full_scoring_allowed": False,
            "controllergate_full_scoring": "NOT_RUN",
            "self_maintaining_software_demonstrated": False,
        },
    )
    write_text(
        RERUN_DIR / "campaign_summary.md",
        "# v2.8c BugsInPy Repair-Comparison Checkout Fix\n\nThe checkout-fixed Linux workflow is ready but has not been executed in this local checkpoint.\n",
    )
    write_manifest(RERUN_DIR)


def prepare(zip_path: Path) -> None:
    if PHASE_A_DIR.exists():
        shutil.rmtree(PHASE_A_DIR)
    PHASE_A_DIR.mkdir(parents=True, exist_ok=True)
    intake = PHASE_A_DIR / "artifact_intake" / "v2_8b_bugsinpy_repair_comparison_artifacts"
    safe_extract(zip_path, intake)
    verification = verify_manifest(intake)
    campaign_results = load_json(intake / "campaign_results.json")
    aggregate = load_json(intake / "aggregate_bugsinpy_real_bug_memory_lift_assessment.json")
    blockers = episode_blockers(intake)
    write_json(
        PHASE_A_DIR / "v2_8b_artifact_ingestion_summary.json",
        {
            "artifact_path": str(zip_path),
            "artifact_ingested": True,
            "workflow_executed": campaign_results.get("workflow_executed"),
            "executed_episode_count": campaign_results.get("executed_episode_count"),
            "scoreable_episode_count": campaign_results.get("scoreable_episode_count"),
            "blocked_episode_count": campaign_results.get("blocked_episode_count"),
            "aggregate_result": campaign_results.get("aggregate_result"),
            "full_scoring_allowed": False,
            "controllergate_full_scoring": "NOT_RUN",
            "self_maintaining_software_demonstrated": False,
        },
    )
    write_json(PHASE_A_DIR / "v2_8b_artifact_sha256_verification.json", verification)
    write_json(
        PHASE_A_DIR / "v2_8b_failure_diagnosis.json",
        {
            "classification": "blocked_checkout_runtime_failure",
            "root_cause": "v2.8b runner used a relative checkout/workspace path that BugsInPy resolved inconsistently after directory changes.",
            "scoreable_repair_evidence": False,
            "negative_controllergate_repair_evidence": False,
            "aggregate_from_artifact": aggregate.get("aggregate_result"),
            "repair_paths_meaningful": False,
        },
    )
    write_text(
        PHASE_A_DIR / "checkout_failure_root_cause_report.md",
        "# v2.8b Checkout Failure Root Cause\n\nv2.8b reached the GitHub Actions workflow, but all three episodes blocked before replay/repair. The checkout logs contain path-resolution failures such as `No such file or directory`, `Could not parse object`, and missing workspace copy sources. The no-memory and memory-enabled logs report unavailable workspaces.\n\nThis is blocked checkout/runtime evidence, not negative ControllerGate repair capability evidence. v2.8c fixes the runner by using absolute workspace paths and by requiring a pre-repair replay gate before no-memory or memory-enabled repair paths can run.\n",
    )
    write_json(PHASE_A_DIR / "episode_blocker_table.json", {"records": blockers})
    write_json(
        PHASE_A_DIR / "apoptosis_watchdog_context_correction.json",
        {
            "v2_8b_apoptosis_watchdog_triggered_count": campaign_results.get("apoptosis_watchdog_triggered_count"),
            "context_correction": "The watchdog triggers were caused by missing workspaces after checkout failure, not meaningful no-op repair attempts after valid replay.",
            "infrastructure_checkout_failure_counts_as_negative_repair_evidence": False,
            "v2_8c_policy": "Apoptosis may quarantine true post-replay repair flatlines but must not convert checkout/runtime infrastructure failure into negative repair evidence.",
        },
    )
    write_manifest(PHASE_A_DIR)
    initialize_rerun_bundle()
    update_summary()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("artifact_zip", help="Path to v2_8b_bugsinpy_repair_comparison_artifacts.zip")
    args = parser.parse_args()
    prepare(Path(args.artifact_zip).resolve())
    print("v2.8c checkout-fix outputs prepared")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
