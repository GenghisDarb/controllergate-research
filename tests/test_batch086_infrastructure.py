from __future__ import annotations

import json
import zipfile
from pathlib import Path

from controllergate.amds.causal_elbow import categorical_causal_elbow
from controllergate.amds.dpp14.engine import TRANSITIONS, run_dpp14
from controllergate.amds.failure_family_graph import FailureFamilyGraph
from controllergate.interlocks.audit import audit_registry
from controllergate.interlocks.negative_regulation import apply_negative_regulation
from controllergate.interlocks.contract import InterlockContract
from controllergate.reactions.orientation import Orientation
from controllergate.reactions.return_map import double_traversal
from controllergate.reactions.twist_audit import audit_twist_return
from controllergate.research.three_projection.interlock import run_three_projection_audit
from controllergate.runtime.historical_package_cutoff import cutoff_eligible
from controllergate.runtime.historical_provider_equivalence import compare_independent_builds, compare_installed_graphs
from controllergate.state.repository import ControllerStateRepository


ROOT = Path(__file__).resolve().parents[1]


def test_historical_provider_cutoff_and_graph_equivalence():
    assert cutoff_eligible("2024-01-01T00:00:00Z", "2024-01-02T00:00:00Z")
    assert not cutoff_eligible("2024-01-03T00:00:00Z", "2024-01-02T00:00:00Z")
    assert compare_installed_graphs([{"name": "Pytest", "version": "8"}], [{"name": "pytest", "version": "8"}])["status"] == "PASS"


def test_two_build_normalized_wheel_equivalence(tmp_path):
    paths = [tmp_path / "a.whl", tmp_path / "b.whl"]
    for index, path in enumerate(paths):
        with zipfile.ZipFile(path, "w") as archive:
            archive.writestr("pkg/module.py", "VALUE = 1\n")
            archive.writestr("pkg-1.dist-info/RECORD", f"volatile-{index}")
    result = compare_independent_builds(*paths)
    assert result["status"] == "PASS"
    assert result["normalized_contents_equivalent"] is True


def test_dpp14_transition_count_parallel_merge_and_safe_abstention():
    assert len(TRANSITIONS) == 14
    result = run_dpp14("candidate", {"source": "s", "provider": "p", "runtime": "r", "command": "c", "target": "t",
        "probes": [{"probe_id": "b", "lane": "provider", "classification": "provider_owned", "direct": True},
                   {"probe_id": "a", "lane": "source", "classification": "provider_owned", "direct": True}],
        "facts": [{"subject": "provider", "value": "p", "verified": True, "evidence_kind": "verified_provider_result"}],
        "interlocks": {"provider": "PASS"}})
    assert len(result["trace"]) == 14
    assert result["terminal"] == "provider_owned"
    assert result["trace"][-1]["sole_merged_state_writer"] is True


def test_dpp14_rejects_source_fallback_and_mutating_lane():
    frame = {"source": "s", "provider": "p", "runtime": "r", "command": "c", "target": "t",
             "probes": [{"probe_id": "x", "classification": "source_owned_behavior_defect", "direct": True, "mutates": True}]}
    result = run_dpp14("candidate", frame)
    assert result["terminal"] == "insufficient_evidence"
    assert result["observations"][0]["status"] == "BLOCK"


def test_interlock_recovery_and_non_authorization():
    assert audit_registry(ROOT)["status"] == "PASS"
    contract = InterlockContract("source", ("source revision",))
    token = {"token_type": "source revision", "token_hash": "a" * 64, "independent_verifier": "fixture-verifier"}
    assert apply_negative_regulation(contract, {"source revision": token})["status"] == "PASS"
    assert apply_negative_regulation(contract, {"source revision": "PASS"})["status"] == "BLOCK"
    blocked = apply_negative_regulation(contract, {"source revision": "MISSING"})
    assert blocked["status"] == "BLOCK"
    assert blocked["can_authorize_patch"] is False


def test_categorical_elbow_requires_one_supported_family():
    graph = FailureFamilyGraph(["source", "provider"], ["provider"], [{"probe": "direct source divergence"}])
    opened = categorical_causal_elbow(graph, intervention_family="source", confounders_controlled=True, interlocks_pass=True, rollback_available=True)
    assert opened["elbow"] == "OPEN"
    assert opened["numeric_threshold_authority"] is False
    graph.eliminated_families = []
    assert categorical_causal_elbow(graph, intervention_family="source", confounders_controlled=True, interlocks_pass=True, rollback_available=True)["elbow"] == "CLOSED"


def test_exact_double_return_and_rollback_identity():
    value = Orientation("reference", "incident", "normal", "patched", "decision_time", "source", "provider", "parent")
    assert double_traversal(value) == value
    assert audit_twist_return(value, rollback_source_hash="source")["status"] == "PASS"
    assert audit_twist_return(value, rollback_source_hash="other")["status"] == "FAIL"


def test_three_projection_is_shadow_only():
    result = run_three_projection_audit({"duplicate_observations": [{"claims": ["a", "b"]}, {"claims": ["a"]}],
        "baseline_claims": ["a", "b"], "perturbations": [{"claims": ["a"]}],
        "controls": {"null": ["a"], "fixed": ["a", "c"]}})
    assert result["invariant_intersection"] == ["a"]
    assert result["authority"] == "NONBLOCKING_RESEARCH"
    assert result["can_grant_patch_authority"] is False
    assert result["n10_n13_n14_assignments_assumed"] is False


def test_failed_branch_lineage_is_durable_and_noncounting(tmp_path):
    repository = ControllerStateRepository(tmp_path / "state.sqlite3")
    record = {"attempt_identity": "a", "parent_event": "p", "input_tokens": ["t"], "candidate_id": "c",
              "source_identity": "s", "provider_seal": "v", "operation_identity": "o",
              "failure_class": "provider", "new_information": {"fact": True}, "rollback_target": "s",
              "branch_closed": True, "reopen_condition": "new provider", "next_legal_action": "reconstruct provider"}
    digest = repository.record_failed_branch(record)
    row = repository.connection.execute("SELECT * FROM failed_branch_lineage WHERE branch_hash=?", (digest,)).fetchone()
    assert row["count_increment"] == 0
    assert row["reopen_condition"] == "new provider"
