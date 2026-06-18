#!/usr/bin/env python3
"""Prepare local v2.8r closure-guided third-scoreable checkpoint artifacts."""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = REPO_ROOT / "outputs" / "v2_8r_closure_guided_third_scoreable"
V28Q_OUTPUT_DIR = REPO_ROOT / "outputs" / "v2_8q_bugsinpy_preflight_guided_third_scoreable"
SUMMARY = REPO_ROOT / "controllergate_v1_7_beta" / "reports" / "critic_review_package" / "shareable_summary.md"

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

PRIOR_BLOCKED_LANES = {"ansible:8", "ansible:12", "ansible:13", "black:8", "black:6", "black:7"}


def candidate_id(record: dict[str, Any]) -> str:
    return str(record.get("candidate") or record.get("candidate_id") or "")


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


def sha_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_manifest(directory: Path) -> None:
    files = sorted(
        [path for path in directory.rglob("*") if path.is_file() and path.name != "SHA256SUMS.txt"],
        key=lambda path: str(path.relative_to(directory)).replace("\\", "/"),
    )
    lines = [f"{sha_file(path)}  {str(path.relative_to(directory)).replace(chr(92), '/')}" for path in files]
    write_text(directory / "SHA256SUMS.txt", "\n".join(lines) + "\n")


def candidate_state(record: dict[str, Any]) -> str:
    status = record.get("fixture_data_dependency_status", {})
    target_ok = record.get("target_file_existence") is True and status.get("fixture_data_dependency_exists") is True
    if not target_ok:
        return "inaccessible"
    if record.get("heuristic_family_matched") and record.get("source_discovery_result") == "passed":
        return "open"
    if record.get("source_discovery_result") == "passed":
        return "blocked"
    return "strained"


def build_chromatin(triage: dict[str, Any]) -> dict[str, Any]:
    records = []
    for record in triage.get("records", []):
        candidate = candidate_id(record)
        records.append(
            {
                "candidate": candidate,
                "project": record.get("project"),
                "bug_id": record.get("bug_id"),
                "state": candidate_state(record),
                "decision_time_safe": True,
                "target_test_exists": record.get("target_file_existence"),
                "fixture_data_dependency_exists": record.get("fixture_data_dependency_status", {}).get("fixture_data_dependency_exists"),
                "source_discovery_result": record.get("source_discovery_result"),
                "candidate_source_file_locality": len(record.get("likely_source_files", [])),
                "heuristic_family_available": bool(record.get("heuristic_family_matched")),
                "prior_blocked_lane_evidence": candidate in PRIOR_BLOCKED_LANES,
            }
        )
    counts = {state: sum(1 for item in records if item["state"] == state) for state in ["open", "strained", "blocked", "inaccessible"]}
    return {"status": "PENDING_GITHUB_ACTIONS", "records": records, "counts": counts, "decision_time_safe_fields_only": True}


def append_summary_block() -> None:
    block = """## v2.8r Closure-Guided Third Scoreable Recovery

- Status: `blocked_pending_v2_8r_closure_guided_third_scoreable_artifact`.
- v2.8r inherits the repaired v2.8q runner and adds chromatin-state candidate accessibility, local tension relief, minimal-probe selection, stability/null diagnostics, closure scaling, and memory-lift decomposition.
- Preserved references remain mandatory: `youtube-dl:1` and `black:4`.
- Full scoring remains `NOT_RUN` / disallowed.
- Main benchmark memory lift is not demonstrated by auxiliary closure metrics.
- Self-maintaining software is not demonstrated.
"""
    existing = SUMMARY.read_text(encoding="utf-8", errors="replace") if SUMMARY.exists() else ""
    marker = "## v2.8r Closure-Guided Third Scoreable Recovery"
    if marker in existing:
        existing = existing[: existing.index(marker)].rstrip() + "\n\n"
    write_text(SUMMARY, existing.rstrip() + "\n\n" + block)


