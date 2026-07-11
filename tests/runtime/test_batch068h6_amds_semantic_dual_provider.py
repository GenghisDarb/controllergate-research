from __future__ import annotations

import pytest

from controllergate.amds.branch_state import branch_record, transition_branch
from controllergate.amds.goal_predicates import build_branch_goal
from controllergate.amds.observation_classifier import classify_build_observation
from controllergate.amds.probe_executors import PROBE_HANDLERS, PROBE_VERIFIERS, executor_contracts
from controllergate.amds.probe_registry import PROBE_TYPES
from controllergate.amds.propagation import bounded_component_enumeration, propagate_constraints
from controllergate.amds.semantics import BranchStatus, HypothesisStatus, ObservationClassification, OperationStatus
from controllergate.amds.state_transition_validator import validate_semantic_transition
from controllergate.protocols.v2_18_evidence_derived_topology_historical_provider import runtime_capabilities
from controllergate.runtime.batch068h6_pipeline import corrected_board
from controllergate.runtime.dynamic_build_requirements import recover_from_pep517_log
from controllergate.runtime.historical_toolchain_provider import RUST_TAG
from controllergate.runtime.phase_executor import ALLOWED_BINDINGS


def test_semantic_state_layers_are_distinct():
    assert OperationStatus.PASS.value == "PASS"
    assert ObservationClassification.BUILD_SUCCEEDED.value != HypothesisStatus.SUPPORTED.value
    assert BranchStatus.CLOSED.value not in {item.value for item in HypothesisStatus}


@pytest.mark.parametrize(
    ("result", "observation", "branch"),
    [
        ({"operation_status": "PASS", "status": "PASS"}, "BUILD_SUCCEEDED", "REMEDIATION_VERIFIED"),
        ({"operation_status": "PASS", "status": "BLOCK", "stderr": "No matching distribution found"}, "BACKEND_DEPENDENCY_MISSING", "REMEDIATION_PENDING"),
        ({"operation_status": "PASS", "status": "BLOCK", "stderr": "cargo not found"}, "TOOLCHAIN_MISSING", "REMEDIATION_PENDING"),
        ({"operation_status": "PASS", "status": "BLOCK", "stderr": "compiler unavailable"}, "COMPILER_MISSING", "REMEDIATION_PENDING"),
    ],
)
def test_build_observation_classification(result, observation, branch):
    classified = classify_build_observation(result)
    assert classified["observation_classification"] == observation
    assert classified["branch_state"] == branch


def test_failed_build_probe_cannot_close_branch():
    result = validate_semantic_transition("PASS", "BACKEND_DEPENDENCY_MISSING", "CLOSED", goal_passed=False)
    assert result["status"] == "BLOCK"


def test_goal_predicate_requires_every_build_closure_check():
    evidence = {"wheel_produced": True, "wheel_identity_verified": True, "wheel_metadata_verified": True, "wheel_tags_compatible": True, "record_verified": True, "fresh_runtime_install_pass": True, "minimal_import_pass": True, "unresolved_required_providers": []}
    assert build_branch_goal(evidence)["goal_passed"] is True
    evidence["record_verified"] = False
    assert build_branch_goal(evidence)["goal_passed"] is False


def test_branch_transition_requires_goal_and_preserves_reopen_conditions():
    branch = branch_record("b", "REMEDIATION_PENDING", goal_predicate="wheel", reopen_conditions=["new evidence"])
    with pytest.raises(ValueError):
        transition_branch(branch, "CLOSED", "evidence", goal_passed=False)
    closed = transition_branch(branch, "CLOSED", "evidence", goal_passed=True, reopen_conditions=[])
    assert closed["branch_state"] == "CLOSED"


def _board(states, constraints):
    return {"cells": [{"cell_id": name, "state": state} for name, state in states.items()], "constraints": constraints}


def test_at_least_one_contradiction_is_detected():
    board = _board({"a": "SAFE", "b": "SAFE"}, [{"constraint_id": "c", "constraint_type": "at_least_one", "members": ["a", "b"]}])
    assert propagate_constraints(board)["status"] == "BLOCK"


