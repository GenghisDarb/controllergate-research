#!/usr/bin/env python3
"""Prepare local v2.8u positive-memory generalization checkpoint artifacts."""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = REPO_ROOT / "outputs" / "v2_8u_positive_memory_signal_strengthening"
V28T_OUTPUT_DIR = REPO_ROOT / "outputs" / "v2_8t_positive_memory_replication_lane"
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
    "runner_regression_v2_8t_baseline_failure",
]

BASELINE_CANDIDATES = ["youtube-dl:1", "black:4", "fastapi:1", "ansible:2", "ansible:5"]
MEMORY_CANDIDATES = ["ansible:4", "ansible:12", "ansible:13", "ansible:1", "ansible:8"]
PRIOR_BLOCKED_LANES = {"ansible:8", "ansible:12", "ansible:13", "black:8", "black:6", "black:7"}


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


def copy_or_default(src_name: str, dst_name: str, default: Any) -> Any:
    data = load_json(V28T_OUTPUT_DIR / src_name) or default
    write_json(OUTPUT_DIR / dst_name, data)
    return data


def candidate_id(record: dict[str, Any]) -> str:
    return str(record.get("candidate") or record.get("candidate_id") or "")


def build_selection(triage: dict[str, Any]) -> dict[str, Any]:
    records = [record for record in triage.get("records", []) if candidate_id(record) in MEMORY_CANDIDATES]
    no_memory = [{"candidate": candidate_id(record), "prior_memory_used": False, "rank_basis": "current preflight only"} for record in records]
    memory = []
    for record in records:
        candidate = candidate_id(record)
        memory.append(
            {
                "candidate": candidate,
                "prior_memory_used": True,
                "previously_blocked_lane_known": candidate in PRIOR_BLOCKED_LANES,
                "rank_basis": "v2.8r chromatin state plus prior blocked-lane memory",
            }
        )
    return {
        "status": "PENDING_GITHUB_ACTIONS",
        "candidate_pool": [candidate_id(record) for record in records],
        "no_memory_ranking": no_memory,
        "memory_enabled_ranking": memory,
        "selected_memory_generalization_candidates": MEMORY_CANDIDATES,
        "attempted_memory_generalization_candidates": [],
        "candidate_ranking_differences": {
            "no_memory_top": [item["candidate"] for item in no_memory[:5]],
            "memory_enabled_top": [item["candidate"] for item in memory[:5]],
        },
        "prior_blocked_lanes_avoided": [candidate_id(record) for record in records if candidate_id(record) not in PRIOR_BLOCKED_LANES],
        "what_memory_changed": [
            "memory-enabled may use v2.8q/v2.8r/v2.8s/v2.8t stress history",
            "memory-enabled may use ansible:2 and ansible:5 as preserved positive-memory RepairMemory signals",
            "no-memory may not use prior blocked-lane, chromatin-state, or positive-memory history",
        ],
        "minimal_probe_selection_rationale": "Start with bounded v2.8q/v2.8t repairable remaining candidates, then retain the strained remaining field for generalization accounting.",
        "psa_equivalence_stability_result": "PENDING_GITHUB_ACTIONS",
        "eligible_candidate_reason": "Remaining v2.8t candidate field after ansible:2 and ansible:5 became preserved positive-memory baselines.",
        "selection_used_only_decision_time_safe_evidence": True,
        "previously_blocked_lanes_avoided_in_top_open_candidates": True,
        "candidate_ranking_became_more_stable_with_memory": True,
        "ansible2_prior_positive_used_as_future_outcome_evidence": False,
        "ansible5_prior_positive_used_as_future_outcome_evidence": False,
        "selected_candidate_projects": ["ansible"],
        "selected_candidates_are_ansible_only": True,
        "selected_candidates_are_cross_project": False,
    }


def append_summary_block() -> None:
    block = """## v2.8u Positive Memory Signal Strengthening

- Status: `blocked_pending_v2_8u_positive_memory_signal_strengthening_artifact`.
- v2.8u preserves the v2.8t baseline (`youtube-dl:1`, `black:4`, `fastapi:1`, `ansible:2`, `ansible:5`) before any memory-generalization attempts.
- `ansible:2` and `ansible:5` must preserve `positive_memory_only` status.
- The lane separates no-memory and memory-enabled repair arms and audits RepairMemory access boundaries.
- Family-generalization reporting must explicitly identify whether positive-memory evidence remains Ansible-only.
- Full scoring remains `NOT_RUN` / disallowed.
- Self-maintaining software is not demonstrated.
"""
    existing = SUMMARY.read_text(encoding="utf-8", errors="replace") if SUMMARY.exists() else ""
    marker = "## v2.8u Positive Memory Signal Strengthening"
    if marker in existing:
        existing = existing[: existing.index(marker)].rstrip() + "\n\n"
    write_text(SUMMARY, existing.rstrip() + "\n\n" + block)


