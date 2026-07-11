from __future__ import annotations

from importlib import import_module
from typing import Any, Callable


PROTOCOL_VERSION = "v2.18"
PROTOCOL_NAME = "evidence_derived_topology_historical_provider_lane"

# Every Batch068h3 production mechanism is exposed through this canonical,
# read-only binding registry. Evidence-producing execution still requires the
# versioned workflow and its authorization records.
RUNTIME_BINDINGS: dict[str, str] = {
    "resolve_contacts": "controllergate.topology.contact_resolvers:resolve_all_contacts",
    "build_semantic_local_topology": "controllergate.topology.brot_local:build_semantic_local_brot",
    "extrude_ast_context": "controllergate.topology.ast_extrusion:extrude_source_tree",
    "classify_source_ownership": "controllergate.topology.source_ownership:classify_source_ownership",
    "trace_failure_to_source": "controllergate.topology.failure_source_trace:trace_failure_to_source",
    "derive_patch_locality": "controllergate.topology.patch_locality:derive_patch_locality",
    "build_structural_signature": "controllergate.topology.homology:structural_signature",
    "evaluate_all_candidate_pairs": "controllergate.topology.homology:evaluate_all_pairs",
    "resolve_contact_pair_obligations": "controllergate.topology.contact_pair_obligation_resolver:resolve_all_contact_pairs",
    "verify_contact_pair_cells": "controllergate.topology.contact_pair_verifiers:verify_cells",
    "run_bounded_environment_measurement": "controllergate.topology.tot_bulb_measurement:run_measurement_loop",
    "evaluate_clean_track_parent": "controllergate.topology.tld_clean_track:evaluate_parent",
    "parse_distribution_metadata": "controllergate.runtime.artifact_metadata_reader:read_artifact_metadata",
    "solve_provider_constraints": "controllergate.runtime.provider_constraint_solver:solve",
    "resolve_historical_provider_roots": "controllergate.runtime.historical_provider_resolver:resolve_from_verified_roots",
    "verify_historical_lock": "controllergate.runtime.historical_lock_verifier:verify_historical_lock",
    "execute_maintenance_order": "controllergate.core.maintenance_order_runtime:execute_maintenance_order",
    "guard_maintenance_transition": "controllergate.core.maintenance_transition_guard:guard_transition",
    "dispatch_authorized_maintenance": "controllergate.runtime.maintenance_dispatcher:dispatch",
    "reconstruct_pinned_roots": "controllergate.runtime.root_requirements:reconstruct_roots",
    "enumerate_historical_releases": "controllergate.runtime.release_catalog:enumerate_release_files",
    "resolve_recursive_provider_closure": "controllergate.runtime.recursive_provider_resolver:resolve_recursive",
    "inspect_dynamic_metadata_capsule": "controllergate.runtime.dynamic_metadata_capsule:dynamic_metadata_capability",
    "execute_batch068h4_phase": "controllergate.runtime.batch068h4_pipeline:execute_phase",
    "build_amds_board": "controllergate.runtime.batch068h5_pipeline:construct_amds_board",
    "validate_amds_board": "controllergate.amds.board:validate_board",
    "propagate_amds_constraints": "controllergate.amds.propagation:propagate_constraints",
    "enumerate_amds_probes": "controllergate.amds.probe_registry:probe_contracts",
    "rank_amds_probes": "controllergate.amds.probe_planner:rank_probes",
    "authorize_amds_probe": "controllergate.amds.runtime_adapter:authorize_amds_probe",
    "execute_amds_probe": "controllergate.amds.runtime_adapter:execute_amds_probe",
    "ingest_amds_observation": "controllergate.amds.runtime_adapter:ingest_amds_observation",
    "update_amds_board": "controllergate.amds.board:update_board",
    "close_amds_branch": "controllergate.amds.branch_closure:close_branch",
    "evaluate_amds_stop": "controllergate.amds.stop_policy:evaluate_stop",
    "run_amds_active_loop": "controllergate.amds.runtime_adapter:run_amds_active_loop",
    "execute_batch068h5_phase": "controllergate.runtime.batch068h5_pipeline:execute_phase",
}

PATHWAY_BINDINGS = {
    "incident_acquisition": "existing_runtime",
    "source_identity": "resolve_contacts",
    "environment_materialization": "run_amds_active_loop",
    "command_recovery": "resolve_contacts",
    "failure_reproduction": "guard_maintenance_transition",
    "failure_family_decomposition": "run_amds_active_loop",
    "repair_authorization": "evaluate_amds_stop",
    "candidate_patch_generation": "blocked_by_current_claim_boundary",
    "target_and_invariant_validation": "resolve_contact_pair_obligations",
    "duplicate_clean_replay": "blocked_until_first_collection_pass",
    "canary_deployment": "existing_runtime_inactive",
    "health_monitoring": "existing_runtime_inactive",
    "commit_or_rollback": "execute_maintenance_order",
    "proof_and_memory_update": "execute_maintenance_order",
}


def protocol() -> dict[str, Any]:
    return {
        "protocol_version": PROTOCOL_VERSION,
        "protocol_name": PROTOCOL_NAME,
        "runtime_binding_count": len(RUNTIME_BINDINGS),
        "unbound_reusable_mechanism_count": 0,
        "patch_authority": False,
        "target_test_execution_authority": False,
    }


def resolve_binding(name: str) -> Callable[..., Any]:
    target = RUNTIME_BINDINGS.get(name)
    if target is None:
        raise KeyError(f"unknown_v2_18_runtime_binding:{name}")
    module_name, function_name = target.split(":", 1)
    function = getattr(import_module(module_name), function_name)
    if not callable(function):
        raise TypeError(f"v2_18_runtime_binding_not_callable:{name}")
    return function


def invoke_binding(name: str, *args: Any, **kwargs: Any) -> Any:
    return resolve_binding(name)(*args, **kwargs)


def runtime_capabilities() -> dict[str, Any]:
    resolved = {name: callable(resolve_binding(name)) for name in RUNTIME_BINDINGS}
    return {
        "status": "PASS" if all(resolved.values()) else "FAIL",
        "protocol": protocol(),
        "bindings": RUNTIME_BINDINGS,
        "binding_resolution": resolved,
        "pathway_bindings": PATHWAY_BINDINGS,
        "unbound_reusable_mechanisms": [],
    }
