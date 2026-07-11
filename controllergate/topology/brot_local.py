from __future__ import annotations

from controllergate.core.evidence import hash_record

from .types import ContactLedger14, LocalBrotEdge, LocalBrotGraph, LocalBrotNode

SEMANTIC_RELATIONS = (
    ("candidate_identity", "source_revision", "authority_dependency"),
    ("failure_signature", "target_test", "oracle_dependency"),
    ("command_authority", "harness_origin", "authority_dependency"),
    ("harness_origin", "runner_origin", "authority_dependency"),
    ("runner_origin", "target_import_origin", "environment_dependency"),
    ("provider_and_cofactor", "environment_compartment", "provider_dependency"),
    ("environment_compartment", "target_import_origin", "environment_dependency"),
    ("workspace_and_execution_boundary", "harness_origin", "causal_dependency"),
    ("source_and_failure_topology", "rollback_and_proof_path", "proof_requirement"),
    ("rollback_and_proof_path", "artifact_custody", "rollback"),
)


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


def build_semantic_local_brot(candidate_id: str, contacts: list[dict[str, object]]) -> dict[str, object]:
    by_role = {str(item["canonical_role"]): item for item in contacts}
    nodes = [{"node_id": f"{candidate_id}:{role}", "role": role, "region": "bounded_region" if item["gate_decision"] == "PASS" else "unresolved_region", "evidence_hashes": item["evidence_hashes"]} for role, item in by_role.items()]
    edges: list[dict[str, object]] = []
    roles = list(by_role)
    for left, right in zip(roles, roles[1:]):
        hashes = list(by_role[left]["evidence_hashes"]) + list(by_role[right]["evidence_hashes"])
        if hashes:
            edges.append({"rule_id": "BROT-CANONICAL-SEQUENCE", "source_node": left, "target_node": right, "edge_class": "canonical_sequence", "evidence_hashes": sorted(set(hashes)), "authority_class": "canonical_operational_law", "confidence": 1.0, "interlock_result": "PASS", "verifier_result": "PASS"})
    for source, target, edge_class in SEMANTIC_RELATIONS:
        left = by_role.get(source); right = by_role.get(target)
        if left and right and left["evidence_hashes"] and right["evidence_hashes"]:
            hashes = sorted(set(list(left["evidence_hashes"]) + list(right["evidence_hashes"])))
            edges.append({"rule_id": f"BROT-{source.upper()}-TO-{target.upper()}", "source_node": source, "target_node": target, "edge_class": edge_class, "evidence_hashes": hashes, "authority_class": "role_specific_evidence", "confidence": min(float(left["confidence"]), float(right["confidence"])), "interlock_result": "PASS", "verifier_result": "PASS"})
    return {"candidate_id": candidate_id, "nodes": nodes, "edges": edges, "semantic_edge_count": sum(item["edge_class"] != "canonical_sequence" for item in edges), "graph_hash": hash_record({"nodes": nodes, "edges": edges})}
