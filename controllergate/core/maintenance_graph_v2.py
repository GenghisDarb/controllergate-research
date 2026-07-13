from __future__ import annotations

from typing import Any

from controllergate.core.evidence import hash_record


STATE_ORDER = (
    "REFERENCE_CORE_PRESERVED",
    "CONTACT_TOPOLOGY_LEGIBLE",
    "WORKSPACE_ACCESSIBLE",
    "PROVIDER_COFACTOR_MATERIALIZED",
    "REPAIR_LICENSE_GRANTED",
    "BOUNDED_SYNTHESIS_COMPLETED",
    "CONTACT_AUDIT_PASSED",
    "DUPLICATE_REPLAY_AND_ROLLBACK_PASSED",
    "PROOF_LEDGER_TERMINAL_LOCKED",
)


def graph_contract() -> dict[str, Any]:
    states = []
    for index, state in enumerate(STATE_ORDER):
        record: dict[str, Any] = {
            "state": state,
            "required_inputs": [] if index == 0 else [STATE_ORDER[index - 1]],
            "allowed_inputs": [] if index == 0 else [STATE_ORDER[index - 1]],
            "forbidden_inputs": [item for item in STATE_ORDER[index + 1 :]],
            "expected_outputs": [STATE_ORDER[index + 1]] if index + 1 < len(STATE_ORDER) else ["TERMINAL_PROOF"],
            "forbidden_outputs": [item for item in STATE_ORDER[index + 2 :]],
            "output_verifiers": [f"verify_{state.lower()}"],
            "positive_regulators": ["direct_execution_evidence", "verified_input_hashes"],
            "negative_regulators": ["forbidden_evidence", "provider_source_conflation", "unverified_inference"],
            "blocker_codes": [f"blocked_{state.lower()}"],
            "terminal_states": ["BLOCKED_EXACT", "COMPLETE"] if index == len(STATE_ORDER) - 1 else ["BLOCKED_EXACT"],
            "reopen_conditions": ["new decision-time-safe evidence resolves the exact blocker"],
            "next_legal_states": [STATE_ORDER[index + 1]] if index + 1 < len(STATE_ORDER) else [],
        }
        record["state_hash"] = hash_record(record)
        states.append(record)
    return {
        "version": 2,
        "public_state_names_neutral": True,
        "states": states,
        "ordering_invariants": [
            "repair licensing follows contact topology",
            "repair licensing follows provider materialization",
            "patching follows repair licensing",
            "counting follows duplicate replay",
            "proof lock follows rollback proof",
            "inferred memory evidence does not establish ground truth",
            "provider identity is not source ownership",
        ],
    }


def evaluate_pathway(candidate_id: str, completed_states: list[str], *, blockers: list[str] | None = None) -> dict[str, Any]:
    blockers = blockers or []
    failures: list[str] = []
    positions = [STATE_ORDER.index(state) for state in completed_states if state in STATE_ORDER]
    if len(positions) != len(completed_states) or positions != list(range(len(positions))):
        failures.append("maintenance_state_order_violation")
    terminal = completed_states[-1] if completed_states else "NOT_STARTED"
    next_state = STATE_ORDER[len(completed_states)] if len(completed_states) < len(STATE_ORDER) else None
    record: dict[str, Any] = {
        "candidate_id": candidate_id,
        "completed_states": completed_states,
        "terminal_state": terminal,
        "next_legal_state": next_state,
        "blockers": blockers,
        "status": "PASS" if not failures else "BLOCK",
        "failures": failures,
    }
    record["pathway_hash"] = hash_record(record)
    return record

