from __future__ import annotations

from typing import Any

from controllergate.core.evidence import hash_record


def new_repair_count_gate(*, record: dict[str, Any], registry: list[dict[str, Any]], prerequisites: dict[str, bool]) -> dict[str, Any]:
    unique = sum(item.get("candidate_id") == record.get("candidate_id") for item in registry) == 0
    required = {**prerequisites, "count_uniqueness": unique}
    passed = all(required.values())
    return {"status": "PASS" if passed else "BLOCK", "mode": "new_repair_count_gate", "prerequisites": required, "count_increment": 1 if passed else 0, "record_hash": hash_record(record)}


def existing_count_hardening_gate(*, record: dict[str, Any], registry: list[dict[str, Any]], prerequisites: dict[str, bool]) -> dict[str, Any]:
    matching = [item for item in registry if item.get("candidate_id") == record.get("candidate_id")]
    exact = len(matching) == 1 and all(matching[0].get(key) == record.get(key) for key in ("candidate_id", "candidate_sha", "patch_sha256"))
    required = {**prerequisites, "exactly_one_existing_count_record": len(matching) == 1, "exact_candidate_source_patch_identity": exact}
    passed = all(required.values())
    return {"status": "PASS" if passed else "BLOCK", "mode": "existing_count_hardening_gate", "prerequisites": required, "count_increment": 0, "record_hash": hash_record(record), "existing_record_hash": hash_record(matching[0]) if len(matching) == 1 else None}


def terminal_proof_event(*, prior_event_hash: str, decision: dict[str, Any]) -> dict[str, Any]:
    event = {"event_type": "terminal_count_or_hardening_decision", "prior_event_hash": prior_event_hash, "decision_hash": hash_record(decision), "decision_status": decision.get("status"), "decision_mode": decision.get("mode")}
    event["event_hash"] = hash_record(event)
    return event
