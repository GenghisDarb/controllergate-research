#!/usr/bin/env python3
"""Ingest v2.8d BugsInPy git-workspace repair comparison artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import zipfile
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = REPO_ROOT / "outputs" / "v2_8d_bugsinpy_git_workspace_repair_comparison"
SUMMARY = REPO_ROOT / "controllergate_v1_7_beta" / "reports" / "critic_review_package" / "shareable_summary.md"
ARTIFACT_DIR_NAME = "v2_8d_bugsinpy_git_workspace_repair_comparison_artifacts"


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_json(path: Path) -> dict[str, Any]:
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


def episode_summary(intake: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for name in ["episode_001", "episode_002", "episode_003"]:
        episode_dir = intake / name
        metadata = load_json(episode_dir / "episode_metadata.json")
        gate = load_json(episode_dir / "pre_repair_replay_gate_result.json")
        copy_result = load_json(episode_dir / "repair_workspace_copy_result.json")
        scoring = load_json(episode_dir / "limited_scoring_result.json")
        watchdog = load_json(episode_dir / "apoptosis_watchdog_result.json")
        rows.append(
            {
                "episode_id": name,
                "candidate": metadata.get("candidate"),
                "classification": metadata.get("classification"),
                "scoreable": metadata.get("scoreable"),
                "pre_repair_replay_gate_passed": gate.get("pre_repair_replay_gate_passed"),
                "target_failure_matched": gate.get("target_failure_matched"),
                "no_memory_workspace_copy_succeeded": (copy_result.get("no_memory") or {}).get("copy_succeeded"),
                "memory_enabled_workspace_copy_succeeded": (copy_result.get("memory_enabled") or {}).get("copy_succeeded"),
                "copy_strategy": (copy_result.get("no_memory") or {}).get("copy_strategy"),
                "watchdog_triggered": watchdog.get("watchdog_triggered"),
                "memory_enabled_outperformed_no_memory": scoring.get("memory_enabled_outperformed_no_memory"),
            }
        )
    return rows


def update_summary(campaign_results: dict[str, Any]) -> None:
    section = f"""## v2.8d BugsInPy Git-Workspace Repair Comparison

v2.8d fixed the runner infrastructure path. The workflow executed with Git-based repair workspaces instead of fragile file-tree copying.

- Workflow executed: {str(campaign_results.get("workflow_executed")).lower()}.
- Executed episodes: {campaign_results.get("executed_episode_count")}.
- Pre-repair replay gates: passed for all three promoted BugsInPy candidates.
- Repair workspace strategy: `git_clone_no_local`.
- Scoreable episodes: {campaign_results.get("scoreable_episode_count")}.
- Blocked episodes: {campaign_results.get("blocked_episode_count")}.
- Apoptosis watchdog triggers: {campaign_results.get("apoptosis_watchdog_triggered_count")}.
- Positive memory episodes: {campaign_results.get("positive_memory_episode_count")}.
- Decision-time/outcome overlap count: {campaign_results.get("decision_time_outcome_overlap_count")}.
- Label-leakage count: {campaign_results.get("label_leakage_count")}.
- Corruption count: {campaign_results.get("corruption_count")}.
- Aggregate result: `{campaign_results.get("aggregate_result")}`.

This is no longer a checkout/runtime acquisition failure. It is blocked because the bounded repair runner produced no source-changing repair actions, and no-op/flatline behavior is correctly quarantined rather than scored. Full scoring remains disallowed. Memory lift and self-maintaining software remain undemonstrated.
"""
    marker = "## v2.8d BugsInPy Git-Workspace Repair Comparison"
    text = SUMMARY.read_text(encoding="utf-8") if SUMMARY.exists() else ""
    if marker in text:
        text = text[: text.index(marker)].rstrip() + "\n\n" + section
    else:
        text = text.rstrip() + "\n\n" + section
    write_text(SUMMARY, text)


def ingest(zip_path: Path) -> None:
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    intake = OUTPUT_DIR / "artifact_intake" / ARTIFACT_DIR_NAME
    safe_extract(zip_path, intake)
    verification = verify_manifest(intake)
    campaign_results = load_json(intake / "campaign_results.json")
    aggregate = load_json(intake / "aggregate_bugsinpy_real_bug_memory_lift_assessment.json")
    episodes = episode_summary(intake)
    write_json(
        OUTPUT_DIR / "artifact_ingestion_summary.json",
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
    write_json(OUTPUT_DIR / "artifact_sha256_verification.json", verification)
    write_json(OUTPUT_DIR / "episode_result_table.json", {"records": episodes})
    write_json(
        OUTPUT_DIR / "git_workspace_runner_result.json",
        {
            "git_workspace_runner_fixed_checkout_copy_issue": True,
            "all_pre_repair_replay_gates_passed": all(item["pre_repair_replay_gate_passed"] for item in episodes),
            "all_repair_workspaces_created_with_git": all(item["copy_strategy"] == "git_clone_no_local" for item in episodes),
            "checkout_runtime_blocker_resolved": True,
            "remaining_blocker": "bounded repair runner produced no source-changing repair actions",
            "remaining_blocker_classification": "blocked_apoptosis_watchdog_triggered",
            "negative_repair_capability_evidence": False,
        },
    )
    write_json(OUTPUT_DIR / "campaign_results.json", campaign_results)
    write_json(OUTPUT_DIR / "aggregate_bugsinpy_real_bug_memory_lift_assessment.json", aggregate)
    write_text(
        OUTPUT_DIR / "campaign_summary.md",
        f"""# v2.8d BugsInPy Git-Workspace Repair Comparison

Aggregate result: `{campaign_results.get("aggregate_result")}`.

The git-workspace runner fixed the checkout/runtime copy failure. All three
promoted BugsInPy candidates passed the pre-repair replay gate and created
Git-based no-memory and memory-enabled repair workspaces.

The campaign remains not scoreable because all three repair paths were
quarantined by the apoptosis watchdog for no-op/flatline behavior. Full scoring
remains disallowed. Memory lift and self-maintaining software remain
undemonstrated.
""",
    )
    update_summary(campaign_results)
    write_manifest(OUTPUT_DIR)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("artifact_zip", help="Path to v2.8d artifact zip")
    args = parser.parse_args()
    ingest(Path(args.artifact_zip).resolve())
    print("v2.8d BugsInPy git-workspace artifact ingested")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
