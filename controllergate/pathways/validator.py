from __future__ import annotations

from typing import Any, Iterable

from .compartment import ALL_COMPARTMENTS


def validate_event(record: dict[str, Any], *, permitted_compartments: Iterable[str] | None = None) -> dict[str, Any]:
    errors: list[str] = []
    required = {
        "event_id", "event_version", "event_type", "schema_type", "compartment",
        "input_entities", "required_input_entities", "catalyst_or_executor",
        "positive_regulators", "negative_regulators", "output_entities",
        "expected_output", "observed_output", "knowledge_status", "evidence_references",
        "author_record", "reviewer_record", "revision_record", "created_timestamp",
        "modified_timestamp", "state_hash",
    }
    errors.extend(f"missing:{name}" for name in sorted(required - record.keys()))
    compartment = record.get("compartment")
    if compartment not in ALL_COMPARTMENTS:
        errors.append("invalid_compartment")
    allowed = set(permitted_compartments or ALL_COMPARTMENTS)
    if compartment not in allowed:
        errors.append("compartment_not_permitted")
    inputs = {item.get("entity_id") for item in record.get("input_entities", [])}
    required_inputs = {item.get("entity_id") for item in record.get("required_input_entities", [])}
    if not required_inputs.issubset(inputs):
        errors.append("required_input_missing")
    if record.get("catalyst_or_executor") is None:
        errors.append("executor_missing")
    if any(item.get("status") != "PASS" for item in record.get("positive_regulators", [])):
        errors.append("positive_regulator_not_passed")
    if any(item.get("status") == "BLOCK" for item in record.get("negative_regulators", [])):
        errors.append("negative_regulator_blocked")
    if not record.get("output_entities"):
        errors.append("output_missing")
    if not record.get("evidence_references"):
        errors.append("evidence_custody_missing")
    if record.get("knowledge_status") != "DIRECTLY_OBSERVED" and not record.get("inferred_from_links"):
        errors.append("inference_provenance_missing")
    return {"status": "PASS" if not errors else "BLOCK", "errors": errors}


def validate_transition(record: dict[str, Any], *, executor_authorized: bool, semantic_verification: str, ledger_appended: bool) -> dict[str, Any]:
    event = validate_event(record)
    errors = list(event["errors"])
    if not executor_authorized:
        errors.append("executor_not_authorized")
    if semantic_verification != "PASS":
        errors.append("semantic_verification_failed")
    if not ledger_appended:
        errors.append("event_ledger_not_appended")
    return {"status": "PASS" if not errors else "BLOCK", "errors": errors}


def validate_pathway(record: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    events = record.get("events", [])
    if not events:
        errors.append("events_missing")
    ids = [event.get("event_id") for event in events]
    if len(ids) != len(set(ids)):
        errors.append("duplicate_event_identity")
    for index, event in enumerate(events):
        result = validate_event(event)
        errors.extend(f"event:{index}:{item}" for item in result["errors"])
    if not record.get("proof_references"):
        errors.append("proof_lineage_missing")
    return {"status": "PASS" if not errors else "BLOCK", "errors": errors, "event_count": len(events)}
