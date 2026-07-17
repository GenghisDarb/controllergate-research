from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class IncidentClass(str, Enum):
    PROVIDER_OR_COFACTOR_ABSENCE = "provider_or_cofactor_absence"
    BUILD_OR_INSTALL_STALL = "build_or_install_stall"
    WORKER_OR_PROCESS_STALL = "worker_or_process_stall"
    COLLISION_OR_BACKPRESSURE = "collision_or_backpressure"
    INCOMPLETE_PRODUCT = "incomplete_product"
    EXIT_ZERO_INVALID_PRODUCT = "exit_zero_invalid_product"
    IMPORT_OR_COLLECTION_FAILURE = "import_or_collection_failure"
    WARNING_ONLY_DEFECT = "warning_only_defect"
    RUNNER_OR_HARNESS_FAILURE = "runner_or_harness_failure"
    TRANSPORT_OR_SERVICE_FAILURE = "transport_or_service_failure"
    SOURCE_BEHAVIOR_DEFECT = "source_behavior_defect"
    MIXED_FAILURE = "mixed_failure"
    INSUFFICIENT_EVIDENCE = "unknown_or_insufficient_evidence"


@dataclass(frozen=True)
class RecoveryDecision:
    incident_class: IncidentClass
    action: str
    preserve_provider: bool
    preserve_evidence: bool
    patch_allowed: bool = False


RECOVERY = {
    IncidentClass.PROVIDER_OR_COFACTOR_ABSENCE: RecoveryDecision(IncidentClass.PROVIDER_OR_COFACTOR_ABSENCE, "reconstruct_provider", False, True),
    IncidentClass.BUILD_OR_INSTALL_STALL: RecoveryDecision(IncidentClass.BUILD_OR_INSTALL_STALL, "rescue_build", True, True),
    IncidentClass.WORKER_OR_PROCESS_STALL: RecoveryDecision(IncidentClass.WORKER_OR_PROCESS_STALL, "terminate_and_replay_worker", True, True),
    IncidentClass.COLLISION_OR_BACKPRESSURE: RecoveryDecision(IncidentClass.COLLISION_OR_BACKPRESSURE, "drain_and_replay", True, True),
    IncidentClass.INCOMPLETE_PRODUCT: RecoveryDecision(IncidentClass.INCOMPLETE_PRODUCT, "reject_product", True, True),
    IncidentClass.EXIT_ZERO_INVALID_PRODUCT: RecoveryDecision(IncidentClass.EXIT_ZERO_INVALID_PRODUCT, "reject_product", True, True),
    IncidentClass.IMPORT_OR_COLLECTION_FAILURE: RecoveryDecision(IncidentClass.IMPORT_OR_COLLECTION_FAILURE, "separate_runner_provider_source", True, True),
    IncidentClass.WARNING_ONLY_DEFECT: RecoveryDecision(IncidentClass.WARNING_ONLY_DEFECT, "verify_warning_contract", True, True),
    IncidentClass.RUNNER_OR_HARNESS_FAILURE: RecoveryDecision(IncidentClass.RUNNER_OR_HARNESS_FAILURE, "reconstruct_harness", True, True),
    IncidentClass.TRANSPORT_OR_SERVICE_FAILURE: RecoveryDecision(IncidentClass.TRANSPORT_OR_SERVICE_FAILURE, "restore_bounded_service", True, True),
    IncidentClass.SOURCE_BEHAVIOR_DEFECT: RecoveryDecision(IncidentClass.SOURCE_BEHAVIOR_DEFECT, "request_source_ownership_proof", True, True),
    IncidentClass.MIXED_FAILURE: RecoveryDecision(IncidentClass.MIXED_FAILURE, "decompose_before_action", True, True),
    IncidentClass.INSUFFICIENT_EVIDENCE: RecoveryDecision(IncidentClass.INSUFFICIENT_EVIDENCE, "safe_abstention", True, True),
}


def classify(*, return_code: int | None, product_valid: bool | None, transport_failed: bool, import_failed: bool, warning_only: bool) -> RecoveryDecision:
    if transport_failed: return RECOVERY[IncidentClass.TRANSPORT_OR_SERVICE_FAILURE]
    if import_failed: return RECOVERY[IncidentClass.IMPORT_OR_COLLECTION_FAILURE]
    if return_code == 0 and product_valid is False: return RECOVERY[IncidentClass.EXIT_ZERO_INVALID_PRODUCT]
    if warning_only: return RECOVERY[IncidentClass.WARNING_ONLY_DEFECT]
    return RECOVERY[IncidentClass.INSUFFICIENT_EVIDENCE]
