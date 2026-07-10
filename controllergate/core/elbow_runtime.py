from __future__ import annotations

from .elbow_policy import OPEN_REQUIREMENTS
from .failure_family import ElbowDecision
from .failure_family_graph import FailureFamilyGraph


def decide_elbow(graph: FailureFamilyGraph, facts: dict[str, bool], *, environment_established: bool, logs_available: bool) -> ElbowDecision:
    hashes = tuple(sorted({value for node in graph.nodes.values() for value in node.evidence_hashes}))
    if not logs_available:
        return ElbowDecision("elbow_closed_evidence_insufficient", None, hashes, False, "capture_lossless_collection_diagnostics")
    if not environment_established:
        return ElbowDecision("elbow_closed_environment_orthology", None, hashes, False, "batch068h2_historical_environment_capsule_recovery")
    isolated = [node for node in graph.nodes.values() if node.isolated and node.reproducible]
    if len(isolated) != 1:
        return ElbowDecision("elbow_closed_multi_family_ambiguous", None, hashes, False, "decompose_failure_families")
    if not all(facts.get(name) is True for name in OPEN_REQUIREMENTS):
        return ElbowDecision("elbow_closed_evidence_insufficient", isolated[0].family_id, hashes, False, "close_elbow_preconditions")
    node = isolated[0]
    if node.provider_involvement:
        classification = "elbow_open_provider_local_recovery_authorized"
    elif node.harness_involvement:
        classification = "elbow_open_harness_local_recovery_authorized"
    elif node.source_involvement:
        classification = "elbow_open_source_local_patch_diagnostic_authorized"
    else:
        classification = "elbow_open_single_causal_family_recovery_authorized"
    return ElbowDecision(classification, node.family_id, hashes, True, "bounded_family_local_diagnostic")
