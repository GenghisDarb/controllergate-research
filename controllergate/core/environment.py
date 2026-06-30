from __future__ import annotations

import configparser
import hashlib
import os
import re
import subprocess
import sys
import tempfile
import venv
from pathlib import Path
from typing import Callable

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python <3.11 fallback
    tomllib = None  # type: ignore[assignment]

CommandRunner = Callable[..., subprocess.CompletedProcess[str]]

ENVIRONMENT_FILE_NAMES = [
    "pyproject.toml",
    "setup.cfg",
    "setup.py",
    "tox.ini",
    "requirements.txt",
    "requirements-dev.txt",
    "requirements-test.txt",
    "requirements_tests.txt",
    "pytest.ini",
]

INSTALL_STRATEGY_ORDER = [
    "editable_test_extra",
    "editable_tests_extra",
    "editable_dev_extra",
    "editable_project",
    "declared_requirements",
    "baseline_pytest_tooling",
]


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def detect_environment_lock_source(root: str | Path) -> list[str]:
    return [name for name in ENVIRONMENT_FILE_NAMES if (Path(root) / name).is_file()]


def create_venv(path: str | Path) -> Path:
    venv.EnvBuilder(with_pip=True, clear=True).create(path)
    return Path(path)


def venv_python(path: str | Path) -> Path:
    root = Path(path)
    if os.name == "nt":
        return root / "Scripts" / "python.exe"
    return root / "bin" / "python"


def _run_command(
    command: list[str],
    cwd: Path | None = None,
    timeout_seconds: int = 300,
    command_runner: CommandRunner | None = None,
) -> subprocess.CompletedProcess[str]:
    runner = command_runner or subprocess.run
    return runner(command, cwd=str(cwd) if cwd else None, text=True, capture_output=True, timeout=timeout_seconds)


def _normalize_text(text: str, checkout: Path | None = None, venv_root: Path | None = None) -> str:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    replacements: list[tuple[str, str]] = []
    if checkout is not None:
        replacements.extend(
            [
                (str(checkout), "<lead_workspace>"),
                (str(checkout).replace("\\", "/"), "<lead_workspace>"),
                (str(checkout.parent), "<runtime_workspace>"),
                (str(checkout.parent).replace("\\", "/"), "<runtime_workspace>"),
            ]
        )
    if venv_root is not None:
        replacements.extend(
            [
                (str(venv_root), "<lead_venv>"),
                (str(venv_root).replace("\\", "/"), "<lead_venv>"),
                (str(venv_root.parent), "<runtime_workspace>"),
                (str(venv_root.parent).replace("\\", "/"), "<runtime_workspace>"),
            ]
        )
    temp_root = Path(tempfile.gettempdir())
    replacements.extend(
        [
            (str(temp_root), "<system_temp>"),
            (str(temp_root).replace("\\", "/"), "<system_temp>"),
        ]
    )
    replacements.extend(
        [
            (sys.executable, "<python_executable>"),
            (sys.executable.replace("\\", "/"), "<python_executable>"),
            (str(Path(sys.base_prefix)), "<python_runtime>"),
            (str(Path(sys.base_prefix)).replace("\\", "/"), "<python_runtime>"),
            (str(Path(sys.prefix)), "<python_runtime>"),
            (str(Path(sys.prefix)).replace("\\", "/"), "<python_runtime>"),
        ]
    )
    for source, target in sorted(replacements, key=lambda item: len(item[0]), reverse=True):
        normalized = normalized.replace(source, target)
    return "\n".join(line.rstrip() for line in normalized.splitlines())


