from .baseline import baseline_projection
from .consensus import consensus_projection
from .perturbation import perturbation_projection


def run_three_projection_audit(frame: dict) -> dict:
    results = [consensus_projection(frame), perturbation_projection(frame), baseline_projection(frame)]
    intersection = set(results[0]["invariant_claims"])
    for item in results[1:]: intersection &= set(item["invariant_claims"])
    return {"status": "PASS", "projections": results, "invariant_intersection": sorted(intersection),
            "contradictions": {item["projection"]: item.get("contradictions", []) for item in results},
            "authority": "NONBLOCKING_RESEARCH", "can_grant_source_ownership": False,
            "can_grant_patch_authority": False, "n10_n13_n14_assignments_assumed": False}
