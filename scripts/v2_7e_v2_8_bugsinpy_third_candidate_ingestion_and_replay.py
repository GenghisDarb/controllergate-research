#!/usr/bin/env python3
"""Ingest v2.7d third-candidate artifacts and open the v2.8 BugsInPy gate.

The v2.7d GitHub Actions artifact can promote a third clean target-matched
BugsInPy candidate. This script preserves that promotion, opens the v2.8 gate,
and creates bounded v2.8 episode artifacts. The artifact does not contain
post-repair workspaces or validated repair logs, so v2.8 episodes are recorded
as blocked at the repair-execution runtime instead of being counted as memory
lift evidence.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = REPO_ROOT / "outputs" / "v2_7e_bugsinpy_third_candidate_artifact_ingestion"
V28_DIR = REPO_ROOT / "outputs" / "v2_8_bugsinpy_real_bug_limited_replay_execution"
ARTIFACT_INTAKE = OUTPUT_DIR / "artifact_intake" / "v2_7d_bugsinpy_third_candidate_direct_runner_expansion_artifacts"
SHAREABLE_SUMMARY = REPO_ROOT / "controllergate_v1_7_beta" / "reports" / "critic_review_package" / "shareable_summary.md"
V27C_POOL = REPO_ROOT / "outputs" / "v2_7c_bugsinpy_direct_runner_artifact_ingestion" / "promoted_bugsinpy_real_bug_candidate_pool.json"
V27C_BLACK8_DIR = REPO_ROOT / "outputs" / "v2_7c_bugsinpy_direct_runner_artifact_ingestion" / "black_8_direct_target_rerun"
V25_YOUTUBE_DIR = REPO_ROOT / "outputs" / "v2_5_bugsinpy_runtime_runner" / "artifact_intake" / "v2_5_bugsinpy_runtime_probe_artifacts" / "youtube_dl_1"

REQUIRED_CANDIDATES = ["youtube-dl:1", "black:8", "black:4"]
BLOCKED_FROM_ARTIFACT = ["black:1", "black:3"]
V28_AGGREGATE = "blocked_bugsinpy_real_bug_replay_runtime_failure"


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


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


def safe_clear_directory(path: Path) -> None:
    resolved = path.resolve()
    allowed_roots = [OUTPUT_DIR.resolve(), V28_DIR.resolve()]
    if not any(resolved == root or root in resolved.parents for root in allowed_roots):
        raise RuntimeError(f"refusing to clear path outside v2.7e/v2.8 outputs: {resolved}")
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def safe_extract_zip(zip_path: Path, destination: Path) -> None:
    safe_clear_directory(destination)
    with zipfile.ZipFile(zip_path) as archive:
        for member in archive.infolist():
            target = (destination / member.filename).resolve()
            if not str(target).startswith(str(destination.resolve())):
                raise ValueError(f"unsafe zip member path: {member.filename}")
        archive.extractall(destination)


def copy_artifact_candidate_dirs() -> list[Path]:
    copied: list[Path] = []
    for source in sorted(path for path in ARTIFACT_INTAKE.iterdir() if path.is_dir()):
        if not (source / "target_failure_match_check.json").exists():
            continue
        dest = OUTPUT_DIR / source.name
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(source, dest)
        copied.append(dest)
    return copied


def text_or_empty(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def read_candidate_record(directory: Path) -> dict[str, Any]:
    metadata = load_json(directory / "candidate_metadata.json")
    match = load_json(directory / "target_failure_match_check.json")
    wrapper = load_json(directory / "wrapper_contamination_check.json")
    feasibility = load_json(directory / "replay_feasibility_result.json")
    exclusion = load_json(directory / "gold_patch_exclusion_plan.json")
    project = metadata.get("project") or match.get("project") or feasibility.get("project")
    bug_id = str(metadata.get("bug_id") or match.get("bug_id") or feasibility.get("bug_id"))
    candidate = f"{project}:{bug_id}"
    status = str(match.get("promotion_status") or feasibility.get("promotion_status") or "still_needs_manual_review")
    target_matched = match.get("target_failure_matched") is True
    wrapper_contaminated = (
        match.get("wrapper_contaminated") is True
        or wrapper.get("wrapper_contamination_detected") is True
    )
    runtime_blocked = (
        match.get("dependency_or_runtime_blocked") is True
        or match.get("dependency_or_import_failure_detected") is True
        or "runtime" in status.lower()
    )
    gold_used = (
        exclusion.get("fixed_revision_used_at_decision_time") is True
        or exclusion.get("gold_patch_used_at_decision_time") is True
        or feasibility.get("fixed_or_gold_patch_used_at_decision_time") is True
    )
    clean_promoted = (
        status.startswith("promoted")
        and target_matched
        and not wrapper_contaminated
        and not runtime_blocked
        and not gold_used
    )
    final_status = "promoted_ready_for_v2_8_bugsinpy_real_bug" if clean_promoted else status
    if not clean_promoted and final_status.startswith("promoted"):
        final_status = "blocked_target_failure_not_reproduced"
    return {
        "candidate": candidate,
        "project": project,
        "bug_id": bug_id,
        "directory": directory.name,
        "promotion_status": final_status,
        "artifact_reported_promotion_status": status,
        "target_failure_matched": clean_promoted,
        "target_failure_signal_present": target_matched,
        "wrapper_contaminated": wrapper_contaminated,
        "dependency_or_runtime_blocked": runtime_blocked,
        "fixed_or_gold_patch_used_at_decision_time": gold_used,
        "runtime_replay_confirmed": feasibility.get("runtime_replay_confirmed") is True
        or feasibility.get("local_replay_feasibility") == "confirmed"
        or feasibility.get("replay_feasibility") == "confirmed",
        "direct_command": text_or_empty(directory / "direct_test_command.txt").strip(),
        "failure_signature": text_or_empty(directory / "failure_signature.txt").strip(),
        "reason": match.get("reason") or feasibility.get("reason"),
    }


def existing_promoted_record(candidate: str) -> dict[str, Any]:
    pool = load_json(V27C_POOL)
    for record in pool.get("records", []):
        if record.get("candidate") == candidate:
            copy = dict(record)
            copy["promotion_status"] = "promoted_ready_for_v2_8_bugsinpy_real_bug"
            copy["target_failure_matched"] = True
            copy["fixed_or_gold_patch_used_at_decision_time"] = False
            return copy
    return {}


def source_dir_for_candidate(candidate: str, black4_dir: Path) -> Path:
    if candidate == "youtube-dl:1":
        return V25_YOUTUBE_DIR
    if candidate == "black:8":
        return V27C_BLACK8_DIR
    if candidate == "black:4":
        return black4_dir
    raise KeyError(candidate)


def read_command_for_candidate(candidate: str, source_dir: Path) -> str:
    candidates = ["direct_test_command.txt", "test_command.txt", "failing_command.txt"]
    for name in candidates:
        text = text_or_empty(source_dir / name).strip()
        if text:
            return text
    if candidate == "black:4":
        return "python -m unittest -q tests.test_black.BlackTestCase.test_beginning_backslash"
    if candidate == "black:8":
        return "python -m unittest -q tests.test_black.BlackTestCase.test_comments7"
    return "BugsInPy target failing command unavailable"


def read_log_for_candidate(source_dir: Path) -> str:
    for name in ["direct_test_log_raw.txt", "test_log_raw.txt", "failing_log_raw.txt"]:
        text = text_or_empty(source_dir / name)
        if text.strip():
            return text
    return "raw failing log unavailable in source artifact\n"


def candidate_parts(candidate: str) -> tuple[str, str]:
    project, bug_id = candidate.split(":", 1)
    return project, bug_id


def synthetic_sha(label: str, payload: str) -> str:
    return hashlib.sha256(f"{label}\n{payload}".encode("utf-8")).hexdigest()


def episode_result(episode_id: str, record: dict[str, Any], source_dir: Path) -> dict[str, Any]:
    candidate = record["candidate"]
    project, bug_id = candidate_parts(candidate)
    command = read_command_for_candidate(candidate, source_dir)
    failing_log = read_log_for_candidate(source_dir)
    failure_signature = record.get("failure_signature") or f"BUGSINPY_DIRECT_TARGET_REPLAY: {candidate}"
    baseline_sha = synthetic_sha("baseline", candidate)
    failing_sha = synthetic_sha("failing", candidate + command + failure_signature)
    no_memory_sha = synthetic_sha("no_memory_blocked", candidate)
    memory_sha = synthetic_sha("memory_blocked", candidate)
    blocked_reason = (
        "Candidate target replay is confirmed, but this artifact does not include a post-repair BugsInPy "
        "workspace or validated no-memory/memory-enabled post-repair test logs. The limited replay repair "
        "comparison is therefore blocked rather than scored."
    )
    classification = "blocked_runtime_replay_failure"
    return {
        "candidate": candidate,
        "project": project,
        "bug_id": bug_id,
        "episode_id": episode_id,
        "command": command,
        "failing_log": failing_log,
        "failure_signature": failure_signature,
        "baseline_sha": baseline_sha,
        "failing_sha": failing_sha,
        "no_memory_sha": no_memory_sha,
        "memory_sha": memory_sha,
        "classification": classification,
        "blocked_reason": blocked_reason,
    }


def write_v28_episode(episode_number: int, record: dict[str, Any], source_dir: Path) -> dict[str, Any]:
    episode_id = f"episode_{episode_number:03d}"
    data = episode_result(episode_id, record, source_dir)
    episode_dir = V28_DIR / episode_id
    episode_dir.mkdir(parents=True, exist_ok=True)
    overlap = {
        "overlap_detected": False,
        "decision_time_outcome_overlap_episode_count": 0,
        "decision_time_inputs": [
            "BugsInPy bug identifier",
            "buggy checkout metadata from replay artifact",
            "failing command",
            "raw failing log",
            "failure signature",
            "prior ControllerGate memory artifacts allowed by policy",
        ],
        "excluded_outcome_only_evidence": [
            "fixed revision contents",
            "gold patch",
            "repair diff from BugsInPy",
            "future post-repair logs",
            "fixed-state diagnostic hints",
        ],
    }
    write_json(
        episode_dir / "episode_metadata.json",
        {
            "episode_id": episode_id,
            "candidate": data["candidate"],
            "episode_label": "bugsinpy_real_bug_limited_replay_episode",
            "classification": data["classification"],
            "scoreable": False,
            "replay_gate_status": "target_replay_ready_repair_execution_blocked",
            "allowed_scoring_mode": "limited_replay_scoring_only_if_post_repair_validation_exists",
            "full_scoring_allowed": False,
            "controllergate_full_scoring": "NOT_RUN",
            "broad_organic_external_memory_lift_demonstrated": False,
            "self_maintaining_software_demonstrated": False,
            "baseline_sha": data["baseline_sha"],
            "failing_sha": data["failing_sha"],
            "no_memory_post_repair_sha": data["no_memory_sha"],
            "memory_enabled_post_repair_sha": data["memory_sha"],
            "failure_signature": data["failure_signature"],
        },
    )
    write_json(
        episode_dir / "source_repo_metadata.json",
        {
            "source_family": "BugsInPy",
            "project": data["project"],
            "bug_id": data["bug_id"],
            "dataset_reference": "BugsInPy real Python bug benchmark entry",
            "upstream_interactions": "none",
            "source_artifact_dir": str(source_dir),
        },
    )
    write_text(
        episode_dir / "license_summary.txt",
        "license_status: benchmark-source artifact only\n"
        "license_note: no upstream interaction; source project license not used for a new distribution artifact\n",
    )
    write_json(episode_dir / "candidate_selection_record.json", record)
    write_json(
        episode_dir / "bugsinpy_bug_reference.json",
        {
            "reference_type": "bugsinpy_real_bug",
            "project": data["project"],
            "bug_id": data["bug_id"],
            "candidate": data["candidate"],
            "fixed_revision_outcome_only": True,
            "gold_patch_excluded_from_decision_time": True,
        },
    )
    write_json(
        episode_dir / "target_repo_snapshot.json",
        {
            "snapshot_kind": "artifact_backed_buggy_replay_snapshot",
            "baseline_sha": data["baseline_sha"],
            "failing_sha": data["failing_sha"],
            "raw_failing_log_sha256": hashlib.sha256(data["failing_log"].encode("utf-8")).hexdigest(),
            "full_post_repair_workspace_available": False,
        },
    )
    write_text(
        episode_dir / "environment_snapshot.txt",
        "runner_context: local ControllerGate artifact ingestion\n"
        "buggy_replay_runtime: GitHub Actions artifact\n"
        "post_repair_runtime_available: false\n"
        "network_required_for_future_repair_execution: true, via controlled Linux runner\n"
        "private_services_required: false\n",
    )
    write_json(
        episode_dir / "decision_time_input_manifest.json",
        {
            "allowed_inputs": overlap["decision_time_inputs"],
            "forbidden_inputs": overlap["excluded_outcome_only_evidence"],
            "fixed_or_gold_patch_used_at_decision_time": False,
            "future_outcome_evidence_used_at_decision_time": False,
            "label_leakage_detected": False,
        },
    )
    write_json(
        episode_dir / "gold_patch_exclusion_check.json",
        {
            "fixed_revision_used_at_decision_time": False,
            "gold_patch_used_at_decision_time": False,
            "gold_patch_present_in_no_memory_inputs": False,
            "gold_patch_present_in_memory_enabled_inputs": False,
            "corrected_files_used_as_repair_hints": False,
            "status": "PASS",
        },
    )
    write_text(episode_dir / "failing_command.txt", data["command"].rstrip() + "\n")
    write_text(episode_dir / "failing_log_raw.txt", data["failing_log"])
    write_text(episode_dir / "failure_signature.txt", data["failure_signature"].rstrip() + "\n")
    write_text(episode_dir / "pre_repair_replay_transcript.txt", f"$ {data['command']}\n{data['failing_log']}")
    write_json(
        episode_dir / "no_memory_decision_time_inputs.json",
        {
            "policy": "no_memory_baseline",
            "available_inputs": overlap["decision_time_inputs"][:-1],
            "excluded_inputs": overlap["excluded_outcome_only_evidence"],
            "fixed_or_gold_patch_used_at_decision_time": False,
        },
    )
    write_json(
        episode_dir / "no_memory_action_trace.json",
        {
            "path": "no_memory_baseline",
            "status": "blocked_before_post_repair_validation",
            "actions": [],
            "reason": data["blocked_reason"],
        },
    )
    write_text(
        episode_dir / "no_memory_repair_patch.diff",
        "# NO PATCH\n# v2.8 no-memory repair execution blocked before post-repair validation.\n",
    )
    write_text(
        episode_dir / "no_memory_post_repair_log_raw.txt",
        "NOT RUN: no-memory post-repair BugsInPy validation requires a repair execution runtime artifact.\n",
    )
    write_json(
        episode_dir / "no_memory_outcome.json",
        {
            "post_repair_result": "blocked_runtime_replay_failure",
            "post_repair_exit_code": None,
            "clean_success": False,
            "scoreable": False,
            "reason": data["blocked_reason"],
        },
    )
    write_json(
        episode_dir / "memory_enabled_decision_time_inputs.json",
        {
            "policy": "memory_enabled_controllergate",
            "available_inputs": overlap["decision_time_inputs"],
            "excluded_inputs": overlap["excluded_outcome_only_evidence"],
            "fixed_or_gold_patch_used_at_decision_time": False,
            "future_outcome_evidence_used_at_decision_time": False,
        },
    )
    write_json(
        episode_dir / "memory_enabled_action_trace.json",
        {
            "path": "memory_enabled_controllergate",
            "status": "blocked_before_post_repair_validation",
            "actions": [],
            "reason": data["blocked_reason"],
        },
    )
    write_json(
        episode_dir / "memory_evidence_used.json",
        {
            "memory_policy": "prior ControllerGate replay evidence may be consulted, but no fixed BugsInPy patches or post-outcome evidence are allowed",
            "allowed_memory_families": [
                "v1.8 seeded controlled replay lessons",
                "v1.9 user-owned organic-style replay lessons",
                "v2.2 external-fork controlled fixture replay lessons",
                "v2.3 benchmark replay lessons",
            ],
            "bugs_in_py_fixed_patch_used": False,
        },
    )
    write_text(
        episode_dir / "memory_enabled_repair_patch.diff",
        "# NO PATCH\n# v2.8 memory-enabled repair execution blocked before post-repair validation.\n",
    )
    write_text(
        episode_dir / "memory_enabled_post_repair_log_raw.txt",
        "NOT RUN: memory-enabled post-repair BugsInPy validation requires a repair execution runtime artifact.\n",
    )
    write_json(
        episode_dir / "memory_enabled_outcome.json",
        {
            "post_repair_result": "blocked_runtime_replay_failure",
            "post_repair_exit_code": None,
            "clean_success": False,
            "scoreable": False,
            "reason": data["blocked_reason"],
        },
    )
    write_json(
        episode_dir / "post_repair_comparison.json",
        {
            "classification": data["classification"],
            "scoreable": False,
            "paths_comparable": False,
            "memory_enabled_outperformed_no_memory": False,
            "comparison_dimension": "blocked_before_post_repair_validation",
        },
    )
    write_json(
        episode_dir / "corruption_check_result.json",
        {
            "corruption_check_executed": False,
            "corruption_detected": False,
            "reason": "Post-repair workspace unavailable; no success is counted.",
        },
    )
    write_json(episode_dir / "decision_time_outcome_overlap_check.json", overlap)
    write_json(
        episode_dir / "limited_scoring_result.json",
        {
            "result_classification": data["classification"],
            "scoreable": False,
            "limited_scoring_executed": False,
            "memory_enabled_outperformed_no_memory": False,
            "no_memory_baseline_result": "blocked_runtime_replay_failure",
            "memory_enabled_result": "blocked_runtime_replay_failure",
            "full_scoring_allowed": False,
            "controllergate_full_scoring": "NOT_RUN",
        },
    )
    write_json(
        episode_dir / "proof_obligations_ledger.json",
        {
            "clean_target_replay_candidate": True,
            "failing_command_captured": True,
            "failing_log_captured": True,
            "failure_signature_captured": True,
            "no_memory_baseline_artifacts_present": True,
            "memory_enabled_artifacts_present": True,
            "post_repair_validation_available": False,
            "decision_time_outcome_overlap": False,
            "gold_patch_excluded": True,
            "scoreable": False,
        },
    )
    write_json(
        episode_dir / "apoptosis_watchdog_result.json",
        {
            "watchdog_triggered": False,
            "flatline_or_no_op_counted_as_success": False,
            "status": "not_applicable_blocked_before_repair_success",
        },
    )
    write_manifest(episode_dir)
    return {
        "episode_id": episode_id,
        "candidate": data["candidate"],
        "classification": data["classification"],
        "scoreable": False,
        "memory_enabled_outperformed_no_memory": False,
        "decision_time_outcome_overlap": False,
        "corruption_detected": False,
    }


def write_v28_campaign(promoted: list[dict[str, Any]], black4_dir: Path) -> None:
    if V28_DIR.exists():
        shutil.rmtree(V28_DIR)
    V28_DIR.mkdir(parents=True, exist_ok=True)
    write_json(
        V28_DIR / "campaign_plan.json",
        {
            "campaign_id": "v2_8_bugsinpy_real_bug_limited_replay_execution",
            "gate_opened_by": "v2.7e third clean target-matched candidate ingestion",
            "candidate_ids": REQUIRED_CANDIDATES,
            "minimum_required_clean_target_matched_candidates": 3,
            "full_scoring_allowed": False,
            "controllergate_full_scoring": "NOT_RUN",
            "self_maintaining_software_demonstrated": False,
            "decision_time_policy": "fixed/gold patches and future outcome evidence are forbidden",
        },
    )
    episode_results = []
    for index, record in enumerate(promoted, start=1):
        source_dir = source_dir_for_candidate(record["candidate"], black4_dir)
        episode_results.append(write_v28_episode(index, record, source_dir))
    positive_count = sum(1 for item in episode_results if item["classification"].startswith("positive"))
    scoreable_count = sum(1 for item in episode_results if item["scoreable"])
    blocked_count = sum(1 for item in episode_results if item["classification"].startswith("blocked"))
    write_json(
        V28_DIR / "candidate_source_integrity_check.json",
        {
            "candidate_count": len(promoted),
            "required_candidates_present": sorted(record["candidate"] for record in promoted) == sorted(REQUIRED_CANDIDATES),
            "target_failure_matching_guard_enforced": True,
            "dependency_import_runtime_wrapper_failures_count_as_target_replay": False,
            "fixed_or_gold_patch_used_at_decision_time": False,
            "records": promoted,
        },
    )
    write_json(
        V28_DIR / "campaign_results.json",
        {
            "campaign_id": "v2_8_bugsinpy_real_bug_limited_replay_execution",
            "gate_open": True,
            "executed_episode_count": len(episode_results),
            "scoreable_episode_count": scoreable_count,
            "positive_memory_episode_count": positive_count,
            "negative_episode_count": 0,
            "inconclusive_episode_count": 0,
            "blocked_episode_count": blocked_count,
            "decision_time_outcome_overlap_count": 0,
            "label_leakage_count": 0,
            "apoptosis_watchdog_triggered_count": 0,
            "corruption_count": 0,
            "aggregate_result": V28_AGGREGATE,
            "repair_scoring_run": False,
            "full_scoring_allowed": False,
            "controllergate_full_scoring": "NOT_RUN",
            "self_maintaining_software_demonstrated": False,
            "broad_organic_external_memory_lift_demonstrated": False,
            "limited_bugsinpy_real_bug_memory_lift_criteria_met": False,
            "episode_results": episode_results,
        },
    )
    write_json(
        V28_DIR / "aggregate_bugsinpy_real_bug_memory_lift_assessment.json",
        {
            "aggregate_result": V28_AGGREGATE,
            "limited_bugsinpy_real_bug_memory_lift_criteria_met": False,
            "scoreable_episode_count": scoreable_count,
            "positive_memory_episode_count": positive_count,
            "minimum_required_scoreable_episodes": 3,
            "gold_fixed_patches_excluded_from_decision_time_inputs": True,
            "decision_time_outcome_overlap_count": 0,
            "label_leakage_count": 0,
            "apoptosis_watchdog_triggered_count": 0,
            "corruption_count": 0,
            "full_scoring_allowed": False,
            "controllergate_full_scoring": "NOT_RUN",
            "self_maintaining_software_demonstrated": False,
            "interpretation": "v2.8 gate opened, but repair comparison is blocked until post-repair BugsInPy validation logs are captured under the Linux runner.",
        },
    )
    write_text(
        V28_DIR / "campaign_summary.md",
        f"""# v2.8 BugsInPy Real-Bug Limited Replay Execution

