from __future__ import annotations

from controllergate.core.evidence import hash_record

from .types import ContactLedger14, ContactRecord

CONTACT_ROLES = (
    ("CG-C14-01", "artifact_custody"),
    ("CG-C14-02", "candidate_identity"),
    ("CG-C14-03", "source_revision"),
    ("CG-C14-04", "failure_signature"),
    ("CG-C14-05", "target_test"),
    ("CG-C14-06", "command_authority"),
    ("CG-C14-07", "harness_origin"),
    ("CG-C14-08", "runner_origin"),
    ("CG-C14-09", "target_import_origin"),
    ("CG-C14-10", "provider_and_cofactor"),
    ("CG-C14-11", "environment_compartment"),
    ("CG-C14-12", "workspace_and_execution_boundary"),
    ("CG-C14-13", "source_and_failure_topology"),
    ("CG-C14-14", "rollback_and_proof_path"),
)


def build_contact_ledger(candidate_id: str, states: dict[str, dict[str, object]]) -> ContactLedger14:
    contacts: list[ContactRecord] = []
    prior = hash_record({"candidate_id": candidate_id, "state": "reference"})
    for contact_id, role in CONTACT_ROLES:
        state = states.get(role, {})
        evidence = tuple(str(item) for item in state.get("evidence_inputs", (f"candidate:{candidate_id}", f"role:{role}")))
        hashes = tuple(str(item) for item in state.get("evidence_hashes", (hash_record(evidence),)))
        evidence_status = str(state.get("evidence_status", "PARTIAL"))
        verifier = str(state.get("verifier_result", "PASS" if evidence_status == "ESTABLISHED" else "PARTIAL"))
        decision = "PASS" if evidence_status == "ESTABLISHED" and verifier == "PASS" else "BLOCK"
        post = hash_record({"prior": prior, "contact_id": contact_id, "evidence_hashes": hashes, "decision": decision})
        contacts.append(ContactRecord(
            contact_id, role, candidate_id, evidence, hashes, str(state.get("handler_result", evidence_status)), verifier,
            str(state.get("operation_status", "COMPLETED")), evidence_status, decision, str(state.get("contact_state", evidence_status.lower())),
            float(state.get("confidence", 1.0 if decision == "PASS" else 0.5)), tuple(state.get("unresolved_dimensions", ())),
            tuple(state.get("interlocks", ("decision_time_evidence", "claim_boundary"))), state.get("blocker") if decision == "BLOCK" else None,
            tuple(state.get("reopen_conditions", ("provide_missing_decision_time_safe_evidence",))) if decision == "BLOCK" else (), prior, post,
        ))
        prior = post
    validate_contact_ledger(tuple(contacts))
    return ContactLedger14(candidate_id, tuple(contacts), hash_record([item.as_dict() for item in contacts]))


def validate_contact_ledger(contacts: tuple[ContactRecord, ...]) -> None:
    ids = [item.contact_id for item in contacts]
    if len(contacts) != 14:
        raise ValueError("exactly_fourteen_canonical_contacts_required")
    if len(set(ids)) != 14:
        raise ValueError("duplicate_contact")
    if set(ids) != {item[0] for item in CONTACT_ROLES}:
        raise ValueError("exactly_fourteen_canonical_contacts_required")
    for item in contacts:
        if item.gate_decision == "PASS" and (not item.evidence_inputs or not item.evidence_hashes or item.verifier_result != "PASS"):
            raise ValueError("empty_or_unverified_contact_pass")
