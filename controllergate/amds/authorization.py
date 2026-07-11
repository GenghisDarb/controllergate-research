from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import secrets
from typing import Any

from controllergate.core.evidence import hash_record, write_json_deterministic


def _load_store(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {"schema_version": "amds.spent_nonces.v1", "spent_nonces": []}
    return json.loads(path.read_text(encoding="utf-8"))


def issue_probe_authorization(*, candidate_id: str, candidate_sha: str, board_hash: str, probe_id: str, allowed_executor: str, network_policy: dict[str, Any], mutation_policy: str, resource_budget: dict[str, Any], ttl_seconds: int = 900, nonce: str | None = None) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    value = {
        "candidate_id": candidate_id, "candidate_sha": candidate_sha, "board_hash": board_hash,
        "probe_id": probe_id, "allowed_executor": allowed_executor, "network_policy": network_policy,
        "mutation_policy": mutation_policy, "resource_budget": resource_budget,
        "issued_at": now.isoformat(), "expires_at": (now + timedelta(seconds=ttl_seconds)).isoformat(),
        "single_use_nonce": nonce or secrets.token_hex(16), "single_use": True,
    }
    value["authorization_hash"] = hash_record(value)
    return value


def consume_probe_authorization(value: dict[str, Any], *, store_path: Path, candidate_id: str, candidate_sha: str, board_hash: str, probe_id: str, executor: str) -> dict[str, Any]:
    unsigned = {key: item for key, item in value.items() if key != "authorization_hash"}
    if value.get("authorization_hash") != hash_record(unsigned):
        return {"status": "BLOCK", "blocker": "amds_probe_authorization_hash_invalid"}
    expected = (candidate_id, candidate_sha, board_hash, probe_id, executor)
    observed = (value.get("candidate_id"), value.get("candidate_sha"), value.get("board_hash"), value.get("probe_id"), value.get("allowed_executor"))
    if observed != expected:
        return {"status": "BLOCK", "blocker": "amds_probe_authorization_scope_mismatch"}
    if value.get("mutation_policy") != "none" or value.get("network_policy", {}).get("network_mode") not in {"none", "bounded_read_only"}:
        return {"status": "BLOCK", "blocker": "amds_probe_authorization_policy_invalid"}
    try:
        if datetime.now(timezone.utc) >= datetime.fromisoformat(str(value["expires_at"])):
            return {"status": "BLOCK", "blocker": "amds_probe_authorization_expired"}
    except Exception:
        return {"status": "BLOCK", "blocker": "amds_probe_authorization_time_invalid"}
    store = _load_store(store_path); nonce = str(value.get("single_use_nonce"))
    if nonce in store.get("spent_nonces", []):
        return {"status": "BLOCK", "blocker": "amds_probe_nonce_already_spent"}
    store["spent_nonces"] = sorted({*store.get("spent_nonces", []), nonce})
    store["last_authorization_hash"] = value["authorization_hash"]
    write_json_deterministic(store_path, store)
    return {"status": "PASS", "blocker": None, "authorization_id": value["authorization_hash"], "nonce_spent": True}