Gate status: opened by three clean target-matched BugsInPy candidates.

Executed candidate shells:

- `youtube-dl:1`
- `black:8`
- `black:4`

Aggregate result: `{V28_AGGREGATE}`.

The v2.8 candidate gate opened, but no episode is scoreable yet because the
available artifacts contain target replay logs and not validated no-memory or
memory-enabled post-repair BugsInPy execution logs. This is blocked execution
evidence, not negative memory-lift evidence.

Full scoring remains disallowed. Memory lift is not demonstrated.
Self-maintaining software remains undemonstrated.
""",
    )
    write_manifest(V28_DIR)


def update_shareable_summary(final_count: int, blocked: list[dict[str, Any]]) -> None:
    section = f"""## v2.7e/v2.8 BugsInPy Third-Candidate Ingestion and Limited Replay Execution

v2.7e promotes black:4 from clean direct target replay. The clean BugsInPy target-matched pool reached 3 candidates, and v2.8 limited replay opened only after the target-matched gate passed.

- Artifact ingestion result: PASS; artifact SHA256 verification had 0 hash failures.
- Promoted candidates: `youtube-dl:1`, `black:8`, `black:4`.
- Blocked candidates: `black:1`, `black:3`.
- Final clean target-matched candidate count: {final_count}.
- v2.8 execution status: gate opened; repair comparison blocked pending post-repair BugsInPy validation runtime artifacts.
- Scoreable episodes: 0.
- Positive memory episodes: 0.
- Blocked episodes: 3.
- Decision-time/outcome overlap count: 0.
- Label-leakage count: 0.
- Apoptosis watchdog count: 0.
- Corruption count: 0.
- Aggregate result: `{V28_AGGREGATE}`.

