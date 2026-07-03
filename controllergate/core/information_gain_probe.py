from __future__ import annotations

from typing import Any

from .active_probe_selection import PROBE_TYPES, probe_selection_formula, select_probe
from .search_space_geometry import stable_record_hash


def information_gain_probe_policy() -> dict[str, Any]:
    return {
        "status": "PASS",
        "allowed_probe_types": PROBE_TYPES,
        "selection_formula": probe_selection_formula(),
        "deterministic": True,
        "input_evidence_hash_required": True,
        "forbidden_evidence_allowed": False,
        "mutates_external_target_repos": False,
    }


def build_probe_candidate_registry(feature_vector: dict[str, Any]) -> list[dict[str, Any]]:
    evidence_hash = stable_record_hash(feature_vector)
    dependency_needed = feature_vector.get("dependency_lock_status") != "PASS"
    probes = [
        {
            "probe_id": "batch019_dependency_lock_probe",
            "probe_type": "dependency_lock_probe",
            "candidate_id": feature_vector.get("candidate_id"),
            "input_evidence_hash": evidence_hash,
            "expected_information_gain": 8 if dependency_needed else 2,
            "expected_probe_cost": 1,
            "expected_probe_risk": 1,
            "provenance_uncertainty_penalty": 0,
            "dependency_uncertainty_penalty": 1 if dependency_needed else 0,
            "claim_boundary_penalty": 0,
            "forbidden_evidence_used": False,
        },
        {
            "probe_id": "batch019_seed_replacement_probe",
            "probe_type": "seed_replacement_probe",
            "candidate_id": feature_vector.get("candidate_id"),
            "input_evidence_hash": evidence_hash,
            "expected_information_gain": 5,
            "expected_probe_cost": 2,
            "expected_probe_risk": 1,
            "provenance_uncertainty_penalty": 1,
            "dependency_uncertainty_penalty": 0,
            "claim_boundary_penalty": 0,
            "forbidden_evidence_used": False,
        },
    ]
    return probes


def probe_selection_status(feature_vector: dict[str, Any]) -> dict[str, Any]:
    registry = build_probe_candidate_registry(feature_vector)
    decision = select_probe(registry)
    return {
        "status": decision["status"],
        "probe_registry_count": len(registry),
        "selected_probe_type": decision.get("selected_probe", {}).get("probe_type") if decision.get("selected_probe") else None,
        "selected_probe_id": decision.get("selected_probe", {}).get("probe_id") if decision.get("selected_probe") else None,
        "blocker": decision.get("blocker"),
    }
