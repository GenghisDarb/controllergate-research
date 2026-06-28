from __future__ import annotations

import subprocess
from pathlib import Path


def run_command_with_timeout(command: list[str], cwd: str | Path, timeout: int = 120) -> dict[str, object]:
    try:
        result = subprocess.run(command, cwd=str(cwd), text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout, check=False)
        return {"command": command, "returncode": result.returncode, "timed_out": False, "stdout": result.stdout, "stderr": result.stderr}
    except subprocess.TimeoutExpired as exc:
        return {"command": command, "returncode": None, "timed_out": True, "stdout": exc.stdout or "", "stderr": exc.stderr or ""}
