from .orientation import Orientation
from .return_map import double_traversal, traverse


def audit_twist_return(value: Orientation, *, rollback_source_hash: str, provider_transition_authorized: bool = False,
                       resulting_provider_hash: str | None = None) -> dict:
    first = traverse(value); returned = double_traversal(value)
    provider_unchanged = resulting_provider_hash in (None, value.provider_hash) or provider_transition_authorized
    exact = returned == value and rollback_source_hash == value.source_hash and provider_unchanged
    return {"status": "PASS" if exact else "FAIL", "first_traversal_changes_orientation": first != value,
            "second_traversal_restores_exact_orientation": returned == value,
            "rollback_restores_exact_source_hash": rollback_source_hash == value.source_hash,
            "proof_parent_preserved": returned.proof_parent == value.proof_parent,
            "provider_identity_preserved_or_authorized": provider_unchanged,
            "approximate_tolerance_accepted": False, "numeric_twist_threshold_authority": False}
