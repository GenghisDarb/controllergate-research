from __future__ import annotations

import hashlib
import json
import urllib.request

from .circuit_breaker import CircuitBreaker
from .retry_policy import RetryPolicy


def read_json(url: str, *, allowed: tuple[str, ...], retry: RetryPolicy | None = None,
              breaker: CircuitBreaker | None = None, timeout: float = 10.0) -> dict[str, object]:
    if not any(url.startswith(prefix) for prefix in allowed):
        return {"status": "BLOCK", "exact_blocker": "connector_resource_not_frozen", "write_authority": False}
    policy, circuit = retry or RetryPolicy(), breaker or CircuitBreaker()
    last: Exception | None = None
    for attempt in range(1, policy.maximum_attempts + 1):
        if circuit.open:
            break
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "ControllerGate-ReadOnly/1"}, method="GET")
            with urllib.request.urlopen(request, timeout=timeout) as response:
                raw = response.read()
                json.loads(raw)
                circuit.record(True)
                return {"status": "CONNECTOR_READ_EXECUTED", "response_hash": hashlib.sha256(raw).hexdigest(),
                        "response_bytes": len(raw), "retry_count": attempt - 1,
                        "rate_limit_remaining": response.headers.get("X-RateLimit-Remaining"),
                        "circuit_breaker_state": "CLOSED", "write_authority": False}
        except Exception as exc:  # bounded connector evidence
            last = exc
            circuit.record(False)
    return {"status": "BLOCKED_EXACT_WITH_NEW_EVIDENCE", "exact_blocker": type(last).__name__ if last else "circuit_open",
            "retry_count": min(policy.maximum_attempts, circuit.failures), "circuit_breaker_state": "OPEN" if circuit.open else "CLOSED",
            "write_authority": False}


def reject_write(resource: str) -> dict[str, object]:
    return {"status": "CONNECTOR_WRITE_AUTHORITY_DISABLED", "resource": resource, "executed": False}
