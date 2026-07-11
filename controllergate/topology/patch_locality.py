from __future__ import annotations


def derive_patch_locality(ownership: dict[str, object], trace: dict[str, object]) -> dict[str, object]:
    established = ownership.get("status") == "PASS" and trace.get("status") == "PASS"
    return {"candidate_id": ownership["candidate_id"], "status": "PASS" if established else "NOT_ESTABLISHED", "patch_locality_region": list(ownership.get("candidate_source_files") or []) if established else [], "broad_semantic_alteration_risk": "NOT_ESTABLISHED" if not established else "bounded", "patch_license": False}
