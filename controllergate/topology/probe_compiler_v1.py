from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Iterable, Mapping

from .causal_hypergraph import BoardCellV1, BoardEdgeV1, CausalRegionV1, CellState


def identity(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()


@dataclass(frozen=True)
class CausalHypothesisV1:
    hypothesis_id: str
    candidate_id: str
    ownership_cell_id: str
    derived_from: tuple[str, ...]
    competing_cell_ids: tuple[str, ...]
    authority: str = "provisional_non_authorizing"


@dataclass(frozen=True)
class CausalConstraintV1:
    constraint_id: str
    candidate_id: str
    relation: str
    subject_ids: tuple[str, ...]
    derived_from: tuple[str, ...]


@dataclass(frozen=True)
class MinimalProbeV1:
    probe_id: str
    candidate_id: str
    run_id: str
    frame_id: str
    source_cell_or_edge_or_region: str
    exact_argv: tuple[str, ...]
    installed_operation_id: str
    cwd_compartment: str
    environment_delta: Mapping[str, str]
    counterfactual_pair_id: str | None
    predicted_neutral_partitions: Mapping[str, tuple[str, ...]]
    semantic_verifier_id: str
    required_raw_outputs: tuple[str, ...]
    budgets: Mapping[str, int]
    timeout_seconds: int
    single_use_nonce: str
    controls: Mapping[str, tuple[str, ...]]
    forbidden_outputs: tuple[str, ...]
    reopen_condition: str
    probe_kind: str
    structured_result_schema: Mapping[str, Any]
    partition_rule: Mapping[str, Any]


def _probe_for(
    cell: BoardCellV1,
    contract: Mapping[str, Any],
    competing: list[BoardCellV1],
    budgets: Mapping[str, int],
    hypothesis_by_cell: Mapping[str, str],
) -> MinimalProbeV1:
    class_to_kind = {
        "OWNERSHIP_SOURCE": "contact_edge",
        "OWNERSHIP_PROVIDER": "provider_variation",
        "OWNERSHIP_ENVIRONMENT_PLATFORM": "boundary_dimension",
        "OWNERSHIP_RUNNER": "runner_variation",
        "OWNERSHIP_HARNESS_FIXTURE": "harness_variation",
        "OWNERSHIP_SERVICE_TRANSPORT": "service_variation",
        "OWNERSHIP_TEST_EXPECTATION": "expectation_relation",
        "OWNERSHIP_MIXED": "modality_conflict",
    }
    kind = class_to_kind.get(cell.cell_class, "recovery_region")
    subject = f"{cell.cell_class}|{cell.subject}|{cell.cell_id}"
    argv = (
        "{python}", "-m", "controllergate.evidence.probe_worker_v2",
        "--kind", kind, "--subject", subject,
    )
    positive_code = f"{kind}_observed"
    negative_code = f"{kind}_not_observed"
    partitions = {
        positive_code: (hypothesis_by_cell[cell.cell_id],),
        negative_code: tuple(sorted(hypothesis_by_cell[row.cell_id] for row in competing if row.cell_id != cell.cell_id)),
    }
    if not all(partitions.values()):
        partitions["insufficient_evidence"] = tuple(sorted(hypothesis_by_cell[row.cell_id] for row in competing))
    source = cell.cell_id
    return MinimalProbeV1(
        probe_id=f"probe:{identity([cell.candidate_id, source, argv, partitions])}", candidate_id=cell.candidate_id, run_id=cell.run_id, frame_id=cell.frame_id,
        source_cell_or_edge_or_region=source, exact_argv=argv, installed_operation_id="controllergate evidence execute-probe",
        cwd_compartment=str(contract.get("target_working_compartment", "EXECUTION_WORKSPACE")), environment_delta=dict(contract.get("target_environment", {})),
        counterfactual_pair_id=None, predicted_neutral_partitions=partitions, semantic_verifier_id=str(contract["verifier_id"]),
        required_raw_outputs=("process_observation", "typed_product", "semantic_verification"), budgets=dict(budgets), timeout_seconds=int(budgets.get("timeout_seconds", 300)),
        single_use_nonce=identity([cell.candidate_id, source, "single-use"])[:32],
        controls={"positive": tuple(row["control_id"] for row in contract.get("positive_controls", ())), "negative": tuple(row["control_id"] for row in contract.get("negative_controls", ())), "adversarial": tuple(row["control_id"] for row in contract.get("adversarial_controls", ()))},
        forbidden_outputs=("terminal_class", "source_owned", "repair_patch", "future_outcome", "diagnosis"), reopen_condition=cell.reopen_condition,
        probe_kind=kind,
        structured_result_schema={"type": "object", "required": ("kind", "subject", "subject_hash", "diagnosis_label_present")},
        partition_rule={"rule_id": f"{kind}-semantic-v1", "positive_when": "kind-specific structured predicate is true", "negative_when": "predicate is false", "subject": subject},
    )


def compile_topology_decision_frame(
    *, candidate: Mapping[str, Any], contract: Mapping[str, Any], cells: Iterable[BoardCellV1], edges: Iterable[BoardEdgeV1], regions: Iterable[CausalRegionV1], budgets: Mapping[str, int]
) -> dict[str, Any]:
    """Derive decisive content only from graph objects; no caller decisive lists exist."""
    cell_rows = list(cells); edge_rows = list(edges); region_rows = list(regions)
    ownership = [row for row in cell_rows if row.cell_class.startswith("OWNERSHIP_") and row.parent_evidence]
    if not ownership:
        contacts = [row for row in cell_rows if row.cell_class.endswith("CONTACT") and row.parent_evidence]
        ownership = contacts
    hypotheses = [CausalHypothesisV1(f"hypothesis:{identity([row.cell_id, row.parent_evidence])}", row.candidate_id, row.cell_id, tuple(row.parent_evidence), tuple(sorted(other.cell_id for other in ownership if other.cell_id != row.cell_id))) for row in ownership]
    hypothesis_by_cell = {row.ownership_cell_id: row.hypothesis_id for row in hypotheses}
    constraints = []
    for edge in edge_rows:
        if edge.relation in {"MUTUALLY_EXCLUSIVE", "CO_DEPENDENT", "CONTRADICTS", "REQUIRES"}:
            constraints.append(CausalConstraintV1(f"constraint:{identity(edge.record())}", edge.candidate_id, edge.relation, (edge.source_cell_id, edge.target_cell_id), tuple(edge.parent_evidence)))
    unresolved = [row for row in ownership if row.state in {CellState.UNRESOLVED, CellState.CONTRADICTED}]
    probes = [_probe_for(row, contract, ownership, budgets, hypothesis_by_cell) for row in unresolved]
    return {
        "candidate_id": candidate["candidate_id"], "run_id": candidate["run_id"], "frame_id": candidate["frame_id"],
        "board_identity": identity({"cells": [row.record() for row in cell_rows], "edges": [row.record() for row in edge_rows], "regions": [row.record() for row in region_rows]}),
        "hypotheses": [asdict(row) for row in hypotheses], "constraints": [asdict(row) for row in constraints], "probes": [asdict(row) for row in probes],
        "compiler": "controllergate.topology.probe_compiler_v1.compile_topology_decision_frame", "caller_supplied_decisive_input_count": 0,
        "empty_derivation_hypothesis_count": sum(not row.derived_from for row in hypotheses), "non_executable_probe_count": sum(not (row.exact_argv or row.installed_operation_id) for row in probes),
        "partitionless_probe_count": sum(len(row.predicted_neutral_partitions) < 2 for row in probes), "authority_allowed": "truth-blind probe planning", "authority_forbidden": ["terminal truth", "repair authority"],
    }


def deterministic_minimax_probe(probes: Iterable[Mapping[str, Any]], active_hypotheses: Iterable[str], spent: Iterable[str] = ()) -> Mapping[str, Any] | None:
    active = set(active_hypotheses); spent_ids = set(spent); scored = []
    for probe in probes:
        if probe["probe_id"] in spent_ids: continue
        partitions = probe["predicted_neutral_partitions"]
        sizes = [len(active.intersection(values)) for values in partitions.values()]
        if len([size for size in sizes if size]) < 2: continue
        score = (max(sizes), int(probe.get("timeout_seconds", 0)), probe["probe_id"])
        scored.append((score, probe))
    return min(scored, default=(None, None), key=lambda row: row[0])[1]


def probe_stagnation_control(executed_probe_ids: Iterable[str], discrimination: Iterable[bool], *, threshold: int) -> dict[str, Any]:
    if threshold < 2: raise ValueError("stagnation threshold must be justified and at least two")
    probes = list(executed_probe_ids); outcomes = list(discrimination); trailing = 0
    for value in reversed(outcomes):
        if value: break
        trailing += 1
    repeated = len(probes) != len(set(probes))
    triggered = repeated or trailing >= threshold
    return {"status": "TRIGGERED" if triggered else "CLEAR", "threshold": threshold, "threshold_basis": "preregistered bounded two-probe no-discrimination control", "repeated_probe": repeated, "trailing_nondiscriminating": trailing, "next_action": "compile_one_legal_cross_region_counterfactual" if triggered else "continue_registered_minimax", "authority_forbidden": ["terminal writing", "repair authority"]}
