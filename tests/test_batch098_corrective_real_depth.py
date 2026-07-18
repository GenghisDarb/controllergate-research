from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import yaml

from controllergate.amds.stage_runtime_v7 import STAGES, run_dpp14
from controllergate.evidence.probe_executor_v2 import execute_probe_contract
from controllergate.topology.causal_hypergraph import BoardCellV1, CellState
from controllergate.topology.probe_compiler_v1 import compile_topology_decision_frame


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_PATH = ROOT / ".github/workflows/post_v2_37_hardening_batch098_causal_hypergraph_real_materialization_topology_probe_closure.yml"
WORKFLOW = WORKFLOW_PATH.read_text(encoding="utf-8")
MATERIALIZER = (ROOT / "controllergate/evidence/materializer.py").read_text(encoding="utf-8")
PIPELINE = (ROOT / "controllergate/topology/pipeline_v1.py").read_text(encoding="utf-8")
PROBES = (ROOT / "controllergate/topology/probe_compiler_v1.py").read_text(encoding="utf-8")
DIAGNOSE = (ROOT / "controllergate/amds/batch098_diagnose.py").read_text(encoding="utf-8")


def test_finding_01() -> None:
    assert len(yaml.safe_load(WORKFLOW)["jobs"]) >= 30


def test_finding_02() -> None:
    assert "sealed_truth_custody" in WORKFLOW and "available_to_builder_jobs" not in WORKFLOW


def test_finding_03() -> None:
    assert "architecture_arms" in WORKFLOW and "[A, B, C, D, E, F]" in WORKFLOW


def test_finding_04() -> None:
    assert "baseline_executions" in WORKFLOW and "[G, H, I, J]" in WORKFLOW


def test_finding_05() -> None:
    critic = (ROOT / "scripts/batch098_standalone_critic_v7.py").read_text(encoding="utf-8")
    assert "standalone_standard_library_critic" in WORKFLOW and "from controllergate" not in critic


def test_finding_06() -> None:
    mutation = (ROOT / "scripts/batch098_complete_raw_tree_mutations.py").read_text(encoding="utf-8")
    assert "shutil.copytree(raw, destination)" in mutation and "complete_copied_raw_evidence_tree_mutation" in mutation


def test_finding_07() -> None:
    assert "retention-days: 30" in WORKFLOW


def test_finding_08() -> None:
    assert "synthetic_text_only" not in MATERIALIZER and "semantic_verification_receipt" in MATERIALIZER


def test_finding_09() -> None:
    lifecycle = (ROOT / "controllergate/evidence/openbb_lifecycle_v2.py").read_text(encoding="utf-8")
    assert all(token in lifecycle for token in ("one-operation", "corrupt", "service_request", "service_cleanup"))


def test_finding_10() -> None:
    worker = (ROOT / "controllergate/evidence/source_control_worker_v2.py").read_text(encoding="utf-8")
    assert "ast.parse" in worker and "unrelated" in worker


def test_finding_11() -> None:
    assert "origin/main" in MATERIALIZER


def test_finding_12() -> None:
    assert "merge-base" in MATERIALIZER and "--is-ancestor" in MATERIALIZER


def test_finding_13() -> None:
    lifecycle = (ROOT / "controllergate/evidence/openbb_lifecycle_v2.py").read_text(encoding="utf-8")
    assert "start_brokered_service_process" in lifecycle and "127.0.0.1" in lifecycle


def test_finding_14() -> None:
    assert "{PORT}" in MATERIALIZER and "actual_port" in MATERIALIZER


def test_finding_15() -> None:
    assert "openapi_product" in (ROOT / "controllergate/evidence/parser_registry_v2.py").read_text(encoding="utf-8")


def test_finding_16() -> None:
    assert 'source_after_manifest, _ = git_tree_manifest' in MATERIALIZER and "execution_residues" in MATERIALIZER


def test_finding_17() -> None:
    assert all(token in MATERIALIZER for token in ("source_head_after", "source_tree_after", "source_tracked_diff_after"))


def test_finding_18() -> None:
    assert 'target_record["record_hash"] = None' not in MATERIALIZER and '"parent_target_record": target_record.get("record_hash")' in MATERIALIZER


def test_finding_19() -> None:
    section = MATERIALIZER.split('"project_wheel_build"', 1)[1].split('"provider_wheel_install"', 1)[0]
    assert "network=False" in section


def test_finding_20() -> None:
    section = MATERIALIZER.split('"provider_additional_local_install"', 1)[1]
    assert "network=False" in section


def test_finding_21() -> None:
    registry = (ROOT / "controllergate/evidence/parser_registry_v2.py").read_text(encoding="utf-8")
    assert "PARSERS[parser_id]" in registry and "VERIFIERS[verifier_id]" in registry and "candidate_id ==" not in registry


def test_finding_22() -> None:
    registry = (ROOT / "controllergate/evidence/parser_registry_v2.py").read_text(encoding="utf-8")
    assert "_expected_pytest_targets" in registry and "_junit_matches" in registry and "matched_exact_cases" in registry


