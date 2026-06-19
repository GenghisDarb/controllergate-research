#!/usr/bin/env python3
"""Prepare local v2.9 topological source discovery checkpoint artifacts."""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = REPO_ROOT / "outputs" / "v2_9_topological_source_discovery"
V28W_OUTPUT_DIR = REPO_ROOT / "outputs" / "v2_8w_non_ansible_materialization_repairability"
SUMMARY = REPO_ROOT / "controllergate_v1_7_beta" / "reports" / "critic_review_package" / "shareable_summary.md"

BASELINE = ["youtube-dl:1", "black:4", "fastapi:1", "ansible:2", "ansible:5"]
POSITIVE_BASELINE = ["ansible:2", "ansible:5"]
NON_ANSIBLE = ["fastapi:2", "fastapi:3", "fastapi:4", "PySnooper:1", "PySnooper:2", "fastapi:5"]

REQUIRED_TOP_LEVEL = [
    "campaign_summary.md",
    "campaign_results.json",
    "decision_report.json",
    "aggregate_report.json",
    "aggregate_bugsinpy_real_bug_memory_lift_assessment.json",
    "preserved_v2_8w_baseline_gate_result.json",
    "topological_source_discovery_v2_9.json",
    "ast_loop_extrusion_context_v2_9.json",
    "causal_context_bundle_v2_9.json",
    "topoisomerase_tension_relief_v2_9.json",
    "materialization_tension_relief_log_v2_9.json",
    "heterochromatin_monitor_v2_9.json",
    "silent_scaffolding_risk_audit_v2_9.json",
    "phase_inversion_seed_constraint_check_v2_9.json",
    "topological_candidate_pool_v2_9.json",
    "repair_path_taxonomy_v2_9.json",
    "environmental_stress_state_v2_9.json",
    "candidate_senescence_policy_v2_9.json",
    "checkpoint_cycle_manifest_v2_9.json",
    "duplicate_clean_replay_verification_v2_9.json",
    "repair_template_transfer_readiness_v2_9.json",
    "memory_arm_separation_check_v2_9.json",
    "memory_evidence_eligibility_check_v2_9.json",
    "observer_state_separation_check_v2_9.json",
    "topological_context_integrity_check_v2_9.json",
    "isomorphism_requirements_matrix_v2_9.json",
    "positive_memory_family_generalization_v2_9.json",
    "harness_sanity_check.json",
    "command_normalization_policy.json",
    "candidate_chromatin_state_v2_9.json",
    "local_tension_relief_v2_9.json",
    "minimal_probe_selection_v2_9.json",
    "candidate_triage_stability_audit_v2_9.json",
    "closure_scaling_audit.json",
    "memory_lift_decomposition.json",
    "broad_candidate_preflight_registry.json",
    "replacement_candidate_policy.json",
    "replacement_candidate_preflight_summary.json",
    "fixture_dependency_preflight_summary.json",
    "candidate_ranking_policy.json",
    "bounded_repair_proposer_summary.json",
    "candidate_pool.json",
    "candidate_source_integrity_check.json",
    "decision_time_policy.json",
    "anti_leakage_policy.json",
    "source_discovery_summary.json",
    "pre_repair_replay_gate_summary.json",
    "workspace_equivalence_summary.json",
    "source_repair_vs_harness_separation.json",
    "classification_vocabulary_check.json",
    "audit.json",
    "package_verification.json",
    "artifact_sha256_verification.json",
    "SHA256SUMS.txt",
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
            "flat_slice_sufficiency": "insufficient",
            "loop_extrusion_status": "PENDING_GITHUB_ACTIONS",
            "source_discovery_upgrade_status": "PENDING_GITHUB_ACTIONS",
            "decision_time_safety_status": "PENDING_GITHUB_ACTIONS",
        }
        for candidate in NON_ANSIBLE
    ]


def isomorphism_matrix() -> dict[str, Any]:
    layers = [
        "chromosome_chromatin_isomorphism",
        "tld_isomorphism",
        "tot_brot_isomorphism",
        "torus_brot_isomorphism",
    ]
    return {
        "status": "PENDING_GITHUB_ACTIONS",
        "complete": True,
        "layers": [
            {
                "layer": layer,
                "required_mechanisms": ["baseline preservation", "loop extrusion", "tension relief", "observer-state separation"],
                "implemented_mechanisms": [],
                "partially_implemented_mechanisms": ["prepared by v2.9 checkpoint"],
                "missing_mechanisms": [],
                "tested_this_run": "PENDING_GITHUB_ACTIONS",
                "passed_requirements": [],
                "failed_requirements": [],
                "next_required_layer": "official v2.9 workflow",
                "evidence_files": ["topological_source_discovery_v2_9.json"],
            }
            for layer in layers
        ],
    }


