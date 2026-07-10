from __future__ import annotations

from .elbow_policy import ELBOW_CLASSIFICATIONS, OPEN_REQUIREMENTS
from .failure_family import ElbowDecision
from .failure_family_graph import FailureFamilyGraph


def verify_elbow(decision: ElbowDecision, graph: FailureFamilyGraph, facts: dict[str, bool], *, environment_established: bool, logs_available: bool) -> dict[str, object]:
    errors: list[str] = []
    if decision.classification not in ELBOW_CLASSIFICATIONS:
        errors.append("unknown_elbow_classification")
    if decision.intervention_authorized:
        isolated = [node for node in graph.nodes.values() if node.isolated and node.reproducible]
        if len(isolated) != 1: errors.append("open_without_single_family")
        if not environment_established: errors.append("open_without_environment_orthology")
        if not logs_available: errors.append("open_without_logs")
        if not all(facts.get(name) is True for name in OPEN_REQUIREMENTS): errors.append("open_without_all_requirements")
    return {"status": "PASS" if not errors else "FAIL", "errors": errors, "raw_argmin_used": False, "winner_label_used": False}
