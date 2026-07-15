from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import IntEnum
from pathlib import Path
from typing import Any


class ExecutionDepth(IntEnum):
    UNIT_MECHANISM_FIXTURE = 10
    IN_PROCESS_INTEGRATION_FIXTURE = 20
    INSTALLED_CLI_EXECUTION = 30
    HISTORICAL_EPISODE_EXECUTION = 40
    DISTINCT_CANARY_EXECUTION = 50


MECHANISM_STATUSES = {"PASS", "BLOCK", "FAILED", "CONTRADICTED", "SAFE_ABSTENTION"}
ASSERTION_STATUSES = {"TEST_PASS", "TEST_FAIL"}


def canonical_hash(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


@dataclass(frozen=True)
class MechanismOutcome:
    outcome_id: str
    mechanism_id: str
    observed_status: str
    raw_output_hashes: dict[str, str]
    blocker: str | None = None

    def __post_init__(self) -> None:
        if self.observed_status not in MECHANISM_STATUSES:
            raise ValueError("invalid mechanism status")
        if not self.raw_output_hashes:
            raise ValueError("mechanism outcome requires raw output")


@dataclass(frozen=True)
class TestAssertion:
    assertion_id: str
    outcome_id: str
    assertion_status: str
    expected_mechanism_status: str

    def __post_init__(self) -> None:
        if self.assertion_status not in ASSERTION_STATUSES:
            raise ValueError("invalid test assertion status")
        if self.expected_mechanism_status not in MECHANISM_STATUSES:
            raise ValueError("invalid expected mechanism status")


@dataclass(frozen=True)
class ExecutionReceipt:
    receipt_id: str
    producer_component: str
    producer_version: str
    operation_or_reaction_id: str
    candidate_id: str
    run_id: str
    frame_hash: str
    input_evidence_hashes: dict[str, str]
    raw_output_hashes: dict[str, str]
    mechanism_observed_status: str
    test_assertion_status: str
    execution_depth: str
    broker_record_hashes: tuple[str, ...]
    sqlite_transaction_identity: str
    verifier_identity: str
    semantic_scopes_allowed: tuple[str, ...]
    semantic_scopes_forbidden: tuple[str, ...]
    created_at: str
    parent_receipt: str | None

    @classmethod
    def create(cls, **values: Any) -> "ExecutionReceipt":
        payload = dict(values)
        payload.setdefault("created_at", datetime.now(timezone.utc).isoformat())
        payload.setdefault("parent_receipt", None)
        payload.setdefault("receipt_id", "")
        payload["broker_record_hashes"] = tuple(payload.get("broker_record_hashes", ()))
        payload["semantic_scopes_allowed"] = tuple(payload.get("semantic_scopes_allowed", ()))
        payload["semantic_scopes_forbidden"] = tuple(payload.get("semantic_scopes_forbidden", ()))
        candidate = cls(**payload)
        record = asdict(candidate)
        record["receipt_id"] = ""
        return cls(**{**asdict(candidate), "receipt_id": canonical_hash(record)})

    def __post_init__(self) -> None:
        if self.mechanism_observed_status not in MECHANISM_STATUSES:
            raise ValueError("invalid receipt mechanism status")
        if self.test_assertion_status not in ASSERTION_STATUSES:
            raise ValueError("invalid receipt assertion status")
        if self.execution_depth not in ExecutionDepth.__members__:
            raise ValueError("invalid execution depth")
        if not self.raw_output_hashes:
            raise ValueError("receipt requires raw output hashes")
        if not self.producer_component or not self.verifier_identity or self.producer_component == self.verifier_identity:
            raise ValueError("independent producer and verifier required")

    def record(self) -> dict[str, Any]:
        value = asdict(self)
        for key in ("broker_record_hashes", "semantic_scopes_allowed", "semantic_scopes_forbidden"):
            value[key] = list(value[key])
        return value


@dataclass(frozen=True)
class ClaimBinding:
    claim_id: str
    claim_type: str
    candidate_id: str
    run_id: str
    frame_hash: str
    producer_component: str
    receipt_id: str
    minimum_execution_depth: str
    verifier_identity: str
    raw_output_paths: tuple[str, ...] = field(default_factory=tuple)

    def validate(self, receipt: ExecutionReceipt, root: Path) -> None:
        if self.receipt_id != receipt.receipt_id:
            raise ValueError("receipt identity mismatch")
        if (self.candidate_id, self.run_id, self.frame_hash) != (receipt.candidate_id, receipt.run_id, receipt.frame_hash):
            raise ValueError("candidate/run/frame mismatch")
        if self.producer_component != receipt.producer_component:
            raise ValueError("claim producer mismatch")
        if self.claim_type not in receipt.semantic_scopes_allowed or self.claim_type in receipt.semantic_scopes_forbidden:
            raise ValueError("claim outside receipt semantic scope")
        if ExecutionDepth[receipt.execution_depth] < ExecutionDepth[self.minimum_execution_depth]:
            raise ValueError("claim exceeds execution depth")
        if self.verifier_identity != receipt.verifier_identity:
            raise ValueError("claim verifier mismatch")
        for relative in self.raw_output_paths:
            path = root / relative
            expected = receipt.raw_output_hashes.get(relative)
            if not path.is_file() or not expected or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
                raise ValueError("raw output missing or hash mismatch")


def claim_graph(receipts: list[ExecutionReceipt], bindings: list[ClaimBinding]) -> dict[str, Any]:
    receipt_ids = {receipt.receipt_id for receipt in receipts}
    edges = [{"claim_id": binding.claim_id, "receipt_id": binding.receipt_id, "claim_type": binding.claim_type} for binding in bindings]
    missing = sorted({edge["receipt_id"] for edge in edges} - receipt_ids)
    return {"receipt_nodes": sorted(receipt_ids), "claim_nodes": sorted({binding.claim_id for binding in bindings}), "edges": edges, "missing_receipts": missing, "status": "PASS" if not missing else "BLOCK"}
