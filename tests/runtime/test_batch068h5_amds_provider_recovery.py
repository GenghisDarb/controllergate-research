from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

import pytest

from controllergate.amds.board import build_board, update_board, validate_board
from controllergate.amds.branch_closure import close_branch, reopen_branch
from controllergate.amds.constraints import validate_constraint
from controllergate.amds.posterior import entropy_nats, bayes_update
from controllergate.amds.priors import structural_uniform_prior
from controllergate.amds.probe_executors import executor_contracts, execute_probe
from controllergate.amds.probe_planner import expected_information_gain, rank_probes
from controllergate.amds.probe_registry import PROBE_TYPES, probe_contracts
from controllergate.amds.propagation import propagate_constraints
from controllergate.amds.runtime_adapter import authorize_amds_probe, run_amds_active_loop
from controllergate.amds.stop_policy import evaluate_stop
from controllergate.amds.types import AmdsCell, AmdsConstraint, AmdsEdge, CellState, ProbeCandidate
from controllergate.amds.validators import validate_amds_implementation
from controllergate.runtime.build_provider_resolver import classify_build_failure
from controllergate.runtime.release_catalog import select_release_file
from controllergate.runtime.wheel_compatibility import compatible_with_ordered_tags


def cell(name: str, state: str = "UNKNOWN") -> AmdsCell:
    return AmdsCell(name,"failure_hypothesis","candidate",("a"*64,),state,allowed_probes=("runtime_incident_probe",))


def board() -> dict:
    return build_board("candidate",[cell("a","CAUSAL_MINE"),cell("b")],[AmdsEdge("e","a","b","implies")],[AmdsConstraint("c","implies",("a","b"))])


def test_board_hash_and_cell_hashes(): assert validate_board(board())["status"]=="PASS"
def test_board_tamper_blocks():
    value=board();value["cells"][0]["state"]="SAFE";assert validate_board(value)["status"]=="BLOCK"
def test_constraint_implication_reaches_fixed_point():
    result=propagate_constraints(board());assert result["fixed_point"] and next(c for c in result["cells"] if c["cell_id"]=="b")["state"]=="CAUSAL_MINE"
def test_exactly_one_marks_remaining_safe():
    value=build_board("candidate",[cell("a","CAUSAL_MINE"),cell("b")],[],[AmdsConstraint("c","exactly_one",("a","b"))]);result=propagate_constraints(value);assert next(c for c in result["cells"] if c["cell_id"]=="b")["state"]=="SAFE"
def test_mutual_exclusion_detects_contradiction():
    value=build_board("candidate",[cell("a","CAUSAL_MINE"),cell("b","CAUSAL_MINE")],[],[AmdsConstraint("c","mutually_exclusive",("a","b"))]);assert propagate_constraints(value)["status"]=="BLOCK"
@pytest.mark.parametrize("kind",["requires","excludes","implies","mutually_exclusive","exactly_one","at_least_one","at_most_one","provider_dependency","environment_dependency","source_ownership","provenance_boundary","interlock_boundary","authorization_boundary","rollback_boundary"])
def test_constraint_families_are_executable(kind): assert validate_constraint(AmdsConstraint("c",kind,("a","b")))
def test_board_update_changes_hash():
    value=board();updated,event=update_board(value,{"b":"RESOLVED"},"event");assert event.board_hash_before!=event.board_hash_after and validate_board(updated)["status"]=="PASS"
def test_branch_reopening(): assert reopen_branch(close_branch("b",[{"status":"PASS"}],resolved=True),"new evidence")["status"]=="UNKNOWN"
def test_uniform_prior_is_explicitly_uncalibrated():
    value=structural_uniform_prior(["a","b"]);assert value["classification"]=="structural_uniform_uncalibrated_prior" and value["calibrated"] is False
