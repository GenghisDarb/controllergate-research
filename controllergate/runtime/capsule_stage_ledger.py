from __future__ import annotations

import hashlib
from typing import Any

from controllergate.core.evidence import hash_record


def build_capsule_stage_record(
    *, stage: str, command: list[str], return_code: int | None, stdout: str, stderr: str,
    exception_class: str | None = None, target_nodes: list[str] | None = None,
    timeout_state: bool = False, process_signal: str | None = None,
) -> dict[str, Any]:
    record = {
        "stage": stage,
        "command": command,
        "return_code": return_code,
        "stdout_hash": hashlib.sha256(stdout.encode()).hexdigest(),
        "stderr_hash": hashlib.sha256(stderr.encode()).hexdigest(),
        "bounded_output_tail": (stdout + "\n" + stderr)[-4000:],
        "exception_class": exception_class,
        "target_nodes": target_nodes or [],
        "timeout_state": timeout_state,
        "process_signal": process_signal,
        "semantic_signature": hashlib.sha256((stdout + "\0" + stderr).encode()).hexdigest(),
    }
    record["record_hash"] = hash_record(record)
    return record
