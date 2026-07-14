from __future__ import annotations

from .failure_family_graph import FailureFamilyGraph


def categorical_causal_elbow(graph: FailureFamilyGraph, *, intervention_family: str,
                             confounders_controlled: bool, interlocks_pass: bool,
                             rollback_available: bool) -> dict:
    remaining = graph.remaining
    open_elbow = (len(graph.initial_families) > 1 and bool(graph.supporting_observations)
                  and len(remaining) == 1 and remaining[0] == intervention_family
                  and confounders_controlled and interlocks_pass and rollback_available)
    return {"initial_families": graph.initial_families, "eliminated_families": graph.eliminated_families,
            "supporting_observations": graph.supporting_observations, "remaining_family": remaining[0] if len(remaining) == 1 else None,
            "unresolved_alternatives": remaining if len(remaining) != 1 else [], "elbow": "OPEN" if open_elbow else "CLOSED",
            "interlock_state": "PASS" if interlocks_pass else "BLOCK", "raw_argmin_authority": False,
            "numeric_threshold_authority": False,
            "next_legal_action": "bounded_family_local_intervention" if open_elbow else "collect_discriminating_observation_or_abstain"}
