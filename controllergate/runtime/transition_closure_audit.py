from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from controllergate.core.evidence import hash_record
from controllergate.runtime.cross_pathway_invariant_set import evaluate_cross_pathway_invariants


def audit_transition_closure(
    *,
    before: Mapping[str, Any],
    after: Mapping[str, Any],
    rollback: Mapping[str, Any],
    expected_changed: set[str],
    expected_unchanged: set[str],
    authorized: bool,
    proof_ledger_bound: bool,
    compartment_escape: bool,
) -> dict[str, Any]:
    invariants = evaluate_cross_pathway_invariants(
        before, after, expected_changed=expected_changed, expected_unchanged=expected_unchanged
    )
    rollback_inverse = all(rollback.get(key) == before.get(key) for key in set(before) | set(rollback))
    passed = authorized and proof_ledger_bound and not compartment_escape and rollback_inverse and invariants["status"] == "PASS"
    return {
        "status": "PASS" if passed else "BLOCK",
        "precondition_state_hash": hash_record(dict(before)),
        "postcondition_state_hash": hash_record(dict(after)),
        "rollback_state_hash": hash_record(dict(rollback)),
        "authorized_transition": authorized,
        "field_invariants": invariants,
        "rollback_inverse": rollback_inverse,
        "proof_ledger_binding": proof_ledger_bound,
        "compartment_escape": compartment_escape,
        "unsupported_topology_gate_used": False,
    }
