def baseline_projection(frame: dict) -> dict:
    controls = frame.get("controls", {})
    common = None
    for claims in controls.values(): common = set(claims) if common is None else common & set(claims)
    return {"projection": "BASELINE_PROJECTION", "invariant_claims": sorted(common or set()), "controls": sorted(controls), "authority": "NONBLOCKING_RESEARCH"}
