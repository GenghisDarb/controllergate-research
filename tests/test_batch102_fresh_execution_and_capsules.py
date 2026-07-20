from __future__ import annotations

from dataclasses import fields

import pytest

from controllergate.evidence.execution_epoch_v1 import BATCH102_FRESH_OPERATION
from controllergate.evidence.fresh_execution_attestation_v1 import Batch102FreshExecutionReceiptV1, verify_fresh_execution_receipt
from controllergate.evidence.provider_capsule_v4 import build_provider_capsule_v4, classify_provider_exactness, verify_provider_capsule_v4


HEAD = "1" * 40


def fresh_receipt() -> dict:
    values = {
        "execution_receipt_id": "receipt:1", "execution_epoch": BATCH102_FRESH_OPERATION,
        "workflow_run_id": "42", "workflow_job_id": "candidate_pybugger", "workflow_job_attempt": "1",
        "workflow_head": HEAD, "candidate_id": "candidate", "program_id": "program", "cell_id": "cell", "replay_index": 1,
        "broker_operation_id": "operation:1", "broker_record_hash": "a" * 64, "source_capsule_hash": "b" * 64,
        "source_commit": "c" * 40, "source_tree_hash_before": "d" * 40, "source_tree_hash_after": "d" * 40,
        "provider_capsule_hash": "e" * 64, "provider_observed_identity": {"version": "3.11.0"},
        "provider_exactness_status": "EXACT_PROVIDER", "platform": "linux", "architecture": "x86_64", "ABI": "cp311", "SOABI": "cpython-311-x86_64-linux-gnu",
        "exact_argv_hash": "f" * 64, "cwd_hash": "0" * 64, "environment_hash": "1" * 64, "fixture_hash": "2" * 64,
        "raw_stdout_object": {"sha256": "3" * 64}, "raw_stderr_object": {"sha256": "4" * 64}, "raw_return_code": 1,
        "semantic_projection_id": "v2", "semantic_fingerprint": "5" * 64, "predicate_registry_hash": "6" * 64,
        "predicate_result": True, "network_policy": "none", "truth_access_count": 0, "private_tld_access_count": 0,
        "patch_operation_count": 0, "cleanup_status": "PASS", "producer": "canonical_external_operation_broker",
        "independent_verifier": "batch102_receipt_verifier", "producer_receipt": {"operation_id": "operation:1"},
        "verifier_receipt": {"status": "PASS"},
    }
    return Batch102FreshExecutionReceiptV1(**values).record()


def test_fresh_receipt_has_every_required_field_and_validates() -> None:
    row = fresh_receipt()
    assert set(field.name for field in fields(Batch102FreshExecutionReceiptV1)) <= set(row)
    assert verify_fresh_execution_receipt(row, current_workflow_run_id="42", current_workflow_head=HEAD) == []


@pytest.mark.parametrize("mutation,blocker", [
    ({"execution_epoch": "BATCH100_RAW_EXECUTION"}, "inherited_execution_rejected"),
    ({"workflow_run_id": "41"}, "workflow_run_mismatch"),
    ({"broker_operation_id": ""}, "broker_operation_missing"),
    ({"source_tree_hash_after": "e" * 40}, "source_tree_mutated"),
    ({"patch_operation_count": 1}, "forbidden_operation_or_private_access"),
])
def test_fresh_receipt_rejects_false_freshness(mutation: dict, blocker: str) -> None:
    row = fresh_receipt(); row.update(mutation)
    assert blocker in verify_fresh_execution_receipt(row, current_workflow_run_id="42", current_workflow_head=HEAD)


def test_provider_exactness_requires_every_semantic_identity_field() -> None:
    requested = {"implementation": "CPython", "version_tuple": [3, 13, 0], "prerelease": {"level": "beta", "serial": 1}, "os": "linux", "architecture": "x86_64", "ABI": "cp313", "SOABI": "cpython-313-x86_64-linux-gnu"}
    assert classify_provider_exactness(requested, dict(requested)) == "EXACT_PROVIDER"
    prefix_only = dict(requested); prefix_only["version_tuple"] = [3, 13, 1]
    assert classify_provider_exactness(requested, prefix_only) == "SERIES_LIMITED_PROVIDER"
    wrong_os = dict(requested); wrong_os["os"] = "windows"
    assert classify_provider_exactness(requested, wrong_os) != "EXACT_PROVIDER"
    capsule = build_provider_capsule_v4(capsule_id="provider:1", candidate_id="candidate", requested=requested, observed=dict(requested), materialization_receipt={"operation_id": "op:1"}, runner_image="ubuntu-latest", dependency_graph_hash="0" * 64, wheel_hashes=[])
    assert verify_provider_capsule_v4(capsule) == []
