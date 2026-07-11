from __future__ import annotations

from .semantics import HypothesisStatus,ObservationClassification,OperationStatus,BranchStatus


def classify_build_observation(result: dict) -> dict:
    if result.get("operation_status","PASS")!="PASS":return {"operation_status":result.get("operation_status","BLOCK"),"observation_classification":ObservationClassification.SECURITY_BLOCK.value,"hypothesis_state":HypothesisStatus.INCONCLUSIVE.value,"branch_state":BranchStatus.BLOCKED.value}
    if result.get("status")=="PASS":return {"operation_status":OperationStatus.PASS.value,"observation_classification":ObservationClassification.BUILD_SUCCEEDED.value,"hypothesis_state":HypothesisStatus.REFUTED.value,"branch_state":BranchStatus.REMEDIATION_VERIFIED.value}
    text=(result.get("stderr",'')+' '+result.get("stdout",'')).lower()
    if 'could not find a version' in text or 'no matching distribution' in text:obs=ObservationClassification.BACKEND_DEPENDENCY_MISSING.value
    elif 'cargo' in text or 'rustc' in text:obs=ObservationClassification.TOOLCHAIN_MISSING.value
    elif 'compiler' in text or 'gcc' in text:obs=ObservationClassification.COMPILER_MISSING.value
    else:obs=ObservationClassification.BUILD_FAILED.value
    return {"operation_status":OperationStatus.PASS.value,"observation_classification":obs,"hypothesis_state":HypothesisStatus.SUPPORTED.value,"branch_state":BranchStatus.REMEDIATION_PENDING.value}
