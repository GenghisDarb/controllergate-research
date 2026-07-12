from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from controllergate.core.evidence import hash_record
from .candidate_execution_authorization import verify_candidate_authorization
from .candidate_execution_plan import parse_candidate_plan, verify_candidate_plan
from .event_ledger import RuntimeEvent, append_event
from .execution_checkpoint import RuntimeCheckpoint, load_checkpoint, write_checkpoint
from .network_authorization import authorize_network_operation
from .network_event_ledger import append_network_event, verify_network_event_ledger
from .phase_executor import execute_binding


def dispatch_authorized_candidate(
    *, manifest_path: str | Path, authorization_path: str | Path,
    plan_path: str | Path, checkpoint_path: str | Path,
    event_ledger_path: str | Path, network_ledger_path: str | Path,
    authorization_store: str | Path,
) -> dict[str, Any]:
    paths = [Path(item) for item in (manifest_path, authorization_path, plan_path)]
    if not all(path.is_file() for path in paths):
        return {"status": "BLOCK", "blocker": "candidate_execution_authorization_inputs_missing"}
    manifest = json.loads(paths[0].read_text(encoding="utf-8"))
    plan_value = json.loads(paths[2].read_text(encoding="utf-8"))
    plan_check = verify_candidate_plan(plan_value, allowed_output_root=manifest.get("allowed_output_root"))
    if plan_check["status"] != "PASS":
        return plan_check
    plan = parse_candidate_plan(plan_value)
    if plan.candidate_id != manifest.get("candidate_id") or plan.candidate_sha != manifest.get("candidate_sha"):
        return {"status": "BLOCK", "blocker": "candidate_execution_plan_manifest_mismatch"}
    checkpoint = load_checkpoint(Path(checkpoint_path))
    if checkpoint.get("status") == "BLOCK":
        return checkpoint
    store_path = Path(authorization_store)
    store = json.loads(store_path.read_text(encoding="utf-8")) if store_path.is_file() else {"spent_nonces": []}
    spent = set(store.get("spent_nonces", []))
    authorization = json.loads(paths[1].read_text(encoding="utf-8"))
    auth_check = verify_candidate_authorization(
        authorization,
        candidate_id=plan.candidate_id,
        candidate_sha=plan.candidate_sha,
        current_state_hash=hash_record(manifest),
        plan_hash=plan.plan_hash,
        spent_nonces=spent,
        output_root=plan.output_root,
    )
    if auth_check["status"] != "PASS":
        return auth_check
    auth = authorization
    completed = list(checkpoint.get("completed_phases", []))
    if checkpoint.get("status") == "PASS" and checkpoint.get("candidate_id") not in {None, plan.candidate_id}:
        return {"status": "BLOCK", "blocker": "runtime_checkpoint_plan_or_candidate_mismatch"}
    if checkpoint.get("status") == "PASS" and checkpoint.get("plan_hash") not in {None, plan.plan_hash}:
        return {"status": "BLOCK", "blocker": "runtime_checkpoint_plan_or_candidate_mismatch"}
    chain = str(checkpoint.get("event_chain_head", "0" * 64))
    context = dict(checkpoint.get("context_state") or {"candidate_manifest": manifest})
    executed: list[str] = []
    for phase in plan.phases:
        if phase.phase_id in completed:
            continue
        if phase.phase_id not in set(auth["allowed_phases"]):
            return {"status": "BLOCK", "blocker": "phase_not_authorized", "phase_id": phase.phase_id}
        if any(parent not in completed for parent in phase.depends_on):
            return {"status": "BLOCK", "blocker": "runtime_phase_skip_rejected", "phase_id": phase.phase_id}
        network_enabled = phase.phase_id in set(auth["network_enabled_phases"])
        expected_mode = "bounded_read_only" if network_enabled else "none"
        if phase.network_mode != expected_mode:
            return {"status": "BLOCK", "blocker": "network_phase_authorization_mismatch", "phase_id": phase.phase_id}
        if phase.test_mutation_allowed:
            return {"status": "BLOCK", "blocker": "candidate_execution_test_mutation_forbidden", "phase_id": phase.phase_id}
        if phase.source_mutation_allowed and not auth["mutation_policy"].get("source", False):
            return {"status": "BLOCK", "blocker": "candidate_execution_source_mutation_not_authorized", "phase_id": phase.phase_id}
        destinations = list(auth["destination_allowlists"].get(phase.phase_id, []))
        destination = manifest.get("network_destinations", {}).get(phase.phase_id)
        policy = {
            "phase_id": phase.phase_id, "network_mode": expected_mode,
            "allowed_network_destinations": destinations,
            "allowed_protocols": ["https"] if network_enabled else [],
            "maximum_requests": int(auth["request_budgets"].get(phase.phase_id, 0)),
            "maximum_download_bytes": int(auth["download_byte_budgets"].get(phase.phase_id, 0)),
            "tls_verification_policy": "required" if network_enabled else None,
            "redirect_policy": "allowlisted_hosts_only" if network_enabled else None,
        }
        network = authorize_network_operation(
            phase_id=phase.phase_id, policy=policy, destination=destination,
            requested_mode=expected_mode,
            projected_requests=int(manifest.get("projected_requests", {}).get(phase.phase_id, 0)),
            projected_bytes=int(manifest.get("projected_bytes", {}).get(phase.phase_id, 0)),
        )
        append_network_event(Path(network_ledger_path), {"phase_id": phase.phase_id, "authorization_status": network["status"], "destination": destination, "network_mode": expected_mode, "policy_hash": hash_record(policy)})
        if network["status"] != "PASS":
            return {**network, "phase_id": phase.phase_id}
        input_hash = hash_record({"phase": phase.phase_id, "context": context, "chain": chain})
        result = execute_binding(phase.binding, phase.phase_id, context, policy)
        event = append_event(Path(event_ledger_path), RuntimeEvent(f"event-{len(completed)+1:03d}", phase.phase_id, str(result["status"]), input_hash, hash_record(result), result.get("blocker"), chain))
        chain = str(event["event_hash"]); executed.append(phase.phase_id); context.update(result.get("context_updates", {}))
        if result["status"] == "PASS":
            completed.append(phase.phase_id)
            continue
        spent.add(str(auth["nonce"])); store_path.parent.mkdir(parents=True, exist_ok=True); store_path.write_text(json.dumps({"spent_nonces": sorted(spent)}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        write_checkpoint(Path(checkpoint_path), RuntimeCheckpoint(plan.candidate_id, plan.plan_hash, tuple(completed), str(result["status"]), result.get("blocker"), tuple(sorted(spent)), chain, context_state=context))
        return {"status": result["status"], "blocker": result.get("blocker"), "phase_id": phase.phase_id, "executed_phases": executed, "completed_phases": completed, "network_ledger": verify_network_event_ledger(Path(network_ledger_path)), "context": context}
    spent.add(str(auth["nonce"])); store_path.parent.mkdir(parents=True, exist_ok=True); store_path.write_text(json.dumps({"spent_nonces": sorted(spent)}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_checkpoint(Path(checkpoint_path), RuntimeCheckpoint(plan.candidate_id, plan.plan_hash, tuple(completed), "PASS", None, tuple(sorted(spent)), chain, context_state=context))
    return {"status": "PASS", "blocker": None, "executed_phases": executed, "completed_phases": completed, "network_ledger": verify_network_event_ledger(Path(network_ledger_path)), "context": context}
