from __future__ import annotations

from controllergate.governance.constitution_v2 import build_registry
from controllergate.governance.law_proof_executor import execute_law, independent_verify_proof


def test_law_status_is_calculated_from_law_specific_proof() -> None:
    law = build_registry()["laws"][0]
    evidence = {law["required_runtime_evidence"][0]: True}
    proof = execute_law(law, evidence, ci_invocation={"job": "test", "invoked": True})
    assert proof["calculated_status"] == "IMPLEMENTED_ENFORCED"
    assert independent_verify_proof(proof)["status"] == "PASS"


def test_missing_law_specific_evidence_is_not_enforced() -> None:
    law = build_registry()["laws"][1]
    proof = execute_law(law, {}, ci_invocation={"job": "test", "invoked": True})
    assert proof["calculated_status"] == "PARTIAL_EXECUTABLE_BLOCKED"


def test_fixed_index_status_is_absent() -> None:
    registry = build_registry()
    assert registry["fixed_index_status_assignment_forbidden"] is True
    assert all("status" not in law for law in registry["laws"])


def test_generic_proof_is_not_shared() -> None:
    laws = build_registry()["laws"]
    assert len({law["proof_artifact"] for law in laws}) == 40
    assert len({law["positive_test_ids"][0] for law in laws}) == 40
    assert len({law["negative_test_ids"][0] for law in laws}) == 40

