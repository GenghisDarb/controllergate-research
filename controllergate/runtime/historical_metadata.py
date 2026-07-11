from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import re
from typing import Any


def canonicalize_name(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def parse_utc(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


@dataclass(frozen=True)
class ArtifactCandidate:
    package: str
    version: str
    filename: str
    artifact_type: str
    upload_timestamp: str
    sha256: str
    source_url: str
    metadata_sha256: str
    requires_python: str | None
    requires_dist: tuple[str, ...]
    yanked: bool = False
    build_requires: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, Any]: return asdict(self)
