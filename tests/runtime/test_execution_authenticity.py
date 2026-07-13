from __future__ import annotations

from datetime import datetime, timedelta, timezone

from controllergate.execution.evidence_kind import EvidenceKind
from controllergate.execution.execution_claim_verifier import verify_execution_claims
from controllergate.execution.execution_record import ExecutionRecord


def base(kind=EvidenceKind.NOT_RUN, operation="NOT_RUN"):
    return ExecutionRecord(execution_id="e", stage_id="s", candidate_id="c", evidence_kind=kind, authorization_id="a", operation_status=operation, evidence_status="NONE", gate_decision="BLOCK", candidate_state="BLOCKED").to_dict()


def test_not_run_record_is_valid_when_not_claimed_pass():
    assert verify_execution_claims([base()], claimed_executed_stages=0)["status"] == "PASS"


def test_pass_not_run_rejected():
    row = base(); row["gate_decision"] = "PASS"
    assert verify_execution_claims([row])["status"] == "BLOCK"


def test_command_missing_argv_rejected():
    row = base(EvidenceKind.EXECUTED_COMMAND, "EXECUTED")
    assert verify_execution_claims([row])["status"] == "BLOCK"


def test_callable_missing_hash_rejected():
    row = base(EvidenceKind.EXECUTED_CALLABLE, "EXECUTED")
    assert verify_execution_claims([row])["status"] == "BLOCK"


def test_future_timestamp_rejected():
    row = base(); row["start_timestamp"] = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
    assert verify_execution_claims([row])["status"] == "BLOCK"


def test_collection_pass_nonzero_rejected_by_status_model():
    row = base(); row["return_code"] = 3; row["gate_decision"] = "PASS"
    assert verify_execution_claims([row])["status"] == "BLOCK"


def test_generic_copied_blocker_rejected():
    one = base(); one.update(candidate_id="a", exact_blocker="same")
    two = base(); two.update(candidate_id="b", exact_blocker="same")
    assert verify_execution_claims([one, two])["status"] == "BLOCK"


def test_provider_recovered_without_artifacts_rejected():
    row = {"stage_id": "provider", "evidence_kind": "DERIVED_VERIFICATION", "operation_status": "RECOVERED", "gate_decision": "PASS"}
    assert verify_execution_claims([row])["failures"][0]["reason"] == "provider_recovered_without_artifacts"


def test_internalerror_collection_pass_rejected():
    row = {"stage_id": "collection", "evidence_kind": "EXECUTED_COMMAND", "operation_status": "PASS", "gate_decision": "PASS", "argv": ["python"], "return_code": 0, "internal_error": True}
    assert verify_execution_claims([row])["status"] == "BLOCK"


def test_preserved_evidence_cannot_be_fresh():
    row = {"evidence_kind": "PRESERVED_PRIOR_EVIDENCE", "operation_status": "PRESERVED", "gate_decision": "PASS", "fresh_execution_claim": True}
    assert verify_execution_claims([row])["status"] == "BLOCK"
