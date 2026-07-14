from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import venv
from pathlib import Path


def python_in(venv_root: Path) -> Path:
    return venv_root / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def offline_install(wheel_dir: Path, roots: list[str], environment: Path, *, timeout: int = 600) -> dict[str, object]:
    if environment.exists():
        import shutil
        shutil.rmtree(environment)
    venv.EnvBuilder(with_pip=True, clear=True).create(environment)
    python = python_in(environment)
    command = [str(python), "-m", "pip", "install", "--no-index", "--find-links", str(wheel_dir), *roots]
    result = subprocess.run(command, text=True, capture_output=True, timeout=timeout,
                            env={**os.environ, "PIP_NO_INDEX": "1", "PIP_DISABLE_PIP_VERSION_CHECK": "1"})
    raw = (result.stdout + result.stderr).encode()
    return {"state": "PROVIDER_OFFLINE_INSTALL_PASSED" if result.returncode == 0 else "BLOCKED_REQUIRED_INPUT_ABSENT",
            "returncode": result.returncode, "command": command, "log_hash": hashlib.sha256(raw).hexdigest(),
            "log_tail": raw.decode(errors="replace")[-2000:], "environment": str(environment)}


def pip_check(environment: Path) -> dict[str, object]:
    result = subprocess.run([str(python_in(environment)), "-m", "pip", "check"], text=True, capture_output=True)
    raw = (result.stdout + result.stderr).encode()
    return {"state": "PROVIDER_DEPENDENCY_CHECK_PASSED" if result.returncode == 0 else "BLOCK",
            "returncode": result.returncode, "log_hash": hashlib.sha256(raw).hexdigest()}
