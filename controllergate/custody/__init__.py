"""Portable evidence-custody services used by the canonical engine."""

from .capsules import (
    CapsuleType,
    acquire_provider_capsule,
    activate_source_capsule,
    build_file_capsule,
    build_source_capsule,
    scan_transport_residue,
    verify_capsule,
)

__all__ = [
    "CapsuleType",
    "acquire_provider_capsule",
    "activate_source_capsule",
    "build_file_capsule",
    "build_source_capsule",
    "scan_transport_residue",
    "verify_capsule",
]
