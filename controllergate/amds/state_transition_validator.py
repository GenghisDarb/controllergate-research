from __future__ import annotations

from .semantics import BranchStatus,ObservationClassification,OperationStatus


def validate_semantic_transition(operation_status: str, observation: str, branch_state: str, *, goal_passed: bool = False) -> dict:
    errors=[]
    if operation_status==OperationStatus.PASS.value and observation in {ObservationClassification.BUILD_FAILED.value,ObservationClassification.BACKEND_DEPENDENCY_MISSING.value,ObservationClassification.TOOLCHAIN_MISSING.value} and branch_state==BranchStatus.CLOSED.value:errors.append('diagnostic_operation_cannot_close_failed_branch')
    if branch_state==BranchStatus.CLOSED.value and not goal_passed:errors.append('closed_branch_requires_goal_predicate')
    return {"status":"PASS" if not errors else "BLOCK","errors":errors}
