from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from controllergate.core.evidence import hash_record
from .evidence_kind import EvidenceKind


@dataclass
class ExecutionRecord:
    execution_id: str
    stage_id: str
    candidate_id: str
    evidence_kind: EvidenceKind
    authorization_id: str
    operation_status: str
    evidence_status: str
    gate_decision: str
    candidate_state: str
    argv: list[str] = field(default_factory=list)
    callable_identity: str | None = None
    callable_source_file: str | None = None
    callable_source_hash: str | None = None
    working_directory: str | None = None
    runtime_root_identity: str | None = None
    runtime_image_or_interpreter_identity: str | None = None
    process_id: int | None = None
    start_timestamp: str | None = None
    end_timestamp: str | None = None
    monotonic_duration: float | None = None
    input_paths_and_hashes: dict[str, str] = field(default_factory=dict)
    environment_allowlist_hash: str | None = None
    network_policy: str = "none"
    return_code: int | None = None
    stdout_hash: str | None = None
    stderr_hash: str | None = None
    bounded_raw_log_locations: list[str] = field(default_factory=list)
    required_sentinels: list[str] = field(default_factory=list)
    observed_sentinels: list[str] = field(default_factory=list)
    output_paths_and_hashes: dict[str, str] = field(default_factory=dict)
    source_tree_hash_before: str | None = None
    source_tree_hash_after: str | None = None
    test_tree_hash_before: str | None = None
    test_tree_hash_after: str | None = None
    independent_verifier: str | None = None
    verifier_result: str | None = None
    ledger_parent_hash: str | None = None
    record_hash: str | None = None

    def to_dict(self) -> dict[str, Any]:
        record = asdict(self)
        record["evidence_kind"] = self.evidence_kind.value
        record["record_hash"] = None
        digest = hash_record(record)
        record["record_hash"] = digest
        return record
