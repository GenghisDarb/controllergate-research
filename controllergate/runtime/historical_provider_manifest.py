from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from controllergate.state.integrity import canonical_hash


@dataclass(frozen=True)
class HistoricalPackagePin:
    name: str
    version: str
    dependency_parent: str
    reason: str


@dataclass(frozen=True)
class HistoricalProviderManifest:
    candidate_id: str
    repo_url: str
    candidate_sha: str
    cutoff: str
    project_name: str
    target: tuple[str, ...]
    target_required_packages: tuple[HistoricalPackagePin, ...]
    declared_but_not_target_required: tuple[str, ...] = field(default_factory=tuple)

    def validate(self) -> None:
        if len(self.candidate_sha) != 40 or any(ch not in "0123456789abcdef" for ch in self.candidate_sha.lower()):
            raise ValueError("historical provider candidate SHA must be exact")
        parsed = datetime.fromisoformat(self.cutoff.replace("Z", "+00:00"))
        if parsed.tzinfo is None or parsed > datetime.now(timezone.utc):
            raise ValueError("historical provider cutoff invalid")
        if not self.target or not self.target_required_packages:
            raise ValueError("historical provider target requirements incomplete")
        if len({(pin.name.casefold(), pin.version) for pin in self.target_required_packages}) != len(self.target_required_packages):
            raise ValueError("historical provider duplicate package pin")

    @property
    def identity(self) -> str:
        return canonical_hash(self.to_record())

    def to_record(self) -> dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "repo_url": self.repo_url,
            "candidate_sha": self.candidate_sha,
            "cutoff": self.cutoff,
            "project_name": self.project_name,
            "target": list(self.target),
            "target_required_packages": [pin.__dict__ for pin in self.target_required_packages],
            "declared_but_not_target_required": list(self.declared_but_not_target_required),
        }

    @classmethod
    def from_record(cls, value: dict[str, Any]) -> "HistoricalProviderManifest":
        manifest = cls(
            candidate_id=str(value["candidate_id"]), repo_url=str(value["repo_url"]),
            candidate_sha=str(value["candidate_sha"]), cutoff=str(value["cutoff"]),
            project_name=str(value["project_name"]), target=tuple(str(item) for item in value["target"]),
            target_required_packages=tuple(HistoricalPackagePin(**item) for item in value["target_required_packages"]),
            declared_but_not_target_required=tuple(str(item) for item in value.get("declared_but_not_target_required", [])),
        )
        manifest.validate()
        return manifest
