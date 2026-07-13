from __future__ import annotations

import copy
from typing import Any

from controllergate.core.evidence import hash_record
from controllergate.governance.constitution_v2 import enforce_law
from controllergate.governance.law_status_adjudicator import calculate_status


def _proof_hash(record: dict[str, Any]) -> str:
    check = dict(record)
    check.pop("proof_hash", None)
    check.pop("independent_verifier_result", None)
    check.pop("calculated_status", None)
    check.pop("exact_blocker", None)
    return hash_record(check)


def independent_verify_proof(proof: dict[str, Any]) -> dict[str, Any]:
    failures: list[str] = []
    if _proof_hash(proof) != proof.get("proof_hash"):
        failures.append("proof_hash_invalid")
    if proof.get("positive_test_id") == proof.get("negative_test_id"):
        failures.append("positive_negative_test_not_distinct")
    if proof.get("negative_test_execution") != "PASS":
        failures.append("negative_control_did_not_reject")
    return {"status": "PASS" if not failures else "BLOCK", "failures": failures}


def execute_law(law: dict[str, Any], runtime_evidence: dict[str, Any], *, ci_invocation: dict[str, Any] | None) -> dict[str, Any]:
    result = enforce_law(law, runtime_evidence)
    negative = copy.deepcopy(runtime_evidence)
    for key in law.get("required_runtime_evidence", []):
        negative.pop(key, None)
    negative_result = enforce_law(law, negative)
    proof: dict[str, Any] = {
        "law_id": law["requirement_id"],
        "law_definition_hash": law["definition_hash"],
        "owner_module": law["owner_module"],
        "enforcement_callable": law["enforcement_callable"],
        "owner_import_result": "PASS" if result["owner_imported"] else "BLOCK",
        "enforcer_execution_result": result["status"],
        "positive_test_id": law["positive_test_ids"][0],
        "positive_test_execution": result["status"],
        "negative_test_id": law["negative_test_ids"][0],
        "negative_test_execution": "PASS" if negative_result["status"] == "BLOCK" else "BLOCK",
        "required_evidence_verification": "PASS" if result["required_evidence_present"] else "BLOCK",
        "verified_runtime_evidence_keys": [key for key in law["required_runtime_evidence"] if runtime_evidence.get(key) is True],
        "ci_invocation_record": ci_invocation,
        "proof_artifact": law["proof_artifact"],
        "proof_hash": None,
        "independent_verifier_result": None,
    }
    proof["proof_hash"] = _proof_hash(proof)
    proof["independent_verifier_result"] = independent_verify_proof(proof)["status"]
    proof["calculated_status"], proof["exact_blocker"] = calculate_status(proof)
    return proof


def execute_registry(registry: dict[str, Any], runtime_evidence: dict[str, Any], *, ci_invocation: dict[str, Any] | None) -> list[dict[str, Any]]:
    return [execute_law(law, runtime_evidence, ci_invocation=ci_invocation) for law in registry["laws"]]

