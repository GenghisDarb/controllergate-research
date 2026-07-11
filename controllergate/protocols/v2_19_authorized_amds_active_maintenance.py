from __future__ import annotations

from importlib import import_module
from typing import Any, Callable


PROTOCOL_VERSION = "v2.19"
PROTOCOL_NAME = "authorized_amds_active_maintenance_lane"

RUNTIME_BINDINGS: dict[str, str] = {
    "ingest_candidate_manifest": "controllergate.runtime.authorized_maintenance:ingest_candidate_manifest",
    "verify_candidate_identity": "controllergate.runtime.authorized_maintenance:verify_candidate_identity",
    "acquire_source": "controllergate.runtime.authorized_maintenance:acquire_source",
    "reconstruct_environment": "controllergate.runtime.authorized_maintenance:reconstruct_environment",
    "resolve_provider_closure": "controllergate.runtime.authorized_maintenance:resolve_provider_closure",
    "resolve_cargo_provider": "controllergate.runtime.authorized_maintenance:resolve_cargo_provider",
    "recover_authoritative_command": "controllergate.runtime.authorized_maintenance:recover_authoritative_command",
    "verify_harness_origin": "controllergate.runtime.authorized_maintenance:verify_harness_origin",
    "verify_runner_target_origin": "controllergate.runtime.authorized_maintenance:verify_runner_target_origin",
    "build_amds_board_from_evidence": "controllergate.amds.generic_board:build_board_from_evidence",
    "run_amds_active_loop": "controllergate.amds.runtime_adapter:run_amds_active_loop",
    "reproduce_prerepair_failure": "controllergate.runtime.authorized_maintenance:reproduce_prerepair_failure",
    "classify_failure_ownership": "controllergate.runtime.authorized_maintenance:classify_failure_ownership",
    "derive_patch_locality": "controllergate.runtime.authorized_maintenance:derive_patch_locality",
    "authorize_source_patch": "controllergate.runtime.authorized_maintenance:authorize_source_patch",
    "generate_bounded_source_patch": "controllergate.runtime.authorized_maintenance:generate_bounded_source_patch",
    "validate_target_and_invariants": "controllergate.runtime.authorized_maintenance:validate_target_and_invariants",
    "run_duplicate_clean_replay": "controllergate.runtime.authorized_maintenance:run_duplicate_clean_replay",
    "execute_count_gate": "controllergate.runtime.authorized_maintenance:execute_count_gate",
    "rollback_candidate": "controllergate.runtime.authorized_maintenance:rollback_candidate",
    "update_proof_ledger": "controllergate.runtime.authorized_maintenance:update_proof_ledger",
    "update_routing_memory": "controllergate.runtime.authorized_maintenance:update_routing_memory",
}


def resolve_binding(name: str) -> Callable[..., Any]:
    target = RUNTIME_BINDINGS.get(name)
    if target is None: raise KeyError(f"unknown_v2_19_runtime_binding:{name}")
    module_name, function_name = target.split(":", 1); function = getattr(import_module(module_name), function_name)
    if not callable(function): raise TypeError(f"v2_19_runtime_binding_not_callable:{name}")
    return function


def runtime_capabilities() -> dict[str, Any]:
    resolved = {name: callable(resolve_binding(name)) for name in RUNTIME_BINDINGS}
    batch_specific = [name for name in RUNTIME_BINDINGS if "batch" in name.lower() or "batch" in RUNTIME_BINDINGS[name].lower()]
    return {"status": "PASS" if all(resolved.values()) and not batch_specific else "FAIL", "protocol_version": PROTOCOL_VERSION, "protocol_name": PROTOCOL_NAME, "runtime_binding_count": len(RUNTIME_BINDINGS), "bindings": RUNTIME_BINDINGS, "binding_resolution": resolved, "batch_specific_current_bindings": batch_specific, "unbound_reusable_mechanisms": []}
