from __future__ import annotations

import email
import zipfile
from pathlib import Path
from typing import Any

try:
    from packaging.requirements import InvalidRequirement, Requirement
    from packaging.utils import canonicalize_name
except ModuleNotFoundError:  # setup-python always supplies pip's vendored PEP 508 parser
    from pip._vendor.packaging.requirements import InvalidRequirement, Requirement
    from pip._vendor.packaging.utils import canonicalize_name

from controllergate.reactions.stable_identity import stable_hash


def normalize_requirement(value: str) -> tuple[str | None, bool]:
    try:
        requirement = Requirement(value)
    except InvalidRequirement:
        return None, False
    applies = requirement.marker is None or requirement.marker.evaluate({"extra": ""})
    return (canonicalize_name(requirement.name) if applies else None), True


def graph_from_wheels(wheel_dir: Path) -> dict[str, Any]:
    nodes: dict[str, dict[str, object]] = {}
    for wheel in sorted(wheel_dir.glob("*.whl")):
        with zipfile.ZipFile(wheel) as archive:
            metadata_name = next((name for name in archive.namelist() if name.endswith(".dist-info/METADATA")), None)
            if not metadata_name:
                continue
            metadata = email.message_from_bytes(archive.read(metadata_name))
        name = canonicalize_name(str(metadata.get("Name", wheel.name)))
        requires = []
        invalid = []
        skipped_by_marker = []
        for raw_requirement in metadata.get_all("Requires-Dist", []):
            normalized, valid = normalize_requirement(raw_requirement)
            if not valid:
                invalid.append(raw_requirement)
            elif normalized is None:
                skipped_by_marker.append(raw_requirement)
            else:
                requires.append(normalized)
        nodes[name] = {"version": metadata.get("Version"), "wheel": wheel.name,
                       "requires": sorted(set(requires)), "invalid_requirements": invalid,
                       "requirements_skipped_by_environment_marker": skipped_by_marker}
    missing = sorted({dep for node in nodes.values() for dep in node["requires"] if dep and dep not in nodes})
    value: dict[str, Any] = {"nodes": nodes, "wheel_count": len(nodes), "missing_runtime_dependencies": missing,
                             "invalid_requirement_count": sum(len(node["invalid_requirements"]) for node in nodes.values()),
                             "state": "PROVIDER_DEPENDENCY_GRAPH_CLOSED" if not missing else "BLOCKED_REQUIRED_INPUT_ABSENT"}
    value["graph_hash"] = stable_hash(value)
    return value
