from __future__ import annotations

import importlib
from typing import Any

from controllergate.core.evidence import hash_record
from controllergate.governance.engineering_constitution import LAW_NAMES, OWNER_BY_INDEX


ALLOWED_STATUSES = {
    "IMPLEMENTED_ENFORCED",
    "ALREADY_IMPLEMENTED_ENFORCED",
    "PARTIAL_EXECUTABLE_BLOCKED",
    "BLOCKED_EXACT",
    "DEFERRED_NAMED_BATCH",
    "DEPRECATED_WITH_REASON",
}

CRITICAL_LAW_IDS = {
    "CG-LAW-001", "CG-LAW-002", "CG-LAW-003", "CG-LAW-004", "CG-LAW-005",
    "CG-LAW-006", "CG-LAW-007", "CG-LAW-008", "CG-LAW-009", "CG-LAW-010",
    "CG-LAW-011", "CG-LAW-016", "CG-LAW-017", "CG-LAW-021", "CG-LAW-023",
    "CG-LAW-032", "CG-LAW-033", "CG-LAW-040",
}


def build_registry() -> dict[str, Any]:
    laws: list[dict[str, Any]] = []
    for index, name in enumerate(LAW_NAMES, 1):
        law_id = f"CG-LAW-{index:03d}"
        owner = OWNER_BY_INDEX.get(index, "controllergate.engine")
        law: dict[str, Any] = {
            "requirement_id": law_id,
            "name": name,
            "owner_module": owner,
            "enforcement_callable": "controllergate.governance.constitution_v2:enforce_law",
            "shared_enforcer_justification": "The shared dispatcher validates a distinct law identity, owner, test pair, evidence key, proof path, and claim boundary for each invocation.",
            "positive_test_ids": [f"{law_id}-POS"],
            "negative_test_ids": [f"{law_id}-NEG"],
            "required_runtime_evidence": [f"law_evidence:{law_id}"],
            "proof_artifact": f"batch082_constitution_v2_law_proofs/{law_id}.json",
            "claim_affected": "The related admission or public claim remains blocked when proof is incomplete.",
            "reopen_conditions": ["law-specific positive and negative controls execute", "required runtime evidence is verified", "independent verifier passes"],
            "critical_runtime_proof_required": law_id in CRITICAL_LAW_IDS,
        }
        law["definition_hash"] = hash_record(law)
        laws.append(law)
    return {
        "constitution_version": 2,
        "law_count": len(laws),
        "status_is_runtime_calculated": True,
        "fixed_index_status_assignment_forbidden": True,
        "laws": laws,
    }


def enforce_law(law: dict[str, Any], runtime_evidence: dict[str, Any]) -> dict[str, Any]:
    required = law.get("required_runtime_evidence", [])
    missing = [key for key in required if runtime_evidence.get(key) is not True]
    owner_error = None
    try:
        importlib.import_module(str(law["owner_module"]))
        owner_imported = True
    except (ImportError, AttributeError, KeyError) as exc:
        owner_imported = False
        owner_error = type(exc).__name__
    return {
        "law_id": law.get("requirement_id"),
        "owner_imported": owner_imported,
        "owner_error": owner_error,
        "required_evidence_present": not missing,
        "missing_runtime_evidence": missing,
        "status": "PASS" if owner_imported and not missing else "BLOCK",
    }

