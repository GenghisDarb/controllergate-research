from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any

from controllergate.core.evidence import hash_record


@dataclass(frozen=True)
class ExecutionScope:
    candidate_id: str
    candidate_sha: str
    allowed_phases: tuple[str, ...]
    allowed_output_root: str
    network_phases: tuple[str, ...] = ()
    patch_authority: bool = False
    source_mutation_authority: bool = False
    test_mutation_authority: bool = False
    network_policies: tuple[dict[str, Any], ...] = ()


@dataclass(frozen=True)
class ExecutionAuthorization:
    authorization_id: str
    scope: ExecutionScope
    current_state_hash: str
    plan_hash: str
    issued_at: str
    expires_at: str
    nonce: str
    plan_path: str
    event_ledger_path: str
    single_use: bool = True
    authorization_hash: str = ""

    def unsigned(self) -> dict[str, Any]:
        value = asdict(self)
        value.pop("authorization_hash", None)
        return value


def authorization_from_dict(value: dict[str, Any]) -> ExecutionAuthorization:
    scope = ExecutionScope(**value["scope"])
    return ExecutionAuthorization(**{**value, "scope": scope})


def seal_authorization(value: ExecutionAuthorization) -> dict[str, Any]:
    record = value.unsigned()
    record["authorization_hash"] = hash_record(record)
    return record


def verify_authorization(value: dict[str, Any], *, candidate_id: str, candidate_sha: str, current_state_hash: str, plan_hash: str, spent_nonces: set[str]) -> dict[str, Any]:
    errors: list[str] = []
    try:
        record = authorization_from_dict(value)
    except Exception as exc:
        return {"status": "BLOCK", "blocker": "authorization_schema_invalid", "errors": [type(exc).__name__]}
    if record.authorization_hash != hash_record(record.unsigned()): errors.append("authorization_hash_invalid")
    if record.scope.candidate_id != candidate_id: errors.append("authorization_candidate_mismatch")
    if record.scope.candidate_sha != candidate_sha: errors.append("authorization_candidate_sha_mismatch")
    if record.current_state_hash != current_state_hash: errors.append("authorization_state_hash_stale")
    if record.plan_hash != plan_hash: errors.append("authorization_plan_hash_mismatch")
    now = datetime.now(timezone.utc)
    expires = datetime.fromisoformat(record.expires_at.replace("Z", "+00:00"))
    if expires <= now: errors.append("authorization_expired")
    if record.single_use and record.nonce in spent_nonces: errors.append("authorization_nonce_spent")
    if record.scope.patch_authority or record.scope.source_mutation_authority or record.scope.test_mutation_authority: errors.append("authorization_scope_overbroad")
    policies = list(record.scope.network_policies)
    policy_ids = [str(item.get("phase_id")) for item in policies]
    if len(policy_ids) != len(set(policy_ids)): errors.append("network_authorization_duplicate_phase")
    if policies and set(policy_ids) != set(record.scope.allowed_phases): errors.append("network_authorization_policy_coverage_incomplete")
    if set(record.scope.network_phases) != {str(item.get("phase_id")) for item in policies if item.get("network_mode") == "bounded_read_only"}: errors.append("network_authorization_phase_policy_mismatch")
    return {"status": "PASS" if not errors else "BLOCK", "blocker": None if not errors else errors[0], "errors": errors, "authorization_id": record.authorization_id, "nonce": record.nonce, "allowed_phases": list(record.scope.allowed_phases), "network_phases": list(record.scope.network_phases), "network_policies": policies}
