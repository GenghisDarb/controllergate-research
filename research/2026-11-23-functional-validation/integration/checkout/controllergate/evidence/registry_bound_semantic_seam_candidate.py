"""Proposed fresh-wrapper/seal integration. No external execution is performed here."""
from __future__ import annotations
import copy
import hashlib
import json
from typing import Any
from . import registry_bound_semantics_candidate as semantics
from .observation_adapters_candidate import adapt_observation
from .execution_contract_binding_candidate import verify_execution_binding, normalized, normalized_argv

PINNED_REGISTRY_SHA256 = "5ee513622558fcceeaeffb7889cbd765194feec1a38e9a5b46e25c9ac7c1ceb9"
SEMANTIC_VERSION = "fresh-registry-binding-local-candidate-v2"


def record_hash(value: dict[str, Any]) -> str:
    # Match the existing fresh-receipt canonicalization, including ASCII escaping.
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                    allow_nan=False).encode()).hexdigest()


def context_from_receipt(row: dict[str, Any]) -> dict[str, Any]:
    return {key: row.get(key) for key in semantics.CONTEXT_FIELDS}


def bind_fresh_receipt(row: dict[str, Any], observation: dict[str, Any],
                       cell: dict[str, Any], registry_bytes: bytes,
                       *, execution_binding: dict[str, Any] | None = None) -> dict[str, Any]:
    for key in ("cell_id", "candidate_id", "program_id"):
        if key not in cell or row.get(key) != cell[key]:
            raise ValueError("fresh_cell_contract_mismatch:" + key)
    adapted = adapt_observation(cell["candidate_id"], observation)
    errors = verify_execution_binding(execution_binding, cell, row)
    if errors:
        raise ValueError("execution_contract_not_verified:" + ",".join(errors))
    if adapted["receipt"]["errors"]:
        raise ValueError("conflicting_observation_adapter:" + ",".join(adapted["receipt"]["errors"]))
    result = semantics.evaluate_bound_outcome(registry_bytes,
        expected_registry_sha256=PINNED_REGISTRY_SHA256,
        candidate_id=cell["candidate_id"], program_id=cell["program_id"],
        role=cell.get("cell_role", "UNDECLARED"), observation=adapted["observation"],
        context=context_from_receipt(row))
    diagnostic_outcomes = {}
    for role in ("incident", "control"):
        diagnostic_outcomes[role] = semantics.evaluate_bound_outcome(registry_bytes,
            expected_registry_sha256=PINNED_REGISTRY_SHA256,
            candidate_id=cell["candidate_id"], program_id=cell["program_id"],
            role=role, observation=adapted["observation"], context=context_from_receipt(row))
    out = copy.deepcopy(row)
    out.update(
        semantic_contract_version=SEMANTIC_VERSION,
        legacy_predicate_result_diagnostic=row.get("predicate_result"),
        legacy_semantic_fingerprint_diagnostic=row.get("semantic_fingerprint"),
        raw_semantic_observation=copy.deepcopy(observation),
        raw_execution_binding=copy.deepcopy(execution_binding),
        observation_adapter_receipt=adapted["receipt"],
        diagnostic_outcomes=diagnostic_outcomes,
        bound_outcome_receipt=result, semantic_status=result["status"],
        predicate_result=result["satisfied"],
        predicate_registry_hash=result["registry_sha256"],
        semantic_projection_id=result["projection_id"],
        semantic_fingerprint=result["semantic_projection_hash"],
    )
    out["record_hash"] = record_hash({k: v for k, v in out.items() if k != "record_hash"})
    return out


