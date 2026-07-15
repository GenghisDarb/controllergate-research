from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone
from typing import Any


def _hash(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def derive_historical_authorization(*, contract: dict[str, Any], candidate_id: str, patch_sha256: str,
                                    allowed_source_path: str, workflow_actor: str | None, workflow_run_id: str | None,
                                    workflow_branch: str, official_run_started_at: str | None) -> dict[str, Any]:
    allowed = {row["candidate_id"]: row for row in contract["human_authorization"]["candidates"]}
    if candidate_id not in allowed or allowed[candidate_id]["patch_sha256"] != patch_sha256 or allowed[candidate_id]["allowed_source_path"] != allowed_source_path:
        return {"status": "HUMAN_AUTHORIZATION_BLOCKED_EXACT", "blocker": "candidate_patch_or_path_not_bound"}
    if contract.get("contract_hash") != contract.get("exact_prompt_bytes_sha256"):
        return {"status": "HUMAN_AUTHORIZATION_BLOCKED_EXACT", "blocker": "prompt_bytes_hash_not_bound"}
    if not workflow_actor or not workflow_run_id or not official_run_started_at:
        return {"status": "PENDING_OFFICIAL_WORKFLOW_BINDING", "blocker": "workflow_actor_run_or_start_unavailable"}
    if workflow_branch != contract["starting_branch"]:
        return {"status": "HUMAN_AUTHORIZATION_BLOCKED_EXACT", "blocker": "workflow_branch_mismatch"}
    started = datetime.fromisoformat(official_run_started_at.replace("Z", "+00:00"))
    expires = started + timedelta(hours=24)
    payload = {
        "status": "PASS", "human_authority": "Brad", "prompt_contract_hash": contract["contract_hash"],
        "human_authorization_block_hash": contract["human_authorization_block_hash"], "candidate_id": candidate_id,
        "patch_sha256": patch_sha256, "allowed_source_path": allowed_source_path, "workflow_actor": workflow_actor,
        "workflow_run_id": str(workflow_run_id), "workflow_branch": workflow_branch,
        "single_use_nonce": _hash([contract["contract_hash"], workflow_run_id, candidate_id, patch_sha256]),
        "official_run_started_at": started.astimezone(timezone.utc).isoformat(), "expiry": expires.astimezone(timezone.utc).isoformat(),
        "historical_non_counting_boundary": True, "public_write_prohibition": True,
    }
    payload["authorization_hash"] = _hash(payload)
    return payload