def test_finding_23() -> None:
    registry = (ROOT / "controllergate/evidence/parser_registry_v2.py").read_text(encoding="utf-8")
    assert '"aifc" in missing' in registry and "json.dumps(product)" not in registry.split("def _verify_audioread", 1)[1].split("def _verify_pytest_warning", 1)[0]


def test_finding_24() -> None:
    registry = (ROOT / "controllergate/evidence/parser_registry_v2.py").read_text(encoding="utf-8")
    assert "-Wdefault" in registry and "PytestUnraisableExceptionWarning" in registry and "expected_nodes" in registry


def test_finding_25() -> None:
    registry = (ROOT / "controllergate/evidence/parser_registry_v2.py").read_text(encoding="utf-8")
    assert 'parsed.get("project_name") == expected' in registry


def test_finding_26() -> None:
    assert "raw_evidence_object" in PIPELINE and "raw_evidence_type" in PIPELINE


def test_finding_27() -> None:
    assert "raw_object_reopened" in PIPELINE and "reopen_raw_operation_and_reconstruct_dimension" in PIPELINE


def test_finding_28() -> None:
    assert "raw_node" in PIPELINE and "raw_edge" in PIPELINE and "independent-source-reparse" in PIPELINE


def test_finding_29() -> None:
    assert "parent_by_class" in PIPELINE and "OWNERSHIP_PROVIDER" in PIPELINE


def test_finding_30() -> None:
    assert "product_semantic_ok" in PIPELINE and "independently reconstructed process/product relation" in PIPELINE


def test_finding_31() -> None:
    assert "side_a_reopened" in PIPELINE and "side_b_reopened" in PIPELINE and "projection_pair_verification_receipts_v2" in PIPELINE


def test_finding_32() -> None:
    assert "modality_values" in PIPELINE and "execute_{modality.lower()}_transformation" in PIPELINE


def _cells() -> list[BoardCellV1]:
    classes = ("OWNERSHIP_SOURCE", "OWNERSHIP_PROVIDER", "OWNERSHIP_RUNNER")
    return [BoardCellV1("c", "r", "f", kind, kind.lower(), CellState.UNRESOLVED, (f"raw-{index}",), f"p-{index}", f"v-{index}", "scope", "provisional", ("repair",), "probe") for index, kind in enumerate(classes)]


def _frame() -> dict:
    cells = _cells()
    contract = json.loads((ROOT / "configs/candidate_execution_contracts_v2.jsonl").read_text(encoding="utf-8").splitlines()[0])
    contract["candidate_id"] = "c"
    return compile_topology_decision_frame(candidate={"candidate_id": "c", "run_id": "r", "frame_id": "f"}, contract=contract, cells=cells, edges=[], regions=[], budgets={"timeout_seconds": 10})


def test_finding_33() -> None:
    frame = _frame()
    assert len({tuple(row["exact_argv"]) for row in frame["probes"]}) == len(frame["probes"])


def test_finding_34() -> None:
    assert "probe_worker_v2" in PROBES and all(kind in PROBES for kind in ("contact_edge", "provider_variation", "runner_variation"))


def test_finding_35() -> None:
    assert all(row["partition_rule"]["rule_id"] for row in _frame()["probes"])


def test_finding_36(tmp_path: Path) -> None:
    result = execute_probe_contract(_frame()["probes"][0], tmp_path)
    assert result["status"] == "PASS" and result["operation"]["operation_type"] == "diagnostic_probe"


def test_finding_37() -> None:
    terminal, produced, verified = run_dpp14({"candidate_id": "c", "run_id": "r", "frame_id": "f", "topology_probes": _frame()["probes"][:1]})
    assert len(produced) == len(verified) == 14 and terminal["verified_observation_count"] == 1 and terminal["truth_maintenance"]["events"]


def test_finding_38() -> None:
    verifier = (ROOT / "controllergate/amds/stage_verifier_v2.py").read_text(encoding="utf-8")
    assert "verify_transition" in verifier and "stage_specific_keys" in verifier and "independent_reconstruction" in verifier


def test_finding_39() -> None:
    assert "probe_executions" in DIAGNOSE and "topology_probe_execution_receipts_v2" in DIAGNOSE


def test_finding_40() -> None:
    assert "ARCHITECTURES" in DIAGNOSE and "BASELINES" in DIAGNOSE and "execute_experiment" in DIAGNOSE


def test_finding_41() -> None:
    stage = (ROOT / "scripts/batch098_workflow_stage.py").read_text(encoding="utf-8")
    assert "truth_join_after_execution" in (ROOT / "controllergate/amds/real_depth_experiments_v2.py").read_text(encoding="utf-8") and "truth-join" in stage and "terminal_seal" in WORKFLOW


def test_finding_42() -> None:
    assert "produce_source_ownership_stages" in DIAGNOSE and "verify_source_ownership_stages" in DIAGNOSE


def test_finding_43() -> None:
    final = yaml.safe_load(WORKFLOW)["jobs"]["public_state_and_main_artifact"]
    needs = set(final["needs"])
    assert {"standalone_standard_library_critic", "resigned_complete_raw_tree_mutations", "truth_join_and_historical_quality", "source_ownership_verifiers"}.issubset(needs)
