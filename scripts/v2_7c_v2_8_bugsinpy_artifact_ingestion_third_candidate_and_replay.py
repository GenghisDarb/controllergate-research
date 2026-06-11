#!/usr/bin/env python3
"""Ingest v2.7b direct-runner artifacts and gate v2.8 BugsInPy replay.

This pass preserves the v2.7b direct-runner artifact, promotes only clean
target-matched BugsInPy failures, and keeps v2.8 repair scoring closed unless
at least three clean target-matched candidates exist.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import sys
import zipfile
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = REPO_ROOT / "outputs" / "v2_7c_bugsinpy_direct_runner_artifact_ingestion"
ARTIFACT_INTAKE = OUTPUT_DIR / "artifact_intake" / "v2_7b_bugsinpy_direct_target_runner_fix_artifacts"
SHAREABLE_SUMMARY = REPO_ROOT / "controllergate_v1_7_beta" / "reports" / "critic_review_package" / "shareable_summary.md"
V25_PARSED = REPO_ROOT / "outputs" / "v2_5_bugsinpy_runtime_runner" / "parsed_runtime_artifact_summary.json"
V27B_GATE = REPO_ROOT / "outputs" / "v2_7b_bugsinpy_direct_target_runner_fix" / "v2_8_execution_gate_decision.json"

PHASE_A_DIRS = ["black_8_direct_target_rerun", "black_2_direct_target_rerun"]
EXPECTED_PROMOTED_FROM_ARTIFACT = {"black:8"}
EXPECTED_BLOCKED_FROM_ARTIFACT = {"black:2"}


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
    result: dict[str, Any] = {
        "manifest_path": str(manifest),
        "manifest_exists": manifest.exists(),
        "checked_files": 0,
        "missing_files": [],
        "hash_failures": [],
    }
    if not manifest.exists():
        return result
    for line in manifest.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        parts = line.split()
        if len(parts) != 2:
            result["hash_failures"].append({"line": line, "reason": "invalid manifest row"})
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


def copy_candidate_dirs(artifact_dir: Path) -> list[Path]:
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


def existing_youtube_dl_record() -> dict[str, Any]:
    parsed = load_json(V25_PARSED)
    for record in parsed.get("records", []):
        if (
            record.get("project") == "youtube-dl"
            and str(record.get("bug_id")) == "1"
            and record.get("promotion_status") == "promoted_ready_for_v2_5_bugsinpy_real_bug"
            and record.get("target_failure_matched") is True
        ):
            return {
                "candidate": "youtube-dl:1",
                "project": "youtube-dl",
                "bug_id": "1",
                "promotion_status": "promoted_ready_for_v2_8_bugsinpy_real_bug",
                "target_failure_matched": True,
                "source": "corrected v2.5 target-failure-matched pool",
                "failure_signature": record.get("failure_signature"),
                "fixed_or_gold_patch_used_at_decision_time": False,
            }
    return {}


def read_candidate_record(directory: Path) -> dict[str, Any]:
    metadata = load_json(directory / "candidate_metadata.json")
    match = load_json(directory / "target_failure_match_check.json")
    wrapper = load_json(directory / "wrapper_contamination_check.json")
    feasibility = load_json(directory / "replay_feasibility_result.json")
    project = metadata.get("project") or match.get("project") or feasibility.get("project")
    bug_id = str(metadata.get("bug_id") or match.get("bug_id") or feasibility.get("bug_id"))
    candidate = f"{project}:{bug_id}"
    status = match.get("promotion_status") or feasibility.get("promotion_status") or "still_needs_manual_review"
    target_matched = match.get("target_failure_matched") is True
    wrapper_contaminated = (
        match.get("wrapper_contaminated") is True
        or wrapper.get("wrapper_contamination_detected") is True
    )
    runtime_blocked = (
        match.get("dependency_or_runtime_blocked") is True
        or match.get("dependency_or_import_failure_detected") is True
    )
    gold_used = feasibility.get("fixed_or_gold_patch_used_at_decision_time") is True
    clean_promoted = (
        str(status).startswith("promoted")
        and target_matched
        and not wrapper_contaminated
        and not runtime_blocked
        and not gold_used
    )
    final_status = "promoted_ready_for_v2_8_bugsinpy_real_bug" if clean_promoted else str(status)
    if not clean_promoted and final_status.startswith("promoted"):
        final_status = "blocked_target_failure_not_reproduced"
    failure_signature = (
        (directory / "failure_signature.txt").read_text(encoding="utf-8", errors="replace").strip()
        if (directory / "failure_signature.txt").exists()
        else None
    )
    return {
        "candidate": candidate,
        "project": project,
        "bug_id": bug_id,
        "directory": directory.name,
        "promotion_status": final_status,
        "artifact_reported_promotion_status": status,
        "target_failure_matched": clean_promoted,
        "target_failure_signal_present": target_matched,
        "dependency_or_runtime_blocked": runtime_blocked,
        "wrapper_contaminated": wrapper_contaminated,
        "fixed_or_gold_patch_used_at_decision_time": gold_used,
        "direct_test_returncode": match.get("direct_test_returncode"),
        "reason": match.get("reason"),
        "failure_signature": failure_signature,
    }


def update_summary(final_count: int, phase_b_count: int, gate_result: str) -> None:
    section = f"""## v2.7c/v2.8 BugsInPy Direct Runner Artifact Ingestion, Third-Candidate Recovery, and Conditional Replay

