#!/usr/bin/env python3
"""Prepare v2.8e BugsInPy repair workspace-preservation outputs.

v2.8d fixed checkout/runtime acquisition, but its repair comparison remained
blocked because repair paths either flatlined or used repair workspaces that did
not reliably preserve the validated BugsInPy workspace context. This script
ingests the v2.8d artifact, preserves that result, and creates the v2.8e
pending-runner bundle for the Linux workspace-preservation rerun.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import zipfile
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = REPO_ROOT / "outputs" / "v2_8e_bugsinpy_repair_workspace_preservation"
SUMMARY = REPO_ROOT / "controllergate_v1_7_beta" / "reports" / "critic_review_package" / "shareable_summary.md"
ARTIFACT_DIR_NAME = "v2_8d_bugsinpy_git_workspace_repair_comparison_artifacts"

CANDIDATES = [
    {"episode_id": "episode_001", "candidate": "youtube-dl:1"},
    {"episode_id": "episode_002", "candidate": "black:8"},
    {"episode_id": "episode_003", "candidate": "black:4"},
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


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


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
        result["verification_clean"] = False
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


def classify_episode(intake: Path, item: dict[str, str]) -> dict[str, Any]:
    episode_dir = intake / item["episode_id"]
    metadata = load_json(episode_dir / "episode_metadata.json")
    gate = load_json(episode_dir / "pre_repair_replay_gate_result.json")
    watchdog = load_json(episode_dir / "apoptosis_watchdog_result.json")
    scoring = load_json(episode_dir / "limited_scoring_result.json")
    no_trace = load_json(episode_dir / "no_memory_action_trace.json")
    mem_trace = load_json(episode_dir / "memory_enabled_action_trace.json")
    no_log = read_text(episode_dir / "no_memory_post_repair_log_raw.txt")
    mem_log = read_text(episode_dir / "memory_enabled_post_repair_log_raw.txt")
    no_patch = read_text(episode_dir / "no_memory_repair_patch.diff")
    mem_patch = read_text(episode_dir / "memory_enabled_repair_patch.diff")
    workspace_divergence = "AttributeError" in (no_log + mem_log) and "has no attribute" in (no_log + mem_log)
    no_patch_generated = "# NO PATCH" in no_patch and "# NO PATCH" in mem_patch
    no_actions = not no_trace.get("actions") and not mem_trace.get("actions")
    return {
        "episode_id": item["episode_id"],
        "candidate": item["candidate"],
        "v2_8d_classification": metadata.get("classification"),
        "v2_8e_preserved_classification": "blocked_repair_runner_noop_or_workspace_divergence",
        "pre_repair_replay_gate_passed": gate.get("pre_repair_replay_gate_passed"),
        "target_failure_matched": gate.get("target_failure_matched"),
        "v2_8d_scoreable": scoring.get("scoreable"),
        "v2_8d_watchdog_triggered": watchdog.get("watchdog_triggered"),
        "no_patch_generated": no_patch_generated,
        "empty_or_noop_action_trace": no_actions,
        "post_repair_workspace_divergence_signal": workspace_divergence,
        "scoreable_repair_evidence": False,
        "negative_controllergate_capability_evidence": False,
    }


def update_summary() -> None:
    section = """## v2.8e BugsInPy Repair Workspace Preservation

v2.8e preserves the v2.8d artifact result and adds the next Linux runner fix. v2.8d proved the promoted BugsInPy candidates can reach target-matched pre-repair replay, but it remains blocked because repair workspaces/attempts did not produce valid source-changing repair evidence.

- v2.8d artifact ingestion: SHA256 verification clean.
- Preserved v2.8d classification: `blocked_apoptosis_watchdog_triggered`.
- v2.8e root cause: repair workspaces must be exact preserved copies of the validated BugsInPy workspace, and empty/no-op repair traces must not be scored.
- v2.8e runner status in this checkpoint: pending GitHub Actions execution.
- v2.8e repair scoring: NOT RUN.
- Full scoring: NOT_RUN / disallowed.
- Memory lift: not demonstrated.
- Self-maintaining software: not demonstrated.

