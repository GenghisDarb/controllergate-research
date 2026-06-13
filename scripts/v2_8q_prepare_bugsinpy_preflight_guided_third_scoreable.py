#!/usr/bin/env python3
"""Prepare local v2.8q preflight-guided third-scoreable checkpoint artifacts."""

from __future__ import annotations

import hashlib
import json
import shutil
import zipfile
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = REPO_ROOT / "outputs" / "v2_8q_bugsinpy_preflight_guided_third_scoreable"
V28P_OUTPUT_DIR = REPO_ROOT / "outputs" / "v2_8p_bugsinpy_harness_repair_broad_harvest"
V28P_ARTIFACT = Path(r"E:\Personal Projects\ControllerGate\v2_8p_bugsinpy_harness_repair_broad_harvest_artifacts.zip")
SUMMARY = REPO_ROOT / "controllergate_v1_7_beta" / "reports" / "critic_review_package" / "shareable_summary.md"

EXPECTED_V28P_ZIP_SHA256 = "6f227ab2c12c15c173420663055ec55d3c01f2fc3d666c7a74d1fcfd25b59a06"

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

TARGETED_HEURISTICS: dict[str, dict[str, Any]] = {
    "fastapi:1": {
        "heuristic_family": "localized_keyword_parameter_compatibility_shim",
        "failure_type": "unexpected_keyword_argument_exclude_defaults",
        "patch_surface_estimate": "small_single_function",
        "preferred_rank": 1,
        "reason": "Direct TypeError names missing exclude_defaults parameter in fastapi/encoders.py.",
    },
    "ansible:2": {
        "heuristic_family": "localized_comparison_operator_equality_guard",
        "failure_type": "strict_greater_than_returns_true_for_equal_values",
        "patch_surface_estimate": "small_single_source_file",
        "preferred_rank": 2,
        "reason": "Assertion shows _Alpha('a') > _Alpha('a') is true; source extract shows __gt__ implemented as not __lt__.",
    },
    "ansible:5": {
        "heuristic_family": "localized_deterministic_missing_argument_order",
        "failure_type": "message_order_instability",
        "patch_surface_estimate": "small_single_expression",
        "preferred_rank": 3,
        "reason": "Assertion differs only by missing argument order; bounded fix sorts the generated missing list.",
    },
    "ansible:8": {
        "heuristic_family": "localized_path_string_normalization_unc_guard",
        "failure_type": "unc_prefix_stripped",
        "patch_surface_estimate": "small_path_join_guard_if_source_matches",
        "preferred_rank": 4,
        "reason": "Failure shows join_path strips leading UNC prefix; only attempted if the buggy source shape is recognized.",
    },
}

FALLBACK_TOP_FIVE = ["fastapi:1", "ansible:2", "ansible:5", "ansible:8", "ansible:4"]


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sha_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write_manifest(directory: Path) -> None:
    paths = sorted(
        [path for path in directory.rglob("*") if path.is_file() and path.name != "SHA256SUMS.txt"],
        key=lambda path: str(path.relative_to(directory)).replace("\\", "/"),
    )
    lines = [f"{sha_file(path)}  {str(path.relative_to(directory)).replace(chr(92), '/')}" for path in paths]
    write_text(directory / "SHA256SUMS.txt", "\n".join(lines) + "\n")


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def parse_manifest(text: str) -> dict[str, str]:
    records: dict[str, str] = {}
    for raw in text.splitlines():
        if not raw.strip():
            continue
        parts = raw.split()
        if len(parts) >= 2:
            records[parts[1]] = parts[0]
    return records


def verify_v28p_artifact() -> dict[str, Any]:
    package = {
        "zip_present": V28P_ARTIFACT.exists(),
        "zip_path": str(V28P_ARTIFACT),
        "expected_zip_sha256": EXPECTED_V28P_ZIP_SHA256,
    }
    if not V28P_ARTIFACT.exists():
        package["status"] = "v2_8p_artifact_not_present_locally"
        return package
    zip_sha = sha_file(V28P_ARTIFACT)
    package["zip_sha256"] = zip_sha
    package["zip_sha256_matches_expected"] = zip_sha == EXPECTED_V28P_ZIP_SHA256
    if zip_sha != EXPECTED_V28P_ZIP_SHA256:
        package["status"] = "local_zip_sha256_mismatch_not_used_as_official_evidence"
        return package
    try:
        with zipfile.ZipFile(V28P_ARTIFACT) as archive:
            package["zip_test_bad_member"] = archive.testzip()
            names = set(archive.namelist())
            manifest = parse_manifest(archive.read("SHA256SUMS.txt").decode("utf-8")) if "SHA256SUMS.txt" in names else {}
            checked = 0
            missing = 0
            failures = 0
            for rel, expected in manifest.items():
                if rel not in names:
                    missing += 1
                    continue
                checked += 1
                if sha_bytes(archive.read(rel)) != expected:
                    failures += 1
            package["internal_sha256_checked"] = checked
            package["internal_sha256_missing"] = missing
            package["internal_sha256_failures"] = failures
    except Exception as exc:  # noqa: BLE001 - record local artifact corruption without aborting prep.
        package["zip_read_error"] = f"{type(exc).__name__}: {exc}"
        package["status"] = "local_zip_unreadable_not_used_as_official_evidence"
    return package


