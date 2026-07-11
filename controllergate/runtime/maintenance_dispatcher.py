from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from controllergate.core.evidence import hash_record
from .event_ledger import RuntimeEvent, append_event
from .execution_authorization import verify_authorization
from .execution_checkpoint import RuntimeCheckpoint, load_checkpoint, write_checkpoint
from .execution_plan import plan_from_dict, verify_plan
from .phase_executor import execute_binding
from .network_policy import validate_network_policy


GENERIC_MAINTENANCE_PHASES = (
    "ingest_candidate_manifest", "verify_candidate_identity", "acquire_source",
    "reconstruct_environment", "resolve_provider_closure", "resolve_cargo_provider",
    "recover_authoritative_command", "verify_harness_origin", "verify_runner_target_origin",
    "reproduce_prerepair_failure", "build_amds_board_from_evidence", "run_amds_active_loop",
    "classify_failure_ownership", "derive_patch_locality", "authorize_source_patch",
    "generate_bounded_source_patch", "validate_target_and_invariants",
    "run_duplicate_clean_replay", "execute_count_gate", "update_proof_ledger",
    "update_routing_memory",
)


def dispatch_candidate_manifest(*, manifest: dict[str, Any], checkpoint_path: Path, event_ledger_path: Path, authorization_store: Path) -> dict[str, Any]:
    manifest_hash = hash_record(manifest); candidate_id = str(manifest.get("candidate_id", "")); candidate_sha = str(manifest.get("candidate_sha", ""))
    checkpoint = load_checkpoint(checkpoint_path)
    if checkpoint.get("status") == "PASS" and (checkpoint.get("candidate_id") != candidate_id or checkpoint.get("plan_hash") != manifest_hash):
        return {"status": "BLOCK", "blocker": "runtime_checkpoint_plan_or_candidate_mismatch"}
    completed = list(checkpoint.get("completed_phases", [])); chain = str(checkpoint.get("event_chain_head", "0" * 64)); context = dict(checkpoint.get("context_state") or {"candidate_manifest": manifest, "authorization_store": str(authorization_store)}); executed = []
    for phase_id in GENERIC_MAINTENANCE_PHASES:
        if phase_id in completed: continue
        input_hash = hash_record({"phase": phase_id, "context": context, "chain": chain})
        network_mode = "bounded_read_only" if phase_id in {"acquire_source", "reconstruct_environment"} and manifest.get("execution_mode") == "live" else "none"
        result = execute_binding(phase_id, phase_id, context, {"phase_id": phase_id, "network_mode": network_mode})
        event = append_event(event_ledger_path, RuntimeEvent(f"event-{len(completed)+1:03d}", phase_id, str(result["status"]), input_hash, hash_record(result), result.get("blocker"), chain)); chain = str(event["event_hash"]); executed.append(phase_id)
        context.update(result.get("context_updates", {}))
        if result["status"] == "PASS": completed.append(phase_id); continue
        terminal = result["status"] in {"BLOCK", "MANUAL_REVIEW"}
        if terminal:
            context["terminal_decision"] = {"phase_id": phase_id, "status": result["status"], "blocker": result.get("blocker")}
            for cleanup_id in ("rollback_candidate", "update_proof_ledger", "update_routing_memory"):
                if cleanup_id in completed:
                    continue
                cleanup_input = hash_record({"phase": cleanup_id, "context": context, "chain": chain})
                cleanup = execute_binding(cleanup_id, cleanup_id, context, {"phase_id": cleanup_id, "network_mode": "none"})
                cleanup_event = append_event(event_ledger_path, RuntimeEvent(f"event-{len(completed)+1:03d}", cleanup_id, str(cleanup["status"]), cleanup_input, hash_record(cleanup), cleanup.get("blocker"), chain))
                chain = str(cleanup_event["event_hash"]); executed.append(cleanup_id); context.update(cleanup.get("context_updates", {}))
                if cleanup["status"] == "PASS": completed.append(cleanup_id)
        write_checkpoint(checkpoint_path, RuntimeCheckpoint(candidate_id, manifest_hash, tuple(completed), str(result["status"]), result.get("blocker"), (), chain, context_state=context))
        return {"status": str(result["status"]), "blocker": result.get("blocker"), "terminal_prepatch": terminal, "phase_id": phase_id, "executed_phases": executed, "completed_phases": completed, "checkpoint_status": "PASS", "resume_status": "SAFE", "context": context}
    write_checkpoint(checkpoint_path, RuntimeCheckpoint(candidate_id, manifest_hash, tuple(completed), "PASS", None, (), chain, context_state=context))
    return {"status": "PASS", "blocker": None, "terminal_prepatch": False, "executed_phases": executed, "completed_phases": completed, "checkpoint_status": "PASS", "resume_status": "SAFE", "context": context}


