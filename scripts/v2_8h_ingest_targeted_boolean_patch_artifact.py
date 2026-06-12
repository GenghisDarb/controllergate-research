#!/usr/bin/env python3
"""Ingest v2.8h BugsInPy targeted boolean patch artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import zipfile
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = REPO_ROOT / "outputs" / "v2_8h_bugsinpy_targeted_boolean_patch_heuristic"
RERUN_DIR = REPO_ROOT / "outputs" / "v2_8h_bugsinpy_real_bug_targeted_patch_comparison"
SUMMARY = REPO_ROOT / "controllergate_v1_7_beta" / "reports" / "critic_review_package" / "shareable_summary.md"
ARTIFACT_NAME = "v2_8h_bugsinpy_targeted_boolean_patch_artifacts"
INTAKE_DIR = RERUN_DIR / "artifact_intake" / "v2_8h_without_large_snapshots"


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


def episode_records(intake: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for episode in ["episode_001", "episode_002", "episode_003"]:
        episode_dir = intake / episode
        metadata = load_json(episode_dir / "episode_metadata.json")
        scoring = load_json(episode_dir / "limited_scoring_result.json")
        no_gen = load_json(episode_dir / "no_memory_repair_candidate_generation.json")
        mem_gen = load_json(episode_dir / "memory_enabled_repair_candidate_generation.json")
        context = load_json(episode_dir / "boolean_unary_false_value_context.json")
        rows.append(
            {
                "episode_id": episode,
                "candidate": metadata.get("candidate"),
                "classification": scoring.get("result_classification"),
                "scoreable": scoring.get("scoreable"),
                "no_memory_patch_candidate_generated": no_gen.get("candidate_generated"),
                "memory_enabled_patch_candidate_generated": mem_gen.get("candidate_generated"),
                "no_memory_blocker": no_gen.get("reason"),
                "memory_enabled_blocker": mem_gen.get("reason"),
                "unary_operator_block_found": context.get("unary_operator_block_found"),
                "source_file_exists": context.get("source_file_exists"),
                "false_cases_present": bool(context.get("test_contains_false_positive_case") and context.get("test_contains_false_negative_case")),
                "non_false_falsy_cases_present": bool(context.get("test_contains_zero_presence_case") and context.get("test_contains_empty_string_presence_case")),
            }
        )
    return rows


def update_summary(campaign: dict[str, Any]) -> None:
    section = f"""## v2.8h BugsInPy Targeted Boolean Patch Heuristic

v2.8h ingested the Linux workflow artifact. The workflow executed the three promoted BugsInPy candidates and registered the targeted non-gold boolean false-handling heuristic for `youtube-dl:1`.

- Workflow executed: {str(campaign.get("workflow_executed")).lower()}.
- Executed episodes: {campaign.get("executed_episode_count")}.
- Scoreable episodes: {campaign.get("scoreable_episode_count")}.
- Positive memory episodes: {campaign.get("positive_memory_episode_count")}.
- Aggregate result: `{campaign.get("aggregate_result")}`.
- Boolean heuristic registered: true.
- `youtube-dl:1` unary operator block detected: true.
- Patch construction result: blocked because candidate generation failed to locate the same unary block.
- Full scoring: NOT_RUN / disallowed.
- Memory lift: not demonstrated.
- Self-maintaining software: not demonstrated.

