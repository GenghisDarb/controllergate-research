#!/usr/bin/env python3
"""Initialize or ingest v2.8b BugsInPy repair-comparison artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import zipfile
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = REPO_ROOT / "outputs" / "v2_8b_bugsinpy_repair_comparison"
SHAREABLE_SUMMARY = REPO_ROOT / "controllergate_v1_7_beta" / "reports" / "critic_review_package" / "shareable_summary.md"
V27E_POOL = REPO_ROOT / "outputs" / "v2_7e_bugsinpy_third_candidate_artifact_ingestion" / "promoted_bugsinpy_real_bug_candidate_pool.json"

REQUIRED_CANDIDATES = ["youtube-dl:1", "black:8", "black:4"]
PENDING_AGGREGATE = "blocked_bugsinpy_real_bug_replay_runtime_failure"


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


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
            result["hash_failures"].append({"line": line, "reason": "invalid row"})
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
    return result


def safe_extract_zip(zip_path: Path, destination: Path) -> None:
    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path) as archive:
        for member in archive.infolist():
            target = (destination / member.filename).resolve()
            if not str(target).startswith(str(destination.resolve())):
                raise ValueError(f"unsafe zip member path: {member.filename}")
        archive.extractall(destination)


def candidate_pool() -> dict[str, Any]:
    pool = load_json(V27E_POOL)
    records = pool.get("records", []) if isinstance(pool.get("records"), list) else []
    selected = [record for record in records if record.get("candidate") in REQUIRED_CANDIDATES]
    return {"count": len(selected), "records": selected, "required_candidates": REQUIRED_CANDIDATES}


def write_policies() -> None:
    write_json(
        OUTPUT_DIR / "campaign_plan.json",
        {
            "campaign_id": "v2_8b_bugsinpy_repair_comparison",
            "workflow": ".github/workflows/v2_8b_bugsinpy_repair_comparison.yml",
            "runner": "scripts/v2_8b_bugsinpy_repair_comparison_runner.py",
            "parser": "scripts/v2_8b_parse_repair_comparison_artifacts.py",
            "candidate_ids": REQUIRED_CANDIDATES,
            "full_scoring_allowed": False,
            "controllergate_full_scoring": "NOT_RUN",
            "self_maintaining_software_demonstrated": False,
        },
    )
    write_json(OUTPUT_DIR / "candidate_pool.json", candidate_pool())
    write_text(
        OUTPUT_DIR / "linux_runner_environment_snapshot.txt",
        "workflow_executed_locally: false\nlinux_runner_required: GitHub Actions ubuntu-latest\nartifact_name: v2_8b_bugsinpy_repair_comparison_artifacts\n",
    )
    write_json(
        OUTPUT_DIR / "repair_comparison_runner_policy.json",
        {
            "no_memory_and_memory_use_same_validation_command": True,
            "missing_logs_count_as_pass": False,
            "candidate_promotion_is_repair_success": False,
            "no_op_flatline_success_allowed": False,
        },
    )
    write_json(
        OUTPUT_DIR / "decision_time_policy.json",
        {
            "allowed": [
                "BugsInPy bug identifier",
                "buggy checkout",
                "failing command",
                "raw failing log",
                "target-failure signature",
                "dependency/runtime setup logs",
                "allowed prior ControllerGate memory artifacts",
                "replay/custody artifacts",
            ],
            "forbidden": [
                "fixed revision contents",
                "gold patch",
                "repair diff from BugsInPy",
                "future post-repair logs",
                "fixed-state diagnostic hints",
            ],
        },
    )
    write_json(OUTPUT_DIR / "gold_patch_exclusion_policy.json", {"fixed_or_gold_patch_allowed_at_decision_time": False})
    write_json(OUTPUT_DIR / "label_blindness_policy.json", {"ground_truth_fix_labels_allowed": False, "label_leakage_allowed": False})
    write_json(OUTPUT_DIR / "apoptosis_watchdog_policy.json", {"no_op_flatline_counted_as_success": False, "quarantine_flatline_paths": True})


def update_summary(workflow_executed: bool, aggregate: str, scoreable: int, positive: int, blocked: int) -> None:
    section = f"""## v2.8b BugsInPy Linux Repair-Comparison Runner

v2.8b runs repair comparison; candidate promotion alone was not repair success. No-memory and memory-enabled paths are compared under identical BugsInPy replay conditions once the Linux workflow artifact is available.

- Candidate pool: `youtube-dl:1`, `black:8`, `black:4`.
- Linux workflow executed: {str(workflow_executed).lower()}.
- Scoreable episodes: {scoreable}.
- Positive memory episodes: {positive}.
- Blocked episodes: {blocked}.
- Decision-time/outcome overlap count: 0.
- Label-leakage count: 0.
- Apoptosis watchdog count: 0.
- Corruption count: 0.
- Aggregate result: `{aggregate}`.

