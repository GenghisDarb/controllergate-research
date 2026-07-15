from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from hashlib import sha256
import json
from typing import Any, Callable


def _digest(value: Any) -> str:
    return sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


class ArtifactState(str, Enum):
    PRIMARY = "PRIMARY"
    CONFORMANT = "CONFORMANT"
    MATURE = "MATURE"
    DEGRADED = "DEGRADED"
    RECYCLED = "RECYCLED"
    REJECTED = "REJECTED"


@dataclass(frozen=True)
class CompiledArtifact:
    artifact_id: str
    template_hash: str
    payload: dict[str, Any]
    state: ArtifactState
    evidence_hashes: tuple[str, ...]
    quality_receipt: str | None = None


@dataclass
class TemplateCompiler:
    compiler_id: str
    generators: dict[str, Callable[[dict[str, Any]], dict[str, Any]]] = field(default_factory=dict)

    def register(self, kind: str, generator: Callable[[dict[str, Any]], dict[str, Any]]) -> None:
        if not kind or kind in self.generators:
            raise ValueError("generator_kind_invalid_or_already_registered")
        self.generators[kind] = generator

    def compile(self, kind: str, template: dict[str, Any], evidence_hashes: tuple[str, ...], *, clearance: bool) -> CompiledArtifact:
        if not clearance:
            raise PermissionError("generation_promoter_clearance_missing")
        if kind not in self.generators:
            raise KeyError("generator_specialization_missing")
        if not evidence_hashes:
            raise ValueError("generation_evidence_missing")
        template_hash = _digest(template)
        payload = self.generators[kind](json.loads(json.dumps(template)))
        return CompiledArtifact(_digest({"compiler": self.compiler_id, "template": template_hash, "payload": payload}), template_hash, payload, ArtifactState.PRIMARY, evidence_hashes)


class ArtifactMaturationService:
    def mature(self, artifact: CompiledArtifact, schema: dict[str, type]) -> CompiledArtifact:
        missing = [key for key in schema if key not in artifact.payload]
        invalid = [key for key, expected in schema.items() if key in artifact.payload and not isinstance(artifact.payload[key], expected)]
        if missing or invalid:
            return CompiledArtifact(artifact.artifact_id, artifact.template_hash, artifact.payload, ArtifactState.REJECTED, artifact.evidence_hashes, _digest({"missing": missing, "invalid": invalid}))
        receipt = _digest({"artifact": artifact.artifact_id, "schema": sorted(schema), "payload": artifact.payload})
        return CompiledArtifact(artifact.artifact_id, artifact.template_hash, artifact.payload, ArtifactState.MATURE, artifact.evidence_hashes, receipt)

    def degrade(self, artifact: CompiledArtifact, reason: str) -> CompiledArtifact:
        if artifact.state is not ArtifactState.MATURE:
            raise ValueError("only_mature_artifact_can_degrade")
        return CompiledArtifact(artifact.artifact_id, artifact.template_hash, artifact.payload, ArtifactState.DEGRADED, artifact.evidence_hashes, _digest({"reason": reason}))

    def recycle(self, artifact: CompiledArtifact, *, references: int) -> CompiledArtifact:
        if references:
            raise PermissionError("active_reference_blocks_recycling")
        return CompiledArtifact(artifact.artifact_id, artifact.template_hash, {}, ArtifactState.RECYCLED, artifact.evidence_hashes, _digest({"recycled": artifact.artifact_id}))
