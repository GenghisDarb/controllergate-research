from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable, Mapping, Sequence

from controllergate.state.integrity import canonical_hash


IDENTIFIER_PATTERNS = (
    re.compile(r"(?i)\bbatch[_-]?(\d{1,3}[a-z]?)\b"),
    re.compile(r"(?i)\bclean_replication_batch[_-]?(\d{1,3}[a-z]?)\b"),
    re.compile(r"(?i)\bpost_v2_37_hardening_batch[_-]?(\d{1,3}[a-z]?)\b"),
    re.compile(r"(?i)\bv(\d+(?:[._]\d+)+(?:[a-z])?)\b"),
)


@dataclass(frozen=True)
class HistoricalIdentifier:
    historical_id: str
    kind: str
    source_paths: tuple[str, ...]
    repository_present: bool
    documentary_present: bool

    @property
    def identity(self) -> str:
        return canonical_hash(self.record())

    def record(self) -> dict[str, object]:
        return {
            "documentary_present": self.documentary_present,
            "historical_id": self.historical_id,
            "kind": self.kind,
            "repository_present": self.repository_present,
            "source_paths": list(self.source_paths),
        }


def _normalize(match: re.Match[str]) -> tuple[str, str]:
    raw = match.group(0).lower().replace("-", "_")
    value = match.group(1).lower().replace("_", ".")
    if raw.startswith("v"):
        return f"v{value}", "protocol_or_version"
    return f"batch{value.zfill(3) if value.isdigit() else value}", "batch_or_campaign"


def discover_identifiers(sources: Mapping[str, str], documentary_paths: Iterable[str] = ()) -> tuple[HistoricalIdentifier, ...]:
    documentary = set(documentary_paths)
    found: dict[tuple[str, str], set[str]] = {}
    for path, text in sources.items():
        surface = f"{path}\n{text}"
        for pattern in IDENTIFIER_PATTERNS:
            for match in pattern.finditer(surface):
                key = _normalize(match)
                found.setdefault(key, set()).add(path)
    rows = [
        HistoricalIdentifier(
            historical_id=identifier,
            kind=kind,
            source_paths=tuple(sorted(paths)),
            repository_present=any(path not in documentary for path in paths),
            documentary_present=any(path in documentary for path in paths),
        )
        for (identifier, kind), paths in found.items()
    ]
    return tuple(sorted(rows, key=lambda row: (row.kind, _natural_key(row.historical_id))))


def _natural_key(value: str) -> tuple[object, ...]:
    return tuple(int(part) if part.isdigit() else part for part in re.split(r"(\d+)", value))


def coverage(discovered: Sequence[HistoricalIdentifier], dispositions: Mapping[str, str]) -> dict[str, object]:
    allowed = {"DOCUMENTARY_ONLY", "NEGATIVE_FIXTURE", "SUPERSEDED", "MIGRATED", "BLOCKED_MISSING_EVIDENCE"}
    ids = [row.historical_id for row in discovered]
    omissions = sorted(identifier for identifier in ids if dispositions.get(identifier) not in allowed)
    duplicates = len(ids) - len(set(ids))
    return {
        "coverage_percentage": 100.0 if not omissions and not duplicates else round(100 * (len(ids) - len(omissions)) / max(len(ids), 1), 4),
        "denominator": len(ids),
        "duplicate_inflation": duplicates,
        "omissions": omissions,
        "status": "PASS" if not omissions and not duplicates else "BLOCK",
    }
