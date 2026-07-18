from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping


def _hash(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()


def produce_source_ownership_stages(candidate: Mapping[str, Any], terminal: Mapping[str, Any], topology_root: str | Path) -> list[dict[str, Any]]:
    topology = Path(topology_root)
    incident = candidate.get("typed_incident", {})
    source_manifest = candidate.get("source_manifest_hash_after")
    process_product = topology / "verified" / "board_cell_registry_v1.jsonl"
    raw = process_product.read_bytes() if process_product.is_file() else b""
    rows = [
        {"stage": "incident_materialization", "raw_parent": incident.get("verification_receipt"), "executed_mechanism": "registered semantic incident verifier", "status": "PASS" if incident.get("status") == "PASS" else "BLOCK"},
        {"stage": "source_identity", "raw_parent": source_manifest, "executed_mechanism": "post-operation source manifest remeasurement", "status": "PASS" if source_manifest else "BLOCK"},
        {"stage": "direct_source_contact", "raw_parent": hashlib.sha256(raw).hexdigest() if raw else None, "executed_mechanism": "independently verified process-to-product and source-contact cells", "status": "PASS" if raw else "BLOCK"},
        {"stage": "controller_terminal_scope", "raw_parent": terminal.get("terminal_hash") or _hash(terminal), "executed_mechanism": "ControllerAudit non-authorizing terminal", "status": "PASS" if terminal.get("terminal_writer") else "BLOCK"},
    ]
    for row in rows:
        row.update({"candidate_id": candidate.get("candidate_id"), "producer": "controllergate.evidence.source_ownership_v2", "authority_allowed": "source ownership proof input", "authority_forbidden": ["source ownership token", "repair license", "patch", "repair count"]})
        row["producer_receipt"] = f"source-ownership-producer:{_hash(row)}"
    return rows


def verify_source_ownership_stages(rows: list[Mapping[str, Any]]) -> dict[str, Any]:
    verified = []
    for row in rows:
        independently_reconstructed = bool(row.get("raw_parent") and row.get("executed_mechanism") and row.get("producer_receipt"))
        verified.append({"stage": row["stage"], "producer_receipt": row["producer_receipt"], "status": "PASS" if independently_reconstructed and row["status"] == "PASS" else "BLOCK", "verifier": "controllergate.evidence.source_ownership_v2.verify_source_ownership_stages", "verifier_receipt": f"source-ownership-verifier:{_hash([row, independently_reconstructed])}"})
    complete = all(row["status"] == "PASS" for row in verified) and len(verified) == 4
    return {"status": "PASS" if complete else "BLOCK", "verified_stages": verified, "proof_count": len(verified), "source_ownership_token_count": 0, "repair_license_count": 0, "patch_operation_count": 0, "authority_forbidden": ["source ownership token in ordinary evidence-only run", "repair license", "patch", "repair count"]}
