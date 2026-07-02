from __future__ import annotations

from typing import Any

REQUIRED_CAPABILITY_IDS = [
    "evidence_bound_repair_validation",
    "artifact_byte_custody",
    "registry_first_provenance",
    "matched_null_evaluation",
    "curvature_based_source_selection",
    "active_failure_memory_routing",
    "source_commit_environment_lock",
    "target_command_manifest",
    "fresh_workspace_purity",
    "baseline_registry_drift_precheck",
    "rollback_block_ledger",
    "runtime_incident_capture",
    "execution_boundary_gateway",
    "isolated_repair_sandbox",
    "dependency_drift_chaperone",
    "active_ast_excision_probe",
    "syntax_micro_rollback",
    "predictive_degradation_telemetry",
    "compute_budget_safe_stop",
    "cryptographic_blue_green_deployment",
    "proof_to_action_compiler",
    "lock_sequence_operation_registry",
    "structure_first_compiler_roadmap",
    "future_agentic_admissibility_compiler_integration",
]


def capability_record(capability_id: str, name: str, tier: int, evidence_paths: list[str], blockers: list[str]) -> dict[str, Any]:
    return {
        "capability_id": capability_id,
        "neutral_public_name": name,
        "translation_source": None,
        "current_tier": tier,
        "evidence_artifact_paths": evidence_paths,
        "ci_reproduction_status": "PASS" if evidence_paths else "evidence_gap_recorded",
        "blockers": blockers,
        "forbidden_overclaims": ["production readiness", "full scoring", "full memory lift"],
        "next_evidence_needed": "audited external reproduction or deterministic fixture evidence",
    }


def validate_catalog(catalog: dict[str, Any]) -> dict[str, Any]:
    capabilities = catalog.get("capabilities", [])
    ids = {item.get("capability_id") for item in capabilities if isinstance(item, dict)}
    missing = [capability_id for capability_id in REQUIRED_CAPABILITY_IDS if capability_id not in ids]
    gaps = [
        item.get("capability_id")
        for item in capabilities
        if isinstance(item, dict) and not item.get("evidence_artifact_paths") and not item.get("blockers")
    ]
    return {"status": "PASS" if not missing and not gaps else "BLOCK", "missing_capabilities": missing, "unexplained_evidence_gaps": gaps}