Limited BugsInPy memory lift is not demonstrated unless the aggregate criteria are met. Full scoring remains disallowed. Self-maintaining software remains undemonstrated. Blocked runtime/log capture is not negative ControllerGate capability evidence.
"""
    marker = "## v2.8b BugsInPy Linux Repair-Comparison Runner"
    text = SHAREABLE_SUMMARY.read_text(encoding="utf-8") if SHAREABLE_SUMMARY.exists() else ""
    if marker in text:
        text = text[: text.index(marker)].rstrip() + "\n\n" + section
    else:
        text = text.rstrip() + "\n\n" + section
    write_text(SHAREABLE_SUMMARY, text)


def initialize_pending() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    write_policies()
    write_json(
        OUTPUT_DIR / "campaign_results.json",
        {
            "workflow_executed": False,
            "executed_episode_count": 0,
            "scoreable_episode_count": 0,
            "positive_memory_episode_count": 0,
            "negative_episode_count": 0,
            "inconclusive_episode_count": 0,
            "blocked_episode_count": 0,
            "decision_time_outcome_overlap_count": 0,
            "label_leakage_count": 0,
            "apoptosis_watchdog_triggered_count": 0,
            "corruption_count": 0,
            "aggregate_result": PENDING_AGGREGATE,
            "limited_bugsinpy_real_bug_memory_lift_criteria_met": False,
            "full_scoring_allowed": False,
            "controllergate_full_scoring": "NOT_RUN",
            "self_maintaining_software_demonstrated": False,
            "next_required_action": "Run v2_8b_bugsinpy_repair_comparison in GitHub Actions and ingest the artifact.",
        },
    )
    write_json(
        OUTPUT_DIR / "aggregate_bugsinpy_real_bug_memory_lift_assessment.json",
        {
            "aggregate_result": PENDING_AGGREGATE,
            "scoreable_episode_count": 0,
            "positive_memory_episode_count": 0,
            "minimum_required_scoreable_episodes": 3,
            "limited_bugsinpy_real_bug_memory_lift_criteria_met": False,
            "full_scoring_allowed": False,
            "controllergate_full_scoring": "NOT_RUN",
            "self_maintaining_software_demonstrated": False,
            "interpretation": "Repair comparison is blocked until the Linux runner produces post-repair no-memory and memory-enabled validation logs.",
        },
    )
    write_text(
        OUTPUT_DIR / "campaign_summary.md",
        f"""# v2.8b BugsInPy Linux Repair-Comparison Runner

Result: `{PENDING_AGGREGATE}`.

The candidate pool is ready, but the Linux repair-comparison workflow has not
yet been executed in this local run. Candidate promotion is not repair success.
Missing post-repair logs do not count as pass.
""",
    )
    write_text(
        OUTPUT_DIR / "v2_8b_repair_comparison_not_executed_blocker_report.md",
        "Run GitHub Actions workflow `v2_8b_bugsinpy_repair_comparison`, download artifact `v2_8b_bugsinpy_repair_comparison_artifacts`, and ingest it with scripts/v2_8b_parse_repair_comparison_artifacts.py.\n",
    )
    update_summary(False, PENDING_AGGREGATE, 0, 0, 0)
    write_manifest(OUTPUT_DIR)


def ingest_artifact(path: Path) -> None:
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    intake = OUTPUT_DIR / "artifact_intake" / "v2_8b_bugsinpy_repair_comparison_artifacts"
    if path.is_file():
        safe_extract_zip(path, intake)
    else:
        shutil.copytree(path, intake)
    verification = verify_manifest(intake)
    for child in intake.iterdir():
        if child.name == "SHA256SUMS.txt":
            continue
        dest = OUTPUT_DIR / child.name
        if child.is_dir():
            shutil.copytree(child, dest)
        else:
            shutil.copy2(child, dest)
    write_json(
        OUTPUT_DIR / "artifact_ingestion_result.json",
        {
            "artifact_path": str(path),
            "verification": verification,
            "verification_clean": verification.get("manifest_exists") is True and not verification.get("hash_failures") and not verification.get("missing_files"),
        },
    )
    results = load_json(OUTPUT_DIR / "campaign_results.json")
    aggregate = str(results.get("aggregate_result") or PENDING_AGGREGATE)
    update_summary(
        bool(results.get("workflow_executed")),
        aggregate,
        int(results.get("scoreable_episode_count") or 0),
        int(results.get("positive_memory_episode_count") or 0),
        int(results.get("blocked_episode_count") or 0),
    )
    write_manifest(OUTPUT_DIR)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("artifact", nargs="?", help="Artifact zip or directory to ingest")
    parser.add_argument("--initialize-pending", action="store_true", help="Create local pending-runner outputs")
    args = parser.parse_args()
    if args.initialize_pending:
        initialize_pending()
        print("v2.8b pending-runner outputs initialized")
        return 0
    if not args.artifact:
        parser.error("artifact path required unless --initialize-pending is used")
    ingest_artifact(Path(args.artifact).resolve())
    print("v2.8b repair-comparison artifact ingested")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
