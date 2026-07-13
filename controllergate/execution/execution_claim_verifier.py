from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from controllergate.core.evidence import hash_record
from .sentinel_contract import sentinel_coverage


SUCCESS_WORDS = {"PASS", "EXECUTED", "VERIFIED", "RECOVERED", "FIXED", "ADMITTED", "MATERIALIZED"}


def _timestamp(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def verify_execution_claims(records: list[dict[str, Any]], *, claimed_executed_stages: int | None = None, now: datetime | None = None) -> dict[str, Any]:
    now = now or datetime.now(timezone.utc)
    failures: list[dict[str, Any]] = []
    executed = 0
    blocker_by_candidate: dict[str, str] = {}
    parent = None
    for index, row in enumerate(records):
        kind = row.get("evidence_kind")
        operation = row.get("operation_status")
        successful = operation in SUCCESS_WORDS or row.get("gate_decision") == "PASS"
        if kind in {"EXECUTED_COMMAND", "EXECUTED_CALLABLE"}:
            executed += 1
        if successful and kind == "NOT_RUN": failures.append({"index": index, "reason": "pass_with_not_run"})
        if kind == "EXECUTED_COMMAND" and not row.get("argv"): failures.append({"index": index, "reason": "command_missing_argv"})
        if kind == "EXECUTED_CALLABLE" and not row.get("callable_source_hash"): failures.append({"index": index, "reason": "callable_missing_hash"})
        if operation == "VERIFIED" and (not row.get("independent_verifier") or row.get("verifier_result") != "PASS"):
            failures.append({"index": index, "reason": "verified_without_independent_verifier"})
        if operation == "MATERIALIZED" and not row.get("output_paths_and_hashes"):
            failures.append({"index": index, "reason": "materialized_without_provider_bytes"})
        if operation == "TARGET_EXECUTED" and sentinel_coverage(["TARGET_STARTED", "TARGET_COMPLETED"], row.get("observed_sentinels", []))["status"] != "PASS":
            failures.append({"index": index, "reason": "target_sentinel_gap"})
        start, end = _timestamp(row.get("start_timestamp")), _timestamp(row.get("end_timestamp"))
        if start and (start > now or (end and end < start)): failures.append({"index": index, "reason": "timestamp_order_invalid"})
        claimed_hash = row.get("record_hash")
        if claimed_hash:
            check = dict(row); check["record_hash"] = None
            if row.get("ledger_parent_hash") != parent or hash_record(check) != claimed_hash:
                failures.append({"index": index, "reason": "ledger_chain_invalid"})
            parent = claimed_hash
        blocker = row.get("exact_blocker")
        candidate = row.get("candidate_id")
        if blocker and candidate:
            previous = blocker_by_candidate.get(blocker)
            if previous and previous != candidate and not row.get("candidate_specific_evidence_hash"):
                failures.append({"index": index, "reason": "generic_copied_blocker"})
            blocker_by_candidate[blocker] = candidate
    if claimed_executed_stages is not None and claimed_executed_stages != executed:
        failures.append({"reason": "claim_ledger_count_mismatch", "claimed": claimed_executed_stages, "ledger": executed})
    return {"status": "PASS" if not failures else "BLOCK", "claimed_executed_stages": claimed_executed_stages, "ledger_executed_stages": executed, "rejected_fake_record_count": len(failures), "failures": failures}
