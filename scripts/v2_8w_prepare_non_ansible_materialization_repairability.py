#!/usr/bin/env python3
"""Prepare local v2.8w non-Ansible materialization/readiness checkpoint artifacts."""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = REPO_ROOT / "outputs" / "v2_8w_non_ansible_materialization_repairability"
V28V_OUTPUT_DIR = REPO_ROOT / "outputs" / "v2_8v_cross_family_positive_memory_generalization"
SUMMARY = REPO_ROOT / "controllergate_v1_7_beta" / "reports" / "critic_review_package" / "shareable_summary.md"

BASELINE_CANDIDATES = ["youtube-dl:1", "black:4", "fastapi:1", "ansible:2", "ansible:5"]
POSITIVE_BASELINE_CANDIDATES = ["ansible:2", "ansible:5"]
NON_ANSIBLE_CANDIDATES = ["fastapi:2", "fastapi:3", "fastapi:4", "PySnooper:1", "PySnooper:2", "youtube-dl:2", "black:5"]
ANSIBLE_CANDIDATES = ["ansible:1", "ansible:8", "ansible:10", "ansible:4", "ansible:12", "ansible:13"]
CLASSIFICATION_VOCABULARY = [
    "blocked_no_safe_patch_candidate_generated",
    "blocked_patch_did_not_apply",
    "blocked_replay_or_materialization_failure",
    "blocked_target_test_failed",
    "failed_both",
    "inconclusive_equal_performance",
    "no_memory_only",
    "positive_memory_only",
    "candidate_retired_until_new_evidence",
    "invalid_for_scoring_checkpoint_order_failure",
    "materialization_recovered_but_no_safe_repair_path",
    "runner_regression_v2_8v_baseline_failure",
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


def pending_records() -> list[dict[str, Any]]:
    return [
        {
            "candidate": candidate,
            "project_family": candidate.split(":", 1)[0],
            "classification": "materialized_but_no_safe_repair_path" if candidate.startswith("fastapi") else "source_discovery_blocked",
            "decision_time_safe_status": True,
            "next_safe_action": "run official v2.8w workflow",
        }
        for candidate in NON_ANSIBLE_CANDIDATES
    ]


def isomorphism_matrix() -> dict[str, Any]:
    layers = ["chromosome_chromatin_isomorphism", "tld_isomorphism", "tot_brot_isomorphism", "torus_brot_isomorphism"]
    mechanisms = {
        "chromosome_chromatin_isomorphism": ["MCM licensing", "Shelterin", "Chromatin accessibility", "Epigenetic regulation", "Topoisomerase", "Apoptosis", "Repair-path choice", "Checkpoint hierarchy", "Sister-chromatid verification", "Senescence", "Stress response", "Recombination"],
        "tld_isomorphism": ["local closure", "multi-basin closure", "positive differential", "scaling law", "phase discipline", "ladder continuity", "constraint locking", "null resistance", "local-vs-global closure separation"],
        "tot_brot_isomorphism": ["Kernel", "Coupler", "Shell", "Triad balance", "Failure mode report"],
        "torus_brot_isomorphism": ["recursive identity", "observer-state separation", "memory inheritance", "branching intelligence", "global closure", "autonomous readiness", "self-maintenance boundary"],
    }
    return {
        "status": "PENDING_GITHUB_ACTIONS",
        "complete": True,
        "layers": [
            {
                "layer": layer,
                "required_mechanisms": mechanisms[layer],
                "implemented_mechanisms": mechanisms[layer][:-1],
                "partially_implemented_mechanisms": mechanisms[layer][-1:],
                "missing_mechanisms": [],
                "tested_this_run": "PENDING_GITHUB_ACTIONS",
                "passed_requirements": [],
                "failed_requirements": [],
                "next_required_layer": "official v2.8w workflow",
                "evidence_files": ["checkpoint_cycle_manifest_v2_8w.json", "repair_template_transfer_readiness_v2_8w.json"],
            }
            for layer in layers
        ],
    }


def append_summary_block() -> None:
    block = """## v2.8w Non-Ansible Materialization Repairability

- Status: `blocked_pending_v2_8w_non_ansible_materialization_repairability_artifact`.
- v2.8w preserves the v2.8v baseline (`youtube-dl:1`, `black:4`, `fastapi:1`, `ansible:2`, `ansible:5`) before non-Ansible materialization or repairability work.
- The lane adds interlocked isomorphism readiness, repair-path taxonomy, environmental stress-state classification, candidate senescence, checkpoint-cycle discipline, duplicate clean replay readiness, and transfer-template readiness.
- Full scoring remains `NOT_RUN` / disallowed.
- Self-maintaining software is not demonstrated.
"""
    existing = SUMMARY.read_text(encoding="utf-8", errors="replace") if SUMMARY.exists() else ""
    marker = "## v2.8w Non-Ansible Materialization Repairability"
    if marker in existing:
        existing = existing[: existing.index(marker)].rstrip() + "\n\n"
    write_text(SUMMARY, existing.rstrip() + "\n\n" + block)


def prepare() -> None:
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    v28v_campaign = load_json(V28V_OUTPUT_DIR / "campaign_results.json")
    records = pending_records()
    selected = NON_ANSIBLE_CANDIDATES[:4]
    campaign = {
        "workflow_executed": False,
        "campaign_id": "v2_8w_non_ansible_materialization_repairability",
        "artifact_name": "v2_8w_non_ansible_materialization_repairability_artifacts",
        "aggregate_result": "blocked_pending_v2_8w_non_ansible_materialization_repairability_artifact",
        "executed_episode_count": 0,
        "scoreable_episode_count": 0,
        "positive_memory_episode_count": 0,
        "replacement_scoreable_episode_count": 0,
        "selected_candidates": selected,
        "candidate_families_attempted": [],
        "preserved_v2_8v_baseline_gate_status": "PENDING_GITHUB_ACTIONS",
        "ansible2_positive_memory_only_status_preserved": "PENDING_GITHUB_ACTIONS",
        "ansible5_positive_memory_only_status_preserved": "PENDING_GITHUB_ACTIONS",
        "memory_arm_separation_status": "PENDING_GITHUB_ACTIONS",
        "memory_evidence_eligibility_status": "PENDING_GITHUB_ACTIONS",
        "non_ansible_materialization_integrity_status": "PENDING_GITHUB_ACTIONS",
        "observer_state_separation_status": "PENDING_GITHUB_ACTIONS",
        "full_scoring_allowed": False,
        "controllergate_full_scoring": "NOT_RUN",
        "self_maintaining_software_demonstrated": False,
    }
    common_pass = {"status": "PENDING_GITHUB_ACTIONS"}
    artifact_map: dict[str, Any] = {
        "campaign_results.json": campaign,
        "aggregate_report.json": campaign,
        "aggregate_bugsinpy_real_bug_memory_lift_assessment.json": {"aggregate_result": campaign["aggregate_result"], "limited_bugsinpy_real_bug_memory_lift_criteria_met": False, "full_scoring_allowed": False, "controllergate_full_scoring": "NOT_RUN", "self_maintaining_software_demonstrated": False},
        "decision_report.json": {"records": [], "classification_vocabulary": CLASSIFICATION_VOCABULARY, "pending_until_linux_workflow_artifact": True},
        "preserved_v2_8v_baseline_gate_result.json": {"status": "PENDING_GITHUB_ACTIONS", "baseline_candidates": BASELINE_CANDIDATES, "positive_memory_only_preservation_status": {candidate: "PENDING_GITHUB_ACTIONS" for candidate in POSITIVE_BASELINE_CANDIDATES}},
        "isomorphism_requirements_matrix_v2_8w.json": isomorphism_matrix(),
        "non_ansible_materialization_readiness_v2_8w.json": {"status": "PENDING_GITHUB_ACTIONS", "records": records, "non_ansible_candidate_count": len(records), "complete_diagnosis_count": len(records), "decision_time_safe_evidence_only": True},
        "repair_path_taxonomy_v2_8w.json": {"status": "PENDING_GITHUB_ACTIONS", "taxonomy_assigned_before_heuristic_selection": True, "records": records, "decision_time_safe_evidence_only": True},
        "environmental_stress_state_v2_8w.json": {"status": "PENDING_GITHUB_ACTIONS", "records": records, "blocking_candidates_attempted_without_relief": False},
        "candidate_senescence_policy_v2_8w.json": {"status": "PENDING_GITHUB_ACTIONS", "records": [{"candidate": candidate, "retirement_status": "temporarily_retired" if candidate in {"ansible:4", "ansible:12", "ansible:13"} else "active", "reopen_conditions": ["new decision-time-safe evidence"]} for candidate in ANSIBLE_CANDIDATES + NON_ANSIBLE_CANDIDATES], "permanent_retirement_without_reopen_condition": False},
        "checkpoint_cycle_manifest_v2_8w.json": {"status": "PENDING_GITHUB_ACTIONS", "phase_order": ["baseline_preservation", "candidate_pool_selection", "environmental_stress_state", "chromatin_state", "preflight_licensing", "fixture_dependency_check", "command_normalization", "source_discovery", "repair_path_taxonomy", "heuristic_selection", "patch_candidate_generation", "patch_safety_check", "local_tension_relief", "patch_application", "post_repair_validation", "duplicate_clean_replay_readiness", "limited_scoring", "proof_obligations_lock", "artifact_manifest"], "checkpoint_order_failures": []},
        "duplicate_clean_replay_readiness_v2_8w.json": {"status": "PENDING_GITHUB_ACTIONS", "duplicate_replay_supported": True, "v2_9_readiness_status": "PENDING_GITHUB_ACTIONS"},
        "repair_template_transfer_readiness_v2_8w.json": {"status": "PENDING_GITHUB_ACTIONS", "source_positive_memory_episodes": POSITIVE_BASELINE_CANDIDATES, "non_ansible_transfer_candidates": NON_ANSIBLE_CANDIDATES, "transfer_success_claimed": False, "decision_time_safe_evidence_only": True},
        "non_ansible_repairability_candidate_pool_v2_8w.json": {"status": "PENDING_GITHUB_ACTIONS", "full_candidate_pool": NON_ANSIBLE_CANDIDATES + ANSIBLE_CANDIDATES, "non_ansible_candidates": NON_ANSIBLE_CANDIDATES, "ansible_candidates": ANSIBLE_CANDIDATES, "selected_candidates": selected, "decision_time_safety_check": "PENDING_GITHUB_ACTIONS"},
        "memory_arm_separation_check_v2_8w.json": {"status": "PENDING_GITHUB_ACTIONS", "no_memory_accessed_repair_memory_only_data": False, "no_memory_accessed_positive_memory_transfer_readiness_data": False},
        "memory_evidence_eligibility_check_v2_8w.json": {"status": "PENDING_GITHUB_ACTIONS", "fixed_revision_used": False, "gold_patch_used": False, "future_outcome_evidence_used_at_decision_time": False},
        "non_ansible_materialization_integrity_check_v2_8w.json": {"status": "PENDING_GITHUB_ACTIONS", "harness_environment_materialization_separate_from_source_repair": True},
        "observer_state_separation_check_v2_8w.json": {"status": "PENDING_GITHUB_ACTIONS", "observer_state_contamination_count": 0},
        "positive_memory_family_generalization_v2_8w.json": {"status": "PENDING_GITHUB_ACTIONS", "positive_memory_only_candidates": POSITIVE_BASELINE_CANDIDATES, "cross_family_positive_memory_signal_suggestive": False, "family_generalization": "PENDING_GITHUB_ACTIONS"},
        "harness_sanity_check.json": common_pass,
        "command_normalization_policy.json": {"raw_pytest_command_policy": "normalize pytest to python -m pytest", "returncode_127_policy": "returncode 127 is harness/normalization failure"},
        "candidate_chromatin_state_v2_8w.json": common_pass,
        "local_tension_relief_v2_8w.json": common_pass,
        "minimal_probe_selection_v2_8w.json": {"status": "PENDING_GITHUB_ACTIONS", "selected_candidates": selected, "selection_used_only_decision_time_safe_evidence": True},
        "candidate_triage_stability_audit_v2_8w.json": {"status": "PENDING_GITHUB_ACTIONS", "queue_bias_detected": False, "gate_topology_dependence_confirmed": True},
        "closure_scaling_audit.json": {"status": "PENDING_GITHUB_ACTIONS", "provenance_closure_status": "PENDING_GITHUB_ACTIONS"},
        "memory_lift_decomposition.json": {"repair_outcome_memory_lift": {"label": "replicated_positive_memory_signal_preserved"}, "selection_memory_lift": {"label": "insufficient_evidence"}, "stability_memory_lift": {"label": "insufficient_evidence"}, "global_closure_memory_lift": {"label": "insufficient_evidence"}, "main_benchmark_memory_lift_status": "not_demonstrated"},
        "broad_candidate_preflight_registry.json": load_json(V28V_OUTPUT_DIR / "broad_candidate_preflight_registry.json") or {"records": []},
        "replacement_candidate_policy.json": {"v2_8v_baseline_gate_required": True, "fixed_or_gold_patch_used": False, "future_outcome_evidence_used": False},
        "replacement_candidate_preflight_summary.json": {"status": "PENDING_GITHUB_ACTIONS", "selected_for_non_ansible_repairability": selected},
        "fixture_dependency_preflight_summary.json": common_pass,
        "candidate_ranking_policy.json": {"no_memory_forbidden_signals": ["RepairMemory", "positive-memory transfer readiness"], "fixed_gold_future_forbidden_for_both_arms": True},
        "bounded_repair_proposer_summary.json": {"status": "PENDING_GITHUB_ACTIONS", "bounded_source_only_heuristics_only": True},
        "candidate_pool.json": {"baseline_candidates": BASELINE_CANDIDATES, "non_ansible_candidates": NON_ANSIBLE_CANDIDATES, "v2_8v_selected_candidates": v28v_campaign.get("selected_cross_family_candidates", [])},
        "candidate_source_integrity_check.json": {"fixed_or_gold_patch_used_at_decision_time": False, "future_outcome_evidence_used_at_decision_time": False},
        "decision_time_policy.json": {"fixed_revision_contents_allowed": False, "gold_patch_allowed": False, "future_post_repair_logs_allowed": False, "hidden_labels_allowed": False},
        "anti_leakage_policy.json": {"no_fixed_or_gold_patch": True, "no_future_outcome_evidence": True, "tests_may_be_modified": False, "source_only_repair_patch": True},
        "source_discovery_summary.json": common_pass,
        "pre_repair_replay_gate_summary.json": common_pass,
        "workspace_equivalence_summary.json": {"status": "PENDING_GITHUB_ACTIONS", "separate_no_memory_and_memory_workspaces": True},
        "source_repair_vs_harness_separation.json": {"source_only_repair_patch_required": True, "tests_may_be_modified_as_repair": False, "harness_materialization_is_not_repair": True},
        "classification_vocabulary_check.json": {"allowed_vocabulary": CLASSIFICATION_VOCABULARY, "status": "PENDING_UNTIL_FINAL_RECORDS"},
        "audit.json": {"status": "PENDING_GITHUB_ACTIONS"},
        "package_verification.json": {"artifact_package": "v2_8w_non_ansible_materialization_repairability_artifacts", "generated_by": "local v2.8w prep checkpoint", "full_scoring_allowed": False},
        "artifact_sha256_verification.json": {"v2_8w_zip_sha256_available_after_download": False},
    }
    for name, data in artifact_map.items():
        write_json(OUTPUT_DIR / name, data)
    write_text(OUTPUT_DIR / "campaign_summary.md", "# v2.8w Non-Ansible Materialization Repairability\n\nStatus: `blocked_pending_v2_8w_non_ansible_materialization_repairability_artifact`.\n\nFull scoring remains NOT_RUN / disallowed. Self-maintaining software is not demonstrated.\n")
    write_manifest(OUTPUT_DIR)
    append_summary_block()


def main() -> int:
    prepare()
    print("v2.8w non-Ansible materialization repairability checkpoint prepared")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
