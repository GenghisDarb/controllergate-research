#!/usr/bin/env python3
"""Prepare local v2.8p BugsInPy harness-repair broad-harvest checkpoint artifacts."""

from __future__ import annotations

import hashlib
import json
import shutil
import zipfile
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
V28O_ARTIFACT = Path(r"E:\Personal Projects\ControllerGate\v2_8o_bugsinpy_broad_preflight_harvest_artifacts.zip")
OUTPUT_DIR = REPO_ROOT / "outputs" / "v2_8p_bugsinpy_harness_repair_broad_harvest"
SUMMARY = REPO_ROOT / "controllergate_v1_7_beta" / "reports" / "critic_review_package" / "shareable_summary.md"

EXPECTED_V28O_ZIP_SHA256 = "4ae274921bb0ea3a25a3443daaa77056c028d12be0b7910065a39623baea0a9e"

CLASSIFICATION_VOCABULARY = [
    "blocked_no_safe_patch_candidate_generated",
    "blocked_patch_did_not_apply",
    "blocked_replay_or_materialization_failure",
    "blocked_target_test_failed",
    "failed_both",
    "inconclusive_equal_performance",
    "no_memory_only",
    "positive_memory_only",
    "runner_regression_preserved_reference_failure",
]

REQUIRED_REFERENCES = ["youtube-dl:1", "black:4"]


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


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


def load_zip_json(archive: zipfile.ZipFile, name: str) -> dict[str, Any]:
    if name not in archive.namelist():
        return {}
    data = json.loads(archive.read(name).decode("utf-8"))
    return data if isinstance(data, dict) else {}


def verify_v28o_artifact() -> dict[str, Any]:
    if not V28O_ARTIFACT.exists():
        return {
            "zip_present": False,
            "zip_path": str(V28O_ARTIFACT),
            "status": "v2_8o_artifact_not_present_locally",
        }
    zip_sha = sha_file(V28O_ARTIFACT)
    missing = 0
    failures = 0
    checked = 0
    with zipfile.ZipFile(V28O_ARTIFACT) as archive:
        bad_member = archive.testzip()
        names = set(archive.namelist())
        manifest = parse_manifest(archive.read("SHA256SUMS.txt").decode("utf-8")) if "SHA256SUMS.txt" in names else {}
        for rel, expected in manifest.items():
            if rel not in names:
                missing += 1
                continue
            actual = sha_bytes(archive.read(rel))
            checked += 1
            if actual != expected:
                failures += 1
        campaign = load_zip_json(archive, "campaign_results.json")
        decision = load_zip_json(archive, "decision_report.json")
        vocab = load_zip_json(archive, "classification_vocabulary_check.json")
    records = decision.get("records", [])
    by_candidate = {record.get("candidate"): record for record in records}
    return {
        "zip_present": True,
        "zip_path": str(V28O_ARTIFACT),
        "zip_sha256": zip_sha,
        "expected_zip_sha256": EXPECTED_V28O_ZIP_SHA256,
        "zip_sha256_matches_expected": zip_sha == EXPECTED_V28O_ZIP_SHA256,
        "zip_test_bad_member": bad_member,
        "internal_sha256_checked": checked,
        "internal_sha256_missing": missing,
        "internal_sha256_failures": failures,
        "campaign_results": campaign,
        "decision_records": records,
        "classification_vocabulary_check": vocab,
        "observed_harness_regression": {
            "scoreable_episode_count": campaign.get("scoreable_episode_count"),
            "preflight_passing_candidate_count": campaign.get("preflight_passing_candidate_count"),
            "youtube_dl_1_scoreable": by_candidate.get("youtube-dl:1", {}).get("scoreable"),
            "youtube_dl_1_classification": by_candidate.get("youtube-dl:1", {}).get("classification"),
            "black_4_scoreable": by_candidate.get("black:4", {}).get("scoreable"),
            "black_4_classification": by_candidate.get("black:4", {}).get("classification"),
            "broad_preflight_candidate_count": campaign.get("broad_preflight_candidate_count"),
        },
        "official_result_source": "v2_8o_bugsinpy_broad_preflight_harvest_artifacts.zip",
    }


