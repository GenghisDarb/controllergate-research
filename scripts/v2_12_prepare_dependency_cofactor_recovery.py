#!/usr/bin/env python3
"""Prepare the local pending v2.12 dependency-cofactor recovery checkpoint."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = REPO_ROOT / "outputs" / "v2_12_dependency_cofactor_recovery"
V211_OUTPUT_DIR = REPO_ROOT / "outputs" / "v2_11_topology_aware_source_repair"
SUMMARY = REPO_ROOT / "controllergate_v1_7_beta" / "reports" / "critic_review_package" / "shareable_summary.md"

REQUIRED_TOP_LEVEL = [
    "campaign_summary.md",
    "campaign_results.json",
    "decision_report.json",
    "aggregate_report.json",
    "aggregate_bugsinpy_real_bug_memory_lift_assessment.json",
    "preserved_v2_11_baseline_gate_result.json",
    "dependency_cofactor_recovery_plan_v2_12.json",
    "python_toolbox_recovery_audit_v2_12.json",
    "declared_dependency_evidence_v2_12.json",
    "cofactor_recovery_decision_log_v2_12.json",
    "v2_11_patch_revalidation_v2_12.json",
    "pysnooper_patch_validation_v2_12.json",
    "v2_12_candidate_recovery_queue.json",
    "bounded_topology_aware_repair_proposer_v2_12.json",
    "topology_to_patch_proof_ledger_v2_12.json",
    "recovered_surface_repair_plan_v2_12.json",
    "duplicate_clean_replay_verification_v2_12.json",
    "phase_inversion_seed_constraint_check_v2_12.json",
    "memory_arm_separation_check_v2_12.json",
    "memory_evidence_eligibility_check_v2_12.json",
    "observer_state_separation_check_v2_12.json",
    "dependency_cofactor_anti_leakage_check_v2_12.json",
    "source_patch_anti_leakage_check_v2_12.json",
    "heterochromatin_monitor_v2_12.json",
    "silent_scaffolding_risk_audit_v2_12.json",
    "isomorphism_requirements_matrix_v2_12.json",
    "positive_memory_family_generalization_v2_12.json",
    "harness_sanity_check.json",
    "command_normalization_policy.json",
    "candidate_chromatin_state_v2_12.json",
    "local_tension_relief_v2_12.json",
    "minimal_probe_selection_v2_12.json",
    "candidate_triage_stability_audit_v2_12.json",
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


def write_json(path: Path, value: Any) -> None:
    write_text(path, json.dumps(value, indent=2, sort_keys=True) + "\n")


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    return value if isinstance(value, dict) else {}


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
            "current_blocker": "pending official v2.12 workflow",
            "v2_9_context_status": "official_context_available",
            "v2_10_materialization_status": "official_state_available",
            "v2_11_patch_status": "generated_unlocked" if candidate == "PySnooper:1" else "prior_state_available",
            "dependency_recovery_feasibility": "pending",
            "source_patch_feasibility": "pending",
            "duplicate_replay_feasibility": candidate.startswith("PySnooper"),
            "phase_inversion_feasibility": candidate.startswith("PySnooper"),
            "selected_for_attempt": candidate == "PySnooper:1",
            "reason": "locked queue pending official Linux execution",
        }
        for candidate in ["PySnooper:1", "PySnooper:2", "fastapi:2", "fastapi:3", "fastapi:4", "fastapi:5"]
    ]


def isomorphism_matrix() -> dict[str, Any]:
    return {
        "status": "PENDING_GITHUB_ACTIONS",
        "complete": True,
        "layers": [
            {"layer": "chromosome_chromatin_isomorphism", "required_mechanisms": ["Dependency/cofactor materialization", "Topology-aware expression repair", "Cofactor-gated validation"]},
            {"layer": "tld_isomorphism", "required_mechanisms": ["materialization-before-repair ordering", "topology-before-patch ordering", "cofactor-before-validation ordering"]},
            {"layer": "tot_brot_isomorphism", "required_mechanisms": ["Kernel constraints", "Coupler adaptation", "Shell provenance", "Triad balance", "failure-mode report"]},
            {"layer": "torus_brot_isomorphism", "required_mechanisms": ["recursive identity", "observer-state separation", "memory inheritance", "branching intelligence", "global closure", "autonomous readiness", "self-maintenance boundary"]},
        ],
    }


def append_summary_block() -> None:
    heading = "## v2.12 Dependency Cofactor Recovery and Locked Non-Ansible Repair Validation Lane"
    text = SUMMARY.read_text(encoding="utf-8") if SUMMARY.exists() else ""
    if heading in text:
        return
    block = (
        f"\n{heading}\n\n"
        "- Status: `blocked_pending_v2_12_dependency_cofactor_recovery_artifact`.\n"
        "- v2.12 preserves the v2.11 baseline, audits the PySnooper `python_toolbox` cofactor against buggy-checkout metadata, and locks any new non-Ansible result only after target validation, duplicate replay, and phase inversion.\n"
        "- Full scoring remains `NOT_RUN` / disallowed.\n"
        "- Self-maintaining software is not demonstrated.\n"
    )
    write_text(SUMMARY, text.rstrip() + "\n" + block)


def prepare() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    campaign211 = load_json(V211_OUTPUT_DIR / "campaign_results.json")
    baseline211 = load_json(V211_OUTPUT_DIR / "preserved_v2_10_baseline_gate_result.json")
    baseline = baseline211 | {
        "status": "PENDING_GITHUB_ACTIONS",
        "preserved_v2_11_baseline_gate_status": "PENDING_GITHUB_ACTIONS",
        "gate_source": "pending official v2.12 workflow",
    }
    campaign = {
        "campaign_id": "v2_12_dependency_cofactor_recovery",
        "artifact_name": "v2_12_dependency_cofactor_recovery_artifacts",
        "aggregate_result": "blocked_pending_v2_12_dependency_cofactor_recovery_artifact",
        "preserved_v2_11_baseline_gate_status": "PENDING_GITHUB_ACTIONS",
        "scoreable_episode_count": int(campaign211.get("scoreable_episode_count", 5) or 5),
        "positive_memory_episode_count": int(campaign211.get("positive_memory_episode_count", 2) or 2),
        "controllergate_full_scoring": "NOT_RUN",
        "full_scoring_allowed": False,
        "self_maintaining_software_demonstrated": False,
        "workflow_executed": False,
    }
    queue = {"status": "PENDING_GITHUB_ACTIONS", "priority_order": ["PySnooper:1", "PySnooper:2", "fastapi:2", "fastapi:3", "fastapi:4", "fastapi:5"], "records": pending_records(), "broad_candidate_search_restarted": False}
    pending = {"status": "PENDING_GITHUB_ACTIONS"}
    artifact_map: dict[str, Any] = {
        "campaign_results.json": campaign,
        "decision_report.json": {"records": [], "classification_vocabulary": [], "pending_until_linux_workflow_artifact": True},
        "aggregate_report.json": campaign,
        "aggregate_bugsinpy_real_bug_memory_lift_assessment.json": campaign,
        "preserved_v2_11_baseline_gate_result.json": baseline,
        "dependency_cofactor_recovery_plan_v2_12.json": {"status": "PENDING_GITHUB_ACTIONS", "complete": True, "records": pending_records()},
        "python_toolbox_recovery_audit_v2_12.json": {"status": "PENDING_GITHUB_ACTIONS", "complete": True, "blocker_name": "python_toolbox", "records": []},
        "declared_dependency_evidence_v2_12.json": {"status": "PENDING_GITHUB_ACTIONS", "complete": True, "records": []},
        "cofactor_recovery_decision_log_v2_12.json": {"status": "PENDING_GITHUB_ACTIONS", "records": []},
        "v2_11_patch_revalidation_v2_12.json": pending,
        "pysnooper_patch_validation_v2_12.json": {"status": "PENDING_GITHUB_ACTIONS", "records": []},
        "v2_12_candidate_recovery_queue.json": queue,
        "bounded_topology_aware_repair_proposer_v2_12.json": {"status": "PENDING_GITHUB_ACTIONS", "records": []},
        "topology_to_patch_proof_ledger_v2_12.json": {"status": "PENDING_GITHUB_ACTIONS", "records": []},
        "recovered_surface_repair_plan_v2_12.json": queue,
        "duplicate_clean_replay_verification_v2_12.json": {"status": "PENDING_GITHUB_ACTIONS", "records": []},
        "phase_inversion_seed_constraint_check_v2_12.json": {"status": "PENDING_GITHUB_ACTIONS", "records": []},
        "isomorphism_requirements_matrix_v2_12.json": isomorphism_matrix(),
        "positive_memory_family_generalization_v2_12.json": pending,
        "candidate_chromatin_state_v2_12.json": pending,
        "local_tension_relief_v2_12.json": pending,
        "minimal_probe_selection_v2_12.json": pending,
        "candidate_triage_stability_audit_v2_12.json": pending,
        "package_verification.json": {"status": "PENDING_GITHUB_ACTIONS"},
        "artifact_sha256_verification.json": {"status": "PENDING_GITHUB_ACTIONS"},
    }
    for name in REQUIRED_TOP_LEVEL:
        if name == "SHA256SUMS.txt":
            continue
        if name == "campaign_summary.md":
            write_text(
                OUTPUT_DIR / name,
                "# v2.12 Dependency Cofactor Recovery and Locked Non-Ansible Repair Validation\n\n"
                "- Status: `blocked_pending_v2_12_dependency_cofactor_recovery_artifact`.\n"
                "- Official evidence is pending the GitHub Actions run.\n",
            )
            continue
        write_json(OUTPUT_DIR / name, artifact_map.get(name, pending))
    write_manifest(OUTPUT_DIR)
    append_summary_block()


if __name__ == "__main__":
    prepare()
    print("v2.12 pending dependency cofactor recovery checkpoint prepared")