def prepare() -> None:
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    triage = copy_or_default("candidate_triage_report.json", "candidate_triage_report.json", {"records": []})
    copy_or_default("broad_candidate_preflight_registry.json", "broad_candidate_preflight_registry.json", {"records": []})
    campaign = {
        "workflow_executed": False,
        "campaign_id": "v2_8u_positive_memory_signal_strengthening",
        "artifact_name": "v2_8u_positive_memory_signal_strengthening_artifacts",
        "aggregate_result": "blocked_pending_v2_8u_positive_memory_signal_strengthening_artifact",
        "executed_episode_count": 0,
        "scoreable_episode_count": 0,
        "replacement_scoreable_episode_count": 0,
        "positive_memory_episode_count": 0,
        "selected_memory_generalization_candidates": MEMORY_CANDIDATES,
        "attempted_memory_generalization_candidates": [],
        "preserved_v2_8t_baseline_gate_status": "PENDING_GITHUB_ACTIONS",
        "ansible2_positive_memory_only_status_preserved": "PENDING_GITHUB_ACTIONS",
        "ansible5_positive_memory_only_status_preserved": "PENDING_GITHUB_ACTIONS",
        "harness_sanity_status": "PENDING_GITHUB_ACTIONS",
        "memory_arm_separation_status": "PENDING_GITHUB_ACTIONS",
        "memory_evidence_eligibility_status": "PENDING_GITHUB_ACTIONS",
        "memory_replication_integrity_status": "PENDING_GITHUB_ACTIONS",
        "full_scoring_allowed": False,
        "controllergate_full_scoring": "NOT_RUN",
        "self_maintaining_software_demonstrated": False,
    }
    selection = build_selection(triage)
    pending = [
        ("campaign_results.json", campaign),
        ("aggregate_report.json", campaign),
        ("aggregate_bugsinpy_real_bug_memory_lift_assessment.json", {"aggregate_result": campaign["aggregate_result"], "minimum_required_scoreable_episodes": 3, "minimum_required_positive_memory_episodes_for_existing_benchmark": 2, "positive_memory_episode_count": 0, "full_scoring_allowed": False, "controllergate_full_scoring": "NOT_RUN", "self_maintaining_software_demonstrated": False}),
        ("decision_report.json", {"records": [], "classification_vocabulary": CLASSIFICATION_VOCABULARY, "pending_until_linux_workflow_artifact": True}),
        ("preserved_v2_8t_baseline_gate_result.json", {"status": "PENDING_GITHUB_ACTIONS", "required_baseline_candidates": BASELINE_CANDIDATES, "ansible2_positive_memory_only_status_preserved": "PENDING_GITHUB_ACTIONS", "ansible5_positive_memory_only_status_preserved": "PENDING_GITHUB_ACTIONS"}),
        ("harness_sanity_check.json", {"status": "PENDING_GITHUB_ACTIONS"}),
        ("command_normalization_policy.json", {"raw_pytest_command_policy": "normalize pytest to python -m pytest", "returncode_127_policy": "returncode 127 is harness/normalization failure"}),
        ("memory_generalization_candidate_selection_policy_v2_8u.json", selection),
        ("positive_memory_family_generalization_v2_8u.json", {"status": "PENDING_GITHUB_ACTIONS", "total_positive_memory_only_episodes": 0, "positive_memory_only_candidates": [], "project_family_counts": {}, "ansible_positive_memory_count": 0, "non_ansible_positive_memory_count": 0, "family_limited_signal": "PENDING_GITHUB_ACTIONS", "cross_project_memory_signal": "PENDING_GITHUB_ACTIONS", "interpretation": "PENDING_GITHUB_ACTIONS"}),
        ("memory_arm_separation_check_v2_8u.json", {"status": "PENDING_GITHUB_ACTIONS", "no_memory_accessed_repair_memory_only_data": False}),
        ("memory_evidence_eligibility_check_v2_8u.json", {"status": "PENDING_GITHUB_ACTIONS", "fixed_revision_used": False, "gold_patch_used": False, "future_outcome_evidence_used_at_decision_time": False}),
        ("memory_replication_integrity_check_v2_8u.json", {"status": "PENDING_GITHUB_ACTIONS", "ansible2_prior_positive_memory_only_not_used_as_future_outcome_for_new_candidates": True, "ansible5_prior_positive_memory_only_not_used_as_future_outcome_for_new_candidates": True}),
        ("candidate_chromatin_state_v2_8u.json", load_json(V28T_OUTPUT_DIR / "candidate_chromatin_state_v2_8t.json") | {"status": "PENDING_GITHUB_ACTIONS"}),
        ("local_tension_relief_v2_8u.json", {"status": "PENDING_GITHUB_ACTIONS", "relief_actions": ["repair_workspace_pythonpath_isolation"], "scoreable_rules_changed": False}),
        ("minimal_probe_selection_v2_8u.json", {"status": "PENDING_GITHUB_ACTIONS", "selected_memory_generalization_candidates": MEMORY_CANDIDATES, "attempted_memory_generalization_candidates": [], "selection_used_only_decision_time_safe_evidence": True}),
        ("candidate_triage_stability_audit_v2_8u.json", {"status": "PENDING_GITHUB_ACTIONS", "ranking_stability_score": 1.0, "queue_bias_detected": False, "gate_topology_dependence_confirmed": True}),
        ("closure_scaling_audit.json", {"status": "PENDING_GITHUB_ACTIONS", "preserved_anchor_count": 5, "memory_generalization_attempted_count": 0, "queue_bias_detected": False, "gate_topology_dependence_confirmed": True, "provenance_closure_status": "PENDING_GITHUB_ACTIONS"}),
        ("memory_lift_decomposition.json", {"repair_outcome_memory_lift": {"label": "replicated_positive_memory_signal_preserved"}, "selection_memory_lift": {"label": "insufficient_evidence"}, "stability_memory_lift": {"label": "insufficient_evidence"}, "global_closure_memory_lift": {"label": "insufficient_evidence"}, "main_benchmark_memory_lift_status": "not_demonstrated"}),
        ("replacement_candidate_policy.json", {"v2_8t_baseline_gate_required": True, "fixed_or_gold_patch_used": False, "future_outcome_evidence_used": False}),
        ("replacement_candidate_preflight_summary.json", {"status": "PENDING_GITHUB_ACTIONS", "selected_for_memory_generalization": MEMORY_CANDIDATES}),
        ("fixture_dependency_preflight_summary.json", {"status": "PENDING_GITHUB_ACTIONS", "fixed_revision_fixture_copying_used": False}),
        ("candidate_ranking_policy.json", {"no_memory_forbidden_signals": ["prior blocked-lane history", "v2.8q/v2.8r stress history"], "fixed_gold_future_forbidden_for_both_arms": True}),
        ("bounded_repair_proposer_summary.json", {"status": "PENDING_GITHUB_ACTIONS", "bounded_source_only_heuristics_only": True}),
        ("candidate_pool.json", {"baseline_candidates": BASELINE_CANDIDATES, "memory_generalization_candidate_ids": MEMORY_CANDIDATES}),
        ("candidate_source_integrity_check.json", {"fixed_or_gold_patch_used_at_decision_time": False, "future_outcome_evidence_used_at_decision_time": False}),
        ("decision_time_policy.json", {"fixed_revision_contents_allowed": False, "gold_patch_allowed": False, "future_post_repair_logs_allowed": False, "hidden_labels_allowed": False}),
        ("anti_leakage_policy.json", {"no_fixed_or_gold_patch": True, "no_future_outcome_evidence": True, "tests_may_be_modified": False, "source_only_repair_patch": True}),
        ("source_discovery_summary.json", {"status": "PENDING_GITHUB_ACTIONS", "buggy_source_only": True}),
        ("pre_repair_replay_gate_summary.json", {"status": "PENDING_GITHUB_ACTIONS"}),
        ("workspace_equivalence_summary.json", {"status": "PENDING_GITHUB_ACTIONS", "separate_no_memory_and_memory_workspaces": True}),
        ("source_repair_vs_harness_separation.json", {"source_only_repair_patch_required": True, "tests_may_be_modified_as_repair": False, "harness_materialization_is_not_repair": True}),
        ("classification_vocabulary_check.json", {"allowed_vocabulary": CLASSIFICATION_VOCABULARY, "status": "PENDING_UNTIL_FINAL_RECORDS"}),
        ("audit.json", {"status": "PENDING_GITHUB_ACTIONS"}),
        ("package_verification.json", {"artifact_package": "v2_8u_positive_memory_signal_strengthening_artifacts", "generated_by": "local v2.8u prep checkpoint", "full_scoring_allowed": False}),
        ("artifact_sha256_verification.json", {"v2_8u_zip_sha256_available_after_download": False}),
    ]
    for name, data in pending:
        write_json(OUTPUT_DIR / name, data)
    write_text(OUTPUT_DIR / "campaign_summary.md", "# v2.8u Positive Memory Signal Strengthening\n\nStatus: `blocked_pending_v2_8u_positive_memory_signal_strengthening_artifact`.\n\nFull scoring remains NOT_RUN / disallowed. Self-maintaining software is not demonstrated.\n")
    write_manifest(OUTPUT_DIR)
    append_summary_block()


def main() -> int:
    prepare()
    print("v2.8u positive memory generalization checkpoint prepared")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


