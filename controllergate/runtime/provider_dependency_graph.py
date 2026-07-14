from __future__ import annotations

import email
import zipfile
from pathlib import Path
from typing import Any

from controllergate.reactions.stable_identity import stable_hash


def normalize_requirement(value: str) -> str:
    return value.split(";", 1)[0].strip().split("[", 1)[0].split(" ", 1)[0].split("(", 1)[0].lower().replace("_", "-")


def graph_from_wheels(wheel_dir: Path) -> dict[str, Any]:
    nodes: dict[str, dict[str, object]] = {}
    for wheel in sorted(wheel_dir.glob("*.whl")):
        with zipfile.ZipFile(wheel) as archive:
            metadata_name = next((name for name in archive.namelist() if name.endswith(".dist-info/METADATA")), None)
            if not metadata_name:
                continue
            metadata = email.message_from_bytes(archive.read(metadata_name))
        name = str(metadata.get("Name", wheel.name)).lower().replace("_", "-")
        requires = [normalize_requirement(value) for value in metadata.get_all("Requires-Dist", [])]
        nodes[name] = {"version": metadata.get("Version"), "wheel": wheel.name, "requires": requires}
    missing = sorted({dep for node in nodes.values() for dep in node["requires"] if dep and dep not in nodes})
    value: dict[str, Any] = {"nodes": nodes, "missing_runtime_dependencies": missing,
                             "state": "PROVIDER_DEPENDENCY_GRAPH_CLOSED" if not missing else "BLOCKED_REQUIRED_INPUT_ABSENT"}
    value["graph_hash"] = stable_hash(value)
    return value
