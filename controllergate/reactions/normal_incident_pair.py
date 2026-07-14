from __future__ import annotations

from controllergate.reactions.stable_identity import stable_hash


def pair_pathways(normal: dict[str, object], incident: dict[str, object]) -> dict[str, object]:
    for key in ("source", "provider", "platform_runtime", "command"):
        if normal.get(key) != incident.get(key):
            raise ValueError(f"normal_incident_pair_mismatch:{key}")
    value = {
        "normal_pathway": normal,
        "incident_pathway": incident,
        "shared_inputs": normal.get("inputs", []),
        "shared_source": normal.get("source"),
        "shared_provider": normal.get("provider"),
        "shared_platform_runtime": normal.get("platform_runtime"),
        "shared_command_reproducer": normal.get("command"),
        "expected_output": normal.get("output"),
        "observed_output": incident.get("output"),
        "last_shared_valid_event": normal.get("last_shared_valid_event"),
        "first_divergent_event": incident.get("first_divergent_event"),
        "direct_divergence_evidence": incident.get("direct_divergence_evidence", []),
        "inferred_divergence_evidence": incident.get("inferred_divergence_evidence", []),
        "ast_contact_domain": incident.get("ast_contact_domain", []),
    }
    return {**value, "pair_hash": stable_hash(value)}