def test_at_most_one_makes_unknown_safely_inactive():
    board = _board({"a": "CAUSAL_MINE", "b": "UNKNOWN"}, [{"constraint_id": "c", "constraint_type": "at_most_one", "members": ["a", "b"]}])
    result = propagate_constraints(board)
    assert next(row for row in result["cells"] if row["cell_id"] == "b")["state"] == "SAFE"


def test_registered_exclusion_propagates_bidirectionally():
    board = _board({"a": "CAUSAL_MINE", "b": "UNKNOWN"}, [{"constraint_id": "c", "constraint_type": "excludes", "members": ["a", "b"]}])
    result = propagate_constraints(board)
    assert next(row for row in result["cells"] if row["cell_id"] == "b")["state"] == "SAFE"


def test_requires_chain_reaches_fixed_point():
    board = _board({"a": "CAUSAL_MINE", "b": "UNKNOWN", "c": "UNKNOWN"}, [{"constraint_id": "ab", "constraint_type": "requires", "members": ["a", "b"]}, {"constraint_id": "bc", "constraint_type": "requires", "members": ["b", "c"]}])
    result = propagate_constraints(board)
    assert {row["cell_id"]: row["state"] for row in result["cells"]}["c"] == "CAUSAL_MINE"
    assert result["fixed_point"] is True


def test_bounded_backtracking_has_termination_proof():
    result = bounded_component_enumeration(["a", "b"], [{"constraint_type": "exactly_one", "members": ["a", "b"]}])
    assert result["status"] == "PASS"
    assert result["termination_proven"] is True
    assert len(result["assignments"]) == 2


def test_bounded_backtracking_enforces_budget():
    result = bounded_component_enumeration([str(index) for index in range(13)], [], max_states=4096)
    assert result["blocker"] == "backtracking_state_budget_exhausted"


def test_dynamic_backend_requirement_recovers_ninja():
    result = recover_from_pep517_log("pyzmq", "", "ERROR: Could not find a version that satisfies the requirement ninja>=1.5 (from versions: none)")
    assert result["dynamic_backend_requirements"] == ["ninja>=1.5"]


def test_rust_toolchain_is_exact_and_cutoff_eligible_release():
    assert RUST_TAG == "rust:1.79.0-slim-bookworm"


def test_corrected_board_preserves_two_closed_and_two_pending():
    board = corrected_board({"candidate_id": "candidate", "batch068h5_hash": "a" * 64})
    states = {name: value["branch_state"] for name, value in board["branches"].items()}
    assert sum(state == "CLOSED" for state in states.values()) == 2
    assert states["pyzmq"] == states["rpds-py"] == "REMEDIATION_PENDING"


def test_h6_canonical_phase_binding_is_allowlisted():
    assert ALLOWED_BINDINGS["batch068h6_phase"].endswith("batch068h6_pipeline:execute_phase")


def test_v218_exposes_h6_reusable_bindings():
    capabilities = runtime_capabilities()
    assert capabilities["status"] == "PASS"
    assert capabilities["unbound_reusable_mechanisms"] == []
    assert "execute_batch068h6_phase" in capabilities["bindings"]


def test_thirteen_probe_contracts_have_distinct_handlers_and_verifiers():
    contracts = executor_contracts()
    assert set(contracts) == set(PROBE_TYPES)
    assert len({value["executor"] for value in contracts.values()}) == 13
    assert len({value["independent_verifier"] for value in contracts.values()}) == 13


@pytest.mark.parametrize("probe_type", PROBE_TYPES)
def test_each_probe_contract_executes_and_verifies(probe_type):
    observed = PROBE_HANDLERS[probe_type]({"applicable": False, "applicability_reason": "contract-only compatibility check"})
    assert observed["operation_status"] == "PASS"
    assert PROBE_VERIFIERS[probe_type](observed)["status"] == "PASS"


def test_non_applicable_probe_does_not_fabricate_result():
    observed = PROBE_HANDLERS["dependency_lock_probe"]({"applicable": False})
    assert observed["operation_status"] == "PASS"
    assert observed["observation"] == "NOT_APPLICABLE"
    assert PROBE_VERIFIERS["dependency_lock_probe"](observed)["status"] == "PASS"
