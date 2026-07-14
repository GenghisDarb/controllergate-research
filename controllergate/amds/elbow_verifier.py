from .causal_elbow import categorical_causal_elbow
from .failure_family_graph import FailureFamilyGraph


def verify_elbow(record: dict) -> dict:
    graph = FailureFamilyGraph(record["initial_families"], record["eliminated_families"], record["supporting_observations"])
    recomputed = categorical_causal_elbow(graph, intervention_family=record.get("remaining_family", ""),
                                          confounders_controlled=record.get("confounders_controlled", False),
                                          interlocks_pass=record.get("interlock_state") == "PASS",
                                          rollback_available=record.get("rollback_available", False))
    return {"status": "PASS" if recomputed["elbow"] == record.get("elbow") else "FAIL", "recomputed": recomputed}