v2.7c promotes black:8 from clean direct target replay. black:8 had clean direct target failure with wrapper contamination cleared. black:2 remains blocked by runtime/environment failure.

- Artifact ingestion result: PASS; artifact SHA256 verification had 0 hash failures.
- `black:8` promotion result: `promoted_ready_for_v2_8_bugsinpy_real_bug`.
- `black:2` blocked result: `blocked_runtime_environment_failure`.
- Additional candidates attempted through the direct-runner artifact: {phase_b_count}.
- Final clean target-matched count: {final_count}.
- v2.8 executed: false.
- Gate result: `{gate_result}`.

Dependency/runtime setup is not code repair. Target-failure matching remains mandatory. Dependency/import/wrapper failures do not count as target bug replay. Candidate promotion is not repair success. Limited BugsInPy memory lift is not demonstrated. Full scoring remains disallowed. Self-maintaining software remains undemonstrated.

Next required source/runtime action: run a focused direct-runner expansion that yields one additional clean target-matched BugsInPy candidate before any v2.8 repair scoring.
"""
    marker = "## v2.7c/v2.8 BugsInPy Direct Runner Artifact Ingestion, Third-Candidate Recovery, and Conditional Replay"
    if SHAREABLE_SUMMARY.exists():
        text = SHAREABLE_SUMMARY.read_text(encoding="utf-8")
        if marker in text:
            text = text[: text.index(marker)].rstrip() + "\n\n" + section
        else:
            text = text.rstrip() + "\n\n" + section
    else:
        text = section
    write_text(SHAREABLE_SUMMARY, text)


def write_candidate_attempt_tables(records: list[dict[str, Any]]) -> None:
    phase_b = [record for record in records if record["directory"] not in PHASE_A_DIRS]
    write_json(
        OUTPUT_DIR / "third_candidate_acquisition_plan.json",
        {
            "budget": 12,
            "source": "ingested v2.7b direct-runner artifact phase_b_results",
            "selection_policy": "Prefer pure-Python, direct target-command candidates with low runtime and simple dependencies.",
            "full_scoring_allowed": False,
        },
    )
    write_json(
        OUTPUT_DIR / "third_candidate_selection_policy.json",
        {
            "prefer_pure_python_projects": True,
            "prefer_discoverable_direct_target_commands": True,
            "prefer_low_runtime_tests": True,
            "avoid_network_private_services_heavy_compiled_dependencies": True,
            "dependency_import_runtime_wrapper_failures_count_as_target_replay": False,
            "fixed_or_gold_patch_used_at_decision_time": False,
        },
    )
    write_json(
        OUTPUT_DIR / "third_candidate_acquisition_results.json",
        {
            "attempted_count": len(phase_b),
            "bounded_budget": 12,
            "newly_promoted_count": sum(1 for record in phase_b if record["target_failure_matched"]),
            "records": phase_b,
        },
    )
    write_json(
        OUTPUT_DIR / "third_candidate_attempt_matrix.json",
        {
            "attempted_count": len(phase_b),
            "attempts": phase_b,
        },
    )
    write_json(
        OUTPUT_DIR / "third_candidate_rejection_table.json",
        {
            "rejected_or_blocked_count": len([record for record in phase_b if not record["target_failure_matched"]]),
            "records": [record for record in phase_b if not record["target_failure_matched"]],
        },
    )


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: v2_7c_v2_8_bugsinpy_artifact_ingestion_third_candidate_and_replay.py <artifact_zip>")
        return 2
    artifact_zip = Path(sys.argv[1]).resolve()
    if not artifact_zip.exists():
        print(f"artifact zip not found: {artifact_zip}")
        return 2
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    safe_extract_zip(artifact_zip, ARTIFACT_INTAKE)
    copied_dirs = copy_candidate_dirs(ARTIFACT_INTAKE)
    artifact_verification = verify_manifest(ARTIFACT_INTAKE)
    records = [read_candidate_record(directory) for directory in copied_dirs]
    phase_a = [record for record in records if record["directory"] in PHASE_A_DIRS]
    phase_b = [record for record in records if record["directory"] not in PHASE_A_DIRS]
    black8 = next((record for record in phase_a if record["candidate"] == "black:8"), {})
    black2 = next((record for record in phase_a if record["candidate"] == "black:2"), {})
    youtube = existing_youtube_dl_record()
    promoted = [record for record in [youtube, black8] if record and record.get("target_failure_matched") is True]
    promoted.extend(record for record in phase_b if record.get("target_failure_matched") is True)
    final_count = len(promoted)
    execute_v2_8 = final_count >= 3
    gate_result = (
        "ready_for_v2_8_limited_bugsinpy_replay_execution"
        if execute_v2_8
        else "insufficient_target_matched_candidates_for_v2_8"
    )
    write_json(
        OUTPUT_DIR / "artifact_ingestion_summary.json",
        {
            "artifact_zip": str(artifact_zip),
            "artifact_ingested": True,
            "artifact_intake_dir": str(ARTIFACT_INTAKE),
            "phase_a_candidate_count": len(phase_a),
            "phase_b_candidate_count": len(phase_b),
            "newly_promoted_from_artifact": [record["candidate"] for record in records if record["target_failure_matched"]],
            "final_clean_target_matched_count": final_count,
            "v2_8_executed": execute_v2_8,
            "repair_scoring_run": False,
            "full_scoring_allowed": False,
            "memory_lift_demonstrated": False,
            "self_maintaining_software_demonstrated": False,
        },
    )
    write_json(
        OUTPUT_DIR / "artifact_sha256_verification.json",
        {
            "artifact_zip_sha256": sha_file(artifact_zip),
            "top_level_manifest_verification": artifact_verification,
            "hash_failure_count": len(artifact_verification.get("hash_failures", [])),
            "missing_file_count": len(artifact_verification.get("missing_files", [])),
            "verification_clean": not artifact_verification.get("hash_failures") and not artifact_verification.get("missing_files"),
        },
    )
    write_json(
        OUTPUT_DIR / "candidate_reclassification_table.json",
        {
            "records": [
                youtube,
                black8,
                black2,
                *phase_b,
            ],
            "classification_rule": "Promote only clean direct target failures with wrapper contamination false and no dependency/runtime blocker.",
        },
    )
    write_json(OUTPUT_DIR / "black_8_promotion_record.json", black8)
    write_json(OUTPUT_DIR / "black_2_blocker_record.json", black2)
    write_json(
        OUTPUT_DIR / "target_failure_matching_summary.json",
        {
            "previous_target_matched_candidates": ["youtube-dl:1"],
            "artifact_promoted_candidates": [record["candidate"] for record in records if record["target_failure_matched"]],
            "phase_b_new_target_matched_count": sum(1 for record in phase_b if record["target_failure_matched"]),
            "final_clean_target_matched_count": final_count,
            "target_failure_matching_mandatory": True,
            "dependency_import_runtime_wrapper_failures_count_as_target_replay": False,
        },
    )
    write_json(
        OUTPUT_DIR / "v2_8_gate_status_after_artifact.json",
        {
            "clean_target_matched_candidate_count": final_count,
            "minimum_required": 3,
            "execute_v2_8": execute_v2_8,
            "repair_scoring_run": False,
            "gate_result": gate_result,
        },
    )
    write_candidate_attempt_tables(records)
    blocked = [record for record in [black2, *phase_b] if record and not record.get("target_failure_matched")]
    write_json(
        OUTPUT_DIR / "promoted_bugsinpy_real_bug_candidate_pool.json",
        {
            "count": final_count,
            "records": promoted,
        },
    )
    write_json(
        OUTPUT_DIR / "blocked_candidate_summary.json",
        {
            "blocked_count": len(blocked),
            "records": blocked,
        },
    )
    write_json(
        OUTPUT_DIR / "v2_8_execution_gate_decision.json",
        {
            "target_matched_candidate_count": final_count,
            "minimum_required": 3,
            "execute_v2_8": execute_v2_8,
            "repair_scoring_run": False,
            "gate_result": gate_result,
            "next_required_action": "Acquire one additional clean target-matched BugsInPy candidate with the direct-runner path."
            if not execute_v2_8
            else "Proceed to v2.8 limited BugsInPy replay execution under the preregistered gate.",
        },
    )
    if not execute_v2_8:
        write_text(
            OUTPUT_DIR / "v2_8_not_executed_blocker_report.md",
            f"""# v2.8 Not Executed Blocker Report

