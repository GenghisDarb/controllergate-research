from __future__ import annotations

import hashlib
import inspect
import json
from dataclasses import dataclass
from typing import Any, Callable


def _hash(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _code_hash(callable_object: Callable[..., object]) -> str:
    return hashlib.sha256(inspect.getsource(callable_object).encode()).hexdigest()


@dataclass(frozen=True)
class StageExecutionReceipt:
    candidate_id: str
    run_id: str
    frame_hash: str
    stage_id: str
    producer_identity: str
    producer_code_hash: str
    raw_input_hashes: tuple[str, ...]
    raw_output_hashes: tuple[str, ...]
    execution_depth: str
    semantic_scope: str
    parent_proofs: tuple[str, ...]
    execution_status: str

    @property
    def receipt_hash(self) -> str:
        return _hash(self.__dict__)

    def record(self) -> dict[str, Any]:
        return {**self.__dict__, "raw_input_hashes": list(self.raw_input_hashes), "raw_output_hashes": list(self.raw_output_hashes), "parent_proofs": list(self.parent_proofs), "receipt_hash": self.receipt_hash}


@dataclass(frozen=True)
class StageVerificationReceipt:
    execution_receipt_hash: str
    candidate_id: str
    run_id: str
    frame_hash: str
    verifier_identity: str
    verifier_code_hash: str
    verified_raw_output_hashes: tuple[str, ...]
    verifier_result: str
    freshness: str
    revoked: bool
    semantic_scope: str

    @property
    def receipt_hash(self) -> str:
        return _hash(self.__dict__)

    def record(self) -> dict[str, Any]:
        return {**self.__dict__, "verified_raw_output_hashes": list(self.verified_raw_output_hashes), "receipt_hash": self.receipt_hash}


def execute_stage(*, candidate_id: str, run_id: str, frame_hash: str, stage_id: str,
                  producer: Callable[[dict[str, Any]], dict[str, Any]], raw_input: dict[str, Any],
                  semantic_scope: str, parent_proofs: tuple[str, ...] = ()) -> tuple[dict[str, Any], StageExecutionReceipt]:
    if not candidate_id or not run_id or len(frame_hash) != 64:
        raise ValueError("candidate/run/frame identity required")
    output = producer(raw_input)
    if not isinstance(output, dict) or not output:
        raise ValueError("stage producer must emit concrete raw output")
    receipt = StageExecutionReceipt(
        candidate_id=candidate_id, run_id=run_id, frame_hash=frame_hash, stage_id=stage_id,
        producer_identity=f"{producer.__module__}:{producer.__qualname__}", producer_code_hash=_code_hash(producer),
        raw_input_hashes=(_hash(raw_input),), raw_output_hashes=(_hash(output),),
        execution_depth="executed_stage", semantic_scope=semantic_scope, parent_proofs=parent_proofs,
        execution_status="EXECUTED",
    )
    return output, receipt


def verify_stage(*, execution: StageExecutionReceipt, raw_output: dict[str, Any],
                 verifier: Callable[[dict[str, Any]], bool]) -> StageVerificationReceipt:
    verifier_identity = f"{verifier.__module__}:{verifier.__qualname__}"
    if verifier_identity == execution.producer_identity:
        raise ValueError("producer and verifier must be independently implemented")
    observed_hash = _hash(raw_output)
    result = "PASS" if observed_hash in execution.raw_output_hashes and verifier(raw_output) is True else "FAIL"
    return StageVerificationReceipt(
        execution_receipt_hash=execution.receipt_hash, candidate_id=execution.candidate_id, run_id=execution.run_id,
        frame_hash=execution.frame_hash, verifier_identity=verifier_identity, verifier_code_hash=_code_hash(verifier),
        verified_raw_output_hashes=(observed_hash,), verifier_result=result, freshness="current_run", revoked=False,
        semantic_scope=execution.semantic_scope,
    )


def proof_from_verified_stage(execution: StageExecutionReceipt, verification: StageVerificationReceipt) -> dict[str, Any]:
    if verification.execution_receipt_hash != execution.receipt_hash or verification.verifier_result != "PASS":
        raise ValueError("verified stage execution required")
    if verification.verifier_identity == execution.producer_identity:
        raise ValueError("producer/verifier independence required")
    proof = {
        "candidate_id": execution.candidate_id, "run_id": execution.run_id, "frame_hash": execution.frame_hash,
        "stage_execution_receipt": execution.receipt_hash, "stage_verification_receipt": verification.receipt_hash,
        "raw_output_hashes": list(execution.raw_output_hashes), "producer_code_hash": execution.producer_code_hash,
        "verifier_code_hash": verification.verifier_code_hash, "execution_depth": "executed_and_independently_verified",
        "freshness": verification.freshness, "revoked": verification.revoked, "semantic_scope": execution.semantic_scope,
        "parent_proofs": list(execution.parent_proofs), "status": "PASS",
    }
    proof["proof_hash"] = _hash(proof)
    return proof