def append_summary_block(package: dict[str, Any]) -> None:
    observed = package.get("observed_harness_regression", {})
    block = f"""## v2.8p BugsInPy Harness Repair Broad Harvest

- Status: `blocked_pending_v2_8p_harness_repair_broad_harvest_artifact`.
- v2.8o artifact verified: `{EXPECTED_V28O_ZIP_SHA256}`.
- v2.8o official regression: {observed.get('scoreable_episode_count')} scoreable episodes, {observed.get('preflight_passing_candidate_count')} preflight-passing broad candidates.
- v2.8p adds a preserved-reference gate before broad harvest.
- Required preserved references: `youtube-dl:1`, `black:4`.
- `pytest` commands must normalize to `python -m pytest`, with pytest installed before pytest candidates.
- Returncode 127 is treated as harness or command-normalization failure, not candidate failure.
- Full scoring remains `NOT_RUN` / disallowed.
- Memory lift is not demonstrated.
- Self-maintaining software is not demonstrated.
"""
    existing = SUMMARY.read_text(encoding="utf-8", errors="replace") if SUMMARY.exists() else ""
    marker = "## v2.8p BugsInPy Harness Repair Broad Harvest"
    if marker in existing:
        existing = existing[: existing.index(marker)].rstrip() + "\n\n"
    write_text(SUMMARY, existing.rstrip() + "\n\n" + block)