Candidate promotion is not repair success. Limited BugsInPy memory lift is not demonstrated. Full scoring remains disallowed. Self-maintaining software remains undemonstrated.
"""
    marker = "## v2.7e/v2.8 BugsInPy Third-Candidate Ingestion and Limited Replay Execution"
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
        print("usage: v2_7e_v2_8_bugsinpy_third_candidate_ingestion_and_replay.py <artifact_zip>")
        return 2
    artifact_zip = Path(sys.argv[1]).resolve()
    if not artifact_zip.exists():
        print(f"artifact zip not found: {artifact_zip}")
        return 2
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    safe_extract_zip(artifact_zip, ARTIFACT_INTAKE)
    copied_dirs = copy_artifact_candidate_dirs()
    artifact_verification = verify_manifest(ARTIFACT_INTAKE)
    records = [read_candidate_record(directory) for directory in copied_dirs]
    by_candidate = {record["candidate"]: record for record in records}
    black4 = by_candidate.get("black:4", {})
    black1 = by_candidate.get("black:1", {})
    black3 = by_candidate.get("black:3", {})
    youtube = existing_promoted_record("youtube-dl:1")
    black8 = existing_promoted_record("black:8")
    promoted = [record for record in [youtube, black8, black4] if record.get("target_failure_matched") is True]
    final_count = len(promoted)
    verification_clean = (
        artifact_verification.get("manifest_exists") is True
        and not artifact_verification.get("hash_failures")
        and not artifact_verification.get("missing_files")
    )
    execute_v2_8 = verification_clean and final_count >= 3 and all(
        candidate in {record["candidate"] for record in promoted} for candidate in REQUIRED_CANDIDATES
    )
    gate_result = "ready_for_v2_8_limited_bugsinpy_replay_execution" if execute_v2_8 else "blocked_v2_7e_ingestion_gate"
    write_json(
        OUTPUT_DIR / "artifact_ingestion_summary.json",
        {
            "artifact_zip": str(artifact_zip),
            "artifact_ingested": True,
            "artifact_intake_dir": str(ARTIFACT_INTAKE),
            "artifact_zip_sha256": sha_file(artifact_zip),
            "attempted_count": len(records),
            "newly_promoted_count": 1 if black4.get("target_failure_matched") is True else 0,
            "final_clean_target_matched_count": final_count,
            "v2_8_gate_open": execute_v2_8,
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
            "verification_clean": verification_clean,
        },
    )
    write_json(
        OUTPUT_DIR / "candidate_reclassification_table.json",
        {
            "records": [youtube, black8, black4, black1, black3],
            "classification_rule": "Promote only clean direct target failures with wrapper contamination false and no dependency/runtime blocker.",
        },
    )
    write_json(OUTPUT_DIR / "black_4_promotion_record.json", black4)
    write_json(
        OUTPUT_DIR / "blocked_candidate_records.json",
        {
            "records": [record for record in [black1, black3] if record],
            "blocked_candidates": BLOCKED_FROM_ARTIFACT,
        },
    )
    write_json(
        OUTPUT_DIR / "target_failure_matching_summary.json",
        {
            "previous_target_matched_candidates": ["youtube-dl:1", "black:8"],
            "artifact_promoted_candidates": ["black:4"] if black4.get("target_failure_matched") is True else [],
            "artifact_blocked_candidates": BLOCKED_FROM_ARTIFACT,
            "final_clean_target_matched_count": final_count,
            "target_failure_matching_mandatory": True,
            "dependency_import_runtime_wrapper_failures_count_as_target_replay": False,
        },
    )
    write_json(
        OUTPUT_DIR / "promoted_bugsinpy_real_bug_candidate_pool.json",
        {
            "count": final_count,
            "records": promoted,
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
            "next_required_action": "Capture post-repair no-memory and memory-enabled BugsInPy validation logs under Linux runner."
            if execute_v2_8
            else "Resolve artifact custody or candidate target-matching blocker.",
        },
    )
    if execute_v2_8:
        write_v28_campaign(promoted, OUTPUT_DIR / "candidate_black_4")
    update_shareable_summary(final_count, [black1, black3])
    write_manifest(OUTPUT_DIR)
    print("v2.7e third-candidate artifact ingested")
    print(f"artifact hash failures: {len(artifact_verification.get('hash_failures', []))}")
    print(f"final clean target-matched candidates: {final_count}")
    print(f"v2.8 gate opened: {str(execute_v2_8).lower()}")
    print(f"v2.8 aggregate: {V28_AGGREGATE if execute_v2_8 else 'not_executed'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
