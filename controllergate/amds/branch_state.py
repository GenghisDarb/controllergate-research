from __future__ import annotations

from controllergate.core.evidence import hash_record
from .semantics import BranchStatus


def branch_record(branch_id: str, state: str = BranchStatus.OPEN.value, *, goal_predicate: str, reopen_conditions: list[str] | None = None, evidence_hashes: list[str] | None = None) -> dict:
    value={"branch_id":branch_id,"branch_state":state,"goal_predicate":goal_predicate,"reopen_conditions":list(reopen_conditions or []),"evidence_hashes":list(evidence_hashes or [])};value["state_hash"]=hash_record(value);return value


def transition_branch(branch: dict, new_state: str, evidence_hash: str, *, goal_passed: bool = False, reopen_conditions: list[str] | None = None) -> dict:
    if new_state==BranchStatus.CLOSED.value and not goal_passed: raise ValueError("branch_closure_requires_goal_predicate")
    value={**branch,"branch_state":new_state,"evidence_hashes":[*branch.get("evidence_hashes",[]),evidence_hash],"reopen_conditions":list(reopen_conditions or branch.get("reopen_conditions",[]))};value.pop("state_hash",None);value["state_hash"]=hash_record(value);return value
