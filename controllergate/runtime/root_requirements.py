from __future__ import annotations

import hashlib
from pathlib import Path
import tomllib
from typing import Any

from packaging.requirements import Requirement


def _poetry_constraint(value: str) -> str:
    if value.startswith("^"):
        version = value[1:]
        parts = [int(item) for item in version.split(".")]
        while len(parts) < 3:
            parts.append(0)
        if parts[0] != 0:
            upper = f"{parts[0] + 1}.0.0"
        elif parts[1] != 0:
            upper = f"0.{parts[1] + 1}.0"
        else:
            upper = f"0.0.{parts[2] + 1}"
        return f">={version},<{upper}"
    if value.startswith("~") and not value.startswith("~="):
        return f"~={value[1:]}"
    return value


def reconstruct_roots(source_root: Path) -> dict[str, Any]:
    pyproject = source_root / "pyproject.toml"
    payload = pyproject.read_bytes(); data = tomllib.loads(payload.decode("utf-8")); source_hash = hashlib.sha256(payload).hexdigest(); records = []
    groups = [("runtime", data.get("project", {}).get("dependencies", []), "project.dependencies"), ("test", data.get("project", {}).get("optional-dependencies", {}).get("test", []), "project.optional-dependencies.test"), ("build", data.get("build-system", {}).get("requires", []), "build-system.requires")]
    poetry = data.get("tool", {}).get("poetry", {})
    poetry_runtime = []
    for name, constraint in poetry.get("dependencies", {}).items():
        if name.lower() == "python":
            continue
        value = constraint if isinstance(constraint, str) else constraint.get("version", "")
        value = _poetry_constraint(value)
        extras = constraint.get("extras", []) if isinstance(constraint, dict) else []
        requirement_name = f"{name}[{','.join(extras)}]" if extras else name
        poetry_runtime.append(f"{requirement_name}{value}" if value and value[0] in "<>=!~" else f"{requirement_name}=={value}" if value else requirement_name)
    poetry_tests = []
    for name, constraint in poetry.get("group", {}).get("tests", {}).get("dependencies", {}).items():
        value = constraint if isinstance(constraint, str) else constraint.get("version", "")
        value = _poetry_constraint(value)
        poetry_tests.append(f"{name}{value}" if value and value[0] in "<>=!~" else f"{name}=={value}" if value else name)
    groups.extend([("runtime", poetry_runtime, "tool.poetry.dependencies"), ("test", poetry_tests, "tool.poetry.group.tests.dependencies")])
    for dependency_class, values, location in groups:
        for index, raw in enumerate(values):
            parsed = Requirement(raw)
            records.append({"dependency_class": dependency_class, "source_file": "pyproject.toml", "source_hash": source_hash, "source_location": f"{location}[{index}]", "raw_requirement": raw, "normalized_requirement": str(parsed), "name": parsed.name, "specifier": str(parsed.specifier), "extra": sorted(parsed.extras), "marker": str(parsed.marker) if parsed.marker else None})
    return {"status": "PASS", "source_sha256": source_hash, "records": records, "runtime_roots": [item for item in records if item["dependency_class"] == "runtime"], "test_roots": [item for item in records if item["dependency_class"] == "test"], "build_roots": [item for item in records if item["dependency_class"] == "build"], "system_dependencies": []}
