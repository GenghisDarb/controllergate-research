from __future__ import annotations

from importlib import import_module
from typing import Any


ALLOWED_BINDINGS = {
    "batch068h4_phase": "controllergate.runtime.batch068h4_pipeline:execute_phase",
    "batch068h5_phase": "controllergate.runtime.batch068h5_pipeline:execute_phase",
    "batch068h6_phase": "controllergate.runtime.batch068h6_pipeline:execute_phase",
    "batch068h7_phase": "controllergate.runtime.batch068h7_pipeline:execute_phase",
    "batch068h8_phase": "controllergate.runtime.batch068h8_pipeline:execute_phase",
    "ingest_candidate_manifest": "controllergate.runtime.authorized_maintenance:ingest_candidate_manifest",
    "verify_candidate_identity": "controllergate.runtime.authorized_maintenance:verify_candidate_identity",
    "acquire_source": "controllergate.runtime.authorized_maintenance:acquire_source",
    "reconstruct_environment": "controllergate.runtime.authorized_maintenance:reconstruct_environment",
    "resolve_provider_closure": "controllergate.runtime.authorized_maintenance:resolve_provider_closure",
    "resolve_cargo_provider": "controllergate.runtime.authorized_maintenance:resolve_cargo_provider",
    "recover_authoritative_command": "controllergate.runtime.authorized_maintenance:recover_authoritative_command",
    "verify_harness_origin": "controllergate.runtime.authorized_maintenance:verify_harness_origin",
    "verify_runner_target_origin": "controllergate.runtime.authorized_maintenance:verify_runner_target_origin",
    "build_amds_board_from_evidence": "controllergate.runtime.authorized_maintenance:build_amds_board_from_evidence",
    "run_amds_active_loop": "controllergate.runtime.authorized_maintenance:run_amds_active_loop_binding",
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


def execute_binding(binding: str, phase_id: str, context: dict[str, Any], network_authorization: dict[str, Any] | None = None) -> dict[str, Any]:
    target = ALLOWED_BINDINGS.get(binding)
    if target is None: return {"status": "BLOCK", "blocker": "runtime_binding_not_allowlisted", "phase_id": phase_id}
    if not binding.startswith("batch068h") and context.get("candidate_manifest", {}).get("execution_mode") == "live":
        target = f"controllergate.runtime.live_authorized_maintenance:{binding if binding != 'run_amds_active_loop' else 'run_amds_active_loop_binding'}"
    module_name, function_name = target.split(":", 1)
    function = getattr(import_module(module_name), function_name)
    if binding == "batch068h8_phase": result = function(phase_id, context, network_authorization or {"phase_id": phase_id, "network_mode": "none"})
    elif binding.startswith("batch068h"): result = function(phase_id, context)
    else: result = function(context, phase_id=phase_id, network_authorization=network_authorization or {"phase_id": phase_id, "network_mode": "none"})
    if result.get("status") not in {"PASS", "BLOCK", "MANUAL_REVIEW"}: return {"status": "BLOCK", "blocker": "runtime_phase_invalid_status", "phase_id": phase_id}
    return result
