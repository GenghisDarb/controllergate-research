from __future__ import annotations

from .types import AmdsConstraint

ALLOWED_CONSTRAINT_TYPES = {"requires", "excludes", "implies", "mutually_exclusive", "exactly_one", "at_least_one", "at_most_one", "provider_dependency", "environment_dependency", "source_ownership", "provenance_boundary", "interlock_boundary", "authorization_boundary", "rollback_boundary"}
BOUNDARY_CONSTRAINT_TYPES = {"source_ownership", "provenance_boundary", "interlock_boundary", "authorization_boundary", "rollback_boundary"}
DEPENDENCY_CONSTRAINT_TYPES = {"requires", "implies", "provider_dependency", "environment_dependency"}


def constraint_semantics_registry() -> dict[str, str]:
    return {
        "requires": "active antecedent requires active or resolved consequent",
        "excludes": "no more than one member may be active",
        "implies": "active antecedent activates consequent",
        "mutually_exclusive": "no more than one member may be active",
        "exactly_one": "exactly one member must be active",
        "at_least_one": "one or more members must be active",
        "at_most_one": "zero or one member may be active",
        "provider_dependency": "action cannot activate until provider prerequisite resolves",
        "environment_dependency": "action cannot activate until environment prerequisite resolves",
        "source_ownership": "patch action requires source-owned classification",
        "provenance_boundary": "action blocked unless provenance prerequisites resolve",
        "interlock_boundary": "action blocked unless interlock prerequisites resolve",
        "authorization_boundary": "action blocked unless authorization prerequisite resolves",
        "rollback_boundary": "action blocked unless rollback and proof prerequisites resolve",
    }


def validate_constraint(value: AmdsConstraint | dict) -> bool:
    kind = value.constraint_type if isinstance(value, AmdsConstraint) else value.get("constraint_type")
    members = value.members if isinstance(value, AmdsConstraint) else value.get("members", [])
    return kind in ALLOWED_CONSTRAINT_TYPES and len(members) >= 1
