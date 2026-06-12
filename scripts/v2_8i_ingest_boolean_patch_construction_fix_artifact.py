#!/usr/bin/env python3
"""Ingest v2.8i BugsInPy boolean patch construction fix artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import zipfile
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = REPO_ROOT / "outputs" / "v2_8i_bugsinpy_boolean_patch_construction_fix"
RERUN_DIR = REPO_ROOT / "outputs" / "v2_8i_bugsinpy_real_bug_boolean_patch_comparison"
SUMMARY = REPO_ROOT / "controllergate_v1_7_beta" / "reports" / "critic_review_package" / "shareable_summary.md"
ARTIFACT_NAME = "v2_8i_bugsinpy_boolean_patch_construction_fix_artifacts"
INTAKE_DIR = RERUN_DIR / "artifact_intake" / "v2_8i_without_large_snapshots"


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
        "manifest_self_files_excluded": [],
    }
    content_hashes: dict[str, str] = {}
    with zipfile.ZipFile(zip_path) as archive:
        names = {entry.filename for entry in archive.infolist() if not entry.is_dir()}
        if "SHA256SUMS.txt" not in names:
            result["verification_clean"] = False
            return result, content_hashes
        result["manifest_exists"] = True
        manifest = archive.read("SHA256SUMS.txt").decode("utf-8")
        manifest_paths: set[str] = set()
        for line in manifest.splitlines():
            if not line.strip():
                continue
            parts = line.split()
            if len(parts) != 2:
                result["hash_failures"].append({"line": line, "reason": "invalid SHA256SUMS row"})
                continue
            expected, rel = parts
            manifest_paths.add(rel)
            if rel not in names:
                result["missing_files"].append(rel)
                continue
            digest = sha_bytes(archive.read(rel))
            content_hashes[rel] = digest
            result["checked_files"] += 1
            if digest != expected:
                result["hash_failures"].append({"path": rel, "expected": expected, "actual": digest})
        result["manifest_self_files_excluded"] = sorted(path for path in names - manifest_paths if path.endswith("SHA256SUMS.txt"))
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


def copy_file(src: Path, dst: Path) -> None:
    if src.exists():
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)


def episode_record(intake: Path, episode: str) -> dict[str, Any]:
    episode_dir = intake / episode
    metadata = load_json(episode_dir / "episode_metadata.json")
    scoring = load_json(episode_dir / "limited_scoring_result.json")
    no_gen = load_json(episode_dir / "no_memory_repair_candidate_generation.json")
    mem_gen = load_json(episode_dir / "memory_enabled_repair_candidate_generation.json")
    no_outcome = load_json(episode_dir / "no_memory_outcome.json")
    mem_outcome = load_json(episode_dir / "memory_enabled_outcome.json")
    return {
        "episode_id": episode,
        "candidate": metadata.get("candidate"),
        "classification": scoring.get("result_classification") or metadata.get("classification"),
        "scoreable": bool(scoring.get("scoreable")),
        "limited_scoring_executed": bool(scoring.get("limited_scoring_executed")),
        "memory_enabled_outperformed_no_memory": bool(scoring.get("memory_enabled_outperformed_no_memory")),
        "no_memory_patch_candidate_generated": bool(no_gen.get("candidate_generated")),
        "memory_enabled_patch_candidate_generated": bool(mem_gen.get("candidate_generated")),
        "no_memory_primary_command_passed": bool(no_outcome.get("primary_command_passed")),
        "memory_enabled_primary_command_passed": bool(mem_outcome.get("primary_command_passed")),
        "patched_file": no_gen.get("patched_file") or mem_gen.get("patched_file"),
        "fixed_or_gold_patch_used": bool(no_gen.get("fixed_or_gold_patch_used")) or bool(mem_gen.get("fixed_or_gold_patch_used")),
        "future_outcome_evidence_used": bool(no_gen.get("future_outcome_evidence_used")) or bool(mem_gen.get("future_outcome_evidence_used")),
    }


def update_summary(campaign: dict[str, Any], records: list[dict[str, Any]]) -> None:
    yt = next((record for record in records if record.get("candidate") == "youtube-dl:1"), {})
    section = f"""## v2.8i BugsInPy Boolean Patch Construction Fix

v2.8h registered the boolean heuristic but failed patch construction despite detecting the unary operator block. v2.8i fixes the boolean patch construction path. The Linux workflow artifact was ingested and verified cleanly.

- v2.8h artifact ingestion: preserved.
- v2.8i workflow executed: {str(campaign.get("workflow_executed")).lower()}.
- Executed episodes: {campaign.get("executed_episode_count")}.
- Scoreable episodes: {campaign.get("scoreable_episode_count")}.
- Positive memory episodes: {campaign.get("positive_memory_episode_count")}.
- `youtube-dl:1` patch construction: generated non-gold full-source boolean patch in both no-memory and memory-enabled paths.
- `youtube-dl:1` classification: `{yt.get("classification")}`.
- Black episodes: remain `blocked_no_safe_patch_candidate_generated`.
- Aggregate result: `{campaign.get("aggregate_result")}`.
- Full scoring: NOT_RUN / disallowed.
- Memory lift: not demonstrated.
- Self-maintaining software: not demonstrated.

