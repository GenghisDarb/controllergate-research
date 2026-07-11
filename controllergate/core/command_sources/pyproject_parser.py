from __future__ import annotations

from pathlib import Path
import tomllib
from typing import Any


def parse_pyproject(path: Path) -> dict[str, Any]:
    value = tomllib.loads(path.read_text(encoding="utf-8")); tool = value.get("tool", {})
    return {
        "status": "PASS", "source_path": path.as_posix(),
        "pytest_options": tool.get("pytest", {}).get("ini_options", {}),
        "poetry_test_dependencies": tool.get("poetry", {}).get("group", {}).get("tests", {}).get("dependencies", {}),
        "project_dependencies": value.get("project", {}).get("dependencies", []),
    }
