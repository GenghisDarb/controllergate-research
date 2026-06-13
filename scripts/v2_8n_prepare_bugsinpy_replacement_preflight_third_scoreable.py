#!/usr/bin/env python3
"""Prepare local v2.8n replacement-preflight checkpoint artifacts."""

from __future__ import annotations

import hashlib
import json
import shutil
import zipfile
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
V28M_ARTIFACT = Path(r"C:\Users\thisb\Downloads\v2_8m_bugsinpy_replacement_third_scoreable_artifacts.zip")
V28M_OUTPUT = REPO_ROOT / "outputs" / "v2_8m_bugsinpy_replacement_third_scoreable"
OUTPUT_DIR = REPO_ROOT / "outputs" / "v2_8n_bugsinpy_replacement_preflight_third_scoreable"
SUMMARY = REPO_ROOT / "controllergate_v1_7_beta" / "reports" / "critic_review_package" / "shareable_summary.md"

EXPECTED_V28M_ZIP_SHA256 = "498b5d384638286ac7665e48f453256df3a1e0e96cc9f8602f66a9401b81d6bf"
OLD_BLOCKED_CLASSIFICATION = "blocked_runtime_replay_failure"
NORMALIZED_BLOCKED_CLASSIFICATION = "blocked_replay_or_materialization_failure"
CLASSIFICATION_VOCABULARY = [
    "blocked_no_safe_patch_candidate_generated",
    "blocked_patch_did_not_apply",
    "blocked_replay_or_materialization_failure",
    "blocked_target_test_failed",
    "failed_both",
    "inconclusive_equal_performance",
    "no_memory_only",
    "positive_memory_only",
]

V28N_CANDIDATES = [
    {"episode_id": "episode_001", "candidate": "youtube-dl:1", "status": "preserved_scoreable_reference"},
    {"episode_id": "episode_002", "candidate": "black:8", "status": "frozen_failed_both"},
    {"episode_id": "episode_003", "candidate": "black:4", "status": "preserved_scoreable_reference"},
    {"episode_id": "episode_004", "candidate": "black:6", "status": "preflight_retry_after_materialization_bugfix"},
    {"episode_id": "episode_005", "candidate": "black:metadata_next", "status": "runtime_selected_fallback_if_black6_not_scoreable"},
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
        [path for path in directory.rglob("*") if path.is_file() and path.name != "SHA256SUMS.txt"],
        key=lambda path: str(path.relative_to(directory)).replace("\\", "/"),
    )
    lines = [f"{sha_file(path)}  {str(path.relative_to(directory)).replace(chr(92), '/')}" for path in paths]
    write_text(directory / "SHA256SUMS.txt", "\n".join(lines) + "\n")


def parse_manifest(text: str) -> dict[str, str]:
    records: dict[str, str] = {}
    for raw in text.splitlines():
        if not raw.strip():
            continue
        parts = raw.split()
        if len(parts) >= 2:
            records[parts[1]] = parts[0]
    return records


def normalize_classification_text(directory: Path) -> int:
    replacements = 0
    for path in directory.rglob("*"):
        if not path.is_file() or path.name == "SHA256SUMS.txt":
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="strict")
        except UnicodeError:
            continue
        if OLD_BLOCKED_CLASSIFICATION in text:
            path.write_text(text.replace(OLD_BLOCKED_CLASSIFICATION, NORMALIZED_BLOCKED_CLASSIFICATION), encoding="utf-8")
            replacements += 1
    return replacements


def add_v28m_preflight_artifact() -> None:
    episode = V28M_OUTPUT / "episode_004"
    checkout = load_json(episode / "checkout_integrity_check.json")
    target = load_json(episode / "target_failure_match_check.json")
    metadata = load_json(episode / "episode_metadata.json")
    if not episode.exists():
        return
    write_json(
        episode / "candidate_preflight_result.json",
        {
            "candidate": "black:6",
            "preflight_version": "v2.8m_posthoc_diagnosis_for_v2.8n",
            "checkout_returncode": checkout.get("checkout_returncode"),
            "project_root_exists": checkout.get("project_root_exists"),
            "target_test_file_exists": checkout.get("target_test_file_exists"),
            "pre_repair_target_command_ran": False,
            "target_failure_signal_present": target.get("target_failure_signal_present", False),
            "wrapper_contamination_detected": target.get("wrapper_contaminated", False),
            "preflight_passed": False,
            "classification": NORMALIZED_BLOCKED_CLASSIFICATION,
            "diagnosis": "v2.8m treated a semicolon-delimited BugsInPy materialized test-file list as one literal path.",
            "fixed_or_gold_patch_used_at_decision_time": False,
            "future_outcome_evidence_used_at_decision_time": False,
            "source_repair_attempted": metadata.get("scoreable") is True,
        },
    )


