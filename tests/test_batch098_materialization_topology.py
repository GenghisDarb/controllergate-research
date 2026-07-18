from __future__ import annotations

import json
from pathlib import Path

import pytest

from controllergate.amds.stage_runtime_v7 import STAGES, run_dpp14
from controllergate.amds.truth_maintenance_v1 import TruthMaintenanceV1, VerifiedCausalFactV1
from controllergate.evidence.contracts import CandidateExecutionContract, FORBIDDEN_FIELDS, load_contracts, seal_contracts
from controllergate.evidence.materializer import COMPARTMENTS, split_manifest
from controllergate.evidence.observations import TypedObservationParser, configured_value_injection_audit, marker_only_verification_audit
from controllergate.topology.causal_hypergraph import BoardCellV1, BoardEdgeV1, CellState, connected_regions
from controllergate.topology.modality_conflicts_v1 import ModalityProposal, reconcile_modalities
from controllergate.topology.probe_compiler_v1 import compile_topology_decision_frame, deterministic_minimax_probe, probe_stagnation_control


ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / "configs" / "candidate_execution_contracts_v2.jsonl"


def _contract_record() -> dict:
    return json.loads(CONTRACTS.read_text(encoding="utf-8").splitlines()[0])


def _cell(subject: str, state: CellState = CellState.UNRESOLVED, cell_class: str = "OWNERSHIP_SOURCE") -> BoardCellV1:
    return BoardCellV1(
        candidate_id="candidate",
        run_id="run",
        frame_id="frame",
        cell_class=cell_class,
        subject=subject,
        state=state,
        parent_evidence=(f"sha256:{subject:0<64}"[:71],),
        producer_execution_receipt=f"producer:{subject}",
        verifier_execution_receipt=f"verifier:{subject}",
        semantic_scope=subject,
        authority_allowed="provisional",
        authority_forbidden=("repair",),
        reopen_condition="execute a discriminating probe",
    )


def test_candidate_contracts_are_exact_eight_and_truth_blind() -> None:
    contracts = load_contracts(CONTRACTS)
    assert len(contracts) == 8
    assert seal_contracts(contracts)["status"] == "PASS"
    assert not FORBIDDEN_FIELDS.intersection(_contract_record())
    darker = contracts[0]
    assert darker.candidate_id == "darker_issue_112_relative_git_dir"
    assert darker.target_argv[-2:] == ("--check", "src")
    assert any(row["control_id"] == "darker-unrelated-exit-one" for row in darker.adversarial_controls)


def test_contract_rejects_truth_and_outcome_fields() -> None:
    record = _contract_record()
    record["terminal_class"] = "source"
    with pytest.raises(ValueError, match="forbidden"):
        CandidateExecutionContract.from_mapping(record)


def test_six_compartments_and_git_manifest_split_are_disjoint() -> None:
    assert len(COMPARTMENTS) == len(set(COMPARTMENTS)) == 6
    source, tests = split_manifest(
        {"src/a.py": {"object_id": "a"}, "tests/test_a.py": {"object_id": "b"}},
        ("tests/test_a.py",),
    )
    assert list(source) == ["src/a.py"]
    assert list(tests) == ["tests/test_a.py"]


def test_typed_parsers_do_not_copy_configured_values(tmp_path: Path) -> None:
    junit = tmp_path / "junit.xml"
    junit.write_text('<testsuite><testcase classname="m" name="t"><failure type="AssertionError">x</failure></testcase></testsuite>', encoding="utf-8")
    parsed = TypedObservationParser.junit(junit)
    assert parsed["cases"][0]["outcome"] == "failure"
    assert configured_value_injection_audit({"operation_count": 7}, {"operation_count": 7})["status"] == "BLOCK"
    assert marker_only_verification_audit({"markers": ["failed"], "structured_product_parents": []})["status"] == "BLOCK"


