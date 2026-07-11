from __future__ import annotations

from collections import defaultdict
from typing import Any

from packaging.markers import default_environment
from packaging.requirements import Requirement
from packaging.specifiers import SpecifierSet
from packaging.version import Version

from .historical_metadata import ArtifactCandidate, canonicalize_name, parse_utc


def requirement_applies(raw: str, environment: dict[str, str], extras: set[str] | None = None) -> bool:
    requirement = Requirement(raw)
    if requirement.marker is None: return True
    environment = {**default_environment(), **environment}
    extras = extras or {""}
    return any(requirement.marker.evaluate({**environment, "extra": extra}) for extra in extras)


def compatible(candidate: ArtifactCandidate, requirements: list[Requirement], environment: dict[str, str], cutoff: str) -> tuple[bool, str | None]:
    if parse_utc(candidate.upload_timestamp) > parse_utc(cutoff): return False, "post_cutoff_artifact"
    if candidate.yanked: return False, "yanked_release"
    version = Version(candidate.version)
    if any(version not in item.specifier for item in requirements): return False, "version_constraint_conflict"
    if candidate.requires_python and Version(environment["python_full_version"]) not in SpecifierSet(candidate.requires_python): return False, "requires_python_mismatch"
    return True, None


def solve(requirements: list[str], candidates: list[ArtifactCandidate], *, environment: dict[str, str], cutoff: str) -> dict[str, Any]:
    environment = {**default_environment(), **environment}
    grouped_requirements: dict[str, list[Requirement]] = defaultdict(list)
    for raw in requirements:
        parsed = Requirement(raw)
        if requirement_applies(raw, environment): grouped_requirements[canonicalize_name(parsed.name)].append(parsed)
    grouped_candidates: dict[str, list[ArtifactCandidate]] = defaultdict(list)
    for candidate in candidates: grouped_candidates[canonicalize_name(candidate.package)].append(candidate)
    decisions = []; selected = {}; conflicts = []
    for package in sorted(grouped_requirements):
        pool = sorted(grouped_candidates.get(package, []), key=lambda item: (Version(item.version), item.filename), reverse=True)
        rejected = []
        for candidate in pool:
            ok, reason = compatible(candidate, grouped_requirements[package], environment, cutoff)
            if ok: selected[package] = candidate; decisions.append({"package": package, "selected": candidate.filename, "rejected": rejected}); break
            rejected.append({"filename": candidate.filename, "reason": reason})
        if package not in selected: conflicts.append({"package": package, "requirements": [str(item) for item in grouped_requirements[package]], "minimal_unsatisfied_constraint_set": [str(item) for item in grouped_requirements[package]], "candidate_rejections": rejected})
    return {"status": "PASS" if not conflicts else "BLOCK", "selected": {key: value.as_dict() for key, value in selected.items()}, "decisions": decisions, "conflicts": conflicts, "deterministic_order": sorted(grouped_requirements)}
