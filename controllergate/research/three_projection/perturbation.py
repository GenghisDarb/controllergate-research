def perturbation_projection(frame: dict) -> dict:
    baseline = set(frame.get("baseline_claims", [])); variants = frame.get("perturbations", [])
    stable = set(baseline)
    for item in variants: stable &= set(item.get("claims", []))
    contradictions = sorted(baseline - stable)
    return {"projection": "PERTURBATION_PROJECTION", "invariant_claims": sorted(stable), "contradictions": contradictions, "authority": "NONBLOCKING_RESEARCH"}
