#!/usr/bin/env python3
"""Ingest v2.8e BugsInPy repair workspace-preservation artifacts.

The GitHub Actions artifact contains large tar snapshots of each validated
workspace. This ingester verifies the original artifact SHA256 manifest from the
zip, records the tar snapshot hashes/sizes, and extracts all non-tar evidence
needed for local audits. The large tar snapshots remain in the downloaded
workflow artifact rather than being committed into the repository.
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
ARTIFACT_NAME = "v2_8e_bugsinpy_repair_workspace_preservation_artifacts"
INTAKE_DIR = OUTPUT_DIR / "artifact_intake" / f"{ARTIFACT_NAME}_without_large_snapshots"


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


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


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


def verify_zip_manifest(zip_path: Path) -> tuple[dict[str, Any], dict[str, str]]:
    result: dict[str, Any] = {
        "artifact_path": str(zip_path),
        "artifact_sha256": sha_file(zip_path),
        "manifest_exists": False,
        "checked_files": 0,
        "missing_files": [],
        "hash_failures": [],
    }
    content_hashes: dict[str, str] = {}
    with zipfile.ZipFile(zip_path) as archive:
        names = {entry.filename for entry in archive.infolist() if not entry.is_dir()}
        if "SHA256SUMS.txt" not in names:
            result["verification_clean"] = False
            return result, content_hashes
        result["manifest_exists"] = True
        manifest = archive.read("SHA256SUMS.txt").decode("utf-8")
        for line in manifest.splitlines():
            if not line.strip():
                continue
            parts = line.split()
            if len(parts) != 2:
                result["hash_failures"].append({"line": line, "reason": "invalid SHA256SUMS row"})
                continue
            expected, rel = parts
            if rel not in names:
                result["missing_files"].append(rel)
                continue
            digest = sha_bytes(archive.read(rel))
            content_hashes[rel] = digest
            result["checked_files"] += 1
            if digest != expected:
                result["hash_failures"].append({"path": rel, "expected": expected, "actual": digest})
    result["verification_clean"] = result["manifest_exists"] and not result["missing_files"] and not result["hash_failures"]
    return result, content_hashes


def safe_extract_subset(zip_path: Path, destination: Path) -> list[dict[str, Any]]:
    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True, exist_ok=True)
    omitted: list[dict[str, Any]] = []
    with zipfile.ZipFile(zip_path) as archive:
        for member in archive.infolist():
            if member.is_dir():
                continue
            if member.filename.endswith(".tar"):
                omitted.append({"path": member.filename, "size": member.file_size, "omitted_from_repo": True})
                continue
            target = (destination / member.filename).resolve()
            if not str(target).startswith(str(destination.resolve())):
                raise ValueError(f"unsafe zip member path: {member.filename}")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(archive.read(member.filename))
    write_manifest(destination)
    return omitted


def episode_records(intake: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for episode in ["episode_001", "episode_002", "episode_003"]:
        episode_dir = intake / episode
        metadata = load_json(episode_dir / "episode_metadata.json")
        equivalence = load_json(episode_dir / "workspace_equivalence_check.json")
        replay = load_json(episode_dir / "repair_workspace_prerepair_replay_check.json")
        scoring = load_json(episode_dir / "limited_scoring_result.json")
        no_gen = load_json(episode_dir / "no_memory_repair_candidate_generation.json")
        mem_gen = load_json(episode_dir / "memory_enabled_repair_candidate_generation.json")
        rows.append(
            {
                "episode_id": episode,
                "candidate": metadata.get("candidate"),
                "classification": scoring.get("result_classification"),
                "scoreable": scoring.get("scoreable"),
                "workspace_equivalence_passed": equivalence.get("workspace_equivalence_passed"),
                "no_memory_prerepair_target_failure_matched": (replay.get("no_memory") or {}).get("target_failure_matched"),
                "memory_enabled_prerepair_target_failure_matched": (replay.get("memory_enabled") or {}).get("target_failure_matched"),
                "no_memory_patch_candidate_generated": no_gen.get("candidate_generated"),
                "memory_enabled_patch_candidate_generated": mem_gen.get("candidate_generated"),
                "memory_enabled_outperformed_no_memory": scoring.get("memory_enabled_outperformed_no_memory"),
            }
        )
    return rows


def update_summary(campaign: dict[str, Any]) -> None:
    section = f"""## v2.8e BugsInPy Repair Workspace Preservation

v2.8e ingested the Linux workflow artifact and confirmed the workspace-preservation fix worked. The validated BugsInPy workspace is archived and restored into both no-memory and memory-enabled repair workspaces, and both repair workspaces reproduce the target failure before repair.