def scrub_command(command: list[str], checkout: Path | None = None, venv_root: Path | None = None) -> list[str]:
    scrubbed: list[str] = []
    for item in command:
        value = item
        for source, target in [
            (sys.executable, "<python_executable>"),
            (sys.executable.replace("\\", "/"), "<python_executable>"),
        ]:
            value = value.replace(source, target)
        if checkout is not None:
            value = value.replace(str(checkout), "<lead_workspace>")
            value = value.replace(str(checkout).replace("\\", "/"), "<lead_workspace>")
            value = value.replace(str(checkout.parent), "<runtime_workspace>")
            value = value.replace(str(checkout.parent).replace("\\", "/"), "<runtime_workspace>")
        if venv_root is not None:
            value = value.replace(str(venv_root), "<lead_venv>")
            value = value.replace(str(venv_root).replace("\\", "/"), "<lead_venv>")
            value = value.replace(str(venv_root.parent), "<runtime_workspace>")
            value = value.replace(str(venv_root.parent).replace("\\", "/"), "<runtime_workspace>")
        scrubbed.append(value)
    return scrubbed


def command_record(
    command: list[str],
    completed: subprocess.CompletedProcess[str],
    checkout: Path | None = None,
    venv_root: Path | None = None,
) -> dict[str, object]:
    combined = f"STDOUT:\n{completed.stdout or ''}\nSTDERR:\n{completed.stderr or ''}"
    normalized = _normalize_text(combined, checkout=checkout, venv_root=venv_root)
    return {
        "command": scrub_command(command, checkout=checkout, venv_root=venv_root),
        "returncode": completed.returncode,
        "output_sha256": sha256_text(combined),
        "normalized_output_sha256": sha256_text(normalized),
        "output_summary": normalized[:1200],
    }


def _parse_pyproject(root: Path) -> dict[str, object]:
    path = root / "pyproject.toml"
    if not path.is_file():
        return {"dependencies": [], "optional_groups": [], "optional_dependencies_by_group": {}, "dependency_groups": {}}
    text = path.read_text(encoding="utf-8")
    if tomllib is None:
        dependencies = _fallback_pyproject_dependencies(text)
        optional_by_group = _fallback_pyproject_optional_dependencies_by_group(text)
        dependency_groups = _fallback_pyproject_dependency_groups(text)
        return {
            "dependencies": dependencies,
            "optional_groups": sorted(optional_by_group),
            "optional_dependencies_by_group": optional_by_group,
            "dependency_groups": dependency_groups,
        }
    try:
        data = tomllib.loads(text)
    except Exception:
        return {"dependencies": [], "optional_groups": [], "optional_dependencies_by_group": {}, "dependency_groups": {}}
    project = data.get("project", {}) if isinstance(data, dict) else {}
    dependencies = project.get("dependencies", []) if isinstance(project, dict) else []
    optional = project.get("optional-dependencies", {}) if isinstance(project, dict) else {}
    optional_by_group = {
        str(key): [str(item) for item in value]
        for key, value in optional.items()
        if isinstance(key, str) and isinstance(value, list)
    } if isinstance(optional, dict) else {}
    dependency_groups_raw = data.get("dependency-groups", {}) if isinstance(data, dict) else {}
    dependency_groups = {
        str(key): [str(item) for item in value]
        for key, value in dependency_groups_raw.items()
        if isinstance(key, str) and isinstance(value, list)
    } if isinstance(dependency_groups_raw, dict) else {}
    return {
        "dependencies": dependencies if isinstance(dependencies, list) else [],
        "optional_groups": sorted(optional_by_group),
        "optional_dependencies_by_group": optional_by_group,
        "dependency_groups": dependency_groups,
    }


def _fallback_pyproject_dependencies(text: str) -> list[str]:
    """Extract simple PEP 621 dependency arrays when tomllib is unavailable."""
    match = re.search(r"(?ms)^\s*dependencies\s*=\s*\[(.*?)\]", text)
    if not match:
        return []
    return [item for item in re.findall(r"""["']([^"']+)["']""", match.group(1)) if item.strip()]


def _fallback_pyproject_optional_groups(text: str) -> list[str]:
    return sorted(_fallback_pyproject_optional_dependencies_by_group(text))