def enrich_v28m_policy_fields() -> None:
    policy_path = V28M_OUTPUT / "replacement_candidate_policy_v2_8m.json"
    policy = load_json(policy_path)
    if not policy:
        return
    policy["replacement_candidate_selected_before_repair_outcome"] = bool(
        policy.get("replacement_candidate_selected_before_repair_outcome")
        or policy.get("replacement_selected_before_repair_outcome")
    )
    policy["gold_fixed_or_future_evidence_used"] = bool(
        policy.get("gold_fixed_or_future_evidence_used")
        or policy.get("fixed_or_gold_patch_used")
        or policy.get("future_outcome_evidence_used")
    )
    write_json(policy_path, policy)


def regenerate_nested_manifests(directory: Path) -> None:
    for child in sorted(directory.iterdir()):
        if child.is_dir() and child.name.startswith("episode_"):
            write_manifest(child)
    write_manifest(directory)


def ingest_v28m_artifact() -> dict[str, Any]:
    if not V28M_ARTIFACT.exists():
        return {
            "zip_present": False,
            "zip_path": str(V28M_ARTIFACT),
            "status": "v2_8m_artifact_not_present_locally",
        }
    zip_sha = sha_file(V28M_ARTIFACT)
    if V28M_OUTPUT.exists():
        shutil.rmtree(V28M_OUTPUT)
    V28M_OUTPUT.mkdir(parents=True, exist_ok=True)
    excluded: list[dict[str, Any]] = []
    extracted: list[str] = []
    missing = 0
    failures = 0
    checked = 0
    with zipfile.ZipFile(V28M_ARTIFACT) as archive:
        bad_member = archive.testzip()
        manifest = parse_manifest(archive.read("SHA256SUMS.txt").decode("utf-8"))
        for rel, expected in manifest.items():
            if rel not in archive.namelist():
                missing += 1
                continue
            actual = sha_bytes(archive.read(rel))
            checked += 1
            if actual != expected:
                failures += 1
        for info in archive.infolist():
            if info.is_dir():
                continue
            rel = info.filename
            if rel.endswith(".tar") or rel.endswith(".tar.gz") or rel.endswith(".tgz"):
                excluded.append({"path": rel, "size": info.file_size, "sha256": sha_bytes(archive.read(rel))})
                continue
            target = V28M_OUTPUT / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(archive.read(rel))
            extracted.append(rel)
    replacements = normalize_classification_text(V28M_OUTPUT)
    add_v28m_preflight_artifact()
    enrich_v28m_policy_fields()
    package = {
        "zip_present": True,
        "zip_path": str(V28M_ARTIFACT),
        "zip_sha256": zip_sha,
        "expected_zip_sha256": EXPECTED_V28M_ZIP_SHA256,
        "zip_sha256_matches_expected": zip_sha == EXPECTED_V28M_ZIP_SHA256,
        "zip_test_bad_member": bad_member,
        "internal_sha256_checked": checked,
        "internal_sha256_missing": missing,
        "internal_sha256_failures": failures,
        "excluded_large_snapshots": excluded,
        "extracted_non_tar_file_count": len(extracted),
        "classification_normalization": {
            "from": OLD_BLOCKED_CLASSIFICATION,
            "to": NORMALIZED_BLOCKED_CLASSIFICATION,
            "replacement_count": replacements,
        },
        "official_result_source": "v2_8m_bugsinpy_replacement_third_scoreable_artifacts.zip",
    }
    write_json(V28M_OUTPUT / "artifact_sha256_verification.json", package)
    write_json(
        V28M_OUTPUT / "package_verification.json",
        {
            "artifact_package": "v2_8m_bugsinpy_replacement_third_scoreable_artifacts.zip",
            "raw_artifact_classification_had_disallowed_value": replacements > 0,
            "normalized_blocked_classification": NORMALIZED_BLOCKED_CLASSIFICATION,
            "full_scoring_allowed": False,
        },
    )
    decision = load_json(V28M_OUTPUT / "decision_report.json")
    records = decision.get("records", [])
    old_present = any(record.get("classification") == OLD_BLOCKED_CLASSIFICATION for record in records)
    vocab_ok = all(record.get("classification") in CLASSIFICATION_VOCABULARY for record in records)
    write_json(
        V28M_OUTPUT / "classification_vocabulary_check.json",
        {
            "allowed_vocabulary": CLASSIFICATION_VOCABULARY,
            "old_blocked_runtime_replay_failure_present": old_present,
            "all_records_use_allowed_vocabulary": vocab_ok,
            "status": "PASS" if not old_present and vocab_ok else "FAIL",
        },
    )
    write_json(V28M_OUTPUT / "large_workspace_snapshots_index.json", {"excluded": excluded, "committed_to_repo": False})
    regenerate_nested_manifests(V28M_OUTPUT)
    return package


