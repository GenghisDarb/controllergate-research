from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from controllergate.evidence.contracts import load_contracts
from controllergate.topology.causal_hypergraph import BoardCellV1, BoardEdgeV1, CellState, connected_regions
from controllergate.topology.probe_compiler_v1 import compile_topology_decision_frame


PRE_TLD_VERSION = "PreTLDDecisionFrameV1"
TLD_JOIN_STATE = "PENDING_PRIVATE_DIRECT_SOURCE_JOIN"
FORBIDDEN_KEYS = {
    "tld_shadow_identities",
    "tld_source_identity",
    "tld_requirement_text",
    "sealed_truth_custody_identity",
    "sealed_truth",
    "final_complete_frame_hash",
    "repair_authority",
    "terminal_authority",
}


def canonical_hash(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    ).hexdigest()


def _json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _cell(row: Mapping[str, Any]) -> BoardCellV1:
    return BoardCellV1(
        row["candidate_id"], row["run_id"], row["frame_id"], row["cell_class"], row["subject"],
        CellState(row["state"]), tuple(row["parent_evidence"]), row["producer_execution_receipt"],
        row["verifier_execution_receipt"], row["semantic_scope"], row["authority_allowed"],
        tuple(row["authority_forbidden"]), row["reopen_condition"],
    )


def _edge(row: Mapping[str, Any]) -> BoardEdgeV1:
    return BoardEdgeV1(
        row["candidate_id"], row["run_id"], row["frame_id"], row["source_cell_id"],
        row["target_cell_id"], row["relation"], tuple(row["parent_evidence"]),
        row["producer_execution_receipt"], row["verifier_execution_receipt"], row["semantic_scope"],
        row["authority_allowed"], tuple(row["authority_forbidden"]), row["reopen_condition"],
    )


def build_pre_tld_frame(
    candidate_dir: str | Path,
    verified_topology_dir: str | Path,
    contracts_path: str | Path,
) -> dict[str, Any]:
    candidate_root = Path(candidate_dir)
    verified_root = Path(verified_topology_dir)
    candidate = _json(candidate_root / "candidate_lane_result_v2.json")
    contracts = [row.record() for row in load_contracts(contracts_path)]
    contract = next(row for row in contracts if row["candidate_id"] == candidate["candidate_id"])
    cells = [_cell(row) for row in _jsonl(verified_root / "board_cell_registry_v1.jsonl")]
    edges = [_edge(row) for row in _jsonl(verified_root / "board_edge_registry_v1.jsonl")]
    regions = connected_regions(candidate["candidate_id"], cells, edges)
    compiled = compile_topology_decision_frame(
        candidate=candidate,
        contract=contract,
        cells=cells,
        edges=edges,
        regions=regions,
        budgets=contract["resource_budget"],
    )
    observation = _json(candidate_root / "neutral_observation_v2.json")
    handoff = verified_root / "environment_exhausted_handoff_v1.json"
    frame: dict[str, Any] = {
        "schema": PRE_TLD_VERSION,
        "candidate_id": candidate["candidate_id"],
        "run_id": candidate["run_id"],
        "frame_id": candidate["frame_id"],
        "candidate_contract_hash": contract["contract_hash"],
        "board_identity": compiled["board_identity"],
        "board_cells": [row.record() for row in cells],
        "board_edges": [row.record() for row in edges],
        "causal_regions": [row.record() for row in regions],
        "boundary_cells": [row.record() for row in cells if row.cell_class == "ENVIRONMENT_BOUNDARY"],
        "environment_exhausted_handoff": _json(handoff) if handoff.is_file() else None,
        "projection_pairs": _jsonl(verified_root / "projection_pairs_v1.jsonl"),
        "modalities": _json(verified_root / "five_modality_reconciliation_v3.json"),
        "hypotheses": compiled["hypotheses"],
        "constraints": compiled["constraints"],
        "legal_probes": compiled["probes"],
        "budgets": contract["resource_budget"],
        "observer_state": observation.get("observer_state"),
        "observer_identity": observation.get("producer_installed_code_hash"),
        "provisional_branch_identity": canonical_hash(
            [candidate["candidate_id"], candidate["run_id"], candidate["frame_id"], "pre-tld-branch"]
        ),
        "tld_join_state": TLD_JOIN_STATE,
        "private_tld_source_access_count": 0,
        "truth_access_count": 0,
        "authority_allowed": "private TLD continuation input",
        "authority_forbidden": [
            "final frame freeze", "terminal", "source ownership", "repair", "count", "release"
        ],
        "producer": "controllergate.topology.pre_tld_frame_v1.build_pre_tld_frame",
        "execution_depth": "verified_topology_and_decision_time_evidence",
        "semantic_scope": "public truth-blind pre-TLD continuation frame",
    }
    frame["pre_tld_frame_hash"] = canonical_hash(frame)
    return frame


def verify_pre_tld_frame(frame: Mapping[str, Any]) -> dict[str, Any]:
    unsigned = {key: value for key, value in frame.items() if key != "pre_tld_frame_hash"}
    forbidden_present = sorted(FORBIDDEN_KEYS.intersection(frame))
    probes = list(frame.get("legal_probes", ()))
    checks = {
        "schema": frame.get("schema") == PRE_TLD_VERSION,
        "hash": frame.get("pre_tld_frame_hash") == canonical_hash(unsigned),
        "join_pending": frame.get("tld_join_state") == TLD_JOIN_STATE,
        "zero_private_source_access": frame.get("private_tld_source_access_count") == 0,
        "zero_truth_access": frame.get("truth_access_count") == 0,
        "legal_probes_present": bool(probes),
        "probe_partitions_preserved": all(len(row.get("predicted_neutral_partitions", {})) >= 2 for row in probes),
        "authority_allowed": frame.get("authority_allowed") == "private TLD continuation input",
        "authority_forbidden": set(frame.get("authority_forbidden", ())) == {
            "final frame freeze", "terminal", "source ownership", "repair", "count", "release"
        },
        "no_forbidden_fields": not forbidden_present,
    }
    status = "PASS" if all(checks.values()) else "BLOCK"
    receipt = {
        "candidate_id": frame.get("candidate_id"),
        "pre_tld_frame_hash": frame.get("pre_tld_frame_hash"),
        "status": status,
        "checks": checks,
        "forbidden_fields_present": forbidden_present,
        "producer": "controllergate.topology.pre_tld_frame_v1.verify_pre_tld_frame",
        "execution_depth": "independent_content_and_authority_verification",
        "semantic_scope": "pre-TLD frame only",
        "authority_allowed": "private TLD continuation input",
        "authority_forbidden": ["terminal", "source ownership", "repair", "count", "release"],
    }
    receipt["verification_receipt"] = canonical_hash(receipt)
    return receipt
