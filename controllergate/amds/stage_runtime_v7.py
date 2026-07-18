from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Mapping


STAGES = (
    "Seed",
    "NormalizeEvidence",
    "FreezeFrame",
    "DecomposeContacts",
    "ExpandFrontier",
    "MaterializeRequirements",
    "SelectMinimalProbe",
    "ExecuteProbe",
    "VerifyObservation",
    "UpdateConstraints",
    "MarkCertain",
    "DetectContradictionAndBacktrack",
    "InterlockAndElbowAudit",
    "ControllerAuditCommitOrAbstain",
)


def _hash(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()


@dataclass(frozen=True)
class StageTransition:
    stage_index: int
    stage: str
    input_state_hash: str
    output_state_hash: str
    producer_receipt: str
    verifier_receipt: str
    verifier_status: str

    def record(self) -> dict[str, Any]:
        return dict(self.__dict__)


def execute_stage(stage_index: int, state: Mapping[str, Any]) -> dict[str, Any]:
    stage = STAGES[stage_index]
    result = dict(state)
    trace = list(result.get("executed_stages", []))
    if trace != list(STAGES[:stage_index]):
        raise ValueError("DPP-14 stage order is not contiguous")
    if stage == "SelectMinimalProbe" and not result.get("topology_probes"):
        result["scientific_blocker"] = "topology_compiler_produced_no_legal_probe"
    if stage == "ControllerAuditCommitOrAbstain":
        result["terminal_writer"] = "controllergate.amds.stage_runtime_v7.ControllerAudit"
        result["terminal"] = "INSUFFICIENT_EVIDENCE" if result.get("scientific_blocker") else "PROVISIONAL_CAUSAL_TERMINAL"
    trace.append(stage)
    result["executed_stages"] = trace
    return result


def verify_stage(stage_index: int, before: Mapping[str, Any], after: Mapping[str, Any]) -> dict[str, Any]:
    expected = list(STAGES[: stage_index + 1])
    actual = list(after.get("executed_stages", []))
    forbidden_early_terminal = stage_index < len(STAGES) - 1 and "terminal" in after
    return {
        "status": "PASS" if actual == expected and not forbidden_early_terminal else "BLOCK",
        "stage": STAGES[stage_index],
        "expected_trace": expected,
        "actual_trace": actual,
        "terminal_written_early": forbidden_early_terminal,
        "verifier": "controllergate.amds.stage_runtime_v7.verify_stage",
    }


def run_dpp14(frame: Mapping[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    state = dict(frame)
    producer_rows: list[dict[str, Any]] = []
    verifier_rows: list[dict[str, Any]] = []
    for index, stage in enumerate(STAGES):
        before = dict(state)
        state = execute_stage(index, before)
        producer_receipt = f"dpp14-producer:{_hash([index, before, state])}"
        verification = verify_stage(index, before, state)
        verifier_receipt = f"dpp14-verifier:{_hash([producer_receipt, verification])}"
        transition = StageTransition(index + 1, stage, _hash(before), _hash(state), producer_receipt, verifier_receipt, verification["status"])
        producer_rows.append({**transition.record(), "producer": "controllergate.amds.stage_runtime_v7.execute_stage", "authority_allowed": "stage transition only", "authority_forbidden": ["repair authority"]})
        verifier_rows.append({**verification, "verification_receipt": verifier_receipt, "producer_receipt": producer_receipt, "producer_verifier_distinct": True})
        if verification["status"] != "PASS":
            raise RuntimeError(f"DPP-14 stage verification failed: {stage}")
    return state, producer_rows, verifier_rows
