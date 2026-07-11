from __future__ import annotations

from .types import AmdsConstraint

ALLOWED_CONSTRAINT_TYPES = {"requires", "excludes", "implies", "mutually_exclusive", "exactly_one", "at_least_one", "at_most_one", "provider_dependency", "environment_dependency", "source_ownership", "provenance_boundary", "interlock_boundary", "authorization_boundary", "rollback_boundary"}


def validate_constraint(value: AmdsConstraint | dict) -> bool:
    kind = value.constraint_type if isinstance(value, AmdsConstraint) else value.get("constraint_type")
    members = value.members if isinstance(value, AmdsConstraint) else value.get("members", [])
    return kind in ALLOWED_CONSTRAINT_TYPES and len(members) >= 1