def dispatch(*, candidate_id: str, candidate_sha: str, current_state_hash: str, authorization_path: Path, plan_path: Path, checkpoint_path: Path, event_ledger_path: Path) -> dict[str, Any]:
    if not authorization_path.is_file(): return {"status": "BLOCK", "blocker": "execution_authorization_manifest_required"}
    plan_value = json.loads(plan_path.read_text(encoding="utf-8")); plan_check = verify_plan(plan_value)
    if plan_check["status"] != "PASS": return plan_check
    plan = plan_from_dict(plan_value)
    if plan.candidate_id != candidate_id or plan.candidate_sha != candidate_sha: return {"status": "BLOCK", "blocker": "execution_plan_candidate_mismatch"}
    checkpoint = load_checkpoint(checkpoint_path)
    if checkpoint.get("status") == "BLOCK": return checkpoint
    if checkpoint.get("status") == "PASS" and (checkpoint.get("candidate_id") != candidate_id or checkpoint.get("plan_hash") != plan.plan_hash): return {"status": "BLOCK", "blocker": "runtime_checkpoint_plan_or_candidate_mismatch"}
    completed = list(checkpoint.get("completed_phases", [])); spent = set(checkpoint.get("spent_nonces", [])); chain = str(checkpoint.get("event_chain_head", "0" * 64))
    authorization_value = json.loads(authorization_path.read_text(encoding="utf-8"))
    auth = verify_authorization(authorization_value, candidate_id=candidate_id, candidate_sha=candidate_sha, current_state_hash=current_state_hash, plan_hash=plan.plan_hash, spent_nonces=spent)
    if auth["status"] != "PASS": return auth
    allowed = set(auth["allowed_phases"])
    context = json.loads(Path(plan.context_path).read_text(encoding="utf-8")); executed = []
    for phase in plan.phases:
        if phase.phase_id in completed:
            if not phase.replay_authorized: continue
        if phase.phase_id not in allowed: return {"status": "BLOCK", "blocker": "phase_not_authorized", "phase_id": phase.phase_id}
        if any(parent not in completed for parent in phase.depends_on): return {"status": "BLOCK", "blocker": "runtime_phase_skip_rejected", "phase_id": phase.phase_id}
        input_hash = hash_record({"phase": phase.phase_id, "context": context, "chain": chain})
        policy = next((item for item in auth.get("network_policies", []) if item.get("phase_id") == phase.phase_id), {"phase_id": phase.phase_id, "network_mode": "none", "allowed_network_destinations": [], "allowed_protocols": [], "maximum_requests": 0, "maximum_download_bytes": 0})
        policy_check = validate_network_policy(policy, phase_id=phase.phase_id)
        if policy_check["status"] != "PASS": return {**policy_check, "phase_id": phase.phase_id}
        if phase.phase_id in set(auth.get("network_phases", [])) and policy.get("network_mode") != "bounded_read_only": return {"status": "BLOCK", "blocker": "network_enabled_phase_policy_missing", "phase_id": phase.phase_id}
        if phase.phase_id not in set(auth.get("network_phases", [])) and policy.get("network_mode") != "none": return {"status": "BLOCK", "blocker": "network_phase_absent_from_authorization", "phase_id": phase.phase_id}
        result = execute_binding(phase.binding, phase.phase_id, context, policy); output_hash = hash_record(result)
        event = append_event(event_ledger_path, RuntimeEvent(f"event-{len(completed)+1:03d}", phase.phase_id, str(result["status"]), input_hash, output_hash, result.get("blocker"), chain))
        chain = str(event["event_hash"]); executed.append(phase.phase_id)
        context.update(result.get("context_updates", {})); Path(plan.context_path).write_text(json.dumps(context, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        if result["status"] == "PASS": completed.append(phase.phase_id)
        else:
            spent.add(str(auth["nonce"])); write_checkpoint(checkpoint_path, RuntimeCheckpoint(candidate_id, plan.plan_hash, tuple(completed), str(result["status"]), result.get("blocker"), tuple(sorted(spent)), chain))
            return {"status": str(result["status"]), "blocker": result.get("blocker"), "phase_id": phase.phase_id, "executed_phases": executed, "completed_phases": completed, "checkpoint_status": "PASS", "resume_status": "SAFE"}
    spent.add(str(auth["nonce"])); write_checkpoint(checkpoint_path, RuntimeCheckpoint(candidate_id, plan.plan_hash, tuple(completed), "PASS", None, tuple(sorted(spent)), chain))
    return {"status": "PASS", "blocker": None, "executed_phases": executed, "completed_phases": completed, "checkpoint_status": "PASS", "resume_status": "SAFE"}
