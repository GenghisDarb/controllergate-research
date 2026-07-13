from __future__ import annotations

from typing import Any


def calculate_status(proof: dict[str, Any]) -> tuple[str, str | None]:
    core = (
        proof.get("owner_import_result") == "PASS"
        and proof.get("enforcer_execution_result") == "PASS"
        and proof.get("positive_test_execution") == "PASS"
        and proof.get("negative_test_execution") == "PASS"
        and proof.get("required_evidence_verification") == "PASS"
        and proof.get("ci_invocation_record") is not None
        and proof.get("proof_hash") is not None
        and proof.get("independent_verifier_result") == "PASS"
    )
    if core:
        return "IMPLEMENTED_ENFORCED", None
    if proof.get("owner_import_result") != "PASS":
        return "BLOCKED_EXACT", "constitution_v2_owner_module_unavailable"
    return "PARTIAL_EXECUTABLE_BLOCKED", "constitution_v2_law_specific_proof_incomplete"

