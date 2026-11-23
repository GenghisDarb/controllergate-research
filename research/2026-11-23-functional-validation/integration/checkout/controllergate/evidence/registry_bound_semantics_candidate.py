"""Local outcome-classification repair candidate; grants no causal or actuation authority.

The projection here is deliberately new: it preserves all fields referenced by
the selected role predicate, plus explicit replay invariants. Both predicates
are separately recorded as diagnostics by the fresh seam; an unavailable field
needed only for the other role does not invalidate this role's measurement.
It is not a claim that the historical v2 projection performed these operations.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any

from . import declarative_predicate_v1 as original

PROJECTION_ID = "program-role-operand-projection-v2-local-candidate"
CONTEXT_FIELDS = (
    "cell_id", "source_commit", "source_capsule_hash", "provider_capsule_hash",
    "exact_argv_hash", "environment_hash", "fixture_hash",
)


class Unresolved(ValueError):
    pass


def canonical_hash(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"),
                     ensure_ascii=False, allow_nan=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result = {}
    for key, value in pairs:
        if key in result:
            raise Unresolved("duplicate_json_key:" + key)
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise Unresolved("nonfinite_registry_number:" + value)


def operand_fields(value: Any) -> set[str]:
    if isinstance(value, dict):
        if set(value) == {"field"}:
            if not isinstance(value["field"], str):
                raise Unresolved("operand_field_path_not_string")
            return {value["field"]}
        fields: set[str] = set()
        for key, item in value.items():
            # Missing in a dictionary is unobserved here; no closed-world assumption.
            if key in {"exists", "missing"}:
                if not isinstance(item, str):
                    raise Unresolved("presence_path_not_string")
                fields.add(item)
            else:
                fields.update(operand_fields(item))
        return fields
    if isinstance(value, list):
        return set().union(*(operand_fields(item) for item in value)) if value else set()
    return set()


def _value(spec: Any, observation: dict[str, Any]) -> Any:
    if isinstance(spec, dict) and set(spec) == {"field"}:
        return original.resolve(observation, spec["field"])
    return spec


def _validate_predicate(predicate: Any, observation: dict[str, Any]) -> None:
    if not isinstance(predicate, dict) or len(predicate) != 1:
        raise Unresolved("malformed_predicate")
    op, arg = next(iter(predicate.items()))
    if op in {"all", "any"}:
        if not isinstance(arg, list) or not arg:
            raise Unresolved("empty_or_malformed_boolean_group")
        for item in arg:
            _validate_predicate(item, observation)
        return
    if op == "not":
        _validate_predicate(arg, observation)
        return
    if op in {"exists", "missing"}:
        original.resolve(observation, arg)
        return
    if op not in {"eq", "ne", "gt", "ge", "lt", "le"}:
        raise Unresolved("unsupported_predicate_operator:" + str(op))
    if not isinstance(arg, list) or len(arg) != 2:
        raise Unresolved("malformed_comparison")
    left, right = (_value(x, observation) for x in arg)
    if op in {"gt", "ge", "lt", "le"}:
        if not all(type(x) in {int, float} and math.isfinite(x) for x in (left, right)):
            raise Unresolved("numeric_operand_not_finite_measurement")
    elif ((type(left) is bool and type(right) in {int, float}) or
          (type(right) is bool and type(left) in {int, float})):
        raise Unresolved("boolean_numeric_equality_forbidden")


def evaluate_bound_outcome(
    registry_bytes: bytes, *, expected_registry_sha256: str,
    candidate_id: str, program_id: str, role: str,
    observation: dict[str, Any], context: dict[str, Any],
) -> dict[str, Any]:
    """Classify exactly the frozen predicate; return UNRESOLVED for missing evidence."""
    registry_sha = hashlib.sha256(registry_bytes).hexdigest()
    result: dict[str, Any] = {
        "schema": "registry-bound-outcome-repair-candidate-v2",
        "candidate_id": candidate_id, "program_id": program_id, "role": role,
        "registry_sha256": registry_sha, "expected_registry_sha256": expected_registry_sha256,
        "registry_entry_hash": None, "predicate_hash": None,
        "raw_observation_hash": None, "execution_context_hash": None,
        "projection_id": PROJECTION_ID, "projection_fields": [],
        "semantic_projection_hash": None,
        "status": "UNRESOLVED", "verdict": "UNRESOLVED", "satisfied": None,
        "unresolved_reason": None,
        "authority_allowed": "declared outcome classification and scoped replay comparison only",
        "authority_forbidden": ["fresh execution attestation", "causal ownership", "patch", "repair count", "biological or physical inference"],
    }
    try:
        if registry_sha != expected_registry_sha256:
            raise Unresolved("registry_digest_mismatch")
        if not isinstance(observation, dict) or not isinstance(context, dict):
            raise Unresolved("observation_and_context_must_be_objects")
        result["raw_observation_hash"] = canonical_hash(observation)
        result["execution_context_hash"] = canonical_hash(context)
        missing_context = [key for key in CONTEXT_FIELDS if not isinstance(context.get(key), str) or not context[key]]
        if missing_context:
            raise Unresolved("missing_replay_invariants:" + ",".join(missing_context))
        rows = [json.loads(line, object_pairs_hook=_object, parse_constant=_reject_constant)
                for line in registry_bytes.decode("utf-8").splitlines() if line.strip()]
        matches = [row for row in rows if row.get("candidate_id") == candidate_id and row.get("program_id") == program_id]
        if len(matches) != 1:
            raise Unresolved("registry_entry_not_unique:" + str(len(matches)))
        entry = matches[0]
        result["registry_entry_hash"] = canonical_hash(entry)
        if role not in {"incident", "control"} or role + "_predicate" not in entry:
            raise Unresolved("role_predicate_not_declared")
        predicate = entry[role + "_predicate"]
        result["predicate_hash"] = canonical_hash(predicate)
        # Every operand of the selected role is required, even if Python's
        # short-circuit evaluation would otherwise hide a missing value.
        fields = sorted(operand_fields(predicate))
        if not fields:
            raise Unresolved("no_measured_operand_fields")
        result["projection_fields"] = fields
        projected = {}
        for field in fields:
            try:
                projected[field] = original.resolve(observation, field)
            except (KeyError, IndexError, TypeError) as exc:
                raise Unresolved("unobserved_operand:" + field) from exc
        _validate_predicate(predicate, observation)
        value = original.evaluate(predicate, observation)
        if type(value) is not bool:
            raise Unresolved("predicate_result_not_boolean")
        result["semantic_projection_hash"] = canonical_hash({
            "projection_id": PROJECTION_ID,
            "registry_entry_hash": result["registry_entry_hash"],
            "observed_operands": projected,
            "replay_invariants": {key: context[key] for key in CONTEXT_FIELDS},
        })
        result["observed_operands"] = projected
        result.update(status="EVALUATED", verdict="SATISFIED" if value else "NOT_SATISFIED", satisfied=value)
    except (Unresolved, KeyError, IndexError, TypeError, ValueError, OverflowError) as exc:
        result["unresolved_reason"] = str(exc) or type(exc).__name__
    result["record_hash"] = canonical_hash(result)
    return result


def verify_bound_receipt(receipt: dict[str, Any], registry_bytes: bytes, *,
                         expected_registry_sha256: str, candidate_id: str,
                         program_id: str, role: str, observation: dict[str, Any],
                         context: dict[str, Any]) -> dict[str, Any]:
    """Recompute from independent inputs, rather than trusting a signed label."""
    expected = evaluate_bound_outcome(
        registry_bytes, expected_registry_sha256=expected_registry_sha256,
        candidate_id=candidate_id, program_id=program_id, role=role,
        observation=observation, context=context,
    )
    try:
        submitted_hash = canonical_hash({k: v for k, v in receipt.items() if k != "record_hash"})
        exact = receipt.get("record_hash") == submitted_hash and canonical_hash(receipt) == canonical_hash(expected)
    except (TypeError, ValueError, OverflowError):
        exact = False
    return {"receipt_matches_recomputation": exact,
            "classification_established": exact and expected["status"] == "EVALUATED",
            "status": "VERIFIED_OUTCOME_ONLY" if exact and expected["status"] == "EVALUATED" else "UNRESOLVED" if exact else "REJECTED",
            "expected_record_hash": expected["record_hash"],
            "causal_or_patch_authority": False}


def compare_scoped_replay(left: dict[str, Any], right: dict[str, Any], *,
    registry_bytes: bytes, expected_registry_sha256: str, candidate_id: str,
    program_id: str, role: str, left_observation: dict[str, Any],
    right_observation: dict[str, Any], left_context: dict[str, Any],
    right_context: dict[str, Any]) -> dict[str, Any]:
    """Verify both receipts before comparing; this still does not attest execution."""
    for receipt, observation, context in ((left, left_observation, left_context),
                                          (right, right_observation, right_context)):
        check = verify_bound_receipt(receipt, registry_bytes,
            expected_registry_sha256=expected_registry_sha256,
            candidate_id=candidate_id, program_id=program_id, role=role,
            observation=observation, context=context)
        if not check["classification_established"]:
            return {"status": "UNRESOLVED", "reason": "receipt_not_verified_outcome",
                    "raw_custody_equal": None}
    same_contract = all(left.get(k) == right.get(k) for k in ("candidate_id", "program_id", "role", "registry_sha256", "predicate_hash", "projection_id"))
    if left.get("status") != "EVALUATED" or right.get("status") != "EVALUATED" or not same_contract:
        return {"status": "UNRESOLVED", "raw_custody_equal": left.get("raw_observation_hash") == right.get("raw_observation_hash")}
    same = left.get("semantic_projection_hash") == right.get("semantic_projection_hash") and left.get("satisfied") == right.get("satisfied")
    return {"status": "SAME_DECLARED_OUTCOME" if same else "DIFFERENT_DECLARED_OUTCOME",
            "raw_custody_equal": left["raw_observation_hash"] == right["raw_observation_hash"],
            "scope": "program operand projection and declared software invariants, not full biological or causal equivalence"}