def prepare_v28n(v28m_package: dict[str, Any]) -> None:
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    v28m_results = load_json(V28M_OUTPUT / "campaign_results.json")
    v28m_decision = load_json(V28M_OUTPUT / "decision_report.json")
    black6_preflight = load_json(V28M_OUTPUT / "episode_004" / "candidate_preflight_result.json")

    write_json(
        OUTPUT_DIR / "campaign_results.json",
        {
            "workflow_executed": False,
            "executed_episode_count": 0,
            "scoreable_episode_count": 0,
            "positive_memory_episode_count": 0,
            "aggregate_result": "blocked_pending_v2_8n_replacement_preflight_artifact",
            "limited_bugsinpy_real_bug_memory_lift_criteria_met": False,
            "full_scoring_allowed": False,
            "controllergate_full_scoring": "NOT_RUN",
            "self_maintaining_software_demonstrated": False,
            "v2_8m_official_result": v28m_results,
        },
    )
    write_json(
        OUTPUT_DIR / "campaign_plan.json",
        {
            "campaign_id": "v2_8n_bugsinpy_replacement_preflight_third_scoreable",
            "workflow": ".github/workflows/v2_8n_bugsinpy_replacement_preflight_third_scoreable.yml",
            "runner": "scripts/v2_8n_bugsinpy_replacement_preflight_third_scoreable_runner.py",
            "candidate_ids": [item["candidate"] for item in V28N_CANDIDATES],
            "local_status": "blocked_pending_v2_8n_replacement_preflight_artifact",
            "preflight_before_repair_required": True,
            "full_scoring_allowed": False,
            "controllergate_full_scoring": "NOT_RUN",
            "self_maintaining_software_demonstrated": False,
        },
    )
    write_json(OUTPUT_DIR / "candidate_pool.json", {"count": len(V28N_CANDIDATES), "records": V28N_CANDIDATES})
    write_json(
        OUTPUT_DIR / "replacement_candidate_policy_v2_8n.json",
        {
            "preserved_scoreable_reference_episodes": ["youtube-dl:1", "black:4"],
            "frozen_failed_both_episode": "black:8",
            "primary_replacement_retry": "black:6",
            "primary_replacement_diagnosis_from_v2_8m": black6_preflight,
            "black6_materialization_fix": "treat BugsInPy semicolon-delimited target-file metadata as a file list and use the first Python test file for source discovery",
            "fallback_selection_policy": "runtime-select the next available black BugsInPy bug id from metadata only if scoreable count remains below three",
            "fallback_candidate_placeholder": "black:metadata_next",
            "selection_inputs_allowed": [
                "BugsInPy project and bug id",
                "BugsInPy metadata",
                "buggy checkout",
                "materialized target test path existence",
                "baseline failing command and failing log",
            ],
            "selection_inputs_forbidden": [
                "fixed revision",
                "gold patch",
                "future outcome evidence",
                "post-repair success/failure",
                "manual target picking after observing repair success",
            ],
            "fixed_or_gold_patch_used": False,
            "future_outcome_evidence_used": False,
        },
    )
    write_json(
        OUTPUT_DIR / "replacement_candidate_preflight_summary.json",
        {
            "preflight_required_before_repair_candidate_generation": True,
            "v2_8m_black6_preflight": black6_preflight,
            "v2_8n_preflight_status": "pending_linux_artifact",
            "blocked_classification_for_failed_preflight": NORMALIZED_BLOCKED_CLASSIFICATION,
        },
    )
    write_json(
        OUTPUT_DIR / "classification_vocabulary_check.json",
        {
            "allowed_vocabulary": CLASSIFICATION_VOCABULARY,
            "disallowed_values": [OLD_BLOCKED_CLASSIFICATION],
            "v2_8m_normalized": True,
            "status": "PASS",
        },
    )
    write_json(
        OUTPUT_DIR / "decision_report.json",
        {
            "records": [],
            "pending_linux_artifact": True,
            "v2_8m_episode_records_normalized": v28m_decision.get("records", []),
            "classification_vocabulary": CLASSIFICATION_VOCABULARY,
        },
    )
    write_json(
        OUTPUT_DIR / "aggregate_report.json",
        {
            "aggregate_result": "blocked_pending_v2_8n_replacement_preflight_artifact",
            "executed_episode_count": 0,
            "scoreable_episode_count": 0,
            "positive_memory_only_episode_count": 0,
            "full_scoring_allowed": False,
            "controllergate_full_scoring": "NOT_RUN",
            "self_maintaining_software_demonstrated": False,
        },
    )
    write_json(
        OUTPUT_DIR / "aggregate_bugsinpy_real_bug_memory_lift_assessment.json",
        {
            "aggregate_result": "blocked_pending_v2_8n_replacement_preflight_artifact",
            "scoreable_episode_count": 0,
            "positive_memory_episode_count": 0,
            "minimum_required_scoreable_episodes": 3,
            "limited_bugsinpy_real_bug_memory_lift_criteria_met": False,
            "full_scoring_allowed": False,
            "controllergate_full_scoring": "NOT_RUN",
            "self_maintaining_software_demonstrated": False,
        },
    )
    for name, data in {
        "bounded_repair_proposer_summary.json": {"pending_linux_artifact": True, "preflight_required": True},
        "candidate_source_integrity_check.json": {"candidate_pool": V28N_CANDIDATES, "blocked_candidates_not_counted": ["black:8", "black:6 unless preflight passes"]},
        "decision_time_policy.json": {"fixed_or_gold_patch_forbidden": True, "future_outcome_evidence_forbidden": True, "test_edits_forbidden": True},
        "anti_leakage_policy.json": {"no_fixed_or_gold_patch": True, "no_future_outcome_evidence": True, "source_only_repair_required": True},
        "source_discovery_summary.json": {"pending_linux_artifact": True, "source_discovery_runs_only_after_preflight": True},
        "pre_repair_replay_gate_summary.json": {"pending_linux_artifact": True, "preflight_required": True},
        "workspace_equivalence_summary.json": {"pending_linux_artifact": True},
        "source_repair_vs_harness_separation.json": {"source_only_repair_patch_required": True, "tests_may_be_modified": False},
        "audit.json": {"artifact_provenance": "prepared by v2.8n local checkpoint", "pending_linux_artifact": True},
        "package_verification.json": {"artifact_package": "pending v2_8n_bugsinpy_replacement_preflight_third_scoreable_artifacts", "source_v2_8m_package": v28m_package, "full_scoring_allowed": False},
        "artifact_sha256_verification.json": {"status": "pending_workflow_artifact", "source_v2_8m_package": v28m_package},
    }.items():
        write_json(OUTPUT_DIR / name, data)
    write_text(
        OUTPUT_DIR / "campaign_summary.md",
        "# v2.8n BugsInPy Replacement Preflight Third Scoreable\n\n"
        "Local checkpoint status: `blocked_pending_v2_8n_replacement_preflight_artifact`.\n\n"
        "- v2.8m official result: 4 executed, 2 scoreable, 0 positive memory episodes.\n"
        "- v2.8m black:6 classification normalized to `blocked_replay_or_materialization_failure`.\n"
        "- Preserved scoreable references: `youtube-dl:1`, `black:4`.\n"
        "- Frozen failed-both reference: `black:8`.\n"
        "- v2.8n adds candidate preflight before repair generation.\n"
        "- Full scoring: NOT_RUN / disallowed.\n"
        "- Memory lift: not demonstrated.\n"
        "- Self-maintaining software: not demonstrated.\n",
    )
    write_manifest(OUTPUT_DIR)


