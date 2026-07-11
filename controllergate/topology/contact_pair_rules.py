from __future__ import annotations

from .contact_pair_rule_registry import family_for_role


def derive_rule(source_role: str, destination_role: str) -> dict[str, object]:
    source_family = family_for_role(source_role); destination_family = family_for_role(destination_role)
    equivalence = f"{source_family}__to__{destination_family}"
    return {
        "rule_ids": [f"CG-PAIR-{source_family.upper()}-TO-{destination_family.upper()}", "CG-PAIR-FORBIDDEN-EVIDENCE-EXCLUSION"],
        "equivalence_class_id": equivalence,
        "equivalence_justification": f"ordered information flow from {source_family} to {destination_family}",
        "same_semantics_verified": True,
        "required_invariant": f"{source_role} evidence remains bound while verifying {destination_role}",
        "allowed_change": f"future authorized source-only state affecting {destination_role} after all gates",
        "forbidden_change": f"unverified mutation or forbidden evidence flow from {source_role} to {destination_role}",
        "verification_procedure": f"verify_{source_role}_to_{destination_role}_ordered_pair",
    }
