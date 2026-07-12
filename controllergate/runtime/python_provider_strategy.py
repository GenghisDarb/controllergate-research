from __future__ import annotations

from pathlib import Path
import tomllib
from typing import Any


def classify_python_source_layout(source: Path) -> dict[str, Any]:
    pyproject = source / "pyproject.toml"
    build_system: dict[str, Any] = {}
    project: dict[str, Any] = {}
    if pyproject.is_file():
        try:
            data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
            build_system = data.get("build-system", {}) if isinstance(data, dict) else {}
            project = data.get("project", {}) if isinstance(data, dict) else {}
        except (OSError, tomllib.TOMLDecodeError):
            pass
    legacy_build = (source / "setup.py").is_file() or (source / "setup.cfg").is_file()
    valid_build = bool(build_system.get("build-backend") and build_system.get("requires")) or legacy_build
    test_imports_source = (source / "tests").is_dir() and any(source.glob("*.py"))
    package_dirs = [path for path in source.iterdir() if path.is_dir() and (path / "__init__.py").is_file() and not path.name.startswith(".")]
    if valid_build and test_imports_source:
        classification = "hybrid_project"
    elif valid_build:
        classification = "buildable_python_package"
    elif (source / "tests").is_dir() and (package_dirs or any(source.glob("*.py"))):
        classification = "source_on_pythonpath"
    else:
        classification = "unsupported_layout"
    return {
        "classification": classification,
        "pyproject_present": pyproject.is_file(),
        "build_system_declared": bool(build_system),
        "build_backend": build_system.get("build-backend"),
        "legacy_build_method": legacy_build,
        "project_metadata_present": bool(project),
        "package_roots": [path.name for path in package_dirs],
        "source_on_pythonpath": classification == "source_on_pythonpath",
        "project_wheel_allowed": classification in {"buildable_python_package", "hybrid_project"},
    }


def provider_strategy(source: Path, target: str, dependency_analysis: dict[str, Any]) -> dict[str, Any]:
    layout = classify_python_source_layout(source)
    strategy = "build_project_wheel" if layout["project_wheel_allowed"] else "source_on_pythonpath" if layout["source_on_pythonpath"] else "unsupported"
    return {
        **layout,
        "strategy": strategy,
        "target": target,
        "selected_extras": dependency_analysis.get("selected_extras", []),
        "requirement_files": dependency_analysis.get("requirement_files", []),
        "candidate_source_mount": "read_only",
        "candidate_import_mode": "installed_wheel" if strategy == "build_project_wheel" else "explicit_PYTHONPATH" if strategy == "source_on_pythonpath" else "none",
    }
