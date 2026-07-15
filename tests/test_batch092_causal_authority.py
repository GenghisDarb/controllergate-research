from __future__ import annotations

import json
from pathlib import Path

import pytest

from controllergate.proof.prompt_authorization import derive_historical_authorization
from controllergate.proof.stage_authority import execute_stage, proof_from_verified_stage, verify_stage


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "outputs" / "post_v2_37_hardening_batch092_reactome_complete_pathway_ir_external_review_correction"


def _json(name: str) -> dict:
    return json.loads((OUTPUT / name).read_text(encoding="utf-8"))


def producer(value: dict[str, object]) -> dict[str, object]:
    return {"measured": value["raw"], "stage_ran": True}


def verifier(value: dict[str, object]) -> bool:
    return value.get("stage_ran") is True and "measured" in value


def test_batch091_answer_key_path_is_retired_from_current_authority() -> None:
    retirement = _json("batch091_amds_negative_fixture_retirement.json")
    assert retirement["status"] == "PASS"
    assert retirement["legacy_candidate_count"] == 8
    assert retirement["class_associated_legacy_key_count"] == 8
    assert retirement["current_authority_import_count"] == 0


def test_ineligible_historical_cohort_blocks_instead_of_copying_baselines() -> None:
    quality = _json("amds_quality_gate.json")
    baselines = _json("amds_executed_baselines.json")
    assert quality["status"] == "BLOCK"
    assert quality["eligible_cohort_count"] == 0
    assert quality["post_repair_or_future_receipt_count"] == 0
    assert quality["role_identity_reuse_without_equivalence_count"] > 0
    assert baselines["status"] == "NOT_RUN"
    assert baselines["copied_result_count"] == 0


def test_stage_proof_requires_real_execution_and_independent_verification() -> None:
    output, execution = execute_stage(
        candidate_id="candidate", run_id="run", frame_hash="a" * 64, stage_id="measurement",
        producer=producer, raw_input={"raw": "evidence"}, semantic_scope="unit measurement",
    )
    verification = verify_stage(execution=execution, raw_output=output, verifier=verifier)
    proof = proof_from_verified_stage(execution, verification)
    assert execution.execution_status == "EXECUTED"
    assert verification.verifier_result == "PASS"
    assert proof["execution_depth"] == "executed_and_independently_verified"
    assert proof["stage_execution_receipt"] == execution.receipt_hash


def test_failed_stage_verification_cannot_become_proof() -> None:
    output, execution = execute_stage(
        candidate_id="candidate", run_id="run", frame_hash="b" * 64, stage_id="measurement",
        producer=producer, raw_input={"raw": "evidence"}, semantic_scope="unit measurement",
    )
    verification = verify_stage(execution=execution, raw_output={**output, "tampered": True}, verifier=verifier)
    assert verification.verifier_result == "FAIL"
    with pytest.raises(ValueError, match="verified stage execution required"):
        proof_from_verified_stage(execution, verification)


def test_prompt_authorization_cannot_be_synthesized_without_official_run_binding() -> None:
    contract = json.loads((ROOT / "configs" / "batch092_prompt_contract.json").read_text(encoding="utf-8"))
    binding = contract["human_authorization"]["candidates"][0]
    result = derive_historical_authorization(
        contract=contract, candidate_id=binding["candidate_id"], patch_sha256=binding["patch_sha256"],
        allowed_source_path=binding["allowed_source_path"], workflow_actor=None, workflow_run_id=None,
        workflow_branch=contract["starting_branch"], official_run_started_at=None,
    )
    assert result["status"] == "PENDING_OFFICIAL_WORKFLOW_BINDING"
    altered = dict(contract); altered["exact_prompt_bytes_sha256"] = "0" * 64
    blocked = derive_historical_authorization(
        contract=altered, candidate_id=binding["candidate_id"], patch_sha256=binding["patch_sha256"],
        allowed_source_path=binding["allowed_source_path"], workflow_actor="actor", workflow_run_id="1",
        workflow_branch=contract["starting_branch"], official_run_started_at="2026-07-15T20:00:00Z",
    )
    assert blocked["status"] == "HUMAN_AUTHORIZATION_BLOCKED_EXACT"