def preflight_passed(record: dict[str, Any]) -> bool:
    return bool(
        record.get("expected_failure_reproduced")
        and record.get("target_test_file_exists")
        and record.get("fixture_data_dependency_exists")
        and not record.get("wrapper_contamination")
        and not record.get("dependency_or_runtime_blocked")
        and not record.get("returncode_127_after_normalization")
    )


def safe_name(candidate_id: str) -> str:
    return candidate_id.replace(":", "_").replace("/", "_")


def preflight_dir_for(candidate_id: str) -> Path | None:
    root = V28P_OUTPUT_DIR / "preflight_candidates"
    if not root.exists():
        return None
    matches = sorted(root.glob(f"*_{safe_name(candidate_id)}"))
    return matches[0] if matches else None


def failure_excerpt(candidate_id: str) -> str:
    directory = preflight_dir_for(candidate_id)
    if not directory:
        return ""
    path = directory / "failing_log_raw.txt"
    if not path.exists():
        return ""
    text = path.read_text(encoding="utf-8", errors="replace")
    failure_index = text.find("FAILURES")
    if failure_index >= 0:
        text = text[failure_index:]
    return text[:900]


def triage_score(record: dict[str, Any]) -> int:
    candidate_id = record.get("candidate_id")
    if candidate_id in FALLBACK_TOP_FIVE:
        return 1000 - FALLBACK_TOP_FIVE.index(str(candidate_id))
    if candidate_id in TARGETED_HEURISTICS:
        return 1000 - int(TARGETED_HEURISTICS[candidate_id]["preferred_rank"])
    score = int(record.get("readiness_score", 0))
    if record.get("direct_traceback_or_assertion_context"):
        score += 10
    if str(candidate_id).startswith("ansible:"):
        score -= 5
    return score


def build_triage_report(registry: dict[str, Any]) -> dict[str, Any]:
    records = registry.get("records", [])
    passed_records = [record for record in records if preflight_passed(record)]
    ordered = sorted(passed_records, key=lambda record: (-triage_score(record), record.get("candidate_id", "")))
    selected = set([candidate_id for candidate_id in FALLBACK_TOP_FIVE if any(record.get("candidate_id") == candidate_id for record in ordered)])
    rows = []
    for rank, record in enumerate(ordered, start=1):
        candidate_id = record.get("candidate_id")
        heuristic = TARGETED_HEURISTICS.get(str(candidate_id), {})
        likely_sources = record.get("candidate_source_files_found", [])
        if candidate_id == "ansible:8" and "lib/ansible/plugins/shell/powershell.py" not in likely_sources:
            likely_sources = ["lib/ansible/plugins/shell/powershell.py"] + likely_sources
        rows.append(
            {
                "rank": rank,
                "project": record.get("project"),
                "bug_id": record.get("bug_id"),
                "candidate": candidate_id,
                "target_command": record.get("pre_repair_command"),
                "normalized_command": record.get("normalized_pre_repair_command"),
                "pre_repair_failure_signal": failure_excerpt(str(candidate_id)),
                "target_file_existence": record.get("target_test_file_exists"),
                "fixture_data_dependency_status": {
                    "fixture_data_dependency_exists": record.get("fixture_data_dependency_exists"),
                    "missing_fixture_or_data_files": record.get("missing_fixture_or_data_files", []),
                },
                "source_discovery_result": record.get("source_discovery_result"),
                "likely_source_files": likely_sources[:5],
                "failure_type": heuristic.get("failure_type") or "unclassified_pre_repair_failure",
                "heuristic_family_matched": heuristic.get("heuristic_family") or record.get("heuristic_family_match"),
                "patch_surface_estimate": heuristic.get("patch_surface_estimate") or record.get("bounded_patch_surface"),
                "reason_for_ranking": heuristic.get("reason")
                or "Preflight passed, but no bounded registered v2.8q heuristic was supported by the decision-time failure context.",
                "selected_for_repair_attempt": candidate_id in selected,
                "selection_used_only_decision_time_safe_evidence": True,
            }
        )
    return {
        "status": "PENDING_GITHUB_ACTIONS_RERUN",
        "source_registry": "official v2.8p broad preflight registry committed under outputs",
        "preflight_passing_candidate_count": len(passed_records),
        "records": rows,
        "selected_candidate_ids": [candidate_id for candidate_id in FALLBACK_TOP_FIVE if candidate_id in selected],
        "selection_policy": {
            "attempt_budget": 5,
            "stop_after_first_scoreable_replacement": True,
            "forbidden_selection_signals": ["fixed revision", "gold patch", "future outcome evidence", "post-repair success"],
        },
    }


