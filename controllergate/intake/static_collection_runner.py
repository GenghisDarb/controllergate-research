from __future__ import annotations

import hashlib
import shlex
import subprocess
from pathlib import Path
from typing import Any

from controllergate.core.evidence import hash_record


def run_static_collection(source_root: Path, command_record: dict[str, Any], target: str, *, timeout: int = 120) -> dict[str, Any]:
    selected = command_record.get("selected") or {}
    argv = list(selected.get("transformed_command") or ["python", "-m", "pytest", target])
    if "--collect-only" not in argv:
        argv.extend(["--collect-only", "-q"])
    try:
        run = subprocess.run(argv, cwd=source_root, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout, check=False)
        stdout, stderr, code = run.stdout, run.stderr, run.returncode
        timed_out = False
    except (OSError, subprocess.TimeoutExpired) as exc:
        stdout, stderr, code = "", str(exc), 124 if isinstance(exc, subprocess.TimeoutExpired) else 127
        timed_out = isinstance(exc, subprocess.TimeoutExpired)
    nodes = [line.strip() for line in stdout.splitlines() if "::" in line and not line.lstrip().startswith(("=", "<"))]
    record = {
        "status": "PASS" if code == 0 and nodes else "BLOCK",
        "command": shlex.join(argv),
        "returncode": code,
        "timed_out": timed_out,
        "nodes": nodes,
        "file_collection_pass": code == 0,
        "node_collection_pass": bool(nodes),
        "stdout_sha256": hashlib.sha256(stdout.encode()).hexdigest(),
        "stderr_sha256": hashlib.sha256(stderr.encode()).hexdigest(),
        "stdout": stdout[-12000:],
        "stderr": stderr[-8000:],
        "target_executed": False,
        "collection_only": True,
        "network": "none",
    }
    if record["status"] != "PASS":
        record["blocker"] = "static_collection_not_established"
    record["collection_hash"] = hash_record(record)
    return record
