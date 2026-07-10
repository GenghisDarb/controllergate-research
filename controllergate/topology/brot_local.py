from __future__ import annotations

from controllergate.core.evidence import hash_record

from .types import ContactLedger14, LocalBrotEdge, LocalBrotGraph, LocalBrotNode


def build_local_brot(ledger: ContactLedger14) -> LocalBrotGraph:
    nodes = [LocalBrotNode("reference-core", "reference_core", "bounded_region", hash_record(ledger.candidate_id))]
    edges: list[LocalBrotEdge] = []
    previous = "reference-core"
    for contact in ledger.contacts:
        region = "bounded_region" if contact.gate_decision == "PASS" else "collapse_region"
        nodes.append(LocalBrotNode(contact.contact_id, "fourteen_contact", region, contact.post_state_hash))
        edges.append(LocalBrotEdge(previous, contact.contact_id, "depends_on", contact.post_state_hash, "decision_time_evidence", contact.confidence, contact.verifier_result, True))
        previous = contact.contact_id
        if contact.gate_decision == "BLOCK":
            reopen = f"reopen:{contact.contact_id}"
            nodes.append(LocalBrotNode(reopen, "proof_path", "recovery_region", hash_record(contact.reopen_conditions)))
            edges.append(LocalBrotEdge(contact.contact_id, reopen, "reopens", hash_record(contact.reopen_conditions), "bounded_recovery", 1.0, "PASS", True))
    return LocalBrotGraph(ledger.candidate_id, tuple(nodes), tuple(edges), "resolve_first_blocked_contact")
