from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Any

SECRET_PATTERN = re.compile(r"(token|secret|password|key|credential)", re.IGNORECASE)


def _hash(value: Any) -> str:
    return sha256(json.dumps(value, sort_keys=True, default=str).encode("utf-8")).hexdigest()


def redact_environment(env: dict[str, str]) -> dict[str, str]:
    return {name: "<redacted>" if SECRET_PATTERN.search(name) else str(value) for name, value in sorted(env.items())}


def classify_incident(stack_trace: str, dependency_metadata: dict[str, Any] | None = None, warning_text: str = "") -> str:
    deps = dependency_metadata or {}
    if deps.get("drift_detected"):
        return "dependency_drift_candidate"
    if "Traceback" in stack_trace or "Exception" in stack_trace:
        return "runtime_failure"
    if warning_text:
        return "warning_degradation"
    if deps.get("latency_ms") or deps.get("memory_mb"):
        return "performance_degradation"
    return "unknown"


def capture_incident(
    *,
    command: list[str],
    cwd: str | Path,
    env: dict[str, str],
    stack_trace: str,
    dependency_metadata: dict[str, Any] | None = None,
    source_closure_hint: list[str] | None = None,
    timestamp: str | None = None,
    incident_id: str | None = None,
    warning_text: str = "",
) -> dict[str, Any]:
    safe_env = redact_environment(env)
    timestamp = timestamp or datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    base = {
        "command": list(command),
        "cwd": str(cwd),
        "env_hash": _hash(safe_env),
        "stack_trace_hash": sha256(stack_trace.encode("utf-8")).hexdigest(),
        "dependency_metadata_hash": _hash(dependency_metadata or {}),
        "source_closure_hint": sorted(source_closure_hint or []),
        "timestamp": timestamp,
        "incident_classification": classify_incident(stack_trace, dependency_metadata, warning_text),
    }
    base["incident_id"] = incident_id or _hash(base)[:16]
    base["incident_bundle_hash"] = _hash(base)
    base["redacted_environment"] = safe_env
    base["secrets_captured"] = False
    return base