def _fallback_pyproject_optional_dependencies_by_group(text: str) -> dict[str, list[str]]:
    groups = re.findall(r"(?m)^\s*\[project\.optional-dependencies\]\s*$([\s\S]*?)(?=^\s*\[|\Z)", text)
    if not groups:
        return {}
    result: dict[str, list[str]] = {}
    for group, raw in re.findall(r"(?ms)^\s*([A-Za-z0-9_.-]+)\s*=\s*\[(.*?)\]", groups[0]):
        result[group] = [item for item in re.findall(r"""["']([^"']+)["']""", raw) if item.strip()]
    return result


def _fallback_pyproject_dependency_groups(text: str) -> dict[str, list[str]]:
    groups = re.findall(r"(?m)^\s*\[dependency-groups\]\s*$([\s\S]*?)(?=^\s*\[|\Z)", text)
    if not groups:
        return {}
    result: dict[str, list[str]] = {}
    for group, raw in re.findall(r"(?ms)^\s*([A-Za-z0-9_.-]+)\s*=\s*\[(.*?)\]", groups[0]):
        result[group] = [item for item in re.findall(r"""["']([^"']+)["']""", raw) if item.strip()]
    return result


def _parse_setup_cfg(root: Path) -> dict[str, object]:
    path = root / "setup.cfg"
    if not path.is_file():
        return {"dependencies": [], "optional_groups": [], "optional_dependencies_by_group": {}}
    parser = configparser.ConfigParser()
    try:
        parser.read(path, encoding="utf-8")
    except Exception:
        return {"dependencies": [], "optional_groups": [], "optional_dependencies_by_group": {}}
    dependencies: list[str] = []
    if parser.has_option("options", "install_requires"):
        dependencies.extend(line.strip() for line in parser.get("options", "install_requires").splitlines() if line.strip())
    optional_by_group: dict[str, list[str]] = {}
    prefix = "options.extras_require"
    if parser.has_section(prefix):
        for group in parser.options(prefix):
            optional_by_group[group] = [line.strip() for line in parser.get(prefix, group).splitlines() if line.strip()]
    return {"dependencies": dependencies, "optional_groups": sorted(optional_by_group), "optional_dependencies_by_group": optional_by_group}


def _parse_requirements(root: Path) -> list[str]:
    requirements: list[str] = []
    for name in ["requirements.txt", "requirements-dev.txt", "requirements-test.txt", "requirements_tests.txt"]:
        path = root / name
        if path.is_file():
            for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
                stripped = line.strip()
                if stripped and not stripped.startswith("#") and not stripped.startswith("-r "):
                    requirements.append(stripped)
    return requirements


def project_metadata_summary(root: str | Path) -> dict[str, object]:
    checkout = Path(root)
    pyproject = _parse_pyproject(checkout)
    setup_cfg = _parse_setup_cfg(checkout)
    requirements = _parse_requirements(checkout)
    optional_groups = sorted(set(pyproject["optional_groups"]) | set(setup_cfg["optional_groups"]))
    optional_by_group = {}
    optional_by_group.update(pyproject.get("optional_dependencies_by_group", {}))
    optional_by_group.update(setup_cfg.get("optional_dependencies_by_group", {}))
    dependency_groups = pyproject.get("dependency_groups", {})
    dependencies = (
        list(pyproject["dependencies"])
        + list(setup_cfg["dependencies"])
        + [item for values in optional_by_group.values() for item in values]
        + [item for values in dependency_groups.values() for item in values] if isinstance(dependency_groups, dict) else []
    ) + requirements
    return {
        "environment_files": detect_environment_lock_source(checkout),
        "optional_dependency_groups": optional_groups,
        "optional_dependencies_by_group": optional_by_group,
        "dependency_groups": dependency_groups if isinstance(dependency_groups, dict) else {},
        "declared_dependency_strings": dependencies,
        "requirements_files": [name for name in ["requirements.txt", "requirements-dev.txt", "requirements-test.txt", "requirements_tests.txt"] if (checkout / name).is_file()],
    }


