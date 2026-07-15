from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Iterable

from .stable_identity import stable_hash


class AccessState(str, Enum):
    SEALED = "SEALED"
    READ_ONLY_DIAGNOSTIC = "READ_ONLY_DIAGNOSTIC"
    WRITE_LICENSED = "WRITE_LICENSED"
    RESEALED = "RESEALED"
    REVOKED = "REVOKED"
    FAILED_TO_RESEAL = "FAILED_TO_RESEAL"


@dataclass
class AccessLease:
    lease_id: str
    candidate_id: str
    run_id: str
    source_tree_hash: str
    test_tree_hash: str
    operation: str
    region: str
    expires_at: str
    resource_budget_hash: str
    audit_parent: str
    state: AccessState = AccessState.SEALED
    consumed: bool = False

    @property
    def lease_hash(self) -> str:
        return stable_hash({**asdict(self), "state": self.state.value})


class SourceRegionAccessController:
    def __init__(self) -> None:
        self.leases: dict[str, AccessLease] = {}

    def diagnostic(self, lease: AccessLease) -> AccessLease:
        if lease.state is not AccessState.SEALED or lease.operation not in {"READ", "AST_INSPECT", "TRACE"}:
            raise ValueError("diagnostic lease must start sealed and remain read only")
        lease.state = AccessState.READ_ONLY_DIAGNOSTIC
        self.leases[lease.lease_id] = lease
        return lease

    def license_write(self, lease: AccessLease, evidence_tokens: Iterable[str], *, human_approval: bool,
                      rollback_ready: bool, single_use: bool = True) -> AccessLease:
        required = {"SOURCE_OWNERSHIP_TOKEN", "REPAIR_LICENSE_TOKEN", "TEST_TREE_IMMUTABLE_TOKEN"}
        if lease.state is not AccessState.SEALED or required - set(evidence_tokens):
            raise ValueError("write lease evidence incomplete")
        if not human_approval or not rollback_ready or not single_use:
            raise ValueError("write lease boundary incomplete")
        lease.state = AccessState.WRITE_LICENSED
        self.leases[lease.lease_id] = lease
        return lease

    def consume(self, lease_id: str) -> None:
        lease = self.leases[lease_id]
        if lease.state is not AccessState.WRITE_LICENSED or lease.consumed:
            raise ValueError("write lease unavailable or already consumed")
        lease.consumed = True
        lease.state = AccessState.REVOKED

    def reseal(self, lease_id: str, *, source_tree_hash: str, test_tree_hash: str) -> AccessState:
        lease = self.leases[lease_id]
        valid = source_tree_hash == lease.source_tree_hash and test_tree_hash == lease.test_tree_hash
        lease.state = AccessState.RESEALED if valid else AccessState.FAILED_TO_RESEAL
        return lease.state


def normalize_coordinate(raw_line: int, raw_column: int, *, ast_identity: str, source_hash: str,
                         representation: str = "source_checkout") -> dict[str, object]:
    if raw_line < 1 or raw_column < 0:
        raise ValueError("invalid source coordinate")
    if representation not in {"source_checkout", "installed_package", "generated", "preprocessed"}:
        raise ValueError("unknown coordinate representation")
    value = {"raw_line": raw_line, "raw_column": raw_column, "ast_identity": ast_identity,
             "source_hash": source_hash, "representation": representation}
    return {**value, "coordinate_hash": stable_hash(value)}
