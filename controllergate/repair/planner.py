from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class RepairCandidate:
    path: str
    before: str
    after: str
    rationale: str


class RepairPlanner(Protocol):
    def propose(self, source: str, allowed_path: str, failure: dict[str, object]) -> list[RepairCandidate]: ...


def validate_candidate(candidate: RepairCandidate, allowed_paths: set[str]) -> dict[str, object]:
    errors = []
    if candidate.path not in allowed_paths:
        errors.append("path_not_licensed")
    if not candidate.before or candidate.before == candidate.after:
        errors.append("empty_or_noop_patch")
    if candidate.path.startswith(("tests/", "test/", ".github/", "configs/")):
        errors.append("non_source_path")
    return {"status": "PASS" if not errors else "BLOCK", "errors": errors}