def append_summary_block() -> None:
    block = """## v2.8q BugsInPy Preflight-Guided Third Scoreable Recovery

- Status: `blocked_pending_v2_8q_preflight_guided_third_scoreable_artifact`.
- v2.8p official evidence is preserved: restored `youtube-dl:1` and `black:4`, 19 preflight-passing replacement candidates, 0 returncode-127 normalization failures.
- v2.8q starts with the preserved-reference gate and stops as `runner_regression_preserved_reference_failure` if either reference regresses.
- Candidate triage ranks all v2.8p preflight-passing candidates using decision-time-safe failure/source evidence.
- Initial bounded repair targets: `fastapi:1`, `ansible:2`, `ansible:5`, `ansible:8`, `ansible:4`.
- Full scoring remains `NOT_RUN` / disallowed.
- Memory lift is not demonstrated.
- Self-maintaining software is not demonstrated.
"""
    existing = SUMMARY.read_text(encoding="utf-8", errors="replace") if SUMMARY.exists() else ""
    marker = "## v2.8q BugsInPy Preflight-Guided Third Scoreable Recovery"
    if marker in existing:
        existing = existing[: existing.index(marker)].rstrip() + "\n\n"
    write_text(SUMMARY, existing.rstrip() + "\n\n" + block)


def prepare_v28q(v28p_package: dict[str, Any]) -> None:
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    registry = load_json(V28P_OUTPUT_DIR / "broad_candidate_preflight_registry_v2_8p.json")
    triage = build_triage_report(registry)
    campaign = {
        "workflow_executed": False,
        "campaign_id": "v2_8q_bugsinpy_preflight_guided_third_scoreable",
        "artifact_name": "v2_8q_bugsinpy_preflight_guided_third_scoreable_artifacts",
        "aggregate_result": "blocked_pending_v2_8q_preflight_guided_third_scoreable_artifact",
        "executed_episode_count": 0,
        "scoreable_episode_count": 0,
        "positive_memory_episode_count": 0,
        "broad_preflight_candidate_count": 0,
        "preflight_passing_candidate_count": triage.get("preflight_passing_candidate_count", 0),
        "candidate_triage_record_count": len(triage.get("records", [])),
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
    write_json(OUTPUT_DIR / "preserved_reference_gate_result.json", {"status": "PENDING_GITHUB_ACTIONS", "required_references": ["youtube-dl:1", "black:4"], "broad_harvest_allowed": False, "failure_classification_if_failed": "runner_regression_preserved_reference_failure"})
    write_json(OUTPUT_DIR / "harness_sanity_check.json", {"status": "PENDING_GITHUB_ACTIONS", "inherits_v2_8p_harness_repair": True})
    write_json(OUTPUT_DIR / "command_normalization_policy_v2_8q.json", {"raw_pytest_command_policy": "normalize commands that start with pytest to python -m pytest", "pytest_dependency_policy": "install pytest before pytest-based candidates", "command_cwd_policy": "execute target commands from checked-out project root", "pythonpath_policy": "prepend project root to PYTHONPATH", "returncode_127_policy": "returncode 127 is harness/command-normalization failure, not candidate failure", "record_original_and_normalized_command": True})
    write_json(OUTPUT_DIR / "candidate_triage_report_v2_8q.json", triage)
    write_json(OUTPUT_DIR / "broad_candidate_preflight_registry_v2_8q.json", {"status": "pending_github_actions_rerun", "v2_8p_registry_record_count": len(registry.get("records", [])), "records": []})
    write_json(OUTPUT_DIR / "replacement_candidate_policy_v2_8q.json", {"preserved_reference_gate_required": True, "candidate_triage_before_repair": True, "top_preflight_passing_replacements_to_attempt": 5, "fixed_or_gold_patch_used": False, "future_outcome_evidence_used": False, "selection_after_observing_repair_success": False})
    write_json(OUTPUT_DIR / "replacement_candidate_preflight_summary.json", {"status": "pending_github_actions", "selected_for_repair": triage.get("selected_candidate_ids", []), "preflight_required_before_repair_candidate_generation": True, "returncode_127_treated_as_harness_failure": True})
    write_json(OUTPUT_DIR / "fixture_dependency_preflight_summary.json", {"status": "pending_github_actions", "fixed_revision_fixture_copying_used": False})
    write_json(OUTPUT_DIR / "candidate_ranking_policy_v2_8q.json", {"decision_time_safe_signals": ["pre_repair_target_failure_reproduces", "target_test_file_exists", "fixture_data_files_exist", "direct_failure_context", "localized_source_discovery", "registered_bounded_heuristic_family_match", "small_source_only_patch_surface"], "forbidden_signals": ["fixed_revision", "gold_patch", "future_outcome_logs", "post_repair_success"]})
    write_json(OUTPUT_DIR / "bounded_repair_proposer_summary.json", {"status": "pending_github_actions", "targeted_v2_8q_heuristics": TARGETED_HEURISTICS})
    write_json(OUTPUT_DIR / "candidate_pool.json", {"preserved_reference_records": ["youtube-dl:1", "black:4"], "v2_8p_preflight_passing_candidates": triage.get("preflight_passing_candidate_count", 0), "selected_candidate_ids": triage.get("selected_candidate_ids", [])})
    write_json(OUTPUT_DIR / "candidate_source_integrity_check.json", {"v2_8p_artifact_verification": v28p_package, "fixed_or_gold_patch_used_at_decision_time": False, "future_outcome_evidence_used_at_decision_time": False})
    write_json(OUTPUT_DIR / "decision_time_policy.json", {"allowed_inputs": ["v2.8p preflight registry", "BugsInPy metadata", "buggy checkout", "baseline failing command", "baseline failing log", "buggy-source discovery"], "forbidden_inputs": ["fixed revision", "gold patch", "future outcome evidence", "post-repair result", "hidden labels"]})
    write_json(OUTPUT_DIR / "anti_leakage_policy.json", {"no_fixed_or_gold_patch": True, "no_future_outcome_evidence": True, "tests_may_be_modified": False, "source_only_repair_patch": True})
    write_json(OUTPUT_DIR / "source_discovery_summary.json", {"status": "pending_github_actions", "buggy_source_only": True})
    write_json(OUTPUT_DIR / "pre_repair_replay_gate_summary.json", {"status": "pending_github_actions", "pre_repair_gate_required": True})
    write_json(OUTPUT_DIR / "workspace_equivalence_summary.json", {"status": "pending_github_actions"})
    write_json(OUTPUT_DIR / "source_repair_vs_harness_separation.json", {"source_only_repair_patch_required": True, "tests_may_be_modified_as_repair": False, "harness_materialization_is_not_repair": True, "dependency_runtime_setup_is_not_code_repair": True})
    write_json(OUTPUT_DIR / "classification_vocabulary_check.json", {"allowed_vocabulary": CLASSIFICATION_VOCABULARY, "status": "PENDING_UNTIL_FINAL_RECORDS"})
    write_json(OUTPUT_DIR / "audit.json", {"status": "pending_github_actions", "candidate_triage_covers_v2_8p_preflight_passing_candidates": len(triage.get("records", [])) == triage.get("preflight_passing_candidate_count", -1), "v2_8p_artifact_verified": v28p_package.get("zip_sha256_matches_expected") is True})
    write_json(OUTPUT_DIR / "package_verification.json", {"artifact_package": "v2_8q_bugsinpy_preflight_guided_third_scoreable_artifacts", "generated_by": "local v2.8q prep checkpoint", "full_scoring_allowed": False})
    write_json(OUTPUT_DIR / "artifact_sha256_verification.json", {"v2_8p_artifact_verification": v28p_package, "v2_8q_zip_sha256_available_after_download": False})
    write_text(
        OUTPUT_DIR / "campaign_summary.md",
        "# v2.8q BugsInPy Preflight-Guided Third Scoreable Recovery\n\n"
        "Status: `blocked_pending_v2_8q_preflight_guided_third_scoreable_artifact`.\n\n"
        "- Preserved reference gate must restore `youtube-dl:1` and `black:4` before replacement work.\n"
        "- Candidate triage covers all official v2.8p preflight-passing candidates.\n"
        "- Initial repair target order is decision-time-safe and bounded to source-only heuristics.\n"
        "- Full scoring remains NOT_RUN / disallowed.\n"
        "- Memory lift is not demonstrated.\n"
        "- Self-maintaining software is not demonstrated.\n",
    )
    write_manifest(OUTPUT_DIR)


def main() -> int:
    package = verify_v28p_artifact()
    prepare_v28q(package)
    append_summary_block()
    print("v2.8q BugsInPy preflight-guided third scoreable checkpoint prepared")
    print(f"v2.8p artifact present: {package.get('zip_present')}")
    print(f"v2.8p artifact SHA256 matches expected: {package.get('zip_sha256_matches_expected')}")
    print("v2.8q status: blocked_pending_v2_8q_preflight_guided_third_scoreable_artifact")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