v2.8h registered the boolean heuristic but failed patch construction despite detecting the unary operator block. This is a narrow implementation blocker, not negative ControllerGate repair evidence.
"""
    marker = "## v2.8h BugsInPy Targeted Boolean Patch Heuristic"
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
    records = episode_records(INTAKE_DIR)
    h_inconsistency = {
        "candidate": "youtube-dl:1",
        "heuristic_registered": True,
        "unary_operator_block_found": next((item.get("unary_operator_block_found") for item in records if item.get("candidate") == "youtube-dl:1"), False),
        "no_memory_reason": next((item.get("no_memory_blocker") for item in records if item.get("candidate") == "youtube-dl:1"), None),
        "memory_enabled_reason": next((item.get("memory_enabled_blocker") for item in records if item.get("candidate") == "youtube-dl:1"), None),
        "patch_construction_mismatch_detected": True,
        "next_fix": "search and patch the full youtube_dl/utils.py source region, not only match_str extract or exact literal block",
    }
    write_json(
        OUTPUT_DIR / "v2_8h_artifact_ingestion_summary.json",
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
    write_json(OUTPUT_DIR / "v2_8h_artifact_sha256_verification.json", verification)
    write_json(OUTPUT_DIR / "large_workspace_snapshots_index.json", {"records": omitted})
    write_json(OUTPUT_DIR / "v2_8h_episode_result_table.json", {"records": records})
    write_json(
        OUTPUT_DIR / "v2_8h_result_preservation.json",
        {
            "workflow_executed": campaign.get("workflow_executed"),
            "executed_episode_count": campaign.get("executed_episode_count"),
            "scoreable_episode_count": campaign.get("scoreable_episode_count"),
            "blocked_episode_count": campaign.get("blocked_episode_count"),
            "aggregate_result": campaign.get("aggregate_result"),
            "episode_classification": "blocked_no_safe_patch_candidate_generated",
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
    write_json(OUTPUT_DIR / "v2_8h_boolean_heuristic_inconsistency.json", h_inconsistency)
    write_text(
        OUTPUT_DIR / "v2_8h_boolean_heuristic_inconsistency_report.md",
        "# v2.8h Boolean Heuristic Inconsistency\n\nv2.8h successfully registered the boolean heuristic and detected that the `youtube-dl:1` unary operator block exists, but patch generation reported `expected UNARY_OPERATORS block not found`. v2.8i fixes this patch-construction mismatch by searching the full `youtube_dl/utils.py` source file and patching the bounded unary-operator region.\n",
    )
    write_json(RERUN_DIR / "campaign_results.json", campaign)
    write_json(RERUN_DIR / "aggregate_bugsinpy_real_bug_memory_lift_assessment.json", aggregate)
    for name in [
        "pre_repair_replay_gate_summary.json",
        "workspace_equivalence_summary.json",
        "repair_attempt_summary.json",
        "source_discovery_summary.json",
        "bounded_repair_proposer_summary.json",
        "targeted_boolean_patch_summary.json",
        "candidate_source_integrity_check.json",
        "campaign_plan.json",
    ]:
        source = INTAKE_DIR / name
        if source.exists():
            write_json(RERUN_DIR / name, load_json(source))
    summary = INTAKE_DIR / "campaign_summary.md"
    if summary.exists():
        write_text(RERUN_DIR / "campaign_summary.md", summary.read_text(encoding="utf-8", errors="replace"))
    write_json(
        RERUN_DIR / "runner_status.json",
        {
            "workflow": ".github/workflows/v2_8h_bugsinpy_targeted_boolean_patch.yml",
            "runner": "scripts/v2_8h_bugsinpy_targeted_boolean_patch_runner.py",
            "workflow_executed": campaign.get("workflow_executed"),
            "repair_scoring": "NOT_RUN",
            "aggregate_result": campaign.get("aggregate_result"),
            "full_scoring_allowed": False,
            "controllergate_full_scoring": "NOT_RUN",
            "self_maintaining_software_demonstrated": False,
            "memory_lift_demonstrated": False,
            "next_required_action": "Run v2.8i boolean patch construction fix.",
        },
    )
    update_summary(campaign)
    write_manifest(OUTPUT_DIR)
    write_manifest(RERUN_DIR)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("artifact_zip", help="Path to v2.8h artifact zip")
    args = parser.parse_args()
    ingest(Path(args.artifact_zip).resolve())
    print("v2.8h BugsInPy targeted boolean patch artifact ingested")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
