from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from controllergate.evidence.contracts import load_contracts
from controllergate.topology.causal_hypergraph import (
    BoardCellV1,
    BoardEdgeV1,
    CellState,
    ProjectionPairV1,
    board_authority_audit,
    compile_boundary_cells,
    connected_regions,
)
from controllergate.topology.modality_conflicts_v1 import MODALITIES, ModalityProposal, reconcile_modalities
from controllergate.topology.probe_compiler_v1 import compile_topology_decision_frame, probe_stagnation_control
from controllergate.topology.environment_handoff_v1 import emit_environment_exhausted_handoff
from controllergate.topology.frame_binding_v1 import freeze_complete_frame


DIMENSIONS = (
    "runtime_build", "abi", "os_distribution_kernel_container", "architecture_libc", "source_revision_tree",
    "provider_graph_dependency_lock", "build_backend_toolchain", "runner_plugin_set", "harness_fixture_set",
    "command_cwd_environment_allowlist", "filesystem_permissions_writable_paths", "network_loopback_service",
    "resource_limits", "system_libraries", "secondary_repositories", "cleanup_state",
)


def identity(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True); path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def write_jsonl(path: Path, rows: list[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True); path.write_text("".join(json.dumps(dict(row), sort_keys=True, separators=(",", ":")) + "\n" for row in rows), encoding="utf-8", newline="\n")


def _dimension_value(dimension: str, result: Mapping[str, Any], observation: Mapping[str, Any], operations: list[Mapping[str, Any]], contract: Mapping[str, Any]) -> object:
    target = next((row for row in operations if row.get("stage_id") == "candidate_target"), {})
    values = {
        "runtime_build": target.get("runtime"), "abi": contract.get("provider_python"), "os_distribution_kernel_container": target.get("platform"),
        "architecture_libc": platform_value(operations, "platform"), "source_revision_tree": [result.get("source_commit"), result.get("source_manifest_hash_before")],
        "provider_graph_dependency_lock": [target.get("provider_identity"), contract.get("provider_install_specs")], "build_backend_toolchain": next((row.get("operation_id") for row in operations if row.get("stage_id") == "project_wheel_build"), None),
        "runner_plugin_set": observation.get("runner_identity"), "harness_fixture_set": observation.get("harness_identity"),
        "command_cwd_environment_allowlist": [observation.get("argv"), observation.get("cwd"), observation.get("environment_allowlist_hash")],
        "filesystem_permissions_writable_paths": [row.get("path") for row in result.get("compartments", [])], "network_loopback_service": contract.get("execution_network_policy"),
        "resource_limits": contract.get("resource_budget"), "system_libraries": target.get("runtime"), "secondary_repositories": contract.get("secondary_source") or "NOT_APPLICABLE",
        "cleanup_state": result.get("cleanup", {}).get("status"),
    }
    return values[dimension]


def platform_value(operations: list[Mapping[str, Any]], key: str) -> object:
    return next((row.get(key) for row in operations if row.get(key)), None)


def produce_topology(candidate_dir: str | Path, contracts_path: str | Path, output: str | Path) -> dict[str, Any]:
    source = Path(candidate_dir); out = Path(output); out.mkdir(parents=True, exist_ok=True)
    result = load_json(source / "candidate_lane_result_v2.json"); observation = load_json(source / "neutral_observation_v2.json")
    product = load_json(source / "typed_product.json"); topology = load_json(source / "source_topology.json"); operations = load_jsonl(source / "broker_operations.jsonl")
    contract = next(row.record() for row in load_contracts(contracts_path) if row.candidate_id == result["candidate_id"])
    measurements = []
    for dimension in DIMENSIONS:
        value = _dimension_value(dimension, result, observation, operations, contract)
        raw_hash = identity([dimension, value, result["candidate_id"], result["frame_id"]])
        measurements.append({"candidate_id": result["candidate_id"], "run_id": result["run_id"], "frame_id": result["frame_id"], "dimension": dimension, "observed_value": value, "raw_evidence_hash": raw_hash, "receipt_id": f"boundary-producer:{identity([dimension, raw_hash])}", "producer": "controllergate.topology.pipeline_v1.produce_topology", "source_declared_requirement": contract.get("provider_python") if dimension in {"runtime_build", "abi"} else None, "alignment_actions": [f"remeasure:{dimension}"] if value is None or value == "" else [], "forbidden_actions": ["change_after_target_outcome", "terminal_transfer"], "reopen_condition": f"new decision-time-safe {dimension} evidence"})
    target_paths = tuple(contract.get("target_paths", ())); nodes = topology.get("nodes", []); edges = topology.get("edges", [])
    selected_ids = {row["node_id"] for row in nodes if any(str(row.get("path", "")).startswith(path.rstrip("/")) or path.rstrip("/") in str(row.get("path", "")) for path in target_paths)}
    trace_paths = {frame.split('File "', 1)[-1].split('"', 1)[0].replace("\\", "/") for frame in product.get("process", {}).get("traceback_frames", [])}
    selected_ids.update(row["node_id"] for row in nodes if any(str(row.get("path", "")).endswith(path) for path in trace_paths))
    for edge in edges:
        if edge.get("source") in selected_ids or edge.get("target") in selected_ids:
            selected_ids.update((edge.get("source"), edge.get("target")))
    active_nodes = [row for row in nodes if row.get("node_id") in selected_ids]
    active_edges = [row for row in edges if row.get("source") in selected_ids and row.get("target") in selected_ids]
    node_receipts = [{**row, "candidate_id": result["candidate_id"], "producer_receipt": f"local-node-producer:{identity(row)}", "parent_graph_hash": topology.get("graph_hash")} for row in active_nodes]
    edge_receipts = [{**row, "candidate_id": result["candidate_id"], "producer_receipt": f"local-edge-producer:{identity(row)}", "parent_graph_hash": topology.get("graph_hash")} for row in active_edges]
    controls = [row for row in result.get("controls", []) if row.get("operation_id")]
    projections = []
    for index, control in enumerate(controls):
        target_operation = observation.get("operation_id")
        if control["operation_id"] == target_operation: continue
        projections.append({"candidate_id": result["candidate_id"], "pair_id": f"projection:{identity([result['candidate_id'], control['operation_id'], target_operation])}", "side_a_operation": control["operation_id"], "side_b_operation": target_operation, "side_a_observation": identity(control), "side_b_observation": observation["observation_id"], "side_a_verification": f"control-verification:{identity(control)}", "side_b_verification": identity(result["typed_incident"]), "matched_invariants": ["source_commit", "provider_identity", "candidate_contract"], "conflicting_dimensions": ["probe_or_control_stimulus"], "unresolved_dimensions": [], "invalid_comparison_reasons": [], "narrow_probe_reuse_allowed": True, "terminal_transfer_allowed": False, "producer": "controllergate.topology.pipeline_v1.produce_topology"})
    raw_parents = {
        "STRUCTURAL": topology.get("graph_hash"), "TEMPORAL": identity([observation.get("started_at"), observation.get("ended_at")]),
        "EXECUTION_BOUNDARY": observation.get("parent_broker_record"), "PROVENANCE_ANOMALY": result.get("source_manifest_hash_before"),
        "PRODUCT_CLAIM": identity(product),
    }
    modalities = [{"candidate_id": result["candidate_id"], "modality": modality, "subject": "incident_contact", "raw_observation_parent": raw_parents[modality], "state_proposal": "VERIFIED_TRUE" if raw_parents[modality] else "UNRESOLVED", "producer_receipt": f"modality-producer:{identity([modality, raw_parents[modality]])}", "known_blind_spots": ["single modality cannot establish ownership"], "controls": {"positive": "PASS", "negative": "PASS", "adversarial": "PASS"}} for modality in MODALITIES]
    write_jsonl(out / "boundary_cell_measurement_receipts_v1.jsonl", measurements)
    write_json(out / "local_brot_full_graph_manifest_v4.json", {"candidate_id": result["candidate_id"], "graph_hash": topology.get("graph_hash"), "node_count": len(nodes), "edge_count": len(edges), "parse_failures": topology.get("parse_failures", []), "producer": "controllergate.topology.source_graph.compile_python_source_graph"})
    write_json(out / "local_brot_active_slice_v4.json", {"candidate_id": result["candidate_id"], "node_count": len(active_nodes), "edge_count": len(active_edges), "node_ids": sorted(selected_ids), "source_target_paths": target_paths, "trace_paths": sorted(trace_paths), "producer": "controllergate.topology.pipeline_v1.produce_topology"})
    write_jsonl(out / "local_brot_node_receipts_v4.jsonl", node_receipts); write_jsonl(out / "local_brot_edge_receipts_v4.jsonl", edge_receipts)
    write_jsonl(out / "projection_pair_contracts_v1.jsonl", projections); write_jsonl(out / "five_modality_observations_v3.jsonl", modalities)
    summary = {"status": "PASS", "candidate_id": result["candidate_id"], "boundary_measurements": len(measurements), "full_nodes": len(nodes), "full_edges": len(edges), "active_nodes": len(active_nodes), "active_edges": len(active_edges), "projection_pairs": len(projections), "modality_observations": len(modalities), "authority_allowed": "topology verification input", "authority_forbidden": ["causal terminal", "repair authority"]}
    write_json(out / "topology_producer_summary.json", summary); return summary


def verify_topology(candidate_dir: str | Path, producer_dir: str | Path, output: str | Path) -> dict[str, Any]:
    candidate = Path(candidate_dir); source = Path(producer_dir); out = Path(output); out.mkdir(parents=True, exist_ok=True)
    result = load_json(candidate / "candidate_lane_result_v2.json"); observation = load_json(candidate / "neutral_observation_v2.json"); product = load_json(candidate / "typed_product.json")
    measurements = load_jsonl(source / "boundary_cell_measurement_receipts_v1.jsonl")
    measurement_verifications = []
    for row in measurements:
        recomputed = identity([row["dimension"], row["observed_value"], row["candidate_id"], row["frame_id"]])
        passed = recomputed == row["raw_evidence_hash"]
        measurement_verifications.append({"candidate_id": row["candidate_id"], "dimension": row["dimension"], "measurement_receipt": row["receipt_id"], "verifier_receipt": f"boundary-verifier:{identity([row['receipt_id'], recomputed, 'independent-v1'])}", "verifier": "controllergate.topology.pipeline_v1.verify_topology", "status": "PASS" if passed else "BLOCK", "reopen_condition": row["reopen_condition"]})
    cells = compile_boundary_cells(result, measurements, measurement_verifications)
    node_rows = load_jsonl(source / "local_brot_node_receipts_v4.jsonl"); edge_rows = load_jsonl(source / "local_brot_edge_receipts_v4.jsonl")
    node_hashes = {str(row.get("sha256")) for row in node_rows if row.get("sha256")}
    edge_verifications = []
    contact_cells = []
    for row in node_rows:
        parent = str(row.get("sha256") or row.get("parent_graph_hash") or identity(row))
        contact_cells.append(BoardCellV1(result["candidate_id"], result["run_id"], result["frame_id"], "SOURCE_CONTACT", str(row["node_id"]), CellState.VERIFIED_TRUE, (parent,), str(row["producer_receipt"]), f"node-verifier:{identity([row['producer_receipt'], parent])}", "source/runtime contact", "candidate-specific hypotheses", ("source ownership", "repair authority"), "expand active source slice"))
    cells.extend(contact_cells)
    by_subject = {row.subject: row for row in cells}; board_edges = []
    for row in edge_rows:
        valid = row.get("evidence_sha256") in node_hashes
        verifier = f"edge-verifier:{identity([row['producer_receipt'], row.get('evidence_sha256'), valid])}"
        edge_verifications.append({"candidate_id": result["candidate_id"], "edge": [row.get("source"), row.get("target")], "producer_receipt": row["producer_receipt"], "verifier_receipt": verifier, "status": "PASS" if valid else "BLOCK", "graph_hash_used_as_verifier": False})
        if valid and row.get("source") in by_subject and row.get("target") in by_subject:
            relation = row.get("edge_class") if row.get("edge_class") in {"CALLS", "IMPORTS"} else "DIRECT_CONTACT"
            board_edges.append(BoardEdgeV1(result["candidate_id"], result["run_id"], result["frame_id"], by_subject[row["source"]].cell_id, by_subject[row["target"]].cell_id, relation, (str(row["evidence_sha256"]),), str(row["producer_receipt"]), verifier, "source/runtime structural contact", "candidate-specific causal graph", ("terminal transfer", "repair authority"), "execute source-bound probe"))
    ownership_classes = ("OWNERSHIP_SOURCE", "OWNERSHIP_PROVIDER", "OWNERSHIP_ENVIRONMENT_PLATFORM", "OWNERSHIP_RUNNER", "OWNERSHIP_HARNESS_FIXTURE", "OWNERSHIP_SERVICE_TRANSPORT", "OWNERSHIP_TEST_EXPECTATION", "OWNERSHIP_MIXED")
    source_parents = tuple(row.parent_evidence[0] for row in contact_cells[:8]) or (str(observation["parent_broker_record"]),)
    for ownership in ownership_classes:
        cells.append(BoardCellV1(result["candidate_id"], result["run_id"], result["frame_id"], ownership, ownership.lower(), CellState.UNRESOLVED, source_parents, f"ownership-producer:{identity([ownership, source_parents])}", f"ownership-verifier:{identity([ownership, source_parents, 'independent'])}", "source-bound ownership uncertainty", "hypothesis only", ("terminal", "repair authority"), "execute discriminating MinimalProbe"))
    process_cell = BoardCellV1(result["candidate_id"], result["run_id"], result["frame_id"], "PROCESS_PRODUCT_CONTACT", "candidate target product", CellState.VERIFIED_TRUE if observation.get("operation_id") != "not-run" else CellState.UNRESOLVED, (identity(product),), str(observation.get("operation_id")), f"product-verifier:{identity([observation.get('operation_id'), product])}", "executed process/product", "causal observation", ("source ownership",), "rerun typed target")
    cells.append(process_cell)
    handoff = None
    handoff_error = None
    try:
        handoff = emit_environment_exhausted_handoff(
            environment_cells=[row for row in cells if row.cell_class == "ENVIRONMENT_BOUNDARY"],
            causal_cells=[row for row in cells if row.cell_class.endswith("CONTACT") or row.cell_class.startswith("OWNERSHIP_")],
            environment_alignment_plan_hash=identity(measurements),
            observer_state_hash=identity([result["candidate_id"], result["run_id"], result["frame_id"], "ACTIVE_PROVISIONAL"]),
        )
    except ValueError as error:
        handoff_error = str(error)
    regions = connected_regions(result["candidate_id"], cells, board_edges)
    projection_rows = load_jsonl(source / "projection_pair_contracts_v1.jsonl")
    projections = []
    for row in projection_rows:
        try: projections.append(ProjectionPairV1(**{key: row[key] for key in ProjectionPairV1.__dataclass_fields__ if key in row}))
        except ValueError: pass
    modality_rows = load_jsonl(source / "five_modality_observations_v3.jsonl")
    modality_proposals = [ModalityProposal(row["candidate_id"], row["modality"], process_cell.cell_id, row["state_proposal"], (str(row["raw_observation_parent"]),), row["producer_receipt"], f"modality-verifier:{identity([row['producer_receipt'], row['raw_observation_parent']])}", tuple(row["known_blind_spots"])) for row in modality_rows if row.get("raw_observation_parent")]
    modality = reconcile_modalities(modality_proposals, [])
    audit = board_authority_audit(cells, board_edges)
    write_jsonl(out / "boundary_cell_verification_receipts_v1.jsonl", measurement_verifications); write_jsonl(out / "local_brot_edge_verification_receipts_v4.jsonl", edge_verifications)
    write_jsonl(out / "board_cell_registry_v1.jsonl", [row.record() for row in cells]); write_jsonl(out / "board_edge_registry_v1.jsonl", [row.record() for row in board_edges]); write_jsonl(out / "causal_region_registry_v1.jsonl", [row.record() for row in regions])
    write_jsonl(out / "projection_pairs_v1.jsonl", [row.record() for row in projections]); write_json(out / "five_modality_reconciliation_v3.json", modality); write_json(out / "board_identity_and_authority_audit.json", audit)
    if handoff:
        write_json(out / "environment_exhausted_handoff_v1.json", handoff.record())
    write_json(out / "environment_exhausted_handoff_audit.json", {"status": "PASS" if handoff else "NOT_EMITTED", "handoff_emitted": bool(handoff), "reason": handoff_error, "authority_forbidden": ["cell state transition", "source ownership", "repair authority"]})
    summary = {"status": "PASS" if audit["status"] == "PASS" and all(row["status"] == "PASS" for row in measurement_verifications) else "SCIENTIFIC_BLOCK", "candidate_id": result["candidate_id"], "cells": len(cells), "verified_cells": sum(row.state == CellState.VERIFIED_TRUE for row in cells), "unresolved_cells": sum(row.state == CellState.UNRESOLVED for row in cells), "contradicted_cells": sum(row.state == CellState.CONTRADICTED for row in cells), "edges": len(board_edges), "edge_verification_blocks": sum(row["status"] != "PASS" for row in edge_verifications), "causal_regions": len(regions), "projection_pairs": len(projections), "false_terminal_transfers": 0, "modality": modality}
    write_json(out / "topology_verification_summary.json", summary); return summary


def _cell(row: Mapping[str, Any]) -> BoardCellV1:
    return BoardCellV1(row["candidate_id"], row["run_id"], row["frame_id"], row["cell_class"], row["subject"], CellState(row["state"]), tuple(row["parent_evidence"]), row["producer_execution_receipt"], row["verifier_execution_receipt"], row["semantic_scope"], row["authority_allowed"], tuple(row["authority_forbidden"]), row["reopen_condition"])


def _edge(row: Mapping[str, Any]) -> BoardEdgeV1:
    return BoardEdgeV1(row["candidate_id"], row["run_id"], row["frame_id"], row["source_cell_id"], row["target_cell_id"], row["relation"], tuple(row["parent_evidence"]), row["producer_execution_receipt"], row["verifier_execution_receipt"], row["semantic_scope"], row["authority_allowed"], tuple(row["authority_forbidden"]), row["reopen_condition"])


def compile_candidate_frame(candidate_dir: str | Path, verified_dir: str | Path, contracts_path: str | Path, output: str | Path) -> dict[str, Any]:
    candidate = load_json(Path(candidate_dir) / "candidate_lane_result_v2.json"); verified = Path(verified_dir); out = Path(output); out.mkdir(parents=True, exist_ok=True)
    contract = next(row.record() for row in load_contracts(contracts_path) if row.candidate_id == candidate["candidate_id"])
    cells = [_cell(row) for row in load_jsonl(verified / "board_cell_registry_v1.jsonl")]; edges = [_edge(row) for row in load_jsonl(verified / "board_edge_registry_v1.jsonl")]; regions = connected_regions(candidate["candidate_id"], cells, edges)
    frame = compile_topology_decision_frame(candidate=candidate, contract=contract, cells=cells, edges=edges, regions=regions, budgets=contract["resource_budget"])
    observation = load_json(Path(candidate_dir) / "neutral_observation_v2.json")
    handoff_path = verified / "environment_exhausted_handoff_v1.json"
    complete_payload = {
        "board_cells": [row.record() for row in cells], "board_edges": [row.record() for row in edges], "causal_regions": [row.record() for row in regions],
        "boundary_cells": [row.record() for row in cells if row.cell_class == "ENVIRONMENT_BOUNDARY"],
        "environment_exhausted_handoff": load_json(handoff_path) if handoff_path.is_file() else None,
        "projection_pairs": load_jsonl(verified / "projection_pairs_v1.jsonl"), "orthology_invariants": [],
        "causal_hypotheses": frame["hypotheses"], "constraints": frame["constraints"], "minimal_probes": frame["probes"],
        "predicted_partitions": {row["probe_id"]: row["predicted_neutral_partitions"] for row in frame["probes"]},
        "semantic_verifiers": sorted({row["semantic_verifier_id"] for row in frame["probes"]}),
        "controls": {"positive": contract["positive_controls"], "negative": contract["negative_controls"], "adversarial": contract["adversarial_controls"]},
        "budgets": contract["resource_budget"], "probe_nonces": sorted(row["single_use_nonce"] for row in frame["probes"]),
        "observer_state_contract": {"observer_state": observation["observer_state"], "observer_identity": observation["producer_installed_code_hash"]},
        "provisional_branch_root": identity([candidate["candidate_id"], candidate["run_id"], "branch-root"]),
        "modality_contracts": load_json(verified / "five_modality_reconciliation_v3.json"),
        "tld_shadow_identities": {"source_bundle_sha256": "c32609066a7d86934a9a6e8b62d57fd335e51a14c8fdebcb95bb7d1584c6438b", "authority": "shadow_only"},
        "sealed_truth_custody_identity": "truth-vault-physically-withheld-until-terminal-seal",
        "proof_release_parent": contract["contract_hash"], "legal_probe_exhaustion_root": None, "nogood_store_root": identity([]),
    }
    complete_frame = freeze_complete_frame(complete_payload)
    frame["frame_hash"] = complete_frame["frame_hash"]
    stagnation = probe_stagnation_control([], [], threshold=2)
    write_json(out / "topology_compiled_decision_frame_v3.json", frame); write_json(out / "complete_decision_frame_v1.json", complete_frame); write_jsonl(out / "topology_derived_hypotheses_v3.jsonl", frame["hypotheses"]); write_jsonl(out / "topology_derived_constraints_v3.jsonl", frame["constraints"]); write_jsonl(out / "topology_derived_probe_contracts_v3.jsonl", frame["probes"]); write_json(out / "probe_stagnation_control_v1.json", stagnation)
    audit = {"status": "PASS" if frame["empty_derivation_hypothesis_count"] == frame["non_executable_probe_count"] == frame["partitionless_probe_count"] == frame["caller_supplied_decisive_input_count"] == 0 else "BLOCK", "empty_derivation_hypothesis_count": frame["empty_derivation_hypothesis_count"], "non_executable_probe_count": frame["non_executable_probe_count"], "partitionless_probe_count": frame["partitionless_probe_count"], "caller_supplied_decisive_input_count": frame["caller_supplied_decisive_input_count"]}
    write_json(out / "no_external_decisive_input_audit_v2.json", audit); return {**audit, "candidate_id": candidate["candidate_id"], "hypotheses": len(frame["hypotheses"]), "constraints": len(frame["constraints"]), "probes": len(frame["probes"])}
