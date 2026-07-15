from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from controllergate.state.integrity import canonical_hash
from controllergate.state.repository import ControllerStateRepository


SOURCE_REQUIREMENTS = (
    "candidate_run_frame_identity", "proof_record_existence", "proof_hash", "producer_identity",
    "verifier_identity", "execution_depth", "freshness", "non_revocation",
    "required_exclusion_semantics", "direct_source_contact_semantics", "causal_elbow_semantics", "interlock_semantics",
)
LICENSE_REQUIREMENTS = (
    "source_ownership_token_hash", "single_use_authorization_record", "human_approval_record", "write_access_lease",
    "allowlisted_region", "patch_plan_hash", "source_only_scope", "test_tree_immutability", "patch_size",
    "forbidden_file_scan", "validation_plan", "native_invariant_plan", "fresh_replay_plan", "same_provider_plan",
    "rollback_ready_proof", "proof_count_nonduplication_plan", "resource_budget", "network_policy", "public_write_prohibition",
)


def _resolve_records(
    repository: ControllerStateRepository,
    run_id: str,
    candidate_id: str,
    frame_hash: str,
    records: dict[str, Any],
    requirements: tuple[str, ...],
) -> dict[str, str]:
    missing = [name for name in requirements if name not in records]
    if missing:
        raise ValueError(f"concrete proof requirements missing: {','.join(missing)}")
    resolved: dict[str, str] = {}
    for name in requirements:
        value = records[name]
        if not isinstance(value, dict) or not value.get("proof_hash") or not value.get("producer_identity") or not value.get("verifier_identity"):
            raise ValueError(f"generic requirement hash rejected: {name}")
        row = repository.connection.execute("SELECT proof_hash,candidate_id,proof_type,proof_json FROM proof_events WHERE run_id=? AND proof_hash=?", (run_id, value["proof_hash"])).fetchone()
        if not row:
            raise ValueError(f"proof record unresolved: {name}")
        proof = json.loads(row["proof_json"])
        if row["candidate_id"] != candidate_id or row["proof_type"] != name:
            raise ValueError(f"proof identity mismatch: {name}")
        if proof.get("candidate_id") != candidate_id or proof.get("run_id") != run_id or proof.get("frame_hash") != frame_hash:
            raise ValueError(f"proof candidate/run/frame mismatch: {name}")
        if proof.get("requirement") != name or proof.get("status") != "PASS" or proof.get("evidence_value") in (None, "", [], {}):
            raise ValueError(f"proof is not concrete: {name}")
        if proof.get("revoked") is not False or proof.get("decision_time_safe") is not True:
            raise ValueError(f"proof freshness or revocation invalid: {name}")
        if proof.get("producer_identity") != value["producer_identity"] or proof.get("verifier_identity") != value["verifier_identity"]:
            raise ValueError(f"proof producer/verifier mismatch: {name}")
        if proof.get("producer_identity") == proof.get("verifier_identity"):
            raise ValueError(f"proof independence invalid: {name}")
        resolved[name] = str(value["proof_hash"])
    return resolved


def mint_source_ownership(repository: ControllerStateRepository, manifest: dict[str, Any], frame_hash: str) -> dict[str, Any]:
    run_id = str(manifest["run_id"]); candidate_id = str(manifest["candidate_id"])
    resolved = _resolve_records(repository, run_id, candidate_id, frame_hash, dict(manifest.get("source_ownership_evidence", {})), SOURCE_REQUIREMENTS)
    payload = {"candidate_id": candidate_id, "run_id": run_id, "frame_hash": frame_hash, "resolved_proofs": resolved, "revoked": False, "created_at": datetime.now(timezone.utc).isoformat()}
    token_hash = canonical_hash(payload)
    repository.connection.execute("INSERT INTO source_ownership_tokens(token_hash,run_id,candidate_id,evidence_json,consumed) VALUES (?,?,?,?,0)", (token_hash, run_id, candidate_id, json.dumps(payload, sort_keys=True)))
    return {**payload, "token_hash": token_hash}


def mint_repair_license(repository: ControllerStateRepository, manifest: dict[str, Any], source_token_hash: str) -> dict[str, Any]:
    run_id = str(manifest["run_id"]); candidate_id = str(manifest["candidate_id"])
    records = dict(manifest.get("repair_license_evidence", {}))
    if isinstance(records.get("source_ownership_token_hash"), dict):
        records["source_ownership_token_hash"] = {**records["source_ownership_token_hash"], "resolved_value": source_token_hash}
    frame_row = repository.connection.execute("SELECT evidence_json FROM source_ownership_tokens WHERE run_id=? AND token_hash=?", (run_id, source_token_hash)).fetchone()
    if not frame_row:
        raise ValueError("source ownership token unresolved")
    frame_hash = str(json.loads(frame_row["evidence_json"])["frame_hash"])
    resolved = _resolve_records(repository, run_id, candidate_id, frame_hash, records, LICENSE_REQUIREMENTS)
    if records["source_ownership_token_hash"].get("resolved_value") != source_token_hash:
        raise ValueError("repair license source token mismatch")
    payload = {"candidate_id": candidate_id, "run_id": run_id, "source_ownership_hash": source_token_hash, "resolved_proofs": resolved, "single_use": True, "revoked": False, "created_at": datetime.now(timezone.utc).isoformat()}
    token_hash = canonical_hash(payload)
    repository.connection.execute("INSERT INTO repair_license_tokens(token_hash,run_id,candidate_id,source_ownership_hash,license_json,consumed) VALUES (?,?,?,?,?,0)", (token_hash, run_id, candidate_id, source_token_hash, json.dumps(payload, sort_keys=True)))
    return {**payload, "token_hash": token_hash}


def consume_repair_license(repository: ControllerStateRepository, run_id: str, token_hash: str) -> None:
    row = repository.connection.execute("SELECT consumed FROM repair_license_tokens WHERE run_id=? AND token_hash=?", (run_id, token_hash)).fetchone()
    if not row or row["consumed"]:
        raise ValueError("repair license missing or already spent")
    repository.connection.execute("UPDATE repair_license_tokens SET consumed=1 WHERE token_hash=?", (token_hash,))
