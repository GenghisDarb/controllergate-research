from .contract import InterlockContract


def _verified_token(value: object, expected_type: str) -> bool:
    return isinstance(value, dict) and value.get("token_type") == expected_type and bool(value.get("token_hash")) and bool(value.get("independent_verifier"))


def apply_negative_regulation(contract: InterlockContract, evidence: dict) -> dict:
    forbidden = evidence.get("forbidden_evidence", [])
    missing = [item for item in contract.canonical_inputs if not _verified_token(evidence.get(item), item)]
    passed = not forbidden and not missing
    return {"interlock_id": contract.interlock_id, "status": "PASS" if passed else "BLOCK",
            "missing_inputs": missing, "forbidden_evidence": forbidden,
            "can_authorize_patch": False, "reopen_condition": None if passed else contract.reopen_condition}