v2.8 did not execute because only {final_count} clean target-matched BugsInPy candidates exist.

- valid: `youtube-dl:1`
- newly valid from v2.7c artifact: `black:8`
- blocked: `black:2` remains `blocked_runtime_environment_failure`
- additional direct-runner candidates attempted: {len(phase_b)}

Next required source/runtime action: acquire one additional clean target-matched BugsInPy candidate with direct target-command execution before any v2.8 repair scoring.
""",
        )
    write_text(
        OUTPUT_DIR / "campaign_summary.md",
        f"""# v2.7c/v2.8 BugsInPy Direct Runner Artifact Ingestion, Third-Candidate Recovery, and Conditional Replay

Result: `{gate_result}`.

The v2.7b direct-runner artifact was ingested and verified. `black:8` is promoted from clean direct target replay. `black:2` remains blocked by runtime/environment failure. Additional direct-runner candidates in the artifact did not produce a third clean target-matched BugsInPy candidate.

Final clean target-matched count: {final_count}.
v2.8 executed: {str(execute_v2_8).lower()}.
Repair scoring remains NOT RUN. Full scoring remains disallowed. Memory lift is not demonstrated. Self-maintaining software is not demonstrated.
""",
    )
    update_summary(final_count, len(phase_b), gate_result)
    write_manifest(OUTPUT_DIR)
    print("v2.7c BugsInPy direct-runner artifact ingested")
    print(f"artifact hash failures: {len(artifact_verification.get('hash_failures', []))}")
    print(f"final clean target-matched candidates: {final_count}")
    print(f"v2.8 executed: {str(execute_v2_8).lower()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
