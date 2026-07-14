from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CofactorRequirement:
    precondition_id: str
    dependency_name: str
    declaring_source: str
    requirement_class: str
    version_constraint: str | None
    platform_constraint: str | None
    runtime_constraint: str | None
    artifact_source: str | None
    artifact_hash: str | None
    consumer_stages: tuple[str, ...]
