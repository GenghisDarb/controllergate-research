from __future__ import annotations

import json
from pathlib import Path

import pytest

from controllergate.amds.dpp14.blind_runtime import run_blind_episode
from controllergate.engine import _register_manifest_proofs
from controllergate.proof.authorization_tokens import produce_stage_proof, validate_candidate_bound_approval
from controllergate.state.repository import ControllerStateRepository


def test_manifest_injected_proof_rejected(tmp_path: Path) -> None:
    repository = ControllerStateRepository(tmp_path / "state.sqlite")
    with pytest.raises(ValueError, match="manifest-injected"):
        _register_manifest_proofs(repository, {"proof_records": [{"status": "PASS"}]}, "f" * 64)


def test_stage_proof_requires_independent_executed_evidence(tmp_path: Path) -> None:
    repository = ControllerStateRepository(tmp_path / "state.sqlite")
    repository.create_run("run", "candidate", {})
    with pytest.raises(ValueError, match="independent"):
        produce_stage_proof(repository, requirement="identity", candidate_id="candidate", run_id="run", frame_hash="f" * 64, producer_identity="same", verifier_identity="same", raw_evidence_hashes=["a" * 64], derivation_parents=[], semantic_scope="identity", evidence_value=True)


def test_candidate_bound_approval_rejects_generic_record() -> None:
    with pytest.raises(ValueError, match="mismatch"):
        validate_candidate_bound_approval({"human_authority": "Brad"}, contract_hash="c", candidate_id="candidate", run_id="run", patch_sha256="a" * 64, allowed_source_path="x.py")


def test_blind_runtime_rejects_terminal_label(tmp_path: Path) -> None:
    result = run_blind_episode({"candidate_id": "x", "run_id": "r", "terminal_class": "source", "anchors": {"source_and_test_tree_identity": "a" * 64}, "probes": []}, tmp_path)
    assert result["status"] == "BLOCK"


def test_batch091_cohort_has_exact_order_and_no_truth_fields() -> None:
    config = json.loads(Path("configs/batch091_amds_measurement_contracts.json").read_text(encoding="utf-8"))
    assert [item["candidate_id"] for item in config["candidates"]] == [
        "darker_issue_112_relative_git_dir", "py_bugger_issue_65",
        "cloudpickle_507_py313_typevar_distutils", "freezegun_547_py313_datetimes_assertion",
        "audioread_144_py313_aifc_removed", "pytest_13480_wdefault_unraisable_threadexception",
        "incident_openbb_7585_modular_openapi_reproducer", "incident_poetry_10974_init_duplicate_name",
    ]
    serialized = json.dumps(config)
    assert "terminal_class" not in serialized
    assert "episode_kind" not in serialized