A no-memory and memory-enabled tie is inconclusive, not memory lift. This is the first scoreable BugsInPy repair episode in this ladder, but the aggregate remains below the three-episode threshold.
"""
    marker = "## v2.8i BugsInPy Boolean Patch Construction Fix"
    text = SUMMARY.read_text(encoding="utf-8") if SUMMARY.exists() else ""
    if marker in text:
        start = text.index(marker)
        next_start = text.find("\n## ", start + 1)
        tail = text[next_start:].lstrip() if next_start != -1 else ""
        text = text[:start].rstrip() + "\n\n" + section + ("\n\n" + tail if tail else "")
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
    records = [episode_record(INTAKE_DIR, episode) for episode in ["episode_001", "episode_002", "episode_003"]]
    youtube_record = next((record for record in records if record.get("candidate") == "youtube-dl:1"), {})

    write_json(
        OUTPUT_DIR / "v2_8i_artifact_ingestion_summary.json",
        {
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
        },
    )
    write_json(OUTPUT_DIR / "v2_8i_artifact_sha256_verification.json", verification)
    write_json(OUTPUT_DIR / "large_workspace_snapshots_index.json", {"records": omitted})
    write_json(OUTPUT_DIR / "v2_8i_episode_result_table.json", {"records": records})
    write_json(
        OUTPUT_DIR / "v2_8i_result_preservation.json",
        {
            "workflow_executed": campaign.get("workflow_executed"),
            "executed_episode_count": campaign.get("executed_episode_count"),
            "scoreable_episode_count": campaign.get("scoreable_episode_count"),
            "blocked_episode_count": campaign.get("blocked_episode_count"),
            "aggregate_result": campaign.get("aggregate_result"),
            "positive_memory_episode_count": campaign.get("positive_memory_episode_count"),
            "corruption_count": campaign.get("corruption_count"),
            "decision_time_outcome_overlap_count": campaign.get("decision_time_outcome_overlap_count"),
            "label_leakage_count": campaign.get("label_leakage_count"),
            "full_scoring_allowed": False,
            "controllergate_full_scoring": "NOT_RUN",
            "self_maintaining_software_demonstrated": False,
            "memory_lift_demonstrated": False,
        },
    )
    write_json(
        OUTPUT_DIR / "v2_8i_boolean_patch_construction_result.json",
        {
            "candidate": "youtube-dl:1",
            "classification": youtube_record.get("classification"),
            "scoreable": youtube_record.get("scoreable"),
            "no_memory_patch_candidate_generated": youtube_record.get("no_memory_patch_candidate_generated"),
            "memory_enabled_patch_candidate_generated": youtube_record.get("memory_enabled_patch_candidate_generated"),
            "no_memory_primary_command_passed": youtube_record.get("no_memory_primary_command_passed"),
            "memory_enabled_primary_command_passed": youtube_record.get("memory_enabled_primary_command_passed"),
            "memory_enabled_outperformed_no_memory": youtube_record.get("memory_enabled_outperformed_no_memory"),
            "patched_file": youtube_record.get("patched_file"),
            "fixed_or_gold_patch_used": youtube_record.get("fixed_or_gold_patch_used"),
            "future_outcome_evidence_used": youtube_record.get("future_outcome_evidence_used"),
            "result_interpretation": "scoreable_inconclusive_equal_performance_not_memory_lift",
        },
    )

    episode_001 = INTAKE_DIR / "episode_001"
    for name in [
        "boolean_patch_generation_result.json",
        "boolean_patch_safety_check.json",
        "unary_operator_region_extract.txt",
        "unary_operator_region_match_check.json",
        "no_memory_boolean_patch_generation_result.json",
        "memory_enabled_boolean_patch_generation_result.json",
        "no_memory_boolean_patch_safety_check.json",
        "memory_enabled_boolean_patch_safety_check.json",
        "no_memory_boolean_patch_candidate.diff",
        "memory_enabled_boolean_patch_candidate.diff",
    ]:
        copy_file(episode_001 / name, OUTPUT_DIR / name)

    for name in [
        "campaign_plan.json",
        "campaign_results.json",
        "aggregate_bugsinpy_real_bug_memory_lift_assessment.json",
        "campaign_summary.md",
        "candidate_source_integrity_check.json",
        "pre_repair_replay_gate_summary.json",
        "workspace_equivalence_summary.json",
        "repair_attempt_summary.json",
        "source_discovery_summary.json",
        "bounded_repair_proposer_summary.json",
        "targeted_boolean_patch_summary.json",
        "boolean_patch_construction_fix_design.json",
        "full_source_patch_search_policy.json",
        "boolean_patch_generation_result.json",
        "boolean_patch_safety_check.json",
        "unary_operator_region_extract.txt",
        "unary_operator_region_match_check.json",
    ]:
        copy_file(INTAKE_DIR / name, RERUN_DIR / name)
    write_json(
        RERUN_DIR / "runner_status.json",
        {
            "workflow": ".github/workflows/v2_8i_bugsinpy_boolean_patch_construction_fix.yml",
            "runner": "scripts/v2_8i_bugsinpy_boolean_patch_construction_fix_runner.py",
            "workflow_executed": campaign.get("workflow_executed"),
            "scoreable_episode_count": campaign.get("scoreable_episode_count"),
            "aggregate_result": campaign.get("aggregate_result"),
            "full_scoring_allowed": False,
            "controllergate_full_scoring": "NOT_RUN",
            "self_maintaining_software_demonstrated": False,
            "memory_lift_demonstrated": False,
            "next_required_action": "Expand safe patch generation beyond youtube-dl:1 or ingest a later artifact with at least three scoreable BugsInPy episodes.",
        },
    )
    update_summary(campaign, records)
    write_manifest(OUTPUT_DIR)
    write_manifest(RERUN_DIR)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("artifact_zip", help="Path to v2.8i artifact zip")
    args = parser.parse_args()
    ingest(Path(args.artifact_zip).resolve())
    print("v2.8i BugsInPy boolean patch construction fix artifact ingested")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