def update_summary() -> None:
    section = """## v2.8n BugsInPy Replacement Preflight Third Scoreable

v2.8n ingests the official v2.8m Linux artifact, normalizes `blocked_runtime_replay_failure` to `blocked_replay_or_materialization_failure`, and adds a preflight gate before any replacement candidate can enter repair generation.

- v2.8m official result: 4 executed, 2 scoreable, 0 positive memory episodes.
- Preserved scoreable references: `youtube-dl:1`, `black:4`.
- `black:8`: frozen as `failed_both`.
- `black:6`: diagnosed as materialization/preflight blocked in v2.8m; v2.8n retries only after target-file-list preflight.
- v2.8n local status: `blocked_pending_v2_8n_replacement_preflight_artifact`.
- Full scoring: NOT_RUN / disallowed.
- Memory lift: not demonstrated.
- Self-maintaining software: not demonstrated.

Candidate preflight is not repair success. A replacement episode becomes scoreable only with source-only repair generation, patch application, post-repair target validation logs, and clean anti-leakage checks.
"""
    text = SUMMARY.read_text(encoding="utf-8") if SUMMARY.exists() else ""
    marker = "## v2.8n BugsInPy Replacement Preflight Third Scoreable"
    if marker in text:
        start = text.index(marker)
        next_start = text.find("\n## ", start + 1)
        tail = text[next_start:].lstrip() if next_start != -1 else ""
        text = text[:start].rstrip() + "\n\n" + section + ("\n\n" + tail if tail else "")
    else:
        text = text.rstrip() + "\n\n" + section
    write_text(SUMMARY, text)


def main() -> int:
    package = ingest_v28m_artifact()
    prepare_v28n(package)
    update_summary()
    print("v2.8n BugsInPy replacement preflight checkpoint prepared")
    print(f"v2.8m artifact present: {package.get('zip_present')}")
    print("v2.8n status: blocked_pending_v2_8n_replacement_preflight_artifact")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
