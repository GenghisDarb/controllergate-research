from __future__ import annotations

from .planner import RepairCandidate


def reviewed_candidate(path: str, before: str, after: str, reviewer: str) -> RepairCandidate:
    if not reviewer.strip():
        raise ValueError("reviewer identity required")
    return RepairCandidate(path, before, after, f"reviewed manual adapter: {reviewer}")
