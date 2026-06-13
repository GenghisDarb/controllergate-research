#!/usr/bin/env python3
"""Prepare local v2.8m replacement third-scoreable checkpoint artifacts."""

from __future__ import annotations

import hashlib
import json
import shutil
import zipfile
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
PYTHON_ARTIFACT = Path(r"C:\Users\thisb\Downloads\v2_8l_bugsinpy_third_scoreable_recovery_artifacts.zip")
V28L_OUTPUT = REPO_ROOT / "outputs" / "v2_8l_bugsinpy_third_scoreable_recovery"
OUTPUT_DIR = REPO_ROOT / "outputs" / "v2_8m_bugsinpy_replacement_third_scoreable"
SUMMARY = REPO_ROOT / "controllergate_v1_7_beta" / "reports" / "critic_review_package" / "shareable_summary.md"

EXPECTED_V28L_ZIP_SHA256 = "d1a7792daf2b65dc589fa32dcd0854401bd775c67d2e5eaa7493c39e5d3eeafe"
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

CANDIDATES = [
    {"episode_id": "episode_001", "candidate": "youtube-dl:1", "status": "preserved_scoreable"},
    {"episode_id": "episode_002", "candidate": "black:8", "status": "frozen_failed_both"},
    {"episode_id": "episode_003", "candidate": "black:4", "status": "preserved_scoreable"},
    {"episode_id": "episode_004", "candidate": "black:6", "status": "selected_outcome_blind_replacement"},
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


def ingest_v28l_artifact() -> dict[str, Any]:
    if not PYTHON_ARTIFACT.exists():
        return {
            "zip_present": False,
            "zip_path": str(PYTHON_ARTIFACT),
            "status": "v2_8l_artifact_not_present_locally",
        }
    zip_sha = sha_file(PYTHON_ARTIFACT)
    if V28L_OUTPUT.exists():
        shutil.rmtree(V28L_OUTPUT)
    V28L_OUTPUT.mkdir(parents=True, exist_ok=True)
    excluded: list[dict[str, Any]] = []
    extracted: list[str] = []
    missing = 0
    failures = 0
    checked = 0
    with zipfile.ZipFile(PYTHON_ARTIFACT) as archive:
        bad_member = archive.testzip()
        manifest_name = "SHA256SUMS.txt"
        manifest = parse_manifest(archive.read(manifest_name).decode("utf-8"))
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
            target = V28L_OUTPUT / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(archive.read(rel))
            extracted.append(rel)
    package = {
        "zip_present": True,
        "zip_path": str(PYTHON_ARTIFACT),
        "zip_sha256": zip_sha,
        "expected_zip_sha256": EXPECTED_V28L_ZIP_SHA256,
        "zip_sha256_matches_expected": zip_sha == EXPECTED_V28L_ZIP_SHA256,
        "zip_test_bad_member": bad_member,
        "internal_sha256_checked": checked,
        "internal_sha256_missing": missing,
        "internal_sha256_failures": failures,
        "excluded_large_snapshots": excluded,
        "extracted_non_tar_file_count": len(extracted),
        "official_result_source": "v2_8l_bugsinpy_third_scoreable_recovery_artifacts.zip",
    }
    write_json(V28L_OUTPUT / "artifact_sha256_verification.json", package)
    write_json(
        V28L_OUTPUT / "package_verification.json",
        {
            "artifact_package": "v2_8l_bugsinpy_third_scoreable_recovery_artifacts.zip",
            "raw_artifact_audit_provenance_stale": True,
            "raw_artifact_audit_provenance_value": load_json(V28L_OUTPUT / "audit.json").get("artifact_provenance"),
            "corrected_interpretation": "official v2.8l Linux artifact result; stale audit provenance is not carried into v2.8m",
            "full_scoring_allowed": False,
        },
    )
    write_json(V28L_OUTPUT / "large_workspace_snapshots_index.json", {"excluded": excluded, "committed_to_repo": False})
    write_json(
        V28L_OUTPUT / "candidate_pool.json",
        {
            "count": 3,
            "records": [
                {"episode_id": "episode_001", "candidate": "youtube-dl:1", "status": "preserved_scoreable"},
                {"episode_id": "episode_002", "candidate": "black:8", "status": "failed_both"},
                {"episode_id": "episode_003", "candidate": "black:4", "status": "preserved_scoreable"},
            ],
            "source": "added during v2.8m artifact hygiene ingestion from official v2.8l decision report",
        },
    )
    write_text(
        V28L_OUTPUT / "github_actions_usage_instructions.md",
        "# v2.8l GitHub Actions Usage\n\n"
        "Run workflow `v2_8l_bugsinpy_third_scoreable_recovery` on branch "
        "`controllergate-v1.7-alpha-real-trace-pilot`.\n\n"
        "Expected artifact: `v2_8l_bugsinpy_third_scoreable_recovery_artifacts`.\n",
    )
    decision_policy = load_json(V28L_OUTPUT / "decision_time_policy.json")
    decision_policy.update(
        {
            "test_edits_forbidden": True,
            "source_only_repair_required": True,
            "fixed_or_gold_patch_forbidden": True,
            "future_outcome_evidence_forbidden": True,
        }
    )
    write_json(V28L_OUTPUT / "decision_time_policy.json", decision_policy)
    write_manifest(V28L_OUTPUT)
    return package


def replacement_pool_sha() -> str:
    pool = [
        {"candidate": "black:6", "status": "selected_outcome_blind_replacement"},
        {"candidate": "black:5", "status": "excluded_fixed_patch_exposure"},
        {"candidate": "black:1", "status": "excluded_prior_runtime_blocked"},
        {"candidate": "black:3", "status": "excluded_prior_runtime_blocked"},
    ]
    return hashlib.sha256(json.dumps(pool, sort_keys=True).encode("utf-8")).hexdigest()


def prepare_v28m(v28l_package: dict[str, Any]) -> None:
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    v28l_results = load_json(V28L_OUTPUT / "campaign_results.json")
    v28l_decision = load_json(V28L_OUTPUT / "decision_report.json")
    write_json(
        OUTPUT_DIR / "campaign_plan.json",
        {
            "campaign_id": "v2_8m_bugsinpy_replacement_third_scoreable",
            "workflow": ".github/workflows/v2_8m_bugsinpy_replacement_third_scoreable.yml",
            "runner": "scripts/v2_8m_bugsinpy_replacement_third_scoreable_runner.py",
            "candidate_ids": [item["candidate"] for item in CANDIDATES],
            "local_status": "blocked_pending_v2_8m_replacement_artifact",
            "full_scoring_allowed": False,
            "controllergate_full_scoring": "NOT_RUN",
            "self_maintaining_software_demonstrated": False,
        },
    )
    write_json(OUTPUT_DIR / "candidate_pool.json", {"count": len(CANDIDATES), "records": CANDIDATES})
    write_json(
        OUTPUT_DIR / "replacement_candidate_policy_v2_8m.json",
        {
            "why_black8_was_frozen_as_failed_both": "v2.8l generated and applied a compact source-only black:8 patch, but the post-repair target validation still failed.",
            "selection_pool_considered": [
                {"candidate": "black:6", "status": "selected_outcome_blind_replacement"},
                {"candidate": "black:5", "status": "excluded_fixed_patch_exposure"},
                {"candidate": "black:1", "status": "excluded_prior_runtime_blocked"},
                {"candidate": "black:3", "status": "excluded_prior_runtime_blocked"},
            ],
            "selection_filters": [
                "pure Python BugsInPy candidate",
                "not previously dependency/runtime blocked if avoidable",
                "no fixed/gold/future outcome evidence for selected candidate",
                "target command discovered from BugsInPy metadata or buggy checkout",
                "source-only patch required",
            ],
            "selected_replacement_candidate": "black:6",
            "evidence_available_at_decision_time": [
                "BugsInPy project/bug id",
                "run_test.sh or target command from BugsInPy metadata",
                "buggy checkout baseline failing log",
                "traceback/source discovery from buggy source",
            ],
            "gold_fixed_or_future_evidence_used": False,
            "replacement_candidate_selected_before_repair_outcome": True,
            "preregistered_candidate_pool_sha256": replacement_pool_sha(),
        },
    )
    write_json(
        OUTPUT_DIR / "campaign_results.json",
        {
            "workflow_executed": False,
            "executed_episode_count": 0,
            "scoreable_episode_count": 0,
            "positive_memory_episode_count": 0,
            "aggregate_result": "blocked_pending_v2_8m_replacement_artifact",
            "limited_bugsinpy_real_bug_memory_lift_criteria_met": False,
            "full_scoring_allowed": False,
            "controllergate_full_scoring": "NOT_RUN",
            "self_maintaining_software_demonstrated": False,
            "v2_8l_official_result": v28l_results,
        },
    )
    write_json(
        OUTPUT_DIR / "decision_report.json",
        {
            "records": [],
            "pending_linux_artifact": True,
            "v2_8l_episode_records": v28l_decision.get("records", []),
            "classification_vocabulary": CLASSIFICATION_VOCABULARY,
        },
    )
    write_json(
        OUTPUT_DIR / "aggregate_report.json",
        {
            "aggregate_result": "blocked_pending_v2_8m_replacement_artifact",
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
            "aggregate_result": "blocked_pending_v2_8m_replacement_artifact",
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
        "bounded_repair_proposer_summary.json": {"pending_linux_artifact": True, "replacement_candidate": "black:6"},
        "candidate_source_integrity_check.json": {"candidate_pool": CANDIDATES, "blocked_candidates_not_counted": ["black:8"]},
        "decision_time_policy.json": {"fixed_or_gold_patch_forbidden": True, "future_outcome_evidence_forbidden": True, "post_repair_outcomes_forbidden_for_selection": True},
        "anti_leakage_policy.json": {"no_fixed_or_gold_patch": True, "no_future_outcome_evidence": True, "black5_excluded_due_fixed_patch_exposure": True},
        "source_discovery_summary.json": {"pending_linux_artifact": True},
        "pre_repair_replay_gate_summary.json": {"pending_linux_artifact": True},
        "workspace_equivalence_summary.json": {"pending_linux_artifact": True},
        "source_repair_vs_harness_separation.json": {"source_only_repair_patch_required": True, "tests_may_be_modified": False},
        "audit.json": {"artifact_provenance": "prepared by v2.8m local checkpoint", "pending_linux_artifact": True},
        "package_verification.json": {"artifact_package": "pending v2_8m_bugsinpy_replacement_third_scoreable_artifacts", "full_scoring_allowed": False},
        "artifact_sha256_verification.json": {"status": "pending_workflow_artifact", "source_v2_8l_package": v28l_package},
    }.items():
        write_json(OUTPUT_DIR / name, data)
    write_text(
        OUTPUT_DIR / "campaign_summary.md",
        "# v2.8m BugsInPy Replacement Third Scoreable Episode\n\n"
        "Local checkpoint status: `blocked_pending_v2_8m_replacement_artifact`.\n\n"
        "- Official v2.8l result: 3 executed, 2 scoreable, 0 positive memory episodes.\n"
        "- black:8 is frozen as `failed_both`.\n"
        "- Replacement candidate selected outcome-blind: `black:6`.\n"
        "- Full scoring: NOT_RUN / disallowed.\n"
        "- Memory lift: not demonstrated.\n"
        "- Self-maintaining software: not demonstrated.\n",
    )
    write_manifest(OUTPUT_DIR)


def update_summary() -> None:
    section = """## v2.8m BugsInPy Replacement Third Scoreable Episode

v2.8m preserves the official v2.8l Linux result and moves to an outcome-blind replacement candidate instead of repeatedly tuning `black:8`.

- v2.8l official result: 3 executed, 2 scoreable, 0 positive memory episodes.
- `black:8`: frozen as `failed_both`.
- Preserved scoreable episodes: `youtube-dl:1`, `black:4`.
- v2.8m replacement candidate: `black:6`.
- v2.8m local status: `blocked_pending_v2_8m_replacement_artifact`.
- Full scoring: NOT_RUN / disallowed.
- Memory lift: not demonstrated.
- Self-maintaining software: not demonstrated.

Candidate promotion or candidate selection is not repair success. v2.8m requires a fresh Linux artifact before any scoreable-count or memory-lift update.
"""
    text = SUMMARY.read_text(encoding="utf-8") if SUMMARY.exists() else ""
    marker = "## v2.8m BugsInPy Replacement Third Scoreable Episode"
    if marker in text:
        start = text.index(marker)
        next_start = text.find("\n## ", start + 1)
        tail = text[next_start:].lstrip() if next_start != -1 else ""
        text = text[:start].rstrip() + "\n\n" + section + ("\n\n" + tail if tail else "")
    else:
        text = text.rstrip() + "\n\n" + section
    write_text(SUMMARY, text)


def main() -> int:
    package = ingest_v28l_artifact()
    prepare_v28m(package)
    update_summary()
    print("v2.8m BugsInPy replacement third scoreable checkpoint prepared")
    print(f"v2.8l artifact present: {package.get('zip_present')}")
    print("v2.8m status: blocked_pending_v2_8m_replacement_artifact")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
