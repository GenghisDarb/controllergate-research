"""Canonical ControllerGate 5/14/6/196 operational translation.

This module is internal software architecture.  It is not biological or
physical proof, and none of its records can authorize a patch or release.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Mapping


CANONICAL_ORDER = (
    "five_set_reference_core",
    "fourteen_set_native_topology",
    "bounded_tension_relief_and_materialization",
    "six_set_activation_licensing",
    "bounded_operation_or_source_only_patch",
    "fourteen_contact_controller_audit",
    "duplicate_clean_replay",
    "phase_inversion_and_seed_constraint",
    "one_ninety_six_proof_obligations_ledger_lock",
)

REJECTED_INTERPRETATIONS = (
    "six_set_builds_closure",
    "preflight_pass_means_repairable",
    "fourteen_means_fourteen_literal_contacts_in_every_case",
    "MCM_loads_over_fourteen_nucleosomes",
    "fourteen_nucleosomes_equal_196_base_pairs",
    "one_ninety_six_is_universal_biology_constant",
    "single_system_TORUS_BROT_equals_ToT_BROT",
    "documentation_equals_empirical_validation",
    "Reactome_coverage_equals_causal_gain",
    "local_effect_equals_generalization",
)

CONTACT_STATUSES = ("PRESENT", "MISSING", "NOT_APPLICABLE")


@dataclass(frozen=True)
class ContactSlotV3:
    slot: int
    status: str
    evidence_parent: str | None

    def __post_init__(self) -> None:
        if self.slot not in range(1, 15):
            raise ValueError("contact slot must be 1 through 14")
        if self.status not in CONTACT_STATUSES:
            raise ValueError("invalid contact status")
        if self.status == "PRESENT" and not self.evidence_parent:
            raise ValueError("present contacts require evidence")
        if self.status != "PRESENT" and self.evidence_parent is not None:
            raise ValueError("missing/non-applicable contacts cannot invent evidence")


def canonical_hash(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def build_contact_ledger(
    present: Mapping[int, str], *, not_applicable: set[int] | None = None
) -> list[dict[str, Any]]:
    """Build all fourteen explicit slots without inventing literal contacts."""
    not_applicable = not_applicable or set()
    if set(present) & not_applicable:
        raise ValueError("a slot cannot be present and not applicable")
    rows = []
    for slot in range(1, 15):
        status = (
            "PRESENT"
            if slot in present
            else "NOT_APPLICABLE" if slot in not_applicable else "MISSING"
        )
        rows.append(
            asdict(
                ContactSlotV3(
                    slot=slot,
                    status=status,
                    evidence_parent=present.get(slot),
                )
            )
        )
    return rows


def validate_order(order: list[str] | tuple[str, ...]) -> bool:
    return tuple(order) == CANONICAL_ORDER


def stack_contract() -> dict[str, Any]:
    payload = {
        "schema": "ControllerGateCanonicalStackV3",
        "order": list(CANONICAL_ORDER),
        "reference_core_count": 5,
        "contact_ledger_slot_count": 14,
        "activation_license_gate_count": 6,
        "proof_recurrence_cell_count": 196,
        "six_set_role": "licenses a bounded operation only after topology is legible",
        "fourteen_set_role": "bounded falsifiable contact audit with explicit missing and non-applicable slots",
        "one_ninety_six_role": "ControllerGate 14x14 proof-recurrence schema",
        "mcm_boundary": "MCM2-7 is a six-subunit licensing system; no exact fourteen-nucleosome or 196-bp loading claim is authorized",
        "authority_allowed": "internal operational translation and nonauthorizing shadow tests",
        "authority_forbidden": [
            "biological proof",
            "physical proof",
            "patch authorization",
            "repair count",
            "release promotion",
        ],
        "rejected_interpretations": list(REJECTED_INTERPRETATIONS),
    }
    payload["contract_hash"] = canonical_hash(payload)
    return payload