def test_board_edges_need_distinct_verifier_and_regions_are_connected() -> None:
    left, right = _cell("left"), _cell("right", cell_class="OWNERSHIP_PROVIDER")
    with pytest.raises(ValueError, match="must differ"):
        BoardEdgeV1("candidate", "run", "frame", left.cell_id, right.cell_id, "CONTRADICTS", ("raw",), "same", "same", "scope", "provisional", ("repair",), "reopen")
    edge = BoardEdgeV1("candidate", "run", "frame", left.cell_id, right.cell_id, "CONTRADICTS", ("raw",), "producer", "verifier", "scope", "provisional", ("repair",), "reopen")
    regions = connected_regions("candidate", [left, right], [edge])
    assert len(regions) == 1
    assert set(regions[0].cell_ids) == {left.cell_id, right.cell_id}


def test_topology_compiler_owns_hypotheses_and_probes() -> None:
    cells = [_cell("source"), _cell("provider", cell_class="OWNERSHIP_PROVIDER")]
    edge = BoardEdgeV1("candidate", "run", "frame", cells[0].cell_id, cells[1].cell_id, "MUTUALLY_EXCLUSIVE", ("raw",), "producer", "verifier", "scope", "provisional", ("repair",), "reopen")
    frame = compile_topology_decision_frame(
        candidate={"candidate_id": "candidate", "run_id": "run", "frame_id": "frame"},
        contract={**_contract_record(), "candidate_id": "candidate"},
        cells=cells,
        edges=[edge],
        regions=connected_regions("candidate", cells, [edge]),
        budgets={"timeout_seconds": 10, "processes": 1},
    )
    assert frame["caller_supplied_decisive_input_count"] == 0
    assert len(frame["hypotheses"]) == 2
    assert frame["empty_derivation_hypothesis_count"] == 0
    assert frame["non_executable_probe_count"] == 0
    assert frame["partitionless_probe_count"] == 0
    selected = deterministic_minimax_probe(frame["probes"], [row["hypothesis_id"] for row in frame["hypotheses"]])
    assert selected is not None


def test_stagnation_and_modality_conflict_do_not_write_terminals() -> None:
    result = probe_stagnation_control(["a", "b"], [False, False], threshold=2)
    assert result["status"] == "TRIGGERED"
    assert "repair authority" in result["authority_forbidden"]
    conflict = reconcile_modalities(
        [
            ModalityProposal("candidate", "TEMPORAL", "s", "VERIFIED_TRUE", ("o1",), "p1", "v1", ()),
            ModalityProposal("candidate", "STRUCTURAL", "s", "VERIFIED_FALSE", ("o2",), "p2", "v2", ()),
        ],
        ["probe:conflict"],
    )
    assert conflict["conflict_count"] == 1
    assert conflict["uncalibrated_averaging_count"] == 0


def test_truth_maintenance_backtracks_from_observed_contradiction() -> None:
    truth = TruthMaintenanceV1({"cell": CellState.VERIFIED_TRUE}, [])
    fact = VerifiedCausalFactV1("candidate", "run", "frame", "cell", CellState.VERIFIED_FALSE, ("observation",), "rule", "verifier", ("other",), "scope", "deterministic/direct", "branch", "reopen")
    event = truth.apply(fact, nonce="once")
    assert event["event"] == "observation_driven_contradiction"
    assert truth.result()["failed_branches"]
    assert truth.result()["spent_nonce_count"] == 1
    repeated = truth.apply(fact, nonce="different")
    assert repeated["event"] == "repeated_branch_rejected"


def test_dpp14_executes_and_independently_verifies_all_stages() -> None:
    terminal, produced, verified = run_dpp14({"topology_probes": [{"probe_id": "p"}]})
    assert terminal["terminal_writer"].endswith("ControllerAudit")
    assert terminal["executed_stages"] == list(STAGES)
    assert len(produced) == len(verified) == 14
    assert all(row["status"] == "PASS" for row in verified)
    assert all(row["producer_verifier_distinct"] for row in verified)
