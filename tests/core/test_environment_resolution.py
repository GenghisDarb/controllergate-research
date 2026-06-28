from __future__ import annotations

import json
import subprocess
from pathlib import Path

import controllergate.core.environment as environment
from controllergate.core.environment import build_install_strategies, dependency_declared, extract_missing_modules, project_metadata_summary, resolve_project_environment


def test_declared_extras_are_attempted_before_editable_project(tmp_path):
    (tmp_path / "pyproject.toml").write_text(
        "[build-system]\nrequires = [\"setuptools\"]\nbuild-backend = \"setuptools.build_meta\"\n\n[project]\nname = \"demo\"\nversion = \"0.0.0\"\n\n[project.optional-dependencies]\ntest = [\"pytest\"]\ndev = [\"pytest\"]\n",
        encoding="utf-8",
        newline="\n",
    )
    strategies = build_install_strategies(tmp_path, "python")

    assert [item["strategy"] for item in strategies[:4]] == [
        "editable_test_extra",
        "editable_tests_extra",
        "editable_dev_extra",
        "editable_project",
    ]


def test_dependency_declaration_and_missing_module_parsing(tmp_path):
    (tmp_path / "pyproject.toml").write_text(
        "[project]\nname = \"demo\"\nversion = \"0.0.0\"\ndependencies = [\"darkgraylib>=1\"]\n",
        encoding="utf-8",
        newline="\n",
    )
    metadata = project_metadata_summary(tmp_path)

    assert dependency_declared("darkgraylib", metadata)
    assert extract_missing_modules("ModuleNotFoundError: No module named 'darkgraylib.utils'") == ["darkgraylib"]


def test_pyproject_dependency_fallback_when_tomllib_unavailable(tmp_path, monkeypatch):
    (tmp_path / "pyproject.toml").write_text(
        "[project]\nname = \"demo\"\nversion = \"0.0.0\"\ndependencies = [\"darkgraylib>=1\"]\n\n[project.optional-dependencies]\ntest = [\"pytest\"]\n",
        encoding="utf-8",
        newline="\n",
    )
    monkeypatch.setattr(environment, "tomllib", None)

    metadata = environment.project_metadata_summary(tmp_path)

    assert environment.dependency_declared("darkgraylib", metadata)
    assert metadata["optional_dependency_groups"] == ["test"]


def test_resolver_records_editable_install_attempt(tmp_path):
    package_dir = tmp_path / "src" / "demo_pkg"
    package_dir.mkdir(parents=True)
    (package_dir / "__init__.py").write_text("VALUE = 1\n", encoding="utf-8", newline="\n")
    (tmp_path / "pyproject.toml").write_text(
        "[build-system]\nrequires = [\"setuptools\"]\nbuild-backend = \"setuptools.build_meta\"\n\n[project]\nname = \"demo-pkg\"\nversion = \"0.0.0\"\n\n[tool.setuptools.packages.find]\nwhere = [\"src\"]\n",
        encoding="utf-8",
        newline="\n",
    )

    result = resolve_project_environment(tmp_path, tmp_path.parent / "demo_venv", repo_name="demo/demo_pkg")

    assert result["venv_created"] is True
    assert result["selected_install_strategy"] in {"editable_test_extra", "editable_tests_extra", "editable_dev_extra", "editable_project"}
    assert any(item["strategy"].startswith("editable_") for item in result["install_strategy_attempts"])
    assert result["import_probe_attempted"] is True
    assert result["import_probe_status"] == "PASS"