def dependency_declared(module_name: str, metadata: dict[str, object]) -> bool:
    target = module_name.replace("_", "-").lower()
    for raw in metadata.get("declared_dependency_strings", []):
        text = str(raw).lower().replace("_", "-")
        if re.split(r"[<>=!~;\\[]", text, maxsplit=1)[0].strip() == target:
            return True
    return False


def infer_project_imports(root: str | Path, repo_name: str | None = None) -> list[str]:
    checkout = Path(root)
    candidates: list[str] = []
    if repo_name:
        candidates.append(repo_name.split("/")[-1].replace("-", "_"))
    src = checkout / "src"
    if src.is_dir():
        candidates.extend(path.name for path in src.iterdir() if path.is_dir() and (path / "__init__.py").is_file())
    candidates.extend(path.name for path in checkout.iterdir() if path.is_dir() and (path / "__init__.py").is_file())
    return sorted({item for item in candidates if item and item not in {"tests", "test"}})


def extract_missing_modules(text: str) -> list[str]:
    modules = set(re.findall(r"No module named ['\"]([^'\"]+)['\"]", text))
    return sorted(module.split(".")[0] for module in modules)


def build_install_strategies(root: str | Path, python: str | Path) -> list[dict[str, object]]:
    checkout = Path(root)
    py = str(python)
    strategies: list[dict[str, object]] = [
        {"strategy": "editable_test_extra", "command": [py, "-m", "pip", "install", "-e", ".[test]"], "supported": (checkout / "pyproject.toml").is_file() or (checkout / "setup.cfg").is_file() or (checkout / "setup.py").is_file()},
        {"strategy": "editable_tests_extra", "command": [py, "-m", "pip", "install", "-e", ".[tests]"], "supported": (checkout / "pyproject.toml").is_file() or (checkout / "setup.cfg").is_file() or (checkout / "setup.py").is_file()},
        {"strategy": "editable_dev_extra", "command": [py, "-m", "pip", "install", "-e", ".[dev]"], "supported": (checkout / "pyproject.toml").is_file() or (checkout / "setup.cfg").is_file() or (checkout / "setup.py").is_file()},
        {"strategy": "editable_project", "command": [py, "-m", "pip", "install", "-e", "."], "supported": (checkout / "pyproject.toml").is_file() or (checkout / "setup.cfg").is_file() or (checkout / "setup.py").is_file()},
    ]
    for name in ["requirements.txt", "requirements-dev.txt", "requirements-test.txt", "requirements_tests.txt"]:
        path = checkout / name
        strategies.append({"strategy": f"requirements:{name}", "command": [py, "-m", "pip", "install", "-r", name], "supported": path.is_file()})
    if not any(item["supported"] for item in strategies):
        strategies.append({"strategy": "baseline_pytest_tooling", "command": [py, "-m", "pip", "install", "pytest"], "supported": True})
    return strategies


def _extra_missing(record: dict[str, object]) -> bool:
    text = str(record.get("output_summary", "")).lower()
    return "does not provide the extra" in text or "unknown extra" in text