def append_summary_block() -> None:
    block = """## v2.9 Topological Source Discovery

- Status: `blocked_pending_v2_9_topological_source_discovery_artifact`.
- v2.9 preserves the v2.8w baseline before adding topological source discovery, AST/dependency loop extrusion, bounded materialization tension relief, heterochromatin risk checks, duplicate replay readiness, and phase-inversion checks.
- Full scoring remains `NOT_RUN` / disallowed.
- Self-maintaining software is not demonstrated.
"""
    existing = SUMMARY.read_text(encoding="utf-8", errors="replace") if SUMMARY.exists() else ""
    marker = "## v2.9 Topological Source Discovery"
    if marker in existing:
        existing = existing[: existing.index(marker)].rstrip() + "\n\n"
    write_text(SUMMARY, existing.rstrip() + "\n\n" + block)


def prepare() -> None:
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    v28w_campaign = load_json(V28W_OUTPUT_DIR / "campaign_results.json")
    records = pending_records()
    campaign = {
        "workflow_executed": False,
        "campaign_id": "v2_9_topological_source_discovery",
        "artifact_name": "v2_9_topological_source_discovery_artifacts",
        "aggregate_result": "blocked_pending_v2_9_topological_source_discovery_artifact",
        "executed_episode_count": 0,
        "scoreable_episode_count": 0,
        "replacement_scoreable_count": 0,
        "positive_memory_episode_count": 0,
        "selected_candidates": NON_ANSIBLE,
        "candidate_families_attempted": [],
        "preserved_v2_8w_baseline_gate_status": "PENDING_GITHUB_ACTIONS",
        "full_scoring_allowed": False,
        "controllergate_full_scoring": "NOT_RUN",
        "self_maintaining_software_demonstrated": False,
        "v2_8w_prerequisite_commit_state": v28w_campaign.get("aggregate_result", "unknown"),
    }
    pass_pending = {"status": "PENDING_GITHUB_ACTIONS"}
    artifact_map: dict[str, Any] = {
        "campaign_results.json": campaign,
        "aggregate_report.json": campaign,
        "aggregate_bugsinpy_real_bug_memory_lift_assessment.json": campaign | {"limited_bugsinpy_real_bug_memory_lift_criteria_met": False},
        "decision_report.json": {"records": [], "classification_vocabulary": [], "pending_until_linux_workflow_artifact": True},
        "preserved_v2_8w_baseline_gate_result.json": {"status": "PENDING_GITHUB_ACTIONS", "baseline_candidates": BASELINE, "positive_memory_only_preservation_status": {candidate: "PENDING_GITHUB_ACTIONS" for candidate in POSITIVE_BASELINE}},
        "topological_source_discovery_v2_9.json": {"status": "PENDING_GITHUB_ACTIONS", "records": records, "decision_time_safe_evidence_only": True},
        "ast_loop_extrusion_context_v2_9.json": {"status": "PENDING_GITHUB_ACTIONS", "records": records},
        "causal_context_bundle_v2_9.json": {"status": "PENDING_GITHUB_ACTIONS", "bundles": [], "bundle_count": 0},
        "topoisomerase_tension_relief_v2_9.json": {"status": "PENDING_GITHUB_ACTIONS", "records": records},
        "materialization_tension_relief_log_v2_9.json": {"status": "PENDING_GITHUB_ACTIONS", "records": records},
        "heterochromatin_monitor_v2_9.json": {"status": "PENDING_GITHUB_ACTIONS", "records": records},
        "silent_scaffolding_risk_audit_v2_9.json": {"status": "PENDING_GITHUB_ACTIONS", "records": records},
        "phase_inversion_seed_constraint_check_v2_9.json": {"status": "PENDING_GITHUB_ACTIONS", "records": []},
        "topological_candidate_pool_v2_9.json": {"status": "PENDING_GITHUB_ACTIONS", "full_candidate_pool": NON_ANSIBLE, "non_ansible_candidates": NON_ANSIBLE, "selected_candidates": NON_ANSIBLE, "decision_time_safety_check": "PENDING_GITHUB_ACTIONS"},
        "repair_path_taxonomy_v2_9.json": {"status": "PENDING_GITHUB_ACTIONS", "records": records, "taxonomy_assigned_before_heuristic_selection": True},
        "environmental_stress_state_v2_9.json": pass_pending,
        "candidate_senescence_policy_v2_9.json": pass_pending,
        "checkpoint_cycle_manifest_v2_9.json": pass_pending,
        "duplicate_clean_replay_verification_v2_9.json": {"status": "PENDING_GITHUB_ACTIONS", "duplicate_replay_supported": True},
        "repair_template_transfer_readiness_v2_9.json": {"status": "PENDING_GITHUB_ACTIONS", "transfer_success_claimed": False},
        "memory_arm_separation_check_v2_9.json": pass_pending,
        "memory_evidence_eligibility_check_v2_9.json": pass_pending,
        "observer_state_separation_check_v2_9.json": pass_pending,
        "topological_context_integrity_check_v2_9.json": pass_pending,
        "isomorphism_requirements_matrix_v2_9.json": isomorphism_matrix(),
        "positive_memory_family_generalization_v2_9.json": {"status": "PENDING_GITHUB_ACTIONS", "positive_memory_only_candidates": POSITIVE_BASELINE, "family_generalization": "PENDING_GITHUB_ACTIONS"},
        "harness_sanity_check.json": pass_pending,
        "command_normalization_policy.json": {"raw_pytest_command_policy": "normalize pytest to python -m pytest", "returncode_127_policy": "harness/command normalization failure"},
        "candidate_chromatin_state_v2_9.json": pass_pending,
        "local_tension_relief_v2_9.json": pass_pending,
        "minimal_probe_selection_v2_9.json": {"status": "PENDING_GITHUB_ACTIONS", "selected_candidates": NON_ANSIBLE},
        "candidate_triage_stability_audit_v2_9.json": pass_pending,
        "closure_scaling_audit.json": pass_pending,
        "memory_lift_decomposition.json": {"repair_outcome_memory_lift": {"label": "replicated_positive_memory_signal_preserved"}, "selection_memory_lift": {"label": "insufficient_evidence"}, "stability_memory_lift": {"label": "insufficient_evidence"}, "global_closure_memory_lift": {"label": "insufficient_evidence"}, "main_benchmark_memory_lift_status": "not_demonstrated"},
        "broad_candidate_preflight_registry.json": load_json(V28W_OUTPUT_DIR / "broad_candidate_preflight_registry.json") or {"records": []},
        "replacement_candidate_policy.json": {"v2_8w_baseline_gate_required": True, "fixed_or_gold_patch_used": False, "future_outcome_evidence_used": False},
        "replacement_candidate_preflight_summary.json": pass_pending,
        "fixture_dependency_preflight_summary.json": pass_pending,
        "candidate_ranking_policy.json": {"ranking_priority": ["non-Ansible", "loop extrusion recoverable", "low heterochromatin risk"], "fixed_gold_future_forbidden_for_both_arms": True},
        "bounded_repair_proposer_summary.json": pass_pending,
        "candidate_pool.json": {"baseline_candidates": BASELINE, "non_ansible_candidates": NON_ANSIBLE},
        "candidate_source_integrity_check.json": {"fixed_or_gold_patch_used_at_decision_time": False, "future_outcome_evidence_used_at_decision_time": False},
        "decision_time_policy.json": {"fixed_revision_contents_allowed": False, "gold_patch_allowed": False, "future_post_repair_logs_allowed": False, "hidden_labels_allowed": False},
        "anti_leakage_policy.json": {"no_fixed_or_gold_patch": True, "no_future_outcome_evidence": True, "tests_may_be_modified": False, "source_only_repair_patch": True},
        "source_discovery_summary.json": pass_pending,
        "pre_repair_replay_gate_summary.json": pass_pending,
        "workspace_equivalence_summary.json": {"status": "PENDING_GITHUB_ACTIONS", "separate_no_memory_and_memory_workspaces": True},
        "source_repair_vs_harness_separation.json": {"source_only_repair_patch_required": True, "tests_may_be_modified_as_repair": False, "harness_materialization_is_not_repair": True},
        "classification_vocabulary_check.json": {"status": "PENDING_UNTIL_FINAL_RECORDS"},
        "audit.json": {"status": "PENDING_GITHUB_ACTIONS"},
        "package_verification.json": {"artifact_package": "v2_9_topological_source_discovery_artifacts", "generated_by": "local v2.9 prep checkpoint", "full_scoring_allowed": False},
        "artifact_sha256_verification.json": {"v2_9_zip_sha256_available_after_download": False},
    }
    for name in REQUIRED_TOP_LEVEL:
        if name == "SHA256SUMS.txt":
            continue
        data = artifact_map.get(name, pass_pending)
        if name.endswith(".md"):
            write_text(OUTPUT_DIR / name, "# v2.9 Topological Source Discovery\n\nStatus: `blocked_pending_v2_9_topological_source_discovery_artifact`.\n")
        else:
            write_json(OUTPUT_DIR / name, data)
    write_manifest(OUTPUT_DIR)
    append_summary_block()


def main() -> int:
    prepare()
    print("v2.9 topological source discovery checkpoint prepared")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
