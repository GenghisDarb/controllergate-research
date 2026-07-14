from __future__ import annotations

from controllergate.reactions.stable_identity import stable_hash


ALLOWED_FIELDS = {
    "ast_node_family_pattern", "call_graph_pattern", "exception_propagation_pattern", "provider_topology",
    "harness_topology", "compartment_transitions", "normal_incident_divergence_pattern", "failed_reaction_pattern",
    "rollback_proof_topology", "probe_cost_history",
}


def contact_topology_signature(record: dict[str, object]) -> dict[str, object]:
    forbidden = set(record) - ALLOWED_FIELDS
    if forbidden:
        raise ValueError(f"forbidden_homology_fields:{','.join(sorted(forbidden))}")
    return {"features": record, "signature": stable_hash(record)}
