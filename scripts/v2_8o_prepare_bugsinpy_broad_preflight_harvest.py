#!/usr/bin/env python3
"""Prepare local v2.8o broad BugsInPy preflight-harvest checkpoint artifacts."""

from __future__ import annotations

import hashlib
import json
import shutil
import zipfile
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
V28N_ARTIFACT = Path(r"C:\Users\thisb\Downloads\v2_8n_bugsinpy_replacement_preflight_third_scoreable_artifacts.zip")
V28N_OUTPUT = REPO_ROOT / "outputs" / "v2_8n_bugsinpy_replacement_preflight_third_scoreable"
OUTPUT_DIR = REPO_ROOT / "outputs" / "v2_8o_bugsinpy_broad_preflight_harvest"
SUMMARY = REPO_ROOT / "controllergate_v1_7_beta" / "reports" / "critic_review_package" / "shareable_summary.md"

EXPECTED_V28N_ZIP_SHA256 = "31ef78b0f9ea422ac56338dd4369966874b89d9f5fe85d7ad63ea922d9280ca6"

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

BASELINE_RECORDS = [
    {"episode_id": "episode_001", "candidate": "youtube-dl:1", "status": "preserved_scoreable_reference"},
    {"episode_id": "episode_002", "candidate": "black:8", "status": "frozen_non_scoreable_unless_preregistered_rule_exists"},
    {"episode_id": "episode_003", "candidate": "black:4", "status": "preserved_scoreable_reference"},
    {"episode_id": "episode_004", "candidate": "black:6", "status": "retained_blocked_materialization_missing_fixture"},
    {"episode_id": "episode_005", "candidate": "black:7", "status": "retained_optional_only_if_bounded_heuristic_matches"},
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


def regenerate_nested_manifests(directory: Path) -> None:
    for child in sorted(directory.iterdir()):
        if child.is_dir() and child.name.startswith("episode_"):
            write_manifest(child)
    write_manifest(directory)


def ingest_v28n_artifact() -> dict[str, Any]:
    if not V28N_ARTIFACT.exists():
        return {
            "zip_present": False,
            "zip_path": str(V28N_ARTIFACT),
            "status": "v2_8n_artifact_not_present_locally",
        }
    zip_sha = sha_file(V28N_ARTIFACT)
    if V28N_OUTPUT.exists():
        shutil.rmtree(V28N_OUTPUT)
    V28N_OUTPUT.mkdir(parents=True, exist_ok=True)
    excluded: list[dict[str, Any]] = []
    extracted: list[str] = []
    missing = 0
    failures = 0
    checked = 0
    with zipfile.ZipFile(V28N_ARTIFACT) as archive:
        bad_member = archive.testzip()
        manifest = parse_manifest(archive.read("SHA256SUMS.txt").decode("utf-8"))
        names = set(archive.namelist())
        for rel, expected in manifest.items():
            if rel not in names:
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
            data = archive.read(rel)
            if rel.endswith(".tar") or rel.endswith(".tar.gz") or rel.endswith(".tgz"):
                excluded.append({"path": rel, "size": info.file_size, "sha256": sha_bytes(data)})
                continue
            target = V28N_OUTPUT / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            extracted.append(rel)
    package = {
        "zip_present": True,
        "zip_path": str(V28N_ARTIFACT),
        "zip_sha256": zip_sha,
        "expected_zip_sha256": EXPECTED_V28N_ZIP_SHA256,
        "zip_sha256_matches_expected": zip_sha == EXPECTED_V28N_ZIP_SHA256,
        "zip_test_bad_member": bad_member,
        "internal_sha256_checked": checked,
        "internal_sha256_missing": missing,
        "internal_sha256_failures": failures,
        "excluded_large_snapshots": excluded,
        "extracted_non_tar_file_count": len(extracted),
        "official_result_source": "v2_8n_bugsinpy_replacement_preflight_third_scoreable_artifacts.zip",
    }
    write_json(V28N_OUTPUT / "artifact_sha256_verification.json", package)
    write_json(V28N_OUTPUT / "large_workspace_snapshots_index.json", {"excluded_large_snapshots": excluded})
    regenerate_nested_manifests(V28N_OUTPUT)
    return package


def append_summary_block() -> None:
    block = """## v2.8o BugsInPy Broad Preflight Harvest

- Status: `blocked_pending_v2_8o_broad_preflight_harvest_artifact`.
- v2.8n artifact ingested and verified: `31ef78b0f9ea422ac56338dd4369966874b89d9f5fe85d7ad63ea922d9280ca6`.
- v2.8n official result remains: 5 executed, 2 scoreable, 0 positive memory episodes.
- v2.8o broadens candidate discovery beyond Black formatter bugs before repair attempts.
- Candidate promotion, source discovery, and patch construction are not repair success.
- Full scoring remains `NOT_RUN` / disallowed.
- Memory lift is not demonstrated.
- Self-maintaining software is not demonstrated.
"""
    existing = SUMMARY.read_text(encoding="utf-8", errors="replace") if SUMMARY.exists() else ""
    marker = "## v2.8o BugsInPy Broad Preflight Harvest"
    if marker in existing:
        existing = existing[: existing.index(marker)].rstrip() + "\n\n"
    write_text(SUMMARY, existing.rstrip() + "\n\n" + block)


def prepare_v28o(package: dict[str, Any]) -> None:
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    v28n_results = load_json(V28N_OUTPUT / "campaign_results.json")
    v28n_decision = load_json(V28N_OUTPUT / "decision_report.json")
    records = v28n_decision.get("records", [])
    campaign = {
        "workflow_executed": False,
        "campaign_id": "v2_8o_bugsinpy_broad_preflight_harvest",
        "artifact_name": "v2_8o_bugsinpy_broad_preflight_harvest_artifacts",
        "aggregate_result": "blocked_pending_v2_8o_broad_preflight_harvest_artifact",
        "executed_episode_count": 0,
        "scoreable_episode_count": 0,
        "positive_memory_episode_count": 0,
        "broad_preflight_candidate_count": 0,
        "preflight_passing_candidate_count": 0,
        "repair_attempted_replacement_count": 0,
        "full_scoring_allowed": False,
        "controllergate_full_scoring": "NOT_RUN",
        "self_maintaining_software_demonstrated": False,
        "memory_lift_demonstrated": False,
    }
    write_json(OUTPUT_DIR / "campaign_results.json", campaign)
    write_json(OUTPUT_DIR / "aggregate_report.json", campaign)
    write_json(
        OUTPUT_DIR / "aggregate_bugsinpy_real_bug_memory_lift_assessment.json",
        {
            "aggregate_result": campaign["aggregate_result"],
            "minimum_required_scoreable_episodes": 3,
            "scoreable_episode_count": 0,
            "positive_memory_episode_count": 0,
            "limited_bugsinpy_real_bug_memory_lift_criteria_met": False,
            "full_scoring_allowed": False,
            "controllergate_full_scoring": "NOT_RUN",
            "self_maintaining_software_demonstrated": False,
        },
    )
    write_json(
        OUTPUT_DIR / "decision_report.json",
        {
            "records": [],
            "pending_until_linux_workflow_artifact": True,
            "classification_vocabulary": CLASSIFICATION_VOCABULARY,
        },
    )
    write_json(
        OUTPUT_DIR / "candidate_pool.json",
        {
            "baseline_records": BASELINE_RECORDS,
            "broad_replacement_pool": "runtime-discovered from BugsInPy metadata; target at least 20 candidates if available",
            "black_formatter_lane_not_first_choice": True,
        },
    )
    write_json(
        OUTPUT_DIR / "broad_candidate_preflight_registry_v2_8o.json",
        {
            "status": "pending_linux_workflow_execution",
            "minimum_target_candidates_if_available": 20,
            "records": [],
            "decision_time_safe_inputs_only": True,
        },
    )
    write_json(
        OUTPUT_DIR / "replacement_candidate_policy_v2_8o.json",
        {
            "preserve_scoreable_reference_candidates": ["youtube-dl:1", "black:4"],
            "black8_policy": "freeze as non-scoreable unless a preregistered source-only rule exists before repair success observation",
            "black6_policy": "blocked_replay_or_materialization_failure unless all fixture/data dependencies materialize from decision-time-safe sources",
            "black7_policy": "optional only if a bounded decision-time-valid heuristic exists; cannot block broad candidate discovery",
            "broad_preflight_before_repair": True,
            "top_preflight_passing_replacements_to_attempt": 3,
            "fixed_or_gold_patch_used": False,
            "future_outcome_evidence_used": False,
            "selection_after_observing_repair_success": False,
        },
    )
    write_json(
        OUTPUT_DIR / "replacement_candidate_preflight_summary.json",
        {
            "status": "pending_linux_workflow_execution",
            "preflight_required_before_repair_candidate_generation": True,
            "blocked_classification_for_failed_preflight": "blocked_replay_or_materialization_failure",
        },
    )
    write_json(
        OUTPUT_DIR / "fixture_dependency_preflight_summary.json",
        {
            "status": "pending_linux_workflow_execution",
            "required_before_repair": True,
            "missing_fixture_or_data_file_blocks_repair": True,
            "fixed_revision_fixture_copying_allowed": False,
        },
    )
    write_json(
        OUTPUT_DIR / "candidate_ranking_policy_v2_8o.json",
        {
            "signals": [
                "pre_repair_target_failure_reproduces",
                "target_test_file_exists",
                "fixture_data_files_exist",
                "simple_dependency_install",
                "direct_traceback_or_assertion_context",
                "localized_source_discovery",
                "registered_heuristic_family_match",
                "bounded_patch_surface",
                "pure_python_source_only_patch_likely",
                "black_formatter_penalty",
                "avoid_broad_formatter_rewrite",
            ],
            "forbidden_signals": ["fixed_revision", "gold_patch", "future_outcome_logs", "post_repair_success"],
        },
    )
    write_json(
        OUTPUT_DIR / "candidate_source_integrity_check.json",
        {
            "v2_8n_reference_records": records,
            "v2_8n_scoreable_episode_count": v28n_results.get("scoreable_episode_count"),
            "v2_8n_positive_memory_episode_count": v28n_results.get("positive_memory_episode_count"),
            "fixed_or_gold_patch_used_at_decision_time": False,
        },
    )
    write_json(
        OUTPUT_DIR / "decision_time_policy.json",
        {
            "allowed_inputs": [
                "BugsInPy project and bug id",
                "BugsInPy metadata",
                "buggy checkout",
                "target test file path",
                "target test method",
                "failing command",
                "baseline failing log",
                "buggy-source discovery",
                "registered heuristic family match",
            ],
            "forbidden_inputs": ["fixed revision", "gold patch", "future outcome evidence", "post-repair result", "hidden labels"],
        },
    )
    write_json(OUTPUT_DIR / "anti_leakage_policy.json", {"no_fixed_or_gold_patch": True, "no_future_outcome_evidence": True, "tests_may_be_modified": False, "source_only_repair_patch": True})
    write_json(OUTPUT_DIR / "source_discovery_summary.json", {"status": "pending_linux_workflow_execution", "buggy_source_only": True})
    write_json(OUTPUT_DIR / "pre_repair_replay_gate_summary.json", {"status": "pending_linux_workflow_execution", "pre_repair_gate_required": True})
    write_json(OUTPUT_DIR / "workspace_equivalence_summary.json", {"status": "pending_linux_workflow_execution"})
    write_json(OUTPUT_DIR / "source_repair_vs_harness_separation.json", {"source_only_repair_patch_required": True, "tests_may_be_modified_as_repair": False, "runtime_setup_is_not_code_repair": True})
    write_json(OUTPUT_DIR / "classification_vocabulary_check.json", {"allowed_vocabulary": CLASSIFICATION_VOCABULARY, "status": "PENDING_UNTIL_FINAL_RECORDS"})
    write_json(OUTPUT_DIR / "audit.json", {"status": "pending_linux_workflow_execution", "v2_8n_artifact_verified": package.get("zip_sha256_matches_expected") is True})
    write_json(OUTPUT_DIR / "package_verification.json", {"artifact_package": "v2_8o_bugsinpy_broad_preflight_harvest_artifacts", "generated_by": "local v2.8o prep checkpoint", "full_scoring_allowed": False})
    write_json(OUTPUT_DIR / "artifact_sha256_verification.json", {"v2_8n_artifact_verification": package, "v2_8o_zip_sha256_available_after_download": False})
    write_text(
        OUTPUT_DIR / "campaign_summary.md",
        "# v2.8o BugsInPy Broad Preflight Harvest\n\n"
        "Status: `blocked_pending_v2_8o_broad_preflight_harvest_artifact`.\n\n"
        "- v2.8n artifact was ingested and verified locally.\n"
        "- v2.8n official result remains 5 executed, 2 scoreable, 0 positive memory episodes.\n"
        "- v2.8o adds a broad outcome-blind BugsInPy preflight harvest before replacement repairs.\n"
        "- Full scoring remains NOT_RUN / disallowed.\n"
        "- Memory lift is not demonstrated.\n"
        "- Self-maintaining software is not demonstrated.\n",
    )
    write_json(OUTPUT_DIR / "bounded_repair_proposer_summary.json", {"status": "pending_linux_workflow_execution", "bounded_source_only_heuristics_only": True})
    write_manifest(OUTPUT_DIR)


def main() -> int:
    package = ingest_v28n_artifact()
    prepare_v28o(package)
    append_summary_block()
    print("v2.8o broad BugsInPy preflight harvest checkpoint prepared")
    print(f"v2.8n artifact present: {package.get('zip_present')}")
    print("v2.8o status: blocked_pending_v2_8o_broad_preflight_harvest_artifact")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
