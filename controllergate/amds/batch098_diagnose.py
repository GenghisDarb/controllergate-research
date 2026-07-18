from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from controllergate.evidence.contracts import load_contracts
from controllergate.evidence.roles_v2 import execute_and_verify_roles, role_quality_gate

from .stage_runtime_v7 import run_dpp14


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in rows), encoding="utf-8", newline="\n")


def diagnose_batch098(evidence_root: str | Path, topology_root: str | Path, contracts_path: str | Path, output: str | Path) -> dict[str, Any]:
    evidence = Path(evidence_root); topology = Path(topology_root); out = Path(output); out.mkdir(parents=True, exist_ok=True)
    contracts = load_contracts(contracts_path)
    candidate_rows: list[dict[str, Any]] = []
    for contract in contracts:
        path = evidence / contract.candidate_id / "candidate_lane_result_v2.json"
        if path.is_file():
            candidate_rows.append(json.loads(path.read_text(encoding="utf-8")))
    eligible = [row for row in candidate_rows if row.get("status") == "PASS" and row.get("cleanup", {}).get("status") == "PASS"]
    gate = {
        "status": "PASS" if len(candidate_rows) == len(eligible) == 8 else "SCIENTIFIC_BLOCK",
        "candidate_count": len(candidate_rows),
        "eligible_count": len(eligible),
        "required_count": 8,
        "substitution_count": sum(bool(row.get("candidate_substitution")) for row in candidate_rows),
        "patch_operation_count": sum(int(row.get("patch_operation_count", 0)) for row in candidate_rows),
        "historical_count_increment": sum(int(row.get("historical_count_increment", 0)) for row in candidate_rows),
        "exact_blocker": None if len(candidate_rows) == len(eligible) == 8 else "batch098_frozen_eight_materialization_gate_not_met",
        "authority_allowed": "role and AMDS admission only",
        "authority_forbidden": ["patch", "repair count", "release promotion"],
    }
    _write_json(out / "eight_episode_materialization_gate_v2.json", gate)
    if gate["status"] != "PASS":
        return gate
    produced: list[dict[str, Any]] = []
    verified: list[dict[str, Any]] = []
    stage_produced: list[dict[str, Any]] = []
    stage_verified: list[dict[str, Any]] = []
    terminals: list[dict[str, Any]] = []
    for row in eligible:
        candidate_dir = evidence / row["candidate_id"]
        observation = json.loads((candidate_dir / "neutral_observation_v2.json").read_text(encoding="utf-8"))
        role_input = {**row, "neutral_observation": observation}
        role_rows, verifier_rows = execute_and_verify_roles(role_input)
        produced.extend(role_rows); verified.extend(verifier_rows)
        frame_path = topology / row["candidate_id"] / "frame" / "topology_compiled_decision_frame_v3.json"
        frame = json.loads(frame_path.read_text(encoding="utf-8"))
        terminal, p_rows, v_rows = run_dpp14({"candidate_id": row["candidate_id"], "frame_id": row["frame_id"], "topology_probes": frame["probes"], "topology_identity": frame["board_identity"]})
        terminals.append({"candidate_id": row["candidate_id"], "terminal": terminal["terminal"], "terminal_writer": terminal["terminal_writer"], "authority_forbidden": ["patch", "repair count"]})
        stage_produced.extend(p_rows); stage_verified.extend(v_rows)
    quality = role_quality_gate(produced, verified, 8)
    _write_jsonl(out / "role_measurement_execution_receipts_v6.jsonl", produced)
    _write_jsonl(out / "role_measurement_verification_receipts_v6.jsonl", verified)
    _write_json(out / "role_measurement_quality_gate_v6.json", quality)
    _write_jsonl(out / "dpp14_stage_execution_receipts_v7.jsonl", stage_produced)
    _write_jsonl(out / "dpp14_stage_verification_receipts_v7.jsonl", stage_verified)
    _write_jsonl(out / "amds_controller_audit_terminals_v7.jsonl", terminals)
    result = {"status": "PASS" if quality["status"] == "PASS" else "SCIENTIFIC_BLOCK", "eligible_count": 8, "role_producer_count": len(produced), "role_verifier_count": len(verified), "stage_producer_count": len(stage_produced), "stage_verifier_count": len(stage_verified), "terminal_count": len(terminals), "patch_operation_count": 0, "historical_count_increment": 0, "exact_blocker": None if quality["status"] == "PASS" else "batch098_role_measurement_quality_gate_failed"}
    _write_json(out / "amds_historical_quality_gate_v7.json", result)
    return result
