from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path

from .provider_offline_installer import python_in


def import_probe(environment: Path, modules: list[str]) -> dict[str, object]:
    script = ";".join(f"import {name}" for name in modules)
    result = subprocess.run([str(python_in(environment)), "-c", script], text=True, capture_output=True)
    raw = (result.stdout + result.stderr).encode()
    return {"state": "PROVIDER_IMPORT_PROBE_PASSED" if result.returncode == 0 else "BLOCK",
            "modules": modules, "returncode": result.returncode, "log_hash": hashlib.sha256(raw).hexdigest()}


def entrypoint_probe(environment: Path, commands: list[list[str]]) -> dict[str, object]:
    records = []
    for command in commands:
        result = subprocess.run(command, text=True, capture_output=True)
        records.append({"command": command, "returncode": result.returncode,
                        "log_hash": hashlib.sha256((result.stdout + result.stderr).encode()).hexdigest()})
    return {"state": "PROVIDER_ENTRYPOINT_PROBE_PASSED" if records and all(r["returncode"] == 0 for r in records) else "BLOCK",
            "records": records}
