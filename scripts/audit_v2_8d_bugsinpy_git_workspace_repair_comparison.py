#!/usr/bin/env python3
"""Audit v2.8d BugsInPy git-workspace repair comparison artifact ingestion."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = REPO_ROOT / "outputs" / "v2_8d_bugsinpy_git_workspace_repair_comparison"
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "v2_8d_bugsinpy_git_workspace_repair_comparison.yml"
RUNNER = REPO_ROOT / "scripts" / "v2_8c_bugsinpy_repair_checkout_fix_runner.py"
SUMMARY = REPO_ROOT / "controllergate_v1_7_beta" / "reports" / "critic_review_package" / "shareable_summary.md"

REQUIRED_FILES = [
    "artifact_ingestion_summary.json",
    "artifact_sha256_verification.json",
    "episode_result_table.json",
    "git_workspace_runner_result.json",
    "campaign_results.json",
    "aggregate_bugsinpy_real_bug_memory_lift_assessment.json",
    "campaign_summary.md",
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
            if path.is_file() and path.name != "SHA256SUMS.txt" and path.suffix.lower() != ".zip":
                rel = str(path.relative_to(directory)).replace("\\", "/")
                if rel not in seen:
                    errors.append(f"SHA256SUMS missing artifact entry {rel}")
    return errors


def require_text(path: Path, snippets: list[str]) -> list[str]:
    if not path.exists():
        return [f"missing text file: {path}"]
    text = path.read_text(encoding="utf-8", errors="replace")
    return [f"{path}: missing required text {snippet!r}" for snippet in snippets if snippet not in text]


def main() -> int:
    errors: list[str] = []
    if not OUTPUT_DIR.exists():
        errors.append(f"missing v2.8d output directory: {OUTPUT_DIR}")
    for path in [WORKFLOW, RUNNER]:
        if not path.exists():
            errors.append(f"missing v2.8d implementation file: {path}")
    for name in REQUIRED_FILES:
        path = OUTPUT_DIR / name
        if not path.exists():
            errors.append(f"missing v2.8d artifact {name}")
        elif path.stat().st_size == 0:
            errors.append(f"empty v2.8d artifact {name}")

    ingestion, ingestion_errors = load_json(OUTPUT_DIR / "artifact_ingestion_summary.json")
    verification, verification_errors = load_json(OUTPUT_DIR / "artifact_sha256_verification.json")
    episode_table, episode_errors = load_json(OUTPUT_DIR / "episode_result_table.json")
    runner_result, runner_errors = load_json(OUTPUT_DIR / "git_workspace_runner_result.json")
    campaign_results, campaign_errors = load_json(OUTPUT_DIR / "campaign_results.json")
    aggregate, aggregate_errors = load_json(OUTPUT_DIR / "aggregate_bugsinpy_real_bug_memory_lift_assessment.json")
    errors.extend(ingestion_errors + verification_errors + episode_errors + runner_errors + campaign_errors + aggregate_errors)

    if verification.get("verification_clean") is not True:
        errors.append("v2.8d artifact SHA256 verification must be clean")
    if ingestion.get("workflow_executed") is not True or ingestion.get("executed_episode_count") != 3:
        errors.append("v2.8d workflow must have executed three episodes")
    records = episode_table.get("records", [])
    if len(records) != 3:
        errors.append("v2.8d episode result table must contain exactly three episodes")
    required_candidates = {"youtube-dl:1", "black:8", "black:4"}
    if {item.get("candidate") for item in records} != required_candidates:
        errors.append("v2.8d candidates must be youtube-dl:1, black:8, and black:4")
    for item in records:
        if item.get("pre_repair_replay_gate_passed") is not True:
            errors.append(f"{item.get('candidate')}: pre-repair replay gate must pass")
        if item.get("target_failure_matched") is not True:
            errors.append(f"{item.get('candidate')}: target failure must match")
        if item.get("copy_strategy") != "git_clone_no_local":
            errors.append(f"{item.get('candidate')}: repair workspace must use git_clone_no_local")
        if item.get("scoreable") is not False or item.get("classification") != "blocked_apoptosis_watchdog_triggered":
            errors.append(f"{item.get('candidate')}: expected blocked apoptosis/no-op classification")
    if runner_result.get("checkout_runtime_blocker_resolved") is not True:
        errors.append("v2.8d must record checkout/runtime blocker resolved")
    if runner_result.get("all_pre_repair_replay_gates_passed") is not True:
        errors.append("v2.8d must record all pre-repair replay gates passed")
    if runner_result.get("all_repair_workspaces_created_with_git") is not True:
        errors.append("v2.8d must record all repair workspaces created with git")
    if runner_result.get("negative_repair_capability_evidence") is not False:
        errors.append("v2.8d no-op block must not be labeled negative repair capability evidence")
    if campaign_results.get("aggregate_result") != "blocked_apoptosis_watchdog_triggered":
        errors.append("v2.8d aggregate result must be blocked_apoptosis_watchdog_triggered")
    if campaign_results.get("scoreable_episode_count") != 0:
        errors.append("v2.8d must have zero scoreable episodes")
    if campaign_results.get("apoptosis_watchdog_triggered_count") != 3:
        errors.append("v2.8d must record three apoptosis watchdog triggers")
    if campaign_results.get("full_scoring_allowed") is not False or campaign_results.get("controllergate_full_scoring") != "NOT_RUN":
        errors.append("full scoring must remain NOT_RUN / disallowed")
    if campaign_results.get("self_maintaining_software_demonstrated") is not False:
        errors.append("self-maintaining software must remain not demonstrated")
    if aggregate.get("limited_bugsinpy_real_bug_memory_lift_criteria_met") is not False:
        errors.append("limited BugsInPy memory lift must remain not demonstrated")
    if RUNNER.exists() and "shutil.copytree(" in RUNNER.read_text(encoding="utf-8"):
        errors.append("runner must not contain legacy shutil.copytree repair workspace path")
    errors.extend(verify_manifest(OUTPUT_DIR))
    errors.extend(
        require_text(
            SUMMARY,
            [
                "v2.8d BugsInPy Git-Workspace Repair Comparison",
                "This is no longer a checkout/runtime acquisition failure.",
                "no-op/flatline behavior is correctly quarantined rather than scored",
                "Full scoring remains disallowed.",
                "Memory lift and self-maintaining software remain undemonstrated.",
            ],
        )
    )
    if errors:
        print("v2.8d BugsInPy git-workspace repair comparison audit: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("v2.8d BugsInPy git-workspace repair comparison audit: PASS")
    print("executed episodes: 3")
    print("pre-repair replay gates passed: 3")
    print("scoreable episodes: 0")
    print("aggregate: blocked_apoptosis_watchdog_triggered")
    print("full scoring allowed: false")
    print("self-maintaining software demonstrated: false")
    return 0


if __name__ == "__main__":
    sys.exit(main())
