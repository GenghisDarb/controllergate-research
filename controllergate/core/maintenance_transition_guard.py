from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from controllergate.core.evidence import hash_record


@dataclass(frozen=True)
class TransitionDecision:
    status: str
    phase: str
    prior_state_hash: str
    post_state_hash: str
    command_invoked: bool
    canonical_state_mutated: bool
    blocker: str | None
    next_allowed_action: str


REQUIRED_PREDECESSORS = {
    "reference_core": (),
    "contact_topology": ("reference_core",),
    "materialization": ("reference_core", "contact_topology"),
    "local_topology": ("materialization",),
    "coupled_topology": ("local_topology",),
    "environment_volume": ("coupled_topology",),
    "metrology": ("environment_volume",),
    "interlock_elbow": ("metrology",),
    "activation_license": ("contact_topology", "interlock_elbow"),
    "bounded_action": ("activation_license",),
    "post_action_contact_audit": ("bounded_action",),
    "duplicate_clean_replay": ("post_action_contact_audit",),
    "return_constraint": ("duplicate_clean_replay",),
    "proof_lock": ("return_constraint",),
}


def guard_transition(phase: str, completed: set[str], prior_state_hash: str, authorization: dict[str, Any], candidate_state: dict[str, Any], interlocks: dict[str, str]) -> TransitionDecision:
    missing = [item for item in REQUIRED_PREDECESSORS[phase] if item not in completed]
    interlock_blocks = [name for name, status in interlocks.items() if status != "PASS"]
    authorized = authorization.get("allowed_phase") == phase and authorization.get("status") == "PASS"
    if missing or interlock_blocks or not authorized:
        blocker = "maintenance_order_predecessor_missing" if missing else ("maintenance_interlock_blocked" if interlock_blocks else "maintenance_authorization_missing")
        material = {"phase": phase, "prior": prior_state_hash, "blocker": blocker, "candidate": candidate_state.get("candidate_id")}
        return TransitionDecision("BLOCK", phase, prior_state_hash, hash_record(material), False, False, blocker, missing[0] if missing else "resolve_blocking_interlock")
    material = {"phase": phase, "prior": prior_state_hash, "candidate_state_hash": hash_record(candidate_state)}
    return TransitionDecision("PASS", phase, prior_state_hash, hash_record(material), bool(authorization.get("invokes_command", False)), False, None, "advance_to_next_registered_phase")
