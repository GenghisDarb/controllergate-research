"""Candidate-specific alternative-exclusion and ownership firewall."""

from __future__ import annotations

from typing import Any


ALTERNATIVES = ("source", "provider", "environment_platform", "runner", "harness_fixture", "service_transport", "test_expectation", "mixed_interaction")


def evaluate_alternatives(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_name = {row.get("alternative"): row for row in rows}
    unresolved = [name for name in ALTERNATIVES if not by_name.get(name, {}).get("excluded", False)]
    return {"receipt_type": "AlternativeExclusionReceiptV2", "alternatives": [by_name.get(name, {"alternative": name, "excluded": False, "evidence": []}) for name in ALTERNATIVES],
            "unresolved_alternatives": unresolved, "all_required_alternatives_resolved": not unresolved,
            "authority_allowed": "candidate-specific alternative bookkeeping", "authority_forbidden": ["exclusion by sensitivity alone", "patch", "repair count"]}


def ownership_support(*, necessity: dict[str, Any], sufficiency: dict[str, Any], alternatives: dict[str, Any],
                      direct_contact: bool, fresh_reproducible: bool, truth_access_count: int, patch_operation_count: int) -> dict[str, Any]:
    checks = {"necessity_or_sufficiency": necessity.get("supported", False) or sufficiency.get("supported", False),
              "direct_contact": direct_contact, "alternatives_resolved": alternatives.get("all_required_alternatives_resolved", False),
              "fresh_reproducible": fresh_reproducible, "no_truth_access": truth_access_count == 0, "no_patch": patch_operation_count == 0}
    return {"receipt_type": "OwnershipSupportReceiptV3", "checks": checks, "ownership_supported": all(checks.values()),
            "authority_allowed": "source ownership support at bounded candidate scope", "authority_forbidden": ["patch", "repair count", "release promotion"]}
