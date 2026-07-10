from __future__ import annotations

from controllergate.core.evidence import hash_record

from .types import BasinRecord, BoundaryVolume, ContactLedger14, TotBrotGraph

ENVIRONMENT_DIMENSIONS = (
    "language_runtime", "runtime_build", "OS", "distribution", "architecture", "libc", "package_epoch", "dependency_lock",
    "build_system", "runner", "plugins", "target_origin", "test_harness", "filesystem", "permissions", "writable_paths",
    "environment_variables", "network", "CPU", "memory", "process_limits", "system_libraries", "external_services", "model_provider_dependencies",
)


def build_tot_bulb_volume(candidate_id: str, ledger: ContactLedger14, coupled: TotBrotGraph, global_mask: dict[str, object], candidate_mask: dict[str, object], selected_dimensions: tuple[str, ...]) -> BoundaryVolume:
    if not candidate_id or not candidate_mask.get("candidate_identity_established"):
        raise ValueError("candidate_identity_required_before_candidate_mask")
    if not selected_dimensions or any(item not in ENVIRONMENT_DIMENSIONS for item in selected_dimensions):
        raise ValueError("evidence_selected_basin_required")
    edge_hash = hash_record(coupled.as_dict())
    basin = BasinRecord(f"{candidate_id}:targeted-basin", edge_hash, True, selected_dimensions)
    blocked_contacts = [item.contact_id for item in ledger.contacts if item.gate_decision == "BLOCK"]
    cells = tuple({"coordinate": {"contact_role": contact, "environment_dimension": dimension, "runtime_phase": "materialization", "evidence_epoch": "decision_time"},
                   "observed_state": candidate_mask.get(dimension, "NOT_ESTABLISHED"), "requested_state": "ESTABLISHED", "orthology_status": candidate_mask.get(dimension, "NOT_ESTABLISHED"),
                   "evidence_hash": hash_record({"candidate": candidate_id, "contact": contact, "dimension": dimension}), "boundary_classification": "environment_boundary",
                   "confidence": 0.5, "associated_contact_ids": [contact], "associated_failure_family_ids": ["FF-002"], "interlocks": ["environment_orthology", "claim_boundary"],
                   "legal_next_probes": ["historical_capsule_evidence_probe"]} for contact in blocked_contacts for dimension in selected_dimensions)
    return BoundaryVolume(candidate_id, global_mask, candidate_mask, (basin,), cells)