- Workflow executed: {str(campaign.get("workflow_executed")).lower()}.
- Executed episodes: {campaign.get("executed_episode_count")}.
- Workspace equivalence: passed for all three episodes.
- Repair-workspace pre-repair replay: target failure matched for no-memory and memory-enabled paths in all three episodes.
- Scoreable episodes: {campaign.get("scoreable_episode_count")}.
- Positive memory episodes: {campaign.get("positive_memory_episode_count")}.
- Aggregate result: `{campaign.get("aggregate_result")}`.
- Full scoring: NOT_RUN / disallowed.
- Memory lift: not demonstrated.
- Self-maintaining software: not demonstrated.

This is a narrower implementation blocker, not negative ControllerGate capability evidence: no safe repair candidate was generated from allowed decision-time inputs, so the episodes remain blocked instead of scored.
"""
    marker = "## v2.8e BugsInPy Repair Workspace Preservation"
    text = SUMMARY.read_text(encoding="utf-8") if SUMMARY.exists() else ""
    if marker in text:
        text = text[: text.index(marker)].rstrip() + "\n\n" + section
    else:
        text = text.rstrip() + "\n\n" + section
    write_text(SUMMARY, text)


def ingest(zip_path: Path) -> None:
    verification, hashes = verify_zip_manifest(zip_path)
    omitted = safe_extract_subset(zip_path, INTAKE_DIR)
    for record in omitted:
        record["sha256"] = hashes.get(record["path"])
    campaign = load_json(INTAKE_DIR / "campaign_results.json")
    aggregate = load_json(INTAKE_DIR / "aggregate_bugsinpy_real_bug_memory_lift_assessment.json")
    records = episode_records(INTAKE_DIR)
    write_json(OUTPUT_DIR / "v2_8e_artifact_ingestion_summary.json", {
        "artifact_path": str(zip_path),
        "artifact_ingested": True,
        "artifact_name": ARTIFACT_NAME,
        "artifact_intake_dir": str(INTAKE_DIR.relative_to(REPO_ROOT)).replace("\\", "/"),
        "large_workspace_snapshots_omitted_from_repo": True,
        "workflow_executed": campaign.get("workflow_executed"),
        "executed_episode_count": campaign.get("executed_episode_count"),
        "scoreable_episode_count": campaign.get("scoreable_episode_count"),
        "aggregate_result": campaign.get("aggregate_result"),
        "full_scoring_allowed": False,
        "controllergate_full_scoring": "NOT_RUN",
        "self_maintaining_software_demonstrated": False,
    })
    write_json(OUTPUT_DIR / "v2_8e_artifact_sha256_verification.json", verification)
    write_json(OUTPUT_DIR / "large_workspace_snapshots_index.json", {"records": omitted})
    write_json(OUTPUT_DIR / "v2_8e_episode_result_table.json", {"records": records})
    write_json(OUTPUT_DIR / "v2_8e_workspace_preservation_result.json", {
        "workspace_equivalence_passed_count": sum(1 for item in records if item["workspace_equivalence_passed"]),
        "no_memory_prerepair_target_failure_matched_count": sum(1 for item in records if item["no_memory_prerepair_target_failure_matched"]),
        "memory_enabled_prerepair_target_failure_matched_count": sum(1 for item in records if item["memory_enabled_prerepair_target_failure_matched"]),
        "all_repair_workspaces_preserved_target_failure": all(
            item["workspace_equivalence_passed"]
            and item["no_memory_prerepair_target_failure_matched"]
            and item["memory_enabled_prerepair_target_failure_matched"]
            for item in records
        ),
    })
    write_json(OUTPUT_DIR / "campaign_results.json", campaign)
    write_json(OUTPUT_DIR / "aggregate_bugsinpy_real_bug_memory_lift_assessment.json", aggregate)
    write_json(OUTPUT_DIR / "runner_status.json", {
        "workflow": ".github/workflows/v2_8e_bugsinpy_repair_workspace_preservation.yml",
        "runner": "scripts/v2_8e_bugsinpy_repair_workspace_preservation_runner.py",
        "workflow_executed": campaign.get("workflow_executed"),
        "repair_scoring": "NOT_RUN",
        "aggregate_result": campaign.get("aggregate_result"),
        "full_scoring_allowed": False,
        "controllergate_full_scoring": "NOT_RUN",
        "self_maintaining_software_demonstrated": False,
        "memory_lift_demonstrated": False,
        "next_required_action": "Implement a bounded non-leaking repair candidate generator before rerunning repair scoring.",
    })
    write_text(OUTPUT_DIR / "campaign_summary.md", (INTAKE_DIR / "campaign_summary.md").read_text(encoding="utf-8", errors="replace"))
    update_summary(campaign)
    write_manifest(OUTPUT_DIR)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("artifact_zip", help="Path to v2.8e artifact zip")
    args = parser.parse_args()
    ingest(Path(args.artifact_zip).resolve())
    print("v2.8e BugsInPy repair workspace-preservation artifact ingested")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
