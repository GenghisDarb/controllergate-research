from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from controllergate.core.evidence import hash_record


def authorize_probe(*, candidate_id: str, candidate_sha: str, board_hash: str, probe_id: str, executor_id: str, nonce: str, resource_budget: dict[str, Any], expires_at: str) -> dict[str, Any]:
    record = {"candidate_id": candidate_id, "candidate_sha": candidate_sha, "board_hash": board_hash, "probe_id": probe_id, "executor_id": executor_id, "nonce": nonce, "resource_budget": resource_budget, "network_policy": "none", "expires_at": expires_at}
    record["authorization_hash"] = hash_record(record)
    return record


class ProbeLedger:
    def __init__(self) -> None:
        self.spent_nonces: set[str] = set(); self.events: list[dict[str, Any]] = []; self.executed: dict[str, str] = {}

    def spend(self, authorization: dict[str, Any], *, probe_id: str, executor_id: str, board_hash: str, replay_reason: str | None = None, evidence_changed: bool = False) -> dict[str, Any]:
        nonce = str(authorization.get("nonce")); reasons = []
        if nonce in self.spent_nonces: reasons.append("reused_probe_nonce")
        if authorization.get("probe_id") != probe_id: reasons.append("probe_id_mismatch")
        if authorization.get("executor_id") != executor_id: reasons.append("executor_mismatch")
        if authorization.get("board_hash") != board_hash: reasons.append("board_hash_mismatch")
        if probe_id in self.executed and not (replay_reason or evidence_changed): reasons.append("repeated_probe_without_authority")
        if reasons: return {"status": "REJECT", "reasons": reasons}
        self.spent_nonces.add(nonce); self.executed[probe_id] = authorization["authorization_hash"]
        parent = self.events[-1]["event_hash"] if self.events else "0" * 64
        event = {"event_type": "probe_execution", "probe_id": probe_id, "executor_id": executor_id, "board_hash": board_hash, "authorization_hash": authorization["authorization_hash"], "nonce": nonce, "parent_event_hash": parent, "timestamp": datetime.now(timezone.utc).isoformat(), "replay_reason": replay_reason}
        event["event_hash"] = hash_record(event)
        self.events.append(event)
        return {"status": "PASS", "event": event}
