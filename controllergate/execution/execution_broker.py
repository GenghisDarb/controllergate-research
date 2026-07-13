from __future__ import annotations

import hashlib
import os
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Mapping

from controllergate.core.evidence import hash_record
from .evidence_kind import EvidenceKind
from .execution_record import ExecutionRecord


def execute_command(*, argv: list[str], cwd: Path, runtime_root: Path, stage_id: str, candidate_id: str, authorization_id: str, env: Mapping[str, str] | None = None, timeout: int = 120, required_sentinels: list[str] | None = None) -> tuple[subprocess.CompletedProcess[str], ExecutionRecord]:
    if not argv:
        raise ValueError("exact argv is required")
    effective_env = dict(env or {})
    started_wall = datetime.now(timezone.utc)
    started = time.monotonic()
    run = subprocess.run(argv, cwd=cwd, env=effective_env or None, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout, check=False)
    ended_wall = datetime.now(timezone.utc)
    observed = [line.strip() for line in (run.stdout + "\n" + run.stderr).splitlines() if line.strip().isupper() and " " not in line.strip()]
    record = ExecutionRecord(
        execution_id=f"command:{stage_id}:{started_wall.timestamp()}", stage_id=stage_id,
        candidate_id=candidate_id, evidence_kind=EvidenceKind.EXECUTED_COMMAND,
        authorization_id=authorization_id, operation_status="COMPLETED",
        evidence_status="RECORDED", gate_decision="PENDING_VERIFICATION", candidate_state="UNCHANGED",
        argv=argv, working_directory=str(cwd.resolve()), runtime_root_identity=str(runtime_root.resolve()),
        runtime_image_or_interpreter_identity=argv[0], process_id=None,
        start_timestamp=started_wall.isoformat(), end_timestamp=ended_wall.isoformat(),
        monotonic_duration=time.monotonic() - started, environment_allowlist_hash=hash_record(sorted(effective_env)),
        network_policy="none", return_code=run.returncode,
        stdout_hash=hashlib.sha256(run.stdout.encode()).hexdigest(), stderr_hash=hashlib.sha256(run.stderr.encode()).hexdigest(),
        required_sentinels=required_sentinels or [], observed_sentinels=observed,
        independent_verifier="execution_claim_verifier", verifier_result="PENDING",
    )
    return run, record
