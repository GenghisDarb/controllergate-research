from __future__ import annotations

import json

import pytest

from controllergate.amds.canonical_v3 import diagnose, quality_gate
from controllergate.amds.memory_isolation import IsolatedMemoryStore
from controllergate.intake.failure_contract_v2 import FailureContractV2
from controllergate.intake.structured_collection import verify_collection
from controllergate.reactions.token_kernel import ReactionToken
from controllergate.runtime.provider_service import ProviderPlan, verify_provider_ready
from scripts.audit_canonical_component_uniqueness import audit as uniqueness_audit


def source_token():
    return ReactionToken.mint(token_type="SOURCE_ACQUIRED_TOKEN", candidate_id="candidate", run_id="run", producer_event="source", input_tokens=(), payload={"tree": "x"}, independent_verifier="test")


def test_canonical_component_uniqueness():
    assert uniqueness_audit()["status"] == "PASS"


def test_timeout_is_not_candidate_failure():
    result = FailureContractV2("resource_timeout", True, True, True, True, 10).validate()
    assert result["status"] == "BLOCK"
    assert "timeout_not_candidate_failure_evidence" in result["errors"]


def test_structured_collection_requires_valid_payload_and_immutability(tmp_path):
    path = tmp_path / "collection.json"
    path.write_text(json.dumps({"nodes": ["tests/test_x.py::test_x"], "internal_error": False}), encoding="utf-8")
    assert verify_collection(path, "tests/test_x.py::test_x", return_code=0, source_hash_before="a", source_hash_after="a", test_hash_before="b", test_hash_after="b")["status"] == "PASS"
    assert verify_collection(path, "missing", return_code=0, source_hash_before="a", source_hash_after="a", test_hash_before="b", test_hash_after="b")["status"] == "BLOCK"


def test_provider_requires_two_matching_offline_installs_and_all_probes():
    plan = ProviderPlan("graph", "linux", "3.11", "cp311", ("wheel",), "none")
    ready = verify_provider_ready(candidate_id="candidate", run_id="run", source_token=source_token(), plan=plan, offline_install_hashes=("a", "a"), dependency_check=True, import_probes=True, entry_point_probes=True, read_only_execution_view=True)
    assert ready.token_type == "PROVIDER_EXECUTION_READY_TOKEN"
    with pytest.raises(ValueError, match="lifecycle"):
        verify_provider_ready(candidate_id="candidate", run_id="run", source_token=source_token(), plan=plan, offline_install_hashes=("a", "b"), dependency_check=True, import_probes=True, entry_point_probes=True, read_only_execution_view=True)


def test_memory_truth_patch_physical_separation_and_truth_join(tmp_path):
    store = IsolatedMemoryStore(tmp_path / "routing.jsonl", tmp_path / "truth.jsonl", tmp_path / "patch.jsonl")
    sealed = store.append_routing({"candidate_id": "candidate", "topology": ["a", "b"]})
    assert store.join_truth_after_seal(sealed, {"terminal": "provider_owned"})["sealed_decision_hash"] == sealed
    with pytest.raises(ValueError, match="forbidden"):
        store.append_routing({"candidate_id": "candidate", "patch": "secret"})


def test_amds_has_no_source_fallback_and_quality_rejects_wrong_authorization():
    abstain = diagnose([])
    assert abstain.classification == "insufficient_evidence" and not abstain.patch_authorized
    wrong = diagnose([{"direct": True, "classification": "source_owned", "source_contact_verified": True}])
    assert quality_gate([wrong], ["provider_owned"])["status"] == "FAIL"
