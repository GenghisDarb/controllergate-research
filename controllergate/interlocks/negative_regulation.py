from .contract import InterlockContract


def apply_negative_regulation(contract: InterlockContract, evidence: dict) -> dict:
    forbidden = evidence.get("forbidden_evidence", [])
    missing = [item for item in contract.canonical_inputs if evidence.get(item) != "PASS"]
    passed = not forbidden and not missing
    return {"interlock_id": contract.interlock_id, "status": "PASS" if passed else "BLOCK",
            "missing_inputs": missing, "forbidden_evidence": forbidden,
            "can_authorize_patch": False, "reopen_condition": None if passed else contract.reopen_condition}
