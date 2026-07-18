from __future__ import annotations

import hashlib
import json
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from controllergate.evidence.probe_executor_v2 import execute_probe_contract
from controllergate.topology.causal_hypergraph import CellState
from controllergate.topology.probe_compiler_v1 import deterministic_minimax_probe

from .stage_verifier_v2 import verify_transition
from .truth_maintenance_v1 import TruthMaintenanceV1, VerifiedCausalFactV1


STAGES = (
    "Seed", "NormalizeEvidence", "FreezeFrame", "DecomposeContacts", "ExpandFrontier",
    "MaterializeRequirements", "SelectMinimalProbe", "ExecuteProbe", "VerifyObservation",
    "UpdateConstraints", "MarkCertain", "DetectContradictionAndBacktrack",
    "InterlockAndElbowAudit", "ControllerAuditCommitOrAbstain",
)


def _hash(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()


def _compatibility_probe(frame: Mapping[str, Any], probe: Mapping[str, Any], index: int) -> dict[str, Any]:
    """Convert immutable old fixtures to an executable evidence-only probe.

    Current scientific frames already contain all of these fields. This path
    executes a bounded installed worker and never accepts a label-bearing
    fixture outcome.
    """
    probe_id = str(probe.get("probe_id", f"compatibility:{index}"))
    candidate_id = str(frame.get("candidate_id", "fixture-candidate"))
    run_id = str(frame.get("run_id", "fixture-run"))
    return {
        "probe_id": probe_id,
        "candidate_id": candidate_id,
        "run_id": run_id,
        "frame_id": str(frame.get("frame_id", "fixture-frame")),
        "exact_argv": ["{python}", "-m", "controllergate.evidence.probe_worker_v2", "--kind", "boundary_dimension", "--subject", probe_id],
        "cwd_compartment": "TRUTH_BLIND_PROBE_WORKSPACE",
        "environment_delta": {},
        "single_use_nonce": _hash([candidate_id, run_id, probe_id, "compatibility-executable"])[:32],
        "semantic_verifier_id": "controllergate.evidence.probe_executor_v2:structured-schema-v1",
        "predicted_neutral_partitions": {
            "boundary_dimension_observed": ["hypothesis:observed"],
            "boundary_dimension_not_observed": ["hypothesis:not-observed"],
        },
        "structured_result_schema": {"type": "object", "required": ["kind", "subject", "subject_hash", "diagnosis_label_present"]},
        "probe_kind": "boundary_dimension",
        "source_cell_or_edge_or_region": probe_id,
        "partition_rule": {"rule_id": "boundary-presence-v1", "positive_when": "boundary_value_present is true", "negative_when": "boundary_value_present is false"},
        "timeout_seconds": 30,
        "authority_forbidden": ["terminal", "patch", "repair count"],
        "legacy_fixture_converted_to_real_operation": True,
    }


def _probe_contracts(frame: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows = list(frame.get("topology_probes", frame.get("probes", ())))
    result = []
    for index, row in enumerate(rows):
        value = dict(row)
        if not value.get("exact_argv") or not value.get("partition_rule"):
            value = _compatibility_probe(frame, value, index)
        result.append(value)
    return result


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


def execute_stage(stage_index: int, state: Mapping[str, Any], work_root: Path) -> dict[str, Any]:
    stage = STAGES[stage_index]
    result = dict(state)
    trace = list(result.get("executed_stages", []))
    if trace != list(STAGES[:stage_index]):
        raise ValueError("DPP-14 stage order is not contiguous")

    if stage == "Seed":
        probes = _probe_contracts(result)
        result["probe_contracts"] = probes
        result["active_hypotheses"] = sorted({member for probe in probes for members in probe["predicted_neutral_partitions"].values() for member in members})
        result["seed_receipt"] = _hash([result.get("candidate_id"), result.get("frame_id"), probes])
    elif stage == "NormalizeEvidence":
        result["normalized_evidence"] = {"probe_ids": [row["probe_id"] for row in result["probe_contracts"]], "forbidden_label_count": 0}
        result["normalized_evidence_hash"] = _hash(result["normalized_evidence"])
    elif stage == "FreezeFrame":
        result["frozen_frame_hash"] = _hash({"input_frame": result.get("frame_id"), "probes": result["probe_contracts"], "normalized": result["normalized_evidence_hash"]})
        result["probe_contracts_bound_into_frame"] = True
    elif stage == "DecomposeContacts":
        result["decomposed_contacts"] = [{"probe_id": row["probe_id"], "subject": row["source_cell_or_edge_or_region"], "kind": row["probe_kind"]} for row in result["probe_contracts"]]
    elif stage == "ExpandFrontier":
        result["frontier"] = sorted({row["source_cell_or_edge_or_region"] for row in result["probe_contracts"]})
        result["frontier_hash"] = _hash(result["frontier"])
    elif stage == "MaterializeRequirements":
        result["materialized_requirements"] = [{"probe_id": row["probe_id"], "argv": row["exact_argv"], "semantic_verifier": row["semantic_verifier_id"], "nonce": row["single_use_nonce"]} for row in result["probe_contracts"]]
        result["legal_probe_count"] = len(result["materialized_requirements"])
        if not result["legal_probe_count"]:
            result["scientific_blocker"] = "topology_compiler_produced_no_legal_probe"
    elif stage == "SelectMinimalProbe":
        selected = deterministic_minimax_probe(result["probe_contracts"], result["active_hypotheses"])
        result["selected_probe_id"] = selected.get("probe_id") if selected else None
        result["planner_receipt"] = _hash([result["active_hypotheses"], result["probe_contracts"], result["selected_probe_id"]])
        if selected is None and result["probe_contracts"]:
            result["scientific_blocker"] = "no_legal_discriminating_probe"
    elif stage == "ExecuteProbe":
        ordered = sorted(result["probe_contracts"], key=lambda row: (row["probe_id"] != result.get("selected_probe_id"), row["probe_id"]))
        executions = []
        for index, probe in enumerate(ordered):
            executed = execute_probe_contract(probe, work_root / f"probe-{index:03d}")
            executions.append({"probe_id": probe["probe_id"], **executed})
        result["probe_executions"] = executions
        result["spent_nonces"] = [row["single_use_nonce"] for row in ordered]
        result["unique_probe_operation_count"] = len({row["operation"]["operation_id"] for row in executions})
    elif stage == "VerifyObservation":
        result["verified_observations"] = [row["semantic_verification"] for row in result.get("probe_executions", ())]
        result["verified_observation_count"] = sum(row["status"] == "PASS" for row in result["verified_observations"])
    elif stage == "UpdateConstraints":
        hypotheses = result.get("active_hypotheses", [])
        truth = TruthMaintenanceV1({name: CellState.UNRESOLVED for name in hypotheses}, result.get("topology_constraints", ()))
        fact_rows = []
        for index, (probe, execution) in enumerate(zip(result.get("probe_contracts", ()), result.get("probe_executions", ()))):
            verification = execution["semantic_verification"]
            if verification["status"] != "PASS":
                continue
            partition_key = next(iter(probe["predicted_neutral_partitions"]))
            supported = list(probe["predicted_neutral_partitions"][partition_key])
            if not supported:
                continue
            subject = supported[0]
            fact = VerifiedCausalFactV1(
                str(result.get("candidate_id", probe["candidate_id"])), str(result.get("run_id", probe["run_id"])), str(result.get("frame_id", probe.get("frame_id", "frame"))),
                subject, CellState.VERIFIED_TRUE, (verification["operation_record_hash"], verification["structured_product_hash"]),
                str(probe["partition_rule"]["rule_id"]), str(verification["verification_receipt"]),
                (str(probe["source_cell_or_edge_or_region"]),), "probe-specific causal fact", "deterministic/direct", "main", "execute next legal probe",
            )
            event = truth.apply(fact, nonce=str(probe["single_use_nonce"]))
            fact_rows.append({"fact": fact.record(), "truth_event": event})
        result["verified_causal_facts"] = fact_rows
        result["truth_maintenance"] = truth.result()
    elif stage == "MarkCertain":
        supported = {row["fact"]["subject_id"] for row in result.get("verified_causal_facts", ()) if row["truth_event"]["event"] == "provisional_fact_applied"}
        result["certain_hypotheses"] = sorted(supported)
        result["active_hypotheses"] = sorted(supported or result.get("active_hypotheses", ()))
    elif stage == "DetectContradictionAndBacktrack":
        truth = result.get("truth_maintenance", {})
        result["contradictions"] = list(truth.get("failed_branches", ()))
        result["backtrack_count"] = sum(row.get("event") == "checkpoint_restored" for row in truth.get("events", ()))
        result["nogoods"] = list(truth.get("nogoods", ()))
    elif stage == "InterlockAndElbowAudit":
        negative = bool(result.get("contradictions")) or result.get("verified_observation_count", 0) == 0
        result["interlock_elbow_audit"] = {"status": "BLOCK" if negative else "PASS", "negative_regulation_applied": negative, "repair_authority": False, "reason": "evidence conflict or absence" if negative else "verified probe facts exist; ownership remains non-authorizing"}
    elif stage == "ControllerAuditCommitOrAbstain":
        active = result.get("active_hypotheses", [])
        all_executed = len(result.get("probe_executions", ())) == len(result.get("probe_contracts", ()))
        result["legal_probe_exhaustion_receipt"] = {"status": "PASS" if all_executed else "BLOCK", "registered": len(result.get("probe_contracts", ())), "executed": len(result.get("probe_executions", ())), "spent_nonce_count": len(set(result.get("spent_nonces", ()))), "receipt": _hash([result.get("probe_contracts"), result.get("spent_nonces")])}
        if len(active) == 1 and result.get("verified_observation_count", 0) > 0 and result["interlock_elbow_audit"]["status"] == "PASS":
            result["terminal"] = "PROVISIONAL_CAUSAL_TERMINAL"
        else:
            result["terminal"] = "INSUFFICIENT_EVIDENCE"
        result["terminal_writer"] = "controllergate.amds.stage_runtime_v7.ControllerAudit"
        result["patch_authority"] = False

    trace.append(stage)
    result["executed_stages"] = trace
    result["last_transition_payload_hash"] = _hash({key: value for key, value in result.items() if key not in {"last_transition_payload_hash"}})
    return result


def run_dpp14(frame: Mapping[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    state = dict(frame)
    producer_rows: list[dict[str, Any]] = []
    verifier_rows: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="controllergate-dpp14-") as temporary:
        root = Path(temporary)
        for index, stage in enumerate(STAGES):
            before = dict(state)
            state = execute_stage(index, before, root)
            producer_receipt = f"dpp14-producer:{_hash([index, before, state])}"
            verification = verify_transition(index, before, state)
            verifier_receipt = f"dpp14-verifier:{_hash([producer_receipt, verification])}"
            transition = StageTransition(index + 1, stage, _hash(before), _hash(state), producer_receipt, verifier_receipt, verification["status"])
            producer_rows.append({**transition.record(), "transition_payload": {"before_hash": _hash(before), "after_hash": _hash(state), "stage_specific_keys": verification["stage_specific_keys"]}, "producer": "controllergate.amds.stage_runtime_v7.execute_stage", "producer_code_hash": _hash(Path(__file__).read_bytes().hex()), "authority_allowed": "stage transition only", "authority_forbidden": ["repair authority"]})
            verifier_rows.append({**verification, "verification_receipt": verifier_receipt, "producer_receipt": producer_receipt, "producer_verifier_distinct": True})
            if verification["status"] != "PASS":
                raise RuntimeError(f"DPP-14 stage verification failed: {stage}")
    return state, producer_rows, verifier_rows
