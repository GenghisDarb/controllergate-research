from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from controllergate.core.evidence import hash_record
from .candidate_execution_authorization import verify_candidate_authorization
from .candidate_execution_plan import parse_candidate_plan, verify_candidate_plan
from .execution_checkpoint import load_checkpoint
from .maintenance_dispatcher import dispatch


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
    spent = set(checkpoint.get("spent_nonces", []))
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
    Path(network_ledger_path).parent.mkdir(parents=True, exist_ok=True)
    Path(authorization_store).parent.mkdir(parents=True, exist_ok=True)
    return dispatch(
        candidate_id=plan.candidate_id,
        candidate_sha=plan.candidate_sha,
        current_state_hash=hash_record(manifest),
        authorization_path=Path(authorization_path),
        plan_path=Path(plan_path),
        checkpoint_path=Path(checkpoint_path),
        event_ledger_path=Path(event_ledger_path),
    )
