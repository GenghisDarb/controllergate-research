from __future__ import annotations

import hashlib
from pathlib import Path
import tomllib
from typing import Any

from packaging.requirements import Requirement


def reconstruct_roots(source_root: Path) -> dict[str, Any]:
    pyproject = source_root / "pyproject.toml"
    payload = pyproject.read_bytes(); data = tomllib.loads(payload.decode("utf-8")); source_hash = hashlib.sha256(payload).hexdigest(); records = []
    groups = [("runtime", data.get("project", {}).get("dependencies", []), "project.dependencies"), ("test", data.get("project", {}).get("optional-dependencies", {}).get("test", []), "project.optional-dependencies.test"), ("build", data.get("build-system", {}).get("requires", []), "build-system.requires")]
    for dependency_class, values, location in groups:
        for index, raw in enumerate(values):
            parsed = Requirement(raw)
            records.append({"dependency_class": dependency_class, "source_file": "pyproject.toml", "source_hash": source_hash, "source_location": f"{location}[{index}]", "raw_requirement": raw, "normalized_requirement": str(parsed), "name": parsed.name, "specifier": str(parsed.specifier), "extra": sorted(parsed.extras), "marker": str(parsed.marker) if parsed.marker else None})
    return {"status": "PASS", "source_sha256": source_hash, "records": records, "runtime_roots": [item for item in records if item["dependency_class"] == "runtime"], "test_roots": [item for item in records if item["dependency_class"] == "test"], "build_roots": [item for item in records if item["dependency_class"] == "build"], "system_dependencies": []}
