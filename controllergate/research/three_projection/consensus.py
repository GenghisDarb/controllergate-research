def consensus_projection(frame: dict) -> dict:
    observations = frame.get("duplicate_observations", [])
    common = set(observations[0].get("claims", [])) if observations else set()
    for item in observations[1:]: common &= set(item.get("claims", []))
    return {"projection": "CONSENSUS_PROJECTION", "invariant_claims": sorted(common), "authority": "NONBLOCKING_RESEARCH"}
