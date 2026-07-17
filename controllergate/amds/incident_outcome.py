from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import Enum
from typing import Any


class IncidentOutcomeFamily(str, Enum):
    NONZERO_FAILURE = "NONZERO_FAILURE"
    SUCCESS_WITH_INVALID_PRODUCT = "SUCCESS_WITH_INVALID_PRODUCT"
    SUCCESS_WITH_STATE_DEFECT = "SUCCESS_WITH_STATE_DEFECT"
    WARNING_ONLY_FAILURE = "WARNING_ONLY_FAILURE"
    IMPORT_OR_COLLECTION_FAILURE = "IMPORT_OR_COLLECTION_FAILURE"
    TRANSPORT_OR_SERVICE_FAILURE = "TRANSPORT_OR_SERVICE_FAILURE"
    SAFE_ABSTENTION_INSUFFICIENT_EVIDENCE = "SAFE_ABSTENTION_INSUFFICIENT_EVIDENCE"


BROAD_MARKERS = frozenset({"failed", "warning", "error", "silent failure"})
FORBIDDEN_CAUSAL_KEYS = frozenset({"terminal_class", "expected_terminal", "causal_family", "source_owned"})


def canonical_hash(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


@dataclass(frozen=True)
class IncidentOutcomeContract:
    contract_id: str
    candidate_id: str
    run_id: str
    frame_id: str
    command_identity: str
    family: IncidentOutcomeFamily
    expected_return_codes: tuple[int, ...]
    required_product_paths: tuple[str, ...]
    product_schema: dict[str, Any]
    product_semantic_invariants: dict[str, Any]
    positive_control_id: str
    negative_control_id: str
    allowed_output_fields: tuple[str, ...]
    exact_output_identities: tuple[str, ...]
    producer_identity: str
    verifier_identity: str
    failure_terminal: str
    reopen_condition: str

    def validate(self) -> None:
        if self.producer_identity == self.verifier_identity:
            raise ValueError("incident producer/verifier identity collision")
        if any(marker.lower() in BROAD_MARKERS for marker in self.exact_output_identities):
            raise ValueError("broad markers are not an incident identity")
        if not self.positive_control_id or not self.negative_control_id:
            raise ValueError("positive and negative controls are required")
        if any(key in FORBIDDEN_CAUSAL_KEYS for key in self.allowed_output_fields):
            raise ValueError("causal labels are forbidden from raw incident output")

    @property
    def contract_hash(self) -> str:
        return canonical_hash(self.record(include_hash=False))

    def record(self, *, include_hash: bool = True) -> dict[str, Any]:
        value = {
            "contract_id": self.contract_id,
            "candidate_id": self.candidate_id,
            "run_id": self.run_id,
            "frame_id": self.frame_id,
            "command_identity": self.command_identity,
            "expected_process_level_outcome": self.family.value,
            "expected_return_codes": list(self.expected_return_codes),
            "required_product_paths": list(self.required_product_paths),
            "product_schema": self.product_schema,
            "product_semantic_invariants": self.product_semantic_invariants,
            "required_positive_control": self.positive_control_id,
            "required_negative_control": self.negative_control_id,
            "allowed_output_fields": list(self.allowed_output_fields),
            "forbidden_causal_labels": sorted(FORBIDDEN_CAUSAL_KEYS),
            "exact_output_identities": list(self.exact_output_identities),
            "producer_identity": self.producer_identity,
            "independent_verifier_identity": self.verifier_identity,
            "failure_terminal": self.failure_terminal,
            "reopen_condition": self.reopen_condition,
        }
        if include_hash:
            value["contract_hash"] = self.contract_hash
        return value


def _product_invariants_match(invariants: dict[str, Any], product: dict[str, Any]) -> bool:
    for key, expected in invariants.items():
        observed = product.get(key)
        if isinstance(expected, dict):
            if "equals" in expected and observed != expected["equals"]:
                return False
            if "minimum" in expected and (not isinstance(observed, (int, float)) or observed < expected["minimum"]):
                return False
            if "maximum" in expected and (not isinstance(observed, (int, float)) or observed > expected["maximum"]):
                return False
            if "nonempty" in expected and bool(observed) is not bool(expected["nonempty"]):
                return False
        elif observed != expected:
            return False
    return True


def verify_incident_outcome(
    contract: IncidentOutcomeContract,
    *,
    process: dict[str, Any],
    product: dict[str, Any],
    controls: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    contract.validate()
    reasons: list[str] = []
    if process.get("candidate_id") != contract.candidate_id or process.get("run_id") != contract.run_id:
        reasons.append("candidate_or_run_identity_mismatch")
    if process.get("command_identity") != contract.command_identity:
        reasons.append("command_identity_mismatch")
    if process.get("return_code") not in contract.expected_return_codes:
        reasons.append("process_return_code_mismatch")
    if any(key in FORBIDDEN_CAUSAL_KEYS for key in process) or any(key in FORBIDDEN_CAUSAL_KEYS for key in product):
        reasons.append("forbidden_causal_label_in_raw_evidence")
    if set(product) - set(contract.allowed_output_fields):
        reasons.append("undeclared_product_field")
    if not _product_invariants_match(contract.product_semantic_invariants, product):
        reasons.append("product_semantic_invariant_mismatch")
    positive = controls.get(contract.positive_control_id, {})
    negative = controls.get(contract.negative_control_id, {})
    if positive.get("status") != "PASS":
        reasons.append("positive_control_failed")
    if negative.get("status") != "PASS":
        reasons.append("negative_control_failed")
    if process.get("transport_failure") and contract.family is not IncidentOutcomeFamily.TRANSPORT_OR_SERVICE_FAILURE:
        reasons.append("transport_failure_is_not_target_incident")
    if product.get("producer_operation_hash") != process.get("record_hash"):
        reasons.append("product_producer_lineage_mismatch")
    status = "PASS" if not reasons else "BLOCK"
    evidence = {
        "process": process,
        "product": product,
        "controls": controls,
        "contract_hash": contract.contract_hash,
    }
    return {
        "status": status,
        "candidate_id": contract.candidate_id,
        "contract_id": contract.contract_id,
        "outcome_family": contract.family.value,
        "typed_incident_materialized": status == "PASS",
        "raw_evidence_hash": canonical_hash(evidence),
        "reasons": reasons,
        "producer_identity": contract.producer_identity,
        "independent_verifier_identity": contract.verifier_identity,
        "authority_allowed": "frozen cohort incident eligibility" if status == "PASS" else "blocker evidence",
        "authority_forbidden": ["causal ownership", "repair authority", "count increment"],
        "failure_terminal": None if status == "PASS" else contract.failure_terminal,
        "reopen_condition": contract.reopen_condition,
    }
