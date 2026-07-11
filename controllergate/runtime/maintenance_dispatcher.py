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
        result = execute_binding(phase.binding, phase.phase_id, context); output_hash = hash_record(result)
        event = append_event(event_ledger_path, RuntimeEvent(f"event-{len(completed)+1:03d}", phase.phase_id, str(result["status"]), input_hash, output_hash, result.get("blocker"), chain))
        chain = str(event["event_hash"]); executed.append(phase.phase_id)
        context.update(result.get("context_updates", {})); Path(plan.context_path).write_text(json.dumps(context, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        if result["status"] == "PASS": completed.append(phase.phase_id)
        else:
            spent.add(str(auth["nonce"])); write_checkpoint(checkpoint_path, RuntimeCheckpoint(candidate_id, plan.plan_hash, tuple(completed), str(result["status"]), result.get("blocker"), tuple(sorted(spent)), chain))
            return {"status": str(result["status"]), "blocker": result.get("blocker"), "phase_id": phase.phase_id, "executed_phases": executed, "completed_phases": completed, "checkpoint_status": "PASS", "resume_status": "SAFE"}
    spent.add(str(auth["nonce"])); write_checkpoint(checkpoint_path, RuntimeCheckpoint(candidate_id, plan.plan_hash, tuple(completed), "PASS", None, tuple(sorted(spent)), chain))
    return {"status": "PASS", "blocker": None, "executed_phases": executed, "completed_phases": completed, "checkpoint_status": "PASS", "resume_status": "SAFE"}
