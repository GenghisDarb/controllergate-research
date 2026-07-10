from __future__ import annotations

from .activation_ring import LICENSE_GATES
from .contact_ledger import CONTACT_ROLES, validate_contact_ledger
from .types import ActivationLicense6, ContactLedger14, ProofMatrix196


def verify_reference_core(core: tuple[object, ...]) -> dict[str, object]:
    return {"status": "PASS" if len(core) == 5 else "FAIL", "role_count": len(core)}


def verify_contact_ledger(ledger: ContactLedger14) -> dict[str, object]:
    try:
        validate_contact_ledger(ledger.contacts)
    except ValueError as exc:
        return {"status": "FAIL", "blocker": str(exc)}
    return {"status": "PASS", "contact_count": 14, "missing_count": 0, "duplicate_count": 0}


def verify_activation_license(license_state: ActivationLicense6) -> dict[str, object]:
    valid = len(license_state.gates) == len(LICENSE_GATES) and license_state.patch_authority is False
    return {"status": "PASS" if valid else "FAIL", "gate_count": len(license_state.gates), "license_result": license_state.status}


def verify_proof_matrix(matrix: ProofMatrix196) -> dict[str, object]:
    pairs = {(item.source_contact, item.destination_contact) for item in matrix.cells}
    return {"status": "PASS" if len(matrix.cells) == len(pairs) == 196 and matrix.status != "PASS" else "FAIL", "cell_count": len(matrix.cells), "proof_lock": matrix.status}
