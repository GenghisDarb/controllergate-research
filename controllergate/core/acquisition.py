from __future__ import annotations

from pathlib import Path


def discover_seed_files(paths: list[str]) -> list[str]:
    found: list[str] = []
    for root in paths:
        base = Path(root)
        if base.is_dir():
            found.extend(path.as_posix() for path in sorted(base.glob("*.json")))
    return found


def classify_candidate_source_mode(seed_count: int, metadata_probe_enabled: bool, issue_derived_enabled: bool) -> str:
    if seed_count:
        return "curated_seed"
    if metadata_probe_enabled and issue_derived_enabled:
        return "mixed"
    if metadata_probe_enabled:
        return "metadata_probe"
    if issue_derived_enabled:
        return "issue_derived"
    return "not_available"
