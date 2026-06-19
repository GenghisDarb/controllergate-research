#!/usr/bin/env python3
"""Prepare local v2.11 topology-aware source repair checkpoint artifacts."""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = REPO_ROOT / "outputs" / "v2_11_topology_aware_source_repair"
V210_OUTPUT_DIR = REPO_ROOT / "outputs" / "v2_10_materialization_recovery_topological_repair"
SUMMARY = REPO_ROOT / "controllergate_v1_7_beta" / "reports" / "critic_review_package" / "shareable_summary.md"

BASELINE = ["youtube-dl:1", "black:4", "fastapi:1", "ansible:2", "ansible:5"]
POSITIVE_BASELINE = ["ansible:2", "ansible:5"]
RECOVERED = ["fastapi:2", "fastapi:3", "fastapi:4", "PySnooper:1"]
CONTEXT_ONLY = ["PySnooper:2", "fastapi:5"]
ALL_CANDIDATES = RECOVERED + CONTEXT_ONLY

REQUIRED_TOP_LEVEL = [
    "campaign_summary.md",
    "campaign_results.json",
    "decision_report.json",
    "aggregate_report.json",
    "aggregate_bugsinpy_real_bug_memory_lift_assessment.json",
    "preserved_v2_10_baseline_gate_result.json",
    "recovered_surface_repair_plan_v2_11.json",
    "bounded_topology_aware_repair_proposer_v2_11.json",
    "topology_to_patch_proof_ledger_v2_11.json",
    "topology_aware_repair_candidate_pool_v2_11.json",
    "duplicate_clean_replay_verification_v2_11.json",
    "phase_inversion_seed_constraint_check_v2_11.json",
    "heterochromatin_monitor_v2_11.json",
    "silent_scaffolding_risk_audit_v2_11.json",
    "memory_arm_separation_check_v2_11.json",
    "memory_evidence_eligibility_check_v2_11.json",
    "observer_state_separation_check_v2_11.json",
    "topology_aware_repair_integrity_check_v2_11.json",
    "source_patch_anti_leakage_check_v2_11.json",
    "isomorphism_requirements_matrix_v2_11.json",
    "positive_memory_family_generalization_v2_11.json",
    "harness_sanity_check.json",
    "command_normalization_policy.json",
    "candidate_chromatin_state_v2_11.json",
    "local_tension_relief_v2_11.json",
    "minimal_probe_selection_v2_11.json",
    "candidate_triage_stability_audit_v2_11.json",
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
    v210_recovery = load_json(V210_OUTPUT_DIR / "bounded_dependency_materialization_recovery_v2_10.json")
    recovery_by_candidate = {
        str(record.get("candidate")): record
        for record in v210_recovery.get("records", [])
        if isinstance(record, dict) and record.get("candidate")
    }
    records: list[dict[str, Any]] = []
    for candidate in ALL_CANDIDATES:
        recovery = recovery_by_candidate.get(candidate, {})
        records.append(
            {
                "candidate": candidate,
                "project_family": candidate.split(":", 1)[0],
                "v2_10_materialization_status": recovery.get("materialization_status_after", "PENDING_GITHUB_ACTIONS"),
                "v2_10_materialization_recovered": recovery.get("materialization_recovered", "PENDING_GITHUB_ACTIONS"),
                "v2_11_repair_path": "PENDING_GITHUB_ACTIONS",
                "repair_attempt_allowed": candidate in RECOVERED,
                "decision_time_safe_status": "PENDING_GITHUB_ACTIONS",
            }
        )
    return records


def isomorphism_matrix() -> dict[str, Any]:
    layers = ["chromosome_chromatin_isomorphism", "tld_isomorphism", "tot_brot_isomorphism", "torus_brot_isomorphism"]
    return {
        "status": "PENDING_GITHUB_ACTIONS",
        "complete": True,
        "layers": [
            {
                "layer": layer,
                "required_mechanisms": ["baseline preservation", "topology-before-patch ordering", "source-only repair boundary"],
                "implemented_mechanisms": [],
                "partially_implemented_mechanisms": ["prepared by v2.11 checkpoint"],
                "missing_mechanisms": [],
                "tested_this_run": "PENDING_GITHUB_ACTIONS",
                "passed_requirements": [],
                "failed_requirements": [],
                "next_required_layer": "official v2.11 workflow",
                "evidence_files": ["recovered_surface_repair_plan_v2_11.json"],
            }
            for layer in layers
        ],
    }


def append_summary_block() -> None:
    block = """## v2.11 Topology-Aware Source Repair

- Status: `blocked_pending_v2_11_topology_aware_source_repair_artifact`.
- v2.11 preserves the v2.10 baseline, uses v2.9/v2.10 recovered context, and attempts bounded topology-aware source-only repairs on recovered non-Ansible surfaces.
- Full scoring remains `NOT_RUN` / disallowed.
- Self-maintaining software is not demonstrated.
"""
    existing = SUMMARY.read_text(encoding="utf-8", errors="replace") if SUMMARY.exists() else ""
    marker = "## v2.11 Topology-Aware Source Repair"
    if marker in existing:
        existing = existing[: existing.index(marker)].rstrip() + "\n\n"
    write_text(SUMMARY, existing.rstrip() + "\n\n" + block)


def prepare() -> None:
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    v210_campaign = load_json(V210_OUTPUT_DIR / "campaign_results.json")
    records = pending_records()
    campaign = {
        "workflow_executed": False,
        "campaign_id": "v2_11_topology_aware_source_repair",
        "artifact_name": "v2_11_topology_aware_source_repair_artifacts",
        "aggregate_result": "blocked_pending_v2_11_topology_aware_source_repair_artifact",
        "executed_episode_count": 0,
        "scoreable_episode_count": 0,
        "replacement_scoreable_count": 0,
        "positive_memory_episode_count": 0,
        "selected_candidates": ALL_CANDIDATES,
        "attempted_candidates": RECOVERED,
        "candidate_families_attempted": [],
        "preserved_v2_10_baseline_gate_status": "PENDING_GITHUB_ACTIONS",
        "full_scoring_allowed": False,
        "controllergate_full_scoring": "NOT_RUN",
        "self_maintaining_software_demonstrated": False,
        "v2_10_prerequisite_aggregate_result": v210_campaign.get("aggregate_result", "unknown"),
        "tooling_note": "v2.10 artifact handling failure was a session tooling surface issue, not ControllerGate evidence.",
    }
    pending = {"status": "PENDING_GITHUB_ACTIONS"}
    artifact_map: dict[str, Any] = {
        "campaign_results.json": campaign,
        "aggregate_report.json": campaign,
        "aggregate_bugsinpy_real_bug_memory_lift_assessment.json": campaign | {"limited_bugsinpy_real_bug_memory_lift_criteria_met": False},
        "decision_report.json": {"records": [], "classification_vocabulary": [], "pending_until_linux_workflow_artifact": True},
        "preserved_v2_10_baseline_gate_result.json": {"status": "PENDING_GITHUB_ACTIONS", "baseline_candidates": BASELINE, "positive_memory_only_preservation_status": {candidate: "PENDING_GITHUB_ACTIONS" for candidate in POSITIVE_BASELINE}},
        "recovered_surface_repair_plan_v2_11.json": {"status": "PENDING_GITHUB_ACTIONS", "records": records},
        "bounded_topology_aware_repair_proposer_v2_11.json": {"status": "PENDING_GITHUB_ACTIONS", "records": records},
        "topology_to_patch_proof_ledger_v2_11.json": {"status": "PENDING_GITHUB_ACTIONS", "records": []},
        "topology_aware_repair_candidate_pool_v2_11.json": {"status": "PENDING_GITHUB_ACTIONS", "full_candidate_pool": ALL_CANDIDATES, "selected_candidates": RECOVERED},
        "duplicate_clean_replay_verification_v2_11.json": {"status": "PENDING_GITHUB_ACTIONS", "duplicate_replay_supported": True, "records": []},
        "phase_inversion_seed_constraint_check_v2_11.json": {"status": "PENDING_GITHUB_ACTIONS", "records": []},
        "heterochromatin_monitor_v2_11.json": {"status": "PENDING_GITHUB_ACTIONS", "records": records},
        "silent_scaffolding_risk_audit_v2_11.json": {"status": "PENDING_GITHUB_ACTIONS", "records": records},
        "memory_arm_separation_check_v2_11.json": pending,
        "memory_evidence_eligibility_check_v2_11.json": pending,
        "observer_state_separation_check_v2_11.json": pending,
        "topology_aware_repair_integrity_check_v2_11.json": pending,
        "source_patch_anti_leakage_check_v2_11.json": pending,
        "isomorphism_requirements_matrix_v2_11.json": isomorphism_matrix(),
        "positive_memory_family_generalization_v2_11.json": {"status": "PENDING_GITHUB_ACTIONS", "non_ansible_positive_memory_count": 0, "cross_family_positive_memory_signal_suggestive": False},
        "harness_sanity_check.json": pending,
        "command_normalization_policy.json": pending,
        "candidate_chromatin_state_v2_11.json": pending,
        "local_tension_relief_v2_11.json": pending,
        "minimal_probe_selection_v2_11.json": pending,
        "candidate_triage_stability_audit_v2_11.json": pending,
        "closure_scaling_audit.json": pending,
        "memory_lift_decomposition.json": pending,
        "broad_candidate_preflight_registry.json": {"records": [], "count": 0},
        "replacement_candidate_policy.json": pending,
        "replacement_candidate_preflight_summary.json": pending,
        "fixture_dependency_preflight_summary.json": pending,
        "candidate_ranking_policy.json": pending,
        "bounded_repair_proposer_summary.json": pending,
        "candidate_pool.json": {"baseline_candidates": BASELINE, "non_ansible_candidates": ALL_CANDIDATES},
        "candidate_source_integrity_check.json": pending,
        "decision_time_policy.json": pending,
        "anti_leakage_policy.json": pending,
        "source_discovery_summary.json": pending,
        "pre_repair_replay_gate_summary.json": pending,
        "workspace_equivalence_summary.json": pending,
        "source_repair_vs_harness_separation.json": pending,
        "classification_vocabulary_check.json": {"status": "PENDING_GITHUB_ACTIONS", "allowed_vocabulary": []},
        "audit.json": pending,
        "package_verification.json": {"status": "PENDING_GITHUB_ACTIONS"},
        "artifact_sha256_verification.json": {"status": "PENDING_GITHUB_ACTIONS"},
    }
    for name in REQUIRED_TOP_LEVEL:
        if name == "SHA256SUMS.txt":
            continue
        write_json(OUTPUT_DIR / name, artifact_map.get(name, pending))
    write_text(
        OUTPUT_DIR / "campaign_summary.md",
        "# v2.11 Topology-Aware Source Repair\n\n"
        "- Status: `blocked_pending_v2_11_topology_aware_source_repair_artifact`.\n"
        "- Official evidence is pending the GitHub Actions run.\n",
    )
    write_manifest(OUTPUT_DIR)
    append_summary_block()


if __name__ == "__main__":
    prepare()
