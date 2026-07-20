import dataclasses
import hashlib
import json

import pytest

from controllergate.evidence.batch103_fresh_execution_attestation_v1 import (
    Batch103FreshExecutionReceiptV1,
    verify_batch103_fresh_execution_receipt,
)


def make_receipt(**changes):
    values = {
        field: "x" for field in Batch103FreshExecutionReceiptV1.__dataclass_fields__
    }
    values.update(
        execution_receipt_id="batch103:slice:cell:0",
        execution_epoch="BATCH103_FRESH_OPERATION",
        workflow_run_id="103",
        workflow_job_id="candidate_linux",
        workflow_job_attempt="1",
        workflow_head="a" * 40,
        replay_index=0,
        provider_observed_identity={},
        raw_stdout_object={"sha256": "1" * 64},
        raw_stderr_object={"sha256": "2" * 64},
        raw_return_code=0,
        predicate_result=True,
        truth_access_count=0,
        private_tld_access_count=0,
        patch_operation_count=0,
        cleanup_status="PASS",
        producer="canonical_external_operation_broker",
        independent_verifier="batch103_fresh_receipt_independent_verifier",
        producer_receipt={},
        verifier_receipt={},
    )
    values["source_tree_hash_before"] = values["source_tree_hash_after"] = "3" * 64
    values.update(changes)
    return Batch103FreshExecutionReceiptV1(**values)


def test_batch103_receipt_is_bound_to_current_run_and_head():
    row = make_receipt().record()
    assert verify_batch103_fresh_execution_receipt(
        row, current_workflow_run_id="103", current_workflow_head="a" * 40
    ) == []


def test_batch102_epoch_cannot_be_relabelled_as_batch103():
    with pytest.raises(ValueError, match="Batch103 execution epoch"):
        make_receipt(execution_epoch="BATCH102_FRESH_OPERATION")


def test_attestation_rejects_truth_patch_mutation_and_historical_head():
    row = make_receipt().record()
    row["truth_access_count"] = 1
    blockers = verify_batch103_fresh_execution_receipt(
        row, current_workflow_run_id="103", current_workflow_head="b" * 40
    )
    assert "forbidden_operation_or_private_access" in blockers
    assert "workflow_head_mismatch" in blockers
    assert "record_hash_mismatch" in blockers


def test_campaign_wrapper_requests_batch103_label():
    source = open("scripts/run_batch103_candidate_slice.py", encoding="utf-8").read()
    assert '"--campaign-label", "batch103"' in source
