"""Evidence-gated necessity, sufficiency, interaction, and ownership receipts."""

from __future__ import annotations

import hashlib
import json
from typing import Any


def _hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def necessity_receipt(program_id: str, evidence: dict[str, Any]) -> dict[str, Any]:
    checks = {
        "incident_materialized": evidence.get("incident_materialized") is True,
        "factor_removed": evidence.get("factor_removed") is True,
        "incident_disappeared": evidence.get("incident_disappeared") is True,
        "held_invariants_stable": evidence.get("held_invariants_stable") is True,
        "semantic_reproducibility": evidence.get("semantic_reproducibility") is True,
        "direct_causal_contact": evidence.get("direct_causal_contact") is True,
        "independent_verifier": bool(evidence.get("independent_verifier")),
        "fresh_execution": evidence.get("fresh_execution") is True,
    }
    row = {"receipt_type": "NecessityReceiptV3", "program_id": program_id, "checks": checks,
           "supported": all(checks.values()), "authority_allowed": "necessity at executed scope",
           "authority_forbidden": ["ownership without alternative exclusion", "patch", "repair count"]}
    row["receipt_hash"] = _hash(row); return row


def sufficiency_receipt(program_id: str, evidence: dict[str, Any]) -> dict[str, Any]:
    checks = {
        "control_materialized": evidence.get("control_materialized") is True,
        "factor_introduced": evidence.get("factor_introduced") is True,
        "incident_appeared": evidence.get("incident_appeared") is True,
        "held_invariants_stable": evidence.get("held_invariants_stable") is True,
        "semantic_reproducibility": evidence.get("semantic_reproducibility") is True,
        "direct_causal_contact": evidence.get("direct_causal_contact") is True,
        "independent_verifier": bool(evidence.get("independent_verifier")),
        "fresh_execution": evidence.get("fresh_execution") is True,
    }
    row = {"receipt_type": "SufficiencyReceiptV3", "program_id": program_id, "checks": checks,
           "supported": all(checks.values()), "authority_allowed": "sufficiency at executed scope",
           "authority_forbidden": ["ownership without alternative exclusion", "patch", "repair count"]}
    row["receipt_hash"] = _hash(row); return row


def interaction_receipt(program_id: str, corners: list[dict[str, Any]], estimand: dict[str, Any]) -> dict[str, Any]:
    checks = {"factorial_complete": len(corners) >= 4 and len({row.get("corner_id") for row in corners}) == len(corners),
              "all_executed": bool(corners) and all(row.get("executed") for row in corners),
              "all_reproducible": bool(corners) and all(row.get("reproducible") for row in corners),
              "held_invariants": bool(corners) and all(row.get("held_invariants") for row in corners),
              "estimand_predeclared": estimand.get("predeclared") is True,
              "non_additive_effect": estimand.get("non_additive") is True}
    row = {"receipt_type": "InteractionReceiptV3", "program_id": program_id, "checks": checks,
           "supported": all(checks.values()), "estimand": estimand,
           "authority_allowed": "interaction at complete factorial depth", "authority_forbidden": ["automatic mixed-failure class", "patch"]}
    row["receipt_hash"] = _hash(row); return row
