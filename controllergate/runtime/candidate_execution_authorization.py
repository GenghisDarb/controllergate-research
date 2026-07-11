from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from controllergate.core.evidence import hash_record


@dataclass(frozen=True)
class CandidateExecutionAuthorization:
    authorization_id: str
    candidate_id: str
    candidate_sha: str
    current_state_hash: str
    plan_hash: str
    allowed_phases: tuple[str, ...]
    network_enabled_phases: tuple[str, ...]
    destination_allowlists: dict[str, tuple[str, ...]]
    request_budgets: dict[str, int]
    download_byte_budgets: dict[str, int]
    mutation_policy: dict[str, bool]
    resource_budget: dict[str, int]
    output_root: str
    issued_at: str
    expires_at: str
    nonce: str
    authorization_hash: str = ""

    def unsigned(self) -> dict[str, Any]:
        value = asdict(self)
        value.pop("authorization_hash", None)
        return value


def seal_candidate_authorization(value: CandidateExecutionAuthorization) -> dict[str, Any]:
    record = value.unsigned()
    record["authorization_hash"] = hash_record(record)
    return record


def verify_candidate_authorization(
    value: dict[str, Any], *, candidate_id: str, candidate_sha: str,
    current_state_hash: str, plan_hash: str, spent_nonces: set[str],
    output_root: str | Path,
) -> dict[str, Any]:
    try:
        auth = CandidateExecutionAuthorization(**value)
    except Exception as exc:
        return {"status": "BLOCK", "blocker": "candidate_execution_authorization_schema_invalid", "error": type(exc).__name__}
    checks = [
        (auth.authorization_hash == hash_record(auth.unsigned()), "candidate_execution_authorization_hash_invalid"),
        (auth.candidate_id == candidate_id and auth.candidate_sha == candidate_sha, "candidate_execution_authorization_candidate_mismatch"),
        (auth.current_state_hash == current_state_hash, "candidate_execution_authorization_state_stale"),
        (auth.plan_hash == plan_hash, "candidate_execution_authorization_plan_mismatch"),
        (auth.nonce not in spent_nonces, "candidate_execution_authorization_nonce_spent"),
        (not auth.mutation_policy.get("tests", False), "candidate_execution_authorization_test_mutation_forbidden"),
        (Path(auth.output_root).resolve() == Path(output_root).resolve(), "candidate_execution_authorization_output_root_mismatch"),
    ]
    for passed, blocker in checks:
        if not passed:
            return {"status": "BLOCK", "blocker": blocker}
    now = datetime.now(timezone.utc)
    issued = datetime.fromisoformat(auth.issued_at.replace("Z", "+00:00"))
    expires = datetime.fromisoformat(auth.expires_at.replace("Z", "+00:00"))
    if issued > now or expires <= now:
        return {"status": "BLOCK", "blocker": "candidate_execution_authorization_expired"}
    network = set(auth.network_enabled_phases)
    if not network <= set(auth.allowed_phases):
        return {"status": "BLOCK", "blocker": "candidate_execution_authorization_network_phase_invalid"}
    for phase in network:
        if not auth.destination_allowlists.get(phase) or auth.request_budgets.get(phase, 0) <= 0 or auth.download_byte_budgets.get(phase, 0) <= 0:
            return {"status": "BLOCK", "blocker": "candidate_execution_network_budget_or_allowlist_missing"}
    return {"status": "PASS", "nonce": auth.nonce, "allowed_phases": list(auth.allowed_phases), "network_enabled_phases": list(auth.network_enabled_phases)}
