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
HISTORICAL_SOURCE_REQUIREMENTS = (
    "candidate_run_frame_identity", "incident_snapshot", "source_revision",
    "source_test_immutability", "provider_runtime", "target_reproducer",
    "command_authority", "runner_origin", "harness_origin", "duplicate_failure",
    "normal_incident_frame", "normal_incident_divergence",
    "provider_alternative_exclusion", "environment_alternative_exclusion",
    "platform_alternative_exclusion", "network_transport_exclusion",
    "harness_target_exclusion", "expectation_consistency", "direct_source_contact",
    "repair_critical_interlock", "categorical_causal_elbow", "remaining_alternative",
)
LICENSE_REQUIREMENTS = (
    "source_ownership_token_hash", "single_use_authorization_record", "human_approval_record", "write_access_lease",
    "allowlisted_region", "patch_plan_hash", "source_only_scope", "test_tree_immutability", "patch_size",
    "forbidden_file_scan", "validation_plan", "native_invariant_plan", "fresh_replay_plan", "same_provider_plan",
    "rollback_ready_proof", "proof_count_nonduplication_plan", "resource_budget", "network_policy", "public_write_prohibition",
)

PROOF_REQUIRED_FIELDS = (
    "proof_type", "candidate_id", "run_id", "frame_hash", "producer_identity",
    "verifier_identity", "raw_evidence_hashes", "derivation_parents", "direct",
    "execution_depth", "freshness", "revoked", "decision_time_safe", "semantic_scope",
)


def produce_stage_proof(
    repository: ControllerStateRepository,
    *,
    requirement: str,
    candidate_id: str,
    run_id: str,
    frame_hash: str,
    producer_identity: str,
    verifier_identity: str,
    raw_evidence_hashes: list[str],
    derivation_parents: list[str],
    semantic_scope: str,
    evidence_value: Any,
    direct: bool = True,
    execution_depth: str = "executed_and_independently_verified",
) -> dict[str, Any]:
    """Persist one proof emitted by an executed producer and independent verifier.

    Manifests may reference the returned hash, but cannot manufacture this row.
    """
    if not requirement or producer_identity == verifier_identity:
        raise ValueError("independent named proof producer and verifier required")
    if not direct or execution_depth != "executed_and_independently_verified":
        raise ValueError("direct executed proof required")
    if not raw_evidence_hashes or any(len(item) != 64 for item in raw_evidence_hashes):
        raise ValueError("raw evidence hashes required")
    if evidence_value in (None, "", [], {}):
        raise ValueError("concrete evidence value required")
    proof = {
        "proof_type": requirement,
        "requirement": requirement,
        "candidate_id": candidate_id,
        "run_id": run_id,
        "frame_hash": frame_hash,
        "producer_identity": producer_identity,
        "verifier_identity": verifier_identity,
        "raw_evidence_hashes": list(raw_evidence_hashes),
        "derivation_parents": list(derivation_parents),
        "direct": True,
        "status": "PASS",
        "evidence_value": evidence_value,
        "execution_depth": execution_depth,
        "freshness": "current_run",
        "revoked": False,
        "decision_time_safe": True,
        "semantic_scope": semantic_scope,
    }
    parent = derivation_parents[-1] if derivation_parents else "0" * 64
    proof_hash = repository.record_proof_event(run_id, candidate_id, requirement, proof, parent)
    return {**proof, "proof_hash": proof_hash}


def validate_candidate_bound_approval(record: dict[str, Any], *, contract_hash: str,
                                      candidate_id: str, run_id: str, patch_sha256: str,
                                      allowed_source_path: str) -> None:
    required = {
        "human_authority": "Brad",
        "prompt_contract_hash": contract_hash,
        "candidate_id": candidate_id,
        "run_id": run_id,
        "patch_sha256": patch_sha256,
        "allowed_source_path": allowed_source_path,
        "public_write_prohibition": True,
        "historical_non_counting_boundary": True,
    }
    if any(record.get(key) != value for key, value in required.items()):
        raise ValueError("candidate-bound human approval mismatch")
    if not record.get("single_use_nonce") or not record.get("expiry"):
        raise ValueError("candidate-bound approval nonce and expiry required")


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
        if proof.get("direct") is not True or proof.get("execution_depth") != "executed_and_independently_verified":
            raise ValueError(f"proof is not direct executed evidence: {name}")
        if not proof.get("raw_evidence_hashes") or not proof.get("semantic_scope"):
            raise ValueError(f"proof evidence custody incomplete: {name}")
        if proof.get("producer_identity") != value["producer_identity"] or proof.get("verifier_identity") != value["verifier_identity"]:
            raise ValueError(f"proof producer/verifier mismatch: {name}")
        if proof.get("producer_identity") == proof.get("verifier_identity"):
            raise ValueError(f"proof independence invalid: {name}")
        resolved[name] = str(value["proof_hash"])
    return resolved


def mint_source_ownership(repository: ControllerStateRepository, manifest: dict[str, Any], frame_hash: str) -> dict[str, Any]:
    run_id = str(manifest["run_id"]); candidate_id = str(manifest["candidate_id"])
    requirements = HISTORICAL_SOURCE_REQUIREMENTS if manifest.get("authority_profile") == "batch091_stage_produced_historical_v1" else SOURCE_REQUIREMENTS
    resolved = _resolve_records(repository, run_id, candidate_id, frame_hash, dict(manifest.get("source_ownership_evidence", {})), requirements)
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
    if manifest.get("authority_profile") == "batch091_stage_produced_historical_v1":
        approval_hash = resolved["human_approval_record"]
        approval_row = repository.connection.execute("SELECT proof_json FROM proof_events WHERE proof_hash=?", (approval_hash,)).fetchone()
        approval = json.loads(approval_row["proof_json"])["evidence_value"]
        validate_candidate_bound_approval(
            approval,
            contract_hash=str(manifest["prompt_contract_hash"]),
            candidate_id=candidate_id,
            run_id=run_id,
            patch_sha256=str(manifest["patch_sha256"]),
            allowed_source_path=str(manifest["allowed_source_path"]),
        )
    payload = {"candidate_id": candidate_id, "run_id": run_id, "source_ownership_hash": source_token_hash, "resolved_proofs": resolved, "single_use": True, "revoked": False, "created_at": datetime.now(timezone.utc).isoformat()}
    token_hash = canonical_hash(payload)
    repository.connection.execute("INSERT INTO repair_license_tokens(token_hash,run_id,candidate_id,source_ownership_hash,license_json,consumed) VALUES (?,?,?,?,?,0)", (token_hash, run_id, candidate_id, source_token_hash, json.dumps(payload, sort_keys=True)))
    return {**payload, "token_hash": token_hash}


def consume_repair_license(repository: ControllerStateRepository, run_id: str, token_hash: str) -> None:
    row = repository.connection.execute("SELECT consumed FROM repair_license_tokens WHERE run_id=? AND token_hash=?", (run_id, token_hash)).fetchone()
    if not row or row["consumed"]:
        raise ValueError("repair license missing or already spent")
    repository.connection.execute("UPDATE repair_license_tokens SET consumed=1 WHERE token_hash=?", (token_hash,))
