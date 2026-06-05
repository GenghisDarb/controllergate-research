#!/usr/bin/env python3
"""Ingest v2.7 BugsInPy target replay recovery artifacts.

This parser preserves fresh GitHub Actions logs, updates the v2.7 promotion
pool, and keeps v2.8 repair scoring blocked unless at least three BugsInPy
candidates are target-failure matched. Dependency/import/runtime failures do
not count as target bug replay.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = REPO_ROOT / "outputs" / "v2_7_bugsinpy_target_replay_promotion_recovery"
V25_PARSED = REPO_ROOT / "outputs" / "v2_5_bugsinpy_runtime_runner" / "parsed_runtime_artifact_summary.json"
SHAREABLE_SUMMARY = REPO_ROOT / "controllergate_v1_7_beta" / "reports" / "critic_review_package" / "shareable_summary.md"

PHASE_A_DIRS = ["black_2_dependency_rerun", "black_8_dependency_rerun"]


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def sha_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_manifest(directory: Path) -> None:
    paths = sorted(
        [path for path in directory.rglob("*") if path.is_file() and path.name != "SHA256SUMS.txt" and path.suffix.lower() != ".zip"],
        key=lambda path: str(path.relative_to(directory)).replace("\\", "/"),
    )
    lines = [f"{sha_file(path)}  {str(path.relative_to(directory)).replace(chr(92), '/')}" for path in paths]
    write_text(directory / "SHA256SUMS.txt", "\n".join(lines) + "\n")


def copy_artifact_dirs(artifact_dir: Path) -> list[Path]:
    copied: list[Path] = []
    for child in sorted(path for path in artifact_dir.iterdir() if path.is_dir()):
        if not (child / "replay_feasibility_result.json").exists():
            continue
        dest = OUTPUT_DIR / child.name
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(child, dest)
        copied.append(dest)
    return copied


def read_candidate_record(directory: Path) -> dict[str, Any]:
    metadata = load_json(directory / "candidate_metadata.json")
    feasibility = load_json(directory / "replay_feasibility_result.json")
    match = load_json(directory / "target_failure_match_check.json")
    project = metadata.get("project") or feasibility.get("project") or match.get("project")
    bug_id = metadata.get("bug_id") or feasibility.get("bug_id") or match.get("bug_id")
    status = match.get("promotion_status") or feasibility.get("promotion_status") or "still_needs_manual_review"
    target_matched = match.get("target_failure_matched") is True
    dependency_blocked = match.get("dependency_or_import_failure_detected") is True
    promoted = (
        status == "promoted_ready_for_v2_7_bugsinpy_real_bug"
        and target_matched
        and not dependency_blocked
    )
    final_status = "promoted_ready_for_v2_7_bugsinpy_real_bug" if promoted else status
    if promoted is False and str(final_status).startswith("promoted"):
        final_status = "blocked_target_failure_not_reproduced"
    match["dependency_or_import_failure_counts_as_target_replay"] = False
    match["promotion_status"] = final_status
    match["target_failure_matched"] = promoted
    write_json(directory / "target_failure_match_check.json", match)
    write_manifest(directory)
    return {
        "candidate": f"{project}:{bug_id}",
        "project": project,
        "bug_id": bug_id,
        "directory": directory.name,
        "promotion_status": final_status,
        "target_failure_matched": promoted,
        "artifact_target_failure_matched": target_matched,
        "dependency_or_import_failure_detected": dependency_blocked,
        "target_failure_match_reason": match.get("target_failure_match_reason"),
        "failure_signature": (directory / "failure_signature.txt").read_text(encoding="utf-8", errors="replace").strip()
        if (directory / "failure_signature.txt").exists()
        else None,
        "fixed_or_gold_patch_used_at_decision_time": feasibility.get("fixed_or_gold_patch_used_at_decision_time") is True,
        "test_returncode": match.get("test_returncode"),
    }


def existing_promoted_records() -> list[dict[str, Any]]:
    parsed = load_json(V25_PARSED)
    records = parsed.get("records", []) if isinstance(parsed.get("records"), list) else []
    return [
        record
        for record in records
        if record.get("promotion_status") == "promoted_ready_for_v2_5_bugsinpy_real_bug"
        and record.get("target_failure_matched") is True
    ]


def update_shareable_summary(final_count: int, black_records: list[dict[str, Any]], phase_b_count: int) -> None:
    black_lines = "\n".join(
        f"- `{record['candidate']}`: `{record['promotion_status']}`; target matched: `{str(record['target_failure_matched']).lower()}`; reason: {record.get('target_failure_match_reason')}"
        for record in black_records
    )
    section = f"""## v2.7 BugsInPy Recovery Artifact Ingestion

