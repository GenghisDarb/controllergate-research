from __future__ import annotations

from controllergate.core.evidence import hash_record


def close_branch(branch_id: str, evidence: list[dict], *, resolved: bool, reopen_conditions: list[str] | None = None) -> dict:
    return {"branch_id":branch_id,"status":"RESOLVED" if resolved else "BLOCKED","evidence_hashes":[hash_record(v) for v in evidence],"reopen_conditions":list(reopen_conditions or [])}


def reopen_branch(value: dict, reason: str) -> dict:
    return {**value,"status":"UNKNOWN","reopened":True,"reopen_reason":reason}
