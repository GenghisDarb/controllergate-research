from __future__ import annotations

import ast
from pathlib import Path
import re
import tomllib
from typing import Any

from packaging.requirements import InvalidRequirement, Requirement


def _normalize(value: str) -> str:
    return re.sub(r"[-_.]+", "_", value).lower()


def _imports(path: Path) -> set[str]:
    if not path.is_file() or path.suffix != ".py":
        return set()
    try:
        tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
    except SyntaxError:
        return set()
    values: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            values.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            values.add(node.module.split(".", 1)[0])
    return values


def _declared_name(value: str) -> str | None:
    try:
        return _normalize(Requirement(value).name)
    except (InvalidRequirement, ValueError):
        return None


def analyze_target_dependencies(source: Path, target: str) -> dict[str, Any]:
    target_file = target.split("::", 1)[0]
    target_path = source / target_file
    conftests = list(target_path.parent.parents) if target_path.parent != source else []
    conftest_paths = [path / "conftest.py" for path in [target_path.parent, *conftests] if source in (path, *path.parents)]
    graph: dict[str, list[str]] = {target_file: sorted(_imports(target_path))}
    for path in conftest_paths:
        if path.is_file():
            graph[path.relative_to(source).as_posix()] = sorted(_imports(path))
    imports = {_normalize(value) for values in graph.values() for value in values}
    optional: dict[str, list[str]] = {}
    project_dependencies: list[str] = []
    pyproject = source / "pyproject.toml"
    if pyproject.is_file():
        try:
            project = tomllib.loads(pyproject.read_text(encoding="utf-8")).get("project", {})
            optional = {str(key): [str(value) for value in values] for key, values in project.get("optional-dependencies", {}).items()}
            project_dependencies = [str(value) for value in project.get("dependencies", [])]
        except (OSError, tomllib.TOMLDecodeError, AttributeError, TypeError):
            pass
    selected: list[str] = []
    rejected: list[dict[str, str]] = []
    basis: dict[str, list[str]] = {}
    target_text = target_path.read_text(encoding="utf-8", errors="replace") if target_path.is_file() else ""
    for extra, requirements in sorted(optional.items()):
        names = {name for value in requirements if (name := _declared_name(value))}
        matches = sorted(names & imports)
        test_client_basis = _normalize(extra) in {"dev", "test", "tests", "testing"} and "testclient" in target_text.lower()
        test_runner_basis = _normalize(extra) in {"dev", "test", "tests", "testing"} and "pytest" in names
        if matches or test_client_basis or test_runner_basis:
            selected.append(extra)
            reasons = [f"declared dependency matches import: {value}" for value in matches]
            if test_client_basis:
                reasons.append("target uses a test client and the declared test/development extra supplies its runtime")
            if test_runner_basis:
                reasons.append("declared test/development extra supplies the authoritative test runner")
            basis[extra] = reasons
        else:
            rejected.append({"extra": extra, "reason": "no target, fixture, or test-runtime dependency basis"})
    requirement_files = [
        name
        for name in ("requirements.txt", "requirements-test.txt", "test-requirements.txt", "requirements-dev.txt")
        if (source / name).is_file()
    ]
    return {
        "target": target,
        "target_import_graph": graph,
        "fixture_import_graph": {key: value for key, value in graph.items() if key.endswith("conftest.py")},
        "normalized_imports": sorted(imports),
        "project_dependencies": project_dependencies,
        "declared_optional_dependencies": optional,
        "selected_extras": selected,
        "rejected_extras": rejected,
        "dependency_basis": basis,
        "requirement_files": requirement_files,
        "independent_verification": "PASS" if target_path.is_file() else "BLOCK_TARGET_MISSING",
    }