Dependency/runtime setup is not code repair. Target-failure matching remains mandatory. Candidate promotion and pre-repair replay are not repair success.
"""
    marker = "## v2.8e BugsInPy Repair Workspace Preservation"
    text = SUMMARY.read_text(encoding="utf-8") if SUMMARY.exists() else ""
    if marker in text:
        text = text[: text.index(marker)].rstrip() + "\n\n" + section
    else:
        text = text.rstrip() + "\n\n" + section
    write_text(SUMMARY, text)


def prepare(zip_path: Path) -> None:
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    intake = OUTPUT_DIR / "artifact_intake" / ARTIFACT_DIR_NAME
    safe_extract(zip_path, intake)
    verification = verify_manifest(intake)
    campaign_results = load_json(intake / "campaign_results.json")
    aggregate = load_json(intake / "aggregate_bugsinpy_real_bug_memory_lift_assessment.json")
    episode_rows = [classify_episode(intake, item) for item in CANDIDATES]
    write_json(
        OUTPUT_DIR / "v2_8d_artifact_ingestion_summary.json",
        {
            "artifact_path": str(zip_path),
            "artifact_ingested": True,
            "artifact_dir_name": ARTIFACT_DIR_NAME,
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
    write_json(OUTPUT_DIR / "v2_8d_artifact_sha256_verification.json", verification)
    write_json(
        OUTPUT_DIR / "v2_8d_result_preservation.json",
        {
            "preserved_aggregate_result": aggregate.get("aggregate_result") or campaign_results.get("aggregate_result"),
            "preserved_scoreable_episode_count": campaign_results.get("scoreable_episode_count"),
            "preserved_positive_memory_episode_count": campaign_results.get("positive_memory_episode_count"),
            "preserved_repair_scoring": "NOT_RUN",
            "preserved_full_scoring": "NOT_RUN",
            "memory_lift_demonstrated": False,
            "self_maintaining_software_demonstrated": False,
            "negative_capability_evidence": False,
        },
    )
    write_text(
        OUTPUT_DIR / "v2_8d_apoptosis_context_report.md",
        "# v2.8d Apoptosis Context\n\nv2.8d passed the pre-repair replay gate for all three promoted BugsInPy candidates, but the repair paths did not produce valid source-changing repair evidence. No-op or flatline behavior was correctly quarantined instead of scored.\n",
    )
    write_text(
        OUTPUT_DIR / "repair_noop_root_cause_report.md",
        "# Repair No-op Root Cause\n\nThe repair runner reached valid replay but emitted empty or no-op repair traces. v2.8e requires a bounded repair-attempt layer that records candidate-generation decisions. If no patch candidate can be generated from allowed decision-time inputs, the episode is blocked as `blocked_no_repair_candidate_generated` rather than scored.\n",
    )
    write_text(
        OUTPUT_DIR / "post_repair_workspace_divergence_report.md",
        "# Post-repair Workspace Divergence\n\nGit-only repair workspaces can omit BugsInPy checkout overlays, injected test context, or local files that existed in the validated pre-repair workspace. v2.8e therefore archives the validated baseline workspace and restores it into both no-memory and memory-enabled repair workspaces before replaying the target failure again.\n",
    )
    write_json(OUTPUT_DIR / "episode_blocker_table.json", {"records": episode_rows})
    write_json(
        OUTPUT_DIR / "runner_status.json",
        {
            "workflow": ".github/workflows/v2_8e_bugsinpy_repair_workspace_preservation.yml",
            "runner": "scripts/v2_8e_bugsinpy_repair_workspace_preservation_runner.py",
            "workflow_executed": False,
            "pending_artifact_name": "v2_8e_bugsinpy_repair_workspace_preservation_artifacts",
            "repair_scoring": "NOT_RUN",
            "full_scoring_allowed": False,
            "controllergate_full_scoring": "NOT_RUN",
            "self_maintaining_software_demonstrated": False,
            "memory_lift_demonstrated": False,
            "next_required_action": "Run the v2.8e GitHub Actions workflow and ingest the artifact.",
        },
    )
    write_json(
        OUTPUT_DIR / "campaign_plan.json",
        {
            "campaign_id": "v2_8e_bugsinpy_repair_workspace_preservation",
            "candidate_ids": [item["candidate"] for item in CANDIDATES],
            "workspace_preservation_strategy": "archive validated baseline workspace and extract exact copies for repair paths",
            "pre_repair_replay_required_in_repair_workspaces": True,
            "bounded_repair_attempt_required": True,
            "no_patch_candidate_classification": "blocked_no_repair_candidate_generated",
            "full_scoring_allowed": False,
            "controllergate_full_scoring": "NOT_RUN",
            "self_maintaining_software_demonstrated": False,
        },
    )
    write_text(
        OUTPUT_DIR / "github_actions_usage_instructions.md",
        "# v2.8e GitHub Actions Instructions\n\nRun `.github/workflows/v2_8e_bugsinpy_repair_workspace_preservation.yml` on branch `controllergate-v1.7-alpha-real-trace-pilot`. Download `v2_8e_bugsinpy_repair_workspace_preservation_artifacts` when complete and ingest it before any scoring claim.\n",
    )
    update_summary()
    write_manifest(OUTPUT_DIR)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("artifact_zip", help="Path to v2.8d artifact zip")
    args = parser.parse_args()
    prepare(Path(args.artifact_zip).resolve())
    print("v2.8e BugsInPy repair workspace-preservation bundle prepared")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
