from __future__ import annotations

from enum import StrEnum


class Compartment(StrEnum):
    ARTIFACT = "artifact"
    SOURCE = "source"
    PROVIDER = "provider"
    RUNTIME = "runtime"
    HARNESS = "harness"
    TEST = "test"
    AUTHORIZATION = "authorization"
    DIAGNOSTIC = "diagnostic"
    MEMORY = "memory"
    PATCH = "patch"
    VALIDATION = "validation"
    ROLLBACK = "rollback"
    PROOF = "proof"


ALL_COMPARTMENTS = frozenset(item.value for item in Compartment)


def require_compartment(value: str | Compartment) -> str:
    normalized = str(value)
    if normalized not in ALL_COMPARTMENTS:
        raise ValueError(f"unknown compartment: {normalized}")
    return normalized