The v2.7 GitHub Actions recovery artifact was ingested.

- Previous target-matched count: 1 (`youtube-dl:1`).
- Phase A Black rerun results:
{black_lines}
- Additional BugsInPy candidates attempted by the runner: {phase_b_count}.
- Final target-matched BugsInPy candidate count: {final_count}.
- v2.8 executed: false.
- Repair scoring: NOT RUN.
- Full scoring: disallowed.
- Memory lift: not demonstrated.
- Self-maintaining software: not demonstrated.

Dependency repair is runtime setup, not code repair. Target-failure matching remains mandatory. Dependency/import/runtime failures do not count as target bug replay. Candidate promotion is not repair success.

Next required action: fix the BugsInPy runner command/runtime path so target tests execute without wrapper contamination, or run a broader BugsInPy expansion that yields at least three target-matched candidates.
"""
    marker = "## v2.7 BugsInPy Recovery Artifact Ingestion"
    if SHAREABLE_SUMMARY.exists():
        text = SHAREABLE_SUMMARY.read_text(encoding="utf-8")
        if marker in text:
            text = text[: text.index(marker)].rstrip() + "\n\n" + section
        else:
            text = text.rstrip() + "\n\n" + section
    else:
        text = section
    write_text(SHAREABLE_SUMMARY, text)


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: v2_7_ingest_bugsinpy_recovery_artifacts.py <artifact_dir>")
        return 2
    artifact_dir = Path(sys.argv[1]).resolve()
    if not artifact_dir.exists():
        print(f"artifact dir not found: {artifact_dir}")
        return 2
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    copied_dirs = copy_artifact_dirs(artifact_dir)
    records = [read_candidate_record(directory) for directory in copied_dirs]
    phase_a_records = [record for record in records if record["directory"] in PHASE_A_DIRS]
    phase_b_records = [record for record in records if record["directory"] not in PHASE_A_DIRS]
    newly_promoted = [record for record in records if record["promotion_status"] == "promoted_ready_for_v2_7_bugsinpy_real_bug" and record["target_failure_matched"] is True]
    previous_promoted = existing_promoted_records()
    final_promoted = previous_promoted + newly_promoted
    final_count = len(final_promoted)
    execute_v2_8 = final_count >= 3
    gate_result = "ready_for_v2_8_limited_bugsinpy_replay_execution" if execute_v2_8 else "insufficient_target_matched_bugsinpy_candidates_for_v2_8"
    write_json(
        OUTPUT_DIR / "runtime_artifact_ingestion_result.json",
        {
            "artifact_dir": str(artifact_dir),
            "artifact_ingested": True,
            "phase_a_candidate_count": len(phase_a_records),
            "phase_b_candidate_count": len(phase_b_records),
            "newly_promoted_count": len(newly_promoted),
            "final_target_matched_candidate_count": final_count,
            "execute_v2_8": execute_v2_8,
            "gate_result": gate_result,
            "full_scoring_allowed": False,
            "controllergate_full_scoring": "NOT_RUN",
            "self_maintaining_software_demonstrated": False,
            "memory_lift_demonstrated": False,
        },
    )
    write_json(
        OUTPUT_DIR / "phase_a_dependency_repair_results.json",
        {
            "phase": "v2.7 Phase A",
            "artifact_ingested": True,
            "results": phase_a_records,
            "newly_promoted_count": sum(1 for record in phase_a_records if record["target_failure_matched"]),
            "interpretation": "Black candidates remain blocked unless target failure matched and dependency/runtime contamination is absent.",
        },
    )
    write_json(
        OUTPUT_DIR / "phase_b_candidate_expansion_results.json",
        {
            "phase": "v2.7 Phase B",
            "artifact_ingested": True,
            "additional_candidates_attempted": len(phase_b_records),
            "additional_candidates_attempted_locally": 0,
            "newly_promoted_count": sum(1 for record in phase_b_records if record["target_failure_matched"]),
            "results": phase_b_records,
        },
    )
    write_json(
        OUTPUT_DIR / "additional_candidate_attempt_matrix.json",
        {
            "attempted_count": len(phase_b_records),
            "bounded_budget": 8,
            "attempts": phase_b_records,
        },
    )
    blocked_records = [record for record in records if record["promotion_status"] != "promoted_ready_for_v2_7_bugsinpy_real_bug"]
    write_json(
        OUTPUT_DIR / "additional_candidate_rejection_table.json",
        {
            "rejected_or_blocked_count": len([record for record in blocked_records if record["directory"] not in PHASE_A_DIRS]),
            "records": [record for record in blocked_records if record["directory"] not in PHASE_A_DIRS],
        },
    )
    write_json(
        OUTPUT_DIR / "promoted_bugsinpy_real_bug_candidate_pool.json",
        {
            "count": final_count,
            "records": final_promoted,
            "source": "corrected v2.5 target-failure-matched pool plus ingested v2.7 recovery artifact",
        },
    )
    write_json(
        OUTPUT_DIR / "blocked_candidate_summary.json",
        {
            "blocked_count": len(blocked_records),
            "records": blocked_records,
            "next_required_source_runtime_action": "Fix BugsInPy runner invocation/runtime contamination or acquire more target-matched BugsInPy candidates.",
        },
    )
    write_json(
        OUTPUT_DIR / "target_failure_matching_summary.json",
        {
            "previous_target_matched_count": len(previous_promoted),
            "phase_a_new_target_matched_count": sum(1 for record in phase_a_records if record["target_failure_matched"]),
            "phase_b_new_target_matched_count": sum(1 for record in phase_b_records if record["target_failure_matched"]),
            "final_target_matched_count": final_count,
            "dependency_import_failures_count_as_target_replay": False,
            "target_failure_matching_mandatory": True,
        },
    )
    write_json(
        OUTPUT_DIR / "v2_8_execution_gate_decision.json",
        {
            "gate": "v2.8 limited BugsInPy real-bug replay execution",
            "target_matched_candidate_count": final_count,
            "minimum_required": 3,
            "execute_v2_8": execute_v2_8,
            "repair_scoring_run": False,
            "gate_result": gate_result,
            "next_required_action": "Do not run v2.8 repair scoring until at least three target-matched candidates exist."
            if not execute_v2_8
            else "Run v2.8 limited BugsInPy real-bug replay execution under the preregistered gate.",
        },
    )
    black_summary = "\n".join(
        f"- `{record['candidate']}`: `{record['promotion_status']}`; target matched: `{str(record['target_failure_matched']).lower()}`; reason: {record.get('target_failure_match_reason')}"
        for record in phase_a_records
    )
    write_text(
        OUTPUT_DIR / "campaign_summary.md",
        f"""# v2.7/v2.8 BugsInPy Target-Replay Recovery and Limited Replay Campaign

Result: `{gate_result}`.

## Artifact Ingestion

The v2.7 GitHub Actions recovery artifact was ingested from:

`{artifact_dir}`

## Phase A

{black_summary}

## Phase B

Additional BugsInPy candidates attempted by the runner: {len(phase_b_records)}.
New target-matched candidates from expansion: {sum(1 for record in phase_b_records if record['target_failure_matched'])}.

## Phase C

Final target-matched BugsInPy candidate count: {final_count}.

## Phase D

v2.8 limited replay execution did not run.
v2.8 executed: {str(execute_v2_8).lower()}.
Repair scoring remains NOT RUN. Full scoring remains disallowed. Memory lift is not demonstrated. Self-maintaining software is not demonstrated.

Dependency repair is runtime setup, not code repair. Target-failure matching remains mandatory. Dependency/import/runtime failures do not count as target bug replay.
""",
    )
    update_shareable_summary(final_count, phase_a_records, len(phase_b_records))
    write_manifest(OUTPUT_DIR)
    print("v2.7 BugsInPy recovery artifact ingested")
    print(f"newly promoted candidates: {len(newly_promoted)}")
    print(f"final target-matched candidates: {final_count}")
    print(f"v2.8 execute: {execute_v2_8}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
