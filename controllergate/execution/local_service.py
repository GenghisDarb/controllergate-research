from __future__ import annotations

import hashlib
import json
import os
import socket
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping
from urllib.request import urlopen

from controllergate.core.evidence import hash_record
from controllergate.execution.execution_broker import record_external_service_event, start_brokered_service_process


def _loopback(host: str) -> bool:
    return host in {"127.0.0.1", "localhost", "::1"}


def _unused_port(host: str) -> int:
    family = socket.AF_INET6 if ":" in host else socket.AF_INET
    with socket.socket(family, socket.SOCK_STREAM) as sock:
        sock.bind((host, 0))
        return int(sock.getsockname()[1])


def _port_closed(host: str, port: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=0.25):
            return False
    except OSError:
        return True


@dataclass
class BrokeredLocalService:
    service_id: str
    candidate_id: str
    run_id: str
    frame_id: str
    argv_template: tuple[str, ...]
    cwd: Path
    runtime_root: Path
    host: str = "127.0.0.1"
    requested_port: int = 0
    environment_allowlist: tuple[str, ...] = ()
    request_budget: int = 32
    byte_budget: int = 16_000_000
    parent_ledger_hash: str | None = None
    runtime_attestation_hash: str | None = None
    process: subprocess.Popen[bytes] | None = field(default=None, init=False)
    port: int | None = field(default=None, init=False)
    receipts: list[dict[str, Any]] = field(default_factory=list, init=False)
    requests_observed: int = field(default=0, init=False)
    bytes_observed: int = field(default=0, init=False)

    def _receipt(self, operation_type: str, **values: Any) -> dict[str, Any]:
        record = record_external_service_event(
            operation_type=operation_type, service_id=self.service_id, candidate_id=self.candidate_id,
            run_id=self.run_id, frame_id=self.frame_id, host=self.host, port=self.port,
            runtime_root=self.runtime_root,
            runtime_attestation_hash=self.runtime_attestation_hash or hash_record([self.candidate_id, self.run_id, str(self.runtime_root.resolve())]),
            parent_ledger_hash=self.parent_ledger_hash,
            values={"request_budget": self.request_budget, "byte_budget": self.byte_budget, **values},
        )
        self.parent_ledger_hash = record["record_hash"]
        self.receipts.append(record)
        return record

    def start(self, readiness_path: str = "/", timeout: float = 30.0) -> dict[str, Any]:
        if not _loopback(self.host):
            raise ValueError("local service binding outside loopback is forbidden")
        self.port = self.requested_port or _unused_port(self.host)
        if not _port_closed(self.host, self.port):
            raise ValueError("requested local service port is already in use")
        argv = [value.replace("{PORT}", str(self.port)) for value in self.argv_template]
        environment = {key: os.environ[key] for key in self.environment_allowlist if key in os.environ}
        self.process, start_receipt = start_brokered_service_process(
            argv=argv, cwd=self.cwd, env=environment or None,
            service_id=self.service_id, candidate_id=self.candidate_id, run_id=self.run_id,
            frame_id=self.frame_id, host=self.host, port=self.port, requested_port=self.requested_port, runtime_root=self.runtime_root,
            runtime_attestation_hash=self.runtime_attestation_hash or hash_record([self.candidate_id, self.run_id, str(self.runtime_root.resolve())]),
            parent_ledger_hash=self.parent_ledger_hash,
        )
        self.parent_ledger_hash = str(start_receipt["record_hash"])
        self.receipts.append(start_receipt)
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if self.process.poll() is not None:
                break
            try:
                with urlopen(f"http://{self.host}:{self.port}{readiness_path}", timeout=0.5) as response:
                    payload = response.read(1_048_576)
                    if response.status < 500:
                        self.requests_observed += 1
                        self.bytes_observed += len(payload)
                        self._receipt(
                            "service_readiness",
                            status="PASS",
                            response_status=response.status,
                            response_sha256=hashlib.sha256(payload).hexdigest(),
                        )
                        return start_receipt
            except Exception:
                time.sleep(0.1)
        self.stop()
        raise RuntimeError("local service readiness failed")

    def request(self, path: str) -> tuple[bytes, dict[str, Any]]:
        if self.process is None or self.process.poll() is not None or self.port is None:
            raise RuntimeError("local service is not running")
        if self.requests_observed >= self.request_budget:
            raise RuntimeError("local service request budget exhausted")
        with urlopen(f"http://{self.host}:{self.port}{path}", timeout=5) as response:
            remaining = self.byte_budget - self.bytes_observed
            payload = response.read(max(0, remaining) + 1)
            if len(payload) > remaining:
                raise RuntimeError("local service byte budget exhausted")
            self.requests_observed += 1
            self.bytes_observed += len(payload)
            receipt = self._receipt(
                "service_request",
                path=path,
                status="PASS",
                response_status=response.status,
                response_sha256=hashlib.sha256(payload).hexdigest(),
            )
            return payload, receipt

    def stop(self) -> dict[str, Any]:
        if self.process is None:
            return self._receipt("service_stop", status="NOT_RUNNING")
        if self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=5)
        stdout, stderr = self.process.communicate()
        stop = self._receipt(
            "service_stop",
            status="PASS",
            exit_code=self.process.returncode,
            stdout_sha256=hashlib.sha256(stdout).hexdigest(),
            stderr_sha256=hashlib.sha256(stderr).hexdigest(),
        )
        closed = bool(self.port is not None and _port_closed(self.host, self.port))
        self._receipt("service_cleanup", status="PASS" if closed else "BLOCK", port_closed=closed, orphan_process=False)
        return stop

    def __enter__(self) -> "BrokeredLocalService":
        self.start()
        return self

    def __exit__(self, _type: object, _value: object, _traceback: object) -> None:
        self.stop()

    def lifecycle_record(self) -> dict[str, Any]:
        cleanup = next((row for row in reversed(self.receipts) if row["operation_type"] == "service_cleanup"), None)
        return {
            "status": "PASS" if cleanup and cleanup.get("port_closed") and not cleanup.get("orphan_process") else "BLOCK",
            "service_id": self.service_id,
            "candidate_id": self.candidate_id,
            "actual_port": self.port,
            "requests_observed": self.requests_observed,
            "bytes_observed": self.bytes_observed,
            "receipts": self.receipts,
            "orphan_process": False if cleanup else None,
        }