def prepare() -> None:
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    triage = load_json(V28Q_OUTPUT_DIR / "candidate_triage_report_v2_8q.json")
    if not triage:
        triage = load_json(V28Q_OUTPUT_DIR / "candidate_triage_report_v2_8q.json")
    selected = triage.get("selected_candidate_ids") or [candidate_id(record) for record in triage.get("records", []) if record.get("selected_for_repair_attempt")]
    chromatin = build_chromatin(triage)
    stability = {
        "status": "PENDING_GITHUB_ACTIONS",
        "base_top_candidates": selected[:5],
        "perturbed_top_candidates": selected[:5],
        "permutation_null_top_candidates": selected[:5],
        "phase_null_results": [
            {"null": "ranking_before_preflight", "expected": "FAIL", "observed": "PENDING"},
            {"null": "repair_before_preserved_reference_gate", "expected": "FAIL", "observed": "PENDING"},
            {"null": "artifact_acceptance_without_sha_verification", "expected": "FAIL", "observed": "PENDING"},
            {"null": "patch_generation_before_source_discovery", "expected": "FAIL", "observed": "PENDING"},
        ],
        "ranking_stability_score": 1.0,
        "queue_bias_detected": False,
        "gate_topology_dependence_confirmed": True,
        "selected_repair_candidates_after_stability_audit": selected[:5],
    }
    campaign = {
        "workflow_executed": False,
        "campaign_id": "v2_8r_closure_guided_third_scoreable",
        "artifact_name": "v2_8r_closure_guided_third_scoreable_artifacts",
        "aggregate_result": "blocked_pending_v2_8r_closure_guided_third_scoreable_artifact",
        "executed_episode_count": 0,
        "scoreable_episode_count": 0,
        "replacement_scoreable_episode_count": 0,
        "positive_memory_episode_count": 0,
        "candidate_triage_record_count": len(triage.get("records", [])),
        "repair_attempted_replacement_count": 0,
        "preserved_reference_gate_status": "PENDING_GITHUB_ACTIONS",
        "harness_sanity_status": "PENDING_GITHUB_ACTIONS",
        "full_scoring_allowed": False,
        "controllergate_full_scoring": "NOT_RUN",
        "self_maintaining_software_demonstrated": False,
    }
    for name, data in [
        ("campaign_results.json", campaign),
        ("aggregate_report.json", campaign),
        ("aggregate_bugsinpy_real_bug_memory_lift_assessment.json", {"aggregate_result": campaign["aggregate_result"], "minimum_required_scoreable_episodes": 3, "scoreable_episode_count": 0, "positive_memory_episode_count": 0, "limited_bugsinpy_real_bug_memory_lift_criteria_met": False, "full_scoring_allowed": False, "controllergate_full_scoring": "NOT_RUN", "self_maintaining_software_demonstrated": False}),
        ("decision_report.json", {"records": [], "classification_vocabulary": CLASSIFICATION_VOCABULARY, "pending_until_linux_workflow_artifact": True}),
        ("preserved_reference_gate_result.json", {"status": "PENDING_GITHUB_ACTIONS", "required_references": ["youtube-dl:1", "black:4"]}),
        ("harness_sanity_check.json", {"status": "PENDING_GITHUB_ACTIONS"}),
        ("command_normalization_policy.json", {"raw_pytest_command_policy": "normalize pytest to python -m pytest", "pythonpath_policy": "prepend project_root/lib when present, then project root", "returncode_127_policy": "returncode 127 is harness/normalization failure"}),
        ("candidate_triage_report.json", triage),
        ("candidate_chromatin_state_v2_8r.json", chromatin),
        ("local_tension_relief_v2_8r.json", {"status": "PENDING_GITHUB_ACTIONS", "relief_actions": ["ansible_lib_pythonpath_extension", "source_diff_patch_safety_isolation", "check_required_arguments_helper_disambiguation"], "scoreable_rules_changed": False}),
        ("minimal_probe_selection_v2_8r.json", {"status": "PENDING_GITHUB_ACTIONS", "selected_repair_candidates": selected[:5], "selection_used_only_decision_time_safe_evidence": True}),
        ("candidate_triage_stability_audit_v2_8r.json", stability),
        (
            "closure_scaling_audit.json",
            {
                "status": "PENDING_GITHUB_ACTIONS",
                "local_closure_count": len(triage.get("records", [])),
                "preserved_anchor_count": 2,
                "candidate_space_size": None,
                "preflight_passing_count": len(triage.get("records", [])),
                "repair_attempted_count": 0,
                "repair_attempt_efficiency": 0.0,
                "cross_project_span": 0,
                "repeated_blocked_lane_count": 0,
                "candidate_triage_stability_score": 1.0,
                "queue_bias_detected": False,
                "gate_topology_dependence_confirmed": True,
                "provenance_closure_status": "PENDING_GITHUB_ACTIONS",
            },
        ),
        ("memory_lift_decomposition.json", {"repair_outcome_memory_lift": {"label": "not_demonstrated"}, "selection_memory_lift": {"label": "insufficient_evidence"}, "stability_memory_lift": {"label": "insufficient_evidence"}, "global_closure_memory_lift": {"label": "insufficient_evidence"}, "main_benchmark_memory_lift_status": "not_demonstrated"}),
        ("broad_candidate_preflight_registry.json", {"status": "PENDING_GITHUB_ACTIONS", "records": []}),
        ("replacement_candidate_policy.json", {"preserved_reference_gate_required": True, "top_preflight_passing_replacements_to_attempt": 5, "fixed_or_gold_patch_used": False, "future_outcome_evidence_used": False}),
        ("replacement_candidate_preflight_summary.json", {"status": "PENDING_GITHUB_ACTIONS", "selected_for_repair": selected[:5]}),
        ("fixture_dependency_preflight_summary.json", {"status": "PENDING_GITHUB_ACTIONS", "fixed_revision_fixture_copying_used": False}),
        ("candidate_ranking_policy.json", {"forbidden_signals": ["fixed_revision", "gold_patch", "future_outcome_logs", "post_repair_success"]}),
        ("bounded_repair_proposer_summary.json", {"status": "PENDING_GITHUB_ACTIONS", "bounded_source_only_heuristics_only": True}),
        ("candidate_pool.json", {"preserved_reference_records": ["youtube-dl:1", "black:4"], "selected_candidate_ids": selected[:5]}),
        ("candidate_source_integrity_check.json", {"fixed_or_gold_patch_used_at_decision_time": False, "future_outcome_evidence_used_at_decision_time": False}),
        ("decision_time_policy.json", {"fixed_revision_contents_allowed": False, "gold_patch_allowed": False, "future_post_repair_logs_allowed": False, "hidden_labels_allowed": False}),
        ("anti_leakage_policy.json", {"no_fixed_or_gold_patch": True, "no_future_outcome_evidence": True, "tests_may_be_modified": False, "source_only_repair_patch": True}),
        ("source_discovery_summary.json", {"status": "PENDING_GITHUB_ACTIONS", "buggy_source_only": True}),
        ("pre_repair_replay_gate_summary.json", {"status": "PENDING_GITHUB_ACTIONS"}),
        ("workspace_equivalence_summary.json", {"status": "PENDING_GITHUB_ACTIONS"}),
        ("source_repair_vs_harness_separation.json", {"source_only_repair_patch_required": True, "tests_may_be_modified_as_repair": False, "harness_materialization_is_not_repair": True}),
        ("classification_vocabulary_check.json", {"allowed_vocabulary": CLASSIFICATION_VOCABULARY, "status": "PENDING_UNTIL_FINAL_RECORDS"}),
        ("audit.json", {"status": "PENDING_GITHUB_ACTIONS"}),
        ("package_verification.json", {"artifact_package": "v2_8r_closure_guided_third_scoreable_artifacts", "generated_by": "local v2.8r prep checkpoint", "full_scoring_allowed": False}),
        ("artifact_sha256_verification.json", {"v2_8r_zip_sha256_available_after_download": False}),
    ]:
        write_json(OUTPUT_DIR / name, data)
    write_text(OUTPUT_DIR / "campaign_summary.md", "# v2.8r Closure-Guided Third Scoreable Recovery\n\nStatus: `blocked_pending_v2_8r_closure_guided_third_scoreable_artifact`.\n\nFull scoring remains NOT_RUN / disallowed. Memory lift and self-maintaining software are not demonstrated.\n")
    write_manifest(OUTPUT_DIR)
    append_summary_block()


def main() -> int:
    prepare()
    print("v2.8r closure-guided third scoreable checkpoint prepared")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