def resolve_project_environment(
    checkout: str | Path,
    venv_root: str | Path,
    repo_name: str | None = None,
    command_runner: CommandRunner | None = None,
) -> dict[str, object]:
    checkout_path = Path(checkout)
    venv_path = Path(venv_root)
    create_venv(venv_path)
    python = venv_python(venv_path)
    metadata = project_metadata_summary(checkout_path)
    install_strategy_attempts: list[dict[str, object]] = []
    install_log_hashes: list[dict[str, object]] = []
    upgrade_command = [str(python), "-m", "pip", "install", "-U", "pip", "setuptools", "wheel"]
    upgrade_result = _run_command(upgrade_command, cwd=checkout_path, timeout_seconds=300, command_runner=command_runner)
    upgrade_record = command_record(upgrade_command, upgrade_result, checkout=checkout_path, venv_root=venv_path)
    install_strategy_attempts.append({"strategy": "upgrade_build_tools", "supported": True, "status": "PASS" if upgrade_result.returncode == 0 else "FAIL", **upgrade_record})
    install_log_hashes.append({"strategy": "upgrade_build_tools", "normalized_output_sha256": upgrade_record["normalized_output_sha256"]})
    if upgrade_result.returncode != 0:
        return {
            "status": "FAILED",
            "blocker": "environment_dependency_install_failed",
            "venv_created": True,
            "venv_path": "<lead_venv>",
            "metadata": metadata,
            "install_strategy_attempts": install_strategy_attempts,
            "selected_install_strategy": None,
            "install_log_hashes": install_log_hashes,
            "import_probe_attempted": False,
            "import_probe_status": "NOT_RUN",
            "import_probe_results": [],
        }
    selected: str | None = None
    for strategy in build_install_strategies(checkout_path, python):
        if not strategy["supported"]:
            install_strategy_attempts.append({"strategy": strategy["strategy"], "supported": False, "status": "SKIPPED_UNSUPPORTED"})
            continue
        result = _run_command(list(strategy["command"]), cwd=checkout_path, timeout_seconds=420, command_runner=command_runner)
        record = command_record(list(strategy["command"]), result, checkout=checkout_path, venv_root=venv_path)
        status = "PASS" if result.returncode == 0 else "FAIL"
        if str(strategy["strategy"]).startswith("editable_") and str(strategy["strategy"]).endswith("_extra") and _extra_missing(record):
            status = "EXTRA_MISSING"
        attempt = {"strategy": strategy["strategy"], "supported": True, "status": status, **record}
        install_strategy_attempts.append(attempt)
        install_log_hashes.append({"strategy": strategy["strategy"], "normalized_output_sha256": record["normalized_output_sha256"]})
        if status == "PASS":
            selected = str(strategy["strategy"])
            break
    import_results: list[dict[str, object]] = []
    for module in infer_project_imports(checkout_path, repo_name=repo_name):
        command = [str(python), "-c", f"import {module}"]
        result = _run_command(command, cwd=checkout_path, timeout_seconds=60, command_runner=command_runner)
        import_results.append({"module": module, "status": "PASS" if result.returncode == 0 else "FAIL", **command_record(command, result, checkout=checkout_path, venv_root=venv_path)})
    import_probe_status = "PASS" if import_results and all(item["status"] == "PASS" for item in import_results) else ("FAIL" if import_results else "NO_MODULES_DISCOVERED")
    if selected is None:
        blocker = "environment_declared_extra_missing" if any(item.get("status") == "EXTRA_MISSING" for item in install_strategy_attempts) else "environment_dependency_install_failed"
    elif any(item["status"] == "FAIL" for item in import_results):
        blocker = "environment_editable_install_failed"
    else:
        blocker = None
    return {
        "status": "PASS" if blocker is None else "FAILED",
        "blocker": blocker,
        "venv_created": True,
        "venv_path": "<lead_venv>",
        "metadata": metadata,
        "install_strategy_attempts": install_strategy_attempts,
        "selected_install_strategy": selected,
        "install_log_hashes": install_log_hashes,
        "import_probe_attempted": bool(import_results),
        "import_probe_status": import_probe_status,
        "import_probe_results": import_results,
        "python": "<lead_venv_python>",
    }


def install_from_project_metadata(root: str | Path, python: str | Path) -> dict[str, object]:
    result = subprocess.run([str(python), "-m", "pip", "install", "-e", "."], cwd=str(root), text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    return {"returncode": result.returncode, "stdout_sha256": sha256_text(result.stdout), "stderr_sha256": sha256_text(result.stderr)}


def record_dependency_plan(root: str | Path) -> dict[str, object]:
    return {"environment_files": detect_environment_lock_source(root), "undeclared_dependency_install": False}


def classify_environment_failure(text: str) -> str:
    markers = ["ModuleNotFoundError", "No module named", "ImportError", "DistributionNotFound"]
    return "environment_failure" if any(marker in text for marker in markers) else "not_environment_only"