def verify_fresh_semantics(row: dict[str, Any], cell: dict[str, Any],
                           registry_bytes: bytes) -> list[str]:
    errors = []
    try:
        if row.get("record_hash") != record_hash({k: v for k, v in row.items() if k != "record_hash"}):
            errors.append("outer_record_hash_mismatch")
        if row.get("semantic_contract_version") != SEMANTIC_VERSION:
            errors.append("bound_semantic_contract_missing")
        if any(row.get(key) != cell.get(key) or key not in cell for key in ("cell_id", "candidate_id", "program_id")):
            errors.append("fresh_cell_contract_mismatch")
        bound = row.get("bound_outcome_receipt")
        raw = row.get("raw_semantic_observation")
        if not isinstance(bound, dict) or not isinstance(raw, dict):
            return errors + ["raw_observation_or_binding_missing"]
        errors.extend(verify_execution_binding(row.get("raw_execution_binding"), cell, row))
        broker = row.get("bound_broker_observation")
        binding = row.get("raw_execution_binding", {})
        if not isinstance(broker, dict):
            errors.append("bound_broker_observation_missing")
        else:
            if broker.get("operation_id") != row.get("broker_operation_id") or broker.get("record_hash") != row.get("broker_record_hash"):
                errors.append("bound_broker_identity_mismatch")
            if normalized_argv(broker.get("argv", []), row.get("platform")) != normalized_argv(binding.get("observed_argv", []), row.get("platform")):
                errors.append("bound_broker_argv_mismatch")
            if normalized(broker.get("working_directory", ""), row.get("platform")) != normalized(binding.get("observed_cwd", ""), row.get("platform")):
                errors.append("bound_broker_cwd_mismatch")
            if broker.get("return_code") != raw.get("return_code") or broker.get("return_code") != row.get("raw_return_code"):
                errors.append("bound_broker_return_code_mismatch")
            for field, broker_key, outer_key in (("stdout_sha256", "stdout_hash", "raw_stdout_object"), ("stderr_sha256", "stderr_hash", "raw_stderr_object")):
                if broker.get(broker_key) != raw.get(field) or broker.get(broker_key) != row.get(outer_key, {}).get("sha256"):
                    errors.append("bound_broker_stream_mismatch:" + field)
        adapted = adapt_observation(cell.get("candidate_id", ""), raw)
        if adapted["receipt"]["errors"]:
            errors.append("observation_adapter_conflict")
        if semantics.canonical_hash(row.get("observation_adapter_receipt")) != semantics.canonical_hash(adapted["receipt"]):
            errors.append("observation_adapter_not_reproduced")
        check = semantics.verify_bound_receipt(bound, registry_bytes,
            expected_registry_sha256=PINNED_REGISTRY_SHA256,
            candidate_id=cell.get("candidate_id", ""), program_id=cell.get("program_id", ""),
            role=cell.get("cell_role", "UNDECLARED"), observation=adapted["observation"],
            context=context_from_receipt(row))
        if not check["receipt_matches_recomputation"]:
            errors.append("predicate_or_projection_not_reproduced")
        expected_diagnostics = {role: semantics.evaluate_bound_outcome(registry_bytes,
            expected_registry_sha256=PINNED_REGISTRY_SHA256,
            candidate_id=cell.get("candidate_id", ""), program_id=cell.get("program_id", ""),
            role=role, observation=adapted["observation"], context=context_from_receipt(row))
            for role in ("incident", "control")}
        if semantics.canonical_hash(row.get("diagnostic_outcomes")) != semantics.canonical_hash(expected_diagnostics):
            errors.append("diagnostic_predicates_not_reproduced")
        linked = {"semantic_status": bound.get("status"), "predicate_result": bound.get("satisfied"),
                  "predicate_registry_hash": bound.get("registry_sha256"),
                  "semantic_projection_id": bound.get("projection_id"),
                  "semantic_fingerprint": bound.get("semantic_projection_hash")}
        actual = {key: row.get(key) for key in linked}
        if semantics.canonical_hash(actual) != semantics.canonical_hash(linked):
            errors.append("outer_semantic_fields_disagree")
    except (ValueError, TypeError, KeyError) as exc:
        errors.append("semantic_verification_error:" + type(exc).__name__)
    return errors


def cell_status_after_verification(rows: list[dict[str, Any]]) -> str:
    if not rows or any(row.get("semantic_status") != "EVALUATED" for row in rows):
        return "EXECUTED_SEMANTICS_UNRESOLVED"
    return "EXECUTED_VERIFIED" if all(row.get("predicate_result") is True for row in rows) else "EXECUTED_PREDICATE_FALSE"


def semantic_pair_consistent(rows: list[dict[str, Any]], cell: dict[str, Any],
                             registry_bytes: bytes) -> bool:
    if len(rows) < 2 or any(verify_fresh_semantics(row, cell, registry_bytes) for row in rows):
        return False
    if any(len({row.get(key) for row in rows}) < 2 for key in
           ("execution_receipt_id", "replay_index", "broker_operation_id")):
        return False
    first = rows[0]
    for other in rows[1:]:
        comparison = semantics.compare_scoped_replay(
            first["bound_outcome_receipt"], other["bound_outcome_receipt"],
            registry_bytes=registry_bytes, expected_registry_sha256=PINNED_REGISTRY_SHA256,
            candidate_id=cell["candidate_id"], program_id=cell["program_id"],
            role=cell.get("cell_role", "UNDECLARED"),
            left_observation=adapt_observation(cell["candidate_id"], first["raw_semantic_observation"])["observation"],
            right_observation=adapt_observation(cell["candidate_id"], other["raw_semantic_observation"])["observation"],
            left_context=context_from_receipt(first), right_context=context_from_receipt(other))
        if comparison["status"] != "SAME_DECLARED_OUTCOME":
            return False
    return True


def measured_pair_contrast(incident: list[dict[str, Any]], control: list[dict[str, Any]]) -> dict[str, Any]:
    """Compare the same two frozen predicates, without comparing context hashes.

Inputs must already have passed verify_fresh_semantics at this boundary. This is
descriptive contrast only; source/provider/budget invariants are a separate gate.
    """
    vectors = []
    for group in (incident, control):
        if not group:
            return {"status": "UNRESOLVED", "contrast": None, "reason": "missing_pair"}
        observed = []
        for row in group:
            d = row.get("diagnostic_outcomes", {})
            if any(d.get(role, {}).get("status") != "EVALUATED" for role in ("incident", "control")):
                return {"status": "UNRESOLVED", "contrast": None, "reason": "common_predicate_vector_incomplete"}
            observed.append(tuple(d[role]["satisfied"] for role in ("incident", "control")))
        if len(set(observed)) != 1:
            return {"status": "UNRESOLVED", "contrast": None, "reason": "nonreproducible_predicate_vector"}
        vectors.append(observed[0])
    return {"status": "DESCRIPTIVE_CONTRAST" if vectors[0] != vectors[1] else "NO_DECLARED_OUTCOME_CONTRAST",
            "contrast": vectors[0] != vectors[1], "incident_vector": list(vectors[0]),
            "control_vector": list(vectors[1]), "causal_authority": False}