def test_entropy_and_posterior(): assert entropy_nats({"a":.5,"b":.5})>0 and bayes_update({"a":.5,"b":.5},{"a":1,"b":0})=={"a":1.0,"b":0.0}
def test_information_gain_nats(): assert expected_information_gain({"a":.5,"b":.5},{"yes":{"probability":.5,"posterior":{"a":1.0,"b":0.0}},"no":{"probability":.5,"posterior":{"a":0.0,"b":1.0}}})>0
def test_unknown_likelihood_stays_unknown(): assert expected_information_gain({"a":1.0},{"x":{"probability":None,"posterior":None}}) is None
def test_probe_ranking_not_fixed_constant():
    probes=[ProbeCandidate("p","runtime_incident_probe","c",("a",),execution_cost=.1)];ranked=rank_probes(probes,{"a":.5,"b":.5},{"p":{"yes":{"probability":.5,"posterior":{"a":1.,"b":0.}},"no":{"probability":.5,"posterior":{"a":0.,"b":1.}}}});assert ranked[0]["utility"]!=4
def test_all_thirteen_probe_contracts(): assert set(probe_contracts())==set(PROBE_TYPES)==set(executor_contracts())
def test_probe_authorization_blocks_mutation(): assert execute_probe("runtime_incident_probe",lambda:{"status":"PASS"},{"allowed":True,"mutation_allowed":True})["status"]=="BLOCK"
def test_candidate_scoped_authorization(): assert authorize_amds_probe("c","p")["single_use"] and not authorize_amds_probe("c","p")["mutation_allowed"]
def test_active_loop_updates_board():
    value=build_board("candidate",[cell("a")],[],[]);probe={"probe_id":"p","probe_type":"runtime_incident_probe","cell_id":"a"};result=run_amds_active_loop(value,[probe],lambda p:lambda:{"status":"PASS","evidence_hash":"a"*64,"mutation_count":0});assert result["probes_executed"]==result["board_updates"]==1
def test_stop_policy_budget(): assert evaluate_stop(unresolved_branches=1,legal_probes=1,budget_remaining=0,interlock_pass=True)["reason"]=="probe budget exhausted"
def test_stop_policy_interlock(): assert evaluate_stop(unresolved_branches=1,legal_probes=1,budget_remaining=1,interlock_pass=False)["reason"]=="interlock blocked"
def test_stop_policy_manual_review(): assert evaluate_stop(unresolved_branches=1,legal_probes=1,budget_remaining=1,interlock_pass=True,manual_review=True)["reason"]=="manual review required"
def test_amds_implementation_complete(): assert validate_amds_implementation()["status"]=="PASS"
@pytest.mark.parametrize(("message","family"),[("cargo was not found","rust"),("CMake executable missing","cmake"),("Python.h: no such file","Python_headers"),("unable to execute 'gcc'","C_compiler"),("Killed","resource_limit")])
def test_build_failure_family_classification(message,family): assert family in classify_build_failure(message,1)["matched_failure_families"]
def test_exact_wheel_tag_ranking():
    result=compatible_with_ordered_tags("rpds_py-0.18.1-cp38-abi3-manylinux_2_17_x86_64.whl",["cp313-cp313-manylinux_2_17_x86_64","cp38-abi3-manylinux_2_17_x86_64"]);assert result["compatible"] and result["rank"]==1
def test_incompatible_wheel_rejected(): assert not compatible_with_ordered_tags("x-1.0-cp312-cp312-win_amd64.whl",["cp313-cp313-manylinux_2_17_x86_64"])["compatible"]
def test_pep440_stable_first_selection():
    files=[{"version":"2.0rc1","cutoff_eligible":True,"packagetype":"sdist","yanked":False,"requires_python":None,"target_environment_compatible":True,"selection_preference":4,"filename":"x-2.0rc1.tar.gz"},{"version":"1.9","cutoff_eligible":True,"packagetype":"sdist","yanked":False,"requires_python":None,"target_environment_compatible":True,"selection_preference":4,"filename":"x-1.9.tar.gz"}];assert select_release_file({"files":files},[">=1"],"3.13.0b2")["version"]=="1.9"
def test_explicit_prerelease_requirement():
    files=[{"version":"2.0rc1","cutoff_eligible":True,"packagetype":"sdist","yanked":False,"requires_python":None,"target_environment_compatible":True,"selection_preference":4,"filename":"x-2.0rc1.tar.gz"}];assert select_release_file({"files":files},[">=2.0rc1"],"3.13.0b2")["version"]=="2.0rc1"