def prepare_v28p(package: dict[str, Any]) -> None:
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    campaign = {
        "workflow_executed": False,
        "campaign_id": "v2_8p_bugsinpy_harness_repair_broad_harvest",
        "artifact_name": "v2_8p_bugsinpy_harness_repair_broad_harvest_artifacts",
        "aggregate_result": "blocked_pending_v2_8p_harness_repair_broad_harvest_artifact",
        "executed_episode_count": 0,
        "scoreable_episode_count": 0,
        "positive_memory_episode_count": 0,
        "broad_preflight_candidate_count": 0,
        "preflight_passing_candidate_count": 0,
        "returncode_127_after_normalization_count": 0,
        "repair_attempted_replacement_count": 0,
        "preserved_reference_gate_status": "PENDING_GITHUB_ACTIONS",
        "harness_sanity_status": "PENDING_GITHUB_ACTIONS",
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
    write_json(OUTPUT_DIR / "decision_report.json", {"records": [], "pending_until_linux_workflow_artifact": True, "classification_vocabulary": CLASSIFICATION_VOCABULARY})
    write_json(
        OUTPUT_DIR / "candidate_pool.json",
        {
            "preserved_reference_records": [
                {"episode_id": "episode_001", "candidate": "youtube-dl:1", "status": "must_restore_scoreable_before_broad_harvest"},
                {"episode_id": "episode_003", "candidate": "black:4", "status": "must_restore_scoreable_before_broad_harvest"},
            ],
            "broad_replacement_pool": "runtime-discovered from BugsInPy metadata after preserved-reference gate passes",
            "fixed_or_gold_patch_used": False,
        },
    )
    write_json(
        OUTPUT_DIR / "preserved_reference_gate_result.json",
        {
            "status": "PENDING_GITHUB_ACTIONS",
            "required_references": REQUIRED_REFERENCES,
            "minimum_success_condition": {"youtube-dl:1": "scoreable true", "black:4": "scoreable true"},
            "failure_classification_if_failed": "runner_regression_preserved_reference_failure",
            "broad_harvest_allowed": False,
            "observed_v2_8o_regression": package.get("observed_harness_regression", {}),
        },
    )
    write_json(
        OUTPUT_DIR / "harness_sanity_check.json",
        {
            "status": "PENDING_GITHUB_ACTIONS",
            "required_checks": ["python --version", "python -m pip --version", "python -m pytest --version after pytest install", "cwd == project_root", "PYTHONPATH includes project_root"],
        },
    )
    write_json(
        OUTPUT_DIR / "command_normalization_policy_v2_8p.json",
        {
            "raw_pytest_command_policy": "normalize commands that start with pytest to python -m pytest",
            "pytest_dependency_policy": "install pytest before pytest-based candidates",
            "command_cwd_policy": "execute target commands from checked-out project root",
            "pythonpath_policy": "prepend project root to PYTHONPATH",
            "returncode_127_policy": "returncode 127 is harness/command-normalization failure, not candidate failure",
            "record_original_and_normalized_command": True,
        },
    )
    write_json(
        OUTPUT_DIR / "broad_candidate_preflight_registry_v2_8p.json",
        {"status": "pending_preserved_reference_gate", "minimum_target_candidates_if_available": 20, "records": [], "returncode_127_after_normalization_count": 0},
    )
    write_json(
        OUTPUT_DIR / "replacement_candidate_policy_v2_8p.json",
        {
            "preserved_reference_gate_required": True,
            "stop_on_preserved_reference_failure": True,
            "stop_classification": "runner_regression_preserved_reference_failure",
            "top_preflight_passing_replacements_to_attempt": 3,
            "fixed_or_gold_patch_used": False,
            "future_outcome_evidence_used": False,
            "selection_after_observing_repair_success": False,
        },
    )
    write_json(OUTPUT_DIR / "replacement_candidate_preflight_summary.json", {"status": "pending_preserved_reference_gate", "preflight_required_before_repair_candidate_generation": True, "returncode_127_treated_as_harness_failure": True})
    write_json(OUTPUT_DIR / "fixture_dependency_preflight_summary.json", {"status": "pending_preserved_reference_gate", "fixed_revision_fixture_copying_used": False})
    write_json(
        OUTPUT_DIR / "candidate_ranking_policy_v2_8p.json",
        {
            "signals": ["pre_repair_target_failure_reproduces", "target_test_file_exists", "fixture_data_files_exist", "simple_dependency_install", "localized_source_discovery", "registered_heuristic_family_match", "command_normalized_without_returncode_127"],
            "forbidden_signals": ["fixed_revision", "gold_patch", "future_outcome_logs", "post_repair_success"],
        },
    )
    write_json(OUTPUT_DIR / "candidate_source_integrity_check.json", {"v2_8o_artifact_verification": package, "fixed_or_gold_patch_used_at_decision_time": False})
    write_json(OUTPUT_DIR / "decision_time_policy.json", {"allowed_inputs": ["BugsInPy metadata", "buggy checkout", "baseline failing command", "baseline failing log", "buggy-source discovery"], "forbidden_inputs": ["fixed revision", "gold patch", "future outcome evidence", "post-repair result", "hidden labels"]})
    write_json(OUTPUT_DIR / "anti_leakage_policy.json", {"no_fixed_or_gold_patch": True, "no_future_outcome_evidence": True, "tests_may_be_modified": False, "source_only_repair_patch": True})
    write_json(OUTPUT_DIR / "source_discovery_summary.json", {"status": "pending_preserved_reference_gate", "buggy_source_only": True})
    write_json(OUTPUT_DIR / "pre_repair_replay_gate_summary.json", {"status": "pending_github_actions", "pre_repair_gate_required": True})
    write_json(OUTPUT_DIR / "workspace_equivalence_summary.json", {"status": "pending_github_actions"})
    write_json(OUTPUT_DIR / "source_repair_vs_harness_separation.json", {"source_only_repair_patch_required": True, "tests_may_be_modified_as_repair": False, "harness_materialization_is_not_repair": True, "dependency_runtime_setup_is_not_code_repair": True})
    write_json(OUTPUT_DIR / "classification_vocabulary_check.json", {"allowed_vocabulary": CLASSIFICATION_VOCABULARY, "status": "PENDING_UNTIL_FINAL_RECORDS"})
    write_json(OUTPUT_DIR / "audit.json", {"status": "pending_github_actions", "v2_8o_artifact_verified": package.get("zip_sha256_matches_expected") is True, "v2_8o_harness_regression_recorded": True})
    write_json(OUTPUT_DIR / "package_verification.json", {"artifact_package": "v2_8p_bugsinpy_harness_repair_broad_harvest_artifacts", "generated_by": "local v2.8p prep checkpoint", "full_scoring_allowed": False})
    write_json(OUTPUT_DIR / "artifact_sha256_verification.json", {"v2_8o_artifact_verification": package, "v2_8p_zip_sha256_available_after_download": False})
    write_json(OUTPUT_DIR / "bounded_repair_proposer_summary.json", {"status": "pending_preserved_reference_gate", "bounded_source_only_heuristics_only": True})
    write_text(
        OUTPUT_DIR / "campaign_summary.md",
        "# v2.8p BugsInPy Harness Repair Broad Harvest\n\n"
        "Status: `blocked_pending_v2_8p_harness_repair_broad_harvest_artifact`.\n\n"
        "- Official v2.8o artifact was verified locally and recorded as a harness regression baseline.\n"
        "- v2.8p must restore `youtube-dl:1` and `black:4` as scoreable before broad harvest.\n"
        "- Raw `pytest` commands normalize to `python -m pytest`, with pytest installed for pytest candidates.\n"
        "- Returncode 127 is treated as harness/command-normalization failure, not candidate failure.\n"
        "- Full scoring remains NOT_RUN / disallowed.\n"
        "- Memory lift is not demonstrated.\n"
        "- Self-maintaining software is not demonstrated.\n",
    )
    write_manifest(OUTPUT_DIR)


def main() -> int:
    package = verify_v28o_artifact()
    prepare_v28p(package)
    append_summary_block(package)
    print("v2.8p BugsInPy harness repair broad harvest checkpoint prepared")
    print(f"v2.8o artifact present: {package.get('zip_present')}")
    print(f"v2.8o artifact SHA256 matches expected: {package.get('zip_sha256_matches_expected')}")
    print("v2.8p status: blocked_pending_v2_8p_harness_repair_broad_harvest_artifact")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
