from __future__ import annotations

from .board import validate_board
from .probe_registry import PROBE_TYPES, probe_contracts


def validate_amds_implementation() -> dict:
    contracts=probe_contracts(); valid=set(contracts)==set(PROBE_TYPES) and all(v.get("authorization_required") for v in contracts.values())
    return {"status":"PASS" if valid else "BLOCK","probe_executor_contract_count":len(contracts),"hardcoded_candidate_logic":False}


def verify_probe_observation(value: dict) -> dict:
    valid=value.get("status") in {"PASS","BLOCK","NOT_APPLICABLE","MANUAL_REVIEW"} and value.get("mutation_count",0)==0
    return {"status":"PASS" if valid else "BLOCK"}
