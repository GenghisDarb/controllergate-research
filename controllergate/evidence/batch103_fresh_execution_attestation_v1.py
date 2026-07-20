"""Batch103 current-workflow attestations for brokered candidate operations."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any

from .execution_epoch_v1 import BATCH103_FRESH_OPERATION, validate_batch103_execution_epoch


def canonical_hash(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


@dataclass(frozen=True)
class Batch103FreshExecutionReceiptV1:
    execution_receipt_id: str
    execution_epoch: str
    workflow_run_id: str
    workflow_job_id: str
    workflow_job_attempt: str
    workflow_head: str
    candidate_id: str
    program_id: str
    cell_id: str
    replay_index: int
    broker_operation_id: str
    broker_record_hash: str
    source_capsule_hash: str
    source_commit: str
    source_tree_hash_before: str
    source_tree_hash_after: str
    provider_capsule_hash: str
    provider_observed_identity: dict[str, Any]
    provider_exactness_status: str
    platform: str
    architecture: str
    ABI: str
    SOABI: str
    exact_argv_hash: str
    cwd_hash: str
    environment_hash: str
    fixture_hash: str
    raw_stdout_object: dict[str, Any]
    raw_stderr_object: dict[str, Any]
    raw_return_code: int
    semantic_projection_id: str
    semantic_fingerprint: str
    predicate_registry_hash: str
    predicate_result: bool
    network_policy: str
    truth_access_count: int
    private_tld_access_count: int
    patch_operation_count: int
    cleanup_status: str
    producer: str
    independent_verifier: str
    producer_receipt: dict[str, Any]
    verifier_receipt: dict[str, Any]

    def __post_init__(self) -> None:
        if self.execution_epoch != BATCH103_FRESH_OPERATION:
            raise ValueError("fresh receipt requires the Batch103 execution epoch")
        if self.producer != "canonical_external_operation_broker":
            raise ValueError("fresh receipt producer must be the canonical broker")
        if self.independent_verifier in {"", self.producer}:
            raise ValueError("fresh receipt requires an independent verifier")
        if not self.broker_operation_id or not self.broker_record_hash:
            raise ValueError("fresh receipt requires a new broker operation")

    def record(self) -> dict[str, Any]:
        row = asdict(self)
        row["record_hash"] = canonical_hash(row)
        return row


def verify_batch103_fresh_execution_receipt(
    row: dict[str, Any], *, current_workflow_run_id: str, current_workflow_head: str
) -> list[str]:
    blockers = validate_batch103_execution_epoch(
        str(row.get("execution_epoch", "")), str(row.get("workflow_head", ""))
    )
    required = set(Batch103FreshExecutionReceiptV1.__dataclass_fields__) | {"record_hash"}
    blockers.extend(f"missing_field:{field}" for field in sorted(required - set(row)))
    if str(row.get("workflow_run_id")) != str(current_workflow_run_id):
        blockers.append("workflow_run_mismatch")
    if row.get("workflow_head") != current_workflow_head:
        blockers.append("workflow_head_mismatch")
    if row.get("producer") != "canonical_external_operation_broker":
        blockers.append("static_or_nonbroker_producer")
    if row.get("independent_verifier") in {None, "", row.get("producer")}:
        blockers.append("independent_verifier_missing")
    if not row.get("broker_operation_id") or not row.get("broker_record_hash"):
        blockers.append("broker_operation_missing")
    if row.get("source_tree_hash_before") != row.get("source_tree_hash_after"):
        blockers.append("source_tree_mutated")
    forbidden = ("truth_access_count", "private_tld_access_count", "patch_operation_count")
    if any(int(row.get(field, -1)) != 0 for field in forbidden):
        blockers.append("forbidden_operation_or_private_access")
    if row.get("cleanup_status") != "PASS":
        blockers.append("cleanup_not_verified")
    expected = canonical_hash({key: value for key, value in row.items() if key != "record_hash"})
    if row.get("record_hash") != expected:
        blockers.append("record_hash_mismatch")
    return blockers
