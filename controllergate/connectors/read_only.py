from __future__ import annotations

import hashlib
import json
import sys
import tempfile
from pathlib import Path

from controllergate.execution.execution_broker import execute_external_operation
from controllergate.state.integrity import canonical_hash

from .circuit_breaker import CircuitBreaker
from .retry_policy import RetryPolicy


def read_json(url: str, *, allowed: tuple[str, ...], retry: RetryPolicy | None = None,
              breaker: CircuitBreaker | None = None, timeout: float = 10.0) -> dict[str, object]:
    if not any(url.startswith(prefix) for prefix in allowed):
        return {"status": "BLOCK", "exact_blocker": "connector_resource_not_frozen", "write_authority": False}
    policy, circuit = retry or RetryPolicy(), breaker or CircuitBreaker()
    with tempfile.TemporaryDirectory(prefix="controllergate-readonly-") as temporary:
        root = Path(temporary); output = root / "response.json"
        code = (
            "import pathlib,sys,urllib.request;"
            "r=urllib.request.Request(sys.argv[1],headers={'User-Agent':'ControllerGate-ReadOnly/2'},method='GET');"
            "x=urllib.request.urlopen(r,timeout=float(sys.argv[3]));d=x.read();pathlib.Path(sys.argv[2]).write_bytes(d)"
        )
        attestation = {"status": "PASS", "attestation_hash": canonical_hash([sys.version, sys.platform])}
        try:
            run, record = execute_external_operation(
                operation_type="secondary_input_acquisition", argv=[sys.executable, "-c", code, url, str(output), str(timeout)],
                cwd=root, runtime_root=root, stage_id="read_only_connector", candidate_id="connector-resource",
                authorization_id=canonical_hash([url, allowed]), runtime_attestation=attestation,
                platform=sys.platform, runtime=sys.version, network_policy="bounded_read_only",
                network_request_budget=policy.maximum_attempts, network_byte_budget=5_000_000,
                timeout=max(1, int(timeout) + 2), output_paths=[output], run_id="connector-read-only",
                nonce=canonical_hash([url, "connector-read-only"]),
            )
            if run.returncode == 0 and output.is_file():
                raw = output.read_bytes(); json.loads(raw); circuit.record(True)
                return {"status": "CONNECTOR_READ_EXECUTED", "response_hash": hashlib.sha256(raw).hexdigest(),
                        "response_bytes": len(raw), "retry_count": 0, "circuit_breaker_state": "CLOSED",
                        "write_authority": False, "broker_record_hash": record["record_hash"]}
            circuit.record(False)
            return {"status": "BLOCKED_EXACT_WITH_NEW_EVIDENCE", "exact_blocker": "brokered_connector_failed",
                    "retry_count": 1, "circuit_breaker_state": "OPEN" if circuit.open else "CLOSED", "write_authority": False}
        except Exception as exc:
            circuit.record(False)
            return {"status": "BLOCKED_EXACT_WITH_NEW_EVIDENCE", "exact_blocker": type(exc).__name__,
                    "retry_count": 1, "circuit_breaker_state": "OPEN" if circuit.open else "CLOSED", "write_authority": False}


def reject_write(resource: str) -> dict[str, object]:
    return {"status": "CONNECTOR_WRITE_AUTHORITY_DISABLED", "resource": resource, "executed": False}
