from __future__ import annotations

import subprocess
import venv
from pathlib import Path


def detect_environment_lock_source(root: str | Path) -> list[str]:
    names = ["pyproject.toml", "setup.cfg", "setup.py", "tox.ini", "requirements.txt", "requirements-dev.txt"]
    return [name for name in names if (Path(root) / name).is_file()]


def create_venv(path: str | Path) -> Path:
    venv.EnvBuilder(with_pip=True, clear=True).create(path)
    return Path(path)


def install_from_project_metadata(root: str | Path, python: str | Path) -> dict[str, object]:
    result = subprocess.run([str(python), "-m", "pip", "install", "-e", "."], cwd=str(root), text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    return {"returncode": result.returncode, "stdout_sha256": __import__("hashlib").sha256(result.stdout.encode()).hexdigest(), "stderr_sha256": __import__("hashlib").sha256(result.stderr.encode()).hexdigest()}


def record_dependency_plan(root: str | Path) -> dict[str, object]:
    return {"environment_files": detect_environment_lock_source(root), "undeclared_dependency_install": False}


def classify_environment_failure(text: str) -> str:
    markers = ["ModuleNotFoundError", "No module named", "ImportError", "DistributionNotFound"]
    return "environment_failure" if any(marker in text for marker in markers) else "not_environment_only"
