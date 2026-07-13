from __future__ import annotations

import inspect
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from controllergate.core.evidence import sha256_file
from .evidence_kind import EvidenceKind
from .execution_record import ExecutionRecord


def observe_callable(fn: Callable[..., Any], *, stage_id: str, candidate_id: str, authorization_id: str, runtime_root: Path) -> tuple[Any, ExecutionRecord]:
    source = Path(inspect.getsourcefile(fn) or "")
    started_wall = datetime.now(timezone.utc)
    started = time.monotonic()
    result = fn()
    duration = time.monotonic() - started
    ended_wall = datetime.now(timezone.utc)
    record = ExecutionRecord(
        execution_id=f"callable:{stage_id}:{started_wall.timestamp()}", stage_id=stage_id,
        candidate_id=candidate_id, evidence_kind=EvidenceKind.EXECUTED_CALLABLE,
        authorization_id=authorization_id, operation_status="COMPLETED",
        evidence_status="RECORDED", gate_decision="PENDING_VERIFICATION",
        candidate_state="UNCHANGED", callable_identity=f"{fn.__module__}.{fn.__qualname__}",
        callable_source_file=str(source), callable_source_hash=sha256_file(source),
        working_directory=str(Path.cwd()), runtime_root_identity=str(runtime_root),
        start_timestamp=started_wall.isoformat(), end_timestamp=ended_wall.isoformat(),
        monotonic_duration=duration, return_code=0, independent_verifier="execution_claim_verifier",
        verifier_result="PENDING",
    )
    return result, record
